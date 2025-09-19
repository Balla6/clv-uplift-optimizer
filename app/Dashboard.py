import streamlit as st

st.set_page_config(page_title="CLV + Uplift + Policy Optimizer", layout="wide")
st.title("CLV + Uplift + Contact-Policy Optimizer")
st.write("""
Use the controls to set budget, unit margin, and fatigue cap, then preview expected profit vs. baselines.
(This is a skeleton — models & optimizer will be wired in later steps.)
""")
budget = st.number_input("Budget (emails per week)", value=50000, step=1000)
margin = st.number_input("Unit margin ($ per conversion)", value=25, step=1)
cost = st.number_input("Cost per contact ($)", value=0.04, step=0.01, format="%.2f")
fatigue = st.slider("Fatigue cap (contacts/user/week)", 0, 7, 2)
st.button("Simulate Policy (placeholder)")
