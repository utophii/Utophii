#!/usr/bin/env python3

import html
import json
from pathlib import Path

import yaml

CONFIG = Path(__file__).parent / "config.yml"
STATS = Path(__file__).parent / "stats.json"
OUT = Path(__file__).parent / "profile.svg"

W = 860

DEFAULT_PALETTE = {
    "bg": "#F5F9FC", "surface": "#FFFFFF", "line": "#DDE9F3",
    "accent": "#6FA8D6", "accent_bg": "#E4F0F9",
    "text": "#3A5570", "text_mid": "#6E8CA6", "text_dim": "#A3B8CB",
    "green": "#7FBF9E",
}
DEFAULT_IDENTITY = {
    "username": "user", "display_nik": "user", "role": "", "sub": "",
    "principle_en": "", "status": "active", "status_level": "on",
}


def load():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["palette"] = {**DEFAULT_PALETTE, **(cfg.get("palette") or {})}
    cfg["identity"] = {**DEFAULT_IDENTITY, **(cfg.get("identity") or {})}
    cfg.setdefault("stack", {})
    cfg.setdefault("focus", [])
    cfg.setdefault("metrics", {})
    cfg.setdefault("streak", {})
    if STATS.exists():
        try:
            data = json.loads(STATS.read_text(encoding="utf-8"))
            if data.get("metrics"):
                cfg["metrics"].update(data["metrics"])
            if data.get("streak"):
                cfg["streak"].update(data["streak"])
            if "auto_projects" in data:
                cfg["auto_projects"] = data["auto_projects"]
            if data.get("activity"):
                cfg["identity"]["status"] = data["activity"].get(
                    "label", cfg["identity"]["status"])
                cfg["identity"]["status_level"] = data["activity"].get(
                    "level", "on")
        except (ValueError, OSError):
            pass
    return cfg


def esc(s):
    return html.escape(str(s), quote=True)


def render_focus(focus):
    if not focus:
        return ""
    chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in focus)
    return f'<div class="focus">{chips}</div>'


def render_stack(stack):
    rows = []
    for domain, tags in stack.items():
        pills = []
        for t in tags or []:
            name = t.get("name", "?") if isinstance(t, dict) else str(t)
            status = (t.get("status", "using")
                      if isinstance(t, dict) else "using")
            if status not in ("core", "using", "learning"):
                status = "using"
            pills.append(f'<span class="tag {status}">{esc(name)}</span>')
        rows.append(
            f'<div class="srow"><div class="sdom">{esc(domain)}</div>'
            f'<div class="stags">{"".join(pills)}</div></div>')
    return "".join(rows)


def render_metrics(m):
    items = [
        ("commits", m.get("commits", 0)),
        ("repos", m.get("repos", 0)),
        ("stars", m.get("stars", 0)),
        ("followers", m.get("followers", 0)),
    ]
    cells = "".join(
        f'<div class="mcell"><div class="mval">{esc(v)}</div>'
        f'<div class="mlbl">{esc(k)}</div></div>'
        for k, v in items)
    return f'<div class="metrics">{cells}</div>'


def render_streak(streak):
    cur = streak.get("current", 0)
    lon = streak.get("longest", 0)
    spark = list(streak.get("spark") or [0] * 14)[-14:]
    spark += [0] * (14 - len(spark))
    peak = max(max(spark), 1)
    bars = []
    for v in spark:
        h = max(3, round(v / peak * 26))
        cls = " lit" if v > 0 else ""
        bars.append(f'<i class="bar{cls}" style="height:{h}px"></i>')
    return (
        f'<div class="streak">'
        f'<div class="spark">{"".join(bars)}</div>'
        f'<div class="sinfo">'
        f'<span class="snum">{esc(cur)}</span><span class="sl">day streak</span>'
        f'<span class="sdiv">·</span>'
        f'<span class="snum dim">{esc(lon)}</span><span class="sl">longest</span>'
        f'</div></div>')


def pick_projects(cfg):
    proj = cfg.get("projects") or {}
    limit = int(proj.get("max", 3))
    if proj.get("mode") == "manual":
        items = proj.get("pinned") or []
    else:
        items = cfg.get("auto_projects") or proj.get("pinned") or []
    return items[:limit]


