"""
Hormuz Watch — Module 3 : Suivi Économique
Scénarios J+5 / J+20 / J+50 à partir d'aujourd'hui
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hormuz Watch – Suivi Économique",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CRISIS_START   = datetime(2026, 2, 28)
TODAY          = datetime.now()
CRISIS_DAY     = (TODAY - CRISIS_START).days

# Valeurs pré-crise (référence 27 fév. 2026)
BASELINE = {
    "brent":      82.0,   # $/bbl
    "wti":        78.0,   # $/bbl
    "ng_us":       2.8,   # $/MMBtu  Henry Hub
    "ttf":        32.0,   # €/MWh   (saisie manuelle)
    "jkm":        13.5,   # $/MMBtu (saisie manuelle)
    "urea":      475.0,   # $/t     (saisie manuelle)
    "dap":       550.0,   # $/t     (saisie manuelle)
    "ammonia":   380.0,   # $/t     (saisie manuelle)
    "corn":      420.0,   # ¢/bu
    "wheat":     580.0,   # ¢/bu
    "soy":      1020.0,   # ¢/bu
    "ships":     138.0,   # navires/jour Hormuz
    "war_risk":    0.125, # %/transit
    "vlcc":       35.0,   # k$/jour (baseline normal)
}

# Seuils alerte / critique
THRESHOLDS = {
    "brent":    (90,  110),
    "wti":      (85,  105),
    "ng_us":    (4.0,  6.5),
    "ttf":      (50,   65),
    "corn":     (500, 650),
    "wheat":    (680, 850),
    "urea":     (550, 700),
    "ships":    (30,   10),   # inversé : < = mauvais
    "war_risk": (0.3, 0.5),
}

SCENARIO_LABELS = {5: "Mai 03", 20: "Mai 18", 50: "Juin 17"}

# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch(ticker: str, period: str = "6mo") -> pd.DataFrame | None:
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return None
        # Aplatir MultiIndex si besoin
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

def last_close(df: pd.DataFrame | None) -> float | None:
    if df is None or df.empty:
        return None
    return float(df["Close"].iloc[-1])

def pct_change(val: float, baseline: float) -> float:
    return (val / baseline - 1) * 100

def status(val: float, key: str, inversed: bool = False) -> str:
    if key not in THRESHOLDS:
        return ""
    warn, crit = THRESHOLDS[key]
    if inversed:
        if val <= crit: return "🔴"
        if val <= warn: return "🟡"
        return "🟢"
    else:
        if val >= crit: return "🔴"
        if val >= warn: return "🟡"
        return "🟢"

def make_chart(
    df: pd.DataFrame | None,
    label: str,
    color: str = "#E8593C",
    warn_level: float | None = None,
    crit_level: float | None = None,
    unit: str = "",
) -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"].squeeze(),
            mode="lines",
            name=label,
            line=dict(color=color, width=2),
            hovertemplate=f"%{{x|%d %b %Y}}<br>{label}: %{{y:.2f}}{unit}<extra></extra>",
        ))
        # Marker crise
        fig.add_vline(
            x=CRISIS_START.timestamp() * 1000,
            line_dash="dash", line_color="rgba(150,150,150,0.6)",
            annotation_text="Fermeture détroit",
            annotation_font_size=10,
            annotation_position="top left",
        )
        if warn_level:
            fig.add_hline(y=warn_level, line_dash="dot",
                         line_color="orange", line_width=1,
                         annotation_text="⚠️ Alerte",
                         annotation_font_size=10, annotation_position="right")
        if crit_level:
            fig.add_hline(y=crit_level, line_dash="dot",
                         line_color="red", line_width=1,
                         annotation_text="🔴 Critique",
                         annotation_font_size=10, annotation_position="right")

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=80, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=11),
        xaxis=dict(
            gridcolor="rgba(128,128,128,0.12)",
            showline=False, zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(128,128,128,0.12)",
            showline=False, zeroline=False,
        ),
    )
    return fig

def kpi_card(col, label: str, value: str, delta: str, is_bad: bool = True):
    dc = "inverse" if is_bad else "normal"
    col.metric(label, value, delta, delta_color=dc)

def score_panel(scores: dict) -> str:
    """Génère un résumé textuel de l'état des indicateurs."""
    reds  = [k for k, v in scores.items() if v == "🔴"]
    warns = [k for k, v in scores.items() if v == "🟡"]
    if len(reds) >= 4:
        return "🔴 **Situation critique** : la majorité des indicateurs dépassent les seuils critiques."
    if len(reds) >= 2:
        return "🟠 **Situation dégradée** : plusieurs indicateurs en zone critique."
    if len(warns) >= 3:
        return "🟡 **Tension élevée** : indicateurs en zone d'alerte."
    return "🟢 **Situation surveillée** : indicateurs hors seuils critiques."

