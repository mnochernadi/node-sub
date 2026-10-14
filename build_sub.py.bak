"""Build a subscription from your own nodes plus clean Cloudflare IPs.

- Your own configs (OWN_NODES secret) are included as they are.
- From the lists in sources.txt only IP addresses are read, and only the ones inside
  Cloudflare's published ranges are kept. Configs in those lists are never used.
- Each of your own TLS+WS configs that uses a domain gets one copy per clean IP: the address
  becomes the IP, while host/sni stay on your domain.
Outputs: docs/sub.txt (plain) and docs/sub_base64.txt (base64).
"""
import base64, ipaddress, json, os, re, urllib.parse, urllib.request

UA = {"User-Agent": "sub-builder/2.0"}
CF_LISTS = ["https://www.cloudflare.com/ips-v4", "https://www.cloudflare.com/ips-v6"]


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def b64decode(s):
    s = s.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", errors="ignore")


def is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def cloudflare_networks():
    nets = []
    for url in CF_LISTS:
        try:
            nets += [ipaddress.ip_network(x) for x in fetch(url).split() if x]
        except Exception as e:
            print("cloudflare ranges fetch failed:", e)
    return nets


def source_ips(text):
    found = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("vmess://"):
            try:
                found.add(str(json.loads(b64decode(line[8:])).get("add", "")))
            except Exception:
                pass
        else:
            m = re.search(r"@(\[[^\]]+\]|[^:/?#]+):\d+", line)
            if m:
                found.add(m.group(1).strip("[]"))
    return found


def clean_ips(nets):
    ips = set()
    for url in [l.strip() for l in open("sources.txt") if l.strip() and not l.startswith("#")]:
        try:
            cands = source_ips(fetch(url))
        except Exception as e:
            print("skip", url, e)
            continue
        for c in cands:
            if is_ip(c) and any(ipaddress.ip_address(c) in n for n in nets):
                ips.add(c)
    return sorted(ips)


def label_of(text):
    return urllib.parse.unquote(text) if text else "node"


def vless_trojan_variants(link, ips):
    p = urllib.parse.urlsplit(link)
    q = urllib.parse.parse_qs(p.query)
    if q.get("security", [""])[0] != "tls" or q.get("type", [""])[0] != "ws":
        return []
    host = p.hostname or ""
    if not host or is_ip(host):
        return []
    query = p.query if "sni" in q else (p.query + "&sni=" + host if p.query else "sni=" + host)
    out = []
    for ip in ips:
        addr = f"[{ip}]" if ":" in ip else ip
        netloc = p.netloc.replace(host, addr, 1)
        frag = urllib.parse.quote(f"{label_of(p.fragment)} CF {ip}", safe="")
        out.append(urllib.parse.urlunsplit((p.scheme, netloc, p.path, query, frag)))
    return out


def vmess_variants(link, ips):
    d = json.loads(b64decode(link[8:]))
    if d.get("tls") != "tls" or d.get("net") != "ws":
        return []
    host = d.get("add", "")
    if not host or is_ip(host):
        return []
    out = []
    for ip in ips:
        c = dict(d)
        c.setdefault("sni", host)
        if not c.get("sni"):
            c["sni"] = host
        c["add"] = ip
        c["ps"] = f"{label_of(d.get('ps', 'node'))} CF {ip}"
        out.append("vmess://" + base64.b64encode(json.dumps(c).encode()).decode())
    return out


def main():
    own = [l.strip() for l in os.environ.get("OWN_NODES", "").splitlines() if l.strip()]
    ips = clean_ips(cloudflare_networks())
    print("clean cloudflare IPs found:", len(ips))

    result, seen = [], set()

    def add(link):
        key = link.split("#")[0]
        if key not in seen:
            seen.add(key)
            result.append(link)

    for link in own:
        add(link)
    for link in own:
        try:
            variants = vmess_variants(link, ips) if link.startswith("vmess://") else \
                vless_trojan_variants(link, ips) if link.startswith(("vless://", "trojan://")) else []
        except Exception as e:
            print("skip variant:", e)
            variants = []
        for v in variants:
            add(v)

    os.makedirs("docs", exist_ok=True)
    plain = "\n".join(result) + "\n"
    open("docs/sub.txt", "w", encoding="utf-8").write(plain)
    open("subscription.txt", "w", encoding="utf-8").write(plain)
    open("docs/sub_base64.txt", "w", encoding="utf-8").write(base64.b64encode(plain.encode()).decode())
    print(f"own configs: {len(own)}, total lines: {len(result)}")


if __name__ == "__main__":
    main()
