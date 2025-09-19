
import argparse, json, joblib, numpy as np, pandas as pd
from pathlib import Path

def load_models(model_dir: Path):
    pre = joblib.load(model_dir / "preprocess.joblib")
    reg_t = joblib.load(model_dir / "rf_treated.joblib")
    reg_c = joblib.load(model_dir / "rf_control.joblib")
    meta = json.loads((model_dir / "meta.json").read_text(encoding="utf-8"))
    return pre, reg_t, reg_c, meta

def prepare_features(df: pd.DataFrame, meta: dict):
    # ensure feature columns exist
    for c in meta["feature_cols"]:
        if c not in df.columns:
            df[c] = np.nan
    X = df[meta["feature_cols"]].copy()
    # keep types friendly
    for c in X.columns:
        if X[c].dtype == "object":
            X[c] = X[c].astype("string")
    return X

def score(input_csv, output_csv, model_dir, margin, cost, policy, topn=None, id_col=None):
    model_dir = Path(model_dir)
    pre, reg_t, reg_c, meta = load_models(model_dir)

    df = pd.read_csv(input_csv)
    # Choose an ID column or create one
    if id_col and id_col in df.columns:
        ids = df[id_col].copy()
    elif meta.get("id_fallback") in df.columns:
        ids = df[meta["id_fallback"]].copy()
    else:
        ids = pd.Series(np.arange(len(df)), name=meta.get("id_fallback","row_id"))
        df[ids.name] = ids

    X = prepare_features(df, meta)
    A = pre.transform(X)

    y1_hat = reg_t.predict(A)
    y0_hat = reg_c.predict(A)
    uplift = y1_hat - y0_hat

    out = pd.DataFrame({
        "row_id": ids.values,
        "y1_hat": y1_hat,
        "y0_hat": y0_hat,
        "uplift_hat": uplift
    }).sort_values("uplift_hat", ascending=False).reset_index(drop=True)

    out["exp_incremental_revenue"] = out["uplift_hat"]
    out["exp_profit_per_contact"]  = margin*out["uplift_hat"] - cost

    # decide contacts
    if policy == "pos":
        chosen = out.loc[out["exp_profit_per_contact"] > 0].copy()
    elif policy == "bestN":
        # maximize expected profit curve
        cg = out["uplift_hat"].cumsum()
        n  = np.arange(1, len(out)+1)
        profit_curve = margin*cg - cost*n
        best_n = int(np.argmax(profit_curve) + 1)
        if topn is not None:
            best_n = int(topn)
        chosen = out.head(best_n).copy()
    else:
        raise ValueError("policy must be 'pos' or 'bestN'")

    chosen["rank"] = np.arange(1, len(chosen)+1)
    cols = ["row_id","rank","uplift_hat","y1_hat","y0_hat","exp_incremental_revenue","exp_profit_per_contact"]
    chosen[cols].to_csv(output_csv, index=False)

    total_rev  = float(chosen["exp_incremental_revenue"].sum())
    total_cost = float(cost*len(chosen))
    total_prof = float(margin*total_rev - total_cost)

    print(f"Contacts: {len(chosen)}  |  Expected revenue: {total_rev:,.2f}  |  Cost: {total_cost:,.2f}  |  Profit: {total_prof:,.2f}")
    print("Saved:", output_csv)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Score uplift and produce a contact list.")
    p.add_argument("--in", dest="input_csv",  required=True)
    p.add_argument("--out", dest="output_csv", required=True)
    p.add_argument("--models", default="models")
    p.add_argument("--margin", type=float, default=0.30)
    p.add_argument("--cost",   type=float, default=0.05)
    p.add_argument("--policy", choices=["pos","bestN"], default="pos")
    p.add_argument("--topn", type=int, default=None, help="optional, only for policy=bestN")
    p.add_argument("--id_col", default=None)
    args = p.parse_args()
    score(args.input_csv, args.output_csv, args.models, args.margin, args.cost, args.policy, args.topn, args.id_col)
