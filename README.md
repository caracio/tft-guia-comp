# TFT · Guia de escolha de comp

Página estática que ajuda a escolher entre as **6 melhores comps do patch atual** de Teamfight Tactics a partir dos bonecos, itens e situação que você tem na partida, e explica como jogar cada uma (early boards, timing de nível, quando rolar, itens, augments, posicionamento).

Os dados são atualizados **uma vez por dia, automaticamente**, a partir da API pública do [MetaTFT](https://www.metatft.com/comps). Não há servidor: um job agendado grava `data/comps.json` e a página lê esse arquivo ao abrir.

## Como funciona

```
GitHub Actions (cron 06:00 BRT)
  └─ python scraper/fetch_meta.py --out data/comps.json
       └─ 9 requests ao MetaTFT (lista + detalhes das 6 melhores), 1 s de intervalo
  └─ commit "data: atualiza meta TFT" se o JSON mudou
       └─ Vercel / GitHub Pages republicam o site a cada commit
```

| Arquivo | Papel |
| --- | --- |
| `index.html` | A página. Faz `fetch("data/comps.json")` e monta COMPS, BOARDS, LVLT e UNITS a partir dele. |
| `data/comps.json` | Dados do dia: top 6 comps com unidades, itens, early boards, timing de nível, augments e posicionamento. |
| `scraper/fetch_meta.py` | Coletor. Só depende de `requests`. Sai com código 1 em falha e nunca corrompe o JSON anterior. |
| `.github/workflows/update-meta.yml` | Agendamento diário e commit automático. |
| `Estudo · Scraping diário do meta TFT (gratuito).md` | Estudo de fontes, ferramentas, custos e riscos que embasou a solução. |
| `PRD · ...md`, `Design System ...md` | Especificação de comportamento e design da página. |

## Rodar localmente

```bash
python -m venv scraper/.venv
scraper/.venv/Scripts/python -m pip install -r scraper/requirements.txt
scraper/.venv/Scripts/python scraper/fetch_meta.py --out data/comps.json
python -m http.server 8765
```

Abra `http://localhost:8765/`. A página precisa ser servida por HTTP; aberta como arquivo local o `fetch` do JSON falha.

## Atualização manual

Na aba **Actions** do repositório, workflow **update-meta**, botão **Run workflow**. O mesmo botão reativa o agendamento caso o GitHub o pause após 60 dias sem atividade.

## Deploy

- **Vercel:** importar este repositório em vercel.com/new. Sem build, framework "Other", diretório raiz. O `vercel.json` já desativa cache do `data/`.
- **GitHub Pages:** Settings → Pages → Deploy from branch `main`, pasta `/`.

## Regras de atualização por patch

- O eixo de decisão do jogador é sempre **itens + early game**.
- Os estilos de comp (`STYLE`: reroll5, reroll7, fast8...) e os 8 tipos de augment são fixos; novos estilos seguem o mesmo formato de pesos.
- O que muda a cada patch são as comps, nomes, bonecos, itens, stats e textos de dica.

## Fonte e atribuição

Dados por [MetaTFT](https://www.metatft.com/). Este projeto não é afiliado à Riot Games nem ao MetaTFT. Teamfight Tactics é marca da Riot Games.
