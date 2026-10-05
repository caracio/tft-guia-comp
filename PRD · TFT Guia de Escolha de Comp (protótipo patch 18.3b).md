# PRD · TFT Guia de Escolha de Comp (protótipo patch 18.3b)

Oct 5, 2026 · @Luis Caracio

## 1. Visão geral

O protótipo é uma página web única que ajuda o jogador de TFT a escolher entre as 6 melhores comps do patch 18.3b a partir dos bonecos, itens e situação que ele tem na partida. Este PRD descreve comportamento, dados e estrutura para que um redesign visual seja aplicado por cima sem alterar a lógica.

**Problema.** No estágio 2 o jogador precisa escolher comps sob pressão de tempo, com muitos bonecos parecidos entre comps e sem um critério fixo. O resultado é rolar ouro sem direção.

**Objetivo.** Dar um Plano A, B e C em poucos toques, explicando o porquê, e orientar o que fazer em cada estágio (subir de nível, juntar ouro, rolar) e que tipo de augment pegar.

**Usuário.** Jogador de TFT de nível intermediário, jogando no celular ou em segunda tela durante a partida. Usa uma mão, tem poucos segundos por rodada e não digita.

**Princípios de produto**

- Tocar, não digitar: toda entrada é um toque em tile, chip ou botão segmentado.
- Resposta imediata: qualquer toque recalcula o resultado na hora.
- Explicável: toda recomendação mostra os sinais que a causaram.
- Escolher três comps: o app sempre mostra Plano A, B e C, nunca uma única resposta.
- Ensinar o critério: o objetivo é o jogador aprender a escolher sozinho, não depender do app.

## 2. Escopo e métricas

O escopo cobre 5 telas de consulta e decisão, sem conta de usuário e sem dados em tempo real.

| Dentro do escopo | Fora do escopo |
| --- | --- |
| Ranking de 6 comps com Plano A, B e C | Integração com o cliente ou API do jogo |
| Marcação de bonecos (1★ a 3★), rivais contestando e componentes | Login, sincronização entre dispositivos |
| Situação (vida e ouro) e checklist do 2-1 | Dados de patch em tempo real (valores fixos do patch 18.3b) |
| Boards de early por nível (4 a 8) e ações por estágio | Nomes e lista exata de augments e itens completos |
| Recomendação de tipo de augment por comp | Imagens oficiais dos campeões |
| Fichas das 6 comps e guia de estágios | Histórico de partidas |
| Tema claro e escuro, persistência local | Idiomas além do português do Brasil |

**Métricas de sucesso propostas** (a validar com uso real):

- Do primeiro toque ao Plano A visível: 1 toque.
- Toques para marcar 5 bonecos e ver o resultado: até 6.
- O jogador consegue responder ao checklist do 2-1 em menos de 10 segundos.
- Pelo menos 80% das sessões usam mais de uma aba (Escolher e Earlys).

## 3. Arquitetura de informação

O app tem uma barra superior fixa e 5 abas; só uma aba fica visível por vez e a aba ativa é lembrada ao reabrir.

| Aba | Rótulo atual | Função | Quando o jogador usa |
| --- | --- | --- | --- |
| pick | Escolher comp | Entrada de dados e resultado Plano A/B/C | Todo estágio 2, a cada nova informação |
| early | Earlys | Boards por nível e ação por estágio | Ao subir de nível, para conferir o board |
| aug | Augments | Qual tipo de augment pegar | Quando a tela de augments aparece |
| comps | As 6 comps | Ficha detalhada de cada comp | Para entender uma comp antes de se comprometer |
| guide | Guia | Resumo de estratégia por estágio | Antes da partida |

**Elementos globais**

- Cabeçalho fixo: título, "Novo jogo" (limpa tudo após confirmar), alternar tema, abas rolando na horizontal quando faltar espaço.
- Barra inferior (somente celular, somente aba Escolher): mostra "A: ... · B: ..." e rola até o resultado.
- Links cruzados: do resultado ou das fichas, "Ver como jogar esta comp" abre a aba As 6 comps e rola até o cartão.
- Os dados marcados (bonecos, itens, situação) são compartilhados entre todas as abas.

