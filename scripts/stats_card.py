#!/usr/bin/env python3
"""Generate an animated GitHub stats card (SVG) from the GitHub GraphQL API.

Usage: python3 scripts/stats_card.py assets/generated/stats.svg [--demo]
Reads GH_USER and GH_TOKEN from the environment (set automatically in the workflow).
"""
import html, json, os, sys, urllib.request

W, H = 420, 170
TEAL, BLUE, INK, MUTE, DIM = "#2DD4BF", "#4EA1FF", "#E6EEF7", "#9FB6CC", "#6F8BA6"
SANS = "'Avenir Next','Segoe UI','Helvetica Neue',Arial,sans-serif"
D = 3.0

QUERY = """query($login:String!){user(login:$login){
  followers{totalCount} pullRequests{totalCount} issues{totalCount}
  repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount}}
  contributionsCollection{totalCommitContributions}}}"""


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-stats-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    u = (payload.get("data") or {}).get("user")
    if not u:
        raise RuntimeError(f"GraphQL error: {payload.get('errors') or 'user not found'}")
    return {
        "Stars earned": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "Commits, last year": u["contributionsCollection"]["totalCommitContributions"],
        "Pull requests": u["pullRequests"]["totalCount"],
        "Issues": u["issues"]["totalCount"],
        "Repositories": u["repositories"]["totalCount"],
        "Followers": u["followers"]["totalCount"],
    }


def demo():
    return {"Stars earned": 14, "Commits, last year": 119, "Pull requests": 6, "Issues": 3, "Repositories": 22, "Followers": 9}


ICONS = {  # 16x16 line icons
    "Stars earned": '<path d="M8 1.2l2.2 4.6 5 .7-3.6 3.5.9 5L8 12.6 3.5 15l.9-5L.8 6.5l5-.7z"/>',
    "Commits, last year": '<circle cx="8" cy="8" r="3"/><path d="M0.8 8H5M11 8h4.2"/>',
    "Pull requests": '<circle cx="4" cy="3.5" r="1.9"/><circle cx="4" cy="12.5" r="1.9"/><circle cx="12" cy="12.5" r="1.9"/><path d="M4 5.4v5.2M12 10.6V6.5c0-1.2-.8-2-2-2H8.5M10 2.5L8.2 4.5 10 6.5"/>',
    "Issues": '<circle cx="8" cy="8" r="6.3"/><circle cx="8" cy="8" r="1.2" fill="currentColor"/>',
    "Repositories": '<path d="M2.5 3.2A1.8 1.8 0 0 1 4.3 1.4H13v10.8H4.2a1.7 1.7 0 0 0 0 3.4H13M13 12.2v3.4"/>',
    "Followers": '<circle cx="6" cy="5" r="2.6"/><path d="M1.2 14c.3-2.6 2.2-4 4.8-4s4.5 1.4 4.8 4M11 2.6a2.6 2.6 0 0 1 0 5M12.5 10.2c1.4.5 2.3 1.7 2.5 3.8"/>',
}


def reveal(delay, dy=8):
    a, b = delay / D, (delay + 0.5) / D
    kt = f"0;{a:.4f};{b:.4f};1"
    return (f'<animate attributeName="opacity" dur="{D}s" begin="0s" fill="freeze" keyTimes="{kt}" values="0;0;1;1"/>'
            f'<animateTransform attributeName="transform" type="translate" dur="{D}s" begin="0s" fill="freeze" calcMode="spline" keyTimes="{kt}" keySplines="0 0 1 1;0.2 0.7 0.2 1;0 0 1 1" values="0 {dy};0 {dy};0 0;0 0"/>')


def render(stats, user):
    cells = []
    for i, (label, value) in enumerate(stats.items()):
        col, row = i % 3, i // 3
        x, y = 26 + col * 130, 74 + row * 52
        c = TEAL if (col + row) % 2 == 0 else BLUE
        txt = f"{value:,}"
        cells.append(
            f'<g><g transform="translate({x} {y-12})" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" color="{c}">{ICONS[label]}</g>'
            f'<text x="{x+22}" y="{y}" font-family="{SANS}" font-size="11.5" fill="{MUTE}">{html.escape(label)}</text>'
            f'<text x="{x}" y="{y+26}" font-family="{SANS}" font-size="23" font-weight="700" fill="{INK}">{txt}</text>'
            f'{reveal(0.3 + i * 0.15)}</g>')
    summary = ", ".join(f"{k}: {v}" for k, v in stats.items())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub stats for {html.escape(user)}. {html.escape(summary)}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1424"/><stop offset="1" stop-color="#0E2038"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#6F8BA6" fill-opacity="0.13"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="url(#bg)" stroke="#17304A"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="url(#dots)"/>
<g clip-path="url(#c)"><g opacity="0"><rect x="-70" y="-10" width="46" height="{H+20}" fill="url(#sh)" transform="skewX(-20)"/>
<animateTransform attributeName="transform" type="translate" dur="8s" begin="2s" repeatCount="indefinite" values="0 0;{W+120} 0;{W+120} 0" keyTimes="0;0.2;1"/>
<animate attributeName="opacity" dur="8s" begin="2s" repeatCount="indefinite" values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.2;1"/></g></g>
<g>{f'<text x="26" y="36" font-family="{SANS}" font-size="16" font-weight="700" fill="{TEAL}">GitHub stats</text>'}{reveal(0.05, 6)}</g>
{"".join(cells)}
</svg>'''


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "stats.svg"
    user = os.environ.get("GH_USER", "ouss-100")
    if "--demo" in sys.argv:
        stats = demo()
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            sys.exit("GH_TOKEN is not set")
        stats = fetch(user, token)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(render(stats, user))
    print(f"wrote {out}: {stats}")


if __name__ == "__main__":
    main()
