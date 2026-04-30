# ═══════════════════════════════════════════════════════════════════════
# Ormuz Monitor — Suivi des 20 événements tripwires
# Indicateur de Risque Global + Décalage Physique / Marché
# ═══════════════════════════════════════════════════════════════════════

import os, json, warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import yfinance as yf

st.set_page_config(
    page_title="Tripwires — Ormuz Monitor",
    page_icon="⚠️",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────
# COULEURS & THÈME
# ─────────────────────────────────────────────────────────────────────────
DARK   = "#080d14"
CARD   = "#0f1923"
BORDER = "#1e2d3d"
DIM    = "#2a3d50"

# ─────────────────────────────────────────────────────────────────────────
# PERSISTANCE
# ─────────────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
STATE_FILE   = "data/event_states.json"
HISTORY_FILE = "data/event_history.json"

# ─────────────────────────────────────────────────────────────────────────
# DÉFINITION DES 20 ÉVÉNEMENTS
# src_type:
#   P = Physique direct (détroit, infra, AIS)
#   M = Marché / Finance (assurance, fret, prix)
#   I = Institutionnel (SPR, sanctions, décisions acheteurs)
#   N = News / Signal politique / Militaire
# ─────────────────────────────────────────────────────────────────────────
EVENTS = {
    "E01": {"label": "Saisie tanker par IRGC",                    "cat": "Physique — Détroit",        "src": "P", "w": 10},
    "E02": {"label": "Tir de sommation sur VLCC",                 "cat": "Physique — Détroit",        "src": "P", "w": 9},
    "E03": {"label": "Mines détectées — chenaux navigation",      "cat": "Physique — Détroit",        "src": "P", "w": 10},
    "E04": {"label": "Frappe drone ADNOC / Fujairah",             "cat": "Physique — Infrastructure", "src": "P", "w": 8},
    "E05": {"label": "Attaque pipeline Petroline (East-West)",    "cat": "Physique — Infrastructure", "src": "P", "w": 9},
    "E06": {"label": "Frappe Abqaiq / Ras Tanura",               "cat": "Physique — Infrastructure", "src": "P", "w": 10},
    "E07": {"label": "Lloyd's suspend war-risk Golfe",            "cat": "Finance — Assurance",       "src": "M", "w": 8},
    "E08": {"label": "Squeeze VLCC (taux > 150k$/j)",            "cat": "Finance — Fret",            "src": "M", "w": 7},
    "E09": {"label": "Backwardation extrême Brent",              "cat": "Finance — Prix",            "src": "M", "w": 7},
    "E10": {"label": "Armateur majeur — reroutage Cap de BEH",   "cat": "Décision — Armateur",      "src": "P", "w": 8},
    "E11": {"label": "Acheteur chinois annule lifting",           "cat": "Décision — Acheteur",      "src": "I", "w": 7},
    "E12": {"label": "Raffinerie asiatique active SPR national",  "cat": "Décision — Acheteur",      "src": "I", "w": 8},
    "E13": {"label": "Frappe israélienne installations Iran",     "cat": "Militaire — Escalade",     "src": "N", "w": 10},
    "E14": {"label": "Houthis reprennent frappes Mer Rouge",     "cat": "Militaire — Escalade",     "src": "P", "w": 7},
    "E15": {"label": "Iran — exercices militaires non notifiés", "cat": "Militaire — Signal",       "src": "N", "w": 6},
    "E16": {"label": "Sanctions secondaires US élargies (Chine)","cat": "Politique — Sanctions",    "src": "I", "w": 8},
    "E17": {"label": "Activation SPR officielle (IEA / Asie)",  "cat": "Institutionnel — SPR",     "src": "I", "w": 9},
    "E18": {"label": "Chute >40% trafic tanker AIS (72h)",      "cat": "AIS — Signal agrégé",      "src": "P", "w": 10},
    "E19": {"label": "Défaut négociant majeur (Vitol/Trafigura)","cat": "Systémique",               "src": "M", "w": 7},
    "E20": {"label": "Cyberattaque SCADA terminal export",       "cat": "Systémique",               "src": "N", "w": 9},
}

TRIPWIRES = {
    "E01": "AIS : perte de signal / déviation forcée d'un VLCC dans le détroit",
    "E02": "GDELT : cluster 'warning shot tanker Strait Hormuz'",
    "E03": "Communiqué NAVCENT/CMF + chute trafic AIS simultanée",
    "E04": "GDELT : 'attack Fujairah terminal' / 'ADNOC drone strike'",
    "E05": "GDELT : 'Petroline attack' / 'East West Pipeline Saudi'",
    "E06": "GDELT + spike Brent >10 % en moins d'1 heure",
    "E07": "Communiqué Lloyd's Market Association / JWC exclusion zone",
    "E08": "Baltic Exchange BDTI TD3C > 150 000 $/jour",
    "E09": "Spread Brent M1 − M3 > +5 $/bbl (backwardation profonde)",
    "E10": "AIS : VLCC grecs/norvégiens déviant vers le Cap de Bonne-Espérance",
    "E11": "Reuters/Platts : 'Sinopec / CNOOC cancel cargo' ou 'force majeure'",
    "E12": "Communiqué METI Japon / MOTIE Corée — libération réserves IEA",
    "E13": "GDELT : volume critique 'Israel strike Iran nuclear facilities'",
    "E14": "AIS : reroutage Bab-el-Mandeb + GDELT 'Houthi missile ship'",
    "E15": "AIS : navires IRIN en formation dans le chenal + communiqué IRNA",
    "E16": "Federal Register / OFAC : 'secondary sanctions Iran oil China'",
    "E17": "Communiqué IEA ou gouvernement national — activation SPR coordonnée",
    "E18": "Calcul interne : count(VLCC in strait 72h) / baseline_30d < 0.60",
    "E19": "Reuters/Bloomberg : 'default delivery forward' Vitol / Trafigura / Gunvor",
    "E20": "GDELT : 'cyberattack Ras Tanura' / 'Kharg Island SCADA disruption'",
}

STATUS_OPTS  = {0: "⚪ Inactif", 1: "🟡 Veille", 2: "🟠 Alerte", 3: "🔴 Déclenché"}
STATUS_SCORE = {0: 0.0, 1: 0.33, 2: 0.66, 3: 1.0}
SRC_FULL     = {"P": "Physique", "M": "Marché", "I": "Institutionnel", "N": "News/Militaire"}

# Couleurs de statut
S_COLOR = {0: "#1e2d3d", 1: "#92400e", 2: "#c2410c", 3: "#b91c1c"}
S_TEXT  = {0: "#64748b", 1: "#fbbf24", 2: "#fb923c", 3: "#f87171"}

# ─────────────────────────────────────────────────────────────────────────
# PERSISTANCE JSON
# ─────────────────────────────────────────────────────────────────────────
def load_state():
    base = {eid: {"status": 0, "notes": "", "updated_at": None} for eid in EVENTS}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            saved = json.load(f)
        base.update(saved)
        # S'assurer que tous les events existent
        for eid in EVENTS:
            if eid not in base:
                base[eid] = {"status": 0, "notes": "", "updated_at": None}
    return base

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def append_history(risk, psi, mri, decoupling):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {"ts": ts, "risk": risk, "psi": psi, "mri": mri, "decoupling": decoupling}
    if history and history[-1]["ts"][:10] == ts[:10]:
        history[-1] = entry          # Met à jour l'entrée du jour
    else:
        history.append(entry)
    history = history[-90:]          # 90 jours max
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

# ─────────────────────────────────────────────────────────────────────────
# DONNÉES MARCHÉS
# ─────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_brent():
    """Retourne (prix actuel, MA30, déviation relative) du Brent futures."""
    try:
        df = yf.download("BZ=F", period="40d", interval="1d",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 5:
            return None, None, 0.0
        close   = df["Close"].dropna().squeeze()
        current = float(close.iloc[-1])
        ma30    = float(close.tail(30).mean())
        dev     = (current - ma30) / ma30      # ex: +0.08 = 8 % au-dessus de la MA30
        return round(current, 2), round(ma30, 2), round(dev, 4)
    except Exception:
        return None, None, 0.0

# ─────────────────────────────────────────────────────────────────────────
# CALCUL DES INDICATEURS
# ─────────────────────────────────────────────────────────────────────────
def compute_indicators(state, brent_dev: float):
    """
    Retourne : risk_score, psi, mri, decoupling

    PSI (Physical Stress Index, 0-100)
        Moyenne pondérée des événements type P uniquement.
        Mesure la pression réelle sur le monde physique.

    MRI (Market Response Index, 0-100)
        70 % = événements type M (finance/fret/assurance)
        30 % = signal de déviation du Brent vs MA30
               (normalisé : 0 % écart → 0 ; ±20 % → 100 ; plafonné à 0 côté baissier)
        Mesure l'ampleur de la réponse des marchés.

    Décalage = PSI − MRI (plage −100 / +100)
        Positif  → physique sous tension, marché ne l'a pas pricé (risque de gap brutal)
        Négatif  → marché en avance sur le physique (excès de spéculation)
    """
    total_w = p_w = m_w = 0
    total_s = p_s = m_s = 0.0

    for eid, ev in EVENTS.items():
        status = state.get(eid, {}).get("status", 0)
        score  = STATUS_SCORE[status] * ev["w"]
        w      = ev["w"]
        total_w += w; total_s += score
        if ev["src"] == "P":
            p_w += w; p_s += score
        elif ev["src"] == "M":
            m_w += w; m_s += score

    risk_score = round(100 * total_s / total_w, 1) if total_w else 0.0
    psi        = round(100 * p_s / p_w, 1)         if p_w     else 0.0
    mri_events = round(100 * m_s / m_w, 1)         if m_w     else 0.0

    # Signal Brent : déviation ±20 % → [0, 100], côté baissier tronqué à 0
    brent_signal = max(0.0, min(100.0, (brent_dev / 0.20) * 100))
    mri          = round(0.70 * mri_events + 0.30 * brent_signal, 1)

    decoupling = round(max(-100.0, min(100.0, psi - mri)), 1)

    return risk_score, psi, mri, decoupling

# ─────────────────────────────────────────────────────────────────────────
# VISUALISATIONS
# ─────────────────────────────────────────────────────────────────────────
def _risk_color(v):
    if v < 20:  return "#22c55e", "#14532d"   # vert
    if v < 45:  return "#f59e0b", "#78350f"   # ambre
    if v < 70:  return "#f97316", "#7c2d12"   # orange
    return              "#ef4444", "#450a0a"   # rouge

def gauge_risk(value, title, subtitle=""):
    color, bg = _risk_color(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={
            "text": f"{title}<br><span style='font-size:10px;color:#64748b'>{subtitle}</span>",
            "font": {"size": 13, "color": "#cbd5e1"}
        },
        number={"font": {"size": 40, "color": color}, "suffix": " /100"},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 25, 50, 75, 100],
                "tickfont": {"color": "#475569", "size": 9},
                "tickcolor": "#1e2d3d"
            },
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": CARD,
            "bordercolor": BORDER,
            "steps": [
                {"range": [0, 25],   "color": "#14532d22"},
                {"range": [25, 50],  "color": "#78350f22"},
                {"range": [50, 75],  "color": "#7c2d1222"},
                {"range": [75, 100], "color": "#450a0a33"},
            ],
        }
    ))
    fig.update_layout(
        height=235, margin=dict(l=20, r=20, t=55, b=5),
        paper_bgcolor=DARK, font_color="#cbd5e1"
    )
    return fig

