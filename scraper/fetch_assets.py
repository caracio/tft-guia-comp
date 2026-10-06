#!/usr/bin/env python
"""Build assets/assets.json: image URLs (MetaTFT CDN) for every unit, item, trait, augment, charm,
armory item and star tier of the current set, plus optional local copies under assets/<category>/.

  python scraper/fetch_assets.py                 # manifest only (URLs verified with HEAD)
  python scraper/fetch_assets.py --download      # also save the PNGs locally (skips files already present)
  python scraper/fetch_assets.py --download --splashes --force

URL pattern (same as MetaTFT's frontend bundle):
  https://cdn.metatft.com/file/metatft/{champions|items|traits|augments|charms|tiers}/{key}.png
  https://cdn.metatft.com/cdn-cgi/image/width=W,height=H,format=auto/<raw url>   (on-the-fly resize)
Exit 1 if the lookups cannot be fetched; individual missing images are reported, not fatal."""
import json, os, sys, time
from datetime import datetime, timezone
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_meta import API, LOOKUPS, HEADERS, get_json, CDN, img_url, resize_url, trait_key, unit_key  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
MANIFEST = os.path.join(ASSETS, "assets.json")
DELAY = 0.15  # seconds between CDN requests


def item_kind(it):
    tags = " ".join(it.get("tags") or [])
    api = it["apiName"]
    if "Component" in api or "Item.Component" in tags: return "component"
    if "Radiant" in api or "Radiant" in tags: return "radiant"
    if "Emblem" in api or "Emblem" in tags: return "emblem"
    if "Artifact" in api or "Artifact" in tags or "Ornn" in tags: return "artifact"
    if "Support" in api or "Support" in tags: return "support"
    if "Consumable" in api: return "consumable"
    if "Craftable" in tags or it.get("composition"): return "craftable"
    return "other"


