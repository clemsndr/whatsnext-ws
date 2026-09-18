#!/usr/bin/env python3
"""
Générateur du site What's Next.

    python3 tools/build.py          # régénère tout le dossier docs/
    python3 tools/build.py --fast   # ne recompresse pas les images déjà présentes

Dépendance : Pillow (pip install pillow). Aucune dépendance côté navigateur :
chaque page est un fichier HTML autonome (CSS et JS intégrés), les polices
et les images sont servies depuis docs/assets/.
"""
import html, json, os, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
OUT = HERE.parent / "docs"
FAST = "--fast" in sys.argv

# ─────────────────────────────────────────────────────────────── Configuration
SITE_URL = "https://whatsnext.sh"          # domaine final (canonical, sitemap, Open Graph)
EMAIL = "contact@whatsnext.sh"
VILLE = "Strasbourg, France"
YEAR = "2026"

# Google Form — « Obtenir le lien prérempli » donne les identifiants entry.XXXX
GFORM_ID = "1FAIpQLSciOhcT7jsGWqSRbnfUDdKcAuv69gGmktyUU9XCdCahtpNA6g"
GFORM_ENTRIES = {
    "nom":     "entry.169085524",
    "email":   "entry.1778819574",
    "type":    "entry.237385432",
    "ville":   "entry.1262051605",
    "message": "entry.1859625948",
}
GFORM_ACTION = f"https://docs.google.com/forms/d/e/{GFORM_ID}/formResponse"

# ─────────────────────────────────────────────────────────────── Contenus
NAV = [("expertises", "Expertises", "expertises/"),
       ("realisations", "Réalisations", "realisations/"),
       ("contact", "Contact", "contact/")]

EXPERTISES = [
    dict(id="eclairage", nom="Éclairage", phrase="La lumière suit les heures, pas les interrupteurs.", detail="Gradation, température de couleur, scénarios par pièce et par moment de la journée.", photo="dressing-eclairage", alt="Dressing éclairé par une lumière graduée", marques=[]),
    dict(id="occultation", nom="Occultation", phrase="Volets et BSO orientés sur la course du soleil.", detail="Volets roulants et brise-soleil orientables motorisés, pilotés selon l'ensoleillement et la saison.", photo="bso-brise-soleil", alt="Façade équipée de brise-soleil orientables", marques=[]),
    dict(id="piscine", nom="Piscine & bien-être", phrase="L'eau est prête avant qu'on y pense.", detail="Filtration, traitement, chauffage de l'eau, couverture et spa pilotés depuis la même interface que le reste de la maison.", photo="piscine-interieure", alt="Piscine intérieure éclairée", marques=[]),
    dict(id="chauffage", nom="Chauffage & climat", phrase="Chaque pièce à sa température, sans y toucher.", detail="Régulation pièce par pièce, pompe à chaleur, plancher chauffant et rafraîchissement asservis à la présence et à la saison.", photo="thermostat", alt="Thermostat mural", marques=[]),
    dict(id="audio", nom="Audio & vidéo", phrase="Le son suit la pièce, l'image reste invisible.", detail="Multiroom, home cinéma, intégration des enceintes et des écrans dans l'architecture.", photo="home-cinema", alt="Salle de home cinéma", marques=[]),
    dict(id="securite", nom="Alarme & sécurité", phrase="Une protection qui ne se remarque pas.", detail="Alarme, protection périmétrique, contrôle d'accès, supervision à distance.", photo="detecteur-alarme", alt="Détecteur d'alarme discret au plafond", marques=[]),
    dict(id="video", nom="Vidéosurveillance", phrase="Des caméras qui comprennent ce qu'elles voient.", detail="Analyse par intelligence artificielle, alertes qualifiées, stockage local.", photo="camera-videosurveillance", alt="Caméra de vidéosurveillance en façade", marques=[]),
    dict(id="reseau", nom="Réseau & Wi-Fi", phrase="Une couverture continue, d'un bout à l'autre.", detail="Réseau structuré, Wi-Fi unifié Unifi, séparation des usages et des invités.", photo="baie-reseau", alt="Baie réseau câblée et étiquetée", marques=["Unifi"]),
    dict(id="knx", nom="Bus KNX", phrase="Le standard qui relie tous les lots.", detail="Armoires techniques, modules d'entrée/sortie, programmation et documentation de l'installation.", photo="ecran-mural", alt="Écran de commande mural", marques=["KNX"]),
    dict(id="interfaces", nom="Interfaces", phrase="Des commandes dessinées pour le mur qui les reçoit.", detail="Claviers et écrans Basalte et équivalents, finitions accordées à l'architecture intérieure.", photo="clavier-basalte", alt="Clavier mural Basalte", marques=["Basalte"]),
]

