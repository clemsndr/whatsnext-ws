# What's Next — site vitrine

Site statique hébergé sur GitHub Pages (dossier `docs/`).

## Mise en ligne
Settings → Pages → Source : « Deploy from a branch » → branche `main`, dossier `/docs`.

Domaine personnalisé : renseigner `whatsnext.sh` dans Settings → Pages (GitHub crée `docs/CNAME`),
puis ajouter chez le registrar les enregistrements DNS indiqués par GitHub.

## Modifier le contenu
Tous les textes, projets et réglages (Google Form, courriel, domaine) sont dans `tools/build.py`.
Après modification :

    pip install pillow
    python3 tools/build.py          # régénère docs/ (Python 3.12+)
    python3 tools/build.py --fast   # sans recompresser les images

Aperçu local : `python3 -m http.server -d docs` puis http://localhost:8000

Nouvelle photo : la déposer dans `tools/src/photos/`, puis la référencer par son nom (sans extension) dans `build.py`.

## Formulaire de contact
Les réponses sont envoyées au Google Form « What's next domotique ».
Les champs du Google Form doivent rester non obligatoires côté Google (la validation se fait sur le site).