## 4. Requisitos funcionais por tela

### 4.1 Escolher comp

Tela em duas colunas no desktop (entradas à esquerda, resultado fixo à direita) e uma coluna no celular.

| ID | Requisito |
| --- | --- |
| E-01 | Grade com todos os bonecos únicos das 6 comps (46 hoje), em ordem alfabética, rolável dentro de um quadro de altura máxima de 430 px. |
| E-02 | Tocar num boneco no modo "Eu tenho" cicla 1★, 2★, 3★ e remove. A estrela aparece no canto do tile. 3★ ganha destaque extra. |
| E-03 | Seletor de modo: "Eu tenho" ou "Rivais estão pegando". No segundo, o toque liga e desliga a marca de contestado (borda tracejada e ícone). Um boneco pode ser seu e contestado ao mesmo tempo. |
| E-04 | Busca por nome e filtros: Todos, Frontline/Vi, Invoker, Reroll, Só os meus. |
| E-05 | Cada tile mostra pontos coloridos das famílias de comp que usam o boneco e uma legenda explica as cores. |
| E-06 | Grade de 9 componentes de item. Cada toque soma 1, de 1 a 4, e volta a 0. O contador aparece no canto. |
| E-07 | Situação: vida (alta, média, baixa) e ouro (pouco, médio, muito) como seletores segmentados. Padrão: média e médio. |
| E-08 | Checklist do 2-1 com 3 perguntas Sim/Não. Tocar na resposta ativa a desmarca. Com 2 ou mais "sim": "Suba para o nível 4". Com menos: "Fique no nível 3". Sem 3 respostas: pede para responder. |
| E-09 | Resultado: caixa "Próxima ação" com título, texto e nível de confiança, e 3 cartões (Plano A, B, C). |
| E-10 | Cada cartão mostra nome, família, estilo, dificuldade, tier, barra de pontuação, motivos (bonecos, componentes, contestação, situação) e tags de média, top 4 e win rate. |
| E-11 | Lista recolhível "Ver as outras 3 comps" com pontuação. Aviso quando há bonecos contestados. |
| E-12 | Sem nenhum dado marcado, o resultado mostra o ranking base pelo meta e a instrução "Toque nos bonecos…". |

### 4.2 Earlys

| ID | Requisito |
| --- | --- |
| Y-01 | Seletor de 6 estágios: Estágio 1, Nível 4, 5, 6, 7 e 8, cada um com o momento típico (por exemplo, \~2-1). Padrão: Nível 4. |
| Y-02 | Para cada estágio, duas listas curtas: "Foque em" e "Evite", e uma nota extra quando existir. |
| Y-03 | Estágio 1: lista de peças flexíveis (presentes em 2 ou mais comps, com ×N) e os boards de nível 4 de cada comp. |
| Y-04 | Níveis 4 a 7: um cartão por comp com round win do nível (verde 60% ou mais, amarelo 45% ou mais, vermelho abaixo), contagem "Você tem X/Y" e o board em chips. |
| Y-05 | Nível 8: o cartão mostra o board final no lugar do round win. |
| Y-06 | Cada cartão mostra uma ação: "Role agora" (nível de rolagem da comp), "Junte ouro" (antes) ou "Complete o board" (depois), com o momento de subir de nível. |
| Y-07 | Os chips são tocáveis e usam o mesmo estado da aba Escolher (1★, 2★, 3★, remove). Rivais aparecem tracejados. |
| Y-08 | Ordenação: pelo que o jogador tem; sem bonecos marcados, pela força no nível. Prefixo A, B ou C no cartão quando a comp está entre os 3 planos. |

### 4.3 Augments

