# ═══════════════════════════════════════════════════════════════════════
# update_tripwires.py — Mise à jour automatique des 20 événements Tripwire
# Sources : GDELT API 2.0 (actualité) + yFinance (marchés)
#
# Usage :
#   python scripts/update_tripwires.py          ← standalone (cron / manuel)
#   import update_tripwires; update_tripwires.run()  ← depuis Streamlit
# ═══════════════════════════════════════════════════════════════════════

import os, json, time, logging
from datetime import datetime
from typing import Optional

import requests
import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tripwires_update")

# ─────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────
DATA_DIR  = "data"
AUTO_FILE = os.path.join(DATA_DIR, "auto_scores.json")
os.makedirs(DATA_DIR, exist_ok=True)

GDELT_URL     = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TIMESPAN = "24H"          # fenêtre d'analyse
GDELT_MAX      = 25             # articles max retournés (= plafond de comptage)
GDELT_PAUSE    = 1.5            # secondes entre requêtes (respect rate-limit)

# Tanker stocks comme proxies du fret VLCC
TANKER_TICKERS = ["FRO", "STNG", "DHT"]

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION GDELT PAR ÉVÉNEMENT
# thresholds = (n_veille, n_alerte, n_declenche) en nombre d'articles / 24h
# Un score 0 = Inactif  1 = Veille  2 = Alerte  3 = Déclenché
# ─────────────────────────────────────────────────────────────────────────
GDELT_EVENTS = {

    # ── Physique — Détroit ───────────────────────────────────────────────
    "E01": {
        "label": "Saisie tanker par IRGC",
        "query": "IRGC tanker seized OR Iran seized tanker OR Iran detained tanker ship",
        "thresholds": (1, 4, 10),
    },
    "E02": {
        "label": "Tir de sommation sur VLCC",
        "query": "warning shot tanker Strait Hormuz OR Iran warning VLCC",
        "thresholds": (1, 3, 7),
    },
    "E03": {
        "label": "Mines détectées — chenaux navigation",
        "query": "sea mines Strait Hormuz OR mines Persian Gulf shipping",
        "thresholds": (1, 3, 7),
    },

    # ── Physique — Infrastructure ────────────────────────────────────────
    "E04": {
        "label": "Frappe drone ADNOC / Fujairah",
        "query": "ADNOC attack drone OR Fujairah oil attack OR UAE oil infrastructure attack",
        "thresholds": (1, 3, 8),
    },
    "E05": {
        "label": "Attaque pipeline Petroline",
        "query": "Petroline pipeline attack OR East West Pipeline Saudi attack",
        "thresholds": (1, 3, 7),
    },
    "E06": {
        "label": "Frappe Abqaiq / Ras Tanura",
        "query": "Abqaiq attack OR Ras Tanura attack OR Saudi oil facility strike",
        "thresholds": (1, 4, 10),
    },

    # ── Finance — Assurance ───────────────────────────────────────────────
    "E07": {
        "label": "Lloyd's suspend war-risk Golfe",
        "query": "war risk insurance Gulf suspended OR Lloyd's Hormuz exclusion OR JWC Persian Gulf",
        "thresholds": (1, 2, 5),
    },

    # E08 et E09 sont calculés via yFinance (voir MARKET_EVENTS)

    # ── Décision — Armateur / Acheteur ───────────────────────────────────
    "E10": {
        "label": "Armateur majeur — reroutage Cap de BEH",
        "query": "tanker reroute Cape Good Hope Hormuz OR VLCC avoid Strait Hormuz",
        "thresholds": (2, 5, 12),
    },
    "E11": {
        "label": "Acheteur chinois annule lifting",
        "query": "China cancel oil cargo OR Sinopec cancel OR CNOOC force majeure cargo",
        "thresholds": (1, 3, 8),
    },
    "E12": {
        "label": "Raffinerie asiatique active SPR national",
        "query": "Japan strategic oil reserve OR Korea SPR release IEA emergency stocks",
        "thresholds": (1, 3, 7),
    },

    # ── Militaire ────────────────────────────────────────────────────────
    "E13": {
        "label": "Frappe israélienne installations Iran",
        "query": "Israel strike Iran nuclear OR Israel attack Iran military",
        "thresholds": (5, 15, 35),   # seuils plus hauts : bruit de fond élevé
    },
    "E14": {
        "label": "Houthis reprennent frappes Mer Rouge",
        "query": "Houthi attack ship Red Sea OR Houthi missile vessel OR Houthi strike tanker",
        "thresholds": (3, 8, 20),
    },
    "E15": {
        "label": "Iran — exercices militaires non notifiés",
        "query": "Iran military exercise Strait Hormuz OR IRGC naval exercise unannounced",
        "thresholds": (2, 5, 12),
    },

    # ── Politique / Institutionnel ────────────────────────────────────────
    "E16": {
        "label": "Sanctions secondaires US élargies (Chine)",
        "query": "secondary sanctions Iran oil China OFAC OR US Iran oil sanctions China buyers",
        "thresholds": (3, 8, 20),
    },
    "E17": {
        "label": "Activation SPR officielle (IEA / Asie)",
        "query": "IEA emergency oil release OR strategic petroleum reserve release coordination",
        "thresholds": (1, 3, 8),
    },

    # ── AIS proxy ─────────────────────────────────────────────────────────
    "E18": {
        "label": "Chute >40% trafic tanker AIS (72h) — proxy GDELT",
        "query": "tanker traffic Hormuz decline OR shipping disruption Strait Hormuz OR vessels avoid Hormuz",
        "thresholds": (2, 5, 12),
        "_note": "Proxy GDELT — idéalement remplacer par données AIS directes",
    },

    # ── Systémique ────────────────────────────────────────────────────────
    "E19": {
        "label": "Défaut négociant majeur",
        "query": "oil trader default delivery OR Vitol Trafigura Gunvor default cargo",
        "thresholds": (1, 2, 5),
    },
    "E20": {
        "label": "Cyberattaque SCADA terminal export",
        "query": "cyberattack oil terminal OR Ras Tanura hack OR SCADA attack refinery Gulf",
        "thresholds": (1, 2, 5),
    },
}