class Fetcher:
    def __init__(self, download, force):
        self.download, self.force = download, force
        self.s = requests.Session(); self.s.headers.update(HEADERS)
        self.ok = self.missing = self.saved = self.skipped = 0

    def fetch(self, url, rel):
        """Verify `url` (HEAD, or GET when downloading). Returns (status, local_rel_path or None)."""
        path = os.path.join(ASSETS, rel)
        if self.download and os.path.exists(path) and not self.force:
            self.skipped += 1; self.ok += 1
            return 200, rel
        try:
            r = self.s.get(url, timeout=40) if self.download else self.s.head(url, timeout=40, allow_redirects=True)
            st = r.status_code
            is_img = st == 200 and r.headers.get("content-type", "").startswith("image/")
        except requests.RequestException as e:  # noqa: PERF203
            print(f"  ERR {url}: {e}", file=sys.stderr); st, is_img = 0, False
        time.sleep(DELAY)
        if not is_img:
            self.missing += 1
            return st, None
        self.ok += 1
        if self.download:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path + ".tmp", "wb") as f:
                f.write(r.content)
            os.replace(path + ".tmp", path); self.saved += 1
            return st, rel
        return st, None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    download, force, splashes = "--download" in argv, "--force" in argv, "--splashes" in argv
    t0 = time.time()
    try:
        comps = get_json(f"{API}/comps_data")
        tft_set = comps["tft_set"]
        lk = get_json(f"{LOOKUPS}/{tft_set}_latest_en_us.json")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: {type(e).__name__}: {e}", file=sys.stderr); return 1
    f = Fetcher(download, force)
    by_name = {"units": {}, "items": {}, "traits": {}, "augments": {}, "charms": {}}

    def entry(kind, key, name, extra):
        url = img_url(kind, key)
        st, local = f.fetch(url, f"{kind}/{key}.png")
        ok = st == 200
        return {"name": name, **extra, "img": url if ok else None, "thumb": resize_url(url, 48) if ok else None,
                "file": local, "status": st}

    units = []
    for u in lk["units"]:
        key = unit_key(u)
        e = entry("champions", key, u["name"], {"apiName": u["apiName"], "assetNames": u.get("assetNames") or [],
                                                "cost": u.get("cost"), "traits": u.get("traits") or [],
                                                "shopUnit": u.get("shopUnit", True)})
        splash = f"{CDN}/championsplashes/{key}.png"
        e["splash"] = splash; e["splash512"] = resize_url(splash, 512, 303)
        if splashes and e["img"]:
            _, e["splashFile"] = f.fetch(e["splash512"], f"splashes/{key}.png")
        units.append(e)
        for n in [u["name"], u["apiName"], *(u.get("assetNames") or [])]:
            by_name["units"].setdefault(n, e["img"])
    items = []
    for it in lk["items"] + lk.get("armory_items", []):
        e = entry("items", it["apiName"].lower(), it["name"], {"apiName": it["apiName"], "kind": item_kind(it),
                                                             "composition": it.get("composition") or []})
        items.append(e)
        for n in [it["name"], it["apiName"]]:
            by_name["items"].setdefault(n, e["img"])
    traits = []
    for t in lk["traits"]:
        # breakpoints = quantos bonecos ativam cada nível do trait (usado pela aba Flex do guia)
        bps = sorted({e["minUnits"] for e in t.get("effects") or [] if e.get("minUnits")})
        e = entry("traits", trait_key(t["apiName"]), t["name"], {"apiName": t["apiName"], "type": t.get("type"),
                                                                 "breakpoints": bps})
        traits.append(e)
        for n in [t["name"], t["apiName"]]:
            by_name["traits"].setdefault(n, e["img"])
    augments = []
    for a in lk["augments"]:
        e = entry("augments", a["apiName"].lower(), a["name"], {"apiName": a["apiName"], "rarity": a.get("rarity"),
                                                              "tags": a.get("manual_tags") or []})
        augments.append(e)
        for n in [a["name"], a["apiName"]]:
            by_name["augments"].setdefault(n, e["img"])
    charms = []
    for c in lk.get("charms", []):
        e = entry("charms", c["apiName"].lower(), c["name"], {"apiName": c["apiName"], "tier": c.get("tier")})
        charms.append(e)
        for n in [c["name"], c["apiName"]]:
            by_name["charms"].setdefault(n, e["img"])
    tiers = {}
    for n in (1, 2, 3, 4):
        st, local = f.fetch(img_url("tiers", str(n)), f"tiers/{n}.png")
        tiers[str(n)] = {"img": img_url("tiers", str(n)), "file": local, "status": st}
    manifest = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "set": tft_set, "set_name": lk.get("_metadata", {}).get("setName"),
                "source": {"site": "MetaTFT", "attribution": "Images via MetaTFT CDN (https://www.metatft.com/). "
                           "Teamfight Tactics and all game art are property of Riot Games.",
                           "lookups": f"{LOOKUPS}/{tft_set}_latest_en_us.json"},
                "cdn": {"base": CDN, "pattern": CDN + "/{champions|items|traits|augments|charms|tiers}/{key}.png",
                        "resize": "https://cdn.metatft.com/cdn-cgi/image/width={w},height={h},format=auto/{img}",
                        "local": "assets/{category}/{key}.png (present when `file` is not null)"},
                "counts": {"units": len(units), "items": len(items), "traits": len(traits), "augments": len(augments),
                           "charms": len(charms), "ok": f.ok, "missing": f.missing},
                "byName": by_name, "units": units, "items": items, "traits": traits, "augments": augments,
                "charms": charms, "tiers": tiers}
    os.makedirs(ASSETS, exist_ok=True)
    with open(MANIFEST + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    os.replace(MANIFEST + ".tmp", MANIFEST)
    miss = [(k, e["apiName"]) for k, arr in (("unit", units), ("item", items), ("trait", traits), ("augment", augments),
                                           ("charm", charms)) for e in arr if not e["img"]]
    print(f"OK set={tft_set} units={len(units)} items={len(items)} traits={len(traits)} augments={len(augments)} "
          f"charms={len(charms)} | verified={f.ok} missing={f.missing} saved={f.saved} skipped={f.skipped} "
          f"{time.time() - t0:.0f}s -> {MANIFEST}")
    for k, a in miss:
        print(f"  missing {k}: {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
