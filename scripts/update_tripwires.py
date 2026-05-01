"""
update_tripwires.py — Mise à jour automatique des 20 événements Tripwire
Sources :
  - RSS      : 11 sources (Al Jazeera, Guardian, OilPrice, Hellenic Shipping, etc.)
  - yFinance : E08 (VLCC proxy) + E09 (Brent backwardation)

Environnement :
  CI=true (GitHub Actions) → RSS + yFinance complets
  Sinon (Streamlit Cloud)  → statuts conservés + yFinance seulement
"""

import os, json, time, logging, datetime
from typing import Optional
import requests
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

try:
    import feedparser
    FEEDPARSER_OK = True
except ImportError:
    FEEDPARSER_OK = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tripwires_update")

# ─── Chemins ──────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "data"))
AUTO_FILE   = os.path.join(DATA_DIR, "auto_scores.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Sources RSS ──────────────────────────────────────────────────────────────
RSS_FEEDS = [
    ("Al Jazeera",        "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Guardian World",    "https://www.theguardian.com/world/rss"),
    ("NYT World",         "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("OilPrice",          "https://oilprice.com/rss/main"),
    ("Hellenic Shipping", "https://www.hellenicshippingnews.com/feed/"),
    ("MarineLink",        "https://www.marinelink.com/rss/news"),
    ("Splash247",         "https://splash247.com/feed/"),
    ("Maritime Exec.",    "https://maritime-executive.com/rss/articles"),
    ("Middle East Eye",   "https://www.middleeasteye.net/rss"),
    ("Arab News",         "https://www.arabnews.com/rss.xml"),
    ("Energy Monitor",    "https://www.energymonitor.ai/feed/"),
]

RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OrmuzMonitor/1.0 +https://github.com)",
    "Accept":     "application/rss+xml, application/xml, text/xml, */*",
}
RSS_TIMEOUT  = 15
RSS_LOOKBACK = 24  # heures

# ─── Groupes d'événements avec mots-clés ─────────────────────────────────────
RSS_GROUPS = {
    "physical_strait": {
        "eids":       ["E01", "E02", "E03"],
        # Exige "hormuz" ou "strait of hormuz" — élimine les articles Iran généraux
        "must":       ["hormuz", "strait of hormuz", "persian gulf strait"],
        "boost":      ["tanker", "seized", "irgc", "mine", "vessel",
                       "detained", "boarded", "warning shot", "blocked", "ship"],
        "label":      "Physique — Détroit",
        "thresholds": (1, 3, 7),
    },
    "infra_military": {
        "eids":       ["E04", "E05", "E06"],
        # Exige les noms d'infrastructure précis — pas d'articles généraux Israel/Iran
        "must":       ["abqaiq", "ras tanura", "fujairah", "petroline",
                       "aramco", "adnoc", "kharg island", "bandar abbas"],
        "boost":      ["attack", "strike", "drone", "missile", "explosion",
                       "damaged", "fire", "sabotage", "hit"],
        "label":      "Infrastructure pétrolière",
        "thresholds": (1, 2, 5),
    },
    "military_escalation": {
        "eids":       ["E13", "E15"],
        # Israel + Iran + infrastructure militaire/nucléaire
        "must":       ["iran", "israel"],
        "boost":      ["nuclear", "strike", "attack", "missile", "military facility",
                       "irgc", "natanz", "isfahan", "ballistic", "air strike",
                       "military exercise", "hormuz"],
        "label":      "Escalade militaire Iran/Israël",
        "thresholds": (2, 6, 15),
    },
    "market_shipping": {
        "eids":       ["E07", "E10", "E11", "E14", "E18", "E19"],
        # Exige un mot shipping/tanker ET un mot d'action spécifique
        "must":       ["hormuz", "tanker", "vlcc", "houthi", "red sea shipping"],
        "boost":      ["reroute", "cancel", "lloyds", "war risk",
                       "cape of good hope", "detour", "freight rate",
                       "insurance", "diverted", "sinopec", "cnooc", "default"],
        "label":      "Marchés + Fret + AIS",
        "thresholds": (2, 5, 12),
    },
    "institutional": {
        "eids":       ["E12", "E16", "E17", "E20"],
        # Mots très spécifiques — élimine les faux positifs météo/général
        "must":       ["iea emergency", "strategic petroleum reserve",
                       "secondary sanctions iran", "ofac iran",
                       "scada attack", "cyberattack oil", "spr release"],
        "boost":      ["oil", "release", "emergency", "iran", "china",
                       "reserve", "sanctions", "cyber", "terminal"],
        "label":      "Institutionnel + Systémique",
        "thresholds": (1, 2, 4),
    },
}

EVENTS_META = {
    "E01": "Saisie tanker par IRGC",
    "E02": "Tir de sommation sur VLCC",
    "E03": "Mines détectées — chenaux navigation",
    "E04": "Frappe drone ADNOC / Fujairah",
    "E05": "Attaque pipeline Petroline",
    "E06": "Frappe Abqaiq / Ras Tanura",
    "E07": "Lloyd's suspend war-risk Golfe",
    "E08": "Squeeze VLCC",
    "E09": "Backwardation extreme Brent",
    "E10": "Armateur — reroutage Cap de BEH",
    "E11": "Acheteur chinois annule lifting",
    "E12": "Raffinerie asiatique active SPR",
    "E13": "Frappe israelienne Iran",
    "E14": "Houthis reprennent frappes Mer Rouge",
    "E15": "Iran exercices militaires non notifies",
    "E16": "Sanctions secondaires US Chine",
    "E17": "Activation SPR IEA Asie",
    "E18": "Chute trafic tanker AIS 72h",
    "E19": "Defaut negociant majeur",
    "E20": "Cyberattaque SCADA terminal export",
}

TANKER_TICKERS = ["FRO", "STNG", "DHT"]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_existing_status(eid):
    state_path = os.path.join(DATA_DIR, "event_states.json")
    if os.path.exists(state_path):
        try:
            with open(state_path) as f:
                return json.load(f).get(eid, {}).get("status", 0)
        except Exception:
            pass
    return 0


def score_article(title, summary, group):
    text = (title + " " + summary).lower()
    return (
        any(kw in text for kw in group["must"]) and
        any(kw in text for kw in group["boost"])
    )


def articles_to_status(n, thresholds):
    v, a, d = thresholds
    if n >= d:  return 3
    if n >= a:  return 2
    if n >= v:  return 1
    return 0


def fetch_all_rss():
    cutoff   = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=RSS_LOOKBACK)
    articles = []

    for source_name, feed_url in RSS_FEEDS:
        try:
            r = requests.get(feed_url, headers=RSS_HEADERS, timeout=RSS_TIMEOUT)
            if r.status_code != 200:
                log.warning(f"  RSS {source_name}: HTTP {r.status_code}")
                continue
            feed  = feedparser.parse(r.text)
            n_new = 0
            for entry in feed.entries:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub:
                    try:
                        dt = datetime.datetime(*pub[:6], tzinfo=datetime.timezone.utc)
                        if dt < cutoff:
                            continue
                    except Exception:
                        pass
                title   = entry.get("title",   "").strip()
                summary = entry.get("summary", "").strip()
                if title:
                    articles.append({
                        "title":   title,
                        "summary": summary[:300],
                        "source":  source_name,
                    })
                    n_new += 1
            log.info(f"  {source_name}: {n_new} articles")
        except Exception as e:
            log.warning(f"  {source_name}: {type(e).__name__}: {e}")
        time.sleep(1)

    log.info(f"  Total : {len(articles)} articles collectes")
    return articles


