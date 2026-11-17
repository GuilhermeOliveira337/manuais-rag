# manuais-rag

Assistente que responde dúvidas técnicas sobre carros **CAOA Changan** usando os **manuais do proprietário oficiais**, sempre citando modelo e página, e que **diz "não encontrei" em vez de inventar**.

Trabalho numa concessionária e vivo ouvindo perguntas como "qual a pressão do pneu?" ou "como desliga isso aqui?". Os manuais têm a resposta, mas são 200 páginas por modelo. Este projeto resolve isso com RAG (Retrieval-Augmented Generation), e mede o quanto acerta.

Roda **100% local**: modelos open source no Ollama, sem custo por pergunta e sem mandar dado pra fora.

## Resultado

Avaliação com 20 perguntas (16 com resposta no manual e 4 que o sistema deve recusar), em `evals/perguntas.jsonl`:

| Métrica | Resultado |
|---|---|
| Página certa entre as 5 primeiras (busca híbrida, bge-m3) | **100%** |
| Resposta contém o fato correto | **94%** (15 de 16) |
| Recusou quando a resposta não está no manual | **100%** (4 de 4) |
| Citações apontando só para páginas recebidas | **100%** |

### Qual modelo de embedding usar? Medi em vez de chutar

| Busca | bge-m3 (multilíngue) | nomic-embed-text (inglês) |
|---|---|---|
| BM25 (palavra exata) | 94% | 94% |
| Vetor (significado) | **100%** | 81% |
| Híbrida (RRF) | **100%** | 88% |

O manual é em português; o modelo multilíngue fez diferença real. A busca híbrida existe porque cada método erra coisas diferentes: BM25 acha "CR2032" e "AUTO HOLD" pela palavra exata, o vetor acha "a chave tá fraca" mesmo quando o manual diz "bateria do controle remoto".

### Onde ainda erra (e por quê)

- **Pressão do estepe do CS75:** o valor está numa tabela (`T125/80D17 420 (61)`) que não usa a palavra "estepe". O texto extraído do PDF perde a estrutura da tabela. Próximo passo: extrair tabelas separadamente e descrevê-las em texto antes de indexar.
- **"Como desligo o bip do sensor de estacionamento?"** O manual do CS75 não ensina isso, e o sistema **recusa**, que é o comportamento certo. Um chatbot comum inventaria um menu.
- **Ambiguidade no próprio manual:** a velocidade em que o ACC desliga aparece como 135 km/h numa página e 155 km/h em outra (contextos diferentes). A avaliação aceita as duas e registra a nota.

## Como funciona

```
PDF ─► texto por página ─► trechos de 900 caracteres (150 de sobreposição)
                                  │
              ┌───────────────────┴───────────────────┐
         vetores (bge-m3)                         índice BM25
              └──────────► Reciprocal Rank Fusion ◄────┘
                                  │
                   5 trechos, no máximo 1 por página
                                  │
             LLM local (qwen3:8b, temperatura 0) com regra:
         "responda só com os trechos, cite [modelo p.N],
          se não estiver aqui diga 'Não encontrei isso no manual.'"
                                  │
          verificação: toda citação aponta pra uma página recebida?
```

## Decisões

1. **Avaliação antes de "achar que está bom".** Cada mudança roda `python -m evals.rodar` e compara o número. Foi assim que escolhi o modelo de embedding.
2. **Recusa é um caso de teste.** Perguntas fora do manual (preço, financiamento, comparação com concorrente) fazem parte da avaliação. Num balcão de concessionária, resposta inventada é pior que "não sei".
3. **Citação verificada por código.** O LLM pode alucinar o número da página; o sistema confere se cada `[modelo p.N]` citado estava entre os trechos enviados.
4. **Filtro por modelo.** O manual do CS55 e o do CS75 têm textos parecidos com valores diferentes; a busca filtra pelo carro antes de tudo.
5. **Sem framework.** BM25, RRF e a orquestração estão escritos à mão (~150 linhas) para eu entender cada passo. Trocar por LangChain ou pgvector é questão de adaptar `rag/busca.py`.

## Rodando

Pré-requisito: [Ollama](https://ollama.com) com os modelos:

```bash
ollama pull bge-m3
ollama pull qwen3:8b
```

```bash
pip install -r requirements.txt
python -m rag.ingest                 # baixa os 4 manuais públicos e indexa
python -m rag.responder --modelo=uni-t "qual bateria usa a chave?"
python -m evals.rodar                # avaliação completa
python -m evals.rodar --so-busca     # só recuperação, mais rápido
```

`OLLAMA_URL`, `EMBEDDER` e `LLM` podem ser trocados por variável de ambiente.

Os PDFs não estão no repositório: são baixados do site oficial ([caoachangan.com.br/manuais](https://caoachangan.com.br/manuais)) na primeira execução. Projeto pessoal de estudo, sem vínculo oficial com a marca.

## Como usei IA para construir

Usei o Claude Code como par de programação. As perguntas de avaliação saíram de dúvidas reais do meu trabalho, e conferi cada resposta esperada direto no PDF. Quando a avaliação falhou, investiguei o motivo antes de mexer no código; em dois casos o erro estava na própria pergunta (ambígua), e corrigi a pergunta, não o resultado.

## Licença

MIT (código). Os manuais pertencem aos respectivos fabricantes.
