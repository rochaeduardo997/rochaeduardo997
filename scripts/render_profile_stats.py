#!/usr/bin/env python3
"""Render the profile cards for sections 04 (estatisticas) and 05 (contribuicoes)."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timedelta
from html import escape, unescape
from pathlib import Path

USERNAME = "rochaeduardo997"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"

LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "SCSS": "#c6538c",
    "Vue": "#41b883",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Elixir": "#6e4a7e",
    "Lua": "#000080",
    "Nix": "#7e7eff",
    "HCL": "#844FBA",
    "MDX": "#fcb32c",
    "Astro": "#ff5a03",
}

MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

LEVELS = {
    "dark": {1: "#0e4429", 2: "#006d32", 3: "#26a641", 4: "#39d353"},
    "light": {1: "#9be9a8", 2: "#40c463", 3: "#30a14e", 4: "#216e39"},
}

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "header": "#161b22",
        "stroke": "#30363d",
        "muted": "#8b949e",
        "text": "#c9d1d9",
        "prompt": "#39d353",
        "flag": "#ffa657",
        "fn": "#d2a8ff",
        "zero": "#21262d",
        "scan": "#39d353",
        "cursor": "#c9d1d9",
        "ok": "#39d353",
        "busy": "#ffa657",
        "commits": "#39d353",
        "prs": "#58a6ff",
        "issues": "#d2a8ff",
        "repos": "#ffa657",
        "stars": "#e3b341",
        "followers": "#58a6ff",
        "zero_flash": "#8b949e",
        "one_flash": "#ffffff",
    },
    "light": {
        "bg": "#ffffff",
        "header": "#f6f8fa",
        "stroke": "#d0d7de",
        "muted": "#57606a",
        "text": "#24292f",
        "prompt": "#1a7f37",
        "flag": "#bc4c00",
        "fn": "#8250df",
        "zero": "#d0d7de",
        "scan": "#1a7f37",
        "cursor": "#24292f",
        "ok": "#1a7f37",
        "busy": "#bc4c00",
        "commits": "#1a7f37",
        "prs": "#0969da",
        "issues": "#8250df",
        "repos": "#bc4c00",
        "stars": "#e3b341",
        "followers": "#0969da",
        "zero_flash": "#57606a",
        "one_flash": "#0d1117",
    },
}


def fetch(url: str) -> bytes:
    headers = {
        "User-Agent": "profile-readme",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch(url).decode())


def fetch_profile() -> dict:
    user = fetch_json(f"https://api.github.com/users/{USERNAME}")
    repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")
    languages: dict[str, int] = {}
    stars = 0
    for repo in repos:
        stars += repo.get("stargazers_count") or 0
        if repo.get("fork"):
            continue
        data = fetch_json(repo["languages_url"])
        for name, amount in data.items():
            languages[name] = languages.get(name, 0) + amount
    ranked = sorted(languages.items(), key=lambda item: item[1], reverse=True)
    total_bytes = sum(amount for _, amount in ranked) or 1
    top = [
        (name, amount / total_bytes * 100)
        for name, amount in ranked
        if amount / total_bytes * 100 >= 0.1
    ][:6]
    return {
        "repos": user.get("public_repos") or 0,
        "stars": stars,
        "followers": user.get("followers") or 0,
        "languages": top,
    }


def fetch_contributions() -> dict:
    html = fetch(f"https://github.com/users/{USERNAME}/contributions").decode("utf-8", "replace")
    total_match = re.search(
        r"([\d][\d,]*)\s*contributions\s*in the last year",
        html,
        re.S,
    )
    if not total_match:
        raise SystemExit("Nao encontrei o total de contribuicoes no calendario.")
    total = int(total_match.group(1).replace(",", ""))

    percentages = {"Commits": 0, "Pull requests": 0, "Issues": 0}
    percent_match = re.search(r'data-percentages="([^"]+)"', html)
    if percent_match:
        parsed = json.loads(unescape(percent_match.group(1)))
        percentages.update({key: int(value) for key, value in parsed.items()})

    cells = []
    pattern = re.compile(
        r'data-date="(\d{4}-\d{2}-\d{2})" id="contribution-day-component-\d+-\d+" data-level="(\d)"'
        r"[\s\S]{0,1200}?<tool-tip[^>]*>(.*?)</tool-tip>"
    )
    for day, level, tip in pattern.findall(html):
        count_match = re.search(r"([\d,]+)\s+contribution", tip)
        count = int(count_match.group(1).replace(",", "")) if count_match else 0
        cells.append(
            {
                "date": datetime.strptime(day, "%Y-%m-%d").date(),
                "level": int(level),
                "count": count,
            }
        )
    if not cells:
        raise SystemExit("Nao encontrei dias no calendario de contribuicoes.")

    commits = round(total * percentages.get("Commits", 0) / 100)
    pull_requests = round(total * percentages.get("Pull requests", 0) / 100)
    issues = round(total * percentages.get("Issues", 0) / 100)
    return {
        "total": total,
        "commits": commits,
        "pull_requests": pull_requests,
        "issues": issues,
        "cells": cells,
    }


def terminal_chrome(theme: dict, width: int, height: int, title: str, title_size: float) -> str:
    return f"""<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="{theme["bg"]}" stroke="{theme["stroke"]}" stroke-width="2"/>
