"""
HORMUZ WATCH — Application complète
Modules 2 · 3 · 4 réunis dans un seul fichier Streamlit.
Gantt : x = date string ISO, base = date string ISO (pas de pd.Timestamp, pas de durée numérique)
"""
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(
    page_title="HORMUZ WATCH",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constantes ────────────────────────────────────────────────────────────────
CLOSURE_DATE = date(2026, 2, 28)
TODAY        = date.today()
DAYS_CLOSED  = (TODAY - CLOSURE_DATE).days
H6           = TODAY + timedelta(days=183)
H12          = TODAY + timedelta(days=365)

SEV_COLOR = {
    "critique": "#ef4444",
    "élevé":    "#f97316",
    "modéré":   "#eab308",
    "limité":   "#22c55e",
    "positif":  "#3b82f6",
}
SCEN_COLOR = {5: "#22c55e", 20: "#f59e0b", 50: "#ef4444"}

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🛢️ HORMUZ WATCH")
    st.error(f"🚫 Fermé J+{DAYS_CLOSED} jours\n28 fév. 2026")
    st.markdown("---")
    module = st.radio("Module", [
        "📊 Module 2 — Scénarios cascade",
        "📈 Module 3 — Suivi économique",
        "🔭 Module 4 — Projections 6-12 mois",
    ])
    st.markdown("---")
    scen_days = st.radio(
        "Scénario réouverture *(depuis aujourd'hui)*",
        options=[5, 20, 50],
        format_func=lambda x: f"J+{x}  →  {(TODAY+timedelta(days=x)).strftime('%d %b %Y')}",
    )
    reopen_date = TODAY + timedelta(days=scen_days)
    sc = SCEN_COLOR[scen_days]
    st.markdown(
        f'<div style="background:{sc}22;border-left:3px solid {sc};'
        f'padding:6px 10px;border-radius:4px;font-size:11px;margin:4px 0">'
        f'Fermeture totale ≈ {DAYS_CLOSED+scen_days} jours<br>'
        f'Réouverture {reopen_date.strftime("%d %b %Y")}</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 Actualiser données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Màj {datetime.now().strftime('%d/%m %H:%M')}")


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
M2 = {
    5: {
        "resume": "Réouverture rapide. Réserves IEA actives. Refill gaz Europe encore possible. Effets agricoles partiellement irréversibles (semis déjà décidés).",
        "zones": [
            dict(flag="🇨🇳", label="Chine", sev="critique",
                 r1=["Perte ~1/3 imports pétroliers","MEG 6,5 Mt/an bloqué","GNL : JKM spot en hausse","Méthanol Gulf : stocks bas"],
                 r2=["Réserves strat. activées (~1 Md bbls)","Chimie/plastiques ralentissent","Textile sous tension (polyester)","Graphite synthétique menacé"],
                 r3=["Pression politique prix carburant","Achats alternatifs Russie/Afrique","Levier géopolitique vs USA"]),
            dict(flag="🇮🇳", label="Inde", sev="critique",
                 r1=["60% imports pétroliers bloqués","40% urée + phosphate bloqués","3 usines urée fermées (manque GNL)","Remittances Gulf (~125 Mds$/an) à risque"],
                 r2=["Kharif 2026 sous pression engrais","Raffineries/chimie ralentissent","Hausse carburant → inflation alim."],
                 r3=["Pression sur roupie","Stocks alim. tampons mobilisés","Pressions politiques internes"]),
            dict(flag="🇪🇺", label="Europe", sev="élevé",
                 r1=["GNL Qatar (12-14%) bloqué","Stockage gaz à 30% (historiquement bas)","TTF ×2 mi-mars","Diesel/kérosène : hausses"],
                 r2=["Industrie chimie/acier : surcharges +30%","Engrais azotés européens réduits","Fret renchérit → inflation imports"],
                 r3=["BCE reporte baisses taux (19 mars)","UK inflation projetée >5% 2026","Débat dépendance énergétique"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["2/3 du GNL importé bloqué","Gas = 50% élec. Bangla / 25% Pakistan","Stop quasi-total LNG spot"],
                 r2=["Coupures électriques industrielles","Textile Bangladesh : risque arrêts","Urée locale stoppée (gaz feedstock)"],
                 r3=["Risque pénuries alimentaires","Instabilité sociale potentielle","Appels aide FAO/ONU"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["~2% conso pétrole via Hormuz","Urée Tampa : 475→680 $/t (+43%)","Prix pompe +30% (>4$/gal. mars)"],
                 r2=["Corn Belt à 75% engrais normaux","Substitution maïs→soja","Chimie USA (Dow) : production full out"],
                 r3=["Pression politique sur Trump","SPR activé (IEA 400 Mbbl)","Débat Congrès sécurité détroit"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Urée + phosphate bloqués","Soufre Gulf (45% mondial) arrêté","OCP Maroc : 3,7 Mt soufre menacées"],
                 r2=["Phosphate mondial réduit","Blé : Égypte/Sahel sous tension","Fret détourné → coût alim. monte"],
                 r3=["FAO : Bangladesh/Égypte/Sri Lanka rouges","Risque crise 2022-bis","Instabilité pays endettés"]),
        ],
        "mults": [
            dict(title="Soufre → phosphate → alimentation",
                 steps=["Soufre Gulf (45% mondial) bloqué","Acide sulfurique indisponible","OCP Maroc + Chine réduisent DAP/MAP","Phosphates raréfiés","Rendements blé/riz/maïs -10-25% (2026-27)"]),
            dict(title="GNL → urée → semis → prix alimentaires",
                 steps=["GNL Qatar (20% mondial) bloqué","Urée non synthétisable","Agriculteurs réduisent azote","Rendements -10 à -25%","Prix alim. +15-30% dès 2027"]),
            dict(title="Énergie → inflation → dette émergents",
                 steps=["Brent >100 $/bbl","Facture énergétique explose","Déficits budgétaires se creusent","FMI : 3,4 Mds pers. surexposés","Risques défauts souverains"]),
        ],
    },
    20: {
        "resume": "Fermeture ~80 jours. Stockage gaz Europe critique pour hiver 2026-27. Saison Kharif décidée sous contrainte. Récessions industrielles Europe confirmées.",
        "zones": [
            dict(flag="🇨🇳", label="Chine", sev="critique",
                 r1=["Réserves strat. en consommation","MEG : stocks sous seuil alerte","Méthanol : inventaires ports critiques"],
                 r2=["Chimie/plastiques -10-20%","Textile reconfiguré vers USA","Batteries EV : graphite +30%","Sidérurgie : pénurie DRI Golfe"],
                 r3=["Stimulus économique interne","Pression vers Russie/Kazakhstan","Signal indépendance énergétique"]),
            dict(flag="🇮🇳", label="Inde", sev="critique",
                 r1=["Kharif compromis (urée, DAP)","3 usines urée fermées confirmées","Raffineries sous tension (-40% crude)"],
                 r2=["Substitution légumineuses/céréales","Prix alim. domestiques +15-25%","Inflation +3-4 pts","Textile/polyester sous tension"],
                 r3=["Stocks alim. urgence mobilisés","Pression politique forte","Réorientation dip. vers alternatifs"]),
            dict(flag="🇪🇺", label="Europe", sev="élevé",
                 r1=["Refill gaz estival impossible","LNG USA/Australie saturé","Diesel : pénuries locales"],
                 r2=["Chimie/acier : réductions production","Engrais azotés européens réduits","Inflation CPI +2-3 pts","Récession technique All./Italie imminente"],
                 r3=["BCE bloquée (stagflation)","Solidarité énergétique intra-UE débattue","UK inflation >5%"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["Coupures électriques quotidiennes","Urée locale effondrée","Textile Bangladesh : arrêts production"],
                 r2=["Exports textiles Bangladesh -30-40%","Sécurité alim. dégradée (Boro rice)","Chômage industriel massif"],
                 r3=["FAO : Bangladesh zone rouge","Instabilité sociale possible","Aide internationale urgente"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["Corn Belt engrais <75%","SPR activé partiellement","Diesel agri. +15-25% coûts"],
                 r2=["Substitution maïs→soja confirmée","Prix viande/lait hausse (lag 3-6m)","Inflation alim. +2-3%"],
                 r3=["Pression tarifaire","Dow/CF Industries bénéficient","Débat food security"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Urée : 40-50% commerce mondial bloqué","OCP Maroc contraint (soufre)","Égypte : imports blé risqués (devises)"],
                 r2=["Saisons agri. 2026 irrémédiablement impactées","Prix alim. hausse pays import.","Sous-nutrition aggravée (PAM)"],
                 r3=["Instabilité politique N-Afrique","Crises gouvernance Sahel","Flux migratoires potentiels"]),
        ],
        "mults": [
            dict(title="MEG → textiles → emplois → stabilité sociale",
                 steps=["MEG Gulf (6,5 Mt/an) bloqué","Pénurie polyester/fibres","Bangladesh/Vietnam : arrêts usines","Millions emplois menacés","Instabilité sociale pays vulnérables"]),
            dict(title="Coke pétrole → graphite → batteries EV",
                 steps=["Raffineries Gulf sous-actives","Coke de pétrole raréfié","Graphite synthétique +30%","Coûts EV augmentent","Transition énergétique ralentie (effet pervers)"]),
            dict(title="Inflation énergie → dette souveraine émergents",
                 steps=["Énergie +50-100% pays import.","Déficits commerciaux explosent","Devises chutent vs USD","Taux dette extérieure montent","FMI : 3,4 Mds surexposés"]),
        ],
    },
    50: {
        "resume": "Fermeture ~110 jours. Crise alimentaire mondiale 2027 confirmée. Récessions industrielles multiples. Commerce mondial -2 pts. Crises humanitaires. Recompositions géopolitiques structurelles.",
        "zones": [
            dict(flag="🇨🇳", label="Chine", sev="critique",
                 r1=["Réserves insuffisantes (>2 mois)","Imports via Cap : +7-10j, +20-30% coût","MEG : chaîne textile restructurée"],
                 r2=["PIB 2026 : -1 à -2 pts","Chimie -15-25%","Chômage industriel localisé","EV : coûts structurellement élevés"],
                 r3=["Récession industrielle partielle","ENR : investissements massifs","Recomposition alliances énergie","Signal indépendance durable"]),
            dict(flag="🇮🇳", label="Inde", sev="critique",
                 r1=["Kharif 2026 : rendements -10 à -20%","Production industrielle -8-12%","Exports riz -25% → cascade mondiale"],
                 r2=["Inflation alim. domestique +20-30%","Pauvreté alim. aggravée (millions)","Textile : pertes emplois structurelles","PIB : -1,5 à -2,5% (FMI)"],
                 r3=["Tensions soc./politiques majeures","Soutien FMI possible","Réorientation dip. durable"]),
            dict(flag="🇪🇺", label="Europe", sev="élevé",
                 r1=["Stockage gaz hiver 2026-27 : <50%","Risque délestages industriels hiver","TTF structurellement >50 €/MWh"],
                 r2=["Récession technique All./Italie/Pays-Bas","Industrie lourde -20-30%","CPI zone euro +3-4 pts","Chômage industriel +0,5-1%"],
                 r3=["BCE : stagflation, politique paralysée","Crise politique pays exposés","LNG USA/ENR accélérée","Remise en cause dépendance fossile"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["Électricité : rationnement sévère","Textile Bangladesh -50-70% exports","Récolte Boro sous-fertilisée"],
                 r2=["Crise humanitaire potentielle","Malnutrition aggravée (millions)","Exode économique"],
                 r3=["Instabilité gouvernementale","Intervention humanitaire internationale","Crises monétaires taka/roupie"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["SPR quasi-épuisé (~120 jours)","Maïs 2026 : récolte réduite","Diesel agri. : impact structurel"],
                 r2=["Inflation alim. +4-6% sur 12m","Prix viande/lait +8-12%","PIB US : -0,5 à -1%"],
                 r3=["Pression politique majeure","Producteurs locaux renforcés durablement","Chimie US : self-sufficiency accélérée"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Saisons agri. 2026 sous-fertilisées","OCP Maroc production réduite","Pays Gulf : économies dévastées"],
                 r2=["Crise alim. régionale : -15-30% rendements","Prix alim. mondiaux +15-20% (FAO)","Exports agri. mondiaux réduits"],
                 r3=["Instabilité politique Égypte/Tunisie/Sahel","Crise dette pays importateurs","Flux migratoires accrus vers Europe"]),
        ],
        "mults": [
            dict(title="Méga-chaîne alimentaire (6 niveaux)",
                 steps=["GNL bloqué","Urée non produite","Soufre bloqué → phosphate indisponible","Agriculteurs réduisent doses","Rendements -10 à -25%","Prix alim. +15-30% · crise 2027"]),
            dict(title="Énergie → stagflation structurelle",
                 steps=["Pétrole >100$/bbl 50+ jours","Inflation mondiale +2-4 pts","Banques centrales paralysées","Taux hauts → crédit cher","PIB global 2,6% (CNUCED)","Défauts souverains émergents"]),
            dict(title="Crise fossile → transition paradoxale",
                 steps=["Coke pétrole raréfié → graphite +30%","EV coûts augmentent court terme","ENR budgets x2 (signal politique)","Crise fossile accélère transition","Reconfigurations géopolitiques durables"]),
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — INSTRUMENTS FINANCIERS
# ══════════════════════════════════════════════════════════════════════════════
INSTRUMENTS = {
    "🛢️ Énergie": [
        dict(label="Brent Crude",          ticker="BZ=F",    unit="$/bbl",   bl=73.5,   thr=30,  note="Pic observé 126$/bbl (8 mars 2026)"),
        dict(label="WTI Crude",            ticker="CL=F",    unit="$/bbl",   bl=70.5,   thr=30,  note="Référence USA"),
        dict(label="Gaz naturel US",       ticker="NG=F",    unit="$/MMBtu", bl=3.5,    thr=50,  note="Proxy Henry Hub (TTF Europe non dispo gratuitement)"),
        dict(label="Gazoline RBOB",        ticker="RB=F",    unit="$/gal",   bl=2.20,   thr=30,  note="+30% observé mars 2026 (>4$/gal)"),
        dict(label="Heating oil / diesel", ticker="HO=F",    unit="$/gal",   bl=2.45,   thr=30,  note="Diesel & kérosène proxy Gulf"),
    ],
    "🌱 Engrais & Chimie": [
        dict(label="CF Industries (urée)", ticker="CF",      unit="USD",     bl=84.0,   thr=30,  note="Proxy urée. CEO : 'full out for the year'"),
        dict(label="Mosaic (phosphate)",   ticker="MOS",     unit="USD",     bl=28.5,   thr=25,  note="Proxy DAP/MAP. Cascade soufre→phosphate"),
        dict(label="Nutrien",              ticker="NTR",     unit="USD",     bl=63.0,   thr=25,  note="Plus grand prod. engrais mondial"),
        dict(label="ICL Group",            ticker="ICL",     unit="USD",     bl=5.2,    thr=25,  note="Potasse + phosphates spécialisés"),
    ],
    "🌾 Alimentation": [
        dict(label="Maïs CBOT",            ticker="ZC=F",    unit="c/bu",    bl=455.0,  thr=20,  note="Corn Belt à 75% engrais normaux mi-mars"),
        dict(label="Blé CBOT",             ticker="ZW=F",    unit="c/bu",    bl=540.0,  thr=20,  note="Sécurité alimentaire mondiale"),
        dict(label="Soja CBOT",            ticker="ZS=F",    unit="c/bu",    bl=1010.0, thr=15,  note="Substitution maïs→soja documentée"),
        dict(label="Riz CBOT",             ticker="ZR=F",    unit="$/cwt",   bl=17.5,   thr=15,  note="Bangladesh/Sri Lanka/Inde : saisons critiques"),
    ],
    "🚢 Fret & Industrie": [
        dict(label="DHT Holdings (VLCC)",  ticker="DHT",     unit="USD",     bl=10.2,   thr=40,  note="Tankers VLCC proxy taux fret"),
        dict(label="Frontline (tankers)",  ticker="FRO",     unit="USD",     bl=19.5,   thr=40,  note="Flotte détournée Cap Bonne-Espérance"),
        dict(label="Aluminium (ALI=F)",    ticker="ALI=F",   unit="$/t",     bl=2460.0, thr=15,  note="Industrie énergie-intensive. Surcharges +30%"),
        dict(label="Dow Chemical",         ticker="DOW",     unit="USD",     bl=34.5,   thr=20,  note="Chimie USA bénéficiaire indirect"),
    ],
    "📊 Macro & Finance": [
        dict(label="EUR/USD",              ticker="EURUSD=X",unit="",        bl=1.047,  thr=5,   note="BCE a bloqué baisses taux (19 mars)"),
        dict(label="USD/JPY",              ticker="JPY=X",   unit="",        bl=152.0,  thr=5,   note="Japon quasi-100% dépendant Gulf"),
        dict(label="VIX",                  ticker="^VIX",    unit="pts",     bl=18.0,   thr=50,  note="Fear index géopolitique"),
        dict(label="S&P 500",              ticker="^GSPC",   unit="pts",     bl=5900.0, thr=10,  note="Impact macro agrégé USA"),
    ],
}


@st.cache_data(ttl=900)
def fetch(ticker, start, end):
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


def safe_last(s):
    if s is None or s.empty:
        return None
    try:
        return float(s.iloc[-1])
    except Exception:
        return None


def dpct(cur, bl):
    if cur is None or bl == 0:
        return 0.0
    return (cur - bl) / bl * 100.0


def sig(dp, thr):
    a, t = abs(dp), abs(thr)
    if a >= t:        return "🔴", "#ef4444"
    if a >= t * 0.60: return "🟠", "#f97316"
    if a >= t * 0.30: return "🟡", "#eab308"
    return "🟢", "#22c55e"


def fmtv(v, unit):
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"{v:,.0f} {unit}".strip()
    if abs(v) >= 100:
        return f"{v:.1f} {unit}".strip()
    return f"{v:.2f} {unit}".strip()


def indexed_chart(series_map, reopen_d, scen_color, scen_lbl):
    palette = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
    fig = go.Figure()
    for i, (lbl, s) in enumerate(series_map.items()):
        if s.empty:
            continue
        pos = s.index.searchsorted(pd.Timestamp(CLOSURE_DATE))
        ref = float(s.iloc[max(0, pos - 1)]) if pos > 0 else float(s.iloc[0])
        if ref == 0:
            continue
        norm = s / ref * 100.0
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm.values.tolist(),
            name=lbl, mode="lines",
            line=dict(width=1.8, color=palette[i % len(palette)])
        ))
    closure_s = CLOSURE_DATE.strftime("%Y-%m-%d")
    reopen_s  = reopen_d.strftime("%Y-%m-%d")
    fig.add_hline(y=100, line=dict(dash="dot", color="#9ca3af", width=0.8))
    fig.add_vline(x=closure_s, line=dict(dash="dash", color="#ef4444", width=1.1))
    fig.add_annotation(x=closure_s, y=1, xref="x", yref="paper",
                       text="Fermeture", showarrow=False,
                       font=dict(size=9, color="#ef4444"),
                       xanchor="left", yanchor="top", bgcolor="white", opacity=0.85)
    fig.add_vline(x=reopen_s, line=dict(dash="dash", color=scen_color, width=1.1))
    fig.add_annotation(x=reopen_s, y=1, xref="x", yref="paper",
                       text=scen_lbl, showarrow=False,
                       font=dict(size=9, color=scen_color),
                       xanchor="right", yanchor="top", bgcolor="white", opacity=0.85)
    fig.update_layout(
        height=300,
        title=dict(text="Indexé base 100 = fermeture (28 fév. 2026)", font_size=11),
        margin=dict(t=36, b=70, l=36, r=12),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6", tickformat="%d %b"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Index"),
        legend=dict(orientation="h", y=-0.38, font_size=10),
        hovermode="x unified",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — DONNÉES PROJECTIONS
# ══════════════════════════════════════════════════════════════════════════════
PROJ = {
    5: {
        "color": "#22c55e", "label": "Réouverture J+5",
        "resume": "Réouverture rapide. Choc absorbé progressivement. Effets agricoles partiellement irréversibles. Hiver 2026-27 gérable.",
        "kpis": [
            ("Brent H+6m",   "~85 $/bbl",    "modéré"),  ("Brent H+12m",  "~78 $/bbl",   "limité"),
            ("Urée H+6m",    "+25-35%",       "élevé"),   ("FAO alim H+6m","+8-12%",      "modéré"),
            ("CPI Euro H+6m","~3%",           "modéré"),  ("PIB Euro 2026","+0.5-0.8%",   "modéré"),
            ("Commerce 2026","+2-2.5%",       "modéré"),  ("Crise alim.",  "Limitée",     "limité"),
        ],
        "cascade": {
            "Énergie":   "Brent → ~85$/bbl. TTF correction progressive.",
            "Engrais":   "Urée +35% résiduel. Semis 2026 déjà impactés.",
            "Alim.":     "FAO +8-12%. Maïs sous tension résiduelle.",
            "Macro":     "VIX retombe. BCE reprend baisses taux H2 2026.",
        },
        "sectors": {
            "Énergie": [
                ("Brent crude",      "~85 $/bbl",          "~78 $/bbl",       "modéré",  "EIA : risk premium résiduel ~10$. Allianz : 78$/bbl fin 2026"),
                ("Gaz Europe TTF",   "~35-40 €/MWh",       "~30-35 €/MWh",    "modéré",  "Refill possible. Stockage ~55-60% objectif hivernage"),
                ("Production Gulf",  "-3 Mb/j résiduel",   "~pré-conflit",    "modéré",  "EIA : retour progressif. Infra. à remettre en route"),
            ],
            "Alimentation": [
                ("Urée prix",        "+25-35%",             "+5-10% résid.",   "élevé",   "Semis 2026 déjà décidés — irréversible cette saison"),
                ("Maïs CBOT",        "+10-15%",             "+3-5% résid.",    "modéré",  "Récolte 2027 normale si engrais disponibles"),
                ("FAO Index",        "+8-12%",              "+3-5% résid.",    "modéré",  "Normalisation attendue courant 2027"),
            ],
            "Industrie": [
                ("MEG polyester",    "Tension résiduelle",  "Normalisé",       "modéré",  "Chine réapprovisionne via USA. Coûts +15-20%"),
                ("Aluminium",        "+8-12%",              "+3-5% résid.",    "modéré",  "Surcharges industrielles réduites"),
                ("Fret maritime",    "+15-25% résid.",      "Normalisé",       "modéré",  "VLCC taux normalisent. Cap Bonne-Espérance cesse"),
            ],
            "Macro": [
                ("PIB Eurozone",     "+0.5-0.8% 2026",      "+0.8-1.2% 2027",  "modéré",  "Allianz : +0.2% si >3 mois. J+5 = récession évitée"),
                ("CPI Eurozone",     "~2.8-3%",             "~2.2-2.5%",       "modéré",  "Inflation résorbée H2 2026. BCE reprend"),
                ("Commerce mondial", "+2-2.5%",             "+3-3.5%",         "modéré",  "CNUCED : haut de fourchette"),
            ],
            "Géopolitique": [
                ("ENR investissement","Accélération",       "+20-30% budgets", "positif", "Signal fort. Budgets ENR revus Europe/Asie"),
                ("LNG USA→Europe",   "Contrats durables",  "Contrats 10-20 ans","positif","Diversification structurelle accélérée"),
                ("Marchés émergents","Stress financier",   "Récupération lente","modéré", "FMI assistance. Risques contenus"),
            ],
        },
    },
    20: {
        "color": "#f59e0b", "label": "Réouverture J+20",
        "resume": "Fermeture totale ~80 jours. Stockage gaz Europe critique. Kharif décidé sous contrainte. Récessions industrielles Europe confirmées.",
        "kpis": [
            ("Brent H+6m",   "~95-105 $/bbl", "élevé"),   ("Brent H+12m",  "~85-95 $/bbl","élevé"),
            ("Urée H+6m",    "+50-60%",        "critique"),("FAO alim H+6m","+15-25%",     "élevé"),
            ("CPI Euro H+6m","~3.5-4%",        "élevé"),   ("PIB Euro 2026","+0.1-0.3%",   "critique"),
            ("Commerce 2026","+1.5-2%",        "élevé"),   ("Crise alim.",  "Confirmée",   "critique"),
        ],
        "cascade": {
            "Énergie":   "Refill gaz Europe <40%. Hiver 2026-27 à risque critique.",
            "Engrais":   "Cascade soufre→phosphate irréversible. Rendements 2026 réduits.",
            "Alim.":     "Prix +10-20% à 6 mois. FAO : escalade planting 2026+.",
            "Macro":     "Récession All./Italie. BCE bloquée. UK inflation >5%.",
        },
        "sectors": {
            "Énergie": [
                ("Brent crude",      "~95-105 $/bbl",       "~85-95 $/bbl",    "élevé",   "Goldman : >100$ si fermeture >1 mois"),
                ("Gaz Europe TTF",   "~50-60 €/MWh",        "~40-50 €/MWh",    "critique", "Hiver 2026-27 sous tension critique"),
                ("Production Gulf",  "-7-9 Mb/j résid.",    "-2-3 Mb/j résid.","critique", "EIA : shut-in 9.1 Mb/j avril 2026"),
            ],
            "Alimentation": [
                ("Urée prix",        "+50-60%",             "+20-30% résid.",  "critique", "Saison agri. 2026 compromise"),
                ("Maïs CBOT",        "+20-25%",             "+10-15% résid.",  "élevé",   "Corn Belt : récolte 2026 réduite"),
                ("FAO Index",        "+15-25%",             "+10-15%",         "élevé",   "FAO : escalade signif. au-delà 2026"),
            ],
            "Industrie": [
                ("MEG polyester",    "Pénurie aiguë",       "+10-15% résid.",  "critique", "Inventaires Chine sous seuil alerte"),
                ("Aluminium",        "+15-20%",             "+8-12% résid.",   "élevé",   "Surcharges +30% maintenues"),
                ("Textile Bangladesh","-30-40% export",     "-10-15% résid.",  "critique", "Millions d'emplois menacés"),
            ],
            "Macro": [
                ("PIB Eurozone",     "+0.1-0.3% 2026",      "~0.5% 2027",      "critique", "Allianz : récession technique All./Italie"),
                ("CPI Eurozone",     "~3.5-4%",             "~3-3.5%",         "élevé",   "UK >5%. Zone euro >3% début 2027"),
                ("Commerce mondial", "+1.5-2%",             "+2-2.5%",         "élevé",   "CNUCED : bas de fourchette"),
            ],
            "Géopolitique": [
                ("Bangladesh/Pak",   "Crise sociale",       "Transition difficile","critique","Électricité rationnée. Textile en crise"),
                ("Égypte/Sahel",     "Alerte FAO",          "Crise alimentaire","critique", "Réserves blé épuisées. Aide int. mobilisée"),
                ("ENR",              "Accélération forte",  "Rupture structurelle","positif","Budgets ENR +30-50% en urgence"),
            ],
        },
    },
    50: {
        "color": "#ef4444", "label": "Réouverture J+50",
        "resume": "Fermeture totale ~110 jours. Crise alimentaire mondiale 2027 confirmée. Récessions multiples. Commerce -2 pts. Crises humanitaires. Recompositions géopolitiques.",
        "kpis": [
            ("Brent H+6m",   "~105-115 $/bbl","critique"),("Brent H+12m",  "~90-100 $/bbl","élevé"),
            ("Urée H+6m",    "+60-70%",        "critique"),("FAO alim H+6m","+25-35%",      "critique"),
            ("CPI Euro H+6m","~4-5%",          "critique"),("PIB Euro 2026","-0.2 à +0.1%", "critique"),
            ("Commerce 2026","+1.5%",          "critique"),("Crise alim.",  "Mondiale 2027","critique"),
        ],
        "cascade": {
            "Énergie":   "Réserves épuisées. Délestages industriels hiver Europe.",
            "Engrais":   "Récoltes 2026 -10-25%. Urée +70%. Phosphate structurel.",
            "Alim.":     "FAO : crise 2027. Bangladesh/Pakistan/Égypte rouges.",
            "Macro":     "Stagflation mondiale. PIB -1%. 3,4 Mds à risque souverain.",
        },
        "sectors": {
            "Énergie": [
                ("Brent crude",      "~105-115 $/bbl",      "~90-100 $/bbl",   "critique", "EIA STEO : pic Q2 115$/bbl. Risk premium prolongé"),
                ("Gaz Europe TTF",   "~60-70 €/MWh",        "~45-55 €/MWh",    "critique", "Hiver 2026-27 : rationnement industrie probable"),
                ("Production Gulf",  "-9-10 Mb/j",          "-2-4 Mb/j résid.","critique", "Standard Chartered : 8 Mb/j retirés des flux"),
            ],
            "Alimentation": [
                ("Urée prix",        "+60-70%",             "+30-40% résid.",  "critique", "FAO : 3 mois = seuil critique décisions planting"),
                ("Maïs CBOT",        "+25-30%",             "+15-20% résid.",  "critique", "Corn Belt -15-20% rendement 2026"),
                ("FAO Index",        "+25-35%",             "+20-25%",         "critique", "Proche 2022 mais système plus fragile"),
            ],
            "Industrie": [
                ("MEG polyester",    "Rupture supply",      "+15-20% résid.",  "critique", "Inventaires Chine à zéro"),
                ("Aluminium",        "+20-30%",             "+10-15% résid.",  "critique", "Fermetures usines Europe confirmées"),
                ("Sidérurgie",       "-15-20% prod.",       "-5-8% résid.",    "critique", "DRI/pellets Gulf bloqués. Reconfiguration longue"),
            ],
            "Macro": [
                ("PIB Eurozone",     "-0.2 à +0.1%",        "~0.2-0.5% 2027",  "critique", "Allianz : récession technique confirmée si >3 mois"),
                ("CPI Eurozone",     "~4-5%",               "~3.5-4% 2027",    "critique", "Stagflation. BCE impuissante"),
                ("Commerce mondial", "+1.5%",               "+2-2.5% 2027",    "critique", "CNUCED : plus bas fourchette 2026"),
            ],
            "Géopolitique": [
                ("Crises humanitaires","Bangla/Pak/Égypte", "Crise 2027",      "critique", "FAO/PAM : 'perfect storm' alimentation"),
                ("Marchés émergents","Défauts souverains",  "Restructurations","critique", "FMI : 3,4 Mds surexposés"),
                ("Ordre énergétique","Recomposition",       "Nouvel ordre",    "élevé",   "ENR +50%. Dépendance fossile remise en cause"),
            ],
        },
    },
}


def make_gantt(scen_days):
    """Retourne une liste de dicts pour le Gantt.
    FIX : x et base sont des strings ISO (pas pd.Timestamp, pas numérique).
    """
    reopen = TODAY + timedelta(days=scen_days)
    # (secteur, effet, offset_depuis_réouverture_jours, durée_jours, sévérité)
    effects = [
        ("Énergie",      "Brent correction",       0,   60,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Énergie",      "TTF gaz Europe",          0,  120,  "modéré"  if scen_days <= 5  else "critique"),
        ("Énergie",      "Production Gulf",         0,  180,  "élevé"   if scen_days <= 5  else "critique"),
        ("Alimentation", "Urée correction prix",    0,   90,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Alimentation", "Impact récolte 2026",    30,  120,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Alimentation", "Crise alimentaire 2027",120,  180,  "limité"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Industrie",    "MEG / méthanol",          0,   60,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Industrie",    "Fret maritime",            0,   90,  "modéré"  if scen_days <= 5  else "élevé"),
        ("Industrie",    "Textile Bangladesh",      30,  120,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Macro",        "Inflation CPI",            0,  180,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Macro",        "PIB Eurozone",            30,  270,  "modéré"  if scen_days <= 5  else "critique"),
        ("Macro",        "Marchés émergents",        0,  270,  "élevé"   if scen_days <= 5  else "critique"),
        ("Géopolitique", "ENR accélération",         0,  365,  "positif"),
        ("Géopolitique", "Crises humanitaires",     60,  300,  "modéré"  if scen_days <= 5  else "élevé"   if scen_days <= 20 else "critique"),
        ("Géopolitique", "Recomposition alliances", 60,  365,  "élevé"),
    ]
    rows = []
    for sector, effect, offset, duration, sev in effects:
        start_d = reopen + timedelta(days=offset)
        end_d   = min(start_d + timedelta(days=duration), H12 + timedelta(days=30))
        rows.append(dict(
            label=f"{sector} · {effect}",
            start=start_d.strftime("%Y-%m-%d"),   # string ISO
            end=end_d.strftime("%Y-%m-%d"),         # string ISO
            color=SEV_COLOR.get(sev, "#9ca3af"),
        ))
    return rows


def gantt_chart(rows, scen_color, scen_lbl):
    """
    FIX GANTT : on utilise go.Bar avec type='date' sur l'axe X.
    - base = [start_str]  (date ISO)
    - x    = [end_str]    (date ISO — plotly calcule la largeur automatiquement)
    - autorange="reversed" pour afficher de haut en bas
    """
    fig = go.Figure()
    for row in rows:
        fig.add_trace(go.Bar(
            x=[row["end"]],
            base=[row["start"]],
            y=[row["label"]],
            orientation="h",
            marker_color=row["color"],
            marker_opacity=0.78,
            showlegend=False,
            hovertemplate=(
                f"<b>{row['label']}</b><br>"
                f"Du {row['start']} au {row['end']}<extra></extra>"
            ),
        ))

    # Lignes verticales — UNIQUEMENT en string ISO, SANS annotation_text dans add_vline
    today_s = TODAY.strftime("%Y-%m-%d")
    h6_s    = H6.strftime("%Y-%m-%d")
    h12_s   = H12.strftime("%Y-%m-%d")

    for x_s, lbl, col in [
        (today_s, "Aujourd'hui", "#6b7280"),
        (h6_s,    "H+6 mois",   "#3b82f6"),
        (h12_s,   "H+12 mois",  "#8b5cf6"),
    ]:
        fig.add_vline(x=x_s, line=dict(dash="dash", color=col, width=1.1))
        fig.add_annotation(
            x=x_s, y=1, xref="x", yref="paper",
            text=lbl, showarrow=False,
            font=dict(size=9, color=col),
            xanchor="left", yanchor="top",
            bgcolor="white", opacity=0.85,
        )

    fig.update_layout(
        height=440,
        margin=dict(t=24, b=20, l=215, r=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            type="date",
            showgrid=True,
            gridcolor="#f3f4f6",
            tickformat="%b %Y",
            range=[TODAY.strftime("%Y-%m-%d"), (H12 + timedelta(days=30)).strftime("%Y-%m-%d")],
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=10),
            autorange="reversed",
        ),
        hovermode="closest",
        barmode="overlay",
    )
    return fig


def risk_chart(scen_days):
    zones = ["Chine", "Inde", "Europe", "Bangladesh/Pak", "USA", "Afrique/M-O"]
    s6  = {5: [55,65,50,75,35,60], 20: [70,80,65,90,45,75], 50: [85,90,80,95,55,85]}[scen_days]
    s12 = {5: [35,45,30,55,20,40], 20: [55,65,50,80,35,65], 50: [70,80,65,90,45,80]}[scen_days]

    def c(s):
        return "#ef4444" if s >= 80 else "#f97316" if s >= 65 else "#eab308" if s >= 45 else "#22c55e"

    fig = go.Figure()
    for i, (z, a, b) in enumerate(zip(zones, s6, s12)):
        fig.add_trace(go.Bar(
            name="6 mois", x=[a], y=[z], orientation="h",
            marker_color=c(a), opacity=0.85, showlegend=(i == 0),
            hovertemplate=f"{z}<br>H+6m : {a}/100<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="12 mois", x=[b], y=[z], orientation="h",
            marker_color=c(b), opacity=0.45, showlegend=(i == 0),
            hovertemplate=f"{z}<br>H+12m : {b}/100<extra></extra>",
        ))
    fig.update_layout(
        barmode="group", height=280,
        margin=dict(t=16, b=20, l=120, r=50),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(range=[0, 100], title="Score risque /100",
                   showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.22, font_size=10),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# RENDU
# ══════════════════════════════════════════════════════════════════════════════

# ── MODULE 2 ──────────────────────────────────────────────────────────────────
if module.startswith("📊"):
    st.title("📊 Module 2 — Effets en cascade par zone")
    d = M2[scen_days]
    st.info(d["resume"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jours fermés",      f"J+{DAYS_CLOSED}")
    c2.metric("Réouverture",       reopen_date.strftime("%d %b %Y"))
    c3.metric("Fermeture totale",  f"~{DAYS_CLOSED+scen_days} jours")
    c4.metric("Trafic détroit",    "6-7 navires/j")

    st.markdown("---")
    st.subheader("Effets par zone géographique")
    for z in d["zones"]:
        c_hex = SEV_COLOR.get(z["sev"], "#9ca3af")
        with st.expander(f"{z['flag']}  {z['label']}  —  **{z['sev'].upper()}**", expanded=False):
            cols = st.columns(3)
            for col, key, title in [
                (cols[0], "r1", "RANG 1 — Choc direct"),
                (cols[1], "r2", "RANG 2 — Dérivés"),
                (cols[2], "r3", "RANG 3 — Macro / social"),
            ]:
                col.markdown(f"**{title}**")
                for item in z[key]:
                    col.markdown(f"- {item}")

    st.markdown("---")
    st.subheader("Effets démultiplicateurs")
    for m in d["mults"]:
        arrows = " → ".join(m["steps"])
        st.markdown(f"**{m['title']}**")
        st.markdown(
            f'<div style="background:#f8f9fa;border-left:3px solid {SCEN_COLOR[scen_days]};'
            f'padding:8px 12px;border-radius:4px;font-size:12px;line-height:1.7;margin-bottom:10px">'
            f'{arrows}</div>',
            unsafe_allow_html=True,
        )

# ── MODULE 3 ──────────────────────────────────────────────────────────────────
elif module.startswith("📈"):
    st.title("📈 Module 3 — Suivi Économique")
    lookback = st.slider("Historique (jours)", 30, 180, 60, step=10)
    START = (TODAY - timedelta(days=lookback)).strftime("%Y-%m-%d")
    END   = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    st.subheader("Indicateurs clés")
    KPI = [
        dict(label="Brent Crude",  ticker="BZ=F",  unit="$/bbl", bl=73.5,  thr=30, inv=False),
        dict(label="CF Industries",ticker="CF",     unit="USD",   bl=84.0,  thr=30, inv=False),
        dict(label="Maïs CBOT",    ticker="ZC=F",  unit="c/bu",  bl=455.0, thr=20, inv=False),
        dict(label="VIX",          ticker="^VIX",  unit="pts",   bl=18.0,  thr=50, inv=True),
    ]
    for col, k in zip(st.columns(4), KPI):
        s   = fetch(k["ticker"], START, END)
        cur = safe_last(s)
        dp  = dpct(cur, k["bl"])
        ico, _ = sig(dp, k["thr"])
        with col:
            if cur is not None:
                st.metric(f"{ico} {k['label']}", fmtv(cur, k["unit"]),
                          f"{dp:+.1f}% vs J0",
                          delta_color="off" if k["inv"] else "normal")
            else:
                st.metric(k["label"], "—", "indisponible")

    st.markdown("---")
    for cat, instruments in INSTRUMENTS.items():
        with st.expander(cat, expanded=False):
            rows, series_map, local_alerts = [], {}, []
            for inst in instruments:
                s   = fetch(inst["ticker"], START, END)
                cur = safe_last(s)
                dp  = dpct(cur, inst["bl"])
                ico, col_hex = sig(dp, inst["thr"])
                rows.append({
                    "": ico, "Indicateur": inst["label"],
                    "Valeur": fmtv(cur, inst["unit"]),
                    "J0 (27/02)": fmtv(inst["bl"], inst["unit"]),
                    "Δ J0": f"{dp:+.1f}%" if cur is not None else "—",
                    "Seuil": f"±{inst['thr']}%",
                })
                if not s.empty:
                    series_map[inst["label"]] = s
                if ico in ("🔴", "🟠"):
                    local_alerts.append((ico, col_hex, inst["label"], dp, inst["note"]))

            left, right = st.columns([1.0, 2.0])
            with left:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220,
                             column_config={
                                 "": st.column_config.TextColumn("", width=28),
                                 "Indicateur": st.column_config.TextColumn("Indicateur", width=175),
                                 "Δ J0": st.column_config.TextColumn("Δ J0", width=70),
                             })
                for ico, col_hex, lbl, dp, note in local_alerts:
                    st.markdown(
                        f'<div style="background:{col_hex}22;border-left:3px solid {col_hex};'
                        f'border-radius:4px;padding:5px 9px;font-size:11px;margin:3px 0">'
                        f'{ico} <b>{lbl}</b> : {dp:+.1f}% · {note}</div>',
                        unsafe_allow_html=True,
                    )
            with right:
                if series_map:
                    st.plotly_chart(
                        indexed_chart(series_map, reopen_date, SCEN_COLOR[scen_days], f"Réouv. J+{scen_days}"),
                        use_container_width=True,
                    )
                else:
                    st.info("Données Yahoo Finance indisponibles pour cette période.")

    st.markdown("---")
    st.subheader("🚨 Alertes actives")
    alert_rows = []
    for cat, instruments in INSTRUMENTS.items():
        for inst in instruments:
            s   = fetch(inst["ticker"], START, END)
            cur = safe_last(s)
            dp  = dpct(cur, inst["bl"])
            ico, _ = sig(dp, inst["thr"])
            if ico in ("🔴", "🟠") and cur is not None:
                alert_rows.append({
                    "Signal": ico, "Cat.": cat.split()[-1],
                    "Indicateur": inst["label"], "Valeur": fmtv(cur, inst["unit"]),
                    "Δ J0": f"{dp:+.1f}%", "Note": inst["note"],
                })
    if alert_rows:
        st.dataframe(pd.DataFrame(alert_rows).sort_values("Signal"),
                     use_container_width=True, hide_index=True)
    else:
        st.success("Aucune alerte active.")
    st.caption("Sources : Yahoo Finance · Baselines J0 au 27 fév. 2026 · Cache 15 min · NG=F = proxy TTF")

# ── MODULE 4 ──────────────────────────────────────────────────────────────────
else:
    st.title("🔭 Module 4 — Projections 6-12 mois")
    p = PROJ[scen_days]
    st.info(p["resume"])

    st.subheader("Indicateurs projetés")
    for chunk in [p["kpis"][:4], p["kpis"][4:]]:
        for col, (lbl, val, sev) in zip(st.columns(4), chunk):
            bg = SEV_COLOR.get(sev, "#9ca3af") + "22"
            col.markdown(
                f'<div style="background:{bg};border-radius:8px;padding:10px 12px;margin:2px">'
                f'<div style="font-size:11px;color:#6b7280;margin-bottom:3px">{lbl}</div>'
                f'<div style="font-size:15px;font-weight:500">{val}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("Timeline des effets — 12 mois post-réouverture")
    gantt_rows = make_gantt(scen_days)
    st.plotly_chart(gantt_chart(gantt_rows, p["color"], p["label"]), use_container_width=True)

    leg_cols = st.columns(5)
    for col, (sev, col_hex) in zip(leg_cols, SEV_COLOR.items()):
        col.markdown(
            f'<div style="background:{col_hex}33;border-left:3px solid {col_hex};'
            f'padding:3px 8px;border-radius:4px;font-size:11px">{sev.capitalize()}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("Matrice risques par zone")
    st.caption("Score composite 0-100 à H+6m (plein) et H+12m (clair). 80+=critique, 65+=élevé, 45+=modéré.")
    st.plotly_chart(risk_chart(scen_days), use_container_width=True)

    st.markdown("---")
    st.subheader("Projections détaillées par secteur")
    for sector, items in p["sectors"].items():
        with st.expander(sector, expanded=False):
            header = st.columns([1, 1, 1, 2])
            header[0].markdown("**Indicateur**")
            header[1].markdown("**H+6 mois**")
            header[2].markdown("**H+12 mois**")
            header[3].markdown("**Source**")
            for ind, v6, v12, sev, note in items:
                c_hex = SEV_COLOR.get(sev, "#9ca3af")
                cols  = st.columns([1, 1, 1, 2])
                cols[0].markdown(f"**{ind}**")
                cols[1].markdown(f'<span style="color:{c_hex};font-weight:500">{v6}</span>', unsafe_allow_html=True)
                cols[2].markdown(f'<span style="color:{c_hex}">{v12}</span>', unsafe_allow_html=True)
                cols[3].caption(note)

    st.markdown("---")
    with st.expander(f"📋 Cascade — {p['label']}"):
        for k, v in p["cascade"].items():
            st.markdown(f"**{k}** : {v}")

    with st.expander("📚 Sources"):
        st.markdown("""
| Source | Données clés |
|---|---|
| **EIA STEO avr. 2026** | Brent pic Q2 115$/bbl · Shut-in 9.1 Mb/j · Risk premium prolongé |
| **Allianz Research mars 2026** | PIB Eurozone +0.2% si >3 mois · CPI 3% zone euro · 3.2% US |
| **FMI avr. 2026** | PIB mondial 2.6% · Iran -6.1% · Arabie Saoudite 3.1% |
| **CNUCED 2026** | Commerce +1.5-2.5% vs 4.7% · 3.4 Mds personnes surexposées |
| **FAO mars 2026** | 3 mois = seuil critique planting 2026+ |
| **Goldman Sachs** | Brent >100$ si fermeture >1 mois |
| **Standard Chartered** | 8 Mb/j retirés des flux mondiaux |
""")

    st.caption(
        f"H+6m = {H6.strftime('%d %b %Y')} · "
        f"H+12m = {H12.strftime('%d %b %Y')} · "
        f"Réouverture scénario = {reopen_date.strftime('%d %b %Y')}"
    )