PROJETS = [
    dict(id="villa-contemporaine", titre="Villa contemporaine", lieu="Strasbourg", annee="2024",
         meta=[("Année", "2024"), ("Surface", "420 m²"), ("Lots", "5 systèmes"), ("Durée", "9 semaines")],
         lots=["KNX", "Éclairage", "BSO", "Piscine", "Multiroom"], photo="piscine-interieure",
         alt="Piscine intérieure, éclairage et filtration pilotés",
         chapeau="Une villa de plain-pied en périphérie de Strasbourg, avec piscine intérieure. L'enjeu : faire disparaître la technique sans rien retirer au confort.",
         texte="Bus KNX pour l'ensemble des lots, éclairage scénarisé par pièce, BSO asservis à la course du soleil, régulation du chauffage pièce par pièce, filtration et chauffage de la piscine automatisés, multiroom sur six zones, réseau unifié et vidéosurveillance analysée.",
         details=[("clavier-basalte", "Clavier mural", "Détail — interface murale"), ("ecran-mural", "Écran de commande mural", "Détail — séjour, fin de journée")],
         citation=("On a oublié qu'il y avait un système.", "Le maître d'ouvrage", "Villa, Strasbourg")),
    dict(id="appartement-haussmannien", titre="Appartement haussmannien", lieu="Strasbourg — Neustadt", annee="2023",
         meta=[("Année", "2023"), ("Lots", "4 systèmes")],
         lots=["Éclairage", "Chauffage", "Audio", "Réseau"], photo="dressing-eclairage",
         alt="Dressing éclairé d'un appartement ancien",
         chapeau="Un appartement de la Neustadt, moulures et parquets d'origine. L'enjeu : moderniser sans toucher à ce qui devait rester intact.",
         texte="Éclairage scénarisé sur les circuits existants, régulation du chauffage pièce par pièce, audio multiroom encastré et réseau Wi-Fi unifié couvrant l'ensemble des pièces.",
         details=[("thermostat", "Thermostat mural", "Détail — régulation pièce par pièce"), ("baie-reseau", "Baie réseau", "Détail — local technique")],
         citation=None),
    dict(id="maison-de-vignoble", titre="Maison de vignoble", lieu="Obernai", annee="2023",
         meta=[("Année", "2023"), ("Lots", "3 systèmes")],
         lots=["KNX", "Sécurité", "Vidéo"], photo="clavier-basalte",
         alt="Clavier mural Basalte dans une maison de vignoble",
         chapeau="Une maison ouverte sur les vignes. L'enjeu : protéger sans enfermer.",
         texte="Bus KNX pour l'ensemble des commandes, alarme et protection périmétrique, vidéosurveillance analysée avec alertes qualifiées, interfaces Basalte accordées aux finitions.",
         details=[("camera-videosurveillance", "Caméra de vidéosurveillance", "Détail — façade"), ("portier-entree", "Portier d'entrée", "Détail — accès")],
         citation=None),
]

METHODE = [("01 — Étude", "Relevé des usages, coordination avec l'architecte et les autres corps de métier, plan technique et budget."),
           ("02 — Intégration", "Câblage, armoires, appareillage. Les interfaces sont choisies avec le décorateur, finition par finition."),
           ("03 — Mise en service", "Programmation KNX, scénarios, tests pièce par pièce, remise de la documentation."),
           ("04 — Suivi", "Réglages après emménagement, mises à jour, intervention sous 48 heures.")]

# ─────────────────────────────────────────────────────────────── Icônes (Lucide, ISC)
ICONS = {
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "minus": '<path d="M5 12h14"/>',
    "mail": '<path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"/><rect x="2" y="4" width="20" height="16" rx="2"/>',
    "map-pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
}

def icon(name, size=16, cls="", sw=1.25):
    c = f"ico ico-{name} {cls}".strip()
    return (f'<svg class="{c}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')