def score_market_events():
    results = {}

    # E08 : tankers
    try:
        records = []
        for ticker in TANKER_TICKERS:
            df = pd.DataFrame()
            for attempt in range(3):
                try:
                    df = yf.download(ticker, period="30d", interval="1d",
                                     progress=False, auto_adjust=True)
                    break
                except Exception:
                    time.sleep(5 * (attempt + 1))
            if df.empty or len(df) < 5:
                continue
            close   = df["Close"].dropna().squeeze()
            current = float(close.iloc[-1])
            ma20    = float(close.tail(20).mean())
            pct_dev = (current - ma20) / ma20 * 100
            records.append(pct_dev)
            log.info(f"  {ticker}: {current:.2f} vs MA20 {ma20:.2f} -> {pct_dev:+.1f}%")
            time.sleep(2)

        if records:
            avg = sum(records) / len(records)
            status = 3 if avg > 30 else 2 if avg > 15 else 1 if avg > 7 else 0
            results["E08"] = {
                "auto_status": status,
                "signal":      f"Tankers (FRO/STNG/DHT) moyenne vs MA20 : {avg:+.1f}%",
                "source":      "yFinance",
                "details":     {t: f"{v:+.1f}%" for t, v in zip(TANKER_TICKERS, records)},
                "updated_at":  datetime.datetime.now().isoformat(),
            }
    except Exception as e:
        log.warning(f"E08 error: {e}")

    # E09 : Brent
    try:
        df = yf.download("BZ=F", period="40d", interval="1d",
                         progress=False, auto_adjust=True)
        if not df.empty and len(df) >= 5:
            close   = df["Close"].dropna().squeeze()
            current = float(close.iloc[-1])
            ma30    = float(close.tail(30).mean())
            dev     = (current - ma30) / ma30 * 100
            log.info(f"  Brent: {current:.2f} vs MA30 {ma30:.2f} -> {dev:+.1f}%")
            status = 3 if dev > 25 else 2 if dev > 15 else 1 if dev > 8 else 0
            results["E09"] = {
                "auto_status": status,
                "signal":      f"Brent vs MA30 : {dev:+.1f}% (proxy backwardation)",
                "source":      "yFinance",
                "updated_at":  datetime.datetime.now().isoformat(),
            }
    except Exception as e:
        log.warning(f"E09 error: {e}")

    return results