| ID | Requisito |
| --- | --- |
| A-01 | Escolha da comp alvo: "Automático" (Plano A atual) ou uma das 6. |
| A-02 | 8 tipos de augment em tiles: Economia, Reroll/Loja, Upgrade de unidade, XP/Nível, Itens, Poder imediato, Sobrevivência, Emblema/Trait. |
| A-03 | Seleção de até 3 tipos; ao escolher o quarto, o mais antigo sai. |
| A-04 | Veredito ordenado do melhor ao pior com rótulo (Pegue, Bom, Ok, Evite) e uma frase de motivo. O primeiro leva um destaque "👉". |
| A-05 | Tabela comparativa 8×6 com notas de 0 a 3, ajustadas pela vida. |

### 4.4 As 6 comps e Guia

- Fichas filtráveis por família. Cada ficha traz estatísticas, quando ir, round win por nível, bonecos de início, board final com carries destacados, como jogar, níveis, tipos de augment e aviso.
- O Guia é conteúdo estático: antes do jogo, estágios 1 e 2, as 3 famílias, reroll ou Fast 8, economia e saúde do jogo.

### 4.5 Globais

- "Novo jogo" pede confirmação e zera bonecos, itens, situação, checklist, augments e estágio.
- O estado é salvo a cada toque e restaurado ao reabrir; a falha de armazenamento não pode quebrar o app.

## 5. Modelo de dados e conteúdo

Todo o conteúdo vem de constantes no código, extraídas dos prints do Meta TFT (patch 18.3b). Atualizar o patch significa editar essas constantes, sem mexer na interface.

| Entidade | Campos principais |
| --- | --- |
| Comp (6) | id, nome, tier (S ou A), família (A, B, C), estilo, dificuldade, spike, média, top 4, win, pick, round win por nível (4 a 7), texto de níveis, texto de rolagem, carries, bonecos de early, board final, pesos de item, flag de estável, quando ir, como jogar, augments, aviso |
| Boneco (derivado) | nome, famílias, peso por comp (carry 3, early 2, board final 1,5; vale o maior) |
| Componente de item (9) | id, ícone, nome |
| Tipo de augment (8) | id, ícone, nome, descrição |
| Estilo (4) | reroll no lvl 5, reroll no lvl 7, Fast 8, Fast 8 com early fraco; nota de 0 a 3 por tipo de augment |
| Boards (6×4) | lista de bonecos do early em cada nível 4 a 7, por comp |
| Níveis por comp | momento de subir de nível (4 a 8) e nível de rolagem |
| Estágio (6) | rótulo, momento típico, nível, listas "foque em" e "evite", nota extra |

**Estado do usuário (salvo no navegador)**

| Campo | Tipo | Padrão |
| --- | --- | --- |
| owned | boneco → estrelas (1 a 3) | vazio |
| cont | boneco → verdadeiro | vazio |
| items | componente → quantidade (0 a 4) | vazio |
| hp, gold | alta/média/baixa, pouco/médio/muito | média, médio |
| checks | 3 valores: 1, 0 ou nulo | nulos |
| mode, fam, q | modo de toque, filtro, busca | Eu tenho, Todos, vazio |
| augComp, augSel | comp alvo, até 3 tipos | automático, vazio |
| tab, stage | aba e estágio ativos | Escolher, Nível 4 |

**As 6 comps (valores do Meta TFT)**

| Comp | Tier | Família | Estilo | Dificuldade | Média | Top 4 % | Win % | Pick rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Flora Fatalis Azir | S | Reroll | Reroll no lvl 7 | Fácil | 4,05 | 58,2 | 16,3 | 0,45 |
| Lunar Aphelios Nidalee | S | Frontline/Vi | Fast 8 | Médio | 4,16 | 58,9 | 9,1 | 0,64 |
| Spellweaver Veigar | A | Reroll | Reroll no lvl 5 | Difícil | 4,27 | 54,5 | 14,4 | 0,44 |
| Invoker Morgana Sentinel | A | Invoker | Fast 8 (early fraco) | Fácil | 4,30 | 53,3 | 14,3 | 0,10 |
| Juggernaut Zyra Sivir | A | Frontline/Vi | Fast 8 | Médio | 4,31 | 52,9 | 14,5 | 0,41 |
| Invoker Ahri | A | Invoker | Fast 8 (early fraco) | Médio | 4,31 | 54,2 | 12,1 | 0,36 |