e = html.escape

# ─────────────────────────────────────────────────────────────── Images
WIDTHS = [360, 640, 960, 1280, 1600]
IMG = {}  # nom -> dict(w, h, widths)

def tone(im):
    """Applique une fois pour toutes le filtre --image-tone de la charte."""
    from PIL import ImageEnhance, ImageOps
    g = ImageOps.grayscale(im).convert("RGB")
    im = Image.blend(im, g, 0.12)
    im = ImageEnhance.Contrast(im).enhance(1.02)
    return ImageEnhance.Brightness(im).enhance(0.98)

def build_images():
    global Image
    from PIL import Image
    dst = OUT / "assets" / "img"
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted((SRC / "photos").iterdir()):
        name = f.stem
        im = Image.open(f).convert("RGB")
        W, H = im.size
        ws = [w for w in WIDTHS if w < W] + [min(W, WIDTHS[-1])]
        ws = sorted(set(ws))
        IMG[name] = dict(w=W, h=H, widths=ws)
        base = None
        for w in ws:
            a, b = dst / f"{name}-{w}.avif", dst / f"{name}-{w}.webp"
            if FAST and a.exists() and b.exists():
                continue
            if base is None:
                base = tone(im)
            r = base.resize((w, round(H * w / W)), Image.LANCZOS)
            r.save(b, "WEBP", quality=74, method=6)
            r.save(a, "AVIF", quality=52, speed=4)
    # Image de partage (Open Graph)
    og = OUT / "assets" / "og.jpg"
    if not (FAST and og.exists()):
        im = tone(Image.open(SRC / "photos" / "piscine-interieure.webp").convert("RGB"))
        W, H = im.size
        t = round(W * 630 / 1200)
        top = max(0, (H - t) // 2)
        im.crop((0, top, W, top + t)).resize((1200, 630), Image.LANCZOS).save(og, "JPEG", quality=80, optimize=True, progressive=True)

def picture(root, name, alt, sizes, ratio=None, eager=False, cls=""):
    i = IMG[name]
    ws = i["widths"]
    src = lambda ext: ", ".join(f"{root}assets/img/{name}-{w}.{ext} {w}w" for w in ws)
    mid = next((w for w in ws if w >= 960), ws[-1])
    h = round(i["h"] * mid / i["w"])
    load = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture><source type="image/avif" srcset="{src("avif")}" sizes="{sizes}">'
            f'<img src="{root}assets/img/{name}-{mid}.webp" srcset="{src("webp")}" sizes="{sizes}" '
            f'width="{mid}" height="{h}" alt="{e(alt)}" {load}{f" class={cls}" if cls else ""}></picture>')

def figure(root, name, alt, ratio, sizes, caption="", eager=False, extra=""):
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return (f'<figure class="fig {extra}"><div class="fig__media" style="aspect-ratio:{ratio}">'
            f'{picture(root, name, alt, sizes, eager=eager)}</div>{cap}</figure>')

# ─────────────────────────────────────────────────────────────── Gabarit
LOGO_VB = LOGO_SYMBOL = ""

def load_logo():
    global LOGO_VB, LOGO_SYMBOL
    s = (SRC / "logo-wordmark.svg").read_text()
    LOGO_VB = re.search(r'viewBox="([^"]+)"', s).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", s, flags=re.S)
    inner = re.sub(r'fill="[^"]*"', "", inner)
    LOGO_SYMBOL = (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">'
                   f'<symbol id="wn" viewBox="{LOGO_VB}" fill="currentColor">{inner}</symbol></svg>')

def logo():
    w, h = LOGO_VB.split()[2:]
    return f'<svg viewBox="0 0 {w} {h}" width="104" height="20" role="img" aria-label="What\'s Next"><use href="#wn"/></svg>'

def minify_css(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*([{}:;,>])\s*", r"\1", s)
    s = s.replace(";}", "}")
    # restaure les espaces obligatoires dans les requêtes média et calc()
    s = s.replace("and(", "and (")
    return s.strip()

def minify_js(s):
    s = re.sub(r"^\s*//.*$", "", s, flags=re.M)
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())

CSS = minify_css((HERE / "site.css").read_text())
JS = minify_js((HERE / "site.js").read_text())

