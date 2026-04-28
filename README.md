# 🛢️ Hormuz Watch — Module 3 : Suivi Économique

Tableau de bord de suivi des indicateurs économiques liés à la fermeture du détroit d'Ormuz.  
Scénarios de réouverture **J+5 / J+20 / J+50 à partir d'aujourd'hui**.

---

## Ce que fait l'application

- **Données automatiques** (yFinance, toutes les 30 min) :
  - Brent & WTI, Gaz naturel US, Maïs / Blé / Soja CBOT
  - Actions tankers (FRO, STNG, DHT) comme proxies du fret
  - EUR/USD, Dollar Index, Or, Aluminium

- **Données manuelles** (barre latérale, à mettre à jour vous-même) :
  - TTF Gaz EU, JKM LNG Asie, Urée Tampa, DAP, Ammoniac
  - Navires/jour Hormuz (IMF PortWatch), War risk premium, VLCC rates, BDTI

- **5 onglets** : Énergie · Engrais & Alimentation · Fret & Trafic · Macro · Scénarios

- **Onglet Scénarios** : interprétation des effets rang 1/2/3 selon la date de réouverture

---

## Déploiement sur Streamlit Community Cloud (gratuit)

### Étape 1 — Mettre les fichiers sur GitHub

1. Connectez-vous à [github.com](https://github.com)
2. Créez un nouveau dépôt public : `hormuz-watch`
3. Uploadez les fichiers :
   - `app.py`
   - `requirements.txt`
   - `README.md`

### Étape 2 — Déployer sur Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez-vous avec votre compte GitHub
3. Cliquez **"New app"**
4. Sélectionnez votre dépôt `hormuz-watch`
5. Fichier principal : `app.py`
6. Cliquez **"Deploy"** → URL publique générée en ~2 minutes

---

## Mise à jour des données manuelles

Ouvrez la **barre latérale gauche** (flèche `>` en haut à gauche) et mettez à jour :

| Donnée | Source recommandée |
|---|---|
| TTF Gaz EU | [tradingeconomics.com/commodity/eu-natural-gas](https://tradingeconomics.com/commodity/eu-natural-gas) |
| JKM LNG Asie | [spglobal.com](https://www.spglobal.com/commodityinsights) |
| Urée Tampa | [greenmarkets.com](https://www.greenmarkets.com) |
| Navires/jour | [hormuztracker.com](https://hormuztracker.com) ou [IMF PortWatch](https://portwatch.imf.org) |
| BDTI | [balticexchange.com](https://www.balticexchange.com) |
| War risk | [lloydslist.com](https://www.lloydslist.com) |

---

## Structure des modules

```
Hormuz Watch
├── Module 1 : Observatoire trafic (AIS) — à venir
├── Module 2 : Analyse des flux (carte) — construit
├── Module 3 : Suivi économique ← vous êtes ici
└── Module 4 : Scénarios & alertes — à venir
```

---

## Dépendances

```
streamlit>=1.33.0
yfinance>=0.2.40
pandas>=2.0.0
plotly>=5.20.0
```
