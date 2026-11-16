"""Genere des images HD candidates avec un moteur gratuit sans compte.

Moteurs :
  horde        AI Horde (https://aihorde.net). Cle : AIHORDE_API_KEY, sinon "horde_api_key" de
               config.local.json (jamais affichee), sinon cle anonyme publique "0000000000",
               modele "AlbedoBase XL (SDXL)" par defaut (suit bien la consigne ; la pixelisation
               vient apres). File communautaire : 2 travaux a la fois, ~30 s a 3 min par image.
  pollinations image.pollinations.ai, sans cle ; palier anonyme ~1 image/min,
               logo en bas a droite (le sujet doit rester centre).

Usage :
  python -I generate.py --prompt "..." --negative "..." --out DIR --seeds 11 22 33 \
      [--engine horde|pollinations] [--model "AIO Pixel Art"] [--size 512] [--steps 30]

N'envoie que la description du sprite : aucune donnee personnelle.
Ecrit DIR/seed<N>.png (ou .jpg) et DIR/generate.json (moteur, modele, prompt, graines, erreurs).
"""
import argparse, base64, json, os, sys, time, urllib.error, urllib.parse, urllib.request

AGENT = "pixel-art-forge:1.0:anonymous"
HORDE = "https://aihorde.net/api/v2"


def http(method, url, body=None, headers=None, timeout=120):
    h = {"Client-Agent": AGENT, "User-Agent": AGENT, "Content-Type": "application/json"}
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), dict(r.headers)


ANON_KEY = "0000000000"


def horde_key():
    """Cle AI Horde, relue a chaque lancement : AIHORDE_API_KEY, puis "horde_api_key" de
    config.local.json (non versionne), sinon cle anonyme publique. La cle n'est JAMAIS
    affichee ni ecrite : seul le fait qu'une cle de compte est utilisee est journalise."""
    k = os.environ.get("AIHORDE_API_KEY", "").strip()
    if not k:
        cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.local.json")
        try:
            with open(cfg, encoding="utf-8") as f:
                k = str(json.load(f).get("horde_api_key", "") or "").strip()
        except Exception:
            k = ""
    return (k, True) if k and k != ANON_KEY else (ANON_KEY, False)


def prepare_source(path, size):
    """Image de base pour la retouche (img2img) : sujet centre sur fond blanc, carre size x size,
    agrandi proprement (LANCZOS), encode en webp base64 comme l'attend AI Horde."""
    import io
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if bb:
        im = im.crop(bb)
    s = (size * 0.82) / max(im.size)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    bg = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    bg.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
    buf = io.BytesIO()
    bg.convert("RGB").save(buf, "WEBP", quality=95)
    return base64.b64encode(buf.getvalue()).decode()


def horde(prompt, negative, seeds, out, model, size, steps, cfg, log, lora="", source="", denoise=0.45, control=""):
    full = prompt + (" ### " + negative if negative else "")
    key, account = horde_key()
    log["cle_compte"] = account
    # Palier anonyme : 2 travaux a la fois ; avec un compte, priorite plus haute, 3 a la fois.
    slots = 3 if account else 2
    src_b64 = prepare_source(source, size) if source else None
    todo = list(seeds)
    t0 = time.time()
    pending = {}
    while (todo or pending) and time.time() - t0 < 900:
        while todo and len(pending) < slots:
            s = todo[0]
            body = {
                "prompt": full,
                "params": {"sampler_name": "k_euler_a", "cfg_scale": cfg, "seed": str(s),
                           "height": size, "width": size, "steps": steps, "n": 1, "karras": True,
                           **({"loras": [{"name": lora.split(":")[0], "model": float(lora.split(":")[1]) if ":" in lora else 0.8, "clip": 1.0}]} if lora else {})},
                "models": [model], "nsfw": False, "censor_nsfw": True, "r2": True,
                "trusted_workers": False, "slow_workers": True,
            }
            if src_b64:  # retouche d'une image de base (img2img), ou forme imposee (ControlNet)
                body["source_image"] = src_b64
                body["source_processing"] = "img2img"
                body["params"]["denoising_strength"] = denoise
                if control:
                    body["params"]["control_type"] = control
            try:
                _, b, _ = http("POST", HORDE + "/generate/async", body, {"apikey": key})
                pending[s] = json.loads(b)["id"]
                todo.pop(0)
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    break  # plus de place : attendre qu'un travail finisse
                log["errors"].append(f"seed {s}: envoi refuse (HTTP {e.code} {e.read()[:200]!r})")
                todo.pop(0)
            except Exception as e:
                log["errors"].append(f"seed {s}: envoi refuse ({e})")
                todo.pop(0)
        time.sleep(6)
        for s, jid in list(pending.items()):
            try:
                _, b, _ = http("GET", f"{HORDE}/generate/check/{jid}")
                st = json.loads(b)
                if st.get("faulted"):
                    log["errors"].append(f"seed {s}: job en echec"); pending.pop(s); continue
                if not st.get("done"):
                    continue
                _, b, _ = http("GET", f"{HORDE}/generate/status/{jid}")
                gens = json.loads(b).get("generations", [])
                if not gens:
                    log["errors"].append(f"seed {s}: aucune image"); pending.pop(s); continue
                g = gens[0]
                img = g["img"]
                if img.startswith("http"):
                    with urllib.request.urlopen(urllib.request.Request(img, headers={"User-Agent": AGENT}), timeout=120) as r:
                        data = r.read()
                else:
                    data = base64.b64decode(img)
                ext = ".webp" if data[:4] == b"RIFF" else ".png"
                p = os.path.join(out, f"seed{s}{ext}")
                with open(p, "wb") as f:
                    f.write(data)
                if g.get("censored"):
                    log["errors"].append(f"seed {s}: image censuree par le worker (ignorer)")
                log["files"].append(p)
                pending.pop(s)
            except Exception as e:
                log["errors"].append(f"seed {s}: suivi ({e})")
    for s in pending:
        log["errors"].append(f"seed {s}: delai depasse (file AI Horde)")