def typo(doc):
    """Espaces fines insécables à la française, uniquement dans le texte visible."""
    parts = re.split(r"(<script.*?</script>|<style.*?</style>|<[^>]+>)", doc, flags=re.S)
    for k, p in enumerate(parts):
        if p.startswith("<"):
            continue
        p = re.sub(r"[ \u00a0]([:;?!»])", "\u202f\\1", p)
        p = re.sub(r"«[ \u00a0]", "«\u202f", p)
        p = p.replace("'", "\u2019")
        parts[k] = p
    return "".join(parts)

def page(path, *, title, desc, body, active=None, over=False, fab=True, depth=None, schema=None):
    depth = path.count("/") if depth is None else depth
    root = "../" * depth
    canonical = SITE_URL + "/" + (path[:-len("index.html")] if path.endswith("index.html") else path)
    nav = "".join(
        f'<a href="{root}{href}"{" aria-current=page" if key == active else ""}>{label}</a>'
        for key, label, href in NAV)
    hero_preload = ""
    if over:
        ws = IMG["dressing-eclairage"]["widths"]
        hero_preload = (f'<link rel="preload" as="image" type="image/avif" fetchpriority="high" imagesizes="100vw" '
                        f'imagesrcset="{", ".join(f"{root}assets/img/dressing-eclairage-{w}.avif {w}w" for w in ws)}">')
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#2D2B2B">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="What's Next">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="preload" href="{root}assets/fonts/cormorant.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/jost.woff2" as="font" type="font/woff2" crossorigin>
{hero_preload}
<script>document.documentElement.classList.add("js")</script>
<style>{CSS.replace("__ROOT__", root)}</style>
{ld}
</head>
<body>
{LOGO_SYMBOL}
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="site-header{" is-over" if over else ""}">
<a class="logo" href="{root or "./"}" aria-label="What's Next — accueil">{logo()}</a>
<nav class="site-nav" id="menu" aria-label="Navigation principale">{nav}<a class="btn btn--primary nav-cta" href="{root}contact/">Parler d'un projet</a></nav>
<a class="btn btn--secondary btn--sm header-cta" href="{root}contact/">Parler d'un projet</a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="menu" aria-label="Menu">{icon("menu", 22)}{icon("x", 22)}</button>
</header>
<main id="contenu">
{body(root)}
</main>
{footer(root)}
{f'<a class="btn btn--primary btn--sm fab" href="{root}contact/">{icon("mail")}<span>Contact</span></a>' if fab else ""}
<script>{JS}</script>
</body>
</html>
"""
    doc = typo(doc)
    out = OUT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    PAGES.append(canonical)

def footer(root):
    xp = "".join(f'<li><a href="{root}expertises/#{x["id"]}">{x["nom"]}</a></li>' for x in EXPERTISES[:5])
    return f"""<footer class="site-footer">
