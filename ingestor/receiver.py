# ingestor/receiver.py
import os, queue, socket, threading, time
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
from sophos import parse, to_text, MAPPING     # MAPPING = the mappings dict from create_index.py

ES_URL     = os.getenv("ES_URL", "http://es:9200")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 64))
FLUSH_SECS = float(os.getenv("FLUSH_SECS", 2))
INDEX      = "sophos-logs"

es    = Elasticsearch(ES_URL)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

if not es.indices.exists(index=INDEX):
    es.indices.create(index=INDEX, mappings=MAPPING)

q = queue.Queue(maxsize=20000)
dropped = 0

def listen():
    global dropped
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.bind(("0.0.0.0", 5514))
    print("listening on udp/5514")
    while True:
        data, _ = sock.recvfrom(65535)
        try:
            q.put_nowait(data.decode(errors="replace"))
        except queue.Full:
            dropped += 1

def flush(lines):
    docs  = [parse(l) for l in lines]
    texts = [to_text(d) for d in docs]
    vecs  = model.encode(texts, batch_size=64, normalize_embeddings=True)
    helpers.bulk(es, (
        {"_index": INDEX,
         "_source": {**d, "message_text": t, "embedding": v.tolist()}}
        for d, t, v in zip(docs, texts, vecs)
    ))
    print(f"indexed {len(docs)} (queue={q.qsize()}, dropped={dropped})")

threading.Thread(target=listen, daemon=True).start()

while True:
    batch, deadline = [], time.time() + FLUSH_SECS
    while len(batch) < BATCH_SIZE and time.time() < deadline:
        try:
            batch.append(q.get(timeout=max(0.01, deadline - time.time())))
        except queue.Empty:
            break
    if batch:
        flush(batch)