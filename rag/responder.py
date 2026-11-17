"""Responde com base só nos trechos encontrados, citando modelo e página."""
import re
import sys

from .busca import buscar
from .config import LLM
from .ollama import gerar

SISTEMA = """Você é o assistente técnico de uma concessionária CAOA Changan.
Responda SOMENTE com base nos trechos do manual fornecidos.
Regras:
- Cite a fonte de cada informação no formato [modelo p.N].
- Se os trechos não trazem a resposta, diga exatamente: "Não encontrei isso no manual." e nada mais.
- Não invente botões, menus ou valores que não estejam nos trechos.
- Responda em português, em até 6 linhas, em passos curtos quando for um procedimento."""

NAO_ACHEI = "Não encontrei isso no manual."


def responder(pergunta: str, modelo: str | None = None, k: int = 5) -> dict:
    trechos = buscar(pergunta, modelo, k)
    contexto = "\n\n".join(f"[{t['modelo']} p.{t['pagina']}]\n{t['texto']}" for t in trechos)
    texto = gerar(f"Trechos do manual:\n\n{contexto}\n\nPergunta: {pergunta}", SISTEMA, LLM)
    citadas = {(m, int(p)) for m, p in re.findall(r"\[([\w-]+) p\.(\d+)\]", texto)}
    fornecidas = {(t["modelo"], t["pagina"]) for t in trechos}
    return {
        "resposta": texto,
        "fontes": sorted(fornecidas),
        "citacoes_invalidas": sorted(citadas - fornecidas),  # o modelo citou página que não recebeu
        "recusou": texto.startswith(NAO_ACHEI),
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    modelo = None
    if args and args[0].startswith("--modelo="):
        modelo = args.pop(0).split("=", 1)[1]
    r = responder(" ".join(args), modelo)
    print(r["resposta"])
    if r["citacoes_invalidas"]:
        print("\n⚠ citação fora das fontes:", r["citacoes_invalidas"])