<path d="M1 13 a12 12 0 0 1 12 -12 H{width - 13} a12 12 0 0 1 12 12 V38 H1Z" fill="{theme["header"]}"/>
<rect x="1" y="38" width="{width - 2}" height="1" fill="{theme["stroke"]}"/>
<circle cx="20" cy="20" r="5.5" fill="#ff5f57"/><circle cx="37" cy="20" r="5.5" fill="#febc2e"/><circle cx="54" cy="20" r="5.5" fill="#28c840"/>
<text x="{width / 2}" y="25" text-anchor="middle" style="font-size:{title_size}px;fill:{theme["muted"]}">{escape(title)}</text>"""


def render_stats(theme_name: str, profile: dict, activity: dict) -> str:
    theme = THEMES[theme_name]
    rows = [
        ("commits:", activity["commits"], theme["commits"], 20, 210),
        ("pull_requests:", activity["pull_requests"], theme["prs"], 230, 420),
        ("issues:", activity["issues"], theme["issues"], 20, 210),
        ("repositorios:", profile["repos"], theme["repos"], 230, 420),
        ("estrelas:", profile["stars"], theme["stars"], 20, 210),
        ("seguidores:", profile["followers"], theme["followers"], 230, 420),
    ]
    body = [terminal_chrome(theme, 440, 220, "stats.sh", 12.5)]
    body.append(
        f'<text x="20" y="64" class="l" style="font-size:13px">'
        f'<tspan fill="{theme["prompt"]}">$</tspan>'
        f'<tspan fill="{theme["text"]}"> git stats </tspan>'
        f'<tspan fill="{theme["flag"]}">--ultimo-ano</tspan></text>'
    )
    for index, (label, value, color, x, value_x) in enumerate(rows):
        col = index % 2
        line = index // 2
        y = 104 + line * 38
        delay = 0.15 + index * 0.12
        rule_x = 20 if col == 0 else 230
        body.append(
            f'<g class="l" style="animation-delay:{delay:.2f}s">'
            f'<text x="{x}" y="{y}" style="font-size:12px;fill:{theme["muted"]}">{label}</text>'
            f'<text x="{value_x}" y="{y}" text-anchor="end" style="font-size:18px;font-weight:700;fill:{color}">{value}</text>'
            f'<rect x="{rule_x}" y="{y + 9}" width="190" height="1" fill="{theme["stroke"]}"/></g>'
        )
    return svg_document(440, 220, "\n".join(body), fade=True)


def render_langs(theme_name: str, languages: list[tuple[str, float]]) -> str:
    theme = THEMES[theme_name]
    shown = languages or [("sem dados", 100.0)]
    body = [terminal_chrome(theme, 440, 220, "linguagens.json", 12.5)]
    body.append(
        f'<text x="20" y="62" class="l" style="font-size:13px">'
        f'<tspan fill="{theme["prompt"]}">$</tspan>'
        f'<tspan fill="{theme["text"]}"> linguist </tspan>'
        f'<tspan fill="{theme["flag"]}">--top 6</tspan></text>'
    )
    body.append('<clipPath id="bc"><rect x="20" y="78" width="400" height="10" rx="5"/></clipPath>')
    segments = []
    cursor = 20.0
    widths = [400 * (percent / 100) for _, percent in shown]
    drift = 400 - sum(widths)
    if widths:
        widths[0] += drift
    for (name, _), width in zip(shown, widths):
        color = LANG_COLORS.get(name, "#8b949e")
        segments.append(
            f'<rect x="{cursor:.1f}" y="78" width="{max(width, 0):.1f}" height="10" fill="{color}"/>'
        )
        cursor += width
    body.append(f'<g clip-path="url(#bc)">{"".join(segments)}</g>')
    for index, (name, percent) in enumerate(shown):
        color = LANG_COLORS.get(name, "#8b949e")
        column = index % 2
        line = index // 2
        x = 25 if column == 0 else 235
        y = 118 + line * 30
        value_x = 210 if column == 0 else 420
        delay = 0.15 + index * 0.1
        body.append(
            f'<g class="l" style="animation-delay:{delay:.2f}s">'
            f'<circle cx="{x}" cy="{y - 4}" r="5" fill="{color}"/>'
            f'<text x="{x + 13}" y="{y}" style="font-size:12.5px;fill:{theme["text"]}">{escape(name)}</text>'
            f'<text x="{value_x}" y="{y}" text-anchor="end" style="font-size:12.5px;fill:{theme["muted"]}">{percent:.1f}%</text></g>'
        )
    return svg_document(440, 220, "\n".join(body), fade=True)


def month_labels(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    labels: list[tuple[int, str]] = []
    last_x = -10_000
    for col, week in enumerate(weeks):
        days = [cell["date"] for cell in week if cell]
        if not days:
            continue
        first_of_month = next((day for day in days if day.day == 1), None)
        if first_of_month is None and not labels:
            chosen = days[0]
        elif first_of_month is None:
            continue
        else:
            chosen = first_of_month
        x = 58 + col * 15
        if x - last_x < 24:
            continue
        labels.append((x, MONTHS[chosen.month - 1]))
        last_x = x
    return labels


def build_weeks(cells: list[dict]) -> tuple[list[list[dict | None]], int]:
    by_day = {cell["date"]: cell for cell in cells}
    start = min(by_day)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    end = max(by_day)
    end += timedelta(days=(5 - end.weekday()) % 7)
    weeks: list[list[dict | None]] = []
    cursor = start
    while cursor <= end:
        week = []
        for _ in range(7):
            week.append(by_day.get(cursor))
            cursor += timedelta(days=1)
        weeks.append(week)
    total = sum(cell["count"] for cell in cells)
    return weeks, total


def render_graph(theme_name: str, cells: list[dict], total: int) -> str:
    theme = THEMES[theme_name]
    weeks, _ = build_weeks(cells)
    columns = len(weeks)
    width = int(65.5 + (columns - 1) * 15 + 37.5)
    height = 275
    scan_distance = columns * 15
    levels = LEVELS[theme_name]
    parts = [
        f"""<style>
