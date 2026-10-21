# ingestor/sophos.py
import re
from datetime import datetime

PRIORITY = re.compile(r"^<\d+>")
KV       = re.compile(r'(\w+)=("[^"]*"|\S+)')

MAPPING = {
    "properties": {
        "timestamp":    {"type": "date"},
        "host":         {"type": "keyword"},
        "date":         {"type": "keyword"},
        "time":         {"type": "keyword"},
        "log_type":     {"type": "keyword"},
        "subtype":      {"type": "keyword"},
        "src_ip":       {"type": "keyword"},
        "dst_ip":       {"type": "keyword"},
        "src_port":     {"type": "integer"},
        "dst_port":     {"type": "integer"},
        "proto":        {"type": "keyword"},
        "rule":         {"type": "keyword"},
        "user":         {"type": "keyword"},
        "app":          {"type": "keyword"},
        "severity":     {"type": "keyword"},
        "msg":          {"type": "text"},
        "message_text": {"type": "text"},
        "embedding":    {"type": "dense_vector", "dims": 384,
                         "index": True, "similarity": "cosine"},
    }
}

def _timestamp(s):
    try:
        return datetime.strptime(s, "%b %d %H:%M:%S").replace(
            year=datetime.now().year).isoformat()
    except ValueError:
        return datetime.now().isoformat()

def parse(line):
    """<PRI>Mon dd hh:mm:ss host tag: key=value ... -> flat doc dict"""
    rest  = PRIORITY.sub("", line, count=1)
    ts    = rest[:15]
    rest  = rest[16:].strip() if len(rest) > 16 else rest
    host  = rest.split(" ", 1)[0]
    tail  = rest.partition(": ")[2]
    doc   = {"timestamp": _timestamp(ts), "host": host}
    for k, v in KV.findall(tail or rest):
        doc[k] = v.strip('"')
    return doc

def _addr(ip, port): return f"{ip}:{port}" if port else ip

def to_text(doc):
    """flat sentence for embedding / semantic search"""
    bits = [" ".join(x for x in (doc.get("log_type"), doc.get("subtype")) if x)]
    if doc.get("src_ip"): bits.append("from " + _addr(doc["src_ip"], doc.get("src_port")))
    if doc.get("dst_ip"): bits.append("to " + _addr(doc["dst_ip"], doc.get("dst_port")))
    if doc.get("proto"):  bits.append(f"over {doc['proto']}")
    if doc.get("app"):    bits.append(f"app {doc['app']}")
    if doc.get("user"):   bits.append(f"user {doc['user']}")
    if doc.get("severity"): bits.append(f"severity {doc['severity']}")
    if doc.get("msg"):    bits.append(doc["msg"])
    return " ".join(bits)
