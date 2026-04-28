"""
HORMUZ WATCH — Module 4 : Projections 6-12 mois
Scénarios de conséquences selon durée de fermeture restante (J+5 / J+20 / J+50 depuis aujourd'hui).
Sources : EIA STEO avril 2026, Allianz Research mars 2026, CNUCED, FMI, FAO, Goldman Sachs.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="HORMUZ WATCH — Projections",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constantes ───────────────────────────────────────────────────────────────
CLOSURE_DATE = date(2026, 2, 28)
TODAY        = date.today()
DAYS_CLOSED  = (TODAY - CLOSURE_DATE).days
H6  = TODAY + timedelta(days=183)   # horizon 6 mois
H12 = TODAY + timedelta(days=365)   # horizon 12 mois

# ── Palettes ─────────────────────────────────────────────────────────────────
SEV_COLOR  = {"critique": "#ef4444", "élevé": "#f97316",
              "modéré": "#eab308",   "limité": "#22c55e", "positif": "#3b82f6"}
SCEN_COLOR = {5: "#22c55e", 20: "#f59e0b", 50: "#ef4444"}
SECTOR_COLOR = {
    "Énergie":      "#3b82f6",
    "Alimentation": "#22c55e",
    "Industrie":    "#f59e0b",
    "Macro":        "#8b5cf6",
    "Géopolitique": "#ec4899",
}

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES DE PROJECTION
# Chaque entrée : secteur, effet, sévérité, valeur à 6m, valeur à 12m, source
# ══════════════════════════════════════════════════════════════════════════════

PROJECTIONS = {
    # ── J+5 : réouverture rapide ──────────────────────────────────────────────
    5: {
        "meta": {
            "label":   "Réouverture J+5",
            "reopen":  TODAY + timedelta(days=5),
            "color":   "#22c55e",
            "resume":  "Réouverture rapide. Choc de prix absorbé progressivement. "
                       "Effets agricoles en partie irréversibles (semis déjà décidés). "
                       "Europe reconstitue ses stocks avec délai mais hiver 2026-27 gérable.",
        },
        "sectors": {
            "Énergie": {
                "h6":  [
                    dict(indicateur="Brent crude",       valeur="~85 $/bbl",     sev="modéré",   detail="Correction depuis 126$/bbl. Risk premium résiduel ~10$. Source : EIA STEO avr. 2026"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~35-40 €/MWh",  sev="modéré",   detail="Détente progressive. Refill estival possible. Stockage ~55-60% objectif hivernage"),
                    dict(indicateur="Production Gulf",   valeur="-3 Mb/j résiduel", sev="modéré", detail="EIA : retour progressif mais pas immédiat. Infrastructures à remettre en route"),
                    dict(indicateur="LNG mondial",       valeur="+5-10% spot",    sev="limité",   detail="Correction rapide une fois les cargaisons reparties de Ras Laffan"),
                ],
                "h12": [
                    dict(indicateur="Brent crude",       valeur="~78 $/bbl",     sev="limité",   detail="Allianz Research : 78$/bbl fin 2026 dans scénario réouverture progressive"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~30-35 €/MWh",  sev="limité",   detail="Normalisation. Stockage hivernal reconstitué à ~80%"),
                    dict(indicateur="Production Gulf",   valeur="~pré-conflit",   sev="limité",   detail="EIA : retour proche des niveaux pré-conflit fin 2026"),
                    dict(indicateur="LNG mondial",       valeur="Normalisé",      sev="limité",   detail="Qatar reprend exportations normales"),
                ],
            },
            "Alimentation": {
                "h6":  [
                    dict(indicateur="Urée (prix)",       valeur="+25-35%",        sev="élevé",    detail="Correction partielle. Semis 2026 déjà décidés — impact irréversible pour récolte"),
                    dict(indicateur="Maïs CBOT",         valeur="+10-15%",        sev="modéré",   detail="Rendements Corn Belt USA réduits (engrais insuffisants saison). Récupération 2027"),
                    dict(indicateur="Blé mondial",       valeur="+8-12%",         sev="modéré",   detail="Marchés se détendent mais pays vulnérables (Égypte) restent sous tension"),
                    dict(indicateur="Prix alim. FAO",    valeur="+8-12%",         sev="modéré",   detail="FAO Food Price Index. Pic dépassé mais résiduel significatif"),
                ],
                "h12": [
                    dict(indicateur="Urée (prix)",       valeur="+5-10% résiduel",sev="limité",   detail="Retour progressif à la normale. Nouvelles capacités réactivées"),
                    dict(indicateur="Maïs CBOT",         valeur="+3-5% résiduel", sev="limité",   detail="Récolte 2027 normale si engrais disponibles en temps voulu"),
                    dict(indicateur="Blé mondial",       valeur="+3-5%",          sev="limité",   detail="Marchés reconstitués. Égypte reste vulnérable (imports)"),
                    dict(indicateur="Prix alim. FAO",    valeur="+3-5% résiduel", sev="limité",   detail="Normalisation attendue courant 2027"),
                ],
            },
            "Industrie": {
                "h6":  [
                    dict(indicateur="MEG (polyester)",   valeur="Tension résiduelle", sev="modéré", detail="Chine se réapprovisionne via USA. Coûts +15-20%"),
                    dict(indicateur="Aluminium",         valeur="+8-12%",          sev="modéré",  detail="Surcharges industrielles réduites. Énergie moins chère"),
                    dict(indicateur="Fret maritime",     valeur="+15-25% résiduel",sev="modéré",  detail="VLCC rates normalisent. Détour Cap Bonne-Espérance cesse"),
                    dict(indicateur="Chimie US",         valeur="Pic production",   sev="positif", detail="Dow Chemical : bénéficiaire — production full out. Exports vers Asie"),
                ],
                "h12": [
                    dict(indicateur="MEG (polyester)",   valeur="Normalisé",       sev="limité",  detail="Chaînes d'approvisionnement reconfigurées"),
                    dict(indicateur="Aluminium",         valeur="+3-5% résiduel",  sev="limité",  detail="Reprise progressive industrie lourde européenne"),
                    dict(indicateur="Fret maritime",     valeur="Normalisé",       sev="limité",  detail="Routes commerciales rétablies"),
                    dict(indicateur="Chimie US",         valeur="Production haute", sev="positif", detail="Gains de part de marché durables pour chimie USA"),
                ],
            },
            "Macro": {
                "h6":  [
                    dict(indicateur="PIB Eurozone",      valeur="+0.5-0.8% 2026",  sev="modéré",  detail="Allianz : +0.2% si fermeture >3 mois. Scénario J+5 = récession évitée de justesse"),
                    dict(indicateur="CPI Eurozone",      valeur="~2.8-3%",         sev="modéré",  detail="Allianz : 3% en 2026. Pic inflationniste en cours de résorption"),
                    dict(indicateur="PIB USA",           valeur="+1.5-2%",         sev="modéré",  detail="Effets offsetting : pertes consommateurs vs gains secteur énergie"),
                    dict(indicateur="Commerce mondial",  valeur="+2-2.5%",         sev="modéré",  detail="CNUCED : +1.5-2.5% (vs 4.7% en 2025). Meilleur scénario de la fourchette"),
                ],
                "h12": [
                    dict(indicateur="PIB Eurozone",      valeur="+0.8-1.2% 2027",  sev="limité",  detail="Reprise modeste. BCE reprend baisses de taux H2 2026"),
                    dict(indicateur="CPI Eurozone",      valeur="~2.2-2.5%",       sev="limité",  detail="Inflation redescend vers cible BCE"),
                    dict(indicateur="PIB USA",           valeur="+2-2.5% 2027",    sev="limité",  detail="Reprise. EIA : demande rebondit 2027 à 106.2 Mb/j"),
                    dict(indicateur="Commerce mondial",  valeur="+3-3.5%",         sev="limité",  detail="Rebond partiel. Reconfiguration chaînes d'approvisionnement"),
                ],
            },
            "Géopolitique": {
                "h6":  [
                    dict(indicateur="ENR investissement",  valeur="Accélération",    sev="positif", detail="Signal politique fort. Budgets ENR revus à la hausse Europe/Asie"),
                    dict(indicateur="LNG USA → Europe",    valeur="Contrats durables",sev="positif", detail="Substitution Qatar → USA LNG accélérée. Terminaux méthaniers saturés"),
                    dict(indicateur="Alliances Golfe",     valeur="Recomposition",    sev="modéré",  detail="GCC sous choc. Modèle économique Gulf disloqué temporairement"),
                    dict(indicateur="Marchés émergents",   valeur="Stress financier", sev="élevé",   detail="Devises sous pression, flight to safety USD. 3.4 Mds pers. exposés (CNUCED)"),
                ],
                "h12": [
                    dict(indicateur="ENR investissement",  valeur="+20-30% budgets",  sev="positif", detail="Reconfiguration durable. Réduction dépendance fossile accélérée"),
                    dict(indicateur="LNG USA → Europe",    valeur="Contrats 10-20 ans",sev="positif",detail="Nouveaux terminaux commandés. Diversification structurelle"),
                    dict(indicateur="Alliances Golfe",     valeur="Transition",       sev="modéré",  detail="GCC reconstruit mais sous pression. Aramco diversification"),
                    dict(indicateur="Marchés émergents",   valeur="Récupération lente",sev="modéré", detail="FMI assistance. Risques souverains contenus dans scénario rapide"),
                ],
            },
        },
    },

    # ── J+20 : fermeture ~80 jours ────────────────────────────────────────────
    20: {
        "meta": {
            "label":   "Réouverture J+20",
            "reopen":  TODAY + timedelta(days=20),
            "color":   "#f59e0b",
            "resume":  "Fermeture totale ~80 jours (J+59 + 20). Stockage gaz européen critique. "
                       "Saisons agricoles 2026 irrémédiablement impactées. "
                       "Récessions industrielles Europe confirmées. Hiver 2026-27 sous tension.",
        },
        "sectors": {
            "Énergie": {
                "h6":  [
                    dict(indicateur="Brent crude",       valeur="~95-105 $/bbl",  sev="élevé",   detail="Goldman Sachs : >100$/bbl si fermeture >1 mois. Risk premium structurel fort"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~50-60 €/MWh",   sev="critique", detail="Refill estival <40% capacité. Hiver 2026-27 à risque critique"),
                    dict(indicateur="Production Gulf",   valeur="-7-9 Mb/j résiduel",sev="critique",detail="EIA : shut-in 9.1 Mb/j avril. Retour très progressif post-réouverture"),
                    dict(indicateur="LNG mondial",       valeur="+30-40% spot",    sev="critique", detail="Force majeure QatarEnergy. Spot asiatique (JKM) sous tension extrême"),
                ],
                "h12": [
                    dict(indicateur="Brent crude",       valeur="~85-95 $/bbl",   sev="élevé",   detail="Risk premium persistant. Incertitude structurelle sur infrastructure Gulf"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~40-50 €/MWh",   sev="élevé",   detail="Hiver 2026-27 traversé avec rationnement. Stockage en reconstitution lente"),
                    dict(indicateur="Production Gulf",   valeur="-2-3 Mb/j résiduel",sev="modéré",detail="Infrastructures endommagées. Retour complet en 2027"),
                    dict(indicateur="LNG mondial",       valeur="+10-15% résiduel",sev="modéré",  detail="Qatar reprend mais capacités partiellement impactées"),
                ],
            },
            "Alimentation": {
                "h6":  [
                    dict(indicateur="Urée (prix)",       valeur="+50-60%",         sev="critique", detail="Cascade soufre→phosphate irréversible. Saison agricole 2026 compromis"),
                    dict(indicateur="Maïs CBOT",         valeur="+20-25%",         sev="élevé",   detail="Corn Belt : récolte 2026 réduite. Substitution maïs→soja confirmée"),
                    dict(indicateur="Blé mondial",       valeur="+20-30%",         sev="élevé",   detail="Égypte/Sahel/Pakistan sous tension alimentaire. FAO : alerte orange"),
                    dict(indicateur="Prix alim. FAO",    valeur="+15-25%",         sev="élevé",   detail="FAO : risques escalade significative planting 2026 et au-delà"),
                ],
                "h12": [
                    dict(indicateur="Urée (prix)",       valeur="+20-30% résiduel",sev="élevé",   detail="Marché restructuré. Nouvelles sources (Russie, Chine) mobilisées"),
                    dict(indicateur="Maïs CBOT",         valeur="+10-15% résiduel",sev="modéré",  detail="Récolte 2026 faible. 2027 meilleure mais incertitude engrais reste"),
                    dict(indicateur="Blé mondial",       valeur="+10-15%",         sev="élevé",   detail="Crise alimentaire 2027 confirmée dans pays vulnérables"),
                    dict(indicateur="Prix alim. FAO",    valeur="+10-15%",         sev="élevé",   detail="FAO prédit impact sur planting 2027. Crise structurelle en Asie du Sud"),
                ],
            },
            "Industrie": {
                "h6":  [
                    dict(indicateur="MEG (polyester)",   valeur="Pénurie aiguë",   sev="critique", detail="Chine : inventaires sous seuil d'alerte. Bangladesh/Vietnam : arrêts usines"),
                    dict(indicateur="Aluminium",         valeur="+15-20%",         sev="élevé",   detail="Récession industrielle Europe. Surcharges +30% maintenues"),
                    dict(indicateur="Fret maritime",     valeur="+40-60%",         sev="élevé",   detail="Détour Cap Bonne-Espérance généralisé. VLCC rates historiques"),
                    dict(indicateur="Textile Bangladesh",valeur="-30-40% export",  sev="critique", detail="Arrêts de production massifs. Millions d'emplois menacés"),
                ],
                "h12": [
                    dict(indicateur="MEG (polyester)",   valeur="+10-15% résiduel",sev="modéré",  detail="Réapprovisionnement USA/Inde. Reconfiguration chaîne durable"),
                    dict(indicateur="Aluminium",         valeur="+8-12% résiduel", sev="modéré",  detail="Reprise industrielle Europe lente. Capacités réduites structurellement"),
                    dict(indicateur="Fret maritime",     valeur="+10-15% résiduel",sev="modéré",  detail="Flotte redéployée. Coûts persistants liés aux nouvelles routes"),
                    dict(indicateur="Textile Bangladesh",valeur="-10-15% résiduel",sev="modéré",  detail="Récupération partielle. Commandes en retard difficiles à rattraper"),
                ],
            },
            "Macro": {
                "h6":  [
                    dict(indicateur="PIB Eurozone",      valeur="+0.1-0.3% 2026",  sev="critique", detail="Allianz : +0.2% en scénario 3 mois. Récession technique Allemagne/Italie"),
                    dict(indicateur="CPI Eurozone",      valeur="~3.5-4%",         sev="élevé",   detail="Inflation structurellement élevée. BCE dans l'impasse stagflation"),
                    dict(indicateur="PIB USA",           valeur="+1-1.5%",         sev="élevé",   detail="Inflation alim. +4-6%. Consommateur US sous pression"),
                    dict(indicateur="Commerce mondial",  valeur="+1.5-2%",         sev="élevé",   detail="CNUCED : bas de fourchette. Incertitude pèse sur investissement"),
                ],
                "h12": [
                    dict(indicateur="PIB Eurozone",      valeur="~0.5% 2027",      sev="élevé",   detail="Stagnation. Réindustrialisation forcée mais coûteuse"),
                    dict(indicateur="CPI Eurozone",      valeur="~3-3.5%",         sev="élevé",   detail="UK : inflation >5% confirmée. Zone euro : >3% début 2027"),
                    dict(indicateur="PIB USA",           valeur="+1.5-2% 2027",    sev="modéré",  detail="Secteur énergie/chimie compense. Mais consommateur affaibli"),
                    dict(indicateur="Commerce mondial",  valeur="+2-2.5%",         sev="modéré",  detail="Reprise timide. Reconfigurations supply chain absorbent de la croissance"),
                ],
            },
            "Géopolitique": {
                "h6":  [
                    dict(indicateur="Instabilité Bangladesh/Pak",valeur="Crise sociale",sev="critique",detail="Électricité rationnée, textile en crise, insécurité alimentaire montante"),
                    dict(indicateur="Égypte/Sahel",       valeur="Alerte FAO",       sev="critique", detail="Réserves blé épuisées. Subventions alimentaires insoutenables"),
                    dict(indicateur="Chine : diplomatie", valeur="Levier majeur",     sev="élevé",   detail="Pression US/Europe pour réouverture. Médiation chinoise possible"),
                    dict(indicateur="ENR/Indépendance",   valeur="Accélération forte",sev="positif", detail="Budgets ENR +30-50% en urgence. Efficacité énergétique prioritaire"),
                ],
                "h12": [
                    dict(indicateur="Instabilité Bangladesh/Pak",valeur="Transition difficile",sev="élevé",detail="Chômage durable, migrations internes, fragilité gouvernementale"),
                    dict(indicateur="Égypte/Sahel",        valeur="Crise alimentaire",sev="critique", detail="FAO : scénario similaire 2022 mais plus sévère. Aide internationale mobilisée"),
                    dict(indicateur="Chine : diplomatie",  valeur="Recomposition",    sev="élevé",   detail="Chine renforce liens avec Gulf, Russie, Afrique. Ordre énergétique recomposé"),
                    dict(indicateur="ENR/Indépendance",    valeur="Rupture structurelle",sev="positif",detail="Accélération massive. Horizon net-zero avancé paradoxalement"),
                ],
            },
        },
    },

    # ── J+50 : fermeture ~110 jours ───────────────────────────────────────────
    50: {
        "meta": {
            "label":   "Réouverture J+50",
            "reopen":  TODAY + timedelta(days=50),
            "color":   "#ef4444",
            "resume":  "Fermeture totale ~110 jours. Crise alimentaire mondiale 2027 confirmée. "
                       "Récessions industrielles multiples. Commerce mondial -2 pts. "
                       "Crises humanitaires émergentes. Recompositions géopolitiques structurelles.",
        },
        "sectors": {
            "Énergie": {
                "h6":  [
                    dict(indicateur="Brent crude",       valeur="~105-115 $/bbl",  sev="critique", detail="EIA STEO avr.2026 : pic Q2 115$/bbl. Risk premium persistant. Prod. −9-10 Mb/j"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~60-70 €/MWh",   sev="critique", detail="Urgence européenne. Hiver 2026-27 : rationnement partiel industrie probable"),
                    dict(indicateur="Production Gulf",   valeur="-9-10 Mb/j",      sev="critique", detail="Standard Chartered : 8 Mb/j retirés. Saudi Arabia +700k b/j pipeline réduit"),
                    dict(indicateur="LNG mondial",       valeur="+50%+ spot",      sev="critique", detail="Force majeure QatarEnergy. LNG spot JKM historique. Bangladesh/Pak : coupures"),
                ],
                "h12": [
                    dict(indicateur="Brent crude",       valeur="~90-100 $/bbl",   sev="élevé",   detail="EIA : risk premium tout au long de la période. Infrastructure Gulf abîmée"),
                    dict(indicateur="Gaz Europe (TTF)",  valeur="~45-55 €/MWh",   sev="élevé",   detail="Hiver passé mais stockage reconstitution lente. Vulnérabilité structurelle"),
                    dict(indicateur="Production Gulf",   valeur="-2-4 Mb/j résiduel",sev="élevé",  detail="EIA : retour proche pré-conflit fin 2026 mais incertitude élevée"),
                    dict(indicateur="LNG mondial",       valeur="+15-20% résiduel",sev="élevé",   detail="Qatar redémarre progressivement. Marché reconfiguré durablement"),
                ],
            },
            "Alimentation": {
                "h6":  [
                    dict(indicateur="Urée (prix)",       valeur="+60-70%",         sev="critique", detail="Pic historique. Cascade soufre totalement impactée. FAO : 3 mois = seuil critique"),
                    dict(indicateur="Maïs CBOT",         valeur="+25-30%",         sev="critique", detail="Récolte 2026 catastrophique. Corn Belt : −15-20% rendement. Feed bovins affecté"),
                    dict(indicateur="Blé mondial",       valeur="+30-40%",         sev="critique", detail="Égypte, Pakistan, Bangladesh : réserves épuisées. Achats spot impossibles"),
                    dict(indicateur="Prix alim. FAO",    valeur="+25-35%",         sev="critique", detail="FAO : niveau proche 2022 mais fragilité du système plus grande"),
                ],
                "h12": [
                    dict(indicateur="Urée (prix)",       valeur="+30-40% résiduel",sev="critique", detail="Marché restructuré mais capacités Gulf partiellement détruites. Pénurie 2027"),
                    dict(indicateur="Maïs CBOT",         valeur="+15-20% résiduel",sev="élevé",   detail="Récolte 2027 sous contrainte. Cycle de récupération long (2-3 ans)"),
                    dict(indicateur="Blé mondial",       valeur="+20-25%",         sev="critique", detail="Crise alimentaire mondiale 2027 confirmée. PAM : aide d'urgence"),
                    dict(indicateur="Prix alim. FAO",    valeur="+20-25%",         sev="critique", detail="FAO prédit impact prolongé jusqu'en 2028. Insécurité alimentaire structurelle"),
                ],
            },
            "Industrie": {
                "h6":  [
                    dict(indicateur="MEG (polyester)",   valeur="Rupture supply",   sev="critique", detail="Inventaires Chine à zéro. Textile Asie du Sud : effondrement partiel"),
                    dict(indicateur="Aluminium",         valeur="+20-30%",          sev="critique", detail="Énergie Europe trop chère. Fermetures usines aluminium confirmées"),
                    dict(indicateur="Fret maritime",     valeur="+60-80%",          sev="critique", detail="VLCC records absolus. Détour Cap systématique (+7-10j). Pénurie tonnage"),
                    dict(indicateur="Sidérurgie",        valeur="-15-20% prod",     sev="critique", detail="DRI/pellets Gulf bloqués. Acier européen/asiatique sous contrainte"),
                ],
                "h12": [
                    dict(indicateur="MEG (polyester)",   valeur="+15-20% résiduel", sev="élevé",   detail="Reconfiguration profonde. USA/Inde fournisseurs alternatifs consolidés"),
                    dict(indicateur="Aluminium",         valeur="+10-15% résiduel", sev="élevé",   detail="Certaines capacités européennes fermées définitivement"),
                    dict(indicateur="Fret maritime",     valeur="+15-20% résiduel", sev="élevé",   detail="Nouvelles routes commerciales intégrées dans les coûts de base"),
                    dict(indicateur="Sidérurgie",        valeur="-5-8% résiduel",   sev="modéré",  detail="Restructuration. DRI alternatifs (Australie, Brésil) mobilisés"),
                ],
            },
            "Macro": {
                "h6":  [
                    dict(indicateur="PIB Eurozone",      valeur="-0.2 à +0.1%",    sev="critique", detail="Allianz : récession technique confirmée si >3 mois. Allemagne : contraction"),
                    dict(indicateur="CPI Eurozone",      valeur="~4-5%",            sev="critique", detail="UK : >5% confirmé. Zone euro : +4% BCE impuissante. Stagflation"),
                    dict(indicateur="PIB USA",           valeur="+0.5-1%",          sev="élevé",   detail="Inflation alimentaire +6-8%. SPR épuisé. Consommateur très affaibli"),
                    dict(indicateur="Commerce mondial",  valeur="+1.5%",            sev="critique", detail="CNUCED : plus bas de fourchette. Récession commerciale mondiale"),
                ],
                "h12": [
                    dict(indicateur="PIB Eurozone",      valeur="~0.2-0.5% 2027",  sev="élevé",   detail="Stagnation. Récession 2026 creuse un trou structurel dans la croissance"),
                    dict(indicateur="CPI Eurozone",      valeur="~3.5-4% 2027",    sev="élevé",   detail="Désinfection longue. Effets de second tour salaires/loyers"),
                    dict(indicateur="PIB USA",           valeur="+1-1.5% 2027",    sev="élevé",   detail="Récupération lente. Secteur énergie compense partiellement"),
                    dict(indicateur="Commerce mondial",  valeur="+2-2.5% 2027",    sev="modéré",  detail="Rebond partiel. Nombreux contrats renégociés. Supply chains réduites"),
                ],
            },
            "Géopolitique": {
                "h6":  [
                    dict(indicateur="Crises humanitaires",valeur="Bangladesh/Pak/Égyp",sev="critique",detail="FAO : 3 pays en urgence rouge. PAM mobilisé. Instabilité gouvernementale"),
                    dict(indicateur="Migrations",          valeur="Hausse flux",      sev="critique", detail="Exode économique Asie du Sud. Pression sur Inde, Golfe, Europe"),
                    dict(indicateur="Marchés émergents",   valeur="Défauts souverains",sev="critique", detail="CNUCED : 3.4 Mds exposés. Dettes libellées USD + devises en chute"),
                    dict(indicateur="Ordre énergétique",   valeur="Recomposition",    sev="élevé",   detail="Fin du modèle GCC actuel. Chine/Inde réorientent alliances durablement"),
                ],
                "h12": [
                    dict(indicateur="Crises humanitaires",valeur="Crise 2027",        sev="critique", detail="FAO/PAM : 'perfect storm' alimentation. Pire que 2022. Long terme compromis"),
                    dict(indicateur="Migrations",          valeur="Flux structurels",  sev="élevé",   detail="Migrations liées à insécurité alimentaire et économique (long terme)"),
                    dict(indicateur="Marchés émergents",   valeur="Restructurations",  sev="élevé",   detail="FMI : programmes d'aide massifs. Dettes restructurées. Décennie perdue?"),
                    dict(indicateur="Ordre énergétique",   valeur="Nouvel ordre",      sev="élevé",   detail="ENR +50% investissements. Fossil fuel dependency permanence remise en cause"),
                ],
            },
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES TIMELINE (effets sur 12 mois)
# ══════════════════════════════════════════════════════════════════════════════
def make_timeline(scen_days: int) -> list[dict]:
    reopen = TODAY + timedelta(days=scen_days)
    r = reopen.strftime("%Y-%m-%d")
    """Retourne une liste de tâches pour Gantt."""
    base = [
        # Secteur, Effet, début offset (jours depuis réouverture), durée (jours), sévérité
        ("Énergie",      "Brent correction",          0,   60,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Énergie",      "TTF gaz Europe",             0,  120,  "modéré"  if scen_days<=5  else "critique"),
        ("Énergie",      "Production Gulf",            0,  180,  "élevé"   if scen_days<=5  else "critique"),
        ("Alimentation", "Urée correction prix",       0,   90,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Alimentation", "Impact récolte 2026",       30,  120,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Alimentation", "Crise alimentaire 2027",   120,  180,  "limité"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Industrie",    "MEG/méthanol normalisation", 0,   60,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Industrie",    "Fret maritime",              0,   90,  "modéré"  if scen_days<=5  else "élevé"),
        ("Industrie",    "Textile Bangladesh",        30,  120,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Macro",        "Inflation CPI",              0,  180,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Macro",        "PIB Eurozone",              30,  270,  "modéré"  if scen_days<=5  else "critique"),
        ("Macro",        "Marchés émergents",          0,  270,  "élevé"   if scen_days<=5  else "critique"),
        ("Géopolitique", "ENR accélération",           0,  365,  "positif"),
        ("Géopolitique", "Crises humanitaires",       60,  300,  "modéré"  if scen_days<=5  else "élevé"    if scen_days<=20 else "critique"),
        ("Géopolitique", "Recomposition alliances",   60,  365,  "élevé"),
    ]
    rows = []
    for sector, effect, offset_start, duration, sev in base:
        start = reopen + timedelta(days=offset_start)
        end   = start  + timedelta(days=duration)
        end   = min(end, H12 + timedelta(days=30))
        rows.append(dict(
            sector=sector, effect=effect,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            sev=sev,
        ))
    return rows


def gantt_chart(rows: list[dict], scen_color: str) -> go.Figure:
    sectors = list(dict.fromkeys(r["sector"] for r in rows))
    fig = go.Figure()

    for row in rows:
        color = SEV_COLOR.get(row["sev"], "#9ca3af")
        fig.add_trace(go.Bar(
            x=[(pd.Timestamp(row["end"]) - pd.Timestamp(row["start"])).days],
            y=[f"{row['sector']} · {row['effect']}"],
            base=[row["start"]],
            orientation="h",
            marker_color=color,
            marker_opacity=0.75,
            name=row["sev"],
            showlegend=False,
            hovertemplate=(
                f"<b>{row['effect']}</b><br>"
                f"Du {row['start']} au {row['end']}<br>"
                f"Sévérité : {row['sev']}<extra></extra>"
            ),
        ))

    # Lignes verticales : aujourd'hui, 6m, 12m — en string
    today_s = TODAY.strftime("%Y-%m-%d")
    h6_s    = H6.strftime("%Y-%m-%d")
    h12_s   = H12.strftime("%Y-%m-%d")
    for x_str, label, col in [
        (today_s, "Aujourd'hui", "#6b7280"),
        (h6_s,    "H+6 mois",   "#3b82f6"),
        (h12_s,   "H+12 mois",  "#8b5cf6"),
    ]:
        fig.add_vline(x=x_str, line=dict(dash="dash", color=col, width=1.1))
        fig.add_annotation(
            x=x_str, y=1, xref="x", yref="paper",
            text=label, showarrow=False,
            font=dict(size=9, color=col),
            xanchor="left", yanchor="top",
            bgcolor="white", opacity=0.85,
        )

    fig.update_layout(
        height=420,
        margin=dict(t=24, b=20, l=200, r=20),
        barmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            type="date",
            showgrid=True, gridcolor="#f3f4f6",
            tickformat="%b %Y",
            range=[TODAY.strftime("%Y-%m-%d"), (H12 + timedelta(days=30)).strftime("%Y-%m-%d")],
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        hovermode="closest",
    )
    return fig


def risk_matrix_chart(scen_days: int) -> go.Figure:
    """Matrice zones × horizons avec score de risque."""
    zones = ["Chine", "Inde", "Europe", "Bangladesh/Pak", "USA", "Afrique/M-O"]
    h6_scores  = {
        5:  [55, 65, 50, 75, 35, 60],
        20: [70, 80, 65, 90, 45, 75],
        50: [85, 90, 80, 95, 55, 85],
    }
    h12_scores = {
        5:  [35, 45, 30, 55, 20, 40],
        20: [55, 65, 50, 80, 35, 65],
        50: [70, 80, 65, 90, 45, 80],
    }

    scores_6  = h6_scores[scen_days]
    scores_12 = h12_scores[scen_days]

    def score_to_color(s):
        if s >= 80: return "#ef4444"
        if s >= 65: return "#f97316"
        if s >= 45: return "#eab308"
        return "#22c55e"

    fig = go.Figure()
    for i, (zone, s6, s12) in enumerate(zip(zones, scores_6, scores_12)):
        fig.add_trace(go.Bar(
            name="6 mois", x=[s6], y=[zone], orientation="h",
            marker_color=score_to_color(s6), opacity=0.85,
            showlegend=(i == 0),
            hovertemplate=f"{zone}<br>Risque H+6m : {s6}/100<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="12 mois", x=[s12], y=[zone], orientation="h",
            marker_color=score_to_color(s12), opacity=0.45,
            showlegend=(i == 0),
            hovertemplate=f"{zone}<br>Risque H+12m : {s12}/100<extra></extra>",
        ))

    fig.update_layout(
        barmode="group",
        height=300,
        margin=dict(t=24, b=20, l=120, r=60),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(range=[0, 100], title="Score de risque (/100)", showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.2, font_size=10),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")

    scen_days = st.radio(
        "Scénario de réouverture *(depuis aujourd'hui)*",
        options=[5, 20, 50],
        format_func=lambda x: f"J+{x}  →  {(TODAY + timedelta(days=x)).strftime('%d %b %Y')}",
    )
    scen_meta = PROJECTIONS[scen_days]["meta"]

    st.markdown(
        f'<div style="background:{scen_meta["color"]}22;border-left:3px solid {scen_meta["color"]};'
        f'padding:8px 10px;border-radius:4px;font-size:12px;line-height:1.5;margin:4px 0">'
        f'{scen_meta["resume"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    focus_sector = st.selectbox(
        "Focus secteur",
        options=["Tous"] + list(PROJECTIONS[5]["sectors"].keys()),
    )

    st.markdown("---")
    st.error(
        f"🚫 **Détroit fermé**  \n"
        f"Depuis le 28 fév. 2026  \n"
        f"**J+{DAYS_CLOSED}** jours"
    )
    st.markdown("---")
    st.markdown(f"""
