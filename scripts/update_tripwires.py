"""
update_tripwires.py
===================
Lancé toutes les heures par GitHub Actions.
1. Collecte les articles RSS des dernières 24h (11 sources)
2. Appelle Claude pour évaluer les 20 événements tripwires
3. Calcule E08 / E09 via yFinance
4. Sauvegarde data/auto_scores.json

Variables d'environnement requises (GitHub Secrets) :
  ANTHROPIC_API_KEY  — clé API Claude
"""

import os, json, time, logging, datetime
import requests, feedparser, anthropic, yfinance as yf, pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

# ── Chemins ───────────────────────────────────────────────────────────────────
ROOT      = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR  = os.path.join(ROOT, "data")
OUT_FILE  = os.path.join(DATA_DIR, "auto_scores.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Sources RSS ───────────────────────────────────────────────────────────────
RSS_SOURCES = [
    ("Al Jazeera",        "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Guardian World",    "https://www.theguardian.com/world/rss"),
    ("NYT World",         "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("OilPrice",          "https://oilprice.com/rss/main"),
    ("Hellenic Shipping", "https://www.hellenicshippingnews.com/feed/"),
    ("Splash247",         "https://splash247.com/feed/"),
    ("Maritime Exec.",    "https://maritime-executive.com/rss/articles"),
    ("Middle East Eye",   "https://www.middleeasteye.net/rss"),
    ("Arab News",         "https://www.arabnews.com/rss.xml"),
    ("MarineLink",        "https://www.marinelink.com/rss/news"),
    ("Energy Monitor",    "https://www.energymonitor.ai/feed/"),
]

RSS_HDR      = {"User-Agent": "Mozilla/5.0 (compatible; OrmuzWatch/2.0)"}
RSS_LOOKBACK = 24   # heures
RSS_KEYWORDS = [    # pré-filtre léger : au moins un de ces mots dans le titre
    "iran", "hormuz", "gulf", "saudi", "oil", "tanker", "ship", "houthi",
    "israel", "sanctions", "iea", "opec", "aramco", "lng", "pipeline",
    "crude", "energy", "strait", "persian", "red sea", "missile",
]

# ── 20 événements tripwires ───────────────────────────────────────────────────
EVENTS = {
    "E01": {"label": "Saisie tanker par IRGC",                    "cat": "Physique — Détroit",        "weight": 10},
    "E02": {"label": "Tir de sommation sur VLCC",                 "cat": "Physique — Détroit",        "weight": 9},
    "E03": {"label": "Mines détectées — chenaux navigation",      "cat": "Physique — Détroit",        "weight": 10},
    "E04": {"label": "Frappe drone ADNOC / Fujairah",             "cat": "Physique — Infrastructure", "weight": 8},
    "E05": {"label": "Attaque pipeline Petroline (East-West)",    "cat": "Physique — Infrastructure", "weight": 9},
    "E06": {"label": "Frappe Abqaiq / Ras Tanura",               "cat": "Physique — Infrastructure", "weight": 10},
    "E07": {"label": "Lloyd's suspend war-risk Golfe",            "cat": "Finance — Assurance",       "weight": 8},
    "E08": {"label": "Squeeze VLCC (taux > 150k$/j)",            "cat": "Finance — Fret",            "weight": 7},
    "E09": {"label": "Backwardation extrême Brent",              "cat": "Finance — Prix",            "weight": 7},
    "E10": {"label": "Armateur majeur — reroutage Cap BEH",      "cat": "Décision — Armateur",      "weight": 8},
    "E11": {"label": "Acheteur chinois annule lifting",           "cat": "Décision — Acheteur",      "weight": 7},
    "E12": {"label": "Raffinerie asiatique active SPR national",  "cat": "Décision — Acheteur",      "weight": 8},
    "E13": {"label": "Frappe israélienne installations Iran",     "cat": "Militaire — Escalade",     "weight": 10},
    "E14": {"label": "Houthis reprennent frappes Mer Rouge",     "cat": "Militaire — Escalade",     "weight": 7},
    "E15": {"label": "Iran — exercices militaires non notifiés", "cat": "Militaire — Signal",       "weight": 6},
    "E16": {"label": "Sanctions secondaires US élargies Chine",  "cat": "Politique — Sanctions",    "weight": 8},
    "E17": {"label": "Activation SPR officielle IEA / Asie",    "cat": "Institutionnel — SPR",     "weight": 9},
    "E18": {"label": "Chute >40% trafic tanker AIS (72h)",      "cat": "AIS — Signal agrégé",      "weight": 10},
    "E19": {"label": "Défaut négociant majeur",                  "cat": "Systémique",               "weight": 7},
    "E20": {"label": "Cyberattaque SCADA terminal export",       "cat": "Systémique",               "weight": 9},
}


# ── 1. Collecte RSS ───────────────────────────────────────────────────────────

def fetch_articles() -> list[dict]:
    """Retourne les articles pertinents des dernières 24h depuis toutes les sources RSS."""
    cutoff   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=RSS_LOOKBACK)
    articles = []

    for source, url in RSS_SOURCES:
        try:
            r    = requests.get(url, headers=RSS_HDR, timeout=15)
            feed = feedparser.parse(r.text if r.status_code == 200 else "")
            n    = 0
            for entry in feed.entries:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub:
                    dt = datetime.datetime(*pub[:6], tzinfo=datetime.timezone.utc)
                    if dt < cutoff:
                        continue
                title   = entry.get("title",   "").strip()
                summary = entry.get("summary", "").strip()[:400]
                # Pré-filtre : au moins un mot-clé dans le titre
                if not title or not any(k in title.lower() for k in RSS_KEYWORDS):
                    continue
                articles.append({"source": source, "title": title, "summary": summary})
                n += 1
            log.info(f"  {source}: {n} articles retenus")
        except Exception as e:
            log.warning(f"  {source}: {e}")
        time.sleep(0.5)

    log.info(f"Total : {len(articles)} articles pertinents collectés")
    return articles


# ── 2. Analyse Claude AI ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un analyste senior spécialisé dans la géopolitique des hydrocarbures et la sécurité maritime.
Tu analyses les signaux d'alerte (tripwires) liés à la fermeture du détroit d'Ormuz (fermé depuis le 28 février 2026).

Contexte actuel :
- Le détroit d'Ormuz est fermé depuis J+60+ jours suite au conflit Iran/US-Israël
- Trafic actuel : 6-7 navires/jour vs baseline 138 (−95%)
- Brent à ~107$/bbl (pic 126$/bbl le 8 mars 2026)
- Cessez-le-feu US-Iran annoncé le 9 avril mais détroit toujours fermé

Échelle de statut :
0 = Inactif    : aucun signal dans l'actualité
1 = Veille     : signal faible, surveiller
2 = Alerte     : signal confirmé, situation dégradée
3 = Déclenché  : événement avéré ou imminent

Règles d'analyse :
- Un article général sur "le conflit Iran" ne suffit pas pour déclencher E01 (saisie tanker)
- Exige des éléments concrets et spécifiques à chaque événement
- Distingue les commentaires/analyses des faits opérationnels
- Sois conservateur : mieux vaut un faux négatif qu'un faux positif
- Le contexte de détroit fermé élève naturellement le niveau de base

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après, avec exactement cette structure :
{
  "E01": {"status": 0, "signal": "résumé en 1 phrase", "reasoning": "explication 2-3 phrases"},
  "E02": {...},
  ...
  "E20": {...}
}"""


def analyse_with_claude(articles: list[dict], api_key: str) -> dict:
    """Envoie les articles à Claude et retourne les statuts pour les 18 événements news."""

    # Construire la liste des événements à analyser (hors E08/E09 = yFinance)
    events_text = "\n".join(
        f"{eid} [{ev['cat']}] — {ev['label']} (poids {ev['weight']}/10)"
        for eid, ev in EVENTS.items()
        if eid not in ("E08", "E09")
    )

    # Construire le corpus d'articles
    if articles:
        articles_text = "\n".join(
            f"[{a['source']}] {a['title']}\n  {a['summary']}"
            for a in articles[:80]   # max 80 articles pour rester dans le contexte
        )
    else:
        articles_text = "Aucun article collecté dans les dernières 24h."

    user_prompt = f"""Analyse les {len(articles)} articles suivants collectés dans les dernières 24h.
Évalue chacun des 18 événements tripwires (E01 à E07 + E10 à E20, hors E08 et E09 qui sont calculés séparément).

ÉVÉNEMENTS À ÉVALUER :
{events_text}

ARTICLES COLLECTÉS :
{articles_text}

Donne un statut (0-3) pour chaque événement en te basant strictement sur ce qui est rapporté dans les articles.
Pour les événements sans signal dans les articles, mets statut 0."""

    client   = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model      = "claude-opus-4-5",
        max_tokens = 4096,
        system     = SYSTEM_PROMPT,
        messages   = [{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    # Nettoyer les éventuels backticks markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── 3. yFinance — E08 + E09 ──────────────────────────────────────────────────

def compute_market_events() -> dict:
    """E08 : proxy tanker stocks. E09 : proxy backwardation Brent."""
    results = {}

    # E08 : FRO / STNG / DHT vs MA20
    try:
        pcts = []
        for ticker in ["FRO", "STNG", "DHT"]:
            for _ in range(3):
                try:
                    df = yf.download(ticker, period="30d", interval="1d",
                                     progress=False, auto_adjust=True)
                    if not df.empty and len(df) >= 5:
                        c   = df["Close"].dropna().squeeze()
                        cur = float(c.iloc[-1])
                        ma  = float(c.tail(20).mean())
                        pcts.append((ticker, (cur - ma) / ma * 100))
                        log.info(f"  {ticker}: {cur:.2f} vs MA20 {ma:.2f} → {pcts[-1][1]:+.1f}%")
                    break
                except Exception:
                    time.sleep(5)
            time.sleep(2)

        if pcts:
            avg    = sum(p for _, p in pcts) / len(pcts)
            status = 3 if avg > 30 else 2 if avg > 15 else 1 if avg > 7 else 0
            results["E08"] = {
                "status":    status,
                "signal":    f"Tankers (FRO/STNG/DHT) moy vs MA20 : {avg:+.1f}%",
                "reasoning": " | ".join(f"{t}: {p:+.1f}%" for t, p in pcts),
            }
    except Exception as e:
        log.warning(f"E08 error: {e}")

    # E09 : Brent vs MA30
    try:
        df = yf.download("BZ=F", period="40d", interval="1d",
                         progress=False, auto_adjust=True)
        if not df.empty and len(df) >= 5:
            c   = df["Close"].dropna().squeeze()
            cur = float(c.iloc[-1])
            ma  = float(c.tail(30).mean())
            dev = (cur - ma) / ma * 100
            log.info(f"  Brent: {cur:.2f} vs MA30 {ma:.2f} → {dev:+.1f}%")
            status = 3 if dev > 25 else 2 if dev > 15 else 1 if dev > 8 else 0
            results["E09"] = {
                "status":    status,
                "signal":    f"Brent {cur:.1f}$/bbl vs MA30 {ma:.1f}$ → {dev:+.1f}%",
                "reasoning": f"Déviation de {dev:+.1f}% par rapport à la moyenne 30j. "
                             f"Seuils : Veille +8%, Alerte +15%, Déclenché +25%.",
            }
    except Exception as e:
        log.warning(f"E09 error: {e}")

    return results


# ── 4. Runner principal ───────────────────────────────────────────────────────

def run() -> dict:
    log.info("=" * 55)
    log.info(f"Update tripwires — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("=" * 55)

    api_key  = os.environ.get("ANTHROPIC_API_KEY", "")
    results  = {}
    now      = datetime.datetime.now().isoformat()

    # ── RSS + Claude (GitHub Actions uniquement)
    if os.environ.get("CI") == "true":
        if not api_key:
            log.error("ANTHROPIC_API_KEY manquante — ajoutez-la dans GitHub Secrets")
        else:
            log.info("\n[1] Collecte RSS...")
            articles = fetch_articles()

            log.info("\n[2] Analyse Claude AI...")
            try:
                ai_scores = analyse_with_claude(articles, api_key)
                for eid, data in ai_scores.items():
                    results[eid] = {
                        "status":     data.get("status", 0),
                        "signal":     data.get("signal", ""),
                        "reasoning":  data.get("reasoning", ""),
                        "source":     "Claude AI + RSS",
                        "articles":   [
                            f"{a['title']} ({a['source']})"
                            for a in articles
                            if any(
                                kw in a["title"].lower()
                                for kw in EVENTS.get(eid, {}).get("label", "").lower().split()
                                if len(kw) > 4
                            )
                        ][:3],
                        "updated_at": now,
                    }
                log.info(f"  Claude a évalué {len(ai_scores)} événements")
            except Exception as e:
                log.error(f"Erreur Claude API: {e}")
    else:
        # Streamlit Cloud : charger le fichier existant sans le modifier
        log.info("\n[RSS+AI] Non exécuté (Streamlit Cloud). Chargement du dernier fichier.")
        if os.path.exists(OUT_FILE):
            with open(OUT_FILE) as f:
                results = json.load(f)

    # ── yFinance — toujours actif
    log.info("\n[3] yFinance E08 + E09...")
    for eid, data in compute_market_events().items():
        results[eid] = {**data, "source": "yFinance", "updated_at": now}

    # ── Sauvegarde (GitHub Actions uniquement)
    if os.environ.get("CI") == "true":
        with open(OUT_FILE, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        log.info(f"\n✅ {OUT_FILE} sauvegardé ({len(results)} événements)")

    # ── Résumé
    actifs = [(e, v) for e, v in results.items() if v.get("status", 0) > 0]
    lbl    = {1: "Veille", 2: "Alerte", 3: "Déclenché"}
    if actifs:
        log.info(f"\n⚠  {len(actifs)} événement(s) actif(s) :")
        for e, v in sorted(actifs, key=lambda x: -x[1]["status"]):
            log.info(f"  {lbl.get(v['status'],'?')} {e} — {v['signal']}")
    else:
        log.info("\n✅ Aucun événement actif")

    return results


if __name__ == "__main__":
    run()