# ─────────────────────────────────────────────────────────────────────
# DONNÉES LIVE (chargement silencieux)
# ─────────────────────────────────────────────────────────────────────
with st.spinner("Chargement des données de marché…"):
    df_brent  = fetch("BZ=F")
    df_wti    = fetch("CL=F")
    df_ng     = fetch("NG=F")
    df_corn   = fetch("ZC=F")
    df_wheat  = fetch("ZW=F")
    df_soy    = fetch("ZS=F")
    df_eurusd = fetch("EURUSD=X")
    df_gold   = fetch("GC=F")
    df_dxy    = fetch("DX-Y.NYB")
    df_fro    = fetch("FRO")
    df_stng   = fetch("STNG")
    df_dht    = fetch("DHT")

p_brent = last_close(df_brent)
p_wti   = last_close(df_wti)
p_ng    = last_close(df_ng)
p_corn  = last_close(df_corn)
p_wheat = last_close(df_wheat)
p_soy   = last_close(df_soy)

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR — saisie manuelle données non-API
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✏️ Données manuelles")
    st.caption("Indicateurs sans API gratuite — à mettre à jour depuis les sources ci-dessous")

    st.markdown("**Énergie**")
    m_ttf      = st.number_input("TTF Gaz EU (€/MWh)",   value=62.0, step=0.5,
                                  help="Source : ICE / Trading Economics")
    m_jkm      = st.number_input("JKM LNG Asie ($/MMBtu)", value=18.0, step=0.5,
                                  help="Source : S&P Global Platts")

    st.markdown("**Engrais**")
    m_urea     = st.number_input("Urée Tampa ($/t)",      value=680,  step=5)
    m_dap      = st.number_input("DAP ($/t)",             value=625,  step=5)
    m_ammonia  = st.number_input("Ammoniac ($/t)",        value=490,  step=5)

    st.markdown("**Fret & Trafic**")
    m_ships    = st.number_input("Navires/jour Hormuz",   value=7,    step=1,
                                  help="Source : IMF PortWatch / HormuzTracker")
    m_war_risk = st.number_input("War risk (%/transit)",  value=0.35, step=0.05)
    m_vlcc     = st.number_input("VLCC day rate ($k/j)",  value=95,   step=5)
    m_bdti     = st.number_input("BDTI (Baltic Tanker)",  value=1380, step=10,
                                  help="Source : Baltic Exchange")

    st.divider()
    st.markdown("**Sources de référence**")
    st.markdown("""
- [IMF PortWatch](https://portwatch.imf.org)
- [HormuzTracker](https://hormuztracker.com)
- [ICE TTF](https://www.theice.com/products/27996665)
- [Green Markets Urée](https://www.greenmarkets.com)
- [Baltic Exchange](https://www.balticexchange.com)
- [Trading Economics](https://tradingeconomics.com/commodities)
""")

# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"## 🛢️ Hormuz Watch &nbsp;·&nbsp; Module 3 — Suivi Économique"
)
st.caption(
    f"Crise active depuis le **28 fév. 2026** &nbsp;·&nbsp; "
    f"Aujourd'hui : **{TODAY.strftime('%d %b %Y')}** (J+{CRISIS_DAY}) &nbsp;·&nbsp; "
    f"Données marchés : différé 15–20 min &nbsp;·&nbsp; "
    f"Actualisation auto toutes les 30 min"
)

# Score global
scores_live = {}
if p_brent:   scores_live["Brent"] = status(p_brent, "brent")
scores_live["TTF"]  = status(m_ttf,      "ttf")
scores_live["Urée"] = status(m_urea,     "urea")
scores_live["Navires"] = status(m_ships, "ships", inversed=True)
scores_live["War risk"] = status(m_war_risk, "war_risk")
if p_corn:    scores_live["Maïs"] = status(p_corn / 100, "corn")

st.info(score_panel(scores_live))

# ─── Barre de KPIs rapides ───────────────────────────────────────────
k = st.columns(6)
if p_brent:
    kpi_card(k[0], f"🛢️ Brent {status(p_brent,'brent')}",
             f"${p_brent:.1f}", f"{pct_change(p_brent, BASELINE['brent']):+.1f}% vs fév.")
else:
    k[0].metric("🛢️ Brent", "N/A", "Données indispo.")

kpi_card(k[1], f"⚡ TTF EU {status(m_ttf,'ttf')}",
         f"{m_ttf:.1f} €/MWh", f"{pct_change(m_ttf, BASELINE['ttf']):+.1f}%")

kpi_card(k[2], f"🌾 Urée {status(m_urea,'urea')}",
         f"${m_urea}/t", f"{pct_change(m_urea, BASELINE['urea']):+.1f}%")

kpi_card(k[3], f"🚢 Navires/j {status(m_ships,'ships',inversed=True)}",
         f"{m_ships}/j", f"Baseline : 138/j")

kpi_card(k[4], f"⚠️ War risk",
         f"{m_war_risk:.2f}%", f"Baseline : 0.125%")

if p_corn:
    kpi_card(k[5], f"🌽 Maïs {status(p_corn/100,'corn')}",
             f"{p_corn:.0f}¢/bu", f"{pct_change(p_corn, BASELINE['corn']):+.1f}%")
else:
    k[5].metric("🌽 Maïs", "N/A", "Données indispo.")

st.divider()

# ─────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────
tab_e, tab_f, tab_m, tab_s, tab_sc = st.tabs([
    "🛢️ Énergie",
    "🌾 Engrais & Alimentation",
    "🚢 Fret & Trafic",
    "📈 Macro & Devises",
    "🎯 Scénarios",
])