def pollinations(prompt, negative, seeds, out, size, log):
    q = prompt + (". Avoid: " + negative if negative else "")
    enc = urllib.parse.quote(q, safe="")
    for i, s in enumerate(seeds):
        url = f"https://image.pollinations.ai/prompt/{enc}?width={size}&height={size}&seed={s}&nologo=true&safe=true"
        for attempt in range(6):
            try:
                st, data, _ = http("GET", url, timeout=180)
                p = os.path.join(out, f"seed{s}.jpg")
                with open(p, "wb") as f:
                    f.write(data)
                log["files"].append(p)
                break
            except urllib.error.HTTPError as e:
                if e.code in (402, 429):  # palier anonyme : 1 image a la fois, attendre
                    time.sleep(35)
                    continue
                log["errors"].append(f"seed {s}: HTTP {e.code}"); break
            except Exception as e:
                log["errors"].append(f"seed {s}: {e}"); break
        else:
            log["errors"].append(f"seed {s}: quota anonyme depasse")
        time.sleep(20)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--negative", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33, 44])
    ap.add_argument("--engine", default="horde", choices=["horde", "pollinations"])
    ap.add_argument("--model", default="AlbedoBase XL (SDXL)")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--lora", default="", help="LoRA AI Horde (id CivitAI[:force]), ex. 120096:0.8 = Pixel Art XL")
    ap.add_argument("--source", default="", help="image de base a retoucher (img2img)")
    ap.add_argument("--denoise", type=float, default=0.45, help="force de retouche 0-1 (0,3 garde, 0,6 change)")
    ap.add_argument("--control", default="", help="ControlNet AI Horde (canny, hed, depth...) : modeles SD 1.5 seulement")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    log = {"engine": a.engine, "model": a.model if a.engine == "horde" else "pollinations-anonyme",
           "prompt": a.prompt, "negative": a.negative, "seeds": a.seeds, "files": [], "errors": []}
    if a.engine == "horde":
        log["lora"] = a.lora
        log["source"] = a.source; log["denoise"] = a.denoise if a.source else None; log["control"] = a.control
        horde(a.prompt, a.negative, a.seeds, a.out, a.model, a.size, a.steps, a.cfg, log, a.lora,
              a.source, a.denoise, a.control)
        if not log["files"]:
            log["errors"].append("AI Horde n'a rien rendu : bascule sur Pollinations")
            log["engine"] = "pollinations (secours)"
            pollinations(a.prompt, a.negative, a.seeds[:2], a.out, a.size, log)
    else:
        pollinations(a.prompt, a.negative, a.seeds, a.out, a.size, log)
    with open(os.path.join(a.out, "generate.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    print(json.dumps({"files": log["files"], "errors": log["errors"]}, ensure_ascii=False, indent=1))
    sys.exit(0 if log["files"] else 1)


if __name__ == "__main__":
    main()
