"""
02_Tripwires.py
===============
Page Streamlit : affichage des 20 événements tripwires.
Données : data/auto_scores.json (mis à jour par GitHub Actions toutes les heures)
Mode : lecture seule — pas de saisie manuelle.
"""

import os, json, sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import yfinance as yf

# ── Chemin vers la racine du repo ─────────────────────────────────────────────
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="Tripwires — Ormuz Monitor",
    page_icon="⚠️",
    layout="wide",
)

# ── Constantes ────────────────────────────────────────────────────────────────
DATA_FILE    = os.path.join(ROOT, "data", "auto_scores.json")
STATUS_LABEL = {0: "⚪ Inactif", 1: "🟡 Veille", 2: "🟠 Alerte", 3: "🔴 Déclenché"}
STATUS_COLOR = {0: "#1e2d3d",   1: "#92400e",  2: "#c2410c",  3: "#991b1b"}
STATUS_TEXT  = {0: "#64748b",   1: "#fbbf24",  2: "#fb923c",  3: "#f87171"}
STATUS_SCORE = {0: 0.0,         1: 0.33,       2: 0.66,       3: 1.0}

DARK  = "#080d14"
CARD  = "#0f1923"
BORD  = "#1e2d3d"

EVENTS = {
    "E01": {"label": "Saisie tanker par IRGC",                    "cat": "Physique — Détroit",        "src": "P", "w": 10},
    "E02": {"label": "Tir de sommation sur VLCC",                 "cat": "Physique — Détroit",        "src": "P", "w": 9},
    "E03": {"label": "Mines détectées — chenaux navigation",      "cat": "Physique — Détroit",        "src": "P", "w": 10},
    "E04": {"label": "Frappe drone ADNOC / Fujairah",             "cat": "Physique — Infrastructure", "src": "P", "w": 8},
    "E05": {"label": "Attaque pipeline Petroline",                "cat": "Physique — Infrastructure", "src": "P", "w": 9},
    "E06": {"label": "Frappe Abqaiq / Ras Tanura",               "cat": "Physique — Infrastructure", "src": "P", "w": 10},
    "E07": {"label": "Lloyd's suspend war-risk Golfe",            "cat": "Finance — Assurance",       "src": "M", "w": 8},
    "E08": {"label": "Squeeze VLCC (taux > 150k$/j)",            "cat": "Finance — Fret",            "src": "M", "w": 7},
    "E09": {"label": "Backwardation extrême Brent",              "cat": "Finance — Prix",            "src": "M", "w": 7},
    "E10": {"label": "Armateur majeur — reroutage Cap BEH",      "cat": "Décision — Armateur",      "src": "P", "w": 8},
    "E11": {"label": "Acheteur chinois annule lifting",           "cat": "Décision — Acheteur",      "src": "I", "w": 7},
    "E12": {"label": "Raffinerie asiatique active SPR national",  "cat": "Décision — Acheteur",      "src": "I", "w": 8},
    "E13": {"label": "Frappe israélienne installations Iran",     "cat": "Militaire — Escalade",     "src": "N", "w": 10},
    "E14": {"label": "Houthis reprennent frappes Mer Rouge",     "cat": "Militaire — Escalade",     "src": "P", "w": 7},
    "E15": {"label": "Iran — exercices militaires non notifiés", "cat": "Militaire — Signal",       "src": "N", "w": 6},
    "E16": {"label": "Sanctions secondaires US élargies Chine",  "cat": "Politique — Sanctions",    "src": "I", "w": 8},
    "E17": {"label": "Activation SPR officielle IEA / Asie",    "cat": "Institutionnel — SPR",     "src": "I", "w": 9},
    "E18": {"label": "Chute >40% trafic tanker AIS (72h)",      "cat": "AIS — Signal agrégé",      "src": "P", "w": 10},
    "E19": {"label": "Défaut négociant majeur",                  "cat": "Systémique",               "src": "M", "w": 7},
    "E20": {"label": "Cyberattaque SCADA terminal export",       "cat": "Systémique",               "src": "N", "w": 9},
}


