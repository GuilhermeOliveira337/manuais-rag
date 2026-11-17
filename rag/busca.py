"""Busca híbrida: vetores (significado) + BM25 (palavra exata), unidos por RRF."""
import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache

import numpy as np

from .config import EMBEDDER, INDICE
from .ollama import embed

STOP = set("a o e de da do das dos em no na nos nas um uma para por com se que ao à os as é ou seu sua".split())


def tokens(t: str) -> list[str]:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP and len(w) > 1]


@lru_cache
def _trechos() -> list[dict]:
    return [json.loads(l) for l in open(INDICE / "trechos.jsonl")]


@lru_cache
def _vetores(embedder: str) -> np.ndarray:
    return np.load(INDICE / f"vetores-{embedder.replace(':', '_')}.npy")


class BM25:
    def __init__(self, docs: list[list[str]], k1=1.5, b=0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.tf = [Counter(d) for d in docs]
        self.media = sum(map(len, docs)) / len(docs)
        df = Counter(w for d in docs for w in set(d))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def notas(self, q: list[str]) -> np.ndarray:
        out = np.zeros(len(self.docs), dtype=np.float32)
        for i, (tf, d) in enumerate(zip(self.tf, self.docs)):
            norm = self.k1 * (1 - self.b + self.b * len(d) / self.media)
            out[i] = sum(self.idf.get(w, 0) * tf[w] * (self.k1 + 1) / (tf[w] + norm) for w in q if w in tf)
        return out


@lru_cache
def _bm25() -> BM25:
    return BM25([tokens(t["texto"]) for t in _trechos()])


def buscar(pergunta: str, modelo: str | None = None, k: int = 5, modo: str = "hibrida", embedder: str = EMBEDDER):
    trechos = _trechos()
    filtro = np.array([modelo is None or t["modelo"] == modelo for t in trechos])
    rankings = []
    if modo in ("hibrida", "vetor"):
        q = np.array(embed([pergunta], embedder)[0], dtype=np.float32)
        s = _vetores(embedder) @ (q / np.linalg.norm(q))
        rankings.append(np.where(filtro, s, -np.inf))
    if modo in ("hibrida", "bm25"):
        rankings.append(np.where(filtro, _bm25().notas(tokens(pergunta)), -np.inf))

    # Reciprocal Rank Fusion: soma 1/(60 + posição) de cada ranking
    rrf = np.zeros(len(trechos))
    for s in rankings:
        for pos, i in enumerate(np.argsort(-s)[:50]):
            if np.isfinite(s[i]):
                rrf[i] += 1 / (60 + pos)
    melhores = [i for i in np.argsort(-rrf)[: k * 3] if rrf[i] > 0]

    vistos, out = set(), []
    for i in melhores:  # um trecho por página, pra citação não repetir
        chave = (trechos[i]["modelo"], trechos[i]["pagina"])
        if chave not in vistos:
            vistos.add(chave)
            out.append({**trechos[i], "nota": float(rrf[i])})
        if len(out) == k:
            break
    return out
