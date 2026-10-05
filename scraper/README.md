# Scraper de meta TFT (protótipo)

Job diário que baixa as **6 melhores comps do patch atual** (Set 18 "Enchanted Wilds", patch 18.3b
em 2026-10-05) com os dados de "como jogar" e grava `scraper/data/comps.json`, para alimentar o guia
de comps (constantes `COMPS`, `BOARDS`, `LVLT`, `AUGS`, `COMPONENTS`) sem copiar screenshots à mão.

Sem dependências pagas: só `requests`. Fonte escolhida: **API JSON pública (não documentada) do MetaTFT**.

## O que foi testado (2026-10-05, `requests` + User-Agent de Chrome, 1 req/s)

| Site | Renderização | API encontrada? | Status observado | Anti-bot | robots.txt |
|---|---|---|---|---|---|
| **MetaTFT** `/comps` | SPA Vite/React (HTML de 4 KB, só `<div id="root">`) | **Sim.** Bundle `assets/main-*.js` expõe `https://api-hc.metatft.com/tft-comps-api/{comps_data, comp_details, latest_cluster_info, latest_cluster_id, comp_options, comp_builds, comp_augment_tiers}` e lookups em `https://data.metatft.com/lookups/` | 200 em todos, sem autenticação; `comps_data` = 262 KB, 59 comps; `comp_details` = 295 KB por comp | Cloudflare na frente, **sem challenge** para HTML nem API | `User-agent: * / Disallow:` (tudo liberado) |
| **tactics.tools** `/team-compositions` | Next.js SSR (Vercel), `__NEXT_DATA__` de 830 KB | **Parcial.** `pageProps.initialData.groups` traz 5 grupos com `units`, `count`, `place`, `top4`, `win`, itens, augments (707 k jogos). Host `https://api.tft.tools` só aparece em `preconnect`/`patreon/login`; endpoint de comps não localizado nos chunks | 200 | Nenhum sinal | `User-agent: *` sem Disallow |
| **Mobalytics** `/tft/tier-list` | Desconhecida (bloqueado antes do HTML) | Não verificável | **403** "Just a moment..." (challenge Cloudflare) | **Sim**, bloqueia `requests` mesmo com UA de browser | `Disallow: /api/tft` (API proibida a bots) |
| **lolchess.gg** `/meta` | Desconhecida | Não | **404 com corpo vazio** em `/meta`, `/meta?hl=en` e `/` (CloudFront), mesmo com headers completos de Chrome | Provável bloqueio geográfico/fingerprint (INFERIDO) | `Disallow: /search`, resto liberado |
| **tftactics.gg** `/tierlist/team-comps` (bônus) | React pré-renderizado (Netlify): HTML de 176 KB já contém `tier-group` S/A/B com `team-name` e `team-playstyle`; mostra "Patch 18.3b" | Nenhuma API; dados embutidos no HTML/bundle de 3 MB | 200 | Nenhum sinal | `User-agent: * / Disallow:` |

Dumps brutos (HTML, JS, JSON) ficaram no scratchpad da sessão, fora do projeto.

## Página de detalhe de uma comp (MetaTFT)

Clicar numa comp em `/comps` dispara **um** GET:
`https://api-hc.metatft.com/tft-comps-api/comp_details?comp=<cluster>&cluster_id=<cluster_id>`
(ex.: `comp=425014&cluster_id=425`, 200, 295 KB). Campos VERIFICADOS no JSON e como o site os usa:

