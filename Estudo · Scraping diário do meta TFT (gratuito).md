# Estudo · Como obter dados de meta do TFT todo dia, de graça (scraping, APIs não documentadas e Riot API)

5 out 2026 · pesquisa para @Luis Caracio · acesso a todas as fontes em 2026-10-05

> Escopo revisado durante a pesquisa: o foco deixou de ser "Firecrawl" e passou a ser **"qual ferramenta ou abordagem gratuita permite puxar os dados de meta (top comps, unidades, itens, augments, colocação média) de MetaTFT, tactics.tools, Mobalytics e lolchess todo dia, com confiabilidade e custo zero"**. O Firecrawl aparece só como uma opção entre outras (seção 2.5). O nome do arquivo foi mantido porque é o caminho combinado.

Convenções deste documento:

- **VERIFICADO** = li a fonte primária ou executei a chamada e observei o resultado nesta data.
- **INFERIDO** = conclusão minha a partir do que foi verificado, ou informação de fonte secundária; tratar como hipótese a confirmar.
- Identificadores de código, endpoints e campos ficam em inglês.

---

## 0. Resumo executivo

| Pergunta | Resposta curta |
| --- | --- |
| Dá para ter dados diários de graça? | Sim. A fonte mais rica (MetaTFT) expõe uma API JSON não documentada, sem autenticação, que o próprio site consome; o tactics.tools entrega o dataset inteiro embutido no HTML (`__NEXT_DATA__`). Nenhum dos dois exige navegador. |
| Qual stack? | Python `requests` + `json`. Nada de browser headless no caminho principal. Playwright só como fallback. |
| Onde rodar todo dia? | GitHub Actions `schedule` em repositório público (grátis, ilimitado para runners padrão), gravando `data/comps.json` com commit automático. Fallback: Agendador de Tarefas do Windows 11 na máquina do usuário. |
| Custo | R$ 0. |
| Maior risco | Dependência de endpoints não documentados que podem mudar ou passar a exigir token sem aviso; e o Mobalytics proíbe explicitamente scraping nos Termos (não usar). |
| Caminho oficial | Riot TFT API (`tft-match-v1` + `tft-league-v1`) é viável para computar um meta próprio, mas **o DTO de partida não traz augments** e exige uma chave Personal/Production aprovada; serve como plano de longo prazo, não como primeira entrega. |

Ordem recomendada (detalhes na seção 6): **(1)** MetaTFT API JSON → **(2)** tactics.tools `__NEXT_DATA__` como segunda fonte/validação → **(3)** Playwright interceptando o XHR do MetaTFT se a API mudar → **(4)** Riot API + Community Dragon como caminho oficial de longo prazo.

---

## 1. O que cada site é por dentro (sondagem empírica)

Todos os testes abaixo foram feitos em 2026-10-05 com `curl` (User-Agent de Chrome) e com o Firecrawl `/scrape` (proxy `basic`), formatos `markdown`/`links`/`rawHtml`. Tamanhos são do que voltou de fato.

### 1.1 Tabela comparativa

| Site / URL da tier list | Renderização | HTML sem JS (curl) | Anti-bot observado | robots.txt (VERIFICADO) | Dados no HTML/markdown | Fonte estruturada encontrada |
| --- | --- | --- | --- | --- | --- | --- |
| **MetaTFT** `https://www.metatft.com/comps` | SPA (React/Vite; bundle `/assets/main-k-lOPnf8.js` de 5,07 MB) | 200, **4.190 bytes** (casca vazia) | Servido por Cloudflare (`cf-ray`), mas `curl` passou com 200 | `User-agent: *` / `Disallow:` (vazio = tudo permitido) + Sitemap | Só com JS: markdown com `waitFor: 6000` veio com 213 KB e todas as comps (tier, nome, dificuldade, unidades, itens, 3★, Avg Place, Pick/Win/Top4) | **API JSON não documentada** `api-hc.metatft.com/tft-comps-api/*` (ver 1.2) |
| **tactics.tools** `https://tactics.tools/team-compositions` | SSR Next.js (pages router, `next-head-count`) na Vercel | 200, **832 KB** com conteúdo | Nenhum (`server: Vercel`, sem Cloudflare) | `User-agent: *` sem nenhum `Disallow` | Sim: nomes ("Riftbeast Nidalee & Aphelios"), unidades e itens (alt das imagens), Play Rate, Place, Top 4 %, Win %, tags ("Fast Level 8", "Level 5 Reroll", "Items Dependent") | **`<script id="__NEXT_DATA__">` com 648 KB de JSON** (ver 1.3) |
| **Mobalytics** `https://mobalytics.gg/tft/tier-list` → redireciona para `/tft/tier-list/team-comps?rank=DIAMOND%2B&…` | SSR | **403** (Cloudflare bloqueou o curl) | Cloudflare WAF ativo; Firecrawl passou (200) | `Allow: /` mas `Disallow: /api/tft` (confirma que existe uma API interna e que ela é vetada a robôs) | Sim na lista: tier S/A, nome, traits, unidades, Avg Place, Win Rate, Pick Rate, Top 4. **Sem itens** na lista; detalhes só ao expandir (client-side) | `/api/tft` (não sondado: vetado por robots + ToS, ver seção 5) |
| **lolchess.gg** `https://lolchess.gg/meta` | SSR Next.js na CloudFront | **404 com 0 bytes** para o curl; Firecrawl recebeu 200 | Comportamento inconsistente sugere filtro por cabeçalhos (INFERIDO) | `Disallow: /search` apenas | 105 KB de markdown com nomes de comp ("Elder Dragon Value", tag "HOT"), traits e unidades; **nenhum número** (zero ocorrências de "Avg", "Win"); itens só parcialmente via alt | Nenhuma encontrada (não aprofundado) |
| **tftactics.gg** `https://tftactics.gg/tierlist/team-comps/` (`/team-comps` dá 404) | SSR na Netlify | 200 | Nenhum | `User-agent: *` / `Disallow:` (vazio) | 64 KB: tier, nome, "Slow Roll (5)"/"Fast 8", unidades. **Sem estatísticas** (é tier list curada) | Nenhuma |

