"""
HORMUZ WATCH — Module 3 : Suivi Économique
Proxy indicators pour suivre l'impact de la fermeture du détroit d'Ormuz.
Streamlit Cloud deployment · Data: Yahoo Finance (yfinance)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HORMUZ WATCH — Suivi Économique",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────────────────────
CLOSURE_DATE = date(2026, 2, 28)
TODAY        = date.today()
DAYS_CLOSED  = (TODAY - CLOSURE_DATE).days

# Baselines au 27 fév. 2026 (sources : EIA, IEA, CNBC, Statista)
INSTRUMENTS = {
    "🛢️ Énergie": [
        dict(label="Brent Crude",          ticker="BZ=F",    unit="$/bbl",   bl=73.5,   thr=30,  note="Pic observé : 126 $/bbl (8 mars 2026)"),
        dict(label="WTI Crude",            ticker="CL=F",    unit="$/bbl",   bl=70.5,   thr=30,  note="Référence USA"),
        dict(label="Gaz naturel US",       ticker="NG=F",    unit="$/MMBtu", bl=3.5,    thr=50,  note="Proxy Henry Hub — TTF Europe non dispo gratuitement"),
        dict(label="Gazoline RBOB",        ticker="RB=F",    unit="$/gal",   bl=2.20,   thr=30,  note="+30% observé (>4 $/gal mars 2026)"),
        dict(label="Heating oil / diesel", ticker="HO=F",    unit="$/gal",   bl=2.45,   thr=30,  note="Diesel & kérosène très liés aux flux Gulf"),
    ],
    "🌱 Engrais & Chimie": [
        dict(label="CF Industries (urée)", ticker="CF",      unit="USD",     bl=84.0,   thr=30,  note="1er prod. azote USA — proxy urée. CEO : 'full out for the year'"),
        dict(label="Mosaic (phosphate)",   ticker="MOS",     unit="USD",     bl=28.5,   thr=25,  note="Proxy DAP/MAP. Cascade : soufre→acide sulfurique→phosphate"),
        dict(label="Nutrien",              ticker="NTR",     unit="USD",     bl=63.0,   thr=25,  note="Plus grand prod. engrais mondial (potasse + azote)"),
        dict(label="ICL Group",            ticker="ICL",     unit="USD",     bl=5.2,    thr=25,  note="Potasse + phosphates. Sensible au soufre Gulf"),
    ],
    "🌾 Alimentation": [
        dict(label="Maïs CBOT",            ticker="ZC=F",    unit="c/bu",    bl=455.0,  thr=20,  note="Corn Belt à 75% engrais normaux mi-mars. Feed bovins + éthanol"),
        dict(label="Blé CBOT",             ticker="ZW=F",    unit="c/bu",    bl=540.0,  thr=20,  note="Sécurité alimentaire mondiale (Égypte, Pakistan, Sahel exposés)"),
        dict(label="Soja CBOT",            ticker="ZS=F",    unit="c/bu",    bl=1010.0, thr=15,  note="Substitution maïs→soja documentée (moins d'engrais requis)"),
        dict(label="Riz CBOT",             ticker="ZR=F",    unit="$/cwt",   bl=17.5,   thr=15,  note="Bangladesh (Boro), Sri Lanka, Inde Kharif : saisons critiques"),
    ],
    "🚢 Fret & Industrie": [
        dict(label="DHT Holdings (VLCC)",  ticker="DHT",     unit="USD",     bl=10.2,   thr=40,  note="Tankers VLCC. Taux journaliers ×3-5 après fermeture"),
        dict(label="Frontline (tankers)",  ticker="FRO",     unit="USD",     bl=19.5,   thr=40,  note="Flotte détournée Cap Bonne-Espérance (+7-10j, +20-30% coût)"),
        dict(label="Aluminium (ALI=F)",    ticker="ALI=F",   unit="$/t",     bl=2460.0, thr=15,  note="Énergie-intensif. Surcharges industrie UE/UK +30%"),
        dict(label="Dow Chemical",         ticker="DOW",     unit="USD",     bl=34.5,   thr=20,  note="Chimie USA — bénéficiaire indirect (production full out)"),
    ],
    "📊 Macro & Finance": [
        dict(label="EUR/USD",              ticker="EURUSD=X",unit="",        bl=1.047,  thr=5,   note="Choc énergétique → pression euro. BCE a bloqué baisses taux"),
        dict(label="USD/JPY",              ticker="JPY=X",   unit="",        bl=152.0,  thr=5,   note="Japon quasi-100% dépendant Gulf (pétrole + GNL)"),
        dict(label="VIX",                  ticker="^VIX",    unit="pts",     bl=18.0,   thr=50,  note="Fear index. Monte quand l'incertitude géopolitique augmente"),
        dict(label="S&P 500",              ticker="^GSPC",   unit="pts",     bl=5900.0, thr=10,  note="Impact macro agrégé USA"),
    ],
}

SCENARIOS = {
    5: dict(
        color="#22c55e",
        label="Réouverture J+5",
        text="Réouverture rapide depuis aujourd'hui. Marchés absorbent le choc. "
             "IEA (400 Mbbl) active. Refill gaz estival Europe encore faisable.",
        cascade=dict(
            Énergie=   "Brent redescend vers 90-100 $/bbl. TTF commence correction.",
            Engrais=   "Urée +50% déjà intégré — décisions semis 2026 quasi irréversibles.",
            Alim=      "Maïs reste sous tension (engrais insuffisants). Blé se détend légèrement.",
            Macro=     "VIX retombe. BCE peut reprendre baisse de taux.",
        ),
    ),
    20: dict(
        color="#f59e0b",
        label="Réouverture J+20",
        text="Fermeture totale ~80 jours. Stockage gaz Europe critique pour hiver 2026-27. "
             "Saison Kharif Inde/Bangladesh décidée sous contrainte d'engrais.",
        cascade=dict(
            Énergie=   "Refill gaz Europe <40%. Hiver à risque même après réouverture.",
            Engrais=   "Cascade soufre→phosphate irréversible. Rendements 2026 réduits.",
            Alim=      "FAO confirme réduction planting. Prix +10-20% à 6 mois.",
            Macro=     "Récession technique All./Italie. BCE bloquée. UK inflation >5%.",
        ),
    ),
    50: dict(
        color="#ef4444",
        label="Réouverture J+50",
        text="Fermeture totale ~110 jours. Crise alimentaire mondiale 2027 confirmée. "
             "Récessions industrielles. Commerce mondial −2 pts. Risques souverains émergents.",
        cascade=dict(
            Énergie=   "Réserves épuisées. Délestages industriels hiver Europe.",
            Engrais=   "Récoltes 2026 −10 à −25%. Prix urée +70%. Crise phosphate structurelle.",
            Alim=      "FAO : crise 2027. Bangladesh/Pakistan/Égypte en rouge.",
            Macro=     "Stagflation mondiale. PIB −1%. 3,4 Mds pers. à risque souverain.",
        ),
    ),
}

# ── Helpers ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=900)
def fetch(ticker: str, start: str, end: str) -> pd.Series:
    """Retourne une pd.Series de clôtures, ou une Series vide en cas d'erreur."""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return pd.Series(dtype=float, name=ticker)
        s = df["Close"].squeeze()
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s.dropna().rename(ticker)
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def safe_last(s: pd.Series):
    """Retourne le dernier float d'une Series, ou None si vide."""
    if s is None or s.empty:
        return None
    try:
        return float(s.iloc[-1])
    except (TypeError, ValueError):
        return None


