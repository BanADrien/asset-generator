#!/usr/bin/env node
'use strict';
/*
 * Page « VOS IMAGES » : tester n'importe quelle image sous la lumiere, sans rien installer.
 *   node scripts/js/apercu.js --vide [--out CHEMIN.html] [--titre T] [--echelle 6]
 * -> vos-images-lumiere.html (dossier courant par defaut ; jamais d'ecrasement : -2, -3...).
 * Ouvrir la page (double-clic, Chrome / Edge), puis « Charger une image » ou glisser-deposer un PNG /
 * JPG (plusieurs = une animation, dans l'ordre des noms). Le calcul complet se fait DANS la page avec
 * coeur.js (meme calcul que scripts/sections.py) : fond uni retire (tolerance reglable), taille d'un
 * pixel dessine detectee ou imposee, retour a 1 pixel par case, couleurs reduites pour une image
 * peinte, neutre, sections, normales, carte contre-jour ; puis l'image s'affiche sous la lumiere
 * (gabarit viewer/lumiere-template.html tel quel, dans une iframe) avec ses cartes a telecharger.
 * Rien n'est envoye sur Internet.
 * Adapte de tools/lumiere/apercu.js du jeu agarica (feature/eclairage-sections, bd62a60) : ici
 * seulement le mode --vide (pas de manifeste du jeu), modele = gabarit du skill.
 */
const fs = require('fs');
const path = require('path');
const GEO = require('./geo.js');

const SKILL = path.resolve(__dirname, '..', '..');
const MODELE = path.join(SKILL, 'viewer', 'lumiere-template.html');

const enScript = (txt) => txt.replace(/<\//g, '<\\/');

// Page complete : bandeau « vos images » + le gabarit valide dans une iframe, refaite a chaque image
// chargee. Embarque geo.js, coeur.js et perso.js. test : cas de scripts/js/test-page.js (aucun sinon).
function construirePage(donnees, test) {
  const modele = fs.readFileSync(MODELE, 'utf8');
  const lire = (n) => fs.readFileSync(path.join(__dirname, n), 'utf8');
  const titre = String(donnees.titre || 'Vos images').replace(/[<&]/g, '');
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${titre} - eclairage</title>
<style>
  :root { --fond: #0d0b1a; --panneau: #15121f; --trait: #2a2536; --texte: #d9d4e3; --pale: #8f88a0; --accent: #c9b27a; }
  html, body { margin: 0; height: 100%; background: var(--fond); color: var(--texte); font: 13px/1.4 system-ui, "Segoe UI", sans-serif; }
  body { display: flex; flex-direction: column; }
  #perso { padding: 8px 16px; border-bottom: 1px solid var(--trait); background: var(--panneau); display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: center; }
  #perso b { font-weight: 600; }
  #perso button { background: transparent; color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 3px 10px; font: inherit; cursor: pointer; }
  #perso input[type=number], #perso input[type=text] { width: 52px; background: var(--fond); color: var(--texte); border: 1px solid var(--trait); border-radius: 4px; padding: 2px 4px; font: inherit; }
  #perso label { display: inline-flex; gap: 5px; align-items: center; color: var(--pale); }
  #perso .pale, #p-detecte { color: var(--pale); }
  #p-etat { flex-basis: 100%; color: var(--pale); }
  #p-etat:empty { display: none; }
  #p-etat.erreur { color: #f08a8a; }
  #p-etat.prudence { color: var(--accent); }
  #p-telecharger { flex-basis: 100%; }
  #p-telecharger a { color: var(--accent); margin-right: 6px; }
  .ligne-tel { color: var(--pale); }
  body.survol #perso { outline: 2px dashed var(--accent); outline-offset: -4px; }
  #vue { flex: 1; width: 100%; border: 0; min-height: 0; }
</style>
</head>
<body>
<div id="perso">
  <b>Vos images</b>
  <button type="button" id="p-charger">Charger une image</button>
  <span class="pale">ou glissez-déposez un PNG / JPG ici (plusieurs = une animation, dans l'ordre des noms)</span>
  <label title="Fond uni (couleur des 4 coins) effacé depuis les bords ; un blanc enfermé, comme un œil, reste."><input type="checkbox" id="p-fond" checked> Retirer le fond</label>
  <label title="Écart de couleur accepté avec la couleur des coins (0-255)">tolérance <input type="number" id="p-tol" min="0" max="255" value="24"></label>
  <label title="Pixels de l'image par pixel dessiné. Vide = détection automatique de la grille.">Taille d'un pixel dessiné <input type="text" id="p-facteur" placeholder="auto"></label>
  <span id="p-detecte"></span>
  <input type="file" id="p-fichier" accept="image/png,image/jpeg" multiple hidden>
  <div id="p-etat"></div>
  <div id="p-telecharger" hidden></div>
</div>
<iframe id="vue" title="Test d'eclairage"></iframe>
<pre id="resultat" hidden></pre>
${test ? test.map((c, i) => c.images.map((u, k) => `<img id="test-${i}-${k}" src="${u}" hidden alt="">`).join(' ')).join(' ') : ''}
<script>${enScript(lire('geo.js'))}</script>
<script>${enScript(lire('coeur.js'))}</script>
<script>
const MODELE = ${enScript(JSON.stringify(modele))};
const DONNEES_DEPART = ${enScript(JSON.stringify(donnees))};
${test ? `window.TEST_PERSO = ${enScript(JSON.stringify(test))};` : ''}
</script>
<script>${enScript(lire('perso.js'))}</script>
</body>
</html>
`;
}

// chemin libre : nom.html, sinon nom-2.html, nom-3.html...
function cheminLibre(p) {
  if (!fs.existsSync(p)) return p;
  const { dir, name, ext } = path.parse(p);
  for (let k = 2; ; k++) {
    const q = path.join(dir, `${name}-${k}${ext}`);
    if (!fs.existsSync(q)) return q;
  }
}

function main() {
  const argv = process.argv.slice(2);
  const a = { titre: 'Vos images', echelle: 6, out: '' };
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    const suite = () => { if (i + 1 >= argv.length) throw new Error(`valeur manquante pour ${t}`); return argv[++i]; };
    if (t === '--vide') continue;   // seul mode du skill (garde pour la compatibilite avec le jeu)
    else if (t === '--out') a.out = suite();
    else if (t === '--titre') a.titre = suite();
    else if (t === '--echelle') a.echelle = Math.max(1, Math.round(Number(suite())) || 6);
    else { console.error(`option inconnue : ${t}`); return 2; }
  }
  const html = construirePage({ titre: a.titre, echelle: a.echelle, assets: [], geoPad: GEO.GEO_PAD });
  const out = cheminLibre(path.resolve(a.out || 'vos-images-lumiere.html'));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, html);
  console.log(out);
  return 0;
}

if (require.main === module) process.exitCode = main();
module.exports = { construirePage };