## 6. Regras de pontuação e recomendação

A pontuação de cada comp é a soma de cinco termos, e o redesign não deve alterá-la. Os pesos são uma heurística construída a partir dos prints, não dados oficiais.

```latex
\text{pontos} = \sum_{b} e(b) \cdot w(b) + 0{,}9 \sum_{i} \min(q_i,4)\, p(i) - \text{contestação} + \text{situação} + 3\,(4{,}5 - \text{média})
```

| Termo | Regra |
| --- | --- |
| Bonecos | Estrelas e(b): 1★ vale 1, 2★ vale 3, 3★ vale 5. Multiplica pelo peso w(b) do boneco na comp (carry 3, early 2, board final 1,5). |
| Itens | Para cada componente com peso p(i) na comp, quantidade limitada a 4, vezes 0,9. |
| Contestação | Subtrai o peso do boneco vezes 3 se for carry da comp, ou vezes 1,5 nos demais. |
| Situação | Ver tabela abaixo. |
| Base do meta | 3 × (4,5 − média de colocação). Só desempata quando não há sinais. |

**Ajustes de situação**

| Condição | Efeito |
| --- | --- |
| Vida baixa | Comp estável (Azir, Aphelios, Veigar) +3; as demais −3 |
| Vida alta e ouro muito | Fast 8: +2,5 |
| Ouro muito (sem vida alta) | Fast 8: +1,5 |
| Ouro pouco | Veigar +1; Invoker −1 |

**Pesos de item por comp** (tendência por tipo de dano)

| Comp | Componentes e peso |
| --- | --- |
| Azir | Vara 2, Lágrima 1,5, Luvas 1, Manto 0,5, Espátula 0,5 |
| Aphelios | Arco 2, Espada 2, Luvas 1,5, Colete 0,5, Espátula 0,5 |
| Zyra | Vara 1, Arco 1, Lágrima, Espada, Luvas, Cinto, Colete e Espátula 0,5 |
| Veigar | Vara 2, Lágrima 1,5, Luvas 1, Manto 0,5, Espátula 0,5 |
| Ahri | Vara 2, Lágrima 2, Manto 1, Luvas 0,5, Espátula 0,5 |
| Morgana | Colete 1,5, Cinto 1,5, Manto 1, Vara 1, Lágrima 1, Espátula 0,5 |

**Ranking e confiança**

- Ordem decrescente de pontos; Plano A, B e C são as 3 primeiras.
- A barra mostra pontos ÷ o maior entre 12 e a pontuação do Plano A, com mínimo de 4% de largura.
- Confiança pela diferença entre A e B: 6 ou mais é forte, de 2,5 a 6 é média, abaixo é baixa (neste caso o texto manda manter 3 opções abertas).
- Sem bonecos nem componentes marcados, a tela mostra o ranking base e a instrução inicial.

**Regras de augment**

- Cada estilo tem nota de 0 a 3 por tipo; Aphelios sobrescreve Economia e Itens para 3.
- Vida baixa: Sobrevivência e Poder +1 (máximo 3) e Economia −1 (mínimo 0). Vida alta com ouro não baixo: Economia +0,5.
- A nota final é arredondada; 3 = Pegue, 2 = Bom, 1 = Ok, 0 = Evite.

| Estilo | Eco | Reroll | Upgrade | XP | Itens | Poder | Sobrev. | Emblema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reroll no lvl 5 | 1 | 3 | 3 | 0 | 2 | 2 | 1 | 1 |
| Reroll no lvl 7 | 2 | 3 | 3 | 1 | 2 | 1 | 1 | 1 |
| Fast 8 | 3 | 0 | 1 | 3 | 2 | 1 | 2 | 2 |
| Fast 8, early fraco | 2 | 0 | 1 | 2 | 2 | 3 | 3 | 2 |