def gauge_decoupling(value):
    if   value < -30: color, lbl = "#38bdf8", "🔵 Surréaction marché"
    elif value <  15: color, lbl = "#34d399", "🟢 Équilibré"
    elif value <  45: color, lbl = "#fbbf24", "🟡 Marché en retard"
    else:             color, lbl = "#f87171", "🔴 Décalage critique"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={
            "text": f"Décalage Physique / Marché<br><span style='font-size:10px;color:#64748b'>{lbl}</span>",
            "font": {"size": 13, "color": "#cbd5e1"}
        },
        number={"font": {"size": 40, "color": color}, "suffix": " pts"},
        gauge={
            "axis": {
                "range": [-100, 100],
                "tickvals": [-100, -50, 0, 50, 100],
                "tickfont": {"color": "#475569", "size": 9},
                "tickcolor": "#1e2d3d"
            },
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": CARD,
            "bordercolor": BORDER,
            "steps": [
                {"range": [-100, -30], "color": "#0c4a6e22"},
                {"range": [-30, 15],   "color": "#14532d22"},
                {"range": [15, 45],    "color": "#78350f22"},
                {"range": [45, 100],   "color": "#450a0a33"},
            ],
        }
    ))
    fig.update_layout(
        height=235, margin=dict(l=20, r=20, t=65, b=5),
        paper_bgcolor=DARK, font_color="#cbd5e1"
    )
    return fig