Conclusão da sondagem: só **MetaTFT** e **tactics.tools** entregam, sem navegador, o conjunto completo que o projeto precisa (comps + colocação média + itens por unidade + timing de nível). Augments só apareceram no MetaTFT (endpoint `comp_augment_tiers`). Mobalytics é tecnicamente scrapeável via proxy mas juridicamente o pior caso (seção 5). lolchess e tftactics não têm números.

### 1.2 MetaTFT: a API que o frontend chama (VERIFICADO)

Método: baixei `https://www.metatft.com/comps` (4 KB), peguei o `src` do bundle principal e fiz `grep` de URLs no JS. Depois chamei cada endpoint com `curl` sem cookies nem token.

Hosts e rotas encontrados no bundle:

```
https://api-hc.metatft.com/tft-comps-api/comps_data
https://api-hc.metatft.com/tft-comps-api/comps_stats
https://api-hc.metatft.com/tft-comps-api/comp_details?comp=
https://api-hc.metatft.com/tft-comps-api/comp_builds
https://api-hc.metatft.com/tft-comps-api/comp_options
https://api-hc.metatft.com/tft-comps-api/comp_augment_tiers
https://api-hc.metatft.com/tft-comps-api/unit_items_processed
https://api-hc.metatft.com/tft-comps-api/latest_cluster_id
https://api-hc.metatft.com/tft-comps-api/latest_cluster_info
https://api-hc.metatft.com/tft-stat-api/{augments_tiers, items, games?days=7, percentiles, units_distribution?queue=}
https://api.metatft.com/{match_data, items_detail?item=, public/pro_players, public/esports/tournaments}
https://data.metatft.com/lookups/trait_mapping.json
```

Resultado das chamadas (todas HTTP 200, `application/json`, cabeçalho `access-control-allow-origin: *`, sem autenticação):

| Endpoint | Tamanho | Conteúdo observado |
| --- | --- | --- |
| `comps_data` | 262 KB | `results.data.{cluster_id: 425, tft_set: "TFTSet18", cluster_details{...}, portals}` + `results.games`. `cluster_details` tem **59 clusters** (comps). Cada cluster: `Cluster`, `units_string` ("DA_18_Ashe, DA_18_Maokai, …"), `traits_string`, `name`/`name_string` ("DA_Juggernaut18, DA_18_Zyra, DA_18_Sivir"), `overall{count: 92996, avg: 4.3946}`, `stars` (unidades a 3★), `builds[]` (por unidade: `buildName[]` com 3 itens, `count`, `avg`, `place_change`), `build_items`, `top_itemNames`, `trends[]` (por dia: `count`, `avg`, `pick`), `top_augments`, `difficulty`, **`levelling: "Fast 8"`** |
| `comps_stats` | 6 KB | Por cluster: `places[8]` (distribuição de colocação 1º–8º) e `count`. Permite derivar Top 4 % e Win % |
| `comp_augment_tiers` | 118 KB | `results{<clusterId>: {augments, gods, source_title}}`, `updated`, `tft_set`, `queue_id`, `cluster_id` → **tier de augments por comp** |
| `unit_items_processed` | 67 KB | `units{<unitId>: {unit, count, place, …}}`, `items`, `itemNames` |
| `latest_cluster_info` | 394 KB | `cluster_id: 425`, `state: "published"`, `created_at: 2026-09-25T08:58Z` — o "cluster" é a versão do modelo de comps publicado |
| `comp_builds`, `comp_options` | ~5 MB cada | Muito grandes; não analisados (presumivelmente builds alternativas e opções de fim de jogo) |

Observações:

- Os IDs seguem o padrão interno da Riot para o Set 18 (prefixo `DA_`, p.ex. `DA_18_Zyra`, `DA_Amumu18`, `DA_KogMaw18_AD`), o mesmo do Data Dragon (`tft-champion.json` lista `DA_CrimsonRaptor18` → "Mama Beak"). Portanto o mapeamento ID → nome legível vem de graça do Data Dragon/CDragon (seção 3.2).
- **Não verifiquei** os parâmetros de filtro que o site usa (rank "Platinum+", "Last 3 Days", "Ranked"). As rotas chamadas sem parâmetros devolveram um recorte padrão. INFERIDO: há query params como `queue`, `rank`/`percentile` e `days` (o bundle mostra `games?days=7` e `units_distribution?queue=`); descobrir via DevTools → aba Network.
- Prior art: a loja parse.bot vende um "MetaTFT API" com 3 endpoints (`get_comps`, `get_comp_details`, `get_unit_items`, 10 créditos por chamada) e afirma que "MetaTFT does not publish a documented public developer API"; ou seja, terceiros já consomem exatamente esses endpoints (VERIFICADO na página; link na seção 7). O repositório `PhucHuwu/TFT_Ranked_Data_viz` usa `requests` contra "the MetaTFT API leaderboard endpoint" (VERIFICADO no README, sem URL explícita).

### 1.3 tactics.tools: `__NEXT_DATA__` (VERIFICADO)

O HTML de `/team-compositions` contém `<script id="__NEXT_DATA__" type="application/json">` com 648.021 bytes. Estrutura observada:

