#!/usr/bin/env python
"""Fetch the current TFT meta (top 6 comps + "how to play" data) from MetaTFT's public,
undocumented JSON API. Output: scraper/data/comps.json (or --out PATH). Exit 1 on any failure.
9 HTTP requests per run (3 list-level + 1 detail per top comp), 1 s apart."""
import json, os, re, sys, time
from datetime import datetime, timezone
import requests

API = "https://api-hc.metatft.com/tft-comps-api"
LOOKUPS = "https://data.metatft.com/lookups"
TOP_N = 6
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
           "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
           "Referer": "https://www.metatft.com/"}
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "comps.json")
CDN = "https://cdn.metatft.com/file/metatft"  # public image CDN used by the MetaTFT frontend


def img_url(kind, key):
    """kind: champions|items|traits|augments|charms|tiers. key: lowercase apiName (see unit_key/trait_key)."""
    return f"{CDN}/{kind}/{key}.png"


def resize_url(url, w, h=None):
    """Cloudflare on-the-fly resize, as the site does for thumbnails (format=auto -> webp/avif when supported)."""
    return f"https://cdn.metatft.com/cdn-cgi/image/width={w},height={h or w},format=auto/{url}"


def unit_key(u):  # frontend unitImageKey(): characterName || apiName, lowercased. da_18_alistar == tft18_alistar
    return str(u.get("characterName") or u["apiName"]).lower()


def trait_key(api_name):  # frontend traitIconKey(): DA_18_Blackthorn -> da_18_blackthorn, TFT14_Trait_X -> trait
    if api_name.startswith("DA_"):
        return re.sub(r"[^\w]", "", re.sub(r"_\d+$", "", api_name)).lower()
    return re.sub(r"[^\w]", "", api_name.split("_")[1] if "_" in api_name else api_name).lower()


def parse_out(argv):
    """`--out PATH` or `--out=PATH`; defaults to scraper/data/comps.json."""
    for i, a in enumerate(argv):
        if a == "--out" and i + 1 < len(argv):
            return os.path.abspath(argv[i + 1])
        if a.startswith("--out="):
            return os.path.abspath(a.split("=", 1)[1])
    return DEFAULT_OUT


def get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"{url} -> {data['error']}")
    time.sleep(1.0)  # be polite
    return data


# --- rules copied from MetaTFT's frontend bundle (main-*.js), so output matches the site ---
def tier_for(avg):
    return "S" if avg < 4.25 else "A" if avg < 4.5 else "B" if avg < 4.75 else "C" if avg < 5 else "D"


def difficulty_for(diff, levelling):
    return "Easy" if diff < -0.05 else "Hard" if (diff > 0.07 or levelling == "Fast 9") else "Medium"


def humanize(api_name):  # fallback only: DA_GuinsoosRageblade -> Guinsoos Rageblade
    s = re.sub(r"^(DA_|TFT\d*_)(\d+_)?", "", api_name)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", re.sub(r"\d+", "", s).replace("_", " ")).strip()


class Names:
    def __init__(self, lk):
        self.unit = {a: u for u in lk["units"] for a in (u.get("assetNames") or [u["apiName"]])}
        self.item = {i["apiName"]: i for i in lk["items"]}
        self.trait = {t["apiName"]: t["name"] for t in lk["traits"]}
        self.aug = {a["apiName"]: a["name"] for a in lk["augments"]}

    # image URLs on MetaTFT's CDN (same keys the site uses); see scraper/fetch_assets.py for the full manifest
    def u_img(self, i): return img_url("champions", unit_key(self.unit[i]) if i in self.unit else i.lower())
    def it_img(self, i): return img_url("items", i.lower())
    def t_img(self, i): return img_url("traits", trait_key(i))
    def a_img(self, i): return img_url("augments", i.lower())

    def u(self, i): return self.unit.get(i, {}).get("name") or humanize(i)
    def shop(self, i): return self.unit.get(i, {}).get("shopUnit", True)  # False = trait-spawned (e.g. Elderwood plants)
    def cost(self, i): return self.unit.get(i, {}).get("cost")
    def it(self, i): return self.item.get(i, {}).get("name") or humanize(i)
    def t(self, i): return self.trait.get(i) or humanize(i)
    def a(self, i): return self.aug.get(i) or humanize(i)


def split_units(s, sep): return [x.strip() for x in s.split(sep) if x.strip()]


def summary(cid, c, total, nm):
    avg, games = c["overall"]["avg"], c["overall"]["count"]
    parts = [nm.t(p["name"]) if p["type"] == "trait" else nm.u(p["name"]) for p in c["name"]]
    return {"id": cid, "name": " ".join(parts), "tier": tier_for(avg), "avgPlacement": round(avg, 3),
            "playRate": round(100 * games / total, 2), "games": games, "top4Rate": None, "winRate": None,
            "levelling": c.get("levelling"), "difficulty": difficulty_for(c.get("difficulty", 0), c.get("levelling"))}


