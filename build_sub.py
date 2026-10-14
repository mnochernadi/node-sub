"""Collect share links from public sources and your own nodes, dedupe, and write subscription files.

Own nodes come from the OWN_NODES env var (set as a GitHub Actions secret), never from the repo.
Outputs: docs/sub.txt (plain links) and docs/sub_base64.txt (base64, the usual subscription format).
"""
import base64, os, re, urllib.request

PROTOCOLS = ("vless://", "vmess://", "trojan://", "ss://")
UA = {"User-Agent": "sub-builder/1.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def maybe_decode(text):
    """Some sources publish the whole list base64-encoded."""
    stripped = "".join(text.split())
    if stripped and not any(stripped.startswith(p) for p in PROTOCOLS):
        try:
            return base64.b64decode(stripped + "=" * (-len(stripped) % 4)).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return text


def extract(text):
    out = []
    for line in maybe_decode(text).splitlines():
        line = line.strip()
        if line.startswith(PROTOCOLS) and re.match(r"^\S+$", line):
            out.append(line)
    return out


def main():
    links, seen = [], set()
    own = [l.strip() for l in os.environ.get("OWN_NODES", "").splitlines() if l.strip()]
    with open("sources.txt") as f:
        urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    for url in urls:
        try:
            batch = extract(fetch(url))
            print(f"{len(batch):4d} links from {url}")
            links.extend(batch)
        except Exception as e:
            print(f"skip {url}: {e}")
    links = own + links
    unique = []
    for link in links:
        key = link.split("#")[0]
        if key not in seen:
            seen.add(key)
            unique.append(link)
    os.makedirs("docs", exist_ok=True)
    plain = "\n".join(unique) + "\n"
    with open("docs/sub.txt", "w", encoding="utf-8") as f:
        f.write(plain)
    with open("docs/sub_base64.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode(plain.encode()).decode())
    print(f"total unique links: {len(unique)} (own: {len(own)})")


if __name__ == "__main__":
    main()
