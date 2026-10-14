"""Fetch configs from the sources in sources.txt, rename them to op_iran N, write subscription.txt.
Your own configs are not included. Runs every 20 minutes via GitHub Actions.
"""
import base64, json, urllib.parse, urllib.request

UA = {"User-Agent": "sub-builder/3.0"}
PROTOCOLS = ("vless://", "vmess://", "trojan://", "ss://")
NAME = "op_iran"


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def decode_all(text):
    s = "".join(text.split())
    if s and not any(s.startswith(p) for p in PROTOCOLS):
        try:
            return base64.b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return text


def rename(link, n):
    if link.startswith("vmess://"):
        try:
            d = json.loads(base64.b64decode(link[8:] + "=" * (-len(link[8:]) % 4)).decode())
        except Exception:
            return None
        d["ps"] = f"{NAME} {n}"
        return "vmess://" + base64.b64encode(json.dumps(d, ensure_ascii=False).encode()).decode()
    base = link.split("#", 1)[0]
    return f"{base}#{urllib.parse.quote(f'{NAME} {n}', safe='')}"


def main():
    urls = [l.strip() for l in open("sources.txt") if l.strip() and not l.startswith("#")]
    found, seen = [], set()
    for url in urls:
        try:
            for line in decode_all(fetch(url)).splitlines():
                line = line.strip()
                if line.startswith(PROTOCOLS) and " " not in line:
                    key = line.split("#", 1)[0]
                    if key not in seen:
                        seen.add(key)
                        found.append(line)
        except Exception as e:
            print("skip", url, e)
    out = []
    for link in found:
        r = rename(link, len(out) + 1)
        if r:
            out.append(r)
    plain = "\n".join(out) + "\n"
    open("subscription.txt", "w", encoding="utf-8").write(plain)
    print(f"written {len(out)} configs")


if __name__ == "__main__":
    main()
