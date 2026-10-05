# assets/ · imagens do jogo para o design

Gerado por `scraper/fetch_assets.py` a partir dos lookups do MetaTFT para o set atual. Roda todo dia no mesmo workflow do `comps.json`, então boneco novo de patch aparece aqui sozinho.

## O que tem

| Pasta / arquivo | Conteúdo | Tamanho típico |
| --- | --- | --- |
| `assets.json` | Manifesto: nome, apiName, URL no CDN, URL de thumbnail, caminho local e status HTTP de cada imagem. | – |
| `champions/` | Ícone quadrado de cada unidade (`tft18_alistar.png`). | 128×128 |
| `splashes/` | Splash horizontal de cada unidade, já reduzido pelo CDN. | 512×303 |
| `items/` | Componentes, itens completos, radiantes, emblemas, artefatos, suportes e consumíveis (`da_adaptivehelm.png`). | 128×128 |
| `traits/` | Ícone branco de cada trait (`da_18_blackthorn.png`), bom para usar com `filter`/máscara CSS. | 32×32 |
| `augments/` | Ícone de cada augment (`da_advancedloan.png`). | 256×256 |
| `charms/` | Ícone de cada charm do set (`da_abandonship18_upgrade.png`). | 128×128 |
| `tiers/` | Estrelas 1★ a 4★ (`3.png`). | 48×16 |

## Como usar no design

**Opção A — link direto no CDN (recomendado para a página publicada).** Tudo que está em `data/comps.json` já vem com `img`:

```js
// unidade, trait e itemPriority/componentPriority têm campo img
comp.units[0].img            // https://cdn.metatft.com/file/metatft/champions/tft18_alistar.png
comp.traits[0].img           // https://cdn.metatft.com/file/metatft/traits/da_18_blackthorn.png
comp.itemPriority[0].img     // https://cdn.metatft.com/file/metatft/items/da_gargoylestoneplate.png

// para qualquer nome que apareça como texto (items de um boneco, early boards, augments):
comp.images.units["Alistar"]
comp.images.items["Gargoyle Stoneplate"]
comp.images.augments["Pandora's Bench"]
```

Para miniaturas use o redimensionador do próprio CDN (entrega webp/avif quando o navegador aceita):

```
https://cdn.metatft.com/cdn-cgi/image/width=48,height=48,format=auto/<URL da imagem>
```

**Opção B — arquivo local (offline / sem depender do MetaTFT).** O manifesto tem `file` com o caminho relativo à raiz do site:

```js
const m = await (await fetch("assets/assets.json")).json();
m.byName.units["Alistar"]          // URL no CDN
m.units.find(u => u.name === "Alistar").file   // "champions/tft18_alistar.png"  → <img src="assets/champions/tft18_alistar.png">
```

`byName` aceita nome de exibição **e** apiName (`"Alistar"`, `"TFT18_Alistar"`, `"DA_18_Alistar"`), então funciona com qualquer id que o `comps.json` use.

## Padrão de URL

```
https://cdn.metatft.com/file/metatft/{champions|items|traits|augments|charms|tiers}/{chave}.png
```

- **champions:** `characterName` em minúsculas (`TFT18_Alistar` → `tft18_alistar`). O alias `da_18_alistar` também funciona.
- **items / augments / charms:** `apiName` em minúsculas.
- **traits:** `apiName` sem o sufixo numérico, em minúsculas (`DA_18_Blackthorn` → `da_18_blackthorn`).
- **splash:** `championsplashes/{chave}.png` (original tem até 7 MB; use sempre o redimensionador).

## Atualizar

```bash
scraper/.venv/Scripts/python scraper/fetch_assets.py --download
```

Só baixa o que ainda não existe. `--force` rebaixa tudo, `--splashes` inclui os splashes 512px. Sem `--download` apenas verifica as URLs e regrava o manifesto.

## Atribuição

Imagens servidas pelo CDN do [MetaTFT](https://www.metatft.com/). Teamfight Tactics e toda a arte do jogo são propriedade da Riot Games. Este projeto não é afiliado a nenhum dos dois.
