# app/Dashboard.py
import streamlit as st, requests, pandas as pd

st.set_page_config(page_title="CLV + Uplift + Policy Optimizer", layout="wide")
st.title("CLV + Uplift + Contact-Policy Optimizer")

st.write("Upload a CSV with the required columns, set margin & cost, and preview profit.")

margin = st.number_input("Unit margin ($ per conversion)", value=25.0, step=0.5)
cost   = st.number_input("Cost per contact ($)", value=0.05, step=0.01, format="%.2f")
topn   = st.number_input("Top-N contacts", value=1000, step=100, min_value=100)

file = st.file_uploader("Upload features CSV", type=["csv"])
if st.button("Score & simulate") and file is not None:
    files = {"file": ("input.csv", file.getvalue(), "text/csv")}
    params = {"margin": margin, "cost": cost, "topn": topn}
    r = requests.post("http://127.0.0.1:8000/score", files=files, params=params, timeout=60)
    if r.ok:
        res = r.json()
        st.subheader("Summary")
        st.json(res["summary"])
        st.subheader("Top contacts")
        st.dataframe(pd.DataFrame(res["top"]).head(20))
    else:
        st.error(f"API error: {r.status_code} {r.text}")
