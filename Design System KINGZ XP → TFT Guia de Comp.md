# Design System KINGZ XP → TFT Guia de Comp

Oct 5, 2026 · @Luis Caracio

## Visão geral

Este documento traduz o visual do painel gamer "KINGZ XP" (screenshot enviado) em tokens, componentes e specs prontos para vestir o protótipo descrito no PRD TFT Guia de Comp, sem mudar lógica, dados nem ganchos.

| Item | Decisão |
| --- | --- |
| Fonte visual | Screenshot 1024×768 px; cores amostradas por pixel e corrigidas onde falham em contraste |
| Esqueleto | PRD TFT Guia de Comp, seções 7 (inventário e tokens), 8 (responsividade e acessibilidade) e 9 (ganchos) |
| Tema principal | Escuro, fiel à referência; tema claro derivado para cumprir o PRD |
| Fora deste documento | Código final da aplicação (será feito em outro chat) |

**Como usar no outro chat.** Cole ou anexe este documento junto com o PRD. A ordem de aplicação está na seção Handoff e segue a ordem de trabalho do PRD (tokens, cabeçalho, tiles, cartões de plano, ícones, demais telas).

**Regras herdadas do guia figma-design-to-code (adaptadas a um screenshot, sem arquivo Figma).**

- O screenshot é o alvo visual, nunca um ativo: nenhuma imagem dele entra no código.
- O layout absoluto da referência vira layout nativo (grid e flex), respeitando os breakpoints do PRD.
- Reaproveitar os modelos de HTML e classes de estado do app (`own`, `own3`, `cont`, `has`, `best`, `roll`, `up`) em vez de recriar componentes.
- Valores sem fonte exata são marcados como estimativa; nenhum ativo protegido (arte de campeão, logos de jogos) é copiado.

## Crítica do design de referência

A referência tem uma linguagem forte e reaproveitável (painéis escuros em camadas, um único laranja de marca, selos coloridos), mas falha em contraste de texto secundário e em alvos de toque; esses pontos são corrigidos nos tokens antes de chegar ao app.

**Primeira impressão.** O olho vai primeiro ao banner e depois aos selos hexagonais coloridos; o laranja marca só o essencial (logo, aba ativa, itens bloqueados). No app TFT, o ponto focal equivalente deve ser a caixa Próxima ação e o cartão do Plano A, não um banner decorativo.

**Usabilidade**