<div class="footer-grid">
<div class="footer-col"><a class="logo" href="{root or "./"}" aria-label="What's Next — accueil">{logo()}</a>
<p>Intégrateur global : un seul interlocuteur pour l'ensemble des systèmes techniques de la maison.</p></div>
<div class="footer-col"><span class="footer-title">Expertises</span><ul>{xp}</ul></div>
<div class="footer-col"><span class="footer-title">Maison</span><ul>
<li><a href="{root}realisations/">Réalisations</a></li><li><a href="{root}expertises/">Les dix domaines</a></li></ul></div>
<div class="footer-col"><span class="footer-title">Contact</span><ul>
<li><a class="footer-contact" href="mailto:{EMAIL}">{icon("mail", 15)}{EMAIL}</a></li>
<li><span class="footer-contact">{icon("map-pin", 15)}{VILLE}</span></li></ul></div>
</div>
<div class="footer-legal"><span>© {YEAR} What's Next — Tous droits réservés</span><a href="{root}mentions-legales/">Mentions légales</a></div>
</footer>"""

def sh(eyebrow, title, lead="", level=2, reveal=True):
    lead = f"<p>{lead}</p>" if lead else ""
    return f'<header class="sh{" reveal" if reveal else ""}"><span class="eyebrow eyebrow--rule">{eyebrow}</span><h{level}>{title}</h{level}>{lead}</header>'

def section(inner, tone="", sid="", style=""):
    cls = "section" + (f" section--{tone}" if tone else "")
    return f'<section class="{cls}"{f" id={sid}" if sid else ""}{f" style={style!r}" if style else ""}><div class="container">{inner}</div></section>'

def proj_card(root, p, i=0, prefix="realisations/"):
    cap = f"<strong>{p['titre']}</strong> — {p['lieu']}, {p['annee']}"
    return (f'<a class="proj reveal" style="--d:{i*90}ms" href="{root}{prefix}{p["id"]}/">'
            + figure(root, p["photo"], f"{p['titre']}, {p['lieu']}", "3 / 4", "(max-width: 899px) 78vw, 30vw", cap) + "</a>")

# ─────────────────────────────────────────────────────────────── Pages
PAGES = []

def home(root):
    cards = "".join(
        f'<a class="card reveal" style="--d:{(i%3)*90}ms" href="{root}expertises/#{x["id"]}"><span class="card__eyebrow">{i+1:02d} — {x["nom"]}</span>'
        f'<h3>{x["phrase"]}</h3><div class="card__body">{x["detail"]}</div><span class="card__more">En savoir plus {icon("arrow-right", 14)}</span></a>'
        for i, x in enumerate(EXPERTISES[:6]))
    projets = "".join(proj_card(root, p, i) for i, p in enumerate(PROJETS))
    acc = "".join(
        f'<details name="methode"{" open" if i == 0 else ""}><summary>{q}{icon("plus", 18)}{icon("minus", 18)}</summary><p>{a}</p></details>'
        for i, (q, a) in enumerate(METHODE))
    return f"""<div class="hero">
{picture(root, "dressing-eclairage", "Dressing éclairé, commande murale intégrée", "100vw", eager=True)}
<div class="hero__inner"><div class="hero__content">
<span class="eyebrow eyebrow--rule eyebrow--inverse">Intégrateur domotique</span>
<h1>L'intelligence d'une maison se mesure à son silence.</h1>
<p class="hero__lead">Éclairage, occultation, chauffage, piscine, audio, sécurité, réseau : un seul système, un seul interlocuteur.</p>
<div class="btn-row"><a class="btn btn--primary" href="{root}contact/"><span>Parler d'un projet</span>{icon("arrow-right")}</a>
<a class="btn btn--inverse" href="#realisations">Nos réalisations</a></div>
</div></div></div>
{section(sh("Nos expertises", "Tous les systèmes techniques de la maison, conçus ensemble.", "Chaque lot est étudié avec les autres : ce qui se pilote d'un seul geste a été pensé d'un seul tenant.")
 + f'<div class="cards mt-9">{cards}</div><div class="mt-8"><a class="btn btn--ghost" href="{root}expertises/"><span>Voir les dix domaines</span>{icon("arrow-right")}</a></div>', sid="expertises")}
{section(f'''<div class="band"><blockquote class="quote reveal"><p>« Tout fonctionne, et rien ne se voit. »</p><footer><cite>Maison L.</cite><span>Villa, Strasbourg — 2023</span></footer></blockquote>
<div class="stats reveal" style="--d:120ms"><div class="stat"><b>2</b><span>Années d'expérience</span></div><div class="stat"><b>10</b><span>Installations</span></div><div class="stat"><b>48 h</b><span>Délai de réponse</span></div></div></div>''', tone="ink")}
{section(sh("Réalisations", "Trois maisons, trois usages, un même niveau de finition.") + f'<div class="projects mt-8">{projets}</div>', tone="card", sid="realisations")}
{section(f'<div class="split">{sh("Méthode", "De l’étude à la mise en service.", "Une seule équipe suit le projet, du plan d’exécution aux réglages qui suivent l’emménagement.")}<div class="acc reveal" style="--d:120ms">{acc}</div></div>', sid="methode")}
{section(f'<div class="cta-band reveal"><h2>Un projet en cours ? Parlons-en avant les plans.</h2><a class="btn btn--primary btn--lg" href="{root}contact/"><span>Prendre rendez-vous</span>{icon("arrow-right")}</a></div>', tone="card", style="padding-top:0")}"""

def expertises(root):
    tabs = "".join(
        f'<a class="xp-tab" role="tab" id="tab-{x["id"]}" href="#{x["id"]}" aria-controls="{x["id"]}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{x["nom"]}{icon("arrow-right", 15)}</a>'
        for i, x in enumerate(EXPERTISES))
    inclus = "".join(f"<li>{icon('check', 15)}{t}</li>" for t in ["Étude et plans d'exécution", "Fourniture et intégration", "Programmation et scénarios", "Documentation et suivi"])
    panels = ""
    for i, x in enumerate(EXPERTISES):
        badges = "".join(f'<span class="badge badge--accent">{m}</span>' for m in x["marques"])
        badges = f'<div class="badges">{badges}</div>' if badges else ""
        panels += (f'<section class="xp-panel{" is-active" if i == 0 else ""}" id="{x["id"]}" role="tabpanel" aria-labelledby="tab-{x["id"]}">'
                   + figure(root, x["photo"], x["alt"], "16 / 9", "(max-width: 899px) 100vw, 62vw")
                   + f'<div class="xp-detail"><div><span class="eyebrow">{x["nom"]}</span><h2>{x["phrase"]}</h2><p>{x["detail"]}</p>'
                   f'<a class="btn btn--ghost" href="{root}contact/"><span>Discuter de ce lot</span>{icon("arrow-right")}</a></div>'
                   f'<div class="xp-side"><span class="eyebrow">Inclus</span><ul class="checklist">{inclus}</ul>{badges}</div></div></section>')
    return (section(sh("Expertises", "Dix domaines, un seul système.", "Le périmètre couvert par What's Next sur une installation complète.", level=1, reveal=False), tone="card", style="padding-bottom:var(--space-8)")
            + section(f'<div class="xp"><nav class="xp-tabs" role="tablist" aria-label="Domaines" aria-orientation="vertical">{tabs}</nav><div>{panels}</div></div>', tone="card", style="padding-top:0"))

def realisations(root):
    projets = "".join(proj_card(root, p, i) for i, p in enumerate(PROJETS))
    return (section(sh("Réalisations", "Trois maisons, trois usages, un même niveau de finition.", "Chaque projet est conçu avec l'architecte et livré documenté, pièce par pièce.", level=1, reveal=False)
                    + f'<div class="projects mt-8">{projets}</div>', tone="card")
            + section(f'<div class="ink-row"><h2>Un projet comparable ? Parlons-en.</h2><a class="btn btn--inverse" href="{root}contact/"><span>Parler d\'un projet</span>{icon("arrow-right")}</a></div>', tone="ink"))

def projet(p, nxt):
    def body(root):
        meta = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in p["meta"])
        badges = "".join(f'<span class="badge">{l}</span>' for l in p["lots"])
        det = "".join(figure(root, n, a, "3 / 4", "(max-width: 899px) 50vw, 24vw", c) for n, a, c in p["details"])
        if p["citation"]:
            q, who, role = p["citation"]
            ink = f'<blockquote class="quote reveal"><p>« {q} »</p><footer><cite>{who}</cite><span>{role}</span></footer></blockquote>'
        else:
            ink = '<h2 class="reveal">Un projet comparable ? Parlons-en.</h2>'
        return (section(f'<a class="back" href="../">{icon("arrow-left", 14)} Réalisations</a>'
                        f'<div class="proj-head"><h1>{p["titre"]}, {p["lieu"]}</h1><dl class="meta">{meta}</dl></div>', tone="card", style="padding-bottom:var(--space-7)")
                + f'<div class="wide">{figure(root, p["photo"], p["alt"], "21 / 9", "100vw", eager=True)}</div>'
                + section(f'<div class="two"><div class="reveal"><span class="eyebrow eyebrow--rule">Le projet</span><p class="lede">{p["chapeau"]}</p>'
                          f'<p class="body-text">{p["texte"]}</p><div class="badges mt-8" style="margin-top:var(--space-5)">{badges}</div></div>'
                          f'<div class="two-figs reveal" style="--d:120ms">{det}</div></div>', tone="card")
                + section(f'<div class="ink-row">{ink}<a class="btn btn--inverse" href="{root}contact/"><span>Parler d\'un projet</span>{icon("arrow-right")}</a></div>', tone="ink")
                + section(f'<a class="next" href="../{nxt["id"]}/"><span><span class="eyebrow">Réalisation suivante</span><strong>{nxt["titre"]}</strong></span>{icon("arrow-right", 24)}</a>', tone="card"))
    return body

def contact(root):
    E = GFORM_ENTRIES
    opts = "".join(f"<option>{o}</option>" for o in ["Construction neuve", "Rénovation", "Extension", "Autre"])
    form = f"""<form class="form" data-gform action="{GFORM_ACTION}" method="POST">
