# generator/generator.py (bottom of the file)
import os, random, socket, time
from datetime import datetime

HOST = os.getenv("SYSLOG_HOST", "ingestor")
PORT = int(os.getenv("SYSLOG_PORT", 5514))
RATE = float(os.getenv("RATE", 8))

CORP = "corp.local"

USERS = ["jsmith", "a.lee", "m.torres", "r.dubois", "admin"]
IPS   = ["10.0.12.31", "10.0.12.45", "10.0.12.58", "10.0.12.77", "10.0.12.10"]

WEB = {"news": ["www.bbc.com", "www.cnn.com"],
       "shopping": ["www.amazon.com", "www.etsy.com"],
       "search": ["www.google.com", "www.bing.com"],
       "social_media": ["www.linkedin.com", "www.reddit.com"],
       "banking": ["secure.chase.com", "www.paypal.com"]}

def wan(): return f"{random.choice([45, 91, 185, 198, 203])}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
def lan(): return f"10.0.12.{random.randint(10, 90)}"

# each function returns (host, tag, log_type, subtype, kv) for one normal event
def mail():
    u = random.choice(USERS)
    if random.random() < 0.5:
        return ("mx-postfix-01", "postfix", "Mail", "Login",
                dict(device="postfix", action="login", user=u, src_ip=IPS[USERS.index(u)],
                     app="webmail", msg=f"{u} logged into webmail"))
    folder = random.choice(["INBOX", "Sent", "Archive", "Trash"])
    n = random.randint(1, 30)
    return ("mx-postfix-01", "postfix", "Mail", "Read",
            dict(device="postfix", action="read", user=u, src_ip=IPS[USERS.index(u)],
                 app="webmail", folder=folder, msg=f"{u} read {n} messages from {folder}"))

def mail_delivery():
    u = random.choice(USERS); sender = random.choice(["newsletter@vendor.com", "billing@supplier.net", "colleague@" + CORP])
    return ("mx-postfix-01", "postfix", "Mail", "Delivered",
            dict(device="postfix", action="deliver", user=u, recipient=f"{u}@{CORP}", sender=sender,
                 subject=random.choice(["Monthly report", "Invoice 2026-04", "Meeting notes"]),
                 msg=f"Message from {sender} delivered to {u}"))

def mail_send():
    u = random.choice(USERS)
    return ("mx-postfix-01", "postfix", "Mail", "Send",
            dict(device="postfix", action="send", user=u, src_ip=IPS[USERS.index(u)],
                 sender=f"{u}@{CORP}", recipient=f"colleague@{CORP}", subject="Re: status",
                 bytes=str(random.randint(10_000, 2_000_000)), msg=f"{u} sent a message"))

def archive():
    u = random.choice(USERS)
    act = random.choice(["login", "search", "view", "download"])
    kv = dict(device="archive", action=act, user=u, src_ip=IPS[USERS.index(u)])
    if act == "login":
        return ("app-archive-01", "archive", "App", "Login", {**kv, "msg": f"{u} logged into the archive application"})
    if act == "search":
        return ("app-archive-01", "archive", "App", "Search", {**kv, "query": random.choice(["budget", "policy", "invoices", "contracts"]),
                "msg": f"{u} searched the archive"})
    if act == "view":
        doc = random.choice(["Q3-budget.pdf", "hr-policy-2026.docx", "client-list.xlsx", "roadmap.pptx"])
        return ("app-archive-01", "archive", "App", "View", {**kv, "doc": doc, "msg": f"{u} viewed document {doc}"})
    doc = random.choice(["Q3-budget.pdf", "hr-policy-2026.docx", "client-list.xlsx", "roadmap.pptx"])
    return ("app-archive-01", "archive", "App", "Download", {**kv, "doc": doc,
            "bytes": str(random.randint(50_000, 8_000_000)), "msg": f"{u} downloaded document {doc} from the archive"})

def web():
    u = random.choice(USERS); cat = random.choice(list(WEB)); domain = random.choice(WEB[cat])
    return ("sophos-fw-01", "sophos", "WebFilter", "Allowed",
            dict(device="sophos_fw", action="allow", user=u, src_ip=IPS[USERS.index(u)],
                 domain=domain, app="HTTPS", dst_ip=wan(), msg=f"{u} browsed {domain} (category '{cat}')"))

def web_blocked():
    u = random.choice(USERS); cat = random.choice(["gambling", "phishing", "malware", "file sharing"])
    return ("sophos-fw-01", "sophos", "WebFilter", "Blocked",
            dict(device="sophos_fw", action="deny", user=u, src_ip=IPS[USERS.index(u)],
                 domain=random.choice(["bet-online.example", "free-movies.example", "dropfile.example"]),
                 app="HTTPS", dst_ip=wan(), msg=f"{u} tried to access a site in category '{cat}' — blocked"))

def fw_permit():
    return ("cisco-fw-01", "cisco", "Firewall", "Connection",
            dict(device="cisco_fw", action="permit", src_ip=lan(), dst_ip=wan(),
                 protocol=random.choice(["TCP", "UDP"]), dst_port=random.choice(["80", "443", "53", "22"]),
                 msg="Outbound connection permitted inside to outside"))

def fw_deny():
    return ("cisco-fw-01", "cisco", "Firewall", "Connection",
            dict(device="cisco_fw", action="deny", src_ip=wan(), dst_ip=lan(),
                 protocol="TCP", dst_port=random.choice(["3389", "445", "23"]),
                 msg="Inbound connection denied at perimeter"))

def vpn():
    u = random.choice(USERS)
    return ("sophos-fw-01", "sophos", "VPN", "TunnelUp",
            dict(device="sophos_fw", action="login", user=u, src_ip=wan(), dst_ip=lan(),
                 protocol="UDP", msg=f"{u} opened an SSL-VPN tunnel"))

def login_fail():
    u = random.choice(USERS)
    return ("app-archive-01", "archive", "App", "Login",
            dict(device="archive", action="login_failed", user=u, src_ip=lan(),
                 msg=f"{u} login failed: invalid credentials"))

def ips():
    return ("sophos-fw-01", "sophos", "IPS", "Signature",
            dict(device="sophos_fw", action="alert", src_ip=wan(), dst_ip=lan(),
                 severity=random.choice(["medium", "high", "critical"]),
                 msg=random.choice(["Port scan detected from external source",
                                    "SQL injection attempt detected",
                                    "Brute force login attempt detected"])))

# weight list: mostly normal traffic, occasional security events
EMITTERS = [mail, mail, mail_delivery, mail_send, archive, archive, archive,
            web, web, web, web_blocked, fw_permit, fw_permit, fw_deny, vpn,
            login_fail, ips]

def event(ts):
    host, tag, log_type, subtype, kv = random.choice(EMITTERS)()
    d = {"date": ts.strftime("%Y-%m-%d"), "time": ts.strftime("%H:%M:%S"),
         "log_type": log_type, "subtype": subtype, **kv}
    payload = " ".join(f'{k}="{v}"' if " " in str(v) else f"{k}={v}" for k, v in d.items())
    return f"<30>{ts:%b %d %H:%M:%S} {host} {tag}: {payload}"

def generate(n):
    for _ in range(n):
        yield event(datetime.now())

def main():
    time.sleep(10)                         # let the ingestor load the model
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        line = next(generate(1))           # one log, timestamp = now
        sock.sendto(line.encode(), (HOST, PORT))
        time.sleep(1 / RATE)

main()