def render_projects(items):
    if not items:
        return '<div class="pempty">repositories load daily via actions</div>'
    cards = []
    for p in items:
        stars = p.get("stars", 0)
        star_html = (f'<span class="pstars">★ {esc(stars)}</span>'
                     if stars else "")
        lang = p.get("lang") or ""
        lang_html = f'<span class="plang">{esc(lang)}</span>' if lang else ""
        cards.append(
            f'<div class="proj">'
            f'<div class="ptop"><span class="pname">{esc(p.get("name", "?"))}'
            f'</span>{star_html}</div>'
            f'<div class="pdesc">{esc(p.get("desc") or "")}</div>'
            f'<div class="pmeta">{lang_html}</div>'
            f'</div>')
    return f'<div class="projects">{cards and "".join(cards)}</div>'


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
.root{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:%BG%;
  color:%TEXT%;padding:44px 52px 40px;position:relative;overflow:hidden;height:100%}
.wave{position:absolute;left:0;right:0;top:0;height:5px;
  background:linear-gradient(90deg,%ACCENT%,%ACCENT_BG% 60%,%ACCENT%)}
@keyframes fadeup{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}

.head{display:flex;align-items:flex-start;justify-content:space-between;
  animation:fadeup .6s ease backwards}
.nick{font-size:34px;font-weight:600;letter-spacing:.14em;color:%TEXT%}
.nick b{color:%ACCENT%;font-weight:600}
.role{margin-top:9px;font-size:14.5px;color:%TEXT_MID%;letter-spacing:.04em}
.sub{margin-top:5px;font-size:12px;color:%TEXT_DIM%;letter-spacing:.08em}
.status{display:flex;align-items:center;font-size:12px;color:%TEXT_MID%;
  background:%SURFACE%;border:1px solid %LINE%;border-radius:20px;
  padding:7px 15px;letter-spacing:.06em;white-space:nowrap}
.sdot{width:8px;height:8px;border-radius:50%;background:%GREEN%;margin-right:8px;
  animation:pulse 2.6s ease-in-out infinite}
.sdot.mid{background:%ACCENT%}
.sdot.off{background:%TEXT_DIM%;animation:none}

.focus{margin-top:20px;display:flex;flex-wrap:wrap;gap:8px;
  animation:fadeup .6s .1s ease backwards}
.chip{font-size:12px;color:%ACCENT%;background:%ACCENT_BG%;border-radius:14px;
  padding:5px 13px;letter-spacing:.04em}

.grid{display:flex;gap:22px;margin-top:26px}
.card{background:%SURFACE%;border:1px solid %LINE%;border-radius:14px;
  padding:20px 22px;animation:fadeup .6s ease backwards}
.card.stackc{flex:1.25;animation-delay:.15s}
.card.livec{flex:1;animation-delay:.25s;display:flex;flex-direction:column;
  justify-content:space-between}
.ct{font-size:11px;letter-spacing:.22em;color:%TEXT_DIM%;
  text-transform:uppercase;margin-bottom:15px}
.ct i{display:inline-block;width:6px;height:6px;border-radius:50%;
  background:%ACCENT%;margin-right:9px;vertical-align:1px}

