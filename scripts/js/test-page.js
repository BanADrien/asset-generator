#!/usr/bin/env node
'use strict';
/*
 * Parite de la page « vos images » (scripts/js/apercu.js) : navigateur = Node = scripts/sections.py.
 *   node scripts/js/test-page.js [IMAGE[@FACTEUR] ...]
 * Sans argument : le crapaud de reference (references/cible/crapaud-cible-principale-2.png).
 * IMAGE@3.76 : sprite du jeu passe par pixel-fixer, taille d'un pixel imposee (sections.py --facteur) ;
 * sans @ : detection automatique dans la page, sections.py recoit la taille detectee.
 * Pour chaque image : la page est construite avec l'image en cas d'essai, ouverte dans un Chrome / Edge
 * SANS FENETRE (--headless --dump-dom) qui fait le calcul complet (decodage par canvas) ; Node refait le
 * meme calcul (coeur.js) ; sections.py (Python de pgAdmin, variable PYTHON sinon) ecrit ses cartes dans
 * un dossier temporaire. Comparaison : navigateur / Node sur tous les pixels, Node / Python sur les
 * pixels opaques (natif, neutre, sections, normales, carte contre-jour).
 * Navigateur : variable NAVIGATEUR, sinon Edge / Chrome aux emplacements habituels.
 * Code 0 si tout est identique, 1 sinon, 2 sans navigateur ou sans Python. N'ecrit que dans le dossier
 * temporaire du systeme (efface a la fin).
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { pathToFileURL } = require('url');
const C = require('./coeur.js');
const PNG = require('./png.js');
const { construirePage } = require('./apercu.js');

const SKILL = path.resolve(__dirname, '..', '..');
const SECTIONS_PY = path.join(SKILL, 'scripts', 'sections.py');
const url = (im) => `data:image/png;base64,${PNG.encoder(im).toString('base64')}`;

function premier(liste) { return liste.find((p) => p && fs.existsSync(p)); }
const navigateur = () => premier([process.env.NAVIGATEUR,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium']);
const python = () => premier([process.env.PYTHON,
  process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs', 'pgAdmin 4', 'python', 'python.exe'),
  'C:/Program Files/pgAdmin 4/python/python.exe']);

function ecarts(a, b) {   // pixels differents (4 canaux), ou taille
  if (!a || !b) return 'absent';
  if (a.width !== b.width || a.height !== b.height) return `taille ${a.width}x${a.height} / ${b.width}x${b.height}`;
  let d = 0;
  for (let p = 0; p < a.width * a.height; p++) {
    for (let k = 0; k < 4; k++) if (a.data[p * 4 + k] !== b.data[p * 4 + k]) { d++; break; }
  }
  return d;
}
function ecartsOpaques(a, b) {   // opacite et RGB des pixels opaques
  if (a.width !== b.width || a.height !== b.height) return `taille ${a.width}x${a.height} / ${b.width}x${b.height}`;
  let d = 0;
  for (let p = 0; p < a.width * a.height; p++) {
    const oa = a.data[p * 4 + 3] >= 128, ob = b.data[p * 4 + 3] >= 128;
    if (oa !== ob || (oa && [0, 1, 2].some((k) => a.data[p * 4 + k] !== b.data[p * 4 + k]))) d++;
  }
  return d;
}
function rognerOpaque(im, ref) {   // im rogne a la boite des pixels opaques de ref (meme taille)
  let x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
  for (let y = 0; y < ref.height; y++) {
    for (let x = 0; x < ref.width; x++) {
      if (ref.data[(y * ref.width + x) * 4 + 3] >= 128) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    }
  }
  const w = x1 - x0 + 1, h = y1 - y0 + 1, o = { width: w, height: h, data: new Uint8Array(w * h * 4) };
  for (let y = 0; y < h; y++) o.data.set(im.data.subarray(((y + y0) * im.width + x0) * 4, ((y + y0) * im.width + x0 + w) * 4), y * w * 4);
  return o;
}
const depuisB64 = (s) => {
  const [t, b] = s.split(':');
  const [w, h] = t.split('x').map(Number);
  return { width: w, height: h, data: new Uint8Array(Buffer.from(b, 'base64')) };
};

function main() {
  const nav = navigateur(), py = python();
  if (!nav) { console.error('Aucun Chrome / Edge trouve : indiquer son chemin dans la variable NAVIGATEUR'); return 2; }
  if (!py) { console.error('Python introuvable : indiquer son chemin dans la variable PYTHON'); return 2; }
  const args = process.argv.slice(2);
  const specs = (args.length ? args : [path.join(SKILL, 'references', 'cible', 'crapaud-cible-principale-2.png')]).map((s) => {
    const m = /^(.*)@([\d.]+)$/.exec(s);
    return { fichier: path.resolve(m ? m[1] : s), facteur: m ? Number(m[2]) : 0 };
  });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'vos-images-test-'));
  let echec = 0;
  try {
    const cas = specs.map((s, i) => {
      const im = PNG.lirePng(s.fichier);
      const stem = path.join(tmp, `cas${i}`);
      const reglages = s.facteur ? { facteur: s.facteur } : {};
      const node = C.traiterImages([im], reglages);
      // sections.py avec la taille de pixel imposee, ou celle que la page a detectee
      const f = node.f > 1 ? node.f : 0;
      execFileSync(py, ['-I', SECTIONS_PY, s.fichier, ...(f ? ['--facteur', String(f)] : []), '--sortie', stem],
        { stdio: ['ignore', 'ignore', 'inherit'] });
      return { nom: `${path.basename(s.fichier)}${s.facteur ? ` (pixel = ${s.facteur} px)` : ' (auto)'}`, im, stem, facteur: f, reglages, node };
    });
    const page = construirePage({ titre: 'essai', echelle: 6, assets: [], geoPad: 10 },
      cas.map((c) => ({ nom: c.nom, reglages: c.reglages, images: [url(c.im)] })));
    const fichier = path.join(tmp, 'test-page.html');
    fs.writeFileSync(fichier, page);
    const profil = fs.mkdtempSync(path.join(tmp, 'profil-'));
    const dom = execFileSync(nav, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
      `--user-data-dir=${profil}`, '--virtual-time-budget=300000', '--dump-dom', pathToFileURL(fichier).href],
    { encoding: 'utf8', maxBuffer: 512 * 1024 * 1024, timeout: 600000, stdio: ['ignore', 'pipe', 'ignore'] });
    const m = /<pre id="resultat"[^>]*>([\s\S]*?)<\/pre>/.exec(dom);
    const brut = m && m[1].replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    if (!brut) { console.error('Pas de resultat dans la page (calcul non termine ?)'); return 1; }
    const res = JSON.parse(brut);
    console.log('| Cas | Pixel detecte (navigateur / Node) | Navigateur = Node | Node = sections.py | Temps navigateur |');
    console.log('|---|---|---|---|---|');
    cas.forEach((c, i) => {
      const b = res.cas[i];
      if (!b || b.erreur) { echec++; console.log(`| ${c.nom} | erreur : ${b ? b.erreur : 'absent'} | | | |`); return; }
      const n = c.node;
      const fr = n.frames[0], bf = b.frames[0];
      let dn = 0;
      for (const q of ['nat', 'neu', 'sec', 'nor', 'cj', 'cjAp']) {
        const e = ecarts(depuisB64(bf[q]), fr[q]);
        dn += typeof e === 'number' ? e : 1e9;
      }
      // Python : sans --facteur, sections.py garde l'image entiere (pas de rognage) -> rogner comme le coeur
      const L = (s) => PNG.lirePng(`${c.stem}.${s}.png`);
      const nor = L('normales');
      const pyNat = c.facteur ? PNG.lirePng(`${c.stem}.png`) : c.im;
      const rog = (x) => (c.facteur ? x : rognerOpaque(x, nor));
      const detail = [];
      let dp = 0;
      for (const [q, im] of [['nat', rog(pyNat)], ['neu', rog(L('neutre'))], ['sec', rog(L('sections'))], ['nor', rog(nor)], ['cj', rog(L('cj'))]]) {
        const e = ecartsOpaques(fr[q], im);
        if (e !== 0) detail.push(`${q} : ${e}`);
        dp += typeof e === 'number' ? e : 1e9;
      }
      if (dn || dp) echec++;
      console.log(`| ${c.nom} | ${b.f} / ${n.f} | ${dn === 0 ? 'oui, 0 pixel different' : `NON, ${dn} pixels`} | ${dp === 0 ? 'oui, 0 pixel different' : `NON (${detail.join(', ')})`} | ${b.ms} ms |`);
      if (b.messages.length) console.log(`|  | ${b.messages.join(' ')} | | | |`);
    });
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  return echec ? 1 : 0;
}

process.exitCode = main();