# ════════════════════════════════════════════════════════════════════
# TAB ÉNERGIE
# ════════════════════════════════════════════════════════════════════
with tab_e:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Brent Crude ($/bbl)**")
        st.caption("Référence mondiale. Seuil alerte 90 $ · critique 110 $")
        st.plotly_chart(make_chart(df_brent, "Brent", "#E8593C", 90, 110, " $"), use_container_width=True)

        st.markdown("**WTI Crude ($/bbl)**")
        st.caption("Référence US — proxy fret pétrolier américain")
        st.plotly_chart(make_chart(df_wti, "WTI", "#C04828", 85, 105, " $"), use_container_width=True)

    with c2:
        st.markdown("**Gaz nat. Henry Hub ($/MMBtu)** — proxy US")
        st.caption("⚠️ Pour le TTF européen (indicateur clé), utiliser la saisie manuelle ←")
        st.plotly_chart(make_chart(df_ng, "Gaz US", "#3B8BD4", 4.0, 6.5, " $"), use_container_width=True)

        # TTF + JKM résumé manuel
        st.markdown("**TTF EU & JKM Asie** *(saisie manuelle)*")
        tm1, tm2 = st.columns(2)
        with tm1:
            st.metric(
                f"TTF EU {status(m_ttf,'ttf')}",
                f"{m_ttf:.1f} €/MWh",
                f"{pct_change(m_ttf, BASELINE['ttf']):+.1f}% vs pré-crise",
                delta_color="inverse",
            )
            pct_ttf = pct_change(m_ttf, BASELINE['ttf'])
            interp = "Stockage hiver 2026-27 compromis" if pct_ttf > 80 else "Forte tension sur marché gaz EU"
            st.caption(f"📌 {interp}")
        with tm2:
            st.metric(
                f"JKM Asie {status(m_jkm,'ttf')}",
                f"{m_jkm:.1f} $/MMBtu",
                f"{pct_change(m_jkm, BASELINE['jkm']):+.1f}% vs pré-crise",
                delta_color="inverse",
            )
            st.caption("📌 Pression sur Bangladesh, Pakistan, Corée du Sud")

        st.markdown("")
        with st.expander("🔗 Sources TTF & JKM", expanded=False):
            st.markdown("""
| Source | Lien |
|---|---|
| ICE TTF Futures | [theice.com](https://www.theice.com/products/27996665) |
| Trading Economics TTF | [tradingeconomics.com](https://tradingeconomics.com/commodity/eu-natural-gas) |
| S&P Global JKM | [spglobal.com](https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/lng) |
| IEA Gas Market | [iea.org](https://www.iea.org/topics/the-middle-east-and-global-energy-markets) |
""")

# ════════════════════════════════════════════════════════════════════
# TAB ENGRAIS & ALIMENTATION
# ════════════════════════════════════════════════════════════════════
with tab_f:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Maïs CBOT (¢/bu)**")
        st.caption("Indicateur alimentation rang 2 · urée → rendements → prix maïs (lag 6–9 mois)")
        st.plotly_chart(make_chart(df_corn, "Maïs", "#639922", 500, 650, " ¢"), use_container_width=True)

        st.markdown("**Blé CBOT (¢/bu)**")
        st.caption("Sensible à l'urée + importations (Égypte, Asie). Lag ~3–6 mois")
        st.plotly_chart(make_chart(df_wheat, "Blé", "#BA7517", 680, 850, " ¢"), use_container_width=True)

    with c2:
        st.markdown("**Soja CBOT (¢/bu)**")
        st.caption("Signal de substitution : si maïs cher → agriculteurs pivotent vers soja")
        st.plotly_chart(make_chart(df_soy, "Soja", "#3B6D11", 1100, 1300, " ¢"), use_container_width=True)

        st.markdown("**Engrais** *(saisie manuelle)*")
        ef1, ef2, ef3 = st.columns(3)
        with ef1:
            st.metric(
                f"Urée Tampa {status(m_urea,'urea')}",
                f"${m_urea}/t",
                f"{pct_change(m_urea, BASELINE['urea']):+.1f}%",
                delta_color="inverse",
            )
        with ef2:
            st.metric(
                "DAP",
                f"${m_dap}/t",
                f"{pct_change(m_dap, BASELINE['dap']):+.1f}%",
                delta_color="inverse",
            )
        with ef3:
            st.metric(
                "Ammoniac",
                f"${m_ammonia}/t",
                f"{pct_change(m_ammonia, BASELINE['ammonia']):+.1f}%",
                delta_color="inverse",
            )

        st.markdown("")
        st.markdown("**Chaîne de causalité engrais → alimentation**")
        chain_days = CRISIS_DAY
        lag_text = "Récoltes 2026–27 **déjà impactées** (décisions semis prises)" if chain_days > 45 else "Fenêtre FAO de 3 mois avant impact irréversible sur semis"
        st.warning(f"📌 J+{chain_days} de crise : {lag_text}")
        st.caption("Soufre Gulf (45% mondial) → H₂SO₄ → phosphate (OCP Maroc, Chine) → DAP/MAP → rendements céréales")

        with st.expander("🔗 Sources engrais", expanded=False):
            st.markdown("""
| Source | Lien |
|---|---|
| Green Markets (Urée) | [greenmarkets.com](https://www.greenmarkets.com) |
| ICIS Fertilizers | [icis.com](https://www.icis.com/fertilizers/) |
| FAO Food Price Index | [fao.org](https://www.fao.org/worldfoodsituation/foodpricesindex/en/) |
| NDSU Ag Trade Monitor | [capts-ndsu.com](https://www.capts-ndsu.com) |
""")