def chart_history(history):
    df = pd.DataFrame(history)
    df["ts"] = pd.to_datetime(df["ts"])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.42, 0.58],
        vertical_spacing=0.08,
        subplot_titles=[
            "Score de Risque Global (/100)",
            "Stress Physique (PSI) vs Réponse Marché (MRI) — Décalage"
        ]
    )

    # ── Risque global
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["risk"], name="Risque Global",
        line=dict(color="#f87171", width=2.5),
        fill="tozeroy", fillcolor="rgba(248,113,113,0.10)", mode="lines"
    ), row=1, col=1)

    # ── PSI
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["psi"], name="Stress Physique (PSI)",
        line=dict(color="#fb923c", width=2.2), mode="lines"
    ), row=2, col=1)

    # ── MRI
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["mri"], name="Réponse Marché (MRI)",
        line=dict(color="#38bdf8", width=2, dash="dash"), mode="lines"
    ), row=2, col=1)

    # ── Décalage (aire remplie)
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["decoupling"], name="Décalage PSI − MRI",
        line=dict(color="#a78bfa", width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(167,139,250,0.06)", mode="lines"
    ), row=2, col=1)

    # Ligne zéro sur le panneau décalage
    fig.add_hline(y=0, line=dict(color="#334155", width=1, dash="dot"), row=2, col=1)

    fig.update_layout(
        height=430,
        paper_bgcolor=DARK, plot_bgcolor=DARK,
        font_color="#94a3b8",
        legend=dict(bgcolor=CARD, bordercolor=BORDER, font_size=11,
                    orientation="h", x=0, y=-0.07),
        margin=dict(l=10, r=10, t=40, b=40)
    )
    for ann in fig.layout.annotations:
        ann.font.color = "#94a3b8"
        ann.font.size  = 12

    fig.update_xaxes(gridcolor=BORDER, zeroline=False, showgrid=True)
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, showgrid=True)
    fig.update_yaxes(range=[0, 100],    row=1)
    fig.update_yaxes(range=[-100, 100], row=2)

    return fig