| Achado | Severidade | Recomendação para o app |
| --- | --- | --- |
| Texto secundário cinza (\~#5a5e6b) sobre painel #0d1018 mede \~2,9:1 | Crítico | Subir para #8b90a0 (5,97:1) |
| Branco sobre laranja #f1460f mede 3,73:1 na aba ativa | Crítico | Fundo #c2380a com texto branco (5,43:1) ou texto #0b0d12 sobre #f1460f (5,2:1) |
| Botões de ícone e pílulas com \~28–32 px de altura | Crítico | Mínimo de 44 px em toque, mantendo o desenho visual menor dentro da área |
| Itens de navegação inativos quase invisíveis (\~2:1) | Moderado | Ícone e rótulo em #8b90a0; ativo com fundo de marca |
| Estado "bloqueado" depende de laranja e opacidade | Moderado | Sempre com ícone de canto e borda; no app vira "contestado" com borda tracejada |
| Selos coloridos se distinguem só pela cor em alguns pares (vermelho e rosa) | Menor | Usar forma e ícone diferentes por categoria |

**Hierarquia visual**

- Leitura em Z: cabeçalho, abas, banner, faixa de perfil, grade de cartões; coluna lateral fixa à direita com a lista de desafios.
- Ênfase por luminância: fundo #07080c, cartão #0d1018, item interno #12151f, controle #1b1e2a. Isso substitui sombras.
- Títulos de cartão em branco 600, descrições em cinza pequeno; números de estatística em ciano destacam o dado.

**Consistência**

| Elemento | Problema | Correção |
| --- | --- | --- |
| Tags | "EXPIRING SOON" preenchida, "COMPLETED" contornada | Padronizar: tag sólida suave (fundo 16% da cor, borda 40%, texto cheio) |
| Raios | Abas, pílulas e cartões variam de 6 a 12 px sem regra visível | Escala fixa de 4 raios (seção Tokens) |
| Texto | "Challanges" grafado errado na referência | Ignorar; o app usa os textos do PRD |

**O que funciona bem e vale adotar**

- Camadas de painel por luminância, sem sombras: leve e legível em segunda tela.
- Laranja reservado para foco e estado: casa com o "Plano A em destaque" do PRD.
- Cartão de progresso com estado concluído (roxo, brilho) versus bloqueado (laranja, canto com ícone): modelo direto para tile de boneco "meu" versus "contestado".
- Linha de desafio (miniatura, título, descrição, tag, tempo): modelo direto para cartão de comp por nível e linhas de veredito.

**Prioridades**

1. Corrigir contraste e alvos de toque nos tokens, antes de qualquer componente.
2. Mapear estados de tile (meu, contestado, ambos) para os padrões concluído e bloqueado.
3. Trocar emojis por ícones de traço único, como os da referência.

## Usuário e contexto

Não há pesquisa com usuários reais ainda; esta seção usa o perfil do PRD como proto-persona e define o que validar depois que o visual for aplicado.

**Proto-persona (PRD, seção 1).** Jogador intermediário de TFT, no celular ou em segunda tela, uma mão livre, poucos segundos por rodada, não digita.

**Job to be done.** "Quando estou no estágio 2 com bonecos espalhados, quero ver em um toque qual comp seguir e por quê, para não rolar ouro sem direção."

**Implicações para o visual**

| Necessidade do usuário | Decisão de design |
| --- | --- |
| Ler de relance em segunda tela, ambiente escuro | Tema escuro como padrão; números grandes e em ciano; Plano A com o maior peso visual da tela |
| Toque com uma mão, sob pressão | Alvos de 44 px; controles segmentados largos; barra inferior com o resumo A e B ao alcance do polegar |
| Muitos bonecos parecidos | Tiles quadrados com iniciais grandes e borda de estado clara; estrelas no canto |
| Entender o porquê | Motivos como tags curtas abaixo do cartão, no mesmo padrão das tags da referência |
| Daltonismo (PRD, seção 8) | Família = cor + forma do selo + rótulo; contestado = borda tracejada + ícone |

**Validação depois da aplicação (teste de usabilidade, 5 jogadores, sessões de 20 min)**

- [ ] Tarefa 1: marcar 5 bonecos e dizer qual é o Plano A. Meta: até 6 toques e menos de 15 s.
- [ ] Tarefa 2: marcar um boneco contestado e explicar o que mudou. Meta: 4 de 5 percebem o aviso sem ajuda.
- [ ] Tarefa 3: responder o checklist do 2-1. Meta: menos de 10 s (métrica do PRD).
- [ ] Tarefa 4: achar o tipo de augment a pegar para o Plano A. Meta: 4 de 5 sem erro.
- [ ] Pergunta final: "O que você olharia primeiro durante a partida?" A resposta esperada é Próxima ação ou Plano A.

## Tokens

Os 13 tokens de cor do PRD ganham novos valores e entram 6 tokens novos; todos os pares de texto foram conferidos em 4,5:1 ou mais sobre o painel.

**Cor: tokens existentes do PRD (manter os nomes de variável atuais do código)**

| Token do PRD | Escuro (padrão) | Claro | Origem na referência |
| --- | --- | --- | --- |
| Fundo | #07080c | #f5f6f9 | Fundo do shell do app |
| Painel | #0d1018 | #ffffff | Cartões About me, Achievements |
| Painel secundário | #12151f | #eef0f5 | Itens da lista Daily Challenges |
| Linha | #1f2330 | #dfe2ea | Divisórias finas (estimativa) |
| Texto | #f5f7fb | #11131a | Títulos de cartão |
| Texto suave | #8b90a0 | #5a5f6e | Descrições, corrigido de \~#5a5e6b |
| Destaque | #f1460f | #c2380a | Laranja da marca (aba ativa, cadeado) |
| Família A (Frontline/Vi) | #f4b740 | #b45309 | Selo dourado |
| Família B (Invoker) | #b06cff | #7c3aed | Selo e card Diamonds roxo |
| Família C (Reroll) | #2fd6a8 | #0f766e | Derivado do verde-azulado do banner |
| Bom | #b4f24e | #4d7a00 | Badge de nível e COMPLETED |
| Atenção | #ff9a3d | #b45309 | Derivado do laranja |
| Ruim | #ff6b6b | #b0164d | Tag EXPIRING SOON |

**Cor: tokens novos**

| Token novo | Escuro | Claro | Uso |
| --- | --- | --- | --- |
| Controle | #1b1e2a | #e6e9f0 | Botões secundários, pílulas, trilho de barra |
| Destaque preenchido | #c2380a | #c2380a | Fundo de aba ativa e segmento selecionado com texto branco (5,43:1) |
| Informação | #3fb8ec | #08729e | Números de estatística, borda do botão contornado, ponto de notificação |
| Moeda / premium | #9a6bff sobre #1d1a36 | #6a2fd6 sobre #efe9ff | Pílula de saldo, cartão concluído |
| Ruim preenchido | #9b1b48 | #b0164d | Segmento "Rivais", tag de alerta com texto branco |
| Borda sutil | rgba(255,255,255,.06) | rgba(17,19,26,.08) | Contorno de cartão e item |

Tags e fundos suaves usam a cor do token com 16% de opacidade no fundo e 40% na borda, texto na cor cheia.

**Tipografia**

| Papel | Tamanho / peso | Uso |
| --- | --- | --- |
| Marca | 22 px, 800 itálico, caixa alta | Título do app (estilo logo KINGZ XP) |
| Título de tela | 20 px / 700 | Nome da comp no Plano A, nome do perfil |
| Título de seção | 1,15 rem (18 px) / 600 | Cabeçalho dos cartões |
| Corpo | 16 px / 400, altura 1,45 | Texto geral |
| Pequeno | 14 px / 500 | Itens de lista, rótulos de chip |
| Legenda | 13 px / 400 | Descrições em texto suave |
| Sobrelinha | 11,5 px / 600, caixa alta, espaçamento .06em | Tags (PEGUE, EVITE, POINTS) |

Fonte: a referência usa uma grotesca geométrica (estimativa: família tipo Satoshi). Substituto no Google Fonts: Plus Jakarta Sans 400, 500, 600, 700 e 800; fallback `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. Números com `font-variant-numeric: tabular-nums`.

**Forma, espaço e camadas**

| Token | Valor | Uso |
| --- | --- | --- |
| Raio XS | 4 px | Selo de tier, badge de nível, tags |
| Raio S | 8 px | Botões, campos, segmentos, pílulas da navegação |
| Raio M | 10 px | Tiles de boneco e componente, itens de lista |
| Raio L | 12 px | Cartões e painéis |
| Raio pleno | 999 px | Avatares e pontos de status |
| Espaço | 4, 8, 12, 16, 20, 24, 32 px | Escala base 4 |
| Padding de cartão | 16 px (14 px abaixo de 420 px) | Cartões |
| Intervalo entre cartões | 12 px | Grades |
| Elevação | Sem sombra; camadas por luminância (Fundo, Painel, Painel secundário, Controle) | Toda a interface |
| Brilho de estado | `box-shadow: 0 0 0 1px cor, 0 0 18px -6px cor` | Plano A, tile 3 estrelas, selo selecionado |

**Movimento**

| Token | Valor | Uso |
| --- | --- | --- |
| Rápido | 120 ms ease-out | Hover e pressão |
| Padrão | 180 ms cubic-bezier(.2,.8,.2,1) | Seleção, troca de aba, barra de pontuação |
| Redução | 0 ms com `prefers-reduced-motion: reduce` | Todo o app |

## Componentes e estados

Os 19 componentes do inventário do PRD (seção 7) têm cada um um padrão equivalente na referência; a tabela diz qual padrão vestir e como fica cada estado.

| Componente do PRD | Padrão da referência | Estados e visual |
| --- | --- | --- |
| Cabeçalho fixo e abas | Barra superior + pílulas Home / Challenges / Games / Seasons | Barra em Painel com borda inferior. Aba: ícone + rótulo, fundo Controle, texto suave. Ativa: Destaque preenchido, texto branco. Rolagem horizontal sem barra visível, com degradê de 16 px nas bordas. Foco: anel de 3 px Informação |
| Botão simples (Novo jogo, Tema) | Botão de ícone (sino) e View More | Fundo Controle, raio S, 44 px de alvo. Hover: Controle +6% de luz. Novo jogo com ícone de reinício; Tema com sol/lua |
| Controle segmentado | Faixa Overview / Spaces / Achievements | Trilho em Painel secundário, raio S, padding 4 px. Selecionado: Destaque preenchido. Não selecionado: texto suave. Variante "Rivais": Ruim preenchido |
| Chip de filtro | Pílulas de estatística (Followers 24k) | Fundo Painel secundário, raio S. Ativo: borda 1 px da cor da família + ponto de forma da família à esquerda |
| Cartão de seção com número de passo | Cartão com título + View More | Painel, raio L, padding 16. Número do passo em quadrado de 22 px, raio XS, fundo Destaque 16%, texto Destaque |
| Tile de boneco | Card de temporada (Diamonds) + ícones de jogos | Normal: Painel secundário, avatar de iniciais. Meu 1 e 2 estrelas: borda Moeda, fundo roxo 12%, estrelas no canto superior direito. Meu 3 estrelas: mesmo, com brilho de estado. Contestado: borda tracejada Destaque + aba de canto superior esquerdo com ícone, como o cadeado. Ambos: estilo meu + aba de contestado |
| Tile de componente | Ícone de jogo quadrado | Ícone de traço em Painel secundário. Com contador: badge de canto 18 px, raio pleno, fundo Informação, texto #07080c |
| Linha de pergunta | Item de Daily Challenge | Painel secundário, raio M, pergunta à esquerda, segmentado Sim / Não à direita. Vazio: segmentos neutros |
| Faixa de veredito | Tag COMPLETED | Faixa larga com tag. Suba: Bom. Fique: Atenção. Aguardando: Controle com texto suave |
| Caixa Próxima ação | Faixa de perfil abaixo do banner | Painel com degradê lateral da cor da confiança (forte Bom, média Atenção, baixa Ruim) a 14%. Título 20/700. Inicial: neutra com ícone de toque |
| Cartão de plano A, B, C | Card concluído (A) e item de lista (B, C) | A: borda Destaque, brilho de estado, letra "A" em selo 28 px. B e C: Painel secundário sem brilho |
| Barra de pontuação | EXP 4854/5000 | Trilho Controle 6 px, raio pleno. Preenchimento Destaque. Mínimo 4% de largura |
| Selo de tier e tags | Badge de nível "23" + tag EXPIRING | Tier S: fundo Família A, texto #07080c. Tier A: fundo Família B, texto #07080c. Tag de família: fundo 16%, forma + rótulo |
| Barra inferior | Barra superior espelhada | Painel com borda superior, área segura inferior, texto "A: … · B: …" em Pequeno, A em Destaque |
| Chip de boneco compacto | Pílula de estatística | Normal: Painel secundário. Meu: borda Moeda. Contestado: borda tracejada Destaque |
| Cartão de comp por nível | Item de Daily Challenge (miniatura, título, descrição, tag, tempo) | Miniatura = selo da família. Round win como tag: 60% ou mais Bom, 45% ou mais Atenção, abaixo Ruim. Ação (Role, Junte ouro, Complete) como tag Informação |
| Tile de augment e linha de veredito | Selos hexagonais de conquistas + "+45" | 8 tipos como selos coloridos de 64 px. Não selecionado: contorno neutro como o "+45". Selecionado: cor cheia + brilho. Veredito: linhas com tag Pegue (Bom), Bom (Informação), Ok (Atenção), Evite (Ruim) |
| Tabela de notas | Faixa POINTS 136 | Células com fundo 16% da cor da nota: 3 Bom, 2 Informação, 1 Atenção, 0 Ruim; número sempre visível |
| Ficha de comp | Cabeçalho de perfil (banner + faixa de estatísticas) | Faixa de topo com degradê da família, nome 20/700, pílulas Média / Top 4 / Win / Pick. Carry com borda Moeda. Aviso como tag Atenção |

**Estados globais a todos os interativos**

| Estado | Visual |
| --- | --- |
| Hover | Fundo +6% de luz, 120 ms |
| Pressionado | Escala 0,98 |
| Foco visível | Anel de 3 px em Informação, deslocamento 2 px |
| Desabilitado | Opacidade 0,4, sem hover |

## Iconografia e ativos visuais

A referência usa ícones de traço único (estilo Lucide, 16–18 px, traço 2 px); o app troca todos os emojis por esse estilo como SVG em linha, sem arquivos externos.

**Ícones (SVG em linha, `currentColor`, 20 px em toque, 16 px em texto)**

| Onde | Ícone sugerido (nome Lucide) |
| --- | --- |
| Aba Escolher | `crosshair` |
| Aba Earlys | `trending-up` |
| Aba Augments | `hexagon` |
| Aba As 6 comps | `layers` |
| Aba Guia | `book-open` |
| Novo jogo / Tema | `rotate-ccw` / `sun` e `moon` |
| Busca | `search` |
| Contestado | `swords` |
| Estrela de boneco | `star` preenchida |
| Componentes de item (9) | `wand-2` vara, `droplet` lágrima, `hand` luvas, `shirt` manto, `shield` colete, `sword` espada, `target` arco, `ribbon` cinto, `circle-dot` espátula |
| Tipos de augment (8) | `coins` economia, `refresh-cw` reroll, `arrow-up-circle` upgrade, `chevrons-up` XP, `package` itens, `zap` poder, `heart` sobrevivência, `flag` emblema |

**Selos (desenhados em SVG, sem imagem)**

| Família ou tipo | Forma | Cor |
| --- | --- | --- |
| Família A (Frontline/Vi) | Escudo apontado para baixo | Família A |
| Família B (Invoker) | Hexágono | Família B |
| Família C (Reroll) | Triângulo arredondado para cima | Família C |
| Augments (8 tipos) | Hexágono com degradê de duas paradas da própria cor e ícone branco ao centro | Uma cor por tipo, alternando Ruim, Família B, Família A, Bom, rosa #e0457b, Informação, Família C, Atenção |

**Ativos que não devem ser copiados.** A arte do banner e os logos de jogos são de terceiros. O banner vira degradê abstrato em CSS (Família B a 35% para Família C a 25% sobre Painel); retratos de campeões ficam fora do escopo do PRD e continuam como avatares de iniciais, agora em quadrado de raio M com a cor gerada pelo nome.

## Handoff para implementação

O redesign entra só por CSS e pelos modelos de HTML das funções `render*`; IDs, atributos `data-*`, classes de estado e dados ficam intactos.

**Bloco de tokens.** Os nomes abaixo são de referência: no outro chat, aplicar estes valores às variáveis já existentes no app (PRD, seção 9: manter os nomes) e criar só as que faltam. Os três blocos de tema do PRD são preservados.

```css
:root{
  --bg:#f5f6f9; --panel:#ffffff; --panel-2:#eef0f5; --control:#e6e9f0;
  --line:#dfe2ea; --border-subtle:rgba(17,19,26,.08);
  --text:#11131a; --text-soft:#5a5f6e;
  --accent:#c2380a; --accent-fill:#c2380a; --info:#08729e;
  --premium:#6a2fd6; --premium-bg:#efe9ff;
  --fam-a:#b45309; --fam-b:#7c3aed; --fam-c:#0f766e;
  --good:#4d7a00; --warn:#b45309; --bad:#b0164d; --bad-fill:#b0164d;
  --font:"Plus Jakarta Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --r-xs:4px; --r-s:8px; --r-m:10px; --r-l:12px; --r-full:999px;
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:20px; --s6:24px; --s8:32px;
  --t-fast:120ms ease-out; --t-base:180ms cubic-bezier(.2,.8,.2,1);
  --hit:44px;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#07080c; --panel:#0d1018; --panel-2:#12151f; --control:#1b1e2a;
    --line:#1f2330; --border-subtle:rgba(255,255,255,.06);
    --text:#f5f7fb; --text-soft:#8b90a0;
    --accent:#f1460f; --accent-fill:#c2380a; --info:#3fb8ec;
    --premium:#9a6bff; --premium-bg:#1d1a36;
    --fam-a:#f4b740; --fam-b:#b06cff; --fam-c:#2fd6a8;
    --good:#b4f24e; --warn:#ff9a3d; --bad:#ff6b6b; --bad-fill:#9b1b48;
  }
}
:root[data-theme="dark"]{ /* repetir os mesmos valores do bloco escuro */ }
body{background:var(--bg);color:var(--text);font:400 16px/1.45 var(--font);}
@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important}}
```

Fonte: `<link>` do Google Fonts para Plus Jakarta Sans com `display=swap` (origem permitida pelo ambiente de publicação).

**Layout**

| Área | Spec |
| --- | --- |
| Container | Largura máxima 1200 px, padding lateral 16 px (24 px acima de 900 px) |
| Cabeçalho | 56 px de altura + área segura superior; marca à esquerda, abas ao centro, botões à direita; abaixo de 900 px as abas descem para uma segunda linha rolável |
| Escolher acima de 900 px | Grid `minmax(0,1fr) 380px`, gap 12; coluna de resultado `position: sticky` como a coluna Daily Challenges |
| Grade de bonecos | `repeat(auto-fill,minmax(72px,1fr))`, gap 8, tile quadrado; área com altura máxima de 430 px e rolagem interna (PRD E-01) |
| Grade de componentes | 9 tiles em `repeat(auto-fill,minmax(56px,1fr))` |
| Augments | Selos em `repeat(auto-fill,minmax(72px,1fr))`, gap 12 |

**Responsividade (breakpoints do PRD mantidos)**

| Largura | Mudança |
| --- | --- |
| Acima de 900 px | Duas colunas, sem barra inferior |
| Até 900 px | Uma coluna, resultado abaixo das entradas, barra inferior fixa na aba Escolher |
| Até 640 px | Listas Foque em / Evite empilhadas; faixa de estatísticas da ficha quebra em 2 por linha |
| Até 420 px | Grades de cartões em 1 coluna; padding de cartão 14 px; tiles de boneco mínimo 64 px |

**Casos de borda**

- Nome de boneco longo: uma linha com reticências no tile; nome completo no `aria-label`.
- Sem dados marcados: caixa Próxima ação em estado inicial e ranking base (PRD E-12).
- Tabela de notas: rola dentro do próprio quadro (`overflow-x: auto`), nunca a página.
- Falha de armazenamento: nenhuma mudança visual.

**Movimento**

| Elemento | Gatilho | Animação | Duração |
| --- | --- | --- | --- |
| Tile de boneco | Toque | Escala 0,96 e volta; estrelas entram com fade | Rápido |
| Barra de pontuação | Recalcular | Largura anima | Padrão |
| Cartões de plano | Troca de ordem | Fade de 0 a 1 no conteúdo, sem deslizar | Padrão |
| Aba | Troca | Fundo ativo com transição de cor | Padrão |

**Acessibilidade**

- Manter `aria-pressed`, `aria-selected` e os `aria-label` atuais (PRD, seção 8).
- Alvo de 44 px também no segmentado: altura do trilho 44 px, segmento interno 36 px.
- Contestado e família nunca só por cor: forma do selo, borda tracejada e ícone.
- Ordem de foco: cabeçalho, abas, entradas na ordem dos passos, resultado, barra inferior.

**Ganchos que não podem mudar (conferir com a seção 9 do PRD)**

- Atributos: `data-tab`, `data-u`, `data-eu`, `data-it`, `data-hp`, `data-gold`, `data-mode`, `data-fam`, `data-ck` com `data-v`, `data-open`, `data-ac`, `data-ag`, `data-cf`, `data-stage`.
- Contêineres: `#units`, `#items`, `#results`, `#checks`, `#checkVerdict`, `#hpSeg`, `#goldSeg`, `#modeSeg`, `#famChips`, `#q`, `#stageSeg`, `#stageBody`, `#augComp`, `#augTypes`, `#augVerdict`, `#augTable`, `#compFam`, `#compCards`, `#dockBtn`, `#dockText`, `#btnReset`, `#btnTheme`.
- Visões: `#v-pick`, `#v-early`, `#v-aug`, `#v-comps`, `#v-guide` com a classe `on`.