.srow{display:flex;align-items:baseline;margin-bottom:11px}
.srow:last-child{margin-bottom:0}
.sdom{width:118px;flex:none;font-size:11px;color:%TEXT_DIM%;letter-spacing:.05em}
.stags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:11.5px;border-radius:10px;padding:3.5px 11px;letter-spacing:.02em}
.tag.core{background:%ACCENT%;color:#fff}
.tag.using{border:1px solid %LINE%;color:%TEXT_MID%;background:%BG%}
.tag.learning{border:1px dashed %LINE%;color:%TEXT_DIM%}

.metrics{display:flex;justify-content:space-between}
.mcell{text-align:center;flex:1}
.mval{font-size:24px;font-weight:600;color:%ACCENT%}
.mlbl{margin-top:3px;font-size:10.5px;letter-spacing:.14em;color:%TEXT_DIM%;
  text-transform:uppercase}
.streak{margin-top:18px;border-top:1px solid %LINE%;padding-top:16px}
.spark{display:flex;align-items:flex-end;gap:5px;height:28px}
.bar{flex:1;background:%LINE%;border-radius:3px 3px 0 0;transform-origin:bottom;
  animation:grow .5s .4s ease backwards}
.bar.lit{background:%ACCENT%}
.sinfo{margin-top:10px;font-size:11.5px;color:%TEXT_DIM%;letter-spacing:.05em}
.snum{font-size:15px;font-weight:600;color:%TEXT%;margin-right:5px}
.snum.dim{color:%TEXT_MID%}
.sdiv{margin:0 9px;color:%TEXT_DIM%}

.card.projc{margin-top:22px;animation-delay:.35s}
.projects{display:flex;gap:14px}
.proj{flex:1;background:%BG%;border:1px solid %LINE%;border-radius:11px;
  padding:14px 16px}
.ptop{display:flex;justify-content:space-between;align-items:baseline}
.pname{font-size:14px;font-weight:600;color:%TEXT%}
.pstars{font-size:11.5px;color:%ACCENT%}
.pdesc{margin-top:6px;font-size:11.5px;line-height:1.45;color:%TEXT_MID%;
  height:50px;overflow:hidden}
.pmeta{margin-top:8px}
.plang{font-size:10.5px;color:%TEXT_DIM%;letter-spacing:.08em;
  text-transform:uppercase}
.pempty{font-size:12px;color:%TEXT_DIM%;letter-spacing:.05em}

.foot{margin-top:24px;text-align:center;font-size:11.5px;color:%TEXT_DIM%;
  letter-spacing:.24em;text-transform:uppercase;
  animation:fadeup .6s .45s ease backwards}
.foot b{color:%ACCENT%;font-weight:400}
"""


def build(cfg):
    p = cfg["palette"]
    ident = cfg["identity"]

    css = CSS
    for key, token in [
        ("bg", "%BG%"), ("surface", "%SURFACE%"), ("line", "%LINE%"),
        ("accent", "%ACCENT%"), ("accent_bg", "%ACCENT_BG%"),
        ("text", "%TEXT%"), ("text_mid", "%TEXT_MID%"),
        ("text_dim", "%TEXT_DIM%"), ("green", "%GREEN%"),
    ]:
        css = css.replace(token, p[key])

    nick = esc(ident["display_nik"])
    if nick:
        nick = f"<b>{nick[0]}</b>{nick[1:]}"

    level = ident.get("status_level", "on")
    dot_cls = {"on": "", "mid": " mid", "off": " off"}.get(level, "")

    sub = (f'<div class="sub">{esc(ident["sub"])}</div>'
           if ident.get("sub") else "")

    principle = ident.get("principle_en", "")
    foot = (f'<div class="foot"><b>—</b>&#160;&#160;{esc(principle)}'
            f'&#160;&#160;<b>—</b></div>' if principle else "")

    body = f"""
<div class="root" xmlns="http://www.w3.org/1999/xhtml">
  <div class="wave"></div>
  <div class="head">
    <div>
      <div class="nick">{nick}</div>
      <div class="role">{esc(ident["role"])}</div>
      {sub}
    </div>
    <div class="status"><span class="sdot{dot_cls}"></span>{esc(ident["status"])}</div>
  </div>
  {render_focus(cfg["focus"])}
  <div class="grid">
    <div class="card stackc">
      <div class="ct"><i></i>stack</div>
      {render_stack(cfg["stack"])}
    </div>
    <div class="card livec">
      <div>
        <div class="ct"><i></i>this year</div>
        {render_metrics(cfg["metrics"])}
      </div>
      {render_streak(cfg["streak"])}
    </div>
  </div>
  <div class="card projc">
    <div class="ct"><i></i>projects</div>
    {render_projects(pick_projects(cfg))}
  </div>
  {foot}
</div>"""

    stack_rows = len(cfg["stack"])
    height = 650 + max(0, stack_rows - 4) * 40
    if cfg["focus"]:
        height += 42

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{esc(ident['username'])} profile">
<style>{css}</style>
<foreignObject x="0" y="0" width="{W}" height="{height}">{body}
</foreignObject>
</svg>
"""


def main():
    cfg = load()
    OUT.write_text(build(cfg), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