def detail(base, c, d, augs, nm):
    """Map comps_data cluster (c) + comp_details results (d) to the page's constants."""
    unit_ids = split_units(c["units_string"], ",")
    stars = {}
    for us in d.get("unit_stats", []):  # most common star level per unit (VERIFIED field: tiers[].pcnt)
        if us["tiers"]:
            stars[us["unit"]] = max(us["tiers"], key=lambda t: t["pcnt"])["tier"]
    builds = {}
    for b in sorted(c.get("builds", []), key=lambda b: -b["count"]):  # the 4 builds the site shows
        builds.setdefault(b["unit"], b.get("buildName") or [])
    units = [{"name": nm.u(u), "id": u, "cost": nm.cost(u),
              "stars": stars.get(u) or (3 if u in c.get("stars", []) else 2),
              "items": [nm.it(i) for i in builds.get(u, [])], "carry": u in builds,
              "img": nm.u_img(u)} for u in unit_ids]
    item_ids = ({x for b in builds.values() for x in b} | {i["itemNames"] for i in d.get("itemNames", [])}
                | set(d.get("first_carousel", [])))
    trait_ids = [t.rsplit("_", 1)[0] for t in split_units(c["traits_string"], ",") if "_" in t]
    early_ids = {u for opts in list(d.get("early_options", {}).values()) + list(d.get("options", {}).values()) if opts
                 for u in split_units(opts[0].get("unit_list") or opts[0].get("units_list") or "", "&")}
    imgs = {"units": {nm.u(u): nm.u_img(u) for u in list(unit_ids) + sorted(early_ids)},
            "items": {nm.it(i): nm.it_img(i) for i in sorted(item_ids)},
            "traits": {nm.t(t): nm.t_img(t) for t in trait_ids},
            "augments": {nm.a(a["id"]): nm.a_img(a["id"]) for a in augs}}
    # positioning: greedy, same as the site's pfe(): each unit takes its most frequent free cell.
    # cell_1..7 = back row (player side), cell_22..28 = front row. rows[0] = front.
    taken, cells = set(), {}
    for u in unit_ids:
        for p in d.get("positioning", {}).get("units", {}).get(u, {}).get("positions", []):
            if p["cell"] not in taken:
                taken.add(p["cell"]); cells[int(p["cell"].split("_")[1])] = nm.u(u); break
    rows = [[cells.get((22 - 7 * r) + col) for col in range(7)] for r in range(4)]
    # level timing (same derivation as the site's get_level_timings)
    lv = {}
    for L in d.get("levels", []):
        if L["stage"]:
            rr = d.get("rerolls", {}).get(str(L["level"]), {})
            lv[str(L["level"])] = {"stage": f"{L['stage']}-{L['round']}", "games": L["count"],
                                   "avgRerolls": round(rr["rerolls"] / rr["matches"], 1) if rr.get("matches") else None}
    roll_level = max(lv, key=lambda k: lv[k]["avgRerolls"] or 0) if lv else None
    fl_total = sum(f["count"] for f in d.get("final_levels", [])) or 1
    final_levels = {f["level"]: round(100 * f["count"] / fl_total, 1) for f in d.get("final_levels", [])}
    early = {str(L): [nm.u(u) for u in split_units(opts[0]["unit_list"], "&") if nm.shop(u)]
             for L, opts in d.get("early_options", {}).items() if opts}
    boards = {L: [nm.u(u) for u in split_units(opts[0]["units_list"], "&") if nm.shop(u)]
              for L, opts in d.get("options", {}).items() if opts}
    total_games = c["overall"]["count"]
    item_prio = sorted(d.get("itemNames", []), key=lambda i: -i["pcnt"])[:10]
    comp_prio = {}
    for i in d.get("itemNames", []):  # carousel/component priority, same as the site's get_carousel()
        for comp in nm.item.get(i["itemNames"], {}).get("composition", []) or []:
            comp_prio[comp] = comp_prio.get(comp, 0) + i["count"]
    pro = (d.get("proComps") or [{}])[0].get("content", {})
    return {**base,
            "units": units, "traits": [{"name": nm.t(t.rsplit("_", 1)[0]), "count": int(t.rsplit("_", 1)[1]),
                                        "img": nm.t_img(t.rsplit("_", 1)[0])}
                                       for t in split_units(c["traits_string"], ",") if "_" in t],
            "images": imgs,                       # display name -> CDN image URL for everything named in this comp
            "carries": [u["name"] for u in units if u["carry"]],
            "early": early,                       # early boards by level 4..7 (most played option)
            "boardsByLevel": boards,              # most played unit set at levels 7..10 (no positions)
            "positioning": {"rows": rows, "cells": {f"cell_{k}": v for k, v in sorted(cells.items())}},
            "levelTiming": {"levels": lv, "rollLevel": roll_level, "finalLevelPct": final_levels,
                            "style": c.get("levelling")},
            "itemPriority": [{"name": nm.it(i["itemNames"]), "id": i["itemNames"], "img": nm.it_img(i["itemNames"]),
                              "perGame": round(i["pcnt"], 2), "avgPlacement": i["avg"],
                              "bestOn": [nm.u(x["units"]) for x in i.get("units", [])[:2]]} for i in item_prio],
            "componentPriority": [{"name": nm.it(k), "id": k, "img": nm.it_img(k), "perGame": round(v / total_games, 2)}
                                  for k, v in sorted(comp_prio.items(), key=lambda kv: -kv[1])],
            "firstCarousel": [nm.it(x) for x in d.get("first_carousel", [])] or None,
            "augments": {t: [nm.a(a["id"]) for a in augs if a["tier"] == t] for t in sorted({a["tier"] for a in augs})} or None,
            "proTips": {"title": pro.get("metadata", {}).get("title"), "notes": pro.get("content", {}).get("notes"),
                        "url": f"https://www.metatft.com/pro-comps?comp={pro['content_id']}" if pro.get("content_id") else None}
            if pro else None,
            "trend": [{"day": t["day"][:10], "avgPlacement": t["avg"], "games": t["count"]} for t in c.get("trends", [])]}