```
props.pageProps
  aperture: {patch: {_0: 16191}, rankGroup: 1, gameType: 0, queue: 1100}
  initialData:
    count: 707682, place: 4.5023
    groups[5]: {full: {...}, children: [...]}
      full.comps[]: {units: ["DA_18_Varus", …], spatItems: [], extraTraits: [], count: 42052, place: 4.3339, top4: 23293, win: 2676}
      full.{count, place, top4, win, carryUnits[[unitId, score]], starUnits{}, unitItems[{unitId,itemId,count,place,top4,won}],
            unitItemPairs[], winCons[], generalItems[], levels[[lvl,count,total]], lvl9Comps[], traits[], placementDistribution[8],
            regionDistribution[], dateStats[], augmentSingles: [], aug1s/aug2s/aug3s: [], extraTraits[], code}
```

Pontos de atenção:

- Tudo é determinístico: `requests.get` + regex do script + `json.loads`. Sem LLM, sem browser.
- Os **nomes de exibição** das comps ("Riftbeast Nidalee & Aphelios") **não** estão no JSON; o site os monta no cliente a partir de traits e carries. Precisa reconstruir (trait principal + `carryUnits`) ou ler o markdown renderizado.
- **Augments vêm vazios** nessa página (`aug1s`, `aug2s`, `aug3s`, `augmentSingles` = `[]`); são carregados sob demanda ou em outra rota. INFERIDO: `https://tactics.tools/augments` tem sua própria `__NEXT_DATA__`.
- O bundle referencia um host `api.tft.tools` (só a raiz apareceu no HTML); INFERIDO que os filtros de rank/patch chamam esse host via XHR.
- Patch está codificado como `patch._0: 16191` (INFERIDO: 16.19.1 → "18.3b").

### 1.4 Mobalytics e lolchess: por que não

- **Mobalytics**: `curl` recebe 403 do Cloudflare; o `robots.txt` veta `/api/tft`; os Termos proíbem "spiders, robots, crawlers, data mining tools" (seção 5). É o único site com três barreiras simultâneas. Não compensa.
- **lolchess.gg**: o markdown não traz colocação média nem win rate (zero ocorrências), só nomes, traits e unidades. Sem números, não alimenta `avg`/`pick`/`win`/`top4` do projeto. Prior art existente (`letigredununavu/tft-scraping-bot`, `fosq/BeetleBot`) scrapeia **perfil de jogador** e **patch notes**, não a tier list.

---

## 2. Stacks gratuitas e quando cada uma é necessária

| Situação | Ferramenta | Quando usar | Custo / licença |
| --- | --- | --- | --- |
| Endpoint JSON (MetaTFT) | Python `requests` (ou `httpx`) + `json` | Padrão. Uma requisição, um `json()`; nada para "parsear" | MIT/BSD, grátis |
| HTML server-rendered com JSON embutido (tactics.tools) | `requests` + `re`/`json` para `__NEXT_DATA__`; `BeautifulSoup`/`selectolax` só se precisar do DOM | Páginas Next.js (pages router) quase sempre têm `__NEXT_DATA__`; é mais estável que seletores CSS | Grátis |
| HTML server-rendered sem JSON (tftactics, lolchess) | `requests` + `BeautifulSoup` (`pip install beautifulsoup4 lxml`) ou `selectolax` (mais rápido) | Quando os dados estão no DOM e o site não precisa de JS | Grátis |
| SPA (MetaTFT via página, não via API) | **Playwright** (Python ou Node): `pip install playwright && playwright install chromium`; usar `page.expect_response("**/tft-comps-api/comps_data")` para capturar o XHR em vez de raspar o DOM | Só quando a API mudar ou exigir algo que o navegador real resolve (cookies, token no header) | Apache-2.0, grátis; ~300 MB de browser |
| Site atrás de Cloudflare que bloqueia `requests` (Mobalytics) | `curl_cffi` (`pip install curl_cffi`, `impersonate="chrome"`) imita TLS/JA3/HTTP2 de browser | Só se for juridicamente aceitável (no caso do Mobalytics não é) | MIT |
| Rastrear muitas páginas com fila, retry e throttling | **Scrapy** (`ROBOTSTXT_OBEY`, AutoThrottle, feed export JSON; sem JS por padrão → `scrapy-playwright`) ou **Crawlee** Python (`pip install 'crawlee[all]'`, `BeautifulSoupCrawler`/`PlaywrightCrawler`, Python ≥ 3.10) | Overkill para 2–3 URLs por dia; útil se o projeto crescer para páginas de detalhe por comp | BSD / Apache-2.0 |
| "SaaS de scraping" | **Firecrawl** (ver 2.5) | Conveniência (markdown + cache + proxy); não é necessário aqui | Free: 1.000 créditos/mês |

Fontes (VERIFICADO em 2026-10-05): Playwright Python intro e Network — https://playwright.dev/python/docs/intro , https://playwright.dev/python/docs/network ; curl_cffi README — https://github.com/lexiforest/curl_cffi ; Crawlee Python quick start — https://crawlee.dev/python/docs/quick-start ; Scrapy overview — https://docs.scrapy.org/en/latest/intro/overview.html .

### 2.5 Firecrawl, em uma caixa (VERIFICADO em docs.firecrawl.dev e firecrawl.dev/pricing, 2026-10-05)