def delta_pct(current, baseline: float) -> float:
    """% de variation vs baseline. Retourne 0.0 si données absentes."""
    if current is None or baseline == 0:
        return 0.0
    return (current - baseline) / baseline * 100.0


def signal(dp: float, thr: float) -> tuple:
    """(icône, couleur hex) selon sévérité."""
    a, t = abs(dp), abs(thr)
    if a >= t:          return "🔴", "#ef4444"
    if a >= t * 0.60:   return "🟠", "#f97316"
    if a >= t * 0.30:   return "🟡", "#eab308"
    return "🟢", "#22c55e"


def fmt_val(v, unit: str) -> str:
    """Formate une valeur numérique pour affichage."""
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"{v:,.0f} {unit}".strip()
    if abs(v) >= 100:
        return f"{v:.1f} {unit}".strip()
    return f"{v:.2f} {unit}".strip()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")

    scen_days = st.radio(
        "Scénario de réouverture *(depuis aujourd'hui)*",
        options=[5, 20, 50],
        format_func=lambda x: f"J+{x}  →  {(TODAY + timedelta(days=x)).strftime('%d %b %Y')}",
    )
    scen = SCENARIOS[scen_days]
    reopen_date = TODAY + timedelta(days=scen_days)

    st.markdown(
        f'<div style="background:{scen["color"]}22;border-left:3px solid {scen["color"]};'
        f'padding:8px 10px;border-radius:4px;font-size:12px;line-height:1.5;margin:4px 0">'
        f'{scen["text"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    lookback = st.slider("Historique affiché (jours)", 30, 180, 60, step=10)
    START = (TODAY - timedelta(days=lookback)).strftime("%Y-%m-%d")
    END   = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    st.markdown("---")
    st.error(
        f"🚫 **Détroit fermé**  \n"
        f"Depuis le 28 fév. 2026  \n"
        f"**J+{DAYS_CLOSED}** jours"
    )

    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Cache 15 min · {datetime.now().strftime('%d/%m %H:%M')}")


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🛢️ HORMUZ WATCH — Module 3")
st.caption(
    f"Proxy indicators · Fermeture depuis J+{DAYS_CLOSED} jours · "
    f"Scénario actif : **{scen['label']}** → réouverture estimée **{reopen_date.strftime('%d %b %Y')}**"
)


# ── KPI Row ───────────────────────────────────────────────────────────────────
st.subheader("Indicateurs clés")
KPI = [
    dict(label="Brent Crude",          ticker="BZ=F",    unit="$/bbl", bl=73.5,  thr=30, inv=False),
    dict(label="CF Industries (urée)", ticker="CF",      unit="USD",   bl=84.0,  thr=30, inv=False),
    dict(label="Maïs CBOT",            ticker="ZC=F",    unit="c/bu",  bl=455.0, thr=20, inv=False),
    dict(label="VIX",                  ticker="^VIX",    unit="pts",   bl=18.0,  thr=50, inv=True),
]
for col, k in zip(st.columns(4), KPI):
    s   = fetch(k["ticker"], START, END)
    cur = safe_last(s)
    dp  = delta_pct(cur, k["bl"])
    ico, _ = signal(dp, k["thr"])
    with col:
        if cur is not None:
            st.metric(
                label=f"{ico} {k['label']}",
                value=fmt_val(cur, k["unit"]),
                delta=f"{dp:+.1f}% vs J0",
                delta_color="off" if k["inv"] else "normal",
            )
        else:
            st.metric(label=k["label"], value="—", delta="données indisponibles")


# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown("---")
tabs = st.tabs(list(INSTRUMENTS.keys()))

for tab_ui, (cat_name, instruments) in zip(tabs, INSTRUMENTS.items()):
    with tab_ui:

        # ── Collecte ────────────────────────────────────────────────────────
        rows       = []
        series_map = {}

        for inst in instruments:
            s   = fetch(inst["ticker"], START, END)
            cur = safe_last(s)
            dp  = delta_pct(cur, inst["bl"])
            ico, _ = signal(dp, inst["thr"])

            rows.append({
                "":             ico,
                "Indicateur":   inst["label"],
                "Valeur":       fmt_val(cur, inst["unit"]),
                "J0 (27/02)":   fmt_val(inst["bl"], inst["unit"]),
                "Δ J0":         f"{dp:+.1f}%" if cur is not None else "—",
                "Seuil alerte": f"±{inst['thr']}%",
                "Note":         inst["note"],
            })

            if not s.empty:
                series_map[inst["label"]] = s

        # ── Layout ──────────────────────────────────────────────────────────
        left, right = st.columns([1.1, 1.9])

        with left:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                height=230,
                column_config={
                    "":             st.column_config.TextColumn("", width=28),
                    "Indicateur":   st.column_config.TextColumn("Indicateur", width=175),
                    "Δ J0":         st.column_config.TextColumn("Δ J0", width=70),
                    "Seuil alerte": st.column_config.TextColumn("Seuil", width=70),
                },
            )
            # Alertes locales
            for inst in instruments:
                s   = fetch(inst["ticker"], START, END)
                cur = safe_last(s)
                dp  = delta_pct(cur, inst["bl"])
                ico, col_hex = signal(dp, inst["thr"])
                if ico in ("🔴", "🟠"):
                    st.markdown(
                        f'<div style="background:{col_hex}22;border-left:3px solid {col_hex};'
                        f'border-radius:4px;padding:5px 9px;font-size:11px;margin:3px 0">'
                        f'{ico} <b>{inst["label"]}</b> : {dp:+.1f}% · {inst["note"]}</div>',
                        unsafe_allow_html=True,
                    )

        with right:
            if series_map:
                palette = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
                fig = go.Figure()

                for i, (lbl, s) in enumerate(series_map.items()):
                    # Normalise base 100 à la date de fermeture
                    pos = s.index.searchsorted(pd.Timestamp(CLOSURE_DATE))
                    pos = min(pos, len(s) - 1)
                    ref = float(s.iloc[max(0, pos - 1)]) if pos > 0 else float(s.iloc[0])
                    if ref == 0:
                        continue
                    norm = s / ref * 100.0
                    fig.add_trace(go.Scatter(
                        x=norm.index, y=norm.values.tolist(),
                        name=lbl, mode="lines",
                        line=dict(width=1.8, color=palette[i % len(palette)])
                    ))

                fig.add_hline(y=100, line=dict(dash="dot", color="#9ca3af", width=0.8),
                              annotation_text="J0", annotation_font_size=9,
                              annotation_position="bottom right")
                fig.add_vline(x=pd.Timestamp(CLOSURE_DATE),
                              line=dict(dash="dash", color="#ef4444", width=1.1),
                              annotation_text="Fermeture", annotation_font_size=9,
                              annotation_position="top right")
                fig.add_vline(x=pd.Timestamp(reopen_date),
                              line=dict(dash="dash", color=scen["color"], width=1.1),
                              annotation_text=scen["label"], annotation_font_size=9,
                              annotation_position="top left")

                fig.update_layout(
                    title=dict(text="Évolution indexée — base 100 au 28 fév. 2026", font_size=11),
                    height=300,
                    margin=dict(t=36, b=70, l=36, r=12),
                    plot_bgcolor="white", paper_bgcolor="white",
                    xaxis=dict(showgrid=True, gridcolor="#f3f4f6", tickformat="%d %b"),
                    yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Index"),
                    legend=dict(orientation="h", y=-0.35, font_size=10),
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Données non disponibles — vérifiez la connexion Yahoo Finance.")


# ── Alertes globales ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🚨 Alertes actives")

alert_rows = []
for cat_name, instruments in INSTRUMENTS.items():
    for inst in instruments:
        s   = fetch(inst["ticker"], START, END)
        cur = safe_last(s)
        dp  = delta_pct(cur, inst["bl"])
        ico, _ = signal(dp, inst["thr"])
        if ico in ("🔴", "🟠") and cur is not None:
            alert_rows.append({
                "Signal":      ico,
                "Catégorie":   cat_name.split()[-1],
                "Indicateur":  inst["label"],
                "Valeur act.": fmt_val(cur, inst["unit"]),
                "Δ J0":        f"{dp:+.1f}%",
                "Seuil":       f"±{inst['thr']}%",
                "Note":        inst["note"],
            })

if alert_rows:
    st.dataframe(
        pd.DataFrame(alert_rows).sort_values("Signal"),
        use_container_width=True, hide_index=True,
        column_config={"Signal": st.column_config.TextColumn("", width=28)},
    )
else:
    st.success("Aucune alerte active au-dessus des seuils.")


# ── Cascade Module 2 ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander(f"📋 Effets en cascade — {scen['label']} (lien Module 2)"):
    casc = scen["cascade"]
    for col_ui, (k, v) in zip(st.columns(len(casc)), casc.items()):
        col_ui.markdown(f"**{k}**")
        col_ui.caption(v)


# ── Export CSV ────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📥 Export CSV des séries complètes"):
    export_rows = []
    for cat_name, instruments in INSTRUMENTS.items():
        for inst in instruments:
            s = fetch(inst["ticker"], START, END)
            if s.empty:
                continue
            for ts, val in s.items():
                v = None
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    pass
                if v is not None:
                    export_rows.append({
                        "date":        ts.strftime("%Y-%m-%d"),
                        "categorie":   cat_name,
                        "indicateur":  inst["label"],
                        "ticker":      inst["ticker"],
                        "valeur":      round(v, 4),
                        "unite":       inst["unit"],
                        "baseline_j0": inst["bl"],
                        "delta_pct":   round(delta_pct(v, inst["bl"]), 2),
                    })

    if export_rows:
        csv = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV",
            data=csv,
            file_name=f"hormuz_watch_{TODAY.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Aucune donnée à exporter pour la période sélectionnée.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.caption(
    "Sources : Yahoo Finance · Baselines J0 estimées au 27 fév. 2026 (EIA, IEA, CNBC, Statista) · "
    "Cache 15 min · NG=F = Henry Hub US (proxy TTF Europe, pas de TTF direct gratuit)"
)
