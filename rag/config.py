import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PDFS = RAIZ / "data" / "pdfs"
INDICE = RAIZ / "data" / "indice"

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDER = os.environ.get("EMBEDDER", "bge-m3")
LLM = os.environ.get("LLM", "qwen3:8b")

# Manuais oficiais públicos (caoachangan.com.br/manuais). Não versionados no repo.
MANUAIS = {
    "cs55": "https://cloudfront.alpes.one/public/6af/1e8/d05/6af1e8d05aeed038740242.pdf",
    "cs55-phev": "https://cloudfront.alpes.one/public/6af/1e9/4fa/6af1e94fa9a42292893073.pdf",
    "cs75": "https://cloudfront.alpes.one/public/6af/1eb/3a7/6af1eb3a7d6c0064386328.pdf",
    "uni-t": "https://cloudfront.alpes.one/public/6af/1ec/022/6af1ec022b4a4994269248.pdf",
}
