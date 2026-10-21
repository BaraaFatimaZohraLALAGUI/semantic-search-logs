# generator/generator.py (bottom of the file)
import os, random, socket, time
from datetime import datetime

HOST = os.getenv("SYSLOG_HOST", "ingestor")
PORT = int(os.getenv("SYSLOG_PORT", 5514))
RATE = float(os.getenv("RATE", 20))

USERS = ["jsmith", "a.lee", "admin", "svc_backup", "m.torres"]

def lan(): return f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}"
def wan(): return f"{random.choice([45, 91, 185, 198, 203])}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def firewall():
    ok = random.random() < 0.7
    return {"log_type": "Firewall", "subtype": "Accept" if ok else "Deny",
            "src_ip": lan(), "dst_ip": wan(),
            "src_port": str(random.randint(49152, 65535)),
            "dst_port": random.choice(["80", "443", "22", "53", "3389", "25"]),
            "proto": "TCP", "rule": "LAN-to-WAN" if ok else "default-deny",
            "msg": "Outbound connection allowed by policy" if ok
                   else "Connection blocked by rule default-deny"}

def ips():
    return {"log_type": "IPS", "subtype": "Signature",
            "src_ip": wan(), "dst_ip": lan(),
            "src_port": str(random.randint(1024, 65535)),
            "dst_port": random.choice(["22", "80", "443", "3389", "445"]),
            "proto": "TCP", "severity": random.choice(["medium", "high", "critical"]),
            "msg": random.choice(["SQL injection attempt detected",
                                  "Remote code execution attempt detected",
                                  "Port scan detected",
                                  "Brute force login attempt detected"])}

def malware():
    return {"log_type": "AntiMalware", "subtype": "Blocked",
            "src_ip": lan(), "dst_ip": wan(), "proto": "TCP",
            "app": random.choice(["HTTP", "HTTPS", "SMTP"]), "severity": "high",
            "msg": "Outbound connection blocked: "
                   + random.choice(["Trojan.JS.Agent", "Mal/EncPk-Gen", "W97M/DocDl", "HTML/Phish.Gen"])
                   + " detected and quarantined"}

def webfilter():
    return {"log_type": "WebFilter", "subtype": "Blocked",
            "src_ip": lan(), "dst_ip": wan(), "app": random.choice(["HTTP", "HTTPS"]),
            "user": random.choice(USERS),
            "msg": "Access to website in category '"
                   + random.choice(["gambling", "adult content", "phishing", "social media", "file sharing"])
                   + "' blocked"}

def login():
    ok = random.random() < 0.6
    return {"log_type": "Authentication", "subtype": "LoginSuccess" if ok else "LoginFailure",
            "user": random.choice(USERS), "src_ip": lan(),
            "app": random.choice(["SSL-VPN", "WebAdmin", "SSH"]),
            "msg": "User logged in successfully" if ok
                   else "User login failed: invalid credentials"}

def vpn():
    return {"log_type": "VPN", "subtype": "TunnelUp",
            "user": random.choice(USERS), "src_ip": wan(), "dst_ip": lan(), "proto": "UDP",
            "msg": "IPsec tunnel established with remote gateway"}

def ssh_brute():
    return {"log_type": "IPS", "subtype": "SSHBruteForce",
            "src_ip": wan(), "dst_ip": lan(), "dst_port": "22", "proto": "TCP",
            "severity": "high",
            "msg": "Repeated SSH login failures from same source, connection dropped"}

SCENARIOS = [firewall, firewall, firewall, ips, malware, webfilter, login, vpn, ssh_brute]

def event(ts):
    kv = {"date": ts.strftime("%Y-%m-%d"), "time": ts.strftime("%H:%M:%S"),
          **random.choice(SCENARIOS)()}
    payload = " ".join(f'{k}="{v}"' if " " in str(v) else f"{k}={v}" for k, v in kv.items())
    return f"<30>{ts:%b %d %H:%M:%S} sophos-sim sophos: {payload}"

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