# ─── Runner ───────────────────────────────────────────────────────────────────

def run():
    log.info("=" * 60)
    log.info(f"Demarrage update tripwires -- {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("=" * 60)

    auto_scores = {}
    run_rss     = os.environ.get("CI", "").lower() == "true"

    # ── 1. RSS (GitHub Actions uniquement) ────────────────────────────────────
    if not run_rss:
        log.info("\n[RSS] Non execute (Streamlit Cloud). Statuts conserves.")
        for eid in EVENTS_META:
            if eid in ("E08", "E09"):
                continue
            auto_scores[eid] = {
                "auto_status": load_existing_status(eid),
                "signal":      "RSS actif via GitHub Actions uniquement (toutes les heures)",
                "source":      "cache",
                "snippets":    [],
                "updated_at":  datetime.datetime.now().isoformat(),
            }
    else:
        if not FEEDPARSER_OK:
            log.error("[RSS] feedparser non installe -- pip install feedparser")
        else:
            log.info(f"\n[RSS] Actif -- {len(RSS_FEEDS)} sources, fenetres {RSS_LOOKBACK}h")
            articles = fetch_all_rss()

            log.info(f"\n[RSS] Scoring sur {len(articles)} articles...")
            group_counts   = {}
            group_snippets = {}

            for gid, grp in RSS_GROUPS.items():
                hits = [a for a in articles if score_article(a["title"], a["summary"], grp)]
                group_counts[gid]   = len(hits)
                group_snippets[gid] = [
                    f"{a['title'][:85]} ({a['source']})" for a in hits[:3]
                ]
                log.info(f"  {grp['label']}: {len(hits)} articles pertinents")
                for s in group_snippets[gid]:
                    log.info(f"    . {s[:80]}")

            for eid in EVENTS_META:
                if eid in ("E08", "E09"):
                    continue
                grp_id = next(
                    (gid for gid, grp in RSS_GROUPS.items() if eid in grp["eids"]),
                    None,
                )
                if grp_id:
                    n      = group_counts[grp_id]
                    thrs   = RSS_GROUPS[grp_id]["thresholds"]
                    status = articles_to_status(n, thrs)
                    snips  = group_snippets[grp_id]
                    signal = f"{n} articles pertinents/24h (seuils {thrs})"
                else:
                    n, status, snips = 0, 0, []
                    signal = "Groupe non defini"

                auto_scores[eid] = {
                    "auto_status": status,
                    "signal":      signal,
                    "source":      "RSS",
                    "snippets":    snips,
                    "updated_at":  datetime.datetime.now().isoformat(),
                }

    # ── 2. yFinance -- toujours actif ─────────────────────────────────────────
    log.info("\n[yFinance] E08 (VLCC proxy) + E09 (Brent backwardation proxy)")
    auto_scores.update(score_market_events())

    # ── 3. Sauvegarde ─────────────────────────────────────────────────────────
    with open(AUTO_FILE, "w") as f:
        json.dump(auto_scores, f, indent=2, ensure_ascii=False)
    log.info(f"\n[OK] auto_scores.json sauvegarde ({len(auto_scores)} evenements)")

    # ── 4. Resume ─────────────────────────────────────────────────────────────
    actifs = [(eid, v) for eid, v in auto_scores.items() if v.get("auto_status", 0) > 0]
    labels = {1: "Veille", 2: "Alerte", 3: "Declenche"}
    if actifs:
        log.info(f"\n[!] {len(actifs)} evenement(s) detecte(s) :")
        for eid, v in sorted(actifs, key=lambda x: -x[1]["auto_status"]):
            log.info(f"   {labels.get(v['auto_status'],'?')} {eid} -- {v['signal']}")
    else:
        log.info("\n[OK] Aucun evenement actif -- situation normale")

    return auto_scores


if __name__ == "__main__":
    run()
