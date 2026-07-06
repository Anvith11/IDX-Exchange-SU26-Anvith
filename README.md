# California Property Close Price Prediction
**IDX Exchange — Summer 2026 Data Science Internship**
*Intern: Anvith Mulpuri | UIUC Data Science & Information Sciences, Class of 2028*

---

## Overview

This repository contains the early-stage data science project developed during my Summer 2026 internship at IDX Exchange. The goal is to build a machine learning model that predicts the **close price (final sale price)** of single-family residential properties in California, using historical sold listing data sourced from **CRMLS (California Regional Multiple Listing Service)** — one of the largest MLS systems in the United States.

The project currently includes a Week 1 deliverable summary and initial notebook work for exploration and preprocessing. The model is trained exclusively on:
- `PropertyType = Residential`
- `PropertySubType = SingleFamilyResidence`

Once trained and validated, the model is intended to predict the close price of any single residential property in California — currently for sale or not — based on its characteristics at query time.

---

## Project Goals

- Develop a reliable ML regression model to predict `ClosePrice` from property features
- Explore, clean, and engineer features from raw MLS sold data
- Evaluate model performance using R², MAPE, and MdAPE
- Document all decisions and findings in reproducible Jupyter notebooks
- (Optional) Deploy a lightweight Streamlit app for live price prediction
- Deliver a final Zoom presentation to IDX Exchange stakeholders

---

## Repository Structure

```
IDX-Exchange-SU26-Anvith/
│
├── Week 1/
│   └── deliverable.md              # Week 1 submission notes and progress summary
│
├── notebooks/
│   ├── 01_exploration.ipynb        # EDA: distributions, patterns, key fields
│   └── 02_preprocessing.ipynb      # Cleaning, encoding, and train/test split prep
│
└── README.md
```

> **Note:** Raw CRMLS data files (`CRMLSSold*`) are not committed to this repository. They are sourced via FTP and stored locally per IDX Exchange data handling guidelines.

---

## Data Source

| Field | Value |
|---|---|
| Source | CRMLS (California Regional Multiple Listing Service) |
| Access | FTP via FileZilla — `Host: 199.250.207.194`, Port 21 |
| Files | `CRMLSSold*` files in `/raw/California` |
| Minimum Window | 6 months of sold listings |
| Filter | `PropertyType = Residential`, `PropertySubType = SingleFamilyResidence` |
| Metadata Reference | `Trestle Property MetaData.pdf` (in `/resources` folder on FTP) |

### Key Fields

| Field | Description |
|---|---|
| `ClosePrice` | **Target variable** — final agreed sale price |
| `ListPrice` | Seller's asking price at listing time |
| `LivingArea` | Interior square footage |
| `BedroomsTotal` | Number of bedrooms |
| `BathroomsTotalInteger` | Number of bathrooms |
| `LotSizeSquareFeet` | Lot size |
| `Latitude / Longitude` | Geographic coordinates |
| `CloseDate` | Date the transaction officially closed |
| `ListingContractDate` | Date the listing agreement was signed |

---

## Methodology

### Train / Test Split
The most recent month of available data is held out as the **test set**. The preceding months serve as the **training window** — the length of this window is treated as a tunable parameter and optimized experimentally.

### Models Explored
1. **Linear Regression** — baseline
2. **Decision Tree Regressor**
3. **Random Forest Regressor**
4. **Gradient Boosting** (XGBoost / LightGBM) — primary candidate

### Feature Engineering
- Bed/bath ratio
- Property age (years since built)
- Price per square foot (exploratory)
- **School district layer** — spatial join against [CA School District Areas 2024–25](https://data.ca.gov/dataset/california-school-district-areas-2024-25/resource/7dfaf005-58eb-45db-93b1-7aff091b2172) boundaries using property lat/lon

### Evaluation Metrics
- **R²** (primary)
- **MAPE** — Mean Absolute Percentage Error
- **MdAPE** — Median Absolute Percentage Error

---

## Tools & Requirements

### Languages & Environment
- Python 3.10+
- Jupyter Notebook / Google Colab

### Core Libraries

```bash
pip install pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm geopandas joblib streamlit
```

| Library | Purpose |
|---|---|
| `pandas`, `numpy` | Data manipulation |
| `matplotlib`, `seaborn` | Visualization |
| `scikit-learn` | Preprocessing, baseline & tree models, evaluation |
| `xgboost` / `lightgbm` | Gradient boosting models |
| `geopandas` | Spatial join for school district features |
| `joblib` | Model serialization |
| `streamlit` | Prediction app (optional) |

### Data Access
- [FileZilla Client](https://filezilla-project.org) — for FTP access to raw CRMLS data

---

## Current Progress

| Area | Status |
|---|---|
| Week 1 deliverable summary | ✅ Completed |
| Exploratory data analysis notebook | ✅ Started |
| Preprocessing notebook | ✅ Added |
| Modeling notebooks and evaluation pipeline | ⬜ Planned |
| Final presentation materials | ⬜ Planned |

---

## How to Run

1. **Clone the repo**
   ```bash
   git clone https://github.com/Anvith11/IDX-Exchange-SU26-Anvith.git
   cd IDX-Exchange-SU26-Anvith
   ```

2. **Install dependencies**
   ```bash
   pip install pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm geopandas joblib streamlit
   ```

3. **Download the data** via FileZilla using the FTP credentials provided by IDX Exchange. Place the `CRMLSSold*` files in a local data directory for local analysis.

4. **Run notebooks in order** — start with [notebooks/01_exploration.ipynb](notebooks/01_exploration.ipynb) and continue with [notebooks/02_preprocessing.ipynb](notebooks/02_preprocessing.ipynb) as the project expands.

---

## Background: MLS Data Context

The data originates from CRMLS, the California Regional Multiple Listing Service. A few key concepts relevant to understanding and working with this dataset:

- **ClosePrice vs. ListPrice** — `ClosePrice` is the true transaction value; `ListPrice` is the seller's initial ask. The ratio between them (sale-to-list ratio) is a strong market health signal.
- **StandardStatus filtering** — Price trend analyses must filter to `StandardStatus = Closed`. Pending records do not yet have a confirmed `ClosePrice`.
- **Single Family Residential (SFR)** — This project focuses exclusively on SFR properties, the standard benchmark for market analysis. Mixing property types (condos, townhouses, multi-family) without filtering produces misleading results.
- **Days on Market (DOM)** — Calculated as days from `ListingContractDate` to `CloseDate`. Low DOM signals high demand; high DOM may indicate overpricing or weak buyer interest.

---

## Deliverables (Current Submission)

- [x] Week 1 deliverable summary in [Week 1/deliverable.md](Week%201/deliverable.md)
- [x] Exploratory notebook in [notebooks/01_exploration.ipynb](notebooks/01_exploration.ipynb)
- [x] Preprocessing notebook in [notebooks/02_preprocessing.ipynb](notebooks/02_preprocessing.ipynb)
- [ ] Additional modeling and evaluation notebooks as the project progresses
- [ ] Final presentation materials for IDX Exchange stakeholders

---