def chart_contributions(state):
    rows = []
    for eid, ev in EVENTS.items():
        st_val = state.get(eid, {}).get("status", 0)
        rows.append({
            "label":  f"{eid}  {ev['label'][:32]}{'…' if len(ev['label'])>32 else ''}",
            "score":  STATUS_SCORE[st_val] * ev["w"],
            "status": st_val,
        })
    df = pd.DataFrame(rows).sort_values("score", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["score"],
        y=df["label"],
        orientation="h",
        marker_color=[S_COLOR[s] for s in df["status"]],
        marker_line_color=BORDER,
        marker_line_width=0.5,
        text=[STATUS_OPTS[s][:2] for s in df["status"]],
        textfont=dict(size=12),
        textposition="outside",
    ))
    fig.update_layout(
        title=dict(text="Contribution au risque par événement",
                   font=dict(size=12, color="#94a3b8")),
        height=510,
        paper_bgcolor=DARK, plot_bgcolor=DARK,
        font_color="#94a3b8",
        xaxis=dict(title="Score pondéré", gridcolor=BORDER, range=[0, 11.5]),
        yaxis=dict(tickfont=dict(size=9.5)),
        margin=dict(l=10, r=55, t=35, b=10)
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────
def main():

    # ── CSS custom minimal
    st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        div[data-testid="stExpander"] { border: 1px solid #1e2d3d; border-radius: 6px; }
        .stAlert { border-radius: 6px; }
        div[data-testid="metric-container"] { background: #0f1923; border-radius: 6px; padding: 8px 12px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header
    col_t, col_r = st.columns([4, 1])
    with col_t:
        st.markdown("## ⚠️ Ormuz — Tripwires & Décalage Physique/Marché")
    with col_r:
        st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y  %H:%M')}")

    # ── Charger l'état
    if "event_state" not in st.session_state:
        st.session_state.event_state = load_state()
    state = st.session_state.event_state

    # ── Données marchés
    brent_price, brent_ma30, brent_dev = fetch_brent()

    # ── Calcul des indicateurs
    risk, psi, mri, decoupling = compute_indicators(state, brent_dev or 0.0)

    # ── Snapshot historique (1 par jour)
    append_history(risk, psi, mri, decoupling)

    # ═══════════════════════════════════════════════════════════════════
    # 1. INDICATEURS PRINCIPAUX
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📊 Indicateurs")
    g1, g2, g3 = st.columns(3)

    with g1:
        st.plotly_chart(
            gauge_risk(risk, "🛑 Risque Global", "Tous événements pondérés"),
            use_container_width=True, key="g_risk"
        )
    with g2:
        st.plotly_chart(
            gauge_risk(psi, "⚙️ Stress Physique", "PSI — événements type P"),
            use_container_width=True, key="g_psi"
        )
    with g3:
        st.plotly_chart(
            gauge_decoupling(decoupling),
            use_container_width=True, key="g_decoupling"
        )

    # ── Ligne Brent
    if brent_price:
        d_pct  = brent_dev * 100
        d_icon = "📈" if d_pct > 1 else ("📉" if d_pct < -1 else "➡️")
        st.info(
            f"**Brent Futures (BZ=F)** : **${brent_price:.2f} /bbl**"
            f"  ·  MA 30j : ${brent_ma30:.2f}"
            f"  ·  Écart MA : {d_icon} **{d_pct:+.1f} %**"
            f"  ·  MRI = **{mri:.0f}/100** _(70% événements marchés · 30% signal Brent)_"
        )
    else:
        st.warning("⚠️ Données Brent indisponibles — MRI calculé sur événements marchés uniquement")

    # ── Bannière événements actifs
    actifs = [(eid, ev) for eid, ev in EVENTS.items()
              if state.get(eid, {}).get("status", 0) > 0]
    if actifs:
        parts = " · ".join(
            f"{STATUS_OPTS[state[eid]['status']][:2]} **{ev['label']}**"
            for eid, ev in actifs
        )
        st.error(f"**{len(actifs)} événement(s) actif(s)** — {parts}")
    else:
        st.success("✅ Aucun événement actif — situation normale")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # 2. HISTORIQUE
    # ═══════════════════════════════════════════════════════════════════
    history = load_history()
    if len(history) >= 2:
        st.markdown("### 📈 Historique (90 jours max)")
        st.plotly_chart(chart_history(history), use_container_width=True)
        st.divider()

    # ═══════════════════════════════════════════════════════════════════
    # 3. TRACKER ÉVÉNEMENTS
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 🎯 Suivi des 20 événements tripwires")

    col_chart, col_form = st.columns([1, 1.35], gap="large")

    # ── Colonne gauche : graphe de contribution
    with col_chart:
        st.plotly_chart(chart_contributions(state), use_container_width=True)

        # Métriques rapides par type de source
        st.markdown("**Répartition par type de source**")
        m1, m2, m3, m4 = st.columns(4)
        for col, src, label in [
            (m1, "P", "🏭 Physique"),
            (m2, "M", "💹 Marché"),
            (m3, "I", "🏛 Institutionnel"),
            (m4, "N", "📰 News"),
        ]:
            triggered = sum(
                1 for eid, ev in EVENTS.items()
                if ev["src"] == src and state.get(eid, {}).get("status", 0) > 0
            )
            total = sum(1 for ev in EVENTS.values() if ev["src"] == src)
            col.metric(label, f"{triggered}/{total}")

    # ── Colonne droite : formulaire de mise à jour
    with col_form:
        st.markdown("**Mise à jour des statuts**")

        # Grouper par catégorie
        cats: dict[str, list[str]] = {}
        for eid, ev in EVENTS.items():
            cats.setdefault(ev["cat"], []).append(eid)

        for cat, eids in cats.items():
            with st.expander(f"📁 {cat}", expanded=False):
                for eid in eids:
                    ev         = EVENTS[eid]
                    cur_status = state.get(eid, {}).get("status", 0)
                    cur_notes  = state.get(eid, {}).get("notes", "")

                    st.markdown(
                        f"**{eid} — {ev['label']}**  "
                        f"<span style='color:#475569;font-size:12px'>poids ×{ev['w']} · {SRC_FULL[ev['src']]}</span>",
                        unsafe_allow_html=True
                    )
                    st.caption(f"🔍 {TRIPWIRES[eid]}")

                    st.select_slider(
                        label=f"statut_{eid}",
                        options=[0, 1, 2, 3],
                        value=cur_status,
                        format_func=lambda x: STATUS_OPTS[x],
                        key=f"slider_{eid}",
                        label_visibility="collapsed"
                    )
                    st.text_input(
                        label=f"notes_{eid}",
                        value=cur_notes,
                        placeholder="Source, lien, horodatage, commentaire…",
                        key=f"notes_{eid}",
                        label_visibility="collapsed"
                    )
                    st.markdown("---")

        # ── Bouton de sauvegarde
        st.markdown(" ")
        if st.button("💾  Sauvegarder tous les statuts", type="primary",
                     use_container_width=True):
            for eid in EVENTS:
                new_status = st.session_state.get(
                    f"slider_{eid}", state.get(eid, {}).get("status", 0))
                new_notes  = st.session_state.get(
                    f"notes_{eid}",  state.get(eid, {}).get("notes", ""))
                old_status = state.get(eid, {}).get("status", 0)
                state[eid] = {
                    "status":     new_status,
                    "notes":      new_notes,
                    "updated_at": datetime.now().isoformat()
                                  if new_status != old_status
                                  else state.get(eid, {}).get("updated_at"),
                }
            save_state(state)
            st.session_state.event_state = state
            st.success("✅ Statuts sauvegardés")
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════
    # 4. TABLEAU DE SYNTHÈSE
    # ═══════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("### 📋 Tableau de synthèse")

    rows = []
    for eid, ev in EVENTS.items():
        st_val  = state.get(eid, {}).get("status", 0)
        notes   = state.get(eid, {}).get("notes") or "—"
        updated = state.get(eid, {}).get("updated_at")
        rows.append({
            "ID":         eid,
            "Événement":  ev["label"],
            "Catégorie":  ev["cat"],
            "Source":     SRC_FULL[ev["src"]],
            "Poids":      ev["w"],
            "Statut":     STATUS_OPTS[st_val],
            "Score":      round(STATUS_SCORE[st_val] * ev["w"], 2),
            "Mis à jour": updated[:10] if updated else "—",
            "Notes":      notes,
        })

    df = pd.DataFrame(rows)

    def color_row(row):
        colors = {
            "⚪ Inactif":   f"color: #475569",
            "🟡 Veille":    f"color: #fbbf24",
            "🟠 Alerte":    f"color: #fb923c; font-weight:600",
            "🔴 Déclenché": f"color: #f87171; font-weight:700",
        }
        result  = [""] * len(row)
        idx_col = list(df.columns).index("Statut")
        result[idx_col] = colors.get(row["Statut"], "")
        idx_s   = list(df.columns).index("Score")
        result[idx_s] = "font-weight:600" if row["Score"] > 0 else "color: #334155"
        return result

    st.dataframe(
        df.style.apply(color_row, axis=1),
        use_container_width=True,
        hide_index=True
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exporter CSV",
        data=csv,
        file_name=f"ormuz_tripwires_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 5. MÉTHODOLOGIE
    # ═══════════════════════════════════════════════════════════════════
    with st.expander("ℹ️ Méthodologie des indicateurs"):
        st.markdown("""
**Score de Risque Global (0–100)**
Moyenne pondérée des 20 événements. Chaque statut est converti en score
(Inactif=0 · Veille=0.33 · Alerte=0.66 · Déclenché=1.0) multiplié par le poids de l'événement (6–10).

---

**PSI — Physical Stress Index (0–100)**
Même calcul, restreint aux événements de type **P** (physiques directs) :
E01, E02, E03, E04, E05, E06, E10, E14, E18.
Mesure le niveau de pression réelle sur les flux physiques d'hydrocarbures.

---

**MRI — Market Response Index (0–100)**
- 70 % = événements de type **M** (marchés) : E07 Lloyd's, E08 VLCC squeeze, E09 backwardation, E19 défaut négociant.
- 30 % = signal de déviation du Brent par rapport à sa MA 30 jours.
  *(+20 % au-dessus de la MA → signal 100 ; en dessous de la MA → signal 0)*

Mesure l'ampleur de la réaction déjà intégrée par les marchés financiers.

---

**Décalage Physique / Marché = PSI − MRI  (plage −100 / +100)**

| Zone | Interprétation |
|------|---------------|
| **> +45** 🔴 | Le monde physique est sous forte tension, les marchés n'ont pas bougé → risque de gap de prix brutal |
| **+15 à +45** 🟡 | Sous-réaction des marchés → signal d'alerte croissant |
| **−15 à +15** 🟢 | Équilibré — marchés et physique cohérents |
| **< −30** 🔵 | Les marchés ont surréagi par rapport aux fondamentaux → excès spéculatif |
        """)

if __name__ == "__main__":
    main()
