"""
HORMUZ WATCH — Application complète
🏠 Accueil · 🚢 Module 1 AIS · 📊 Module 2 Cascade
📈 Module 3 Marchés · 🔭 Module 4 Projections
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, datetime, timedelta

st.set_page_config(
    page_title="HORMUZ WATCH",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
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
# DONNÉES CARTE D'ACCUEIL — VULNÉRABILITÉ PAR PAYS
# ══════════════════════════════════════════════════════════════════════════════
VULNERABILITY = [
    ("IRN","Iran",           98,"critique","Pays en guerre. Fermeture du détroit directement liée au conflit. PIB -6,1% (FMI)"),
    ("QAT","Qatar",          95,"critique","100% exports GNL via détroit. Force majeure QatarEnergy déclarée 4 mars"),
    ("KWT","Koweït",         92,"critique","100% exports pétrole via détroit. Économie en récession sévère"),
    ("IRQ","Irak",           92,"critique","Pétrole = 90% des revenus. Shut-in 2+ Mb/j. Crise économique"),
    ("BGD","Bangladesh",     90,"critique","2/3 du GNL importé via détroit. Gaz = 50% électricité"),
    ("JPN","Japon",          90,"critique","Quasi-100% dépendant Gulf (pétrole + GNL). Aucune alternative"),
    ("KOR","Corée du Sud",   90,"critique","Quasi-100% dépendant Gulf (pétrole + GNL). Industrie exposée"),
    ("LKA","Sri Lanka",      85,"critique","3/4 énergie importée. Déjà fragilisé par crise 2022"),
    ("PAK","Pakistan",       85,"critique","Gaz = 25% élec. Urée locale effondrée. Crise alimentaire imminente"),
    ("ARE","Émirats arabes", 85,"critique","Exports partiellement bloqués. Pipeline Fujairah (capacité limitée)"),
    ("SAU","Arabie Saoudite",82,"critique","Exports partiellement bloqués. Pipeline Petroline limité à 5 Mb/j"),
    ("IND","Inde",           85,"critique","60% imports pétroliers + 40% urée/phosphate bloqués"),
    ("CHN","Chine",          80,"critique","1/3 pétrole importé + MEG + méthanol bloqués. PIB -1 à -2 pts"),
    ("TWN","Taïwan",         80,"critique","Quasi-100% dépendant Gulf. Semi-conducteurs (hélium) menacés"),
    ("PHL","Philippines",    68,"élevé",  "Dépendant pétrole Gulf. FMI : second tier exposé"),
    ("THA","Thaïlande",      65,"élevé",  "Énergie + chimie. Industrie textile exposée via MEG"),
    ("MYS","Malaisie",       60,"élevé",  "Énergie + chimie. Ports de transit perturbés"),
    ("SGP","Singapour",      58,"élevé",  "Hub régional. Fret maritime + raffinage sous tension"),
    ("IDN","Indonésie",      52,"élevé",  "Imports partiels. Dépendant urée Gulf pour agriculture"),
    ("EGY","Égypte",         72,"critique","Blé + énergie. Réserves de change limitées. Alerte FAO"),
    ("TUN","Tunisie",        62,"élevé",  "Imports alimentaires + énergie. Déjà fragilisé"),
    ("MAR","Maroc",          55,"élevé",  "OCP phosphate menacé (soufre Gulf 45% mondial)"),
    ("DEU","Allemagne",      65,"élevé",  "Industrie lourde. GNL Qatar + engrais. Récession technique"),
    ("ITA","Italie",         63,"élevé",  "Très dépendant gaz. Récession technique confirmée"),
    ("NLD","Pays-Bas",       60,"élevé",  "Hub pétrole/gaz européen. Rotterdam impacté"),
    ("GBR","Royaume-Uni",    58,"élevé",  "Inflation >5% projetée. GNL + diesel sous tension"),
    ("FRA","France",         55,"élevé",  "GNL Qatar + engrais. Inflation +2-3 pts"),
    ("BEL","Belgique",       55,"élevé",  "Anvers hub. Chimie + fret sous tension"),
    ("HUN","Hongrie",        60,"élevé",  "Très dépendant énergie russe + Gulf. FMI: exposé"),
    ("TUR","Turquie",        60,"élevé",  "Énergie + engrais. FMI: second tier exposé"),
    ("GRC","Grèce",          55,"élevé",  "Armateurs grecs (VLCC) bénéficient / importateurs exposés"),
    ("ESP","Espagne",        48,"modéré", "Gaz Algérie + GNL. Moins exposé que N. Europe"),
    ("PRT","Portugal",       45,"modéré", "Gaz diversifié. Exposition modérée"),
    ("AUT","Autriche",       58,"élevé",  "Gaz dépendant + industrie chimique exposée"),
    ("USA","États-Unis",     30,"modéré", "2% pétrole via Hormuz. Engrais (+43%). Chimie bénéficie"),
    ("CAN","Canada",         18,"limité", "Exportateur net énergie. Peu exposé. Blé export bénéficie"),
    ("AUS","Australie",      22,"limité", "Exportateur LNG + minerai. Peu exposé côté import"),
    ("BRA","Brésil",         25,"limité", "Pré-sal pétrole. Exportateur. Engrais = préoccupation"),
    ("RUS","Russie",         12,"limité", "Exportateur énergie. Bénéficiaire indirect prix hauts"),
    ("NOR","Norvège",        12,"limité", "Exportateur LNG + pétrole. Bénéficiaire"),
    ("NGA","Nigéria",        18,"limité", "Exportateur pétrole. Revenus en hausse"),
    ("DZA","Algérie",        15,"limité", "Fournisseur alternatif gaz pour Europe (pipeline)"),
    ("ZAF","Afrique du Sud", 38,"modéré", "Imports pétrole + engrais. Détour Cap = surcoût fret"),
    ("MEX","Mexique",        25,"limité", "Pétrole + gaz domestiques. Exposition limitée"),
    ("ARG","Argentine",      28,"modéré", "Importateur énergie. Engrais phosphate (soufre)"),
    ("VNM","Vietnam",        65,"élevé",  "Textile + énergie. Supply chain polyester menacée"),
    ("BGD","Bangladesh",     90,"critique","2/3 GNL importé. Textile = 85% exports menacés"),
    ("NPL","Népal",          70,"élevé",  "Dépendant Inde (elle-même sous pression)"),
    ("CMB","Cambodge",       58,"élevé",  "Textile + énergie importée. MEG supply chain"),
]

# Dédupliquer sur l'ISO
seen = set()
VULN_CLEAN = []
for row in VULNERABILITY:
    if row[0] not in seen:
        seen.add(row[0])
        VULN_CLEAN.append(row)

# Mapping sévérité → score choropleth discret
SEV_SCORE = {"critique": 4, "élevé": 3, "modéré": 2, "limité": 1}
SEV_LABEL = {4: "Critique (70-98)", 3: "Élevé (50-70)", 2: "Modéré (25-50)", 1: "Limité (<25)"}

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES MODULE 1 — AIS / TRAFIC
# ══════════════════════════════════════════════════════════════════════════════

# Timeline du trafic (navires/jour, sources : EIA, Wikipedia, AIS publics)
AIS_TIMELINE = [
    ("2026-01-15", 138, "Normal · baseline 2025-2026"),
    ("2026-02-15", 138, "Normal · baseline"),
    ("2026-02-27", 135, "Dernier jour pré-fermeture"),
    ("2026-02-28",  80, "🚨 Fermeture effective — tirs sur navires commerciaux"),
    ("2026-03-01",  50, "Trafic chute brutalement"),
    ("2026-03-04",  18, "QatarEnergy déclare force majeure"),
    ("2026-03-05",  12, "EIA : détroit 'practically closed'"),
    ("2026-03-08",   8, "Brent atteint 126 $/bbl — record depuis 2022"),
    ("2026-03-10",   7, "Production Gulf réduite de 6,7 Mb/j (EIA)"),
    ("2026-03-12",   7, "Production réduite de 10 Mb/j"),
    ("2026-03-20",   6, "FMI revise croissance mondiale"),
    ("2026-04-01",   6, "EIA STEO : shut-in 9,1 Mb/j en avril"),
    ("2026-04-07",   7, "EIA STEO avr. 2026 publié"),
    ("2026-04-09",   6, "Cessez-le-feu US-Iran annoncé. Trafic reste nul"),
    ("2026-04-14",   7, "FMI : croissance mondiale 2,6% vs 2,9%"),
    ("2026-04-29",   6, f"Aujourd'hui · J+{DAYS_CLOSED}"),
]

# Types de navires baseline vs actuel
VESSEL_TYPES = [
    ("Tankers brut (VLCC/Suezmax)", 32, 1),
    ("Tankers produits",            15, 1),
    ("LNG carriers",                 6, 0),
    ("Vraquier / bulk (engrais)",    8, 0),
    ("Porte-conteneurs",            25, 2),
    ("Navires généraux / divers",   52, 3),
]

EVENTS = [
    ("28 fév. 2026", "🚨", "Fermeture effective",          "Tirs sur navires commerciaux. Trafic s'effondre"),
    ("4 mars 2026",  "⚡", "Force majeure QatarEnergy",    "100% exports GNL Qatar bloqués"),
    ("8 mars 2026",  "📈", "Brent 126 $/bbl",             "Plus haut depuis 4 ans. TTF gaz ×2 en 10 jours"),
    ("10 mars 2026", "🛢️", "Production -6,7 Mb/j",        "EIA : Gulf shut-in. Aramco réduit prod."),
    ("12 mars 2026", "🛢️", "Production -10 Mb/j",         "Quasi-totalité Gulf bloquée"),
    ("19 mars 2026", "🏦", "BCE bloque baisses taux",      "Inflation CPI Europe remonte vers 3%"),
    ("31 mars 2026", "📊", "Allianz Research",             "PIB Eurozone 2026 : +0,2% si >3 mois fermeture"),
    ("7 avr. 2026",  "📊", "EIA STEO publié",              "Brent pic Q2 115 $/bbl. Risk premium prolongé"),
    ("9 avr. 2026",  "🕊️", "Cessez-le-feu US-Iran",       "Annoncé. Trafic reste quasi nul (Standard Chartered)"),
    ("14 avr. 2026", "📊", "FMI révision mondiale",        "Croissance 2,6% vs 2,9% · Iran -6,1% · PIB mondial touché"),
    ("29 avr. 2026", "📍", f"Aujourd'hui J+{DAYS_CLOSED}", "6-7 navires/jour vs baseline 138. Détroit toujours fermé"),
]

# Points clés du détroit (pour carte zoom)
STRAIT_POINTS = [
    (26.56, 56.27, "🚫 Détroit d'Ormuz", "21 miles de large · 20% pétrole mondial · fermé depuis J+59"),
    (25.36, 56.35, "🏭 Fujairah (EAU)",  "Terminal pétrolier bypass · capacité ~1,5 Mb/j"),
    (27.13, 56.27, "🏭 Bandar Abbas (Iran)", "Port principal iranien · bloqué"),
    (26.2,  50.63, "🏭 Ras Tanura (Arabie)",  "Plus grand terminal export monde · 6 Mb/j normal"),
    (24.98, 55.10, "🏭 Jebel Ali (EAU)",    "Largest port M-O · fret ralenti"),
    (25.29, 51.53, "🏭 Ras Laffan (Qatar)", "Terminal GNL mondial · force majeure"),
    (29.97, 48.88, "🏭 Al Ahmadi (Koweït)", "Export terminal pétrole · bloqué"),
    (29.78, 48.62, "🏭 Basra (Irak)",       "Terminal Khor Al-Amaya · shut-in 2+ Mb/j"),
]

# Flux commerciaux (pour carte mondiale)
TRADE_FLOWS = [
    # label, from_lat, from_lon, to_lat, to_lon, couleur, dash, width, note
    ("→ Chine (pétrole + GNL)",  26.5, 56.3,  31.2, 121.5, "#ef4444", "solid", 3, "1/3 pétrole chinois"),
    ("→ Inde (pétrole)",         26.5, 56.3,  18.9,  72.8, "#f97316", "solid", 2, "60% pétrole indien"),
    ("→ Japon (pétrole + GNL)",  26.5, 56.3,  35.7, 139.7, "#ef4444", "solid", 2, "Quasi-100% dépendant"),
    ("→ Corée du Sud",           26.5, 56.3,  37.5, 127.0, "#f97316", "solid", 2, "Quasi-100% dépendant"),
    ("→ Singapour (hub)",        26.5, 56.3,   1.3, 103.8, "#f59e0b", "solid", 1, "Hub régional"),
    ("→ Europe (bloqué)",        26.5, 56.3,  51.9,   4.5, "#9ca3af", "dash",  2, "GNL Qatar bloqué"),
]

# Route de délestage Cap de Bonne-Espérance
CAPE_ROUTE_LATS = [26.5, 20, 12,  5, -5, -20, -35, -35, -20, -5,  5, 20, 35, 45, 51.9]
CAPE_ROUTE_LONS = [56.3, 58, 60, 65,  65,  50,  20,  18,  10,  5,  0, -5, -8, -5,  4.5]

# ══════════════════════════════════════════════════════════════════════════════
# MODULES 2, 3, 4 — DONNÉES (identiques à version précédente)
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
                 r2=["Industrie chimie/acier : surcharges +30%","Engrais azotés réduits","Fret renchérit → inflation"],
                 r3=["BCE reporte baisses taux (19 mars)","UK inflation projetée >5% 2026","Débat dépendance énergétique"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["2/3 du GNL importé bloqué","Gas = 50% élec. Bangla / 25% Pakistan","Stop quasi-total LNG spot"],
                 r2=["Coupures électriques industrielles","Textile Bangladesh : risque arrêts","Urée locale stoppée"],
                 r3=["Risque pénuries alimentaires","Instabilité sociale potentielle","Appels aide FAO/ONU"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["~2% conso pétrole via Hormuz","Urée Tampa : 475→680 $/t (+43%)","Prix pompe +30% (>4$/gal.)"],
                 r2=["Corn Belt à 75% engrais normaux","Substitution maïs→soja","Chimie USA (Dow) : full out"],
                 r3=["Pression politique sur Trump","SPR activé (IEA 400 Mbbl)","Débat Congrès sécurité"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Urée + phosphate bloqués","Soufre Gulf (45% mondial) arrêté","OCP Maroc : 3,7 Mt soufre menacées"],
                 r2=["Phosphate mondial réduit","Blé : Égypte/Sahel sous tension","Fret détourné → alim. monte"],
                 r3=["FAO : Bangladesh/Égypte/Sri Lanka rouges","Risque crise 2022-bis","Instabilité pays endettés"]),
        ],
        "mults": [
            dict(title="Soufre → phosphate → alimentation",
                 steps=["Soufre Gulf (45% mondial) bloqué","Acide sulfurique indisponible","OCP Maroc + Chine réduisent DAP/MAP","Phosphates raréfiés","Rendements blé/riz/maïs −10-25% (2026-27)"]),
            dict(title="GNL → urée → semis → prix alimentaires",
                 steps=["GNL Qatar (20% mondial) bloqué","Urée non synthétisable","Agriculteurs réduisent azote","Rendements −10 à −25%","Prix alim. +15-30% dès 2027"]),
            dict(title="Énergie → inflation → dette émergents",
                 steps=["Brent >100 $/bbl","Facture énergétique explose","Déficits budgétaires se creusent","FMI : 3,4 Mds pers. surexposés","Risques défauts souverains"]),
        ],
    },
    20: {
        "resume": "Fermeture ~80 jours. Stockage gaz Europe critique pour hiver 2026-27. Saison Kharif décidée sous contrainte. Récessions industrielles Europe confirmées.",
        "zones": [
            dict(flag="🇨🇳", label="Chine", sev="critique",
                 r1=["Réserves strat. en consommation","MEG : stocks sous seuil alerte","Méthanol : inventaires critiques"],
                 r2=["Chimie/plastiques −10-20%","Textile reconfiguré vers USA","Batteries EV : graphite +30%","Sidérurgie : pénurie DRI"],
                 r3=["Stimulus économique interne","Pression vers Russie/Kazakhstan","Signal indépendance énergétique"]),
            dict(flag="🇮🇳", label="Inde", sev="critique",
                 r1=["Kharif compromis (urée, DAP)","3 usines urée fermées","Raffineries sous tension (−40% crude)"],
                 r2=["Substitution légumineuses/céréales","Prix alim. domestiques +15-25%","Inflation +3-4 pts","Textile/polyester sous tension"],
                 r3=["Stocks alim. urgence mobilisés","Pression politique forte","Réorientation dip."]),
            dict(flag="🇪🇺", label="Europe", sev="élevé",
                 r1=["Refill gaz estival impossible","LNG USA/Australie saturé","Diesel : pénuries locales"],
                 r2=["Chimie/acier : réductions prod.","Engrais azotés réduits","CPI +2-3 pts","Récession technique imminente"],
                 r3=["BCE bloquée (stagflation)","Solidarité énergétique débattue","UK inflation >5%"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["Coupures électriques quotidiennes","Urée locale effondrée","Textile Bangladesh : arrêts"],
                 r2=["Exports textiles −30-40%","Sécurité alim. dégradée (Boro rice)","Chômage industriel massif"],
                 r3=["FAO : Bangladesh zone rouge","Instabilité sociale","Aide internationale urgente"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["Corn Belt engrais <75%","SPR activé partiellement","Diesel agri. +15-25% coûts"],
                 r2=["Substitution maïs→soja confirmée","Prix viande/lait hausse (lag)","Inflation alim. +2-3%"],
                 r3=["Pression tarifaire","Dow/CF Industries bénéficient","Débat food security"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Urée : 40-50% commerce mondial bloqué","OCP Maroc contraint (soufre)","Égypte : imports blé risqués"],
                 r2=["Saisons agri. 2026 irrémédiablement impactées","Prix alim. hausse","Sous-nutrition aggravée (PAM)"],
                 r3=["Instabilité politique N-Afrique","Crises gouvernance Sahel","Flux migratoires potentiels"]),
        ],
        "mults": [
            dict(title="MEG → textiles → emplois → stabilité sociale",
                 steps=["MEG Gulf (6,5 Mt/an) bloqué","Pénurie polyester/fibres","Bangladesh/Vietnam : arrêts usines","Millions emplois menacés","Instabilité sociale pays vulnérables"]),
            dict(title="Coke pétrole → graphite → batteries EV",
                 steps=["Raffineries Gulf sous-actives","Coke de pétrole raréfié","Graphite synthétique +30%","Coûts EV augmentent","Transition énergétique ralentie"]),
            dict(title="Inflation énergie → dette souveraine émergents",
                 steps=["Énergie +50-100% pays import.","Déficits commerciaux explosent","Devises chutent vs USD","Taux dette extérieure montent","FMI : 3,4 Mds surexposés"]),
        ],
    },
    50: {
        "resume": "Fermeture ~110 jours. Crise alimentaire mondiale 2027 confirmée. Récessions multiples. Commerce mondial −2 pts. Crises humanitaires. Recompositions géopolitiques.",
        "zones": [
            dict(flag="🇨🇳", label="Chine", sev="critique",
                 r1=["Réserves insuffisantes (>2 mois)","Imports via Cap : +7-10j, +20-30% coût","MEG : chaîne textile restructurée"],
                 r2=["PIB 2026 : −1 à −2 pts","Chimie −15-25%","Chômage industriel localisé","EV : coûts structurellement élevés"],
                 r3=["Récession industrielle partielle","ENR : investissements massifs","Recomposition alliances énergie","Signal indépendance durable"]),
            dict(flag="🇮🇳", label="Inde", sev="critique",
                 r1=["Kharif 2026 : rendements −10 à −20%","Production industrielle −8-12%","Exports riz −25% → cascade mondiale"],
                 r2=["Inflation alim. domestique +20-30%","Pauvreté alim. aggravée (millions)","Textile : pertes emplois structurelles","PIB : −1,5 à −2,5% (FMI)"],
                 r3=["Tensions soc./politiques majeures","Soutien FMI possible","Réorientation dip. durable"]),
            dict(flag="🇪🇺", label="Europe", sev="élevé",
                 r1=["Stockage gaz hiver 2026-27 : <50%","Risque délestages industriels hiver","TTF structurellement >50 €/MWh"],
                 r2=["Récession technique All./Italie/Pays-Bas","Industrie lourde −20-30%","CPI zone euro +3-4 pts","Chômage industriel +0,5-1%"],
                 r3=["BCE : stagflation, politique paralysée","Crise politique pays exposés","LNG USA/ENR accélérée"]),
            dict(flag="🌏", label="Bangladesh & Pakistan", sev="critique",
                 r1=["Électricité : rationnement sévère","Textile Bangladesh −50-70% exports","Récolte Boro sous-fertilisée"],
                 r2=["Crise humanitaire potentielle","Malnutrition aggravée (millions)","Exode économique"],
                 r3=["Instabilité gouvernementale","Intervention humanitaire internationale","Crises monétaires taka/roupie"]),
            dict(flag="🇺🇸", label="États-Unis", sev="modéré",
                 r1=["SPR quasi-épuisé (~120 jours)","Maïs 2026 : récolte réduite","Diesel agri. : impact structurel"],
                 r2=["Inflation alim. +4-6% sur 12m","Prix viande/lait +8-12%","PIB US : −0,5 à −1%"],
                 r3=["Pression politique majeure","Producteurs locaux renforcés durablement","Chimie US : self-sufficiency accélérée"]),
            dict(flag="🌍", label="Afrique & M-O", sev="élevé",
                 r1=["Saisons agri. 2026 sous-fertilisées","OCP Maroc production réduite","Pays Gulf : économies dévastées"],
                 r2=["Crise alim. régionale : −15-30% rendements","Prix alim. mondiaux +15-20% (FAO)","Exports agri. mondiaux réduits"],
                 r3=["Instabilité politique Égypte/Tunisie/Sahel","Crise dette pays importateurs","Flux migratoires accrus vers Europe"]),
        ],
        "mults": [
            dict(title="Méga-chaîne alimentaire (6 niveaux)",
                 steps=["GNL bloqué","Urée non produite","Soufre bloqué → phosphate indisponible","Agriculteurs réduisent doses","Rendements −10 à −25%","Prix alim. +15-30% · crise 2027"]),
            dict(title="Énergie → stagflation structurelle",
                 steps=["Pétrole >100$/bbl 50+ jours","Inflation mondiale +2-4 pts","Banques centrales paralysées","Taux hauts → crédit cher","PIB global 2,6% (CNUCED)","Défauts souverains émergents"]),
            dict(title="Crise fossile → transition paradoxale",
                 steps=["Coke pétrole raréfié → graphite +30%","EV coûts augmentent court terme","ENR budgets ×2 (signal politique)","Crise fossile accélère transition","Reconfigurations géopolitiques durables"]),
        ],
    },
}

INSTRUMENTS = {
    "🛢️ Énergie": [
        dict(label="Brent Crude",          ticker="BZ=F",    unit="$/bbl",   bl=73.5,   thr=30,  note="Pic observé 126$/bbl (8 mars 2026)"),
        dict(label="WTI Crude",            ticker="CL=F",    unit="$/bbl",   bl=70.5,   thr=30,  note="Référence USA"),
        dict(label="Gaz naturel US",       ticker="NG=F",    unit="$/MMBtu", bl=3.5,    thr=50,  note="Proxy Henry Hub (TTF Europe non dispo gratuit)"),
        dict(label="Gazoline RBOB",        ticker="RB=F",    unit="$/gal",   bl=2.20,   thr=30,  note="+30% observé mars 2026"),
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
        dict(label="DHT Holdings (VLCC)",  ticker="DHT",     unit="USD",     bl=10.2,   thr=40,  note="Tankers VLCC — proxy taux fret pétrolier"),
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

PROJ = {
    5: {
        "color": "#22c55e", "label": "Réouverture J+5",
        "resume": "Réouverture rapide. Choc absorbé progressivement. Effets agricoles partiellement irréversibles. Hiver 2026-27 gérable.",
        "kpis": [
            ("Brent H+6m","~85 $/bbl","modéré"),     ("Brent H+12m","~78 $/bbl","limité"),
            ("Urée H+6m","+25-35%","élevé"),          ("FAO alim H+6m","+8-12%","modéré"),
            ("CPI Euro H+6m","~3%","modéré"),          ("PIB Euro 2026","+0.5-0.8%","modéré"),
            ("Commerce 2026","+2-2.5%","modéré"),      ("Crise alim.","Limitée","limité"),
        ],
        "cascade": {"Énergie":"Brent →85$/bbl. TTF correction progressive.","Engrais":"Urée +35% résiduel. Semis 2026 impactés.","Alim.":"FAO +8-12%. Maïs sous tension.","Macro":"VIX retombe. BCE reprend H2 2026."},
        "sectors": {
            "Énergie":      [("Brent crude","~85 $/bbl","~78 $/bbl","modéré","EIA : risk premium résiduel ~10$. Allianz : 78$/bbl fin 2026"),("Gaz Europe TTF","~35-40 €/MWh","~30-35 €/MWh","modéré","Refill possible. Stockage ~55-60%"),("Production Gulf","-3 Mb/j résid.","~pré-conflit","modéré","EIA : retour progressif")],
            "Alimentation": [("Urée prix","+25-35%","+5-10% résid.","élevé","Semis 2026 déjà décidés — irréversible"),("Maïs CBOT","+10-15%","+3-5% résid.","modéré","Récolte 2027 normale si engrais ok"),("FAO Index","+8-12%","+3-5% résid.","modéré","Normalisation attendue 2027")],
            "Industrie":    [("MEG polyester","Tension résid.","Normalisé","modéré","Chine réapprovisionne via USA"),("Aluminium","+8-12%","+3-5% résid.","modéré","Surcharges réduites"),("Fret maritime","+15-25% résid.","Normalisé","modéré","VLCC taux normalisent")],
            "Macro":        [("PIB Eurozone","+0.5-0.8% 2026","+0.8-1.2% 2027","modéré","Allianz : +0.2% si >3 mois. J+5 = évité"),("CPI Eurozone","~2.8-3%","~2.2-2.5%","modéré","Inflation résorbée H2 2026"),("Commerce mondial","+2-2.5%","+3-3.5%","modéré","CNUCED : haut de fourchette")],
            "Géopolitique": [("ENR investissement","Accélération","+20-30% budgets","positif","Signal fort. Budgets ENR revus Europe/Asie"),("LNG USA→Europe","Contrats durables","Contrats 10-20 ans","positif","Diversification structurelle"),("Marchés émergents","Stress financier","Récupération lente","modéré","FMI assistance. Risques contenus")],
        },
    },
    20: {
        "color": "#f59e0b", "label": "Réouverture J+20",
        "resume": "Fermeture totale ~80 jours. Stockage gaz Europe critique. Kharif décidé sous contrainte. Récessions industrielles Europe confirmées.",
        "kpis": [
            ("Brent H+6m","~95-105 $/bbl","élevé"),  ("Brent H+12m","~85-95 $/bbl","élevé"),
            ("Urée H+6m","+50-60%","critique"),        ("FAO alim H+6m","+15-25%","élevé"),
            ("CPI Euro H+6m","~3.5-4%","élevé"),       ("PIB Euro 2026","+0.1-0.3%","critique"),
            ("Commerce 2026","+1.5-2%","élevé"),       ("Crise alim.","Confirmée","critique"),
        ],
        "cascade": {"Énergie":"Refill gaz Europe <40%. Hiver 2026-27 à risque.","Engrais":"Cascade soufre→phosphate irréversible.","Alim.":"Prix +10-20% à 6 mois. FAO alerte.","Macro":"Récession All./Italie. BCE bloquée."},
        "sectors": {
            "Énergie":      [("Brent crude","~95-105 $/bbl","~85-95 $/bbl","élevé","Goldman : >100$ si fermeture >1 mois"),("Gaz Europe TTF","~50-60 €/MWh","~40-50 €/MWh","critique","Hiver 2026-27 sous tension"),("Production Gulf","-7-9 Mb/j résid.","-2-3 Mb/j résid.","critique","EIA : shut-in 9.1 Mb/j avril 2026")],
            "Alimentation": [("Urée prix","+50-60%","+20-30% résid.","critique","Saison agri. 2026 compromise"),("Maïs CBOT","+20-25%","+10-15% résid.","élevé","Corn Belt récolte réduite"),("FAO Index","+15-25%","+10-15%","élevé","FAO : escalade signif. au-delà 2026")],
            "Industrie":    [("MEG polyester","Pénurie aiguë","+10-15% résid.","critique","Inventaires Chine sous seuil alerte"),("Aluminium","+15-20%","+8-12% résid.","élevé","Surcharges +30% maintenues"),("Textile Bangladesh","-30-40% export","-10-15% résid.","critique","Millions emplois menacés")],
            "Macro":        [("PIB Eurozone","+0.1-0.3% 2026","~0.5% 2027","critique","Allianz : récession technique All./Italie"),("CPI Eurozone","~3.5-4%","~3-3.5%","élevé","UK >5%. Zone euro >3%"),("Commerce mondial","+1.5-2%","+2-2.5%","élevé","CNUCED : bas de fourchette")],
            "Géopolitique": [("Bangladesh/Pak","Crise sociale","Transition difficile","critique","Électricité rationnée. Textile en crise"),("Égypte/Sahel","Alerte FAO","Crise alimentaire","critique","Réserves blé épuisées"),("ENR","Accélération forte","Rupture structurelle","positif","Budgets ENR +30-50%")],
        },
    },
    50: {
        "color": "#ef4444", "label": "Réouverture J+50",
        "resume": "Fermeture totale ~110 jours. Crise alimentaire mondiale 2027 confirmée. Récessions multiples. Commerce −2 pts. Crises humanitaires.",
        "kpis": [
            ("Brent H+6m","~105-115 $/bbl","critique"), ("Brent H+12m","~90-100 $/bbl","élevé"),
            ("Urée H+6m","+60-70%","critique"),           ("FAO alim H+6m","+25-35%","critique"),
            ("CPI Euro H+6m","~4-5%","critique"),          ("PIB Euro 2026","−0.2 à +0.1%","critique"),
            ("Commerce 2026","+1.5%","critique"),          ("Crise alim.","Mondiale 2027","critique"),
        ],
        "cascade": {"Énergie":"Réserves épuisées. Délestages industriels hiver Europe.","Engrais":"Récoltes 2026 −10-25%. Urée +70%.","Alim.":"FAO : crise 2027. Bangladesh/Pakistan/Égypte rouges.","Macro":"Stagflation mondiale. PIB −1%. 3,4 Mds à risque."},
        "sectors": {
            "Énergie":      [("Brent crude","~105-115 $/bbl","~90-100 $/bbl","critique","EIA STEO : pic Q2 115$/bbl. Risk premium prolongé"),("Gaz Europe TTF","~60-70 €/MWh","~45-55 €/MWh","critique","Hiver 2026-27 : rationnement industrie"),("Production Gulf","-9-10 Mb/j","-2-4 Mb/j résid.","critique","Standard Chartered : 8 Mb/j retirés")],
            "Alimentation": [("Urée prix","+60-70%","+30-40% résid.","critique","FAO : 3 mois = seuil critique planting"),("Maïs CBOT","+25-30%","+15-20% résid.","critique","Corn Belt −15-20% rendement 2026"),("FAO Index","+25-35%","+20-25%","critique","Proche 2022 mais système plus fragile")],
            "Industrie":    [("MEG polyester","Rupture supply","+15-20% résid.","critique","Inventaires Chine à zéro"),("Aluminium","+20-30%","+10-15% résid.","critique","Fermetures usines Europe confirmées"),("Sidérurgie","-15-20% prod.","-5-8% résid.","critique","DRI/pellets Gulf bloqués")],
            "Macro":        [("PIB Eurozone","−0.2 à +0.1%","~0.2-0.5% 2027","critique","Allianz : récession technique si >3 mois"),("CPI Eurozone","~4-5%","~3.5-4% 2027","critique","Stagflation. BCE impuissante"),("Commerce mondial","+1.5%","+2-2.5% 2027","critique","CNUCED : plus bas fourchette 2026")],
            "Géopolitique": [("Crises humanitaires","Bangla/Pak/Égypte","Crise 2027","critique","FAO/PAM : 'perfect storm'"),("Marchés émergents","Défauts souverains","Restructurations","critique","FMI : 3,4 Mds surexposés"),("Ordre énergétique","Recomposition","Nouvel ordre","élevé","ENR +50%. Fossile remis en cause")],
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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
    if v is None: return "N/A"
    if abs(v) >= 1000: return f"{v:,.0f} {unit}".strip()
    if abs(v) >= 100:  return f"{v:.1f} {unit}".strip()
    return f"{v:.2f} {unit}".strip()

def indexed_chart(series_map, reopen_d, scen_color, scen_lbl):
    palette = ["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6"]
    fig = go.Figure()
    for i, (lbl, s) in enumerate(series_map.items()):
        if s.empty: continue
        pos = s.index.searchsorted(pd.Timestamp(CLOSURE_DATE))
        ref = float(s.iloc[max(0, pos-1)]) if pos > 0 else float(s.iloc[0])
        if ref == 0: continue
        norm = s / ref * 100.0
        fig.add_trace(go.Scatter(x=norm.index, y=norm.values.tolist(), name=lbl, mode="lines",
                                 line=dict(width=1.8, color=palette[i % len(palette)])))
    fig.add_hline(y=100, line=dict(dash="dot", color="#9ca3af", width=0.8))
    for xs, lbl, col in [
        (CLOSURE_DATE.strftime("%Y-%m-%d"), "Fermeture", "#ef4444"),
        (reopen_d.strftime("%Y-%m-%d"),     scen_lbl,   scen_color),
    ]:
        fig.add_vline(x=xs, line=dict(dash="dash", color=col, width=1.1))
        fig.add_annotation(x=xs, y=1, xref="x", yref="paper", text=lbl, showarrow=False,
                           font=dict(size=9, color=col), xanchor="left", yanchor="top",
                           bgcolor="white", opacity=0.85)
    fig.update_layout(height=300, title=dict(text="Indexé base 100 = fermeture (28 fév. 2026)", font_size=11),
                      margin=dict(t=36, b=70, l=36, r=12), plot_bgcolor="white", paper_bgcolor="white",
                      xaxis=dict(showgrid=True, gridcolor="#f3f4f6", tickformat="%d %b"),
                      yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Index"),
                      legend=dict(orientation="h", y=-0.38, font_size=10), hovermode="x unified")
    return fig

def make_gantt(scen_days):
    reopen = TODAY + timedelta(days=scen_days)
    effects = [
        ("Énergie",      "Brent correction",       0,   60,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Énergie",      "TTF gaz Europe",          0,  120,  "modéré"  if scen_days<=5 else "critique"),
        ("Énergie",      "Production Gulf",         0,  180,  "élevé"   if scen_days<=5 else "critique"),
        ("Alimentation", "Urée correction prix",    0,   90,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Alimentation", "Impact récolte 2026",    30,  120,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Alimentation", "Crise alimentaire 2027",120,  180,  "limité"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Industrie",    "MEG / méthanol",          0,   60,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Industrie",    "Fret maritime",            0,   90,  "modéré"  if scen_days<=5 else "élevé"),
        ("Industrie",    "Textile Bangladesh",      30,  120,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Macro",        "Inflation CPI",            0,  180,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Macro",        "PIB Eurozone",            30,  270,  "modéré"  if scen_days<=5 else "critique"),
        ("Macro",        "Marchés émergents",        0,  270,  "élevé"   if scen_days<=5 else "critique"),
        ("Géopolitique", "ENR accélération",         0,  365,  "positif"),
        ("Géopolitique", "Crises humanitaires",     60,  300,  "modéré"  if scen_days<=5 else "élevé"   if scen_days<=20 else "critique"),
        ("Géopolitique", "Recomposition alliances", 60,  365,  "élevé"),
    ]
    rows = []
    for sector, effect, offset, duration, sev in effects:
        sd = reopen + timedelta(days=offset)
        ed = min(sd + timedelta(days=duration), H12 + timedelta(days=30))
        rows.append(dict(label=f"{sector} · {effect}",
                         start=sd.strftime("%Y-%m-%d"),
                         end=ed.strftime("%Y-%m-%d"),
                         color=SEV_COLOR.get(sev, "#9ca3af")))
    return rows

def gantt_chart(rows, scen_color, scen_lbl):
    fig = go.Figure()
    for row in rows:
        fig.add_trace(go.Bar(
            x=[row["end"]], base=[row["start"]], y=[row["label"]],
            orientation="h", marker_color=row["color"], marker_opacity=0.78,
            showlegend=False,
            hovertemplate=f"<b>{row['label']}</b><br>{row['start']} → {row['end']}<extra></extra>",
        ))
    today_s = TODAY.strftime("%Y-%m-%d")
    h6_s    = H6.strftime("%Y-%m-%d")
    h12_s   = H12.strftime("%Y-%m-%d")
    for xs, lbl, col in [(today_s,"Aujourd'hui","#6b7280"),(h6_s,"H+6m","#3b82f6"),(h12_s,"H+12m","#8b5cf6")]:
        fig.add_vline(x=xs, line=dict(dash="dash", color=col, width=1.1))
        fig.add_annotation(x=xs, y=1, xref="x", yref="paper", text=lbl, showarrow=False,
                           font=dict(size=9, color=col), xanchor="left", yanchor="top",
                           bgcolor="white", opacity=0.85)
    fig.update_layout(height=440, margin=dict(t=24, b=20, l=215, r=20),
                      plot_bgcolor="white", paper_bgcolor="white", barmode="overlay",
                      xaxis=dict(type="date", showgrid=True, gridcolor="#f3f4f6", tickformat="%b %Y",
                                 range=[TODAY.strftime("%Y-%m-%d"), (H12+timedelta(days=30)).strftime("%Y-%m-%d")]),
                      yaxis=dict(showgrid=False, tickfont=dict(size=10), autorange="reversed"),
                      hovermode="closest")
    return fig

def risk_chart(scen_days):
    zones = ["Chine","Inde","Europe","Bangladesh/Pak","USA","Afrique/M-O"]
    s6  = {5:[55,65,50,75,35,60], 20:[70,80,65,90,45,75], 50:[85,90,80,95,55,85]}[scen_days]
    s12 = {5:[35,45,30,55,20,40], 20:[55,65,50,80,35,65], 50:[70,80,65,90,45,80]}[scen_days]
    def c(s): return "#ef4444" if s>=80 else "#f97316" if s>=65 else "#eab308" if s>=45 else "#22c55e"
    fig = go.Figure()
    for i,(z,a,b) in enumerate(zip(zones,s6,s12)):
        fig.add_trace(go.Bar(name="6 mois",  x=[a], y=[z], orientation="h",
                             marker_color=c(a), opacity=0.85, showlegend=(i==0),
                             hovertemplate=f"{z}<br>H+6m : {a}/100<extra></extra>"))
        fig.add_trace(go.Bar(name="12 mois", x=[b], y=[z], orientation="h",
                             marker_color=c(b), opacity=0.45, showlegend=(i==0),
                             hovertemplate=f"{z}<br>H+12m : {b}/100<extra></extra>"))
    fig.update_layout(barmode="group", height=280, margin=dict(t=16,b=20,l=120,r=50),
                      plot_bgcolor="white", paper_bgcolor="white",
                      xaxis=dict(range=[0,100], title="Score risque /100", showgrid=True, gridcolor="#f3f4f6"),
                      yaxis=dict(showgrid=False), legend=dict(orientation="h", y=-0.22, font_size=10))
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🛢️ HORMUZ WATCH")
    st.error(f"🚫 Fermé depuis J+{DAYS_CLOSED} jours\n28 fév. 2026")
    st.markdown("---")
    module = st.radio("Module", [
        "🏠 Accueil — Carte de crise",
        "🚢 Module 1 — Observatoire AIS",
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
    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Màj {datetime.now().strftime('%d/%m %H:%M')}")


# ══════════════════════════════════════════════════════════════════════════════
# 🏠 PAGE D'ACCUEIL — CARTE DE CRISE
# ══════════════════════════════════════════════════════════════════════════════
if module.startswith("🏠"):
    st.title("🌍 Carte de crise — Fermeture du détroit d'Ormuz")
    st.caption(f"J+{DAYS_CLOSED} de fermeture · 28 fév. 2026 → aujourd'hui · Zones critiques et flux commerciaux bloqués")

    # ── KPIs ──
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Jours fermés",      f"J+{DAYS_CLOSED}",    "Depuis 28 fév. 2026")
    k2.metric("Trafic détroit",    "6-7 navires/j",       "−95% vs baseline 138")
    k3.metric("Pétrole bloqué",    "~8 Mb/j",             "Standard Chartered")
    k4.metric("Brent (pic)",       "126 $/bbl",           "+72% vs J0 (73,5$)")
    k5.metric("Personnes exposées","3,4 Mds",             "CNUCED — dette > santé")

    st.markdown("---")

    # ── CARTE MONDIALE ──
    df_vuln = pd.DataFrame(VULN_CLEAN, columns=["iso","name","score","sev","detail"])
    df_vuln["sev_score"] = df_vuln["sev"].map(SEV_SCORE)
    df_vuln["hover"] = df_vuln.apply(
        lambda r: f"<b>{r['name']}</b><br>Vulnérabilité : <b>{r['sev'].upper()}</b> ({r['score']}/100)<br>{r['detail']}", axis=1
    )

    # Choropleth
    fig_world = go.Figure()

    # Fond choropleth (vulnérabilité)
    fig_world.add_trace(go.Choropleth(
        locations=df_vuln["iso"],
        z=df_vuln["score"],
        text=df_vuln["hover"],
        hovertemplate="%{text}<extra></extra>",
        colorscale=[
            [0.0,  "#dcfce7"],   # limité — vert clair
            [0.25, "#fef9c3"],   # modéré — jaune clair
            [0.50, "#fed7aa"],   # élevé  — orange clair
            [0.75, "#fecaca"],   # critique-bord — rose
            [1.0,  "#ef4444"],   # critique — rouge
        ],
        zmin=0, zmax=100,
        colorbar=dict(
            title=dict(text="Vulnérabilité<br>(/100)", font_size=11),
            thickness=12, len=0.6, x=1.01,
            tickvals=[10, 30, 55, 80, 95],
            ticktext=["Limité", "Modéré", "Élevé", "Critique", "Extrême"],
        ),
        showscale=True,
        marker_line_color="white",
        marker_line_width=0.4,
        name="Vulnérabilité",
    ))

    # Flux commerciaux normaux (lignes)
    for label, flat, flon, tlat, tlon, color, dash, width, note in TRADE_FLOWS:
        fig_world.add_trace(go.Scattergeo(
            lat=[flat, tlat], lon=[flon, tlon],
            mode="lines",
            line=dict(width=width, color=color,
                      dash="dot" if dash == "dash" else "solid"),
            opacity=0.55 if dash == "dash" else 0.8,
            name=label,
            hovertemplate=f"<b>{label}</b><br>{note}<extra></extra>",
            showlegend=False,
        ))

    # Route de délestage Cap de Bonne-Espérance (tirets orange)
    fig_world.add_trace(go.Scattergeo(
        lat=CAPE_ROUTE_LATS, lon=CAPE_ROUTE_LONS,
        mode="lines",
        line=dict(width=2, color="#f59e0b", dash="dash"),
        opacity=0.7,
        name="Route via Cap (détour actuel)",
        hovertemplate="<b>Route de délestage</b><br>Cap de Bonne-Espérance<br>+7-10 jours · +20-30% coût fret<extra></extra>",
        showlegend=True,
    ))

    # Marqueur Détroit d'Ormuz
    fig_world.add_trace(go.Scattergeo(
        lat=[26.5], lon=[56.3],
        mode="markers+text",
        marker=dict(size=18, color="#ef4444", symbol="star",
                    line=dict(color="white", width=1.5)),
        text=["🚫 Ormuz"],
        textposition="top center",
        textfont=dict(size=11, color="#ef4444"),
        name="Détroit d'Ormuz (fermé)",
        hovertemplate="<b>🚫 Détroit d'Ormuz</b><br>Fermé depuis J+" + str(DAYS_CLOSED) + " jours<br>21 miles de large · 20% pétrole mondial<extra></extra>",
        showlegend=True,
    ))

    # Points capitales/villes clés
    key_cities = [
        (31.2, 121.5, "Shanghai"),  (18.9, 72.8, "Mumbai"),
        (35.7, 139.7, "Tokyo"),     (51.9,   4.5, "Rotterdam"),
        (1.3,  103.8, "Singapour"), (23.7, 90.4, "Dhaka"),
        (33.7, 73.1, "Islamabad"),  (30.0, 31.2, "Le Caire"),
    ]
    fig_world.add_trace(go.Scattergeo(
        lat=[c[0] for c in key_cities],
        lon=[c[1] for c in key_cities],
        mode="markers+text",
        marker=dict(size=6, color="#1e293b", symbol="circle"),
        text=[c[2] for c in key_cities],
        textposition="top right",
        textfont=dict(size=9, color="#1e293b"),
        name="Villes clés",
        showlegend=False,
        hovertemplate="<b>%{text}</b><extra></extra>",
    ))

    fig_world.update_geos(
        projection_type="natural earth",
        showland=True,     landcolor="#f8fafc",
        showocean=True,    oceancolor="#eff6ff",
        showcoastlines=True, coastlinecolor="#cbd5e1",
        showframe=False,
        showlakes=True,   lakecolor="#eff6ff",
        showcountries=True, countrycolor="#e2e8f0",
    )
    fig_world.update_layout(
        height=520,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white",
        legend=dict(
            orientation="h", y=-0.06, x=0.0,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#e2e8f0", borderwidth=1,
            font_size=10,
        ),
    )
    st.plotly_chart(fig_world, use_container_width=True)

    # ── LÉGENDE VULNÉRABILITÉ ──
    st.markdown("**Niveaux de vulnérabilité**")
    leg = st.columns(4)
    for col, (sev, hex_c) in zip(leg, [("critique","#ef4444"),("élevé","#f97316"),("modéré","#eab308"),("limité","#22c55e")]):
        n = sum(1 for r in VULN_CLEAN if r[3] == sev)
        col.markdown(
            f'<div style="background:{hex_c}22;border-left:4px solid {hex_c};'
            f'padding:6px 10px;border-radius:4px;font-size:12px">'
            f'<b>{sev.capitalize()}</b> · {n} pays</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── ZOOM GOLFE PERSIQUE ──
    st.subheader("Zoom — Golfe Persique & Détroit d'Ormuz")
    fig_gulf = go.Figure()

    # Fond géographique
    fig_gulf.add_trace(go.Scattergeo(
        lat=[p[0] for p in STRAIT_POINTS],
        lon=[p[1] for p in STRAIT_POINTS],
        mode="markers+text",
        marker=dict(
            size=[20, 12, 12, 12, 12, 12, 12, 12],
            color=["#ef4444","#3b82f6","#6b7280","#f59e0b","#3b82f6","#f97316","#6b7280","#6b7280"],
            symbol=["star","square","square","square","square","square","square","square"],
            line=dict(color="white", width=1),
        ),
        text=[p[2] for p in STRAIT_POINTS],
        textposition="top right",
        textfont=dict(size=10),
        hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
        customdata=[p[3] for p in STRAIT_POINTS],
        name="Infrastructures clés",
    ))

    fig_gulf.update_geos(
        center=dict(lat=26.5, lon=53.0),
        projection_scale=5,
        showland=True, landcolor="#f1f5f9",
        showocean=True, oceancolor="#dbeafe",
        showcoastlines=True, coastlinecolor="#94a3b8",
        showcountries=True, countrycolor="#cbd5e1",
        showframe=False,
    )
    fig_gulf.update_layout(
        height=380,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white",
        showlegend=False,
    )
    col_map, col_info = st.columns([2, 1])
    with col_map:
        st.plotly_chart(fig_gulf, use_container_width=True)
    with col_info:
        st.markdown("**Chiffres clés du détroit**")
        facts = [
            ("Largeur minimale",  "21 miles nautiques"),
            ("Trafic pré-crise",  "~138 navires/jour"),
            ("Trafic actuel",     f"~6-7 navires/jour"),
            ("Pétrole bloqué",    "~8 Mb/j (EIA)"),
            ("GNL bloqué",        "~19% du commerce mondial"),
            ("Engrais bloqués",   "~30% du commerce mondial"),
            ("Valeur quotidienne","~1,2 Mds$ pétrole seul"),
            ("Alternative pétrole","3,5-5,5 Mb/j (pipeline)"),
            ("Alternative GNL",   "Aucune"),
        ]
        for label, val in facts:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:5px 0;border-bottom:1px solid #f1f5f9;font-size:12px">'
                f'<span style="color:#6b7280">{label}</span>'
                f'<span style="font-weight:500">{val}</span></div>',
                unsafe_allow_html=True,
            )

    # ── TOP 10 PAYS CRITIQUES ──
    st.markdown("---")
    st.subheader("Top pays les plus exposés")
    top_countries = sorted(VULN_CLEAN, key=lambda x: x[2], reverse=True)[:12]
    cols_c = st.columns(4)
    for i, (iso, name, score, sev, detail) in enumerate(top_countries):
        c_hex = SEV_COLOR.get(sev, "#9ca3af")
        cols_c[i % 4].markdown(
            f'<div style="background:{c_hex}15;border:1px solid {c_hex}44;'
            f'border-radius:8px;padding:8px 10px;margin:4px 0;font-size:11px">'
            f'<div style="font-weight:600;font-size:13px">{name} <span style="color:{c_hex}">{score}/100</span></div>'
            f'<div style="color:#6b7280;margin-top:2px">{detail[:70]}…</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.caption(
        "Sources : EIA STEO avr. 2026 · Standard Chartered · CNUCED · FMI avr. 2026 · FAO mars 2026 · "
        "Wikipedia Economic impact 2026 Iran war · Allianz Research mars 2026"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 🚢 MODULE 1 — OBSERVATOIRE AIS
# ══════════════════════════════════════════════════════════════════════════════
elif module.startswith("🚢"):
    st.title("🚢 Module 1 — Observatoire du trafic maritime")
    st.caption("Suivi AIS · proxys indirects · timeline de crise · sources : EIA, Wikipedia, IMF PortWatch, AIS publics")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Navires/jour actuels",    "~6-7",            f"−95% vs baseline (138)")
    k2.metric("Tankers pétrole",         "~0-1/jour",       "vs 32/jour baseline")
    k3.metric("LNG carriers",            "0/jour",          "vs 6/jour baseline — arrêt total")
    k4.metric("Jours de fermeture",      f"J+{DAYS_CLOSED}","depuis 28 fév. 2026")

    st.markdown("---")

    # ── TIMELINE TRAFIC ──
    st.subheader("Évolution du trafic (navires/jour)")
    df_ais = pd.DataFrame(AIS_TIMELINE, columns=["date", "ships", "note"])
    df_ais["date"] = pd.to_datetime(df_ais["date"])

    fig_ais = go.Figure()
    fig_ais.add_trace(go.Scatter(
        x=df_ais["date"], y=df_ais["ships"],
        mode="lines+markers",
        line=dict(width=2.5, color="#3b82f6"),
        marker=dict(size=7, color=["#ef4444" if s <= 10 else "#f59e0b" if s <= 50 else "#22c55e"
                                    for s in df_ais["ships"]]),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>%{y} navires/jour<br>%{customdata}<extra></extra>",
        customdata=df_ais["note"],
        name="Navires/jour",
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
    ))
    # Ligne baseline
    fig_ais.add_hline(y=138, line=dict(dash="dot", color="#22c55e", width=1.2),
                      annotation_text="Baseline 138/j", annotation_font_size=10,
                      annotation_position="right")
    # Fermeture
    closure_s = CLOSURE_DATE.strftime("%Y-%m-%d")
    fig_ais.add_vline(x=closure_s, line=dict(dash="dash", color="#ef4444", width=1.5))
    fig_ais.add_annotation(x=closure_s, y=80, xref="x", yref="y",
                           text="🚨 Fermeture", showarrow=True, arrowhead=2,
                           font=dict(size=10, color="#ef4444"),
                           arrowcolor="#ef4444", ax=30, ay=-30)
    # Cessez-le-feu
    ceasfire_s = "2026-04-09"
    fig_ais.add_vline(x=ceasfire_s, line=dict(dash="dash", color="#f59e0b", width=1.2))
    fig_ais.add_annotation(x=ceasfire_s, y=40, xref="x", yref="y",
                           text="🕊️ Cessez-le-feu (trafic reste nul)", showarrow=True,
                           font=dict(size=9, color="#f59e0b"), arrowcolor="#f59e0b", ax=40, ay=-20)
    fig_ais.update_layout(
        height=320, margin=dict(t=24, b=40, l=50, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6", tickformat="%d %b"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Navires/jour", range=[0, 160]),
        hovermode="x unified",
    )
    st.plotly_chart(fig_ais, use_container_width=True)

    st.markdown("---")

    # ── BREAKDOWN PAR TYPE ──
    col_type, col_events = st.columns([1, 1])

    with col_type:
        st.subheader("Trafic par type de navire")
        df_vessels = pd.DataFrame(VESSEL_TYPES, columns=["type", "baseline", "actuel"])
        fig_vessels = go.Figure()
        fig_vessels.add_trace(go.Bar(
            name="Baseline (2025-2026)",
            x=df_vessels["type"], y=df_vessels["baseline"],
            marker_color="#93c5fd", opacity=0.85,
        ))
        fig_vessels.add_trace(go.Bar(
            name="Actuel (avril 2026)",
            x=df_vessels["type"], y=df_vessels["actuel"],
            marker_color="#ef4444", opacity=0.85,
        ))
        fig_vessels.update_layout(
            barmode="group", height=300,
            margin=dict(t=16, b=80, l=40, r=10),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(tickangle=-25, tickfont=dict(size=10)),
            yaxis=dict(title="Navires/jour", showgrid=True, gridcolor="#f3f4f6"),
            legend=dict(orientation="h", y=-0.35, font_size=10),
        )
        st.plotly_chart(fig_vessels, use_container_width=True)

    with col_events:
        st.subheader("Journal des événements clés")
        for date_str, icon, title, desc in EVENTS:
            st.markdown(
                f'<div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid #f1f5f9">'
                f'<span style="font-size:16px;min-width:24px">{icon}</span>'
                f'<div><div style="font-size:11px;color:#6b7280">{date_str}</div>'
                f'<div style="font-size:12px;font-weight:500">{title}</div>'
                f'<div style="font-size:11px;color:#6b7280">{desc}</div></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── PROXYS AIS VIA ACTIONS TANKERS ──
    st.subheader("Proxys AIS — Actions sociétés de transport maritime")
    st.caption("La valeur boursière des armateurs est un proxy indirect du niveau d'activité et des taux de fret")
    lookback = st.slider("Historique (jours)", 30, 120, 60, step=10, key="m1_lb")
    START = (TODAY - timedelta(days=lookback)).strftime("%Y-%m-%d")
    END   = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    proxy_tickers = [
        dict(ticker="DHT",  label="DHT Holdings (VLCC)",   bl=10.2,  note="Tankers pétroliers géants"),
        dict(ticker="FRO",  label="Frontline",              bl=19.5,  note="Flotte tankers mixte"),
        dict(ticker="INSW", label="Int'l Seaways",          bl=41.0,  note="Tankers + produits raffinés"),
        dict(ticker="TK",   label="Teekay Corp",            bl=7.5,   note="LNG + tankers"),
    ]
    series_proxy = {}
    proxy_cols = st.columns(4)
    for col, k in zip(proxy_cols, proxy_tickers):
        s   = fetch(k["ticker"], START, END)
        cur = safe_last(s)
        dp  = dpct(cur, k["bl"])
        ico, _ = sig(dp, 40)
        if not s.empty:
            series_proxy[k["label"]] = s
        with col:
            if cur is not None:
                st.metric(f"{ico} {k['label']}", fmtv(cur, "USD"), f"{dp:+.1f}% vs J0")
            else:
                st.metric(k["label"], "—", "indisponible")

    if series_proxy:
        fig_proxy = go.Figure()
        palette = ["#3b82f6","#f59e0b","#10b981","#8b5cf6"]
        for i, (lbl, s) in enumerate(series_proxy.items()):
            pos = s.index.searchsorted(pd.Timestamp(CLOSURE_DATE))
            ref = float(s.iloc[max(0, pos-1)]) if pos > 0 else float(s.iloc[0])
            if ref == 0: continue
            norm = s / ref * 100.0
            fig_proxy.add_trace(go.Scatter(
                x=norm.index, y=norm.values.tolist(),
                name=lbl, mode="lines",
                line=dict(width=1.8, color=palette[i % len(palette)])
            ))
        fig_proxy.add_hline(y=100, line=dict(dash="dot", color="#9ca3af", width=0.8))
        fig_proxy.add_vline(x=closure_s, line=dict(dash="dash", color="#ef4444", width=1.1))
        fig_proxy.add_annotation(x=closure_s, y=1, xref="x", yref="paper",
                                  text="Fermeture", showarrow=False,
                                  font=dict(size=9, color="#ef4444"),
                                  xanchor="left", yanchor="top", bgcolor="white", opacity=0.85)
        fig_proxy.update_layout(
            height=280, title=dict(text="Armateurs indexés — base 100 = fermeture (28 fév. 2026)", font_size=11),
            margin=dict(t=36, b=60, l=36, r=12), plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#f3f4f6", tickformat="%d %b"),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6", title="Index"),
            legend=dict(orientation="h", y=-0.28, font_size=10), hovermode="x unified",
        )
        st.plotly_chart(fig_proxy, use_container_width=True)

    st.markdown("---")
    st.caption(
        "**Sources AIS** : EIA STEO avr. 2026 · Wikipedia 2026 Strait of Hormuz crisis · "
        "IMF PortWatch (portwatch.imf.org) · AIS publics VesselFinder · MarineTraffic · "
        "Données boursières : Yahoo Finance · Cache 15 min"
    )
    with st.expander("🔗 Sources AIS en temps réel"):
        st.markdown("""