## 7. Inventário de UI e tokens atuais

O visual atual é deliberadamente neutro (cartões, bordas finas, cor por família). Esta seção lista o que existe para o redesign trocar peça por peça.

**Componentes**

| Componente | Onde aparece | Estados que precisam de design |
| --- | --- | --- |
| Cabeçalho fixo e abas | Todas | Aba ativa, rolagem horizontal, foco |
| Botão simples | Novo jogo, Tema | Padrão, hover, foco |
| Controle segmentado | Modo, vida, ouro, Sim/Não, estágio | Selecionado, não selecionado; variante vermelha para "Rivais" |
| Chip de filtro | Famílias, comp alvo | Ativo, inativo |
| Cartão de seção com número de passo | Escolher (passos 1 a 4) | Padrão |
| Tile de boneco | Escolher | Normal, meu (1★, 2★, 3★), contestado, ambos |
| Tile de componente | Escolher | Normal, com contador (1 a 4) |
| Linha de pergunta | Checklist | Sim, Não, vazio |
| Faixa de veredito | Checklist | Suba, Fique, aguardando |
| Caixa "Próxima ação" | Resultado | Inicial, confiança forte, média, baixa |
| Cartão de plano (A, B, C) | Resultado | A em destaque, B e C neutros |
| Barra de pontuação | Resultado | 4% a 100% |
| Selo de tier e tags | Resultado, fichas | S, A; tags de família |
| Barra inferior | Escolher, celular | Com e sem dados |
| Chip de boneco compacto | Earlys | Normal, meu, contestado |
| Cartão de comp por nível | Earlys | Melhor round win, ação Role / Junte ouro / Complete |
| Tile de augment e linha de veredito | Augments | Selecionado, rótulos Pegue, Bom, Ok, Evite |
| Tabela de notas | Augments | Cores de nota 0 a 3 |
| Ficha de comp | As 6 comps | Estatísticas, mini chips, carry destacado, aviso |

**Tokens de cor atuais**

| Token | Claro | Escuro |
| --- | --- | --- |
| Fundo | #eef1f6 | #0e1320 |
| Painel | #ffffff | #171e30 |
| Painel secundário | #f4f6fa | #1e2740 |
| Linha | #d6dce8 | #2b3654 |
| Texto | #1b2233 | #e8ecf7 |
| Texto suave | #5d6980 | #97a3c0 |
| Destaque | #2f5bea | #6f93ff |
| Família A (Frontline/Vi) | #d97b00 | #ffb04a |
| Família B (Invoker) | #8a45d6 | #c196ff |
| Família C (Reroll) | #0f9d7a | #45d9b0 |
| Bom | #12915a | #4ad991 |
| Atenção | #c77700 | #ffb04a |
| Ruim | #c93a3a | #ff7b7b |

**Tipografia, forma e espaço**

- Fonte do sistema, 16 px no corpo; títulos de seção 1,15 rem; rótulos pequenos de 0,72 a 0,9 rem.
- Raio de borda: 10 px em botões e campos, 12 px em tiles, 14 px em cartões, 999 px em chips.
- Espaçamento base de 8 px, com 14 px de padding em cartões.
- Avatar do boneco: círculo com iniciais e cor gerada a partir do nome (matiz de 0 a 359, saturação 55%, luminosidade 42%).

**Pontos onde o redesign tem mais ganho**

- Os ícones são emojis (abas, componentes de item, tipos de augment). Substituir por um conjunto de ícones SVG próprio.
- Os avatares usam iniciais porque imagens externas são bloqueadas; o redesign pode embutir imagens como dados na própria página.
- A cor da família (A, B, C) é o único código visual entre comps; reforçar com forma ou ícone ajuda daltônicos.

