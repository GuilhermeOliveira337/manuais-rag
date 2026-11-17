import json
import urllib.request

from .config import OLLAMA


def _post(rota: str, corpo: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        OLLAMA + rota, data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def embed(textos: list[str], modelo: str) -> list[list[float]]:
    return _post("/api/embed", {"model": modelo, "input": textos})["embeddings"]


def gerar(prompt: str, sistema: str, modelo: str) -> str:
    r = _post("/api/chat", {
        "model": modelo,
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    })
    return r["message"]["content"].strip()
