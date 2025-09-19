# Profit-Driven CLV + Uplift + Contact-Policy Optimizer

**Goal:** Maximize expected profit by combining CLV estimation with uplift modeling and a budgeted contact policy optimizer.

## Datasets
- **CLV:** UCI Online Retail II (transactions 2009–2011).
- **Uplift:** Hillstrom Email Marketing (randomized treatment vs control). Optional: Criteo Uplift for scale.

## Methods
- **CLV:** BG/NBD + Gamma-Gamma (lifetimes); PNBD (PyMC-Marketing)
- **Uplift:** T-/X-learner, Uplift Trees (scikit-uplift, causalml); metrics: AUUC, Qini, uplift@k
- **Policy:** ILP / greedy to allocate contacts under budget and fatigue constraints.

## Profit Framing
For each candidate customer \(i\):
\[ \text{profit}_i = x_i (u_i \cdot m - c_i) \]
where \(x_i\in\{0,1\}\) is contact decision, \(u_i\) is predicted uplift (incremental conversion probability), `m` is unit margin, and `c_i` is contact cost.

## Quickstart
```bash
# 1) create & activate a virtual env (macOS/Linux)
python -m venv .venv && source .venv/bin/activate
# (Windows PowerShell)
# python -m venv .venv; .\.venv\Scripts\Activate.ps1

# 2) install deps
pip install -r requirements.txt

# 3) (optional) set up pre-commit hooks
pre-commit install

# 4) run notebooks
jupyter lab notebooks/01_clv_eda_and_pnbd.ipynb
```

## Project Structure
See the repository tree.

## Results
We will report AUUC, incremental revenue, ROI, and policy feasibility here after experiments.

## License
This repo is for educational/portfolio use.
