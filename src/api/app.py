# src/api/app.py
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd, joblib, json
from pathlib import Path
from io import BytesIO

APP_ROOT = Path(__file__).parents[2]
MODELS   = APP_ROOT / "models"

enc   = joblib.load(MODELS / "preprocess.joblib")
reg_t = joblib.load(MODELS / "rf_treated.joblib")
reg_c = joblib.load(MODELS / "rf_control.joblib")
meta  = json.load(open(MODELS / "meta.json"))

app = FastAPI(title="CLV + Uplift + Policy API")

@app.get("/health")
def health():
    return {"status": "ok"}

def score_core(df: pd.DataFrame, margin: float, cost: float, topn: int):
    feat_cols = meta["feature_cols"]
    X = df[feat_cols].copy()
    for c in meta["cat_cols"]:
        if c in X.columns: X[c] = X[c].astype(str)
    A  = enc.transform(X)
    y1 = reg_t.predict(A)
    y0 = reg_c.predict(A)
    uplift = y1 - y0

    out = pd.DataFrame({
        "row_id": df.get(meta.get("id_fallback","row_id"), pd.RangeIndex(len(df))),
        "uplift_hat": uplift
    }).sort_values("uplift_hat", ascending=False)

    out["exp_incremental_revenue"] = out["uplift_hat"]
    out["exp_profit_per_contact"]  = margin*out["exp_incremental_revenue"] - cost
    out["rank"] = range(1, len(out)+1)
    top = out.head(topn).reset_index(drop=True)
    summary = {
        "contacts": int(len(top)),
        "expected_revenue": float(top["exp_incremental_revenue"].sum()),
        "expected_cost": float(cost*len(top)),
        "expected_profit": float((margin*top["exp_incremental_revenue"] - cost).sum())
    }
    return top, summary

@app.post("/score")
async def score_csv(
    file: UploadFile = File(...),
    margin: float = Query(0.30),
    cost: float = Query(0.05),
    topn: int = Query(1000)
):
    raw = await file.read()
    df  = pd.read_csv(BytesIO(raw))
    top, summary = score_core(df, margin, cost, topn)
    return JSONResponse({"summary": summary, "top": top.to_dict(orient="records")})