- Plano Free: **1.000 créditos/mês, 2 browsers concorrentes, 10 req/min em `/scrape`**; `scrape` = 1 crédito/página; formato `json` (extração por LLM com schema) = **+4 créditos/página**; `/map` = 1 crédito/chamada; `/search` = 2 créditos por 10 resultados. Parâmetro `proxy` está marcado como *deprecated* (modo `auto` tenta `basic` e cai para `enhanced` "ao mesmo custo"). Cache `maxAge` padrão de 2 dias.
- Teste real neste estudo: `formats: ["json"]` com um schema de 8 campos contra `tactics.tools/team-compositions` custou **5 créditos e devolveu 1 das 8 comps visíveis**, com itens atribuídos à unidade errada (Red Buff do Kog'Maw foi parar na Nidalee). O `markdown` (1 crédito) veio completo. Ou seja: para dados tabulares, extração por LLM é cara e pouco confiável; parsing determinístico ganha.
- Self-hosted: licença **AGPL-3.0** (SDKs em MIT), Docker Compose (api, playwright-service, Postgres, Redis); a stack padrão **não inclui** fire-engine (anti-bot), screenshots nem `actions`; extração `json` exige sua própria chave de LLM. Fontes: https://github.com/firecrawl/firecrawl , https://docs.firecrawl.dev/contributing/self-host .
- Veredito para este projeto: desnecessário. O caminho é JSON direto.

---

## 3. Caminho oficial sem scraping: Riot API + dados estáticos

### 3.1 Riot TFT API (VERIFICADO em developer.riotgames.com, 2026-10-05)

| Item | Detalhe |
| --- | --- |
| `tft-match-v1` (roteamento **regional**: `americas`, `asia`, `europe`, `sea` → `americas.api.riotgames.com`; AMERICAS cobre NA, BR, LAN, LAS) | `GET /tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=20&startTime=&endTime=` → `List[string]`; `GET /tft/match/v1/matches/{matchId}` → `MatchDto{metadata{match_id, participants[]}, info{game_datetime, game_version, tft_set_number, tft_game_type, queue_id, participants[]}}` |
| `ParticipantDto` | `placement`, `level`, `last_round`, `gold_left`, `players_eliminated`, `total_damage_to_players`, `traits[{name, num_units, style, tier_current}]`, `units[{character_id, itemNames[], tier (estrelas), rarity}]`, `puuid`, `riotIdGameName`, `win`. **Não há campo de augments.** |
| `tft-league-v1` (roteamento por **plataforma**: `br1`, `na1`, `euw1`, …) | `GET /tft/league/v1/challenger`, `/grandmaster`, `/master` (`?queue=RANKED_TFT`) → `LeagueListDTO{entries[{puuid, leaguePoints, wins, losses, rank}]}`; `GET /tft/league/v1/entries/{tier}/{division}?page=`; `GET /tft/league/v1/by-puuid/{puuid}`; `GET /tft/league/v1/rated-ladders/{queue}/top` |
| Chave **Development** | Gerada no login; **"deactivate every 24 hours"**; limites **20 req/s** e **100 req/2 min** |
| Chave **Personal** | Mesmos limites da dev key, mas não expira; "require a detailed description of the product"; "You may not run your application for public consumption using a personal key" |
| Chave **Production** | "500 requests every 10 seconds" e "30,000 requests every 10 minutes"; costuma exigir "a working prototype" |
| Política | "Products should use supported services from Riot Games for data ingestion"; aviso legal obrigatório "[Your product] isn't endorsed by Riot Games…" (já presente nos rodapés de MetaTFT e Mobalytics) |

Fontes: https://developer.riotgames.com/apis#tft-match-v1 , https://developer.riotgames.com/apis#tft-league-v1 , https://developer.riotgames.com/docs/portal , https://developer.riotgames.com/docs/lol (routing values), https://developer.riotgames.com/policies/general (atualizada em 29 mai 2025).

**Dá para computar um "meta" a partir disso num job diário?** (INFERIDO, aritmética sobre os limites verificados)

- Fluxo: `tft-league-v1/challenger` + `/grandmaster` (BR1) → lista de `puuid` → `by-puuid/{puuid}/ids?count=20` → `matches/{id}` → agrupar por conjunto de unidades (ou por trait principal + carries) → média de `placement`, Top 4 %, Win %, itens mais frequentes por unidade (`itemNames`), nível final (`level`).
- Orçamento: 100 req / 2 min = **50 req/min ≈ 3.000 req/h**. Cada partida = 1 requisição e dedup é obrigatório (8 jogadores por partida). Em 1 h de job: ~2.500 partidas únicas ≈ 20.000 tabuleiros. Suficiente para ranquear as 10–15 comps mais jogadas com colocação média estável; insuficiente para a granularidade do MetaTFT (7,48 M de comps analisadas segundo o próprio site).
- Bloqueios práticos: (a) a dev key morre em 24 h → um job diário precisa de **Personal key** (cadastro de produto, sem aprovação formal); (b) **sem augments** no DTO, logo a recomendação de tipo de augment do app teria de continuar manual ou vir de outra fonte; (c) agrupar tabuleiros em "comps" é exatamente o problema de clustering que o MetaTFT resolve com ML (`cluster_id`), e um agrupamento ingênuo por trait gera ruído; (d) `timings de nível` (LVLT) e `early boards` (BOARDS) não saem de uma partida terminada sem reconstruir a linha do tempo, que a API não dá.
- Guia da comunidade sobre crawling de partidas (seed pelo ladder vs BFS por participantes, dedup em banco): https://hextechdocs.dev/crawling-matches-using-the-riot-games-api/ (VERIFICADO; não traz aritmética de limites).

### 3.2 Dados estáticos: Data Dragon e Community Dragon (VERIFICADO por download em 2026-10-05)

| Fonte | URL | Observado |
| --- | --- | --- |
| Versões | `https://ddragon.leagueoflegends.com/api/versions.json` | Última: **16.19.1** |
| Campeões TFT | `https://ddragon.leagueoflegends.com/cdn/16.19.1/data/en_US/tft-champion.json` | 84 KB, 344 entradas (todos os sets ativos); ex.: `{"id": "DA_CrimsonRaptor18", "name": "Mama Beak", "tier": 3, "cost": 3, "image": {"full": "DA_CrimsonRaptor18.TFT_Set18.png"}}` → Set 18 presente |
| Itens / Traits / Augments | `…/tft-item.json` (299 KB), `…/tft-trait.json` (72 KB), `…/tft-augments.json` (246 KB) | Todos 200. `tft-augments.json` cobre "all non-hero augments for all active sets" |
| Community Dragon TFT | `https://raw.communitydragon.org/latest/cdragon/tft/en_us.json` (24,2 MB) e **`pt_br.json`** (23,3 MB, datado 2026-09-29) | Chaves `items`, `setData[]`, `sets`; cada `setData` tem `number`, `mutator`, `champions[{apiName, characterName, cost, icon, name, traits, ability, stats}]`, `augments[]`. Inclui variantes de modo (`TFTSet13_PAIRS`, `_TURBO`): filtrar pelo set/mutator certo |

Uso no projeto: mapear IDs (`DA_18_Zyra`) → nome em **pt-BR** (`pt_br.json`), custo, traits e ícone; e validar que os nomes das constantes `UNITS`/`COMPONENTS` do HTML batem com os oficiais. Fontes: https://developer.riotgames.com/docs/tft , https://www.communitydragon.org/documentation/assets .

---

## 4. Rodar todo dia de graça: onde e com que riscos

| Opção | Custo | Confiabilidade | Pegadinhas (VERIFICADO salvo indicação) |
| --- | --- | --- | --- |
| **GitHub Actions `schedule`** (repo público) | R$ 0 — "GitHub Actions usage is free for … public repositories" | Alta, mas não pontual: "The `schedule` event can be delayed during periods of high loads … High load times include the start of every hour" | Cron em **UTC**; intervalo mínimo 5 min; **"In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days"**; o workflow só dispara a partir do branch padrão; precisa `permissions: contents: write` para o `GITHUB_TOKEN` commitar; IPs dos runners são um pool Azure conhecido e há relatos de bloqueio por Cloudflare WAF (INFERIDO para o MetaTFT: a API respondeu ao `curl` daqui, mas não testei de um runner) |
| GitHub Actions (repo privado) | 2.000 min/mês no plano Free (Linux 1×; Windows 2×) | Idem | Um job de ~1 min/dia gasta ~30 min/mês: cabe folgado |
| **Agendador de Tarefas do Windows 11** (`schtasks /create /sc daily /st 08:00 /tn TFTMeta /tr "py C:\…\fetch.py"`) | R$ 0 | Só roda com o PC ligado (sem opção de acordar via `schtasks`; na GUI há "Wake the computer to run this task") | IP residencial raramente é bloqueado; precisa de `git push` configurado localmente para publicar o JSON |
| **Oracle Cloud Always Free** (`cron`) | R$ 0 — 2× `VM.Standard.E2.1.Micro` (AMD) ou Arm `A1.Flex` com 1.500 OCPU-h + 9.000 GB-h/mês, 200 GB de bloco, 10 TB de saída/mês | Alta, 24/7 | **Recuperação de instâncias ociosas**: Oracle pode reclamar a VM se em 7 dias CPU p95 < 20 %, rede < 20 % e memória < 20 % (A1). Um cron de 1 min/dia é "ocioso"; exige cartão no cadastro |
| Firecrawl hospedado | 1.000 créditos/mês grátis | Média (fila por concorrência de 2) | Não resolve o agendamento; ainda precisa de um cron em algum lugar |

Fontes: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows , https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions , https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions , https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create , https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm . Relatos de bloqueio Cloudflare → runners: https://github.com/snowdreamtech/bypass-cloudflare-for-github-action , https://github.com/chamirusenarath96/card-max/issues/157 (fonte secundária; INFERIDO).

Como o HTML estático consome o resultado: o job grava `data/comps.json` e faz commit; a página passa a fazer `fetch('./data/comps.json')` (ou lê um `<script src="data/comps.js">` que define `window.COMPS_DATA`, se quiser continuar abrindo via `file://` sem CORS). Hospedagem no GitHub Pages do mesmo repo fecha o ciclo sem custo.

---

## 5. Jurídico e etiqueta

| Site | robots.txt (VERIFICADO) | Termos de uso (VERIFICADO salvo indicação) | Leitura prática |
| --- | --- | --- | --- |
| MetaTFT | Tudo permitido | ToS (vigência 29 set 2026, https://www.metatft.com/tos): **nenhuma cláusula sobre scraping/robôs**. §6.1 "All content and data provided on the Platform … are the property of MetaTFT.com"; §5.1 licença do app desktop é "personal, non-exclusive … non-commercial" | Risco baixo para uso pessoal/não comercial com 1 execução/dia e atribuição. Dados são "propriedade" deles: não redistribuir o JSON bruto como se fosse seu; citar a fonte na página |
| tactics.tools | Tudo permitido | ToS (atualizado 23 ago 2021, https://tactics.tools/terms): nenhuma cláusula sobre scraping, API ou uso comercial | Risco baixo. Site mantido por doações (Patreon no rodapé): ser gentil com a frequência |
| Mobalytics | `Disallow: /api/tft` | ToS (atualizado 23 jul 2026, https://mobalytics.gg/terms/): proíbe "access or search the Services … through the use of any engine, software, tool, agent, device or mechanism (including spiders, robots, crawlers, data mining tools or the like)", "Use the Services or Content … for any commercial purpose", e "Copy, data mine, scrape … for the purpose of AI Training" | **Não usar.** Proibição explícita + Cloudflare 403 + robots |
| lolchess.gg | `Disallow: /search` | Página de termos (`/about/terms_and_service`) retornou **404** para o fetch; **não verificado** | Irrelevante: sem números úteis |
| tftactics.gg | Tudo permitido | Não consultado | Irrelevante: sem números |
| Riot Games | — | Políticas do portal: usar "supported services … for data ingestion"; aviso "isn't endorsed by Riot Games" obrigatório e visível | O app já deve exibir o aviso (os sites de referência exibem). Não há no texto lido uma proibição de scraping de **terceiros**, mas a Riot espera que produtos usem a API dela |

Etiqueta mínima para o job: 1 execução/dia (ou 2, após patch), `User-Agent` identificável com contato (ex.: `tft-guia-comp/1.0 (+github.com/<user>/<repo>)`), `timeout` e retry com backoff, respeitar `429`/`Retry-After`, cachear o último JSON bom e não quebrar a página se a fonte falhar.

---

## 6. Recomendação para este projeto

### 6.1 Opções ranqueadas

| # | Opção | O que entrega para as constantes do app | Esforço | Risco principal |
| --- | --- | --- | --- | --- |
| **1** | **MetaTFT API JSON** (`comps_data` + `comps_stats` + `comp_augment_tiers` + `unit_items_processed`) via `requests`, GitHub Actions cron diário, commit de `data/comps.json` | `COMPS.{name, tier, avg, pick, win, top4, carries, core, items, diff, lvl/roll via levelling, aug via augment tiers}`; `UNITS` (via Data Dragon); `BOARDS` possivelmente via `comp_details?comp=` (não verificado) | Baixo (1 dia) | Endpoint não documentado pode mudar/exigir token; semântica dos campos (`difficulty`, `diff_pick`) é inferida; GH runners podem ser bloqueados pelo Cloudflare → fallback Task Scheduler |
| **2** | **tactics.tools `__NEXT_DATA__`** como segunda fonte e validação cruzada | `avg/pick/win/top4`, itens por unidade (`unitItems`), `levels`, `carryUnits`, `starUnits`; **sem augments e sem nomes de comp** | Baixo | Reconstrução de nome; JSON de 650 KB por request (ok para 1×/dia); possível mudança de `buildId`/estrutura em deploys |
| **3** | **Playwright** (Python) abrindo `metatft.com/comps` e capturando o XHR com `page.expect_response("**/tft-comps-api/comps_data")` | Igual à opção 1, mas sobrevive a mudanças de headers/tokens que o browser resolve sozinho | Médio (browser no CI: `playwright install --with-deps chromium`, ~2–3 min por run) | Mais frágil (timeouts, ad-blockers, pop-ups); mais lento |
| **4** | **Riot API + CDragon** (meta próprio) | `avg/top4/win` por comp agrupada, itens por unidade, nível final; **sem augments, sem timings de estágio, sem early boards** | Alto (clustering, dedup, banco) | Chave Personal necessária; amostra pequena no limite de 100 req/2 min; qualidade inferior ao MetaTFT |
| — | Mobalytics | Rico, mas | — | **Vetado por ToS + robots + WAF** |
| — | Firecrawl (`json`) | Teste devolveu 1/8 comps por 5 créditos | — | Caro e impreciso para tabela; só faria sentido para páginas de texto |

Recomendação: implementar **1 + 2** juntas (um script, duas fontes, o app lê a primária e usa a secundária para preencher `pick`/`unitItems` e para sinalizar divergência grande em `avg`), deixar **3** pronto como fallback manual, e tratar **4** como roadmap caso o projeto queira independência total de terceiros.

### 6.2 Esquema JSON proposto para `data/comps.json`

Pensado para casar com `COMPS`, `BOARDS`, `LVLT` e `AUGS` do HTML atual (linhas 347, 688, 697 e 441 de `TFT 18.3b · Guia de escolha de comp.html`). Campos marcados `manual` continuam editados à mão (texto em pt-BR que nenhuma fonte dá).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "tft-guia-comp/comps",
  "type": "object",
  "required": ["patch", "set", "fetchedAt", "sources", "comps"],
  "properties": {
    "patch": {"type": "string", "examples": ["18.3b"]},
    "set": {"type": "integer", "examples": [18]},
    "fetchedAt": {"type": "string", "format": "date-time"},
    "sources": {"type": "array", "items": {"type": "object",
      "properties": {"name": {"enum": ["metatft", "tactics.tools", "riot"]},
                     "url": {"type": "string"}, "clusterId": {"type": "string"},
                     "rank": {"type": "string"}, "window": {"type": "string"}}}},
    "comps": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/comp"}}
  },
  "$defs": {
    "unit": {"type": "object", "required": ["id", "name"],
      "properties": {
        "id": {"type": "string", "examples": ["DA_18_Zyra"]},
        "name": {"type": "string", "description": "pt-BR via CDragon pt_br.json"},
        "cost": {"type": "integer", "minimum": 1, "maximum": 5},
        "stars": {"type": "integer", "minimum": 1, "maximum": 4, "description": "estrelas alvo (3 se em metatft.stars)"},
        "items": {"type": "array", "maxItems": 3, "items": {"type": "string"}, "description": "nomes de item; build mais frequente"},
        "carry": {"type": "boolean"}
      }},
    "comp": {"type": "object",
      "required": ["id", "name", "tier", "avg", "units"],
      "properties": {
        "id": {"type": "string", "description": "slug estável (mantém os ids atuais: azir, aph, zyra…)"},
        "sourceIds": {"type": "object", "properties": {"metatftCluster": {"type": "string"}, "tacticsCode": {"type": "string"}}},
        "name": {"type": "string"},
        "tier": {"enum": ["S", "A", "B", "C"]},
        "style": {"enum": ["fast8", "fast9", "reroll5", "reroll7", "flex"], "description": "derivado de levelling: 'Fast 8' → fast8, 'Level 7 Reroll' → reroll7"},
        "diff": {"enum": ["Fácil", "Médio", "Difícil"]},
        "avg": {"type": "number"}, "pick": {"type": "number"}, "win": {"type": "number"}, "top4": {"type": "number"},
        "games": {"type": "integer"},
        "placements": {"type": "array", "minItems": 8, "maxItems": 8, "items": {"type": "integer"}, "description": "comps_stats.places[0..7]"},
        "trend": {"type": "array", "items": {"type": "object", "properties": {"day": {"type": "string"}, "avg": {"type": "number"}, "pick": {"type": "number"}}}},
        "traits": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "count": {"type": "integer"}}}},
        "carries": {"type": "array", "items": {"type": "string"}},
        "core": {"type": "array", "items": {"type": "string"}},
        "units": {"type": "array", "items": {"$ref": "#/$defs/unit"}},
        "components": {"type": "object", "additionalProperties": {"type": "number"}, "description": "mapa componente→peso, como COMPS.items {rod, tear, …}; derivar de itens dos carries"},
        "augments": {"type": "object",
          "properties": {
            "tiers": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "tier": {"type": "string"}, "avg": {"type": "number"}}}},
            "categories": {"type": "array", "items": {"enum": ["eco", "reroll", "upg", "xp", "items", "power"]}, "description": "mapeamento manual/heurístico para AUGS do app"}
          }},
        "levelTiming": {"type": "object", "description": "LVLT",
          "properties": {"t": {"type": "array", "minItems": 5, "maxItems": 5, "items": {"type": "string"}, "examples": [["-", "2-5", "3-2", "3-6", "4-2"]]},
                         "roll": {"type": "integer"}, "source": {"enum": ["metatft", "manual"]}}},
        "boards": {"type": "array", "description": "BOARDS: tabuleiros por nível 4..8", "items": {"type": "object",
          "properties": {"level": {"type": "integer"}, "units": {"type": "array", "items": {"type": "string"}}}}},
        "manual": {"type": "object", "description": "texto pt-BR mantido à mão", "properties": {
          "when": {"type": "string"}, "how": {"type": "array", "items": {"type": "string"}}, "aug": {"type": "string"}, "spike": {"type": "string"}, "stable": {"type": "boolean"}}}
      }}
  }
}
```

Mapeamento fonte → campo (resumo): `name` ← `metatft.name_string` traduzido via CDragon (ou nome curado à mão por `id`); `avg` ← `overall.avg`; `placements` ← `comps_stats.places`; `top4` = soma(`places[0..3]`)/`count`; `win` = `places[0]`/`count`; `pick` ← `tactics.tools full.count / initialData.count` ou `metatft trends[-1].pick`; `units[].items` ← `builds[].buildName`; `units[].stars` = 3 se em `stars`; `style` ← `levelling`; `augments.tiers` ← `comp_augment_tiers.results[cluster].augments`; `tier` S/A/B/C ← faixa de `avg` (ex.: ≤ 4,10 S; ≤ 4,35 A; ≤ 4,55 B) **definida pelo projeto**, já que o MetaTFT só expõe a letra na UI (INFERIDO). `boards` e `levelTiming` ficam `manual` até confirmar o conteúdo de `comp_details?comp=`.

### 6.3 Trechos mínimos

Python `requests` contra o MetaTFT (opção 1):

```python
# fetch_metatft.py — roda 1x/dia; grava data/comps.json
import json, time, requests
from datetime import datetime, timezone