- **[IMF PortWatch](https://portwatch.imf.org)** — transit journalier par chokepoint (libre accès)
- **[MarineTraffic](https://www.marinetraffic.com/fr/ais/home/centerx:60.0/centery:23.4/zoom:7)** — AIS live Golfe Persique
- **[VesselFinder](https://www.vesselfinder.com)** — AIS live alternatif
- **[EIA Weekly Petroleum Status](https://www.eia.gov/petroleum/supply/weekly/)** — stocks + flux USA
- **[Freightos Baltic Index](https://fbx.freightos.com)** — taux de fret temps réel
        """)


# ══════════════════════════════════════════════════════════════════════════════
# 📊 MODULE 2 — SCÉNARIOS CASCADE
# ══════════════════════════════════════════════════════════════════════════════
elif module.startswith("📊"):
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


# ══════════════════════════════════════════════════════════════════════════════
# 📈 MODULE 3 — SUIVI ÉCONOMIQUE
# ══════════════════════════════════════════════════════════════════════════════
elif module.startswith("📈"):
    st.title("📈 Module 3 — Suivi Économique")
    lookback = st.slider("Historique (jours)", 30, 180, 60, step=10)
    START = (TODAY - timedelta(days=lookback)).strftime("%Y-%m-%d")
    END   = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    st.subheader("Indicateurs clés")
    KPI = [
        dict(label="Brent Crude",  ticker="BZ=F",  unit="$/bbl", bl=73.5,  thr=30, inv=False),
        dict(label="CF Industries",ticker="CF",     unit="USD",   bl=84.0,  thr=30, inv=False),
        dict(label="Maïs CBOT",    ticker="ZC=F",   unit="c/bu",  bl=455.0, thr=20, inv=False),
        dict(label="VIX",          ticker="^VIX",   unit="pts",   bl=18.0,  thr=50, inv=True),
    ]
    for col, k in zip(st.columns(4), KPI):
        s = fetch(k["ticker"], START, END); cur = safe_last(s); dp = dpct(cur, k["bl"])
        ico, _ = sig(dp, k["thr"])
        with col:
            if cur is not None:
                st.metric(f"{ico} {k['label']}", fmtv(cur, k["unit"]), f"{dp:+.1f}% vs J0",
                          delta_color="off" if k["inv"] else "normal")
            else:
                st.metric(k["label"], "—", "indisponible")

    st.markdown("---")
    for cat, instruments in INSTRUMENTS.items():
        with st.expander(cat, expanded=False):
            rows, series_map, local_alerts = [], {}, []
            for inst in instruments:
                s = fetch(inst["ticker"], START, END); cur = safe_last(s)
                dp = dpct(cur, inst["bl"]); ico, col_hex = sig(dp, inst["thr"])
                rows.append({"": ico, "Indicateur": inst["label"], "Valeur": fmtv(cur, inst["unit"]),
                              "J0 (27/02)": fmtv(inst["bl"], inst["unit"]),
                              "Δ J0": f"{dp:+.1f}%" if cur is not None else "—",
                              "Seuil": f"±{inst['thr']}%"})
                if not s.empty: series_map[inst["label"]] = s
                if ico in ("🔴","🟠"): local_alerts.append((ico, col_hex, inst["label"], dp, inst["note"]))

            left, right = st.columns([1.0, 2.0])
            with left:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220,
                             column_config={"": st.column_config.TextColumn("", width=28),
                                            "Indicateur": st.column_config.TextColumn("Indicateur", width=175),
                                            "Δ J0": st.column_config.TextColumn("Δ J0", width=70)})
                for ico, col_hex, lbl, dp, note in local_alerts:
                    st.markdown(
                        f'<div style="background:{col_hex}22;border-left:3px solid {col_hex};'
                        f'border-radius:4px;padding:5px 9px;font-size:11px;margin:3px 0">'
                        f'{ico} <b>{lbl}</b> : {dp:+.1f}% · {note}</div>',
                        unsafe_allow_html=True)
            with right:
                if series_map:
                    st.plotly_chart(indexed_chart(series_map, reopen_date, SCEN_COLOR[scen_days],
                                                  f"Réouv. J+{scen_days}"), use_container_width=True)
                else:
                    st.info("Données Yahoo Finance indisponibles pour cette période.")

    st.markdown("---")
    st.subheader("🚨 Alertes actives")
    alert_rows = []
    for cat, instruments in INSTRUMENTS.items():
        for inst in instruments:
            s = fetch(inst["ticker"], START, END); cur = safe_last(s)
            dp = dpct(cur, inst["bl"]); ico, _ = sig(dp, inst["thr"])
            if ico in ("🔴","🟠") and cur is not None:
                alert_rows.append({"Signal": ico, "Cat.": cat.split()[-1], "Indicateur": inst["label"],
                                   "Valeur": fmtv(cur, inst["unit"]), "Δ J0": f"{dp:+.1f}%",
                                   "Note": inst["note"]})
    if alert_rows:
        st.dataframe(pd.DataFrame(alert_rows).sort_values("Signal"), use_container_width=True, hide_index=True)
    else:
        st.success("Aucune alerte active.")
    st.caption("Sources : Yahoo Finance · Baselines J0 au 27 fév. 2026 · Cache 15 min · NG=F = proxy TTF")


# ══════════════════════════════════════════════════════════════════════════════
# 🔭 MODULE 4 — PROJECTIONS 6-12 MOIS
# ══════════════════════════════════════════════════════════════════════════════
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
                unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Timeline des effets — 12 mois post-réouverture")
    st.plotly_chart(gantt_chart(make_gantt(scen_days), p["color"], p["label"]), use_container_width=True)
    leg_cols = st.columns(5)
    for col, (sev, col_hex) in zip(leg_cols, SEV_COLOR.items()):
        col.markdown(
            f'<div style="background:{col_hex}33;border-left:3px solid {col_hex};'
            f'padding:3px 8px;border-radius:4px;font-size:11px">{sev.capitalize()}</div>',
            unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Matrice risques par zone")
    st.caption("Score composite 0-100 à H+6m et H+12m")
    st.plotly_chart(risk_chart(scen_days), use_container_width=True)

    st.markdown("---")
    st.subheader("Projections détaillées par secteur")
    for sector, items in p["sectors"].items():
        with st.expander(sector, expanded=False):
            h = st.columns([1,1,1,2])
            h[0].markdown("**Indicateur**"); h[1].markdown("**H+6 mois**")
            h[2].markdown("**H+12 mois**");  h[3].markdown("**Source**")
            for ind, v6, v12, sev, note in items:
                c_hex = SEV_COLOR.get(sev, "#9ca3af")
                cols = st.columns([1,1,1,2])
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
| **FMI avr. 2026** | PIB mondial 2.6% · Iran −6.1% · Arabie Saoudite 3.1% |
| **CNUCED 2026** | Commerce +1.5-2.5% vs 4.7% · 3.4 Mds personnes surexposées |
| **FAO mars 2026** | 3 mois = seuil critique planting 2026+ |
| **Goldman Sachs** | Brent >100$ si fermeture >1 mois |
| **Standard Chartered** | 8 Mb/j retirés des flux mondiaux |
""")
    st.caption(f"H+6m = {H6.strftime('%d %b %Y')} · H+12m = {H12.strftime('%d %b %Y')} · Réouverture = {reopen_date.strftime('%d %b %Y')}")