## 8. Responsividade, acessibilidade e requisitos não funcionais

O app precisa funcionar com uma mão no celular e em uma segunda tela no desktop, e essas regras valem também depois do redesign.

| Largura | Comportamento atual |
| --- | --- |
| Acima de 900 px | Escolher em 2 colunas; resultado fixo à direita; sem barra inferior |
| Até 900 px | 1 coluna; resultado abaixo das entradas; barra inferior fixa na aba Escolher |
| Até 640 px | Listas "Foque em / Evite" empilhadas |
| Até 420 px | Grades de cartões em 1 coluna |

**Acessibilidade**

- Botões de alternância usam `aria-pressed`; abas usam `aria-selected`; tiles têm `aria-label` com nome, estrelas e contestado.
- Foco visível de 3 px em todos os elementos interativos.
- Respeitar redução de movimento: sem transição quando solicitada.
- Alvos de toque de pelo menos 44 px (hoje parte dos botões segmentados fica um pouco abaixo; o redesign deve corrigir).
- Contraste mínimo de 4,5:1 para texto; validar de novo as cores de família sobre os fundos de tag.
- Nunca usar só a cor para dizer algo: o contestado já usa borda tracejada e ícone, e as famílias devem ganhar um segundo sinal.

**Temas e área segura**

- Tema claro e escuro seguem o sistema, com botão para alternar manualmente.
- Respeitar as áreas seguras do celular (topo e rodapé) no cabeçalho fixo e na barra inferior.

**Não funcionais**

- Desempenho: cada toque recalcula e redesenha as áreas visíveis; o conjunto de dados cabe em memória e a resposta deve ser imediata em celulares de entrada.
- Persistência: armazenamento local do navegador, uma chave, privado por dispositivo; qualquer falha é ignorada sem erro visível.
- Rede: nenhuma chamada externa; funciona offline depois de carregado.
- Idioma: português do Brasil, textos curtos, frases com menos de 25 palavras.

## 9. Restrições técnicas e guia de implementação do redesign

O app é um único arquivo HTML com CSS e JavaScript embutidos, publicado como artefato. Para aplicar o redesign por cima, troque o CSS e os modelos de HTML sem renomear os ganchos que a lógica usa.

**Restrições do ambiente de publicação**

- Um só arquivo, até 16 MB, com imagens e fontes embutidas como dados.
- Scripts externos só de cdnjs.cloudflare.com, cdn.jsdelivr.net/npm, cdn.tailwindcss.com e code.jquery.com, em versão fixa; estilos externos só do Google Fonts. Qualquer outra origem falha em silêncio.
- Sem imagens remotas e sem chamadas de rede para outros sites.
- Manter `viewport-fit=cover`, o espaçamento de área segura e as variáveis de tema com os três blocos (claro, escuro pelo sistema, escuro manual).
- Armazenamento local sempre dentro de try/catch.

**Ganchos que não podem mudar**

| Tipo | Nomes |
| --- | --- |
| Atributos de dados | `data-tab`, `data-u`, `data-eu`, `data-it`, `data-hp`, `data-gold`, `data-mode`, `data-fam`, `data-ck` com `data-v`, `data-open`, `data-ac`, `data-ag`, `data-cf`, `data-stage` |
| IDs de contêiner | `#units`, `#items`, `#results`, `#checks`, `#checkVerdict`, `#hpSeg`, `#goldSeg`, `#modeSeg`, `#famChips`, `#q`, `#stageSeg`, `#stageBody`, `#augComp`, `#augTypes`, `#augVerdict`, `#augTable`, `#compFam`, `#compCards`, `#v-guide`, `#dockBtn`, `#dockText`, `#btnReset`, `#btnTheme` |
| Visões | `#v-pick`, `#v-early`, `#v-aug`, `#v-comps`, `#v-guide` (classe `on` mostra a visão) |

**Como a interface é montada**