BASE = "https://api-hc.metatft.com/tft-comps-api"
H = {"User-Agent": "tft-guia-comp/1.0 (+https://github.com/<user>/<repo>)",
     "Origin": "https://www.metatft.com", "Referer": "https://www.metatft.com/"}

def get(path):
    for attempt in range(3):
        r = requests.get(f"{BASE}/{path}", headers=H, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "30"))); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError(f"falhou: {path}")

data  = get("comps_data")["results"]["data"]
stats = {s["cluster"]: s for s in get("comps_stats")["results"] if s.get("cluster")}
augs  = get("comp_augment_tiers")["results"]

comps = []
for cid, c in data["cluster_details"].items():
    pl = stats.get(cid, {}).get("places", [0]*9)
    n  = pl[8] or 1
    comps.append({
        "sourceIds": {"metatftCluster": cid},
        "name": c["name_string"],                      # traduzir via CDragon depois
        "avg": c["overall"]["avg"], "games": c["overall"]["count"],
        "win": round(100*pl[0]/n, 1), "top4": round(100*sum(pl[:4])/n, 1),
        "placements": pl[:8], "style": c.get("levelling"),
        "units": [{"id": u.strip(), "stars": 3 if u.strip() in c["stars"] else None}
                  for u in c["units_string"].split(",")],
        "builds": [{"unit": b["unit"], "items": b["buildName"], "avg": b["avg"]} for b in c["builds"]],
        "augments": {"tiers": augs.get(cid, {}).get("augments")},
    })