<label class="field"><span class="field__label">Nom *</span><input name="{E['nom']}" autocomplete="name" placeholder="Votre nom" required></label>
<label class="field"><span class="field__label">Courriel *</span><input type="email" name="{E['email']}" autocomplete="email" placeholder="vous@domaine.fr" required></label>
<label class="field"><span class="field__label">Type de projet</span><span class="select"><select name="{E['type']}"><option value="">Choisir</option>{opts}</select>{icon("chevron-down")}</span></label>
<label class="field"><span class="field__label">Ville</span><input name="{E['ville']}" autocomplete="address-level2" placeholder="Strasbourg"><span class="field__hint">Facultatif</span></label>
<label class="field field--full"><span class="field__label">Votre projet *</span><textarea name="{E['message']}" rows="5" required></textarea><span class="field__hint">Quelques lignes suffisent.</span></label>
<div class="hp" aria-hidden="true"><label>Ne pas remplir<input tabindex="-1" autocomplete="off"></label></div>
<p class="form-error" role="alert" hidden>L'envoi n'a pas abouti. Réessayez, ou écrivez-nous à <a class="link" href="mailto:{EMAIL}">{EMAIL}</a>.</p>
<div class="form-foot">
<label class="check"><input type="checkbox" required><span class="check__box">{icon("check", 12, sw=2)}</span><span class="check__label">J'accepte d'être recontacté au sujet de ce projet. <a class="link" href="{root}mentions-legales/#donnees">Données personnelles</a></span></label>
<button class="btn btn--primary" type="submit"><span>Envoyer</span>{icon("arrow-right")}</button>
</div>
</form>
<div class="sent" id="form-ok" tabindex="-1" role="status" hidden>{icon("check", 22)}<h2>Message reçu.</h2><p>Nous revenons vers vous sous 48 heures.</p>
<button class="btn btn--ghost" type="button" id="form-reset">Nouveau message</button></div>"""
    info = (sh("Contact", "Décrivez votre projet en quelques lignes.", "Nous répondons sous 48 heures. L'échange initial est sans engagement.", level=1, reveal=False)
            + f'<hr><div class="contact-lines"><a href="mailto:{EMAIL}">{icon("mail")}{EMAIL}</a><span>{icon("map-pin")}{VILLE}</span></div>')
    return section(f'<div class="contact"><div>{info}</div><div>{form}</div></div>', tone="card")

def mentions(root):
    T = lambda s: f'<span class="todo">[{s}]</span>'
    return section(f"""<div class="prose">
