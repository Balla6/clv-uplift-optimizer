# Profit-Driven CLV + Uplift + Contact-Policy Optimizer

**Project Overview**  
A production-style marketer’s toolkit that (1) predicts *incremental* response via **uplift modeling**, (2) optionally estimates **CLV** with BG/NBD & Gamma-Gamma (PNBD), and (3) selects who to contact under a **profit** objective and **budget/fatigue** constraints. It ships with a **CLI scorer**, **FastAPI** for programmatic scoring, and a **Streamlit** UI for quick simulations.

---

## Table of Contents
- [1. Data](#1-data)
- [2. Modeling](#2-modeling)
- [3. Profit & Policy](#3-profit--policy)
- [4. Parity Check (CLI ↔ Notebooks)](#4-parity-check-cli--notebooks)
- [5. Local Setup & Runbook](#5-local-setup--runbook)
- [6. How to Use](#6-how-to-use)
  - [6.1 CLI (batch CSV)](#61-cli-batch-csv)
  - [6.2 FastAPI (programmatic)](#62-fastapi-programmatic)
  - [6.3 Streamlit App (no-code)](#63-streamlit-app-no-code)
- [7. Key Artifacts & Results](#7-key-artifacts--results)
- [8. Project Structure](#8-project-structure)
- [9. Future Improvements](#9-future-improvements)
- [Built With](#built-with)
- [License](#license)

---

## 1. Data

- **Uplift training**: *Hillstrom Email Marketing* (randomized treatment/control).  
  Output: per-user **uplift** (predicted incremental revenue / probability delta).
- **CLV (optional)**: *UCI Online Retail II* for PNBD/BG-NBD + Gamma-Gamma examples.  
  CLV features can be merged into the uplift model or used for reporting.
- **Serving schema**: enforced by `data/processed/required_features_schema.csv`, which documents the **exact columns** and whether each is **numeric** or **categorical**.

---

## 2. Modeling

- **Uplift**: two random-forest regressors (T-Learner style)
  - `rf_treated.joblib` predicts spend if emailed.
  - `rf_control.joblib` predicts spend if not emailed.
  - **uplift = y1_hat − y0_hat** (expected incremental revenue per contact).
- **Preprocessing**: a One-Hot encoder and column order are frozen in:
  - `preprocess.joblib` (fit on **train only**)
  - `meta.json` → `feature_cols`, `cat_cols`, `num_cols`, `treatment_col`, etc.
- **Notebooks** (reproducible pipeline)
  1) `notebooks/01_clv_eda_and_pnbd.ipynb` – optional CLV/PNBD exploration  
  2) `notebooks/02_uplift_eda_and_models.ipynb` – train uplift models & save artifacts  
  3) `notebooks/03_policy_optimization.ipynb` – profit curves & policy sensitivity  
  4) `notebooks/04_eval_dashboard_prototyping.ipynb` – parity, reports, pack export

---

## 3. Profit & Policy

**Profit framing (per user i):**
\[
\text{profit}_i = x_i \cdot ( \text{uplift}_i \cdot m - c_i )
\]
where \(x_i \in \{0,1\}\) is the contact decision, \(m\) is **unit margin**, and \(c_i\) is **cost per contact** (e.g., $0.05 per email).  

**Policy selector**  
- **bestN** (greedy): sort by uplift and contact top-N s.t. budget/fatigue caps.  
- **Sensitivity**: `policy_sensitivity.csv` explores the **best contact %** vs margin & cost.  
- **Curves**: `policy_curve_email.csv` shows cumulative revenue/cost/profit vs N.

---

## 4. Parity Check (CLI ↔ Notebooks)

To ensure the shipped CLI reproduces notebook results:

- **Rows in common**: 16,000 / 16,000  
- **Pearson corr (uplift_hat vs CLI)**: **1.000**  
- **Top-1,000 overlap**: **1.000**

This confirms artifact/feature ordering and encodings are consistent at serve time.

---

## 5. Local Setup & Runbook

> Works on Windows (Git Bash / PowerShell) and macOS/Linux.

**Python**: 3.10+

```bash
# 1) create & activate venv
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows Git Bash
source .venv/Scripts/activate
# macOS/Linux
# source .venv/bin/activate

# 2) install deps
pip install -r requirements.txt

# (optional) pre-commit
pre-commit install
```
Artifacts you should have (already in this repo after training):
```bash
models/
  preprocess.joblib
  rf_treated.joblib
  rf_control.joblib
  meta.json
tools/score_contacts.py
data/processed/
  hillstrom_uplift_scores_test.csv
  hillstrom_uplift_deciles.csv
  hillstrom_uplift_curve.csv
  policy_curve_email.csv
  policy_sensitivity.csv
  policy_contact_list.csv
  nb_scored_test.csv
  cli_sanity_contacts_test.csv
  required_features_schema.csv
  scored_contacts.csv
  scored_contacts_with_flag.csv
```
## 6. How to Use
6.1 CLI (batch CSV)

Score any CSV that follows the required schema:
```bash
# from repo root
python tools/score_contacts.py \
  --in data/processed/final_contact_list_email.csv \
  --out data/processed/scored_contacts.csv \
  --models models \
  --policy bestN \
  --margin 0.30 \
  --cost 0.05
```
- Adds uplift, y1_hat, y0_hat, expected incremental revenue, and exp_profit_per_contact.

- If your file lacks an ID column, the tool will create row_id as a fallback.

- Use --id_col YOUR_ID to pass an existing identifier.

6.2 FastAPI (programmatic)

Start the API:
```bash
uvicorn src.api.app:app --reload --port 8000
# Swagger: http://127.0.0.1:8000/docs
```
Endpoints

- GET /health – liveness

- POST /score – multipart/form-data with a CSV file (file), and optional margin, cost, topn

Example (curl):
```bash
curl -X POST "http://127.0.0.1:8000/score" \
  -F "file=@data/processed/final_contact_list_email.csv" \
  -F "margin=0.30" \
  -F "cost=0.05" \
  -F "topn=1000"
```
6.3 Streamlit App (no-code)
```bash
streamlit run app/Dashboard.py
# opens http://localhost:8501
```
Upload a CSV with the required features, set margin & cost, pick Top-N, then Score & Simulate to preview revenue / cost / profit.

## 7. Key Artifacts & Results

- Heatmap: data/processed/figs/policy_sensitivity_heatmap.png
  best contact % across grid of (margin × email cost)

- Economics bar chart: data/processed/figs/campaign_economics.png

- Policy pack: data/processed/policy_pack.xlsx
  policy curve, uplift deciles, sensitivity grid, sample contact lists

- Contact pack: data/processed/contact_pack_YYYYMMDD_HHMM.xlsx and matching *.md summary

- Parity (test-only): corr = 1.000, top-1,000 overlap = 1.000

## 8. Project Structure
```bash
clv-uplift-optimizer/
├─ app/
│  └─ Dashboard.py                 # Streamlit UI (upload CSV → simulate profit)
├─ data/
│  ├─ raw/                         # (optional) original CSVs
│  └─ processed/                   # curves, packs, parity, scored outputs
├─ models/
│  ├─ preprocess.joblib            # one-hot encoder (fit on train only)
│  ├─ rf_treated.joblib            # y1_hat model
│  ├─ rf_control.joblib            # y0_hat model
│  └─ meta.json                    # feature order, cat/num lists, config
├─ notebooks/
│  ├─ 01_clv_eda_and_pnbd.ipynb
│  ├─ 02_uplift_eda_and_models.ipynb
│  ├─ 03_policy_optimization.ipynb
│  └─ 04_eval_dashboard_prototyping.ipynb
├─ src/
│  └─ api/
│     └─ app.py                    # FastAPI with /health, /score (multipart CSV)
├─ tools/
│  └─ score_contacts.py            # CLI batch scorer + policy flag
├─ requirements.txt
└─ README.md
```
## 9. Future Improvements

- True ILP optimizer: add budget/fatigue constraints as a formal integer program.

- Calibration: map uplift to probability × margin with uncertainty bands.

- Champion/Challenger: CATBoost uplift, meta-learners (X-/R-/DR-Learner).

- Monitoring: data drift & policy ROI tracking; weekly retrain jobs.

- Docker & CI: reproducible builds and one-command deploy.

## Built With
Python 3.10 · pandas · scikit-learn · numpy · matplotlib · Streamlit · FastAPI · Uvicorn

## License
MIT