| Horizon | Date |
|---|---|
| H+6 mois | {H6.strftime('%d %b %Y')} |
| H+12 mois | {H12.strftime('%d %b %Y')} |
| Réouverture | {scen_meta['reopen'].strftime('%d %b %Y')} |
""")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔭 HORMUZ WATCH — Module 4 : Projections 6-12 mois")
st.caption(
    f"Scénario actif : **{scen_meta['label']}** · "
    f"Réouverture estimée **{scen_meta['reopen'].strftime('%d %b %Y')}** · "
    f"J+{DAYS_CLOSED} de fermeture"
)

# ── KPI Projections ───────────────────────────────────────────────────────────
st.subheader("Projections clés aux deux horizons")
kpi_data = {
    5:  [("Brent H+6m",  "~85 $/bbl",     "modéré"),  ("Brent H+12m",  "~78 $/bbl",   "limité"),
         ("Urée H+6m",   "+25-35%",        "élevé"),   ("FAO alim H+6m","+8-12%",      "modéré"),
         ("CPI Euro H+6m","~3%",           "modéré"),  ("PIB Euro 2026","+0.5-0.8%",   "modéré"),
         ("Commerce 2026","+2-2.5%",       "modéré"),  ("Crise alim.",  "Limitée",     "limité")],
    20: [("Brent H+6m",  "~95-105 $/bbl",  "élevé"),   ("Brent H+12m",  "~85-95 $/bbl","élevé"),
         ("Urée H+6m",   "+50-60%",        "critique"),("FAO alim H+6m","+15-25%",     "élevé"),
         ("CPI Euro H+6m","~3.5-4%",       "élevé"),   ("PIB Euro 2026","+0.1-0.3%",  "critique"),
         ("Commerce 2026","+1.5-2%",       "élevé"),   ("Crise alim.",  "Confirmée",  "critique")],
    50: [("Brent H+6m",  "~105-115 $/bbl", "critique"),("Brent H+12m",  "~90-100 $/bbl","élevé"),
         ("Urée H+6m",   "+60-70%",        "critique"),("FAO alim H+6m","+25-35%",     "critique"),
         ("CPI Euro H+6m","~4-5%",         "critique"),("PIB Euro 2026","-0.2 à +0.1%","critique"),
         ("Commerce 2026","+1.5%",         "critique"),("Crise alim.",  "Mondiale 2027","critique")],
}
row1 = kpi_data[scen_days]
for i, chunk in enumerate([row1[:4], row1[4:]]):
    cols = st.columns(4)
    for col, (label, val, sev) in zip(cols, chunk):
        bg = SEV_COLOR.get(sev, "#9ca3af") + "22"
        col.markdown(
            f'<div style="background:{bg};border-radius:8px;padding:10px 12px;margin:2px">'
            f'<div style="font-size:11px;color:#6b7280;margin-bottom:3px">{label}</div>'
            f'<div style="font-size:15px;font-weight:500">{val}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Timeline ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Timeline des effets — 12 mois post-réouverture")
st.caption("Chaque barre = durée estimée de l'effet. Couleur = sévérité. Les barres débutent à la date de réouverture sauf pour les effets différés.")

timeline_rows = make_timeline(scen_days)
st.plotly_chart(gantt_chart(timeline_rows, scen_meta["color"]), use_container_width=True)

# Légende sévérité
leg_cols = st.columns(5)
for col, (sev, col_hex) in zip(leg_cols, SEV_COLOR.items()):
    col.markdown(
        f'<div style="background:{col_hex}33;border-left:3px solid {col_hex};'
        f'padding:3px 8px;border-radius:4px;font-size:11px">{sev.capitalize()}</div>',
        unsafe_allow_html=True,
    )

# ── Matrice risques par zone ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("Matrice de risques par zone géographique")
st.caption("Score de risque composite (0-100) à 6 et 12 mois. 80+ = critique, 65+ = élevé, 45+ = modéré.")
st.plotly_chart(risk_matrix_chart(scen_days), use_container_width=True)

# ── Deep-dives sectoriels ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Projections détaillées par secteur")

sectors_to_show = (
    list(PROJECTIONS[scen_days]["sectors"].keys())
    if focus_sector == "Tous"
    else [focus_sector]
)

for sector in sectors_to_show:
    data = PROJECTIONS[scen_days]["sectors"][sector]
    color = SECTOR_COLOR.get(sector, "#6b7280")
    with st.expander(f"{sector}", expanded=(focus_sector != "Tous")):
        col_h6, col_h12 = st.columns(2)

        for col_ui, horizon_key, horizon_label in [
            (col_h6,  "h6",  f"À 6 mois — {H6.strftime('%b %Y')}"),
            (col_h12, "h12", f"À 12 mois — {H12.strftime('%b %Y')}"),
        ]:
            col_ui.markdown(f"**{horizon_label}**")
            for item in data[horizon_key]:
                sev    = item["sev"]
                c_hex  = SEV_COLOR.get(sev, "#9ca3af")
                col_ui.markdown(
                    f'<div style="background:{c_hex}18;border-left:3px solid {c_hex};'
                    f'border-radius:4px;padding:7px 10px;margin:4px 0;font-size:12px">'
                    f'<b>{item["indicateur"]}</b> &nbsp;<span style="color:{c_hex};font-weight:500">{item["valeur"]}</span>'
                    f'<br><span style="color:#6b7280;font-size:11px">{item["detail"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ── Comparaison 3 scénarios ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("Comparaison des 3 scénarios à 12 mois")

comp_rows = []
metrics_comp = [
    ("Énergie",      "Brent crude",        "h12", 0),
    ("Énergie",      "Gaz Europe (TTF)",   "h12", 1),
    ("Alimentation", "Urée (prix)",        "h12", 0),
    ("Alimentation", "Prix alim. FAO",     "h12", 3),
    ("Macro",        "PIB Eurozone",       "h12", 0),
    ("Macro",        "CPI Eurozone",       "h12", 2),
    ("Macro",        "Commerce mondial",   "h12", 3),
]
for sector, indicator, horizon, idx in metrics_comp:
    row = {"Secteur": sector, "Indicateur": indicator}
    for sd in [5, 20, 50]:
        items = PROJECTIONS[sd]["sectors"][sector][horizon]
        match = [x for x in items if x["indicateur"] == indicator]
        if match:
            row[f"J+{sd} ({PROJECTIONS[sd]['meta']['reopen'].strftime('%d %b')})"] = (
                match[0]["valeur"] + " · " + match[0]["sev"].upper()
            )
        else:
            row[f"J+{sd} ({PROJECTIONS[sd]['meta']['reopen'].strftime('%d %b')})"] = "—"
    comp_rows.append(row)

st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

# ── Sources ───────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📚 Sources utilisées"):
    st.markdown("""