**Ordem de aplicação**

1. Tokens e fonte.
2. Cabeçalho, abas e barra inferior.
3. Tile de boneco e tile de componente.
4. Cartões de plano e caixa Próxima ação.
5. Ícones SVG e selos.
6. Earlys, Augments, fichas e Guia.
7. Conferência de acessibilidade em 375, 768 e 1280 px.

## Checklist de verificação visual

O redesign está aplicado quando o app parece a referência em tema escuro e todos os itens abaixo passam, além dos critérios de aceite do PRD.

- [ ] Camadas Fundo, Painel, Painel secundário e Controle visíveis sem nenhuma sombra.
- [ ] Laranja aparece só em aba ativa, segmento selecionado, Plano A, contestado e barra de pontuação.
- [ ] Texto suave mede 4,5:1 ou mais nos dois temas; texto branco nunca sobre #f1460f.
- [ ] Tile de boneco mostra os 5 estados (normal, 1, 2 e 3 estrelas, contestado, ambos) distinguíveis em escala de cinza.
- [ ] Família identificável por forma e rótulo, não só por cor.
- [ ] Nenhum emoji restante; todos os ícones em SVG em linha com `currentColor`.
- [ ] Nenhuma imagem da referência ou de terceiros no arquivo.
- [ ] Alvos de toque de 44 px em abas, segmentos, tiles e botões.
- [ ] Tema claro, escuro automático e escuro manual corretos em todas as abas.
- [ ] Sem rolagem horizontal da página em 375, 768 e 1280 px.
- [ ] Todos os ganchos da seção 9 do PRD presentes e a lógica sem alteração.

**Pontos em aberto**

- Valores de cor são amostras de um screenshot comprimido; tons de borda e de texto suave podem precisar de ajuste fino à vista.
- A fonte original não foi identificada com certeza; Plus Jakarta Sans é o substituto mais próximo disponível no Google Fonts.