text{{font-family:'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace}}
.m{{font-size:11px;fill:{theme["muted"]}}}
.d{{font-size:11px;fill:{theme["muted"]}}}
.z,.c{{font-size:12px;text-anchor:middle;font-weight:700}}
.z{{fill:{theme["zero"]};animation:z 9s linear infinite}}
.c{{animation:c 9s linear infinite}}
@keyframes z{{0%{{fill:{theme["zero_flash"]}}}4%{{fill:{theme["zero"]}}}100%{{fill:{theme["zero"]}}}}}
@keyframes c{{0%{{fill:{theme["one_flash"]}}}6%{{fill:{theme["ok"]}}}100%{{}}}}
.a{{animation:a 9s steps(1) infinite}}.b{{opacity:0;animation:b 9s steps(1) infinite}}
@keyframes a{{0%{{opacity:1}}92%{{opacity:0}}100%{{opacity:0}}}}
@keyframes b{{0%{{opacity:0}}92%{{opacity:1}}100%{{opacity:1}}}}
.cur{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}
</style>
<defs>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{theme["scan"]}" stop-opacity="0"/><stop offset=".85" stop-color="{theme["scan"]}" stop-opacity=".25"/><stop offset="1" stop-color="{theme["scan"]}" stop-opacity=".9"/></linearGradient>
<clipPath id="cl"><rect x="54" y="88" width="{width - 80}" height="113"/></clipPath>
</defs>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="{theme["bg"]}" stroke="{theme["stroke"]}" stroke-width="2"/>
<path d="M1 13 a12 12 0 0 1 12 -12 H{width - 13} a12 12 0 0 1 12 12 V40 H1Z" fill="{theme["header"]}"/>
<rect x="1" y="40" width="{width - 2}" height="1" fill="{theme["stroke"]}"/>
<circle cx="22" cy="21" r="6" fill="#ff5f57"/><circle cx="40" cy="21" r="6" fill="#febc2e"/><circle cx="58" cy="21" r="6" fill="#28c840"/>
<text x="{width / 2}" y="26" text-anchor="middle" style="font-size:13px;fill:{theme["muted"]}">contribuicoes.bin — compilando @{USERNAME}</text>
<text x="22" y="66" style="font-size:13px"><tspan fill="{theme["prompt"]}">$</tspan><tspan fill="{theme["text"]}"> git log --since="1 ano" </tspan><tspan fill="{theme["muted"]}">| </tspan><tspan fill="{theme["fn"]}">compilar</tspan><tspan fill="{theme["flag"]}"> --binario</tspan></text>"""
    ]
    for x, name in month_labels(weeks):
        parts.append(f'<text x="{x}" y="78" class="m">{name}</text>')
    parts.append(f'<text x="46" y="118" class="d" text-anchor="end">seg</text>')
    parts.append(f'<text x="46" y="148" class="d" text-anchor="end">qua</text>')
    parts.append(f'<text x="46" y="178" class="d" text-anchor="end">sex</text>')
    for col, week in enumerate(weeks):
        delay = col * 9 / max(columns, 1)
        x = 65.5 + col * 15
        for row, cell in enumerate(week):
            y = 103 + row * 15
            count = cell["count"] if cell else 0
            level = cell["level"] if cell else 0
            if count <= 0 or level <= 0:
                parts.append(
                    f'<text x="{x}" y="{y}" class="z" style="animation-delay:{delay:.2f}s">0</text>'
                )
            else:
                fill = levels.get(min(level, 4), levels[1])
                parts.append(
                    f'<text x="{x}" y="{y}" class="c" fill="{fill}" style="animation-delay:{delay:.2f}s">1</text>'
                )
    parts.append(
        f"""<g clip-path="url(#cl)"><g>
  <animateTransform attributeName="transform" type="translate" from="0 0" to="{scan_distance} 0" dur="9s" repeatCount="indefinite"/>
  <rect x="-12" y="88" width="70" height="113" fill="url(#g)"/>
  <rect x="56" y="88" width="2" height="113" fill="{theme["scan"]}"/>
</g></g>
<g style="font-size:13px">
  <text x="22" y="231"><tspan fill="{theme["muted"]}">[</tspan></text>
  <rect x="34" y="221" width="629" height="12" rx="2" fill="{theme["header"]}"/>
  <rect x="34" y="221" width="0" height="12" rx="2" fill="{theme["scan"]}"><animate attributeName="width" from="0" to="629" dur="9s" repeatCount="indefinite"/></rect>
  <text x="669" y="231"><tspan fill="{theme["muted"]}">]</tspan></text>
  <text class="a" x="685" y="231" fill="{theme["busy"]}">compilando...</text>
  <text class="b" x="685" y="231" fill="{theme["ok"]}">✔ build ok</text>
  <text x="22" y="257"><tspan fill="{theme["ok"]}">✔</tspan><tspan fill="{theme["text"]}"> {total} contribuições compiladas</tspan><tspan fill="{theme["muted"]}"> · 0 erros · 0 warnings</tspan></text>
  <rect class="cur" x="{width - 38}" y="245" width="8" height="15" fill="{theme["cursor"]}"/>
</g>"""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        + "\n".join(parts)
        + "\n</svg>\n"
    )


def svg_document(width: int, height: int, body: str, fade: bool) -> str:
    fade_css = (
        "<style>text{font-family:'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace}\n"
        ".l{opacity:0;animation:l .4s ease-out forwards}@keyframes l{to{opacity:1}}</style>"
        if fade
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f"{fade_css}{body}</svg>\n"
    )


def main() -> None:
    profile = fetch_profile()
    activity = fetch_contributions()
    summed = sum(cell["count"] for cell in activity["cells"])
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "stats.svg": render_stats("light", profile, activity),
        "stats-dark.svg": render_stats("dark", profile, activity),
        "langs.svg": render_langs("light", profile["languages"]),
        "langs-dark.svg": render_langs("dark", profile["languages"]),
        "code-contribution-graph.svg": render_graph("light", activity["cells"], activity["total"]),
        "code-contribution-graph-dark.svg": render_graph("dark", activity["cells"], activity["total"]),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(
        f"commits={activity['commits']} prs={activity['pull_requests']} "
        f"issues={activity['issues']} repos={profile['repos']} stars={profile['stars']} "
        f"followers={profile['followers']} contributions={activity['total']} "
        f"calendar_sum={summed} days={len(activity['cells'])} "
        f"langs={profile['languages']}"
    )


if __name__ == "__main__":
    main()