comps.sort(key=lambda x: x["avg"])
out = {"patch": None, "set": 18, "fetchedAt": datetime.now(timezone.utc).isoformat(),
       "sources": [{"name": "metatft", "clusterId": str(data["cluster_id"])}], "comps": comps[:12]}
json.dump(out, open("data/comps.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
```

Python `requests` contra o tactics.tools (opção 2), sem navegador:

```python
import re, json, requests
html = requests.get("https://tactics.tools/team-compositions", timeout=30,
                    headers={"User-Agent": "tft-guia-comp/1.0 (+contato)"}).text
nd = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))
groups = nd["props"]["pageProps"]["initialData"]["groups"]
for g in groups:
    f = g["full"]
    print(round(f["place"], 2), f["count"], [u for u, _ in f["carryUnits"][:2]], f["levels"])
```

Playwright (opção 3), capturando o XHR em vez de raspar o DOM:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    with page.expect_response("**/tft-comps-api/comps_data*") as resp:
        page.goto("https://www.metatft.com/comps", wait_until="domcontentloaded")
    data = resp.value.json()
```

GitHub Actions (cron diário em UTC = 06:00 BRT; `workflow_dispatch` para rodar à mão e evitar a desativação por inatividade):

```yaml
name: refresh-tft-meta
on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch:
permissions:
  contents: write
jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install requests
      - run: python fetch_metatft.py
      - run: |
          git config user.name "tft-bot" && git config user.email "bot@users.noreply.github.com"
          git add data/comps.json
          git diff --cached --quiet || git commit -m "data: meta $(date -u +%F)" && git push
```

