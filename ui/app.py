import os, pandas as pd
import streamlit as st

BASE = os.path.join(os.environ["HOME"], "WANSTAGE")
st.title("WANSTAGE Dashboard")
log = os.path.join(BASE, "logs", "revenue_log.csv")
st.caption(f"Base: {BASE}")
st.info("revenue_log.csv があれば下に表示")
if os.path.exists(log):
    st.dataframe(pd.read_csv(log).tail(50))
