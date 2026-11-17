"""Mede a qualidade do RAG.

Recuperação: a página certa veio entre as 5 primeiras? (por modo de busca)
Resposta: contém o fato esperado? ("a|b" aceita qualquer alternativa) cita só páginas que recebeu? recusa quando deve?
"""
import json
import sys
import time
from pathlib import Path

from rag.busca import buscar
from rag.responder import responder

AQUI = Path(__file__).parent
casos = [json.loads(l) for l in open(AQUI / "perguntas.jsonl")]
com_resposta = [c for c in casos if not c.get("recusar")]


def recuperacao(modo: str, k: int = 5) -> float:
    acertos = sum(
        any(t["pagina"] in c["paginas"] for t in buscar(c["pergunta"], c["modelo"], k, modo)) for c in com_resposta
    )
    return acertos / len(com_resposta)


def respostas():
    linhas, ok_fato, ok_cit, ok_rec = [], 0, 0, 0
    for c in casos:
        t0 = time.time()
        r = responder(c["pergunta"], c["modelo"])
        if c.get("recusar"):
            certo = r["recusou"]
            ok_rec += certo
        else:
            certo = not r["recusou"] and all(any(alt.lower() in r["resposta"].lower() for alt in x.split("|")) for x in c["deve_conter"])
            ok_fato += certo
        ok_cit += not r["citacoes_invalidas"]
        linhas.append({"id": c["id"], "certo": certo, "segundos": round(time.time() - t0, 1), "resposta": r["resposta"]})
        print(("✔" if certo else "✘"), c["id"], flush=True)
    n_rec = len(casos) - len(com_resposta)
    return linhas, ok_fato / len(com_resposta), ok_rec / n_rec, ok_cit / len(casos)


if __name__ == "__main__":
    print("Recuperação (página certa no top 5):")
    rec = {m: recuperacao(m) for m in ("bm25", "vetor", "hibrida")}
    for m, v in rec.items():
        print(f"  {m:8} {v:.0%}")
    if "--so-busca" in sys.argv:
        sys.exit()
    linhas, fato, recusa, cit = respostas()
    print(f"\nResposta com o fato certo: {fato:.0%}\nRecusou quando devia:      {recusa:.0%}\nCitações válidas:          {cit:.0%}")
    (AQUI / "resultados").mkdir(exist_ok=True)
    out = AQUI / "resultados" / time.strftime("%Y%m%d-%H%M.json")
    out.write_text(json.dumps({"recuperacao": rec, "fato": fato, "recusa": recusa, "citacoes": cit, "casos": linhas}, ensure_ascii=False, indent=1))
    print("detalhes em", out.relative_to(AQUI.parent))