# ─────────────────────────────────────────────────────────────────────────
# ÉVÉNEMENTS CALCULÉS VIA YFINANCE (marchés)
# ─────────────────────────────────────────────────────────────────────────
def score_market_events() -> dict:
    """
    E08 : Squeeze VLCC  → composite des tanker stocks (FRO/STNG/DHT)
           Si moyenne % vs MA20 > +15 % → Alerte, > +30 % → Déclenché

    E09 : Backwardation Brent → proxy Brent 1j vs MA30
           Backwardation réelle nécessiterait 2 contrats futures;
           ici on utilise la déviation Brent vs MA30 comme signal de tension.
           > +8 % → Veille, > +15 % → Alerte, > +25 % → Déclenché
    """
    results = {}

    # ── E08 : Tanker stocks proxy ────────────────────────────────────────
    try:
        records = []
        for ticker in TANKER_TICKERS:
            df = yf.download(ticker, period="30d", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < 5:
                continue
            close   = df["Close"].dropna().squeeze()
            current = float(close.iloc[-1])
            ma20    = float(close.tail(20).mean())
            pct_dev = (current - ma20) / ma20 * 100
            records.append(pct_dev)
            log.info(f"  {ticker}: {current:.2f} vs MA20 {ma20:.2f} → {pct_dev:+.1f}%")

        if records:
            avg_dev = sum(records) / len(records)
            if   avg_dev > 30: status = 3
            elif avg_dev > 15: status = 2
            elif avg_dev > 7:  status = 1
            else:              status = 0
            results["E08"] = {
                "auto_status": status,
                "signal":      f"Tankers (FRO/STNG/DHT) moyenne vs MA20 : {avg_dev:+.1f}%",
                "source":      "yFinance",
                "details":     {t: f"{v:+.1f}%" for t, v in zip(TANKER_TICKERS, records)},
                "updated_at":  datetime.now().isoformat(),
            }
    except Exception as e:
        log.warning(f"E08 yFinance error: {e}")
        results["E08"] = _error_entry("E08", str(e))

    # ── E09 : Brent deviation proxy ──────────────────────────────────────
    try:
        df = yf.download("BZ=F", period="40d", interval="1d",
                         progress=False, auto_adjust=True)
        if not df.empty and len(df) >= 5:
            close   = df["Close"].dropna().squeeze()
            current = float(close.iloc[-1])
            ma30    = float(close.tail(30).mean())
            dev_pct = (current - ma30) / ma30 * 100
            log.info(f"  Brent: {current:.2f} vs MA30 {ma30:.2f} → {dev_pct:+.1f}%")
            if   dev_pct > 25: status = 3
            elif dev_pct > 15: status = 2
            elif dev_pct > 8:  status = 1
            else:              status = 0
            results["E09"] = {
                "auto_status": status,
                "signal":      f"Brent vs MA30 : {dev_pct:+.1f}% (proxy backwardation)",
                "source":      "yFinance",
                "updated_at":  datetime.now().isoformat(),
            }
    except Exception as e:
        log.warning(f"E09 yFinance error: {e}")
        results["E09"] = _error_entry("E09", str(e))

    return results

# ─────────────────────────────────────────────────────────────────────────
# GDELT
# ─────────────────────────────────────────────────────────────────────────
def query_gdelt(query: str) -> tuple[int, list[str]]:
    """
    Interroge GDELT 2.0 API.
    Retourne (nombre d'articles, liste de snippets/titres).
    """
    params = {
        "query":      query,
        "mode":       "ArtList",
        "maxrecords": GDELT_MAX,
        "timespan":   GDELT_TIMESPAN,
        "format":     "JSON",
        "sourcelang": "english",
    }
    try:
        r = requests.get(GDELT_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", []) or []
        n = len(articles)
        snippets = [
            f"{a.get('title', '')[:90]} ({a.get('domain', '')})"
            for a in articles[:3]
        ]
        return n, snippets
    except Exception as e:
        log.warning(f"  GDELT error pour '{query[:50]}': {e}")
        return -1, []

def articles_to_status(n: int, thresholds: tuple) -> int:
    """Convertit un nombre d'articles en statut 0-3."""
    if n < 0:      return 0   # erreur → inactif par défaut
    v, a, d = thresholds
    if n >= d:     return 3   # Déclenché
    elif n >= a:   return 2   # Alerte
    elif n >= v:   return 1   # Veille
    return 0                  # Inactif

def _error_entry(eid: str, msg: str) -> dict:
    return {
        "auto_status": 0,
        "signal":      f"Erreur : {msg}",
        "source":      "erreur",
        "updated_at":  datetime.now().isoformat(),
    }

# ─────────────────────────────────────────────────────────────────────────
# RUNNER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────
def run() -> dict:
    """
    Lance la mise à jour complète.
    Retourne le dict des auto_scores (aussi sauvegardé dans data/auto_scores.json).
    """
    log.info("═" * 60)
    log.info(f"Démarrage update tripwires — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log.info("═" * 60)

    auto_scores = {}

    # ── 1. Événements GDELT ──────────────────────────────────────────────
    log.info(f"\n[GDELT] {len(GDELT_EVENTS)} événements à analyser — fenêtre {GDELT_TIMESPAN}")
    for eid, cfg in GDELT_EVENTS.items():
        log.info(f"  → {eid} : {cfg['label']}")
        n_articles, snippets = query_gdelt(cfg["query"])

        if n_articles >= 0:
            status = articles_to_status(n_articles, cfg["thresholds"])
            log.info(f"     {n_articles} articles → statut {status}")
        else:
            status = 0
            log.warning(f"     Erreur API — statut maintenu à 0")

        auto_scores[eid] = {
            "auto_status": status,
            "signal":      f"{n_articles} articles/24h (seuils {cfg['thresholds']})",
            "source":      "GDELT",
            "snippets":    snippets,
            "updated_at":  datetime.now().isoformat(),
        }
        time.sleep(GDELT_PAUSE)   # respect rate-limit

    # ── 2. Événements marchés (yFinance) ─────────────────────────────────
    log.info("\n[yFinance] Calcul E08 (VLCC proxy) + E09 (Brent backwardation proxy)")
    market = score_market_events()
    auto_scores.update(market)

    # ── 3. Sauvegarde ────────────────────────────────────────────────────
    with open(AUTO_FILE, "w") as f:
        json.dump(auto_scores, f, indent=2, ensure_ascii=False)
    log.info(f"\n✅ auto_scores.json sauvegardé ({len(auto_scores)} événements)")

    # ── 4. Résumé ────────────────────────────────────────────────────────
    actifs = [(eid, v) for eid, v in auto_scores.items() if v.get("auto_status", 0) > 0]
    if actifs:
        log.info(f"\n⚠️  {len(actifs)} événement(s) détecté(s) :")
        for eid, v in sorted(actifs, key=lambda x: -x[1]["auto_status"]):
            labels = {1:"🟡 Veille", 2:"🟠 Alerte", 3:"🔴 Déclenché"}
            log.info(f"   {labels[v['auto_status']]} {eid} — {v['signal']}")
    else:
        log.info("\n✅ Aucun événement détecté — situation normale")

    return auto_scores


# ─────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE CLI
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run()