| Source | Données clés utilisées |
|---|---|
| **EIA STEO avril 2026** | Brent pic Q2 115$/bbl · Production shut-in 9.1 Mb/j avril · Risk premium prolongé |
| **Allianz Research mars 2026** | PIB Eurozone +0.2% si >3 mois · CPI Eurozone 3% · CPI USA 3.2% |
| **FMI avr. 2026** | PIB Iran −6.1% · Saudi Arabia 3.1% · Croissance mondiale 2.6% vs 2.9% |
| **CNUCED 2026** | Commerce mondial +1.5-2.5% vs 4.7% · 3.4 Mds personnes surexposées |
| **FAO mars 2026** | 3 mois = seuil critique décisions planting · Bangladesh/Inde/Égypte en rouge |
| **Goldman Sachs** | Brent >100$/bbl si fermeture >1 mois |
| **Standard Chartered** | 8 Mb/j retirés des flux mondiaux |
| **Wikipedia / Economic impact 2026 Iran war** | Données agrégées temps réel |
""")

st.caption(
    "HORMUZ WATCH Module 4 — Projections basées sur EIA, Allianz, FMI, CNUCED, FAO, Goldman Sachs · "
    f"Horizons : H+6m = {H6.strftime('%d %b %Y')} · H+12m = {H12.strftime('%d %b %Y')}"
)
