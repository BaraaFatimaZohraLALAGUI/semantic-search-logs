# app/ui.py
import os
import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

ES_URL = os.getenv("ES_URL", "http://es:9200")
INDEX  = os.getenv("INDEX_PATTERN", "*-logs")   # searches every per-source index at once

@st.cache_resource
def load():
    return (Elasticsearch(ES_URL),
            SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2"))

es, model = load()

st.set_page_config(page_title="Semantic log search", layout="wide")
st.title("Semantic log search")
st.caption(f"index: {INDEX} · all-MiniLM-L6-v2 · kNN runs in Elasticsearch")

q = st.text_input("Ask a question about the logs",
                   placeholder="did anyone try to break in?")
u = st.text_input("Filter by user (optional)", placeholder="jsmith")
k = st.slider("Results", 3, 25, 8)

if q:
    try:
        vector = model.encode(q, normalize_embeddings=True).tolist()
        body = {"knn": {"field": "embedding", "query_vector": vector,
                        "k": k, "num_candidates": 100}}
        if u:
            body["query"] = {"term": {"user": u}}
        res = es.search(index=INDEX, size=k, **body)
        hits = res["hits"]["hits"]
    except Exception as e:
        st.error(f"search failed: {e}")
        hits = []

    if not hits:
        st.info("no matches")

    for h in hits:
        d = h["_source"]
        head = " / ".join(x for x in (d.get("device"), d.get("log_type"), d.get("subtype")) if x)
        c1, c2, c3 = st.columns([4, 1, 5])
        c1.markdown(f"**{head}**")
        c1.caption(f'{d.get("timestamp", "")} · {d.get("user", "—")}')
        c2.metric("score", f"{h['_score']:.3f}")
        c3.write(d.get("message_text", ""))
        with st.expander("raw document"):
            st.json(d)

    st.divider()

total = es.count(index=INDEX)["count"]
st.caption(f"{total} logs indexed")