| Campo em `results` | Conteúdo | Uso no guia |
|---|---|---|
| `levels[]` `{level, stage, round, count}` | Em que estágio-rodada os jogadores sobem cada nível (ex.: lvl 5 em 3-2) | **LVLT** (timing de level) |
| `rerolls{level: {rerolls, matches}}` | Rolagens médias por nível (`rerolls/matches`); o nível com mais rolagens = quando rolar | **LVLT.roll** ("rola no lvl X") |
| `final_levels[]` | Distribuição de nível final; >50 % no 9 => "Fast 9" | estilo da comp |
| `early_options{4..7: [{unit_list, count, avg, win}]}` | Tabuleiros early mais jogados por nível | **COMPS.early** |
| `options{7..10: [{units_list, traits_list, count, avg}]}` | Tabuleiros mais jogados nos níveis 7-10 (sem posições) | **BOARDS** (por nível) |
| `positioning.units{unit: positions[{cell, count}]}` | Frequência de cada unidade em cada hex (`cell_1..7` = linha de trás, `cell_22..28` = frente); o site faz atribuição gulosa (função `pfe`) | **BOARDS** (posicionamento) |
| `unit_stats[]` `{unit, tiers[{tier, pcnt, avg}], num_items[]}` | Nível de estrela mais comum por unidade | **COMPS.units[].stars** |
| `builds[]` (300) e `comps_data.builds` (4 por comp) | Itens por carry (`unit`, `buildName[]`, `count`, `avg`) | **COMPS.units[].items / carries** |
| `itemNames[]` `{itemNames, pcnt, avg, units[]}` | Prioridade de itens completos e em quem funcionam melhor; o site deriva daí a prioridade de componentes (carrossel) via `items[].composition` do lookup | **COMPONENTS / items** |
| `comp_augment_tiers` (endpoint separado) | Augments em tiers S/A/B... por comp | **AUGS** |
| `proComps[]` | Comp de pro player mais parecida (título, notas, posições) | dicas |
| `first_carousel`, `augments`, `suggested_legends`, `portals` | **Vazios** neste set (18) | - |
| `counters[]`, `ranks[]`, `trends[]`, `players{}` | Matchups, distribuição por elo, tendência diária | extras |

Também VERIFICADO (200) mas não usado: `comp_options?cluster_id=` (5 MB; `options` de todas as comps),
`comp_builds?cluster_id=` (5 MB), `latest_cluster_info` (394 KB; lookups e centroides).

### Regras copiadas do bundle do MetaTFT (para o JSON bater com o site)

- Tier: `avg < 4.25 S, < 4.5 A, < 4.75 B, < 5 C, senão D`.
- Dificuldade: `difficulty < -0.05 Easy`, `> 0.07 ou "Fast 9" Hard`, senão Medium.
- Estilo: `levelling` começando com `lvl` = reroll; `Fast 8`/`Fast 9` = boost. Textos oficiais dos
  tooltips: "lvl 5: 1 cost reroll, roll to ~33g before level 5, slow roll at 5 above 50g"; "lvl 7: level to 7
  then slow-roll above 50g; if contested go 8"; "Fast 8: level to 8 asap to secure 4-costs".
- Nome da comp: `name[]` (trait + unidades, o que o site exibe) e não `name_string` (difere em 35/59 comps).
- Posicionamento: para cada unidade da comp, na ordem, pega o hex mais frequente ainda livre.

## Esquema de `data/comps.json`

```json
{
  "fetched_at": "...", "source": {"site": "MetaTFT", "attribution": "...", "endpoints": ["..."]},
  "set": "TFTSet18", "set_name": "Enchanted Wilds", "patch": null, "cluster_id": 425,
  "total_games": 1520092, "not_provided_by_source": ["patch label", "top4Rate", "winRate", "firstCarousel"],
  "top": [{
    "id": "425014", "name": "Spellweaver Veigar", "tier": "S", "avgPlacement": 4.206, "playRate": 7.17,
    "games": 109004, "top4Rate": null, "winRate": null, "levelling": "lvl 5", "difficulty": "Hard",
    "units": [{"name": "Veigar", "id": "DA_18_Veigar", "cost": 1, "stars": 3,
               "items": ["Flora Fatalis Emblem", "Blue Buff", "Jeweled Gauntlet"], "carry": true}],
    "traits": [{"name": "Spellweaver", "count": 2}],
    "carries": ["Alistar", "LeBlanc", "Ornn", "Veigar"],
    "early": {"4": ["LeBlanc", "Ornn", "Rek'Sai", "Veigar"], "5": ["..."], "6": ["..."], "7": ["..."]},
    "boardsByLevel": {"7": ["..."], "8": ["..."], "9": ["..."], "10": ["..."]},
    "positioning": {"rows": [["frente..."], [], [], ["Veigar", "LeBlanc", null, null, null, null, null]],
                    "cells": {"cell_1": "Veigar", "cell_2": "LeBlanc", "cell_25": "Alistar"}},
    "levelTiming": {"levels": {"4": {"stage": "2-3", "avgRerolls": 7.2}, "5": {"stage": "3-2", "avgRerolls": 20.6}},
                    "rollLevel": "5", "finalLevelPct": {"7": 37.1, "8": 33.4, "9": 19.3}, "style": "lvl 5"},
    "itemPriority": [{"name": "Gargoyle Stoneplate", "perGame": 1.22, "avgPlacement": 4.05, "bestOn": ["Ornn", "Alistar"]}],
    "componentPriority": [{"name": "Tear Of The Goddess", "id": "DA_TearOfTheGoddess", "perGame": 3.91}],
    "firstCarousel": null,
    "augments": {"S": ["Item Extraction", "Pandora's Bench", "Trade Sector"]},
    "proTips": {"title": "VEIGAR > Blackthorn > Lvl 5 reroll", "notes": "...", "url": "https://www.metatft.com/pro-comps?comp=..."},
    "trend": [{"day": "2026-09-28", "avgPlacement": 4.24, "games": 2708}]
  }],
  "all_comps": [{"id": "...", "name": "...", "tier": "...", "avgPlacement": 0, "playRate": 0, "games": 0}]
}
```

