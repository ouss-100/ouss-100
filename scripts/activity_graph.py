#!/usr/bin/env python3
"""Generate an animated contribution-activity SVG for a GitHub user.

Usage:  python3 scripts/activity_graph.py dist/activity.svg [--demo]

In GitHub Actions it reads GH_USER and GH_TOKEN from the environment and queries
the GraphQL API. With --demo it renders random sample data (for local preview).
"""
import datetime as dt, json, math, os, random, sys, urllib.request

DAYS = 90
W, H = 830, 282
PX0, PX1, PY0, PY1 = 64, 794, 112, 222          # plot area
TEAL, BLUE, INK, MUTE, DIM = "#2DD4BF", "#4EA1FF", "#E6EEF7", "#9FB6CC", "#6F8BA6"
SANS = "'Avenir Next','Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"


def fetch(user, token):
    today = dt.date.today()
    start = today - dt.timedelta(days=DAYS - 1)
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){contributionsCollection(from:$from,to:$to){
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    variables = {
        "login": user,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{today.isoformat()}T23:59:59Z",
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-activity-graph"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload or not payload.get("data", {}).get("user"):
        raise RuntimeError(f"GraphQL error: {payload.get('errors') or 'user not found'}")
    counts = {}
    for wk in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in wk["contributionDays"]:
            counts[d["date"]] = d["contributionCount"]
    days = [start + dt.timedelta(days=i) for i in range(DAYS)]
    return [(d, counts.get(d.isoformat(), 0)) for d in days]


def demo():
    random.seed(11)
    today = dt.date.today()
    out = []
    for i in range(DAYS):
        d = today - dt.timedelta(days=DAYS - 1 - i)
        base = max(0, int(random.gauss(3, 3)))
        if random.random() < 0.18:
            base = 0
        out.append((d, base))
    return out


def smooth_path(pts, ybot):
    """Catmull-Rom spline through pts, control points clamped above the baseline."""
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(ybot, p1[1] + (p2[1] - p0[1]) / 6))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(ybot, p2[1] - (p3[1] - p1[1]) / 6))
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def render(data, user):
    counts = [c for _, c in data]
    total = sum(counts)
    peak = max(counts)
    step = max(1, math.ceil(max(peak, 4) / 4))
    ymax = step * 4
    n = len(data)

    def X(i): return PX0 + (PX1 - PX0) * i / (n - 1)
    def Y(v): return PY1 - (PY1 - PY0) * v / ymax

    pts = [(X(i), Y(c)) for i, c in enumerate(counts)]
    line = smooth_path(pts, PY1)
    area = line + f"L{PX1} {PY1}L{PX0} {PY1}Z"

    grid, ylabels = [], []
    for k in range(5):
        v = step * k
        y = Y(v)
        grid.append(f'<line x1="{PX0}" y1="{y:.1f}" x2="{PX1}" y2="{y:.1f}" stroke="#1E4A63" stroke-opacity="{0.9 if k == 0 else 0.45}" {"" if k == 0 else "stroke-dasharray=\"3 6\""}/>')
        ylabels.append(f'<text x="{PX0-12}" y="{y+4:.1f}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{DIM}">{v}</text>')

    xlabels = []
    for i, (d, _) in enumerate(data):
        if d.day == 1 and i > 2:
            xlabels.append(f'<line x1="{X(i):.1f}" y1="{PY1}" x2="{X(i):.1f}" y2="{PY1+5}" stroke="#2A5C78"/><text x="{X(i):.1f}" y="{PY1+22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{DIM}">{d.strftime("%b")}</text>')
    xlabels.append(f'<text x="{PX0}" y="{PY1+22}" text-anchor="start" font-family="{MONO}" font-size="11" fill="{DIM}">{data[0][0].strftime("%b %d")}</text>')
    xlabels.append(f'<text x="{PX1}" y="{PY1+22}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{DIM}">today</text>')

    pi = counts.index(peak)
    px, py = X(pi), Y(peak)
    peak_marker = ""
    if peak > 0:
        lab_x = min(max(px, PX0 + 24), PX1 - 24)
        peak_marker = f'''<g opacity="0"><animate attributeName="opacity" dur="3s" begin="0s" fill="freeze" keyTimes="0;0.6;0.75;1" values="0;0;1;1"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="none" stroke="{TEAL}" stroke-opacity="0"><animate attributeName="r" dur="2.4s" repeatCount="indefinite" values="4;14;14" keyTimes="0;0.7;1"/><animate attributeName="stroke-opacity" dur="2.4s" repeatCount="indefinite" values="0.8;0;0" keyTimes="0;0.7;1"/></circle>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#0A1424" stroke="{TEAL}" stroke-width="2"/>
<rect x="{lab_x-20:.1f}" y="{py-30:.1f}" width="40" height="19" rx="9.5" fill="{TEAL}"/><text x="{lab_x:.1f}" y="{py-16.5:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" fill="#06101D">{peak}</text></g>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution activity of {user} over the last {DAYS} days: {total} contributions, best day {peak}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1424"/><stop offset="1" stop-color="#0E2038"/></linearGradient>
<linearGradient id="ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>
<linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.32"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#6F8BA6" fill-opacity="0.14"/></pattern>
<clipPath id="plot"><rect x="{PX0}" y="{PY0-40}" width="{PX1-PX0}" height="{PY1-PY0+40}"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="22" fill="url(#bg)" stroke="#17304A"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="22" fill="url(#dots)"/>
<text x="36" y="52" font-family="{SANS}" font-size="20" font-weight="700" fill="{INK}">Contribution activity</text>
<text x="36" y="72" font-family="{SANS}" font-size="13" fill="{DIM}">Last {DAYS} days</text>
<text x="{W-36}" y="52" text-anchor="end" font-family="{SANS}" font-size="26" font-weight="700" fill="{TEAL}">{total}</text>
<text x="{W-36}" y="72" text-anchor="end" font-family="{SANS}" font-size="13" fill="{DIM}">contributions</text>
{"".join(grid)}{"".join(ylabels)}{"".join(xlabels)}
<g clip-path="url(#plot)">
<path d="{area}" fill="url(#fill)" opacity="0"><animate attributeName="opacity" dur="3s" begin="0s" fill="freeze" keyTimes="0;0.35;0.7;1" values="0;0;1;1"/></path>
<path d="{line}" fill="none" stroke="url(#ln)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" dur="2s" begin="0s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1" values="1;0"/></path>
</g>
{peak_marker}
</svg>'''
    return svg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "activity.svg"
    user = os.environ.get("GH_USER", "ouss-100")
    if "--demo" in sys.argv:
        data = demo()
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            sys.exit("GH_TOKEN is not set")
        data = fetch(user, token)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(data, user))
    print(f"wrote {out}: {sum(c for _, c in data)} contributions over {len(data)} days")


if __name__ == "__main__":
    main()
