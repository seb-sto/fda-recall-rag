import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="FDA Recall RAG", page_icon="🔍")
st.title("FDA Recall & Compliance Assistant")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Filters")
    source_type = st.selectbox("Source type", ["(any)", "regulation", "food", "drug", "device"])
    cfr_part = st.text_input("CFR part (e.g. 117)")
    state = st.text_input("State (e.g. CA)")
    n_results = st.slider("Number of sources", 1, 10, 5)

for past_q, past_a, past_sources in st.session_state.history:
    with st.chat_message("user"):
        st.write(past_q)
    with st.chat_message("assistant"):
        st.write(past_a)
        with st.expander("Sources"):
            for s in past_sources:
                citation = s["metadata"].get("citation") or s["metadata"].get("recall_number")
                st.markdown(f"**{citation}** (rerank score: {s.get('rerank_score', 'n/a')})")
                st.caption(s["text"][:300])

question = st.chat_input("Ask a question about FDA regulations or recalls...")

if question:
    filters = {}
    if source_type != "(any)":
        filters["source_type"] = source_type
    if cfr_part.strip():
        filters["cfr_part"] = int(cfr_part)
    if state.strip():
        filters["state"] = state

    payload = {"question": question, "session_id": st.session_state.session_id, "n_results": n_results}
    if filters:
        payload["filters"] = filters

    with st.spinner("Thinking..."):
        resp = requests.post(f"{API_URL}/query", json=payload, headers={"X-API-Key": API_KEY})

    if resp.status_code == 200:
        data = resp.json()
        st.session_state.history.append((question, data["answer"], data["sources"]))
        st.rerun()
    else:
        st.error(f"Error {resp.status_code}: {resp.text}")