`top` = exatamente as 6 melhores por `avgPlacement` (ranked, fila 1100); `all_comps` = as 59 em resumo.
`positioning.rows[0]` é a linha da frente (lado do inimigo), `rows[3]` a de trás; 7 colunas, `null` = vazio.

### Mapeamento para as constantes da página

| Constante | De onde vem | Observação |
|---|---|---|
| `COMPS.name/tier/avg/pick` | `top[].name/tier/avgPlacement/playRate` | `pick` da página é fração (0.45); aqui é % |
| `COMPS.top4/win` | **não fornecido** | `top4Rate`/`winRate` = `null` |
| `COMPS.units{name,cost,stars,items,carry}` | `top[].units[]` | estrelas = nível mais comum nas partidas |
| `COMPS.carries/early/core` | `carries`, `early["4".."7"]`, `boardsByLevel["8"]` | |
| `COMPS.items{rod:2,...}` | `componentPriority[].perGame` | converter para os ids `rod/tear/...` da página |
| `COMPS.style/spike/roll/lvl` | `levelling`, `levelTiming.rollLevel`, `levelTiming.levels[*].stage` | texto em pt-BR continua manual |
| `BOARDS` (4 boards por estágio) | `early["5"]`, `early["6"]`, `early["7"]`, `boardsByLevel["8"]` + `positioning` | hoje a página só lista nomes; posições vêm de `positioning.rows` |
| `LVLT{t:[...], roll}` | `levelTiming.levels[n].stage` para n=5..9, `rollLevel` | |
| `AUGS` (categorias) | `top[].augments` dá os **augments por tier**; a categorização (eco/reroll/xp...) é da página | manual |
| `COMPONENTS` | `componentPriority[].id` | ids do jogo, não os da página |

**Precisa de fonte manual/outra:** rótulo do patch (18.3b; tftactics.gg mostra no HTML), `top4`/`win`
(tactics.tools tem `top4`/`win` no `__NEXT_DATA__`, mas sem nomes de comp), textos em pt-BR (`when`, `roll`,
`spike`, dicas por estágio), categorias de augments da página, `fam`/`stable`, carrossel inicial (vazio na API).

## Como rodar

```powershell
cd "C:\Users\Luis Caracio\Desktop\tft\scraper"
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python fetch_meta.py
```

Saída: `OK top 6 of 59 comps, set=TFTSet18, cluster=425, 20.6s -> ...\data\comps.json` + uma linha por comp.
9 requests (~3 MB) com 1 s de intervalo. Exit code 1 (mensagem em stderr) em falha de rede/JSON ou se vierem
menos de 6 comps; a escrita é atômica (`.tmp` + `os.replace`), então uma falha nunca corrompe o JSON anterior.

## Automação diária (grátis)

**Viabilidade no GitHub Actions:** o endpoint escolhido respondeu **200 a um `requests.get` simples com UA de
browser, sem cookies nem JS, sem challenge do Cloudflare** (VERIFICADO desta máquina, IP residencial BR, 20+
chamadas). Isso é o pré-requisito para rodar num runner. **Não foi testado a partir de IPs do GitHub** (INFERIDO
que funciona; datacenters às vezes recebem challenge do Cloudflare). Se o runner receber 403/"Just a moment", a
alternativa é rodar o job no Windows (Task Scheduler) e fazer `git push` do JSON.