Fallback no Windows 11 (roda só com o PC ligado):

```
schtasks /create /sc daily /st 08:00 /tn "TFT Meta" /tr "py C:\Users\Luis Caracio\Desktop\tft\fetch_metatft.py"
```

### 6.4 Riscos e mitigação

| Risco | Probabilidade | Mitigação |
| --- | --- | --- |
| MetaTFT muda rota/campos ou passa a exigir token | Média (API interna; já vi `api.metatft.com` vs `api-hc.metatft.com` coexistindo) | Validar o JSON contra o schema a cada run; se falhar, manter o último `comps.json` bom e abrir issue automática; fallback Playwright interceptando XHR |
| Runner do GitHub bloqueado por Cloudflare (403) | Baixa–média (relatos existem; a API respondeu ao `curl` residencial) | Detectar 403 e cair para a fonte 2 (tactics.tools, sem Cloudflare); ou rodar no Task Scheduler |
| Workflow desativado após 60 dias sem atividade | Certa, se o repo ficar parado | O commit diário do bot conta como atividade; ainda assim, deixar `workflow_dispatch` |
| Mudança de set/patch quebra IDs | Certa a cada set | Ler `tft_set`/`cluster_id` da resposta e `versions.json` do Data Dragon; recarregar o mapa de nomes do CDragon no mesmo job |
| Questionamento de ToS | Baixa (MetaTFT e tactics.tools não proíbem; frequência mínima; uso não comercial) | Atribuição visível ("dados: MetaTFT / tactics.tools"), 1 req/dia por endpoint, `User-Agent` com contato, nunca republicar o JSON bruto |
| Dados divergentes entre fontes | Certa (recortes de rank/dias diferentes: MetaTFT Platinum+/3 dias vs tactics.tools Diamond+) | Declarar a fonte primária na UI; usar a segunda só para campos ausentes e alerta de divergência > 0,3 em `avg` |