# ── Chargement des données ────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_scores() -> dict:
    """Charge auto_scores.json. Retourne un dict vide si absent."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_brent():
    try:
        df = yf.download("BZ=F", period="40d", interval="1d",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 5:
            return None, None, 0.0
        c   = df["Close"].dropna().squeeze()
        cur = float(c.iloc[-1])
        ma  = float(c.tail(30).mean())
        return round(cur, 2), round(ma, 2), round((cur - ma) / ma, 4)
    except Exception:
        return None, None, 0.0


# ── Calcul des indicateurs ────────────────────────────────────────────────────

def compute(scores: dict, brent_dev: float) -> dict:
    """Calcule Risk, PSI, MRI, Décalage."""
    tw, ts, pw, ps, mw, ms = 0, 0.0, 0, 0.0, 0, 0.0

    for eid, ev in EVENTS.items():
        st_val = scores.get(eid, {}).get("status", 0)
        sc     = STATUS_SCORE[st_val] * ev["w"]
        tw += ev["w"]; ts += sc
        if ev["src"] == "P": pw += ev["w"]; ps += sc
        if ev["src"] == "M": mw += ev["w"]; ms += sc

    risk = round(100 * ts / tw, 1) if tw else 0.0
    psi  = round(100 * ps / pw, 1) if pw else 0.0
    mri_evt = round(100 * ms / mw, 1) if mw else 0.0
    brent_sig = max(0.0, min(100.0, (brent_dev / 0.20) * 100))
    mri  = round(0.70 * mri_evt + 0.30 * brent_sig, 1)
    dec  = round(max(-100.0, min(100.0, psi - mri)), 1)

    return {"risk": risk, "psi": psi, "mri": mri, "decoupling": dec}


# ── Visualisations ────────────────────────────────────────────────────────────

def gauge(value, title, suffix=" /100", rng=(0, 100)):
    color = (
        "#22c55e" if value < 20 else
        "#f59e0b" if value < 45 else
        "#f97316" if value < 70 else "#ef4444"
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 12, "color": "#cbd5e1"}},
        number={"font": {"size": 36, "color": color}, "suffix": suffix},
        gauge={
            "axis": {"range": list(rng), "tickfont": {"color": "#475569", "size": 9}},
            "bar":  {"color": color, "thickness": 0.28},
            "bgcolor": CARD, "bordercolor": BORD,
            "steps": [
                {"range": [rng[0], rng[0] + (rng[1]-rng[0])*0.25], "color": "rgba(20,83,45,0.12)"},
                {"range": [rng[0] + (rng[1]-rng[0])*0.25, rng[0] + (rng[1]-rng[0])*0.5],  "color": "rgba(120,53,15,0.12)"},
                {"range": [rng[0] + (rng[1]-rng[0])*0.5,  rng[0] + (rng[1]-rng[0])*0.75], "color": "rgba(124,45,18,0.12)"},
                {"range": [rng[0] + (rng[1]-rng[0])*0.75, rng[1]], "color": "rgba(69,10,10,0.18)"},
            ],
        }
    ))
    fig.update_layout(
        height=220, margin=dict(l=20, r=20, t=50, b=5),
        paper_bgcolor=DARK, font_color="#cbd5e1",
    )
    return fig


def bar_contributions(scores: dict) -> go.Figure:
    rows = sorted([
        {
            "label": f"{eid}  {ev['label'][:30]}",
            "score": STATUS_SCORE.get(scores.get(eid, {}).get("status", 0), 0) * ev["w"],
            "st":    scores.get(eid, {}).get("status", 0),
        }
        for eid, ev in EVENTS.items()
    ], key=lambda x: x["score"])

    fig = go.Figure(go.Bar(
        x=[r["score"] for r in rows],
        y=[r["label"] for r in rows],
        orientation="h",
        marker_color=[STATUS_COLOR[r["st"]] for r in rows],
        marker_line_width=0,
    ))
    fig.update_layout(
        height=480, margin=dict(l=10, r=30, t=24, b=10),
        paper_bgcolor=DARK, plot_bgcolor=DARK, font_color="#94a3b8",
        xaxis=dict(range=[0, 11], gridcolor=BORD, title="Score pondéré"),
        yaxis=dict(tickfont=dict(size=9)),
        title=dict(text="Contribution au risque", font=dict(size=11, color="#94a3b8")),
    )
    return fig


# ── Page principale ───────────────────────────────────────────────────────────

def main():
    st.markdown("""
    <style>
        .block-container { padding-top: 1.2rem; }
        div[data-testid="stExpander"] { border: 1px solid #1e2d3d; border-radius:6px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header
    col_t, col_r = st.columns([5, 1])
    col_t.markdown("## ⚠️ Ormuz — Tripwires & Indicateurs de risque")
    col_r.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # ── Chargement
    scores = load_scores()
    brent_price, brent_ma30, brent_dev = fetch_brent()
    ind    = compute(scores, brent_dev or 0.0)

    # ── Source info
    if scores:
        ts_vals = [v.get("updated_at","") for v in scores.values() if v.get("updated_at")]
        ts_last = max(ts_vals)[:16].replace("T"," ") if ts_vals else "—"
        n_actifs = sum(1 for v in scores.values() if v.get("status",0) > 0)
        st.caption(f"📡 Dernière analyse IA : **{ts_last}** · **{n_actifs}** événement(s) actif(s)")
    else:
        st.warning("⚠️ Données non disponibles — lancez le workflow GitHub Actions pour initialiser.")

    st.divider()

    # ── Jauges
    st.markdown("### 📊 Indicateurs")
    g1, g2, g3, g4 = st.columns(4)
    with g1: st.plotly_chart(gauge(ind["risk"],      "🛑 Risque Global"),      key="g1")
    with g2: st.plotly_chart(gauge(ind["psi"],       "⚙️ Stress Physique"),    key="g2")
    with g3: st.plotly_chart(gauge(ind["mri"],       "💹 Réponse Marchés"),    key="g3")
    with g4:
        dec = ind["decoupling"]
        dec_color = "#38bdf8" if dec<-30 else "#34d399" if dec<15 else "#fbbf24" if dec<45 else "#f87171"
        dec_label = "🔵 Surréaction" if dec<-30 else "🟢 Équilibré" if dec<15 else "🟡 Retard marché" if dec<45 else "🔴 Décalage critique"
        fig_dec = go.Figure(go.Indicator(
            mode="gauge+number",
            value=dec,
            title={"text": f"Décalage P/M<br><span style='font-size:10px'>{dec_label}</span>",
                   "font": {"size": 12, "color": "#cbd5e1"}},
            number={"font": {"size": 36, "color": dec_color}, "suffix": " pts"},
            gauge={
                "axis": {"range": [-100, 100], "tickfont": {"color": "#475569", "size": 9}},
                "bar":  {"color": dec_color, "thickness": 0.28},
                "bgcolor": CARD, "bordercolor": BORD,
                "steps": [
                    {"range": [-100, -30], "color": "rgba(12,74,110,0.12)"},
                    {"range": [-30,  15],  "color": "rgba(20,83,45,0.12)"},
                    {"range": [15,   45],  "color": "rgba(120,53,15,0.12)"},
                    {"range": [45,  100],  "color": "rgba(69,10,10,0.18)"},
                ],
            }
        ))
        fig_dec.update_layout(height=220, margin=dict(l=20,r=20,t=50,b=5),
                              paper_bgcolor=DARK, font_color="#cbd5e1")
        st.plotly_chart(fig_dec, key="g4")

    # ── Brent info
    if brent_price:
        icon = "📈" if brent_dev > 0.01 else "📉" if brent_dev < -0.01 else "➡️"
        st.info(
            f"**Brent BZ=F** : **${brent_price:.2f}/bbl** · MA30 : ${brent_ma30:.2f} · "
            f"Écart : {icon} **{brent_dev*100:+.1f}%** · MRI = **{ind['mri']:.0f}/100**"
        )

    # ── Bannière événements actifs
    actifs = [(eid, ev) for eid, ev in EVENTS.items() if scores.get(eid, {}).get("status", 0) > 0]
    if actifs:
        st.error(f"**{len(actifs)} événement(s) actif(s)** — " +
                 " · ".join(f"{STATUS_LABEL[scores[eid]['status']][:2]} {ev['label']}"
                            for eid, ev in actifs))
    else:
        st.success("✅ Aucun événement actif")

    st.divider()

    # ── Synthèse IA : articles détectés
    articles_actifs = [
        (eid, v) for eid, v in scores.items()
        if v.get("status", 0) > 0 and (v.get("articles") or v.get("reasoning"))
    ]
    if articles_actifs:
        st.markdown("### 🤖 Synthèse IA — Signaux actifs")
        for eid, v in sorted(articles_actifs, key=lambda x: -x[1].get("status", 0)):
            st_val2 = v.get("status", 0)
            col     = STATUS_COLOR.get(st_val2, "#334155")
            lbl     = STATUS_LABEL.get(st_val2, "")
            ev_l = EVENTS.get(eid, {}).get("label", eid)
            ts   = v.get("updated_at", "")[:16].replace("T", " ")

            st_expander = st_val2 >= 2  # auto-ouvert si Alerte ou Déclenché

            with st.expander(
                f"{lbl}  **{eid} — {ev_l}**",
                expanded=st_expander,
            ):
                # Signal + reasoning
                if v.get("signal"):
                    st.markdown(
                        f'<div style="background:{col}22;border-left:3px solid {col};'
                        f'padding:7px 10px;border-radius:4px;font-size:13px;margin-bottom:8px">'
                        f'<b>Signal</b> : {v["signal"]}</div>',
                        unsafe_allow_html=True,
                    )
                if v.get("reasoning"):
                    st.markdown(
                        f'<div style="font-size:12px;color:#94a3b8;padding:4px 0">'
                        f'💬 {v["reasoning"]}</div>',
                        unsafe_allow_html=True,
                    )
                # Articles sources
                arts = v.get("articles", [])
                if arts:
                    st.markdown("**Sources :**")
                    for a in arts:
                        st.markdown(
                            f'<div style="font-size:12px;padding:3px 0;color:#cbd5e1">'
                            f'📄 {a}</div>',
                            unsafe_allow_html=True,
                        )
                st.caption(f"Source : {v.get('source','?')} · {ts}")

        st.divider()

    # ── Tableau complet des 20 événements
    st.markdown("### 🎯 Tableau des 20 événements")

    col_left, col_right = st.columns([1, 1.4])

    with col_left:
        st.plotly_chart(bar_contributions(scores))

    with col_right:
        rows = []
        for eid, ev in EVENTS.items():
            sc = scores.get(eid, {})
            st_val = sc.get("status", 0)
            rows.append({
                "ID":       eid,
                "Événement": ev["label"],
                "Catégorie": ev["cat"],
                "Poids":    ev["w"],
                "Statut":   STATUS_LABEL[st_val],
                "Score":    round(STATUS_SCORE[st_val] * ev["w"], 2),
                "Signal IA": sc.get("signal", "—")[:60],
            })
        df = pd.DataFrame(rows)

        def color_row(row):
            colors = {
                "⚪ Inactif":   "color:#475569",
                "🟡 Veille":    "color:#fbbf24",
                "🟠 Alerte":    "color:#fb923c;font-weight:600",
                "🔴 Déclenché": "color:#f87171;font-weight:700",
            }
            res              = [""] * len(row)
            res[df.columns.get_loc("Statut")] = colors.get(row["Statut"], "")
            res[df.columns.get_loc("Score")]  = "font-weight:600" if row["Score"] > 0 else "color:#334155"
            return res

        st.dataframe(df.style.apply(color_row, axis=1),
                     use_container_width=True, hide_index=True, height=520)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV", csv,
                           f"tripwires_{datetime.now().strftime('%Y%m%d')}.csv",
                           "text/csv")

    # ── Méthodologie
    st.divider()
    with st.expander("ℹ️ Méthodologie"):
        st.markdown("""
**Mise à jour** : GitHub Actions toutes les heures — collecte RSS (11 sources, 24h) + analyse Claude AI.

**Score de Risque Global** : moyenne pondérée des 20 événements (poids 6-10).
Statuts : Inactif=0 · Veille=0.33 · Alerte=0.66 · Déclenché=1.0

**PSI** (Physical Stress Index) : événements physiques (P) uniquement.

**MRI** (Market Response Index) : 70% événements marché (M) + 30% signal Brent vs MA30.

**Décalage P/M** = PSI − MRI :
>+45 🔴 Physique sous tension non pricé · +15→+45 🟡 Retard marché ·
-15→+15 🟢 Équilibré · <-30 🔵 Surréaction marché

**E08** (Squeeze VLCC) et **E09** (Backwardation Brent) sont calculés directement via yFinance.
Les 18 autres événements sont évalués par Claude AI sur la base des articles RSS des 24 dernières heures.
        """)


if __name__ == "__main__":
    main()