- As funções `renderUnits`, `renderItems`, `renderSit`, `renderChecks`, `renderResults`, `renderEarly`, `renderAug`, `renderComps` e `renderGuide` escrevem HTML em texto dentro dos contêineres acima.
- As classes de estado (`own`, `own3`, `cont`, `has`, `best`, `roll`, `up`) são aplicadas por esses modelos; o redesign pode estilizá-las ou editar os modelos.
- Os dados (`COMPS`, `BOARDS`, `LVLT`, `STYLE`, `AUGS`, `COMPONENTS`, `STAGES`, `STIPS`) ficam separados da interface e não devem ser tocados no redesign.

**Ordem sugerida de trabalho**

1. Definir novos tokens (cor, tipografia, raio, espaço) mantendo os nomes de variável, claro e escuro.
2. Redesenhar o cabeçalho, as abas e a barra inferior.
3. Redesenhar tile de boneco e tile de componente (a parte mais tocada).
4. Redesenhar os cartões de plano e a caixa Próxima ação.
5. Trocar os emojis por ícones.
6. Redesenhar Earlys, Augments, fichas e Guia.
7. Revisar acessibilidade (alvos de 44 px, contraste, foco) e conferir em 375, 768 e 1280 px de largura.

## 10. Critérios de aceite, riscos e roadmap

O redesign está pronto quando todo o comportamento atual continua igual e os itens abaixo passam.

**Critérios de aceite**

- [ ] Tocar num boneco cicla 1★, 2★, 3★ e remove, e o resultado muda na hora.
- [ ] O modo "Rivais estão pegando" marca contestado sem apagar o que o jogador tem.
- [ ] Plano A, B e C aparecem com motivos, e o aviso de contestação surge quando houver marcas.
- [ ] O checklist do 2-1 mostra as três mensagens (aguardando, suba, fique).
- [ ] Em Earlys, os 6 estágios mostram o conteúdo certo e os chips compartilham o estado com a aba Escolher.
- [ ] Em Augments, a seleção de 3 tipos funciona com troca do mais antigo e a tabela reflete a vida.
- [ ] "Novo jogo" confirma e zera tudo; reabrir o app restaura o último estado.
- [ ] Tema claro, escuro e automático funcionam em todas as telas.
- [ ] Sem rolagem horizontal da página em 375, 768 e 1280 px; tabelas rolam dentro do próprio quadro.
- [ ] Alvos de toque de 44 px, foco visível e contraste de 4,5:1 conferidos.

**Riscos**

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Renomear ganchos (IDs e atributos de dados) | Quebra a lógica | Manter a lista da seção 9 e testar cada aba |
| Pesos de pontuação não validados | Recomendações ruins | Marcar como heurística; revisar com partidas reais |
| Dados fixos do patch 18.3b | Ficam velhos no próximo patch | Isolar dados em constantes e atualizar por patch |
| Imagens pesadas embutidas | Página lenta, limite de 16 MB | Usar SVG e imagens pequenas |
| Layout denso no celular | Erros de toque durante a partida | Alvos de 44 px e testes em tela pequena |

**Pontos em aberto**

- A unidade do pick rate no Meta TFT (valores como 0,45) não está confirmada; hoje o app mostra o número seguido de "%".
- Os itens exatos de cada comp não foram lidos dos prints; os pesos de item são por tipo de dano.
- Os momentos de subir de nível variam por partida; o app mostra os valores típicos do site.

**Roadmap sugerido**

1. Lista de itens completos por comp (a partir da aba Units & Items).
2. Nomes de augments recomendados por comp.
3. Atualização de dados por patch em um arquivo à parte.
4. Imagens dos campeões embutidas.
5. Histórico das últimas partidas com a comp escolhida e a colocação.

**Fontes**

- Prints do Meta TFT com as 6 comps de maior média no patch 18.3b, enviados pelo usuário.
- Resumo do vídeo sobre estágios 1 e 2, enviado pelo usuário (checklist do 2-1, três comps, scouting, economia dinâmica).