### Opção A: GitHub Actions + GitHub Pages / Vercel

`.github/workflows/update-meta.yml` (criar quando o projeto virar repositório git):

```yaml
name: update-meta
on:
  schedule:
    - cron: "0 9 * * *"      # 09:00 UTC = 06:00 BRT, 1x/dia
  workflow_dispatch:          # botão "Run workflow" para testar/reativar
jobs:
  fetch:
    runs-on: ubuntu-latest
    permissions: { contents: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r scraper/requirements.txt
      - run: python scraper/fetch_meta.py          # exit 1 => job falha, JSON antigo fica
      - name: Commit if changed
        run: |
          git config user.name "meta-bot"
          git config user.email "meta-bot@users.noreply.github.com"
          git add scraper/data/comps.json
          git diff --cached --quiet && echo "sem mudanças" || (git commit -m "chore: meta $(date -u +%F)" && git push)
```

O `git push` do bot dispara o redeploy automaticamente: no **GitHub Pages** (Settings > Pages > Deploy from
branch, ou um workflow `actions/deploy-pages` com `on: push`) e no **Vercel** (integração Git importa o repo e
faz deploy a cada push na branch de produção). A página só precisa fazer `fetch("scraper/data/comps.json")`.

Gotchas do GitHub Actions:
- **Cron pausa após 60 dias sem atividade no repositório** (GitHub desativa schedules em repos inativos e
  manda e-mail). O commit diário do bot conta como atividade enquanto o JSON mudar; se parar de mudar
  (fim de set), use `workflow_dispatch` para reativar ou faça o bot commitar `fetched_at` sempre.
- Cron do GitHub atrasa 5-30 min em horário de pico e não roda em forks por padrão.
- IPs dos runners são de datacenter (Azure) e **podem ser bloqueados pelo Cloudflare**; o script falha com
  exit 1 e o job fica vermelho, sem corromper o JSON publicado.
- Pushes feitos com o `GITHUB_TOKEN` padrão **não disparam outros workflows**; se o deploy do Pages for um
  workflow separado, chame-o no mesmo job ou use um PAT/`repository_dispatch`.

### Opção B: Windows Task Scheduler (todo dia às 06:00)

```powershell
schtasks /Create /TN "TFT Meta Fetch" /SC DAILY /ST 06:00 /F ^
  /TR "\"C:\Users\Luis Caracio\Desktop\tft\scraper\.venv\Scripts\python.exe\" \"C:\Users\Luis Caracio\Desktop\tft\scraper\fetch_meta.py\""
```

Testar com `schtasks /Run /TN "TFT Meta Fetch"`; histórico em `schtasks /Query /TN "TFT Meta Fetch" /V /FO LIST`.
Para publicar, acrescente ao comando um `git add/commit/push` (ou um `vercel deploy`).

## Riscos conhecidos

- **API não documentada**: o MetaTFT pode renomear campos, trocar host (`api-hc` -> `api-hc2` já existe como
  fallback no bundle) ou exigir token sem aviso. O script falha com exit 1 e mantém o último JSON bom.
- **Mudança de set**: o lookup é derivado de `tft_set` da própria resposta, então Set 18 -> 19 deve funcionar
  sozinho; os limiares de tier/dificuldade são os do site hoje e podem mudar.
- **Bloqueio**: Cloudflare na frente. Manter 1 req/s, ~9 requests/dia, UA normal. Não paralelizar, não retentar em loop.
- **ToS / cortesia**: os dados são do MetaTFT (agregados de partidas via Riot API). Dar crédito e link no guia
  (campo `source.attribution`); não republicar o JSON bruto. Mobalytics proíbe `/api/tft` no robots.txt e foi descartado.
- **Semântica**: `stars` do MetaTFT é uma lista por cluster (pode citar unidades fora da comp principal); o
  nível de estrela aqui vem de `unit_stats` (nível mais comum). Unidades invocadas por trait (`shopUnit=false`,
  ex.: plantas de Elderwood) são removidas dos boards.
- **Alternativa oficial**: Riot Developer API (`/tft/match/v1`) exige chave e agregação própria; fora do escopo.
