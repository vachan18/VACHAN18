
#!/usr/bin/env python3
import json, os, urllib.request, html
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "profile-data.json").read_text(encoding="utf-8"))
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
USER = DATA["username"]
TOKEN = os.getenv("GITHUB_TOKEN", "")

def api(path):
    headers = {"Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))

def esc(value):
    return html.escape(str(value), quote=True)

def txt(x, y, value, size=16, color="#EAF7FF", weight="400", family="Arial,sans-serif"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="{family}">{esc(value)}</text>'

def panel(x,y,w,h,title,accent="#FF168A"):
    return (f'<path d="M{x+18} {y} H{x+w-22} L{x+w} {y+22} V{y+h-16} L{x+w-16} {y+h} H{x} V{y+18} Z" fill="#080D16" stroke="{accent}" stroke-width="1.6"/>'
            + txt(x+22,y+34,title,18,accent,"700","monospace"))

def generate_svg(user, repos, stars, languages, stamp):
    parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1040" viewBox="0 0 1500 1040">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070912"/><stop offset=".55" stop-color="#10102A"/><stop offset="1" stop-color="#050A12"/></linearGradient>
<linearGradient id="glow"><stop stop-color="#FF168A"/><stop offset="1" stop-color="#20E8FF"/></linearGradient>
<pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="#163448" stroke-opacity=".28"/></pattern>
</defs>
<rect width="1500" height="1040" fill="url(#bg)"/><rect width="1500" height="1040" fill="url(#grid)"/><rect x="10" y="10" width="1480" height="1020" rx="14" fill="none" stroke="url(#glow)" stroke-width="2"/>''']
    parts.append(panel(28,28,690,330,"VACHAN.EXE / ENGINEERING DIVISION"))
    parts += [txt(58,105,"VACHAN U S",48,"#FFFFFF","700"),
              txt(60,145,"SOFTWARE ENGINEER  //  AI SYSTEMS  //  CLOUD",18,"#20E8FF","700","monospace"),
              txt(60,195,DATA["bio"],17),
              txt(60,230,f'ROLE / {DATA["role"]} @ {DATA["company"]}',16,"#FF4BA8","700","monospace"),
              txt(60,260,f'LOCATION / {DATA["location"]}',16,"#20E8FF","700","monospace"),
              txt(60,290,"FOCUS / AI • BACKEND • FULL STACK • CLOUD",15),
              txt(60,325,f"LAST SYNC / {stamp}",12,"#8CA7BC","400","monospace")]
    parts.append(panel(748,28,724,330,"CAPABILITY MATRIX / TECH STACK","#20E8FF"))
    for i,(group,items) in enumerate(DATA["skills"].items()):
        x=778+(i%2)*340
        y=94+(i//2)*82
        parts += [txt(x,y,group.upper(),15,"#FF4BA8","700","monospace"),
                  txt(x,y+28," / ".join(items[:5]),13),
                  f'<path d="M{x} {y+42} h290" stroke="#244154"/>']
    parts.append(panel(28,390,930,600,"PROJECT ARCHIVE / DEPLOYED SYSTEMS"))
    for i,proj in enumerate(DATA["projects"]):
        x=52+(i%3)*303
        y=450+(i//3)*250
        parts += [f'<rect x="{x}" y="{y}" width="278" height="215" rx="9" fill="#0C1421" stroke="#31506A"/>',
                  txt(x+14,y+30,f"BUILD / {i+1:02d}",12,"#20E8FF","700","monospace"),
                  txt(x+14,y+62,proj["name"][:27],16,"#FFFFFF","700"),
                  txt(x+14,y+98,proj["category"],12,"#FF4BA8","700"),
                  txt(x+14,y+130,proj["description"][:39],12),
                  txt(x+14,y+158," · ".join(proj["stack"][:4])[:35],11,"#20E8FF"),
                  txt(x+14,y+195,"OPEN REPOSITORY ↗",11,"#FF4BA8","700","monospace")]
    parts.append(panel(990,390,482,600,"GITHUB TELEMETRY / LIVE API","#20E8FF"))
    metrics=[("PUBLIC REPOS",user.get("public_repos",0)),("FOLLOWERS",user.get("followers",0)),("FOLLOWING",user.get("following",0)),("TOTAL STARS",stars)]
    for i,(label,value) in enumerate(metrics):
        x=1020+(i%2)*210
        y=465+(i//2)*100
        parts += [txt(x,y,label,13,"#FF4BA8","700","monospace"),txt(x,y+42,value,34,"#20E8FF","700")]
    parts.append(txt(1020,690,"TOP LANGUAGES",16,"#FF4BA8","700","monospace"))
    if languages:
        maxval=max(languages.values()) or 1
        for i,(lang,count) in enumerate(list(languages.items())[:6]):
            yy=730+i*35
            bar=int(200*count/maxval)
            parts += [txt(1020,yy,lang,13),f'<rect x="1150" y="{yy-13}" width="220" height="12" rx="5" fill="#182536"/>',
                      f'<rect x="1150" y="{yy-13}" width="{bar}" height="12" rx="5" fill="url(#glow)"/>']
    else:
        parts.append(txt(1020,730,"Language data pending.",13))
    parts += [txt(1020,950,"SOURCE: api.github.com / PUBLIC DATA",11,"#8CA7BC","400","monospace"),"</svg>"]
    (ASSETS/"dossier.svg").write_text("".join(parts),encoding="utf-8")

def generate_readme(user, repos, stars, stamp):
    projects = []
    for p in DATA["projects"]:
        projects.append(f'<tr><td><b>{esc(p["name"])}</b><br/><sub>{esc(p["category"])}</sub><br/>{esc(p["description"])}<br/><sub>{esc(" · ".join(p["stack"]))}</sub><br/><a href="{esc(p["url"])}">OPEN REPOSITORY ↗</a></td></tr>')
    skills = []
    for group, items in DATA["skills"].items():
        skills.append(f'**{esc(group.upper())}**<br/>'+" · ".join(f'`{esc(x)}`' for x in items))
    experience = []
    for e in DATA["experience"]:
        experience.append(f'<tr><td><b>{esc(e["period"])}</b></td><td><b>{esc(e["title"])}</b><br/>{esc(e["organization"])}<br/><sub>{esc(e["detail"])}</sub></td></tr>')
    readme = f'''<div align="center">

<img src="./assets/dossier.svg" width="100%" alt="Vachan U S — Cyberpunk Engineering Dossier"/>

<a href="https://github.com/{USER}">GITHUB</a> ·
<a href="{DATA["linkedin"]}">LINKEDIN</a> ·
<a href="{DATA["portfolio"]}">PORTFOLIO</a> ·
<a href="{DATA["devfolio"]}">DEVFOLIO</a> ·
<a href="mailto:{DATA["email"]}">EMAIL</a>

</div>

## OPERATOR PROFILE

**{DATA["name"]} — {DATA["role"]} @ {DATA["company"]}**

{DATA["bio"]}

**Location:** {DATA["location"]}  
**Education:** {DATA["education"]}

---

## PROJECT DOSSIERS

<table>
{''.join(projects)}
</table>

---

## ENGINEERING CAPABILITIES

{chr(10).join(skills)}

---

## CAREER & TRAINING

<table>
{''.join(experience)}
</table>

**Additional technical experience**

{chr(10).join("- "+esc(x) for x in DATA["additional"])}

---

## LIVE REPOSITORY DATA

<div align="center">
<img src="https://github-readme-stats.vercel.app/api?username={USER}&show_icons=true&theme=transparent&hide_border=true&title_color=FF168A&icon_color=20E8FF&text_color=C9D1D9&rank_icon=github" width="49%"/>
<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={USER}&layout=compact&theme=transparent&hide_border=true&title_color=FF168A&text_color=C9D1D9" width="49%"/>
</div>

---

## CONTRIBUTION NETWORK

<div align="center">
<img src="https://raw.githubusercontent.com/{USER}/{USER}/output/github-contribution-grid-snake-dark.svg" width="100%" alt="GitHub contribution snake"/>
</div>

---

<div align="center">

**THINK DIFFERENTLY. BUILD INTELLIGENTLY. ENGINEER RELIABLY.**

<img src="https://komarev.com/ghpvc/?username={USER}&style=flat-square&color=FF168A&label=PROFILE+VISITS"/>

<sub>VACHAN U S · NEON DISTRICT · LAST SYNC: {stamp}</sub>

</div>
'''
    (ROOT/"README.md").write_text(readme,encoding="utf-8")

def main():
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        user=api(f"/users/{USER}")
        repos=api(f"/users/{USER}/repos?per_page=100&sort=updated&type=owner")
    except Exception as exc:
        print(f"GitHub API request failed; leaving existing files unchanged: {exc}")
        raise
    stars=sum(r.get("stargazers_count",0) for r in repos)
    languages={}
    curated={p["url"].rstrip("/").split("/")[-1].lower() for p in DATA["projects"]}
    selected=[r for r in repos if r.get("name","").lower() in curated][:12]
    for repo in selected:
        try:
            for lang,count in api(f"/repos/{USER}/{repo['name']}/languages").items():
                languages[lang]=languages.get(lang,0)+count
        except Exception as exc:
            print(f"Skipping language data for {repo.get('name')}: {exc}")
    languages=dict(sorted(languages.items(),key=lambda item:item[1],reverse=True))
    generate_svg(user,repos,stars,languages,stamp)
    generate_readme(user,repos,stars,stamp)
    print(f"Generated dashboard: {len(repos)} public repositories; {stars} stars.")
if __name__=="__main__":
    main()
