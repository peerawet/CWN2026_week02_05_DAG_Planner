"""สร้าง homework/index.html: ตารางรวมการบ้านทั้ง 10 ข้อ ลิงก์ไป report.html ของแต่ละข้อ

usage: py -3 tools/build_index.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(ROOT, "homework")
SIZE = {"S": 0.6, "M": 1.5, "L": 3.0}
COLOR = {"yolo": "#7c3aed", "cyolo": "#059669", "image": "#db2777", "review": "#2563eb", "debate": "#475569", "best_of": "#d97706"}


def e(s):
    return html.escape(str(s), quote=True)


def answered(path):
    """ANSWER.md มีคำตอบแล้วหรือยัง: นับบรรทัดที่ไม่ใช่หัวข้อ คำอธิบายโจทย์ หรือ comment ของแม่แบบ"""
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S)
    return sum(1 for ln in text.splitlines() if ln.strip() and not ln.startswith(("#", ">")))


rows = []
for d in sorted(os.listdir(HW)):
    p = os.path.join(HW, d)
    if not os.path.isfile(os.path.join(p, "evidence", "plan.json")):
        continue
    with open(os.path.join(p, "blocks.json"), encoding="utf-8") as f:
        bd = json.load(f)
    with open(os.path.join(p, "evidence", "plan.json"), encoding="utf-8") as f:
        p4 = json.load(f)
    with open(os.path.join(p, "evidence", "plan-max2.json"), encoding="utf-8") as f:
        p2 = json.load(f)
    blocks = bd["blocks"]
    by = {b["id"]: b for b in blocks}
    crit = p4["critical_path"]
    skills = sorted({b["skill"] for b in blocks}, key=list(COLOR).index)
    span4 = max(v["end"] for v in p4["assign"].values()) * 60
    ok2 = sum(1 for v in p2["assign"].values() if v.get("status", "planned") == "planned")
    rows.append(dict(name=d, goal=bd["goal"], n=len(blocks), skills=skills, crit=crit,
                     crit_len=sum(SIZE[by[i]["size"]] for i in crit), span4=span4, ok2=ok2,
                     ans=answered(os.path.join(p, "ANSWER.md"))))

body = []
for k, r in enumerate(rows, 1):
    chips = " ".join(f'<span class="chip" style="background:{COLOR[s]}">{e(s)}</span>' for s in r["skills"])
    ans = '<span class="ok">เขียนแล้ว</span>' if r["ans"] >= 4 else '<span class="todo">ยังไม่เขียน</span>'
    body.append(f"""<tr><td>{k}</td>
<td><a href="{e(r['name'])}/report.html"><b>{e(r['name'])}</b></a><div class="muted">{e(r['goal'])}</div></td>
<td>{r['n']}</td><td>{chips}</td>
<td class="mono">{e(' → '.join(r['crit']))}<div class="muted">{r['crit_len']:g}M tok</div></td>
<td class="mono nw">{r['span4']:.1f} นาที</td>
<td class="mono nw {'bad' if r['ok2'] < r['n'] else ''}">{r['ok2']}/{r['n']} บล็อก</td>
<td>{ans}</td></tr>""")

page = f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>การบ้าน DAG Planner</title>
<style>
:root {{ --bg:#f6f7f9; --card:#fff; --text:#1c2230; --muted:#5b6475; --line:#e3e6ec; --accent:#e8590c; --ok:#1f8a4c; --bad:#c62828; --head:#1f3a5f; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#11141a; --card:#1a1f28; --text:#e6e9ef; --muted:#9aa3b2; --line:#2b3240; --accent:#ff8a4c; --ok:#5cc98a; --bad:#ff7b7b; --head:#24466f; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font-family:"Noto Sans Thai","Leelawadee UI","Sarabun",system-ui,sans-serif; line-height:1.6; }}
header {{ background:var(--head); color:#fff; padding:26px 16px; }}
header .in, main {{ max-width:1120px; margin:0 auto; }}
header h1 {{ margin:0 0 4px; font-size:24px; }} header p {{ margin:0; opacity:.9; }}
main {{ padding:18px 16px 48px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:20px; padding:18px 20px; }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:900px; font-size:14px; }}
th, td {{ border-bottom:1px solid var(--line); padding:9px 8px; text-align:start; vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; white-space:nowrap; }}
.muted {{ color:var(--muted); font-size:13px; }} .mono {{ font-family:ui-monospace,Consolas,monospace; font-size:13px; }}
.nw {{ white-space:nowrap; }} .ok {{ color:var(--ok); font-weight:600; }} .bad {{ color:var(--bad); }} .todo {{ color:var(--accent); font-weight:600; }}
.chip {{ display:inline-block; border-radius:999px; padding:0 8px; margin:1px 0; font-size:12px; color:#fff; white-space:nowrap; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
ul {{ margin:12px 0 0; padding-inline-start:20px; }}
</style>
</head>
<body>
<header><div class="in"><h1>การบ้านบท 05 · DAG Planner</h1>
<p>CWN2026 Week 02 · วางแผน 10 โจทย์ด้วยสกิล dag-planner (DAG + Gantt · ยังไม่รันจริง) · คลิกชื่อแผนเพื่อดูว่าแต่ละข้อเกิดอะไรขึ้น</p></div></header>
<main><div class="card"><div class="scroll"><table>
<tr><th>ข้อ</th><th>แผน · โจทย์</th><th>บล็อก</th><th>สกิลที่ใช้</th><th>สายวิกฤต</th><th>แผน 4 agent</th><th>ถ้าเหลือ 2 agent</th><th>ANSWER.md</th></tr>
{''.join(body)}
</table></div>
<ul class="muted">
<li>ทุกแผนใช้โควตาสมมติ yolo1:80 · yolo2:60 · cyolo1:90 · cyolo2:70 จึงไม่ได้เรียกบัญชีจริงและไม่ใช้โทเคนของทีม</li>
<li>“ถ้าเหลือ 2 agent” = จำนวนบล็อกที่ยังมีบัญชีรับ บล็อก debate (3 บัญชี) และ best_of (n+1) รับไม่ได้ และบล็อกที่รอมันอยู่ทำต่อไม่ได้ด้วย</li>
<li>ANSWER.md อาจารย์ให้เขียนเอง ข้อละ 4 คำถาม หน้า report.html ของแต่ละข้อบอกว่าข้อมูลที่ใช้ตอบอยู่ตรงไหน</li>
</ul></div></main>
</body>
</html>
"""
with open(os.path.join(HW, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
print(f"index: {len(rows)} ข้อ")