# ════════════════════════════════════════════════════════════════════
# TAB FRET & TRAFIC
# ════════════════════════════════════════════════════════════════════
with tab_m:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Actions tankers (proxies taux fret)**")
        st.caption("Hausse = taux fret élevés = détroit fermé / tension forte")

        for ticker, df, color, label in [
            ("FRO", df_fro, "#185FA5", "Frontline (FRO)"),
            ("STNG", df_stng, "#0C447C", "Scorpio Tankers (STNG)"),
            ("DHT", df_dht, "#3B8BD4", "DHT Holdings (DHT)"),
        ]:
            if df is not None:
                st.markdown(f"*{label}*")
                st.plotly_chart(make_chart(df, label, color, unit=" $"), use_container_width=True)

    with c2:
        st.markdown("**Indicateurs fret manuels**")
        fm1, fm2 = st.columns(2)
        with fm1:
            ship_pct = (m_ships / BASELINE["ships"]) * 100
            st.metric(
                f"Navires/j {status(m_ships, 'ships', inversed=True)}",
                f"{m_ships}/j",
                f"{ship_pct:.0f}% du trafic normal",
                delta_color="inverse",
            )
            st.metric(
                f"War risk {status(m_war_risk,'war_risk')}",
                f"{m_war_risk:.2f}%/transit",
                f"×{m_war_risk/BASELINE['war_risk']:.1f} vs normal",
                delta_color="inverse",
            )
        with fm2:
            st.metric(
                "VLCC day rate",
                f"${m_vlcc}k/j",
                f"×{m_vlcc/BASELINE['vlcc']:.1f} vs baseline",
                delta_color="inverse",
            )
            st.metric(
                "BDTI",
                f"{m_bdti}",
                "Baltic Tanker Index",
            )

        # Barre de progression trafic
        st.markdown("**Trafic détroit (% du niveau normal)**")
        pct_ships = min(m_ships / BASELINE["ships"], 1.0)
        bar_color = "#E24B4A" if pct_ships < 0.1 else "#EF9F27" if pct_ships < 0.3 else "#639922"
        st.markdown(
            f"""
            <div style="background:rgba(128,128,128,0.15);border-radius:6px;height:22px;width:100%;overflow:hidden">
              <div style="background:{bar_color};height:100%;width:{pct_ships*100:.1f}%;border-radius:6px;
                          display:flex;align-items:center;padding-left:8px;color:white;font-size:12px;font-weight:500">
                {pct_ships*100:.1f}% ({m_ships} navires/j)
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("")
        st.markdown("**Détour Cap de Bonne-Espérance**")
        extra_days = 8 if m_ships < 20 else 3
        extra_cost_pct = 25 if m_ships < 20 else 10
        st.info(
            f"📌 Avec {m_ships} navires/j → détournement actif\n\n"
            f"• +{extra_days} jours de transit\n"
            f"• +{extra_cost_pct}% coût fret estimé\n"
            f"• Taux VLCC × {m_vlcc/BASELINE['vlcc']:.1f}"
        )

        with st.expander("🔗 Sources fret & trafic", expanded=False):
            st.markdown("""
| Source | Lien |
|---|---|
| IMF PortWatch | [portwatch.imf.org](https://portwatch.imf.org) |
| HormuzTracker (libre) | [hormuztracker.com](https://hormuztracker.com) |
| NBC News Tracker | [nbcnews.com](https://www.nbcnews.com/data-graphics/strait-of-hormuz-ports-traffic-trump-us-iran-war-rcna331507) |
| Baltic Exchange | [balticexchange.com](https://www.balticexchange.com) |
| Lloyd's List | [lloydslist.com](https://www.lloydslist.com) |
| Statista (graphique) | [statista.com](https://www.statista.com/chart/35984/ship-traffic-in-the-strait-of-hormuz/) |
""")

# ════════════════════════════════════════════════════════════════════
# TAB MACRO & DEVISES
# ════════════════════════════════════════════════════════════════════
with tab_s:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**EUR/USD** — signal stress économique européen")
        st.plotly_chart(make_chart(df_eurusd, "EUR/USD", "#534AB7", unit=""), use_container_width=True)

        st.markdown("**Or ($/oz)** — signal risque géopolitique & inflation")
        st.plotly_chart(make_chart(df_gold, "Or", "#BA7517", unit=" $"), use_container_width=True)

    with c2:
        st.markdown("**Dollar Index (DXY)** — force USD = pression émergents")
        st.plotly_chart(make_chart(df_dxy, "DXY", "#0F6E56", unit=""), use_container_width=True)

        st.markdown("**Aluminium (ALI=F)** — proxy énergie industrielle")
        df_alu = fetch("ALI=F")
        st.plotly_chart(make_chart(df_alu, "Aluminium", "#888780", unit=" $"), use_container_width=True)

    st.markdown("")
    st.markdown("**Interprétation macro**")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.info("🇪🇺 **Europe**\nTTF ×2 + stockage 30%\n→ BCE bloquée\n→ Récession technique imminente DE/IT")
    with mc2:
        st.warning("🌏 **Pays émergents**\nDollar fort + énergie chère\n→ Devises sous pression\n→ Risque dette souveraine\n(CNUCED : 3,4 Mds de pers.)")
    with mc3:
        st.error("🇧🇩🇵🇰 **Asie du Sud**\nGNL coupé + urée bloquée\n→ Électricité rationnée\n→ Risque crise humanitaire")

# ════════════════════════════════════════════════════════════════════
# TAB SCÉNARIOS
# ════════════════════════════════════════════════════════════════════
with tab_sc:
    st.markdown(
        f"#### Si le détroit rouvre dans… *(à partir d'aujourd'hui, {TODAY.strftime('%d %b %Y')}, J+{CRISIS_DAY})*"
    )
    st.caption("⚠️ Les effets de rang 2 et 3 ne s'inversent pas instantanément à la réouverture — certains sont irréversibles à court terme.")

    sc1, sc2, sc3 = st.columns(3)

    with sc1:
        reopen_5 = TODAY + timedelta(days=5)
        st.markdown(f"### J+5\n*{reopen_5.strftime('%d %b %Y')} — Jour {CRISIS_DAY+5}*")
        st.markdown("---")
        st.markdown("""
**🛢️ Énergie**
- Prix déjà intégrés par marchés → baisse partielle seulement
- Réserves stratégiques partiellement reconstituables
- Primes d'assurance normalisent en ~2 semaines

**🌾 Alimentation**
- Urée : livraisons reprennent mais semis **déjà décidés**
- Impact récoltes 2026 **irréversible** dans certains pays
- Prix alimentaires restent élevés 3–6 mois

**🏭 Industrie**
- MEG, méthanol, graphite : stocks se reconstituent en 3–6 sem.
- Textile Bangladesh/Pakistan : dommages emplois persistants

**🌍 Verdict**
> 🟡 Réouverture utile pour l'énergie mais **ne résout pas les effets rang 2–3** déjà enclenchés (alimentation, industrie, emploi)
""")

    with sc2:
        reopen_20 = TODAY + timedelta(days=20)
        st.markdown(f"### J+20\n*{reopen_20.strftime('%d %b %Y')} — Jour {CRISIS_DAY+20}*")
        st.markdown("---")
        st.markdown("""
**🛢️ Énergie**
- Stockage gaz Europe : refill estival **insuffisant** pour hiver 2026-27
- SPR en cours d'épuisement dans plusieurs pays
- Pétrole : approvisionnement reconstitué mais coûts durables

**🌾 Alimentation**
- Saison Kharif Inde/Pakistan : **impact confirmé** sur rendements
- Boro rice Bangladesh : récolte sous-fertilisée → pénurie locale
- FAO : fenêtre 3 mois dépassée → effets 2026-27 inévitables

**🏭 Industrie**
- Bangladesh : pertes structurelles dans le textile
- Graphite synthétique EV : chaîne désorganisée ~6 mois

**🌍 Verdict**
> 🔴 La plupart des **effets rang 2 sont devenus irréversibles** à court terme. Récession technique Europe probable quelle que soit la suite.
""")

    with sc3:
        reopen_50 = TODAY + timedelta(days=50)
        st.markdown(f"### J+50\n*{reopen_50.strftime('%d %b %Y')} — Jour {CRISIS_DAY+50}*")
        st.markdown("---")
        st.markdown("""
**🛢️ Énergie**
- SPR épuisés dans plusieurs pays → prochain choc sans tampon
- Europe : hiver 2026-27 critique (stockage <50%)
- Pétrole : reconfigurations d'approvisionnement **durables**

**🌾 Alimentation**
- Récoltes mondiales 2026 réduites : –10 à –25% céréales
- Prix alimentaires +15–30% en 2026-27 (FAO projections)
- Bangladesh, Pakistan, Afrique Est : crise humanitaire

**🏭 Industrie & Macro**
- Récession Europe (DE, IT, NL) et Asie du Sud **confirmée**
- CNUCED : croissance mondiale 2,6% vs 2,9% attendu
- 3,4 Mds de personnes en risque de crise de la dette

**🌍 Verdict**
> 🔴🔴 **Effets rang 3 (macro, social, politique) déclenchés** dans toutes les zones. Reconfigurations géopolitiques durables en cours.
""")

    st.divider()

    # Tableau de seuils
    st.markdown("### Tableau de seuils de déclenchement")
    df_thresh = pd.DataFrame({
        "Indicateur":           ["Brent Crude", "TTF Gaz EU", "Urée Tampa", "Maïs CBOT", "Navires/j", "War risk"],
        "Baseline (fév. 2026)": ["82 $/bbl",    "32 €/MWh",   "475 $/t",   "420 ¢/bu",  "138/j",    "0.125%"],
        "Seuil alerte 🟡":      ["90 $/bbl",    "50 €/MWh",   "550 $/t",   "500 ¢/bu",  "<30/j",    "0.3%"],
        "Seuil critique 🔴":    ["110 $/bbl",   "65 €/MWh",   "700 $/t",   "650 ¢/bu",  "<10/j",    "0.5%"],
        "Valeur actuelle":      [
            f"{p_brent:.1f} $/bbl {status(p_brent,'brent') if p_brent else '?'}" ,
            f"{m_ttf} €/MWh {status(m_ttf,'ttf')}",
            f"{m_urea} $/t {status(m_urea,'urea')}",
            f"{p_corn:.0f} ¢/bu {status(p_corn/100,'corn') if p_corn else '?'}",
            f"{m_ships}/j {status(m_ships,'ships',inversed=True)}",
            f"{m_war_risk}% {status(m_war_risk,'war_risk')}",
        ],
    })
    st.dataframe(df_thresh, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**Sources automatiques** : yFinance (marchés, différé 15-20 min) · "
    "**Sources manuelles** (sidebar) : IMF PortWatch, ICE TTF, Green Markets, Baltic Exchange · "
    "**Analyses** : IEA, EIA, FAO, CNUCED, Atlantic Council, WEF · "
    "Hormuz Watch v1.0 — Module 3"
)