def main(argv=None):
    OUT = parse_out(sys.argv[1:] if argv is None else argv)
    t0 = time.time()
    try:
        comps = get_json(f"{API}/comps_data")  # current patch, ranked (queue 1100)
        tft_set, cluster = comps["tft_set"], comps["cluster_id"]
        lk = get_json(f"{LOOKUPS}/{tft_set}_latest_en_us.json")
        aug_tiers = get_json(f"{API}/comp_augment_tiers?cluster_id={cluster}")["results"]
        nm = Names(lk)
        clusters = comps["results"]["data"]["cluster_details"]
        total = sum(c["overall"]["count"] for c in clusters.values())
        ranked = sorted(clusters.items(), key=lambda kv: kv[1]["overall"]["avg"])
        if len(ranked) < TOP_N:
            raise RuntimeError(f"only {len(ranked)} comps returned")
        top = []
        for cid, c in ranked[:TOP_N]:
            d = get_json(f"{API}/comp_details?comp={cid}&cluster_id={cluster}")["results"]
            top.append(detail(summary(cid, c, total, nm), c, d, aug_tiers.get(cid, {}).get("augments", []), nm))
        result = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "source": {"site": "MetaTFT", "attribution": "Data by MetaTFT (https://www.metatft.com/comps)",
                             "endpoints": [f"{API}/comps_data", f"{LOOKUPS}/{tft_set}_latest_en_us.json",
                                           f"{API}/comp_augment_tiers?cluster_id={cluster}",
                                           f"{API}/comp_details?comp=<id>&cluster_id={cluster}"]},
                  "set": tft_set, "set_name": lk.get("_metadata", {}).get("setName"), "patch": None,
                  "cluster_id": cluster, "queue_id": comps["queue_id"], "total_games": total,
                  "source_updated_at": datetime.fromtimestamp(comps["updated"] / 1000, timezone.utc).isoformat(timespec="seconds"),
                  "not_provided_by_source": ["patch label", "top4Rate", "winRate", "firstCarousel (empty for this set)"],
                  "images": {"cdn": CDN, "pattern": CDN + "/{champions|items|traits|augments}/{key}.png",
                             "resize": "https://cdn.metatft.com/cdn-cgi/image/width={w},height={h},format=auto/{img}",
                             "manifest": "assets/assets.json"},
                  "top": top, "all_comps": [summary(cid, c, total, nm) for cid, c in ranked]}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT + ".tmp", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        os.replace(OUT + ".tmp", OUT)
        print(f"OK top {TOP_N} of {len(ranked)} comps, set={tft_set}, cluster={cluster}, {time.time() - t0:.1f}s -> {OUT}")
        for r in top:
            print(f"  [{r['tier']}] {r['avgPlacement']:.3f} {r['playRate']:5.2f}% {r['name']:<28} roll@{r['levelTiming']['rollLevel']} "
                  f"{r['levelling']:<9} carries={','.join(r['carries'])}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
