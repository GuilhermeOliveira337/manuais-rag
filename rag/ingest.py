"""Lê os PDFs, quebra em trechos e gera o índice (vetores + texto)."""
import json
import re
import sys
import urllib.request

import numpy as np
from pypdf import PdfReader

from .config import EMBEDDER, INDICE, MANUAIS, PDFS
from .ollama import embed

TAM, SOBRA = 900, 150  # caracteres por trecho e sobreposição entre trechos


def baixar():
    PDFS.mkdir(parents=True, exist_ok=True)
    for nome, url in MANUAIS.items():
        alvo = PDFS / f"{nome}.pdf"
        if not alvo.exists():
            print("baixando", nome)
            urllib.request.urlretrieve(url, alvo)


def limpar(t: str) -> str:
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)  # junta palavra quebrada com hífen
    return re.sub(r"\s+", " ", t).strip()


def trechos():
    for pdf in sorted(PDFS.glob("*.pdf")):
        modelo = pdf.stem
        for i, pagina in enumerate(PdfReader(pdf).pages, start=1):
            texto = limpar(pagina.extract_text() or "")
            if len(texto) < 80:
                continue
            ini = 0
            while ini < len(texto):
                yield {"modelo": modelo, "pagina": i, "texto": texto[ini : ini + TAM]}
                if ini + TAM >= len(texto):
                    break
                ini += TAM - SOBRA


def indexar(embedder: str = EMBEDDER, lote: int = 32):
    baixar()
    lista = list(trechos())
    print(f"{len(lista)} trechos; gerando vetores com {embedder}...")
    vetores = []
    for i in range(0, len(lista), lote):
        vetores += embed([t["texto"] for t in lista[i : i + lote]], embedder)
        print(f"\r{min(i + lote, len(lista))}/{len(lista)}", end="", flush=True)
    m = np.array(vetores, dtype=np.float32)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    INDICE.mkdir(parents=True, exist_ok=True)
    np.save(INDICE / f"vetores-{embedder.replace(':', '_')}.npy", m)
    with open(INDICE / "trechos.jsonl", "w") as f:
        for t in lista:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print("\nok")


if __name__ == "__main__":
    indexar(*(sys.argv[1:2] or [EMBEDDER]))