<h1>Mentions légales</h1>
<h2>Éditeur du site</h2>
<p>What's Next, SAS au capital de 1 000 €<br>Siège social : 10 rue Sophie Germain, 67720 Hœrdt<br>SIREN 934 875 915 — TVA intracommunautaire FR21934875915<br>Courriel : <a class="link" href="mailto:{EMAIL}">{EMAIL}</a></p>
<p>Président : Charlie Sierra Invest SAS<br>Directeur de la publication : le représentant légal de Charlie Sierra Invest SAS, présidente de What's Next</p>
<h2>Hébergement</h2>
<p>GitHub Pages — GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis.</p>
<h2 id="donnees">Données personnelles</h2>
<p>Les informations saisies dans le formulaire de contact (nom, courriel, type de projet, ville, description) servent uniquement à répondre à votre demande et à préparer un éventuel rendez-vous. Elles sont transmises via Google Forms (Google Ireland Ltd.) et conservées trois ans au plus après le dernier échange.</p>
<p>Vous disposez d'un droit d'accès, de rectification, d'effacement et d'opposition, que vous pouvez exercer en écrivant à <a class="link" href="mailto:{EMAIL}">{EMAIL}</a>. Vous pouvez également adresser une réclamation à la CNIL.</p>
<h2>Cookies</h2>
<p>Ce site ne dépose aucun cookie et n'utilise aucun outil de mesure d'audience.</p>
<h2>Crédits</h2>
<p>Photographies : What's Next. Icônes : Lucide (licence ISC). Polices : Cormorant Garamond et Jost (licence SIL Open Font License).</p>
</div>""", tone="card")

def notfound(root):
    return section(f'{sh("Erreur 404", "Cette page n’existe pas, ou plus.", "Le lien est peut-être ancien. Tout le reste est à sa place.", level=1, reveal=False)}'
                   f'<div class="btn-row mt-8"><a class="btn btn--primary" href="{root or "./"}"><span>Retour à l\'accueil</span>{icon("arrow-right")}</a>'
                   f'<a class="btn btn--ghost" href="{root}contact/"><span>Nous écrire</span>{icon("arrow-right")}</a></div>', tone="card")

# ─────────────────────────────────────────────────────────────── Build
def main():
    if OUT.exists():
        for p in OUT.iterdir():
            if p.name == "assets" and FAST:
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    (OUT / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for f in (SRC / "fonts").iterdir():
        shutil.copy(f, OUT / "assets" / "fonts" / f.name)
    shutil.copy(SRC / "favicon.svg", OUT / "favicon.svg")
    build_images()
    load_logo()

    org = {"@context": "https://schema.org", "@type": "HomeAndConstructionBusiness", "name": "What's Next",
           "description": "Intégrateur domotique haut de gamme : éclairage, occultation, chauffage, piscine, audio-vidéo, sécurité, réseau.",
           "url": SITE_URL, "email": EMAIL, "image": SITE_URL + "/assets/og.jpg",
           "address": {"@type": "PostalAddress", "addressLocality": "Strasbourg", "addressCountry": "FR"},
           "areaServed": ["Alsace", "Grand Est"]}

    page("index.html", title="What's Next — Intégrateur domotique haut de gamme, Strasbourg",
         desc="Éclairage, occultation, chauffage, piscine, audio, sécurité, réseau : un seul système, un seul interlocuteur. Intégration domotique KNX en Alsace.",
         body=home, over=True, schema=org)
    page("expertises/index.html", title="Expertises — What's Next",
         desc="Dix domaines, un seul système : éclairage, occultation, piscine, chauffage, audio-vidéo, alarme, vidéosurveillance, réseau Wi-Fi, bus KNX, interfaces.",
         body=expertises, active="expertises")
    page("realisations/index.html", title="Réalisations — What's Next",
         desc="Villas, appartements et maisons équipés par What's Next en Alsace.", body=realisations, active="realisations")
    for i, p in enumerate(PROJETS):
        nxt = PROJETS[(i + 1) % len(PROJETS)]
        page(f"realisations/{p['id']}/index.html", title=f"{p['titre']}, {p['lieu']} — What's Next",
             desc=p["chapeau"], body=projet(p, nxt), active="realisations")
    page("contact/index.html", title="Contact — What's Next",
         desc="Décrivez votre projet en quelques lignes. Nous répondons sous 48 heures.", body=contact, active="contact", fab=False)
    page("mentions-legales/index.html", title="Mentions légales — What's Next",
         desc="Mentions légales et données personnelles du site What's Next.", body=mentions)

    # 404 : servie à n'importe quelle profondeur → chemins absolus vers la racine du site
    global PAGES
    saved = list(PAGES)
    page("404.html", title="Page introuvable — What's Next", desc="Page introuvable.", body=notfound, depth=0)
    PAGES = saved
    p404 = OUT / "404.html"
    s = p404.read_text()
    base = "<base href=\"/\"><script>(function(){var h=location.hostname,p=location.pathname.split('/')[1];if(/github\\.io$/.test(h)&&p){document.querySelector('base').href='/'+p+'/'}})()</script>"
    p404.write_text(s.replace("<meta charset=\"utf-8\">", "<meta charset=\"utf-8\">" + base, 1))

    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{u}</loc></url>" for u in PAGES)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')

    placeholders = [k for k, v in GFORM_ENTRIES.items() if "A_REMPLACER" in v]
    print(f"✓ {len(PAGES) + 1} pages générées dans {OUT}")
    if placeholders:
        print("⚠ Formulaire : identifiants Google Form à renseigner →", ", ".join(placeholders))

if __name__ == "__main__":
    main()
