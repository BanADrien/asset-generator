"""Genere des images brutes de pixel art avec Codex (`codex exec`, generateur d'images de
l'utilisateur, valide par lui : image brute notee 7,25, sa meilleure note).

Securite :
- Codex est lance dans un dossier VIDE (le dossier de sortie), bac a sable `workspace-write`
  limite a ce dossier, avec pour seule mission de generer des PNG.
- Ce script ne lit jamais ~/.codex/auth.json ni config.toml ; il n'affiche aucun secret.

Usage :
  python -I generate.py --out DIR --prompt-file PROMPT.txt [--ref IMG ...] [--n 6]
  --ref : images jointes avec `-i` (etalon de style, sprite actuel du sujet, champion a corriger).
  Le prompt doit demander de sauver seed1.png ... seedN.png dans le dossier courant
  (modeles dans references/prompting.md).
Ecrit DIR/seed1.png..., DIR/codex-log.txt et DIR/generate.json (refs, prompt, fichiers, erreurs).
Quota de l utilisateur : 6 images par essai, 4 essais maximum par sprite (par defaut).
"""
import argparse, glob, json, os, shutil, subprocess, sys, time


def find_codex():
    """codex.exe de l'extension VS Code (version la plus recente), sinon `codex` du PATH."""
    if os.environ.get("CODEX_EXE") and os.path.exists(os.environ["CODEX_EXE"]):
        return os.environ["CODEX_EXE"]
    home = os.path.expanduser("~")
    cands = glob.glob(os.path.join(home, ".vscode", "extensions", "openai.chatgpt-*", "bin", "windows-x86_64", "codex.exe"))

    def ver(p):
        name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))
        parts = name.replace("openai.chatgpt-", "").split("-")[0].split(".")
        return tuple(int(x) for x in parts if x.isdigit())
    if cands:
        return max(cands, key=ver)
    return shutil.which("codex")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--n", type=int, default=6, help="images demandees (quota : 6 par essai)")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    if [f for f in os.listdir(a.out) if not f.startswith(".")]:
        raise SystemExit("le dossier de sortie doit etre vide (Codex y travaille en bac a sable)")
    codex = find_codex()
    if not codex:
        raise SystemExit("codex introuvable (extension VS Code openai.chatgpt ou codex dans le PATH)")
    prompt = open(a.prompt_file, encoding="utf-8").read()
    out = os.path.abspath(a.out)
    cmd = [codex, "exec", "-s", "workspace-write", "--skip-git-repo-check", "-C", out]
    for r in a.ref:
        cmd += ["-i", os.path.abspath(r)]
    log = {"generateur": "codex", "codex": os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(codex)))),
           "refs": a.ref, "prompt_file": a.prompt_file, "n": a.n, "files": [], "errors": []}
    t0 = time.time()
    with open(os.path.join(out, "codex-log.txt"), "w", encoding="utf-8") as lf:
        try:
            r = subprocess.run(cmd, input=prompt, text=True, cwd=out, stdout=lf, stderr=subprocess.STDOUT,
                               timeout=a.timeout, encoding="utf-8")
            log["code"] = r.returncode
        except subprocess.TimeoutExpired:
            log["errors"].append("delai depasse")
    log["duree_s"] = round(time.time() - t0)
    log["files"] = sorted(glob.glob(os.path.join(out, "seed*.png")))
    if not log["files"]:
        log["errors"].append("aucune image seed*.png : voir codex-log.txt")
    with open(os.path.join(out, "generate.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    print(json.dumps({"files": log["files"], "errors": log["errors"]}, ensure_ascii=False, indent=1))
    sys.exit(0 if log["files"] else 1)


if __name__ == "__main__":
    main()