---

## 7. Fontes consultadas (todas em 2026-10-05)

Sites de meta (sondagem direta): https://www.metatft.com/comps · https://www.metatft.com/robots.txt · https://www.metatft.com/tos · https://tactics.tools/team-compositions · https://tactics.tools/robots.txt · https://tactics.tools/terms · https://mobalytics.gg/tft/tier-list · https://mobalytics.gg/tft/team-comps · https://mobalytics.gg/robots.txt · https://mobalytics.gg/terms/ · https://lolchess.gg/meta · https://lolchess.gg/robots.txt · https://tftactics.gg/tierlist/team-comps/ · https://tftactics.gg/robots.txt

Riot: https://developer.riotgames.com/apis#tft-match-v1 · https://developer.riotgames.com/apis#tft-league-v1 · https://developer.riotgames.com/docs/portal · https://developer.riotgames.com/docs/tft · https://developer.riotgames.com/docs/lol · https://developer.riotgames.com/policies/general · https://ddragon.leagueoflegends.com/api/versions.json · https://raw.communitydragon.org/latest/cdragon/tft/ · https://www.communitydragon.org/documentation/assets · https://hextechdocs.dev/crawling-matches-using-the-riot-games-api/

Ferramentas: https://playwright.dev/python/docs/intro · https://playwright.dev/python/docs/network · https://github.com/lexiforest/curl_cffi · https://crawlee.dev/python/docs/quick-start · https://docs.scrapy.org/en/latest/intro/overview.html · https://docs.firecrawl.dev/api-reference/endpoint/scrape · https://docs.firecrawl.dev/features/llm-extract · https://docs.firecrawl.dev/rate-limits · https://www.firecrawl.dev/pricing · https://docs.firecrawl.dev/contributing/self-host · https://github.com/firecrawl/firecrawl

Agendamento: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows · https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions · https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions · https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create · https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

Prior art (GitHub e afins): https://parse.bot/marketplace/5194af2c-7ceb-40ce-8b3f-b6f70748fa6e/metatft-com-api (wrapper pago sobre a API do MetaTFT) · https://github.com/PhucHuwu/TFT_Ranked_Data_viz (MetaTFT leaderboard API, `requests`) · https://github.com/AlexAndrasi-git/tft-meta-teamcomp-checker (Playwright/Python contra Mobalytics, agendado em GitHub Actions) · https://github.com/mk-gg/hypertft (meta próprio via Riot API, coletor diário em GitHub Actions, Cloudflare Pages) · https://github.com/Uranium2/tft_augments_helper (scraping diário de augments; cita tactics.tools/augments/gm) · https://github.com/letigredununavu/tft-scraping-bot e https://github.com/fosq/BeetleBot (lolchess: perfil de jogador e patch notes) · https://github.com/victorxia18/tft-meta-mind (stats raspadas diariamente)

## 8. O que não consegui verificar

- Parâmetros de filtro (rank, janela de dias, fila) dos endpoints do MetaTFT; e o conteúdo de `comp_details?comp=`, `comp_builds` e `comp_options` (os dois últimos têm ~5 MB e não foram analisados). Confirmar via DevTools → Network no site.
- Semântica exata de `difficulty`, `diff_pick`, `diff_place` e dos valores de `levelling` no MetaTFT (só vi "Fast 8").
- Rotas e parâmetros do host `api.tft.tools` (tactics.tools) e onde a página carrega augments.
- Termos de uso do lolchess.gg (`/about/terms_and_service` devolveu 404) e do tftactics.gg.
- Se os IPs dos runners do GitHub Actions passam pelo Cloudflare na frente de `api-hc.metatft.com` (só testei de IP residencial).
- A aritmética de "partidas por dia" com chave Personal da Riot é inferida dos limites publicados; não rodei um coletor.
- O resultado de `formats: ["json"]` do Firecrawl foi observado uma única vez (1 de 8 comps); pode variar entre execuções.
