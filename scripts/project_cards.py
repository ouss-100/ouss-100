#!/usr/bin/env python3
"""Build animated project cards (SVG) from projects.json + live GitHub repo data.

Usage: python3 scripts/project_cards.py dist [--offline]
Reads GH_TOKEN from the environment when available (higher rate limit).
For each repo it writes dist/project-<repo-name>.svg
"""
import html, json, os, re, sys, urllib.request

INK, MUTE, DIM, TEAL, BLUE = "#E6EEF7", "#9FB6CC", "#6F8BA6", "#2DD4BF", "#4EA1FF"
SANS = "'Avenir Next','Segoe UI','Helvetica Neue',Arial,sans-serif"
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "Jupyter Notebook": "#DA5B0B",
    "HTML": "#E34C26", "CSS": "#8957E5", "Java": "#B07219", "C++": "#F34B7D", "C": "#8A8A8A", "PHP": "#4F5D95",
    "Shell": "#89E051", "Go": "#00ADD8", "Rust": "#DEA584", "Dockerfile": "#384D54", "SCSS": "#C6538C",
}
H = 156


def api(repo, token):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-project-cards",
                 **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def wrap(text, limit, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= limit:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;:")[: max(0, limit - 1)] + "…"
    return lines


def fmt(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def card(name, desc, lang, stars, forks, wide, k):
    W = 808 if wide else 400
    limit = 118 if wide else 54
    lines = wrap(desc, limit, 2 if wide else 3) if desc else []
    accent = TEAL if k % 2 == 0 else BLUE
    b = f"{0.7 * k:.1f}s"
    text = "".join(
        f'<text x="26" y="{70 + i * 20}" font-family="{SANS}" font-size="13.5" fill="{MUTE}">{html.escape(l)}</text>'
        for i, l in enumerate(lines))
    meta, x = [], 26
    if lang:
        col = LANG_COLORS.get(lang, TEAL)
        meta.append(f'<circle cx="{x+5}" cy="{H-26}" r="5" fill="{col}"/><text x="{x+16}" y="{H-21.5}" font-family="{SANS}" font-size="12.5" fill="{MUTE}">{html.escape(lang)}</text>')
        x += 16 + len(lang) * 6.8 + 18
    if stars:
        meta.append(f'<path transform="translate({x} {H-33}) scale(0.82)" d="M8 .25l2.3 4.9 5.4.7-3.9 3.7 1 5.3L8 12.3l-4.8 2.55 1-5.3L.3 5.85l5.4-.7z" fill="{DIM}"/><text x="{x+17}" y="{H-21.5}" font-family="{SANS}" font-size="12.5" fill="{MUTE}">{fmt(stars)}</text>')
        x += 17 + len(fmt(stars)) * 7 + 16
    if forks:
        meta.append(f'<g transform="translate({x} {H-33}) scale(0.82)" fill="none" stroke="{DIM}" stroke-width="1.6"><circle cx="4" cy="3.5" r="2"/><circle cx="12" cy="3.5" r="2"/><circle cx="8" cy="13" r="2"/><path d="M4 5.5v1.5c0 1.2 1 2 2 2h4c1 0 2-.8 2-2V5.5M8 9v2"/></g><text x="{x+17}" y="{H-21.5}" font-family="{SANS}" font-size="12.5" fill="{MUTE}">{fmt(forks)}</text>')
    sweep_to = W + 120
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(name)}: {html.escape(desc)}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A1424"/><stop offset="1" stop-color="#0E2038"/></linearGradient>
<radialGradient id="gl" cx="0" cy="0" r="1"><stop offset="0" stop-color="{accent}" stop-opacity="0.18"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.11"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#6F8BA6" fill-opacity="0.13"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="url(#bg)"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="url(#dots)"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="url(#gl)"/>
<g clip-path="url(#c)"><g opacity="0"><rect x="-80" y="-10" width="52" height="{H+20}" fill="url(#sh)" transform="skewX(-20)"/>
<animateTransform attributeName="transform" type="translate" dur="7s" begin="{b}" repeatCount="indefinite" values="0 0;{sweep_to} 0;{sweep_to} 0" keyTimes="0;0.2;1"/>
<animate attributeName="opacity" dur="7s" begin="{b}" repeatCount="indefinite" values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.2;1"/></g></g>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="{accent}" stroke-opacity="0.35"><animate attributeName="stroke-opacity" dur="7s" begin="{b}" repeatCount="indefinite" values="0.35;0.85;0.35;0.35" keyTimes="0;0.1;0.28;1"/></rect>
<path transform="translate(26 24)" d="M1 2.8A2.3 2.3 0 0 1 3.3.5H13v12H3.8a1.8 1.8 0 0 0 0 3.6H13M13 12.5v3.6" fill="none" stroke="{accent}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
<text x="50" y="38" font-family="{SANS}" font-size="17" font-weight="700" fill="{INK}">{html.escape(name)}</text>
<g transform="translate({W-42} 24)"><path d="M0 12L12 0M3 0H12V9" fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
<animateTransform attributeName="transform" type="translate" dur="2.6s" begin="{b}" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.2 1;0.4 0 0.2 1" values="{W-42} 24;{W-38} 20;{W-42} 24"/></g>
{text}
{"".join(meta)}
</svg>'''


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "dist"
    offline = "--offline" in sys.argv
    token = os.environ.get("GH_TOKEN")
    cfg = json.load(open(os.path.join(os.path.dirname(__file__), "..", "projects.json"), encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    for k, p in enumerate(cfg["projects"]):
        repo = p["repo"]; name = repo.split("/")[-1]
        data = {}
        if not offline:
            try:
                data = api(repo, token)
            except Exception as e:  # keep going with config values
                print(f"warning: {repo}: {e}", file=sys.stderr)
        desc = (p.get("description") or data.get("description") or "").strip()
        svg = card(name, desc, data.get("language"), data.get("stargazers_count", 0), data.get("forks_count", 0), p.get("wide", False), k)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        with open(os.path.join(out, f"project-{slug}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote project-{slug}.svg  lang={data.get('language')} stars={data.get('stargazers_count')} forks={data.get('forks_count')}")


if __name__ == "__main__":
    main()
