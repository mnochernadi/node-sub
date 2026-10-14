# sub-builder

Builds a subscription link from public sources and your own nodes.

- `sources.txt`: one source URL per line.
- `OWN_NODES` secret: your own share links, one per line. Keep them out of the code.
- Output: `docs/sub.txt` and `docs/sub_base64.txt`, rebuilt every 3 hours by GitHub Actions.

Subscription URL (after the first run):
https://raw.githubusercontent.com/mnochernadi/node-sub/main/docs/sub_base64.txt
