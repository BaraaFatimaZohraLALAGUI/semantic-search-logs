# ingestor/sophos.py
import re
from datetime import datetime

PRIORITY = re.compile(r"^<\d+>")
KV       = re.compile(r'(\w+)=("[^"]*"|\S+)')

# device field value -> target index
DEVICE_INDEX = {
    "postfix":   "postfix-logs",
    "archive":   "archive-logs",
    "sophos_fw": "sophos-logs",
    "cisco_fw":  "cisco-logs",
}
DEFAULT_INDEX = "other-logs"

# fields present in every index (same type across all, so cross-index queries merge cleanly)
COMMON = {
    "timestamp":    {"type": "date"},
    "host":         {"type": "keyword"},
    "date":         {"type": "keyword"},
    "time":         {"type": "keyword"},
    "device":       {"type": "keyword"},
    "log_type":     {"type": "keyword"},
    "subtype":      {"type": "keyword"},
    "action":       {"type": "keyword"},
    "user":         {"type": "keyword"},
    "src_ip":       {"type": "keyword"},
    "dst_ip":       {"type": "keyword"},
    "src_port":     {"type": "integer"},
    "dst_port":     {"type": "integer"},
    "proto":        {"type": "keyword"},
    "protocol":     {"type": "keyword"},
    "severity":     {"type": "keyword"},
    "msg":          {"type": "text"},
    "message_text": {"type": "text"},
    "embedding":    {"type": "dense_vector", "dims": 384,
                     "index": True, "similarity": "cosine"},
}

# device-specific fields, only mapped in the index that uses them
EXTRA = {
    "postfix-logs": {"app": {"type": "keyword"}, "folder": {"type": "keyword"},
                     "sender": {"type": "keyword"}, "recipient": {"type": "keyword"},
                     "subject": {"type": "text"}, "bytes": {"type": "long"}},
    "archive-logs": {"doc": {"type": "keyword"}, "query": {"type": "text"},
                     "bytes": {"type": "long"}},
    "sophos-logs":  {"domain": {"type": "keyword"}, "app": {"type": "keyword"},
                     "rule": {"type": "keyword"}},
    "cisco-logs":   {"rule": {"type": "keyword"}},
    "other-logs":   {},
}

# per-index mappings: common fields + that index's extras
MAPPINGS = {idx: {"properties": {**COMMON, **fields}}
            for idx, fields in EXTRA.items()}

def index_for(doc):
    return DEVICE_INDEX.get(doc.get("device"), DEFAULT_INDEX)

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
    bits = []
    if doc.get("device"): bits.append(f"[{doc['device']}]")
    head = " ".join(x for x in (doc.get("log_type"), doc.get("subtype")) if x)
    if head: bits.append(head)
    if doc.get("action"): bits.append(f"action {doc['action']}")
    if doc.get("user"):   bits.append(f"user {doc['user']}")
    if doc.get("src_ip"): bits.append("from " + _addr(doc["src_ip"], doc.get("src_port")))
    if doc.get("dst_ip"): bits.append("to " + _addr(doc["dst_ip"], doc.get("dst_port")))
    if doc.get("proto"):  bits.append(f"over {doc['proto']}")
    if doc.get("protocol"): bits.append(f"over {doc['protocol']}")
    if doc.get("app"):    bits.append(f"app {doc['app']}")
    if doc.get("domain"): bits.append(f"website {doc['domain']}")
    if doc.get("sender"): bits.append(f"email from {doc['sender']}")
    if doc.get("recipient"): bits.append(f"to {doc['recipient']}")
    if doc.get("subject"): bits.append(f"subject {doc['subject']}")
    if doc.get("doc"):    bits.append(f"file {doc['doc']}")
    if doc.get("query"):  bits.append(f"searched {doc['query']}")
    if doc.get("bytes"):  bits.append(f"{int(doc['bytes']) // 1024} KB")
    if doc.get("severity"): bits.append(f"severity {doc['severity']}")
    if doc.get("msg"):    bits.append(doc["msg"])
    return " ".join(bits)
