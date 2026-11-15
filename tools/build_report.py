"""สร้าง report.html ของการบ้าน 1 ข้อ จากไฟล์ที่ dag-planner สร้าง + เหตุผลตอนแตกบล็อก (notes.json)

usage: py -3 tools/build_report.py homework/<ชื่อแผน> tools/src/<ชื่อแผน>.notes.json
อ่าน: blocks.json · evidence/plan.json · evidence/plan-max2.json · evidence/run.log
ตัวเลขทุกตัวในหน้านี้มาจากไฟล์ข้างบน ไม่ได้พิมพ์เอง (ยกเว้นข้อความเหตุผลใน notes.json)
"""
import html
import json
import os
import re
import sys

SIZE = {"S": 0.6, "M": 1.5, "L": 3.0}
ROLE = {"worker": "ทำ", "reviewer": "ตรวจ", "judge": "ตัดสิน", "candidate": "ตอบ", "debater": "ตอบ", "answer": "ตอบ"}
SKILL_INFO = {
    "yolo": ("🧠", "Claude 1 บัญชี · งานคิดยาว"),
    "cyolo": ("⚙️", "Codex 1 บัญชี · งานตรงไปตรงมา"),
    "image": ("🖼️", "Codex สร้างภาพ"),
    "review": ("🔍", "ผู้ทำ + ผู้ตรวจคนละ CLI · 2 บัญชี"),
    "debate": ("⚖️", "Claude vs Codex + ผู้ตัดสิน · 3 บัญชี"),
    "best_of": ("🏆", "หลายคนทำ + ผู้ตัดสิน · n+1 บัญชี"),
}
DIFF = {1: "haiku/low", 2: "sonnet/medium", 3: "opus/high", 4: "opus/xhigh", 5: "opus/max", 6: "opus/max"}


def e(s):
    return html.escape(str(s), quote=True)


def num(x):
    return f"{round(x, 2):g}"


def mins(h):
    return round(h * 60, 1)


def need_agents(b):
    s = b["skill"]
    return {"review": 2, "debate": 3, "best_of": int(b.get("n", 2)) + 1}.get(s, 1)


def chip(skill):
    icon = SKILL_INFO.get(skill, ("", ""))[0]
    return f'<span class="chip sk-{e(skill)}">{icon} {e(skill)}</span>'


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dag_section(log, name):
    """ข้อความผลของคำสั่ง dag รอบหลักใน run.log"""
    m = re.search(rf"^\$ python dagplan\.py dag {re.escape(name)} .*?$(.*?)^\(exit (\d+)\)", log, re.S | re.M)
    return (m.group(1).strip(), int(m.group(2))) if m else ("", -1)


def main(hw_dir, notes_path):
    blocks_doc = load(os.path.join(hw_dir, "blocks.json"))
    plan = load(os.path.join(hw_dir, "evidence", "plan.json"))
    plan2 = load(os.path.join(hw_dir, "evidence", "plan-max2.json"))
    notes = load(notes_path) if os.path.exists(notes_path) else {}
    with open(os.path.join(hw_dir, "evidence", "run.log"), encoding="utf-8") as f:
        log = f.read()

    name = blocks_doc["name"]
    goal = blocks_doc["goal"]
    blocks = blocks_doc["blocks"]
    by = {b["id"]: b for b in blocks}
    order = [b["id"] for b in blocks]
    succ = {i: [b["id"] for b in blocks if i in b.get("depends_on", [])] for i in order}
    rank = plan["rank"]
    crit = plan["critical_path"]
    crit_set = set(crit)
    crit_len = sum(SIZE[by[i]["size"]] for i in crit)

    # rank คิดเองจาก blocks แล้วเทียบกับที่สกิลคำนวณ
    calc = {}
    for i in order:
        c = SIZE[by[i]["size"]]
        if succ[i]:
            best = max(succ[i], key=lambda s: rank[s])
            parts = ", ".join((f"<b>{s} {num(rank[s])}</b>" if s == best else f"{s} {num(rank[s])}") for s in succ[i])
            calc[i] = (f"{num(c)} + max({parts}) = {num(c + rank[best])}", abs(c + rank[best] - rank[i]) < 0.01)
        else:
            calc[i] = (f"{num(c)} (ไม่มีบล็อกไหนรอ)", abs(c - rank[i]) < 0.01)
    rank_ok = all(ok for _, ok in calc.values())

    dag_out, dag_rc = dag_section(log, name)
    dag_error = dag_rc != 0 or "ERROR" in dag_out
    warns = [ln.strip(" ⚠") for ln in dag_out.splitlines() if "⚠" in ln or ln.strip().startswith("WARN")]

    # ---------- แผน 4 agent: เวลาเริ่ม/จบ และการรอ
    A = plan["assign"]
    rows4 = {}
    for i in order:
        a = A[i]
        st, en = mins(a["start"]), mins(a["end"])
        ready = max([mins(A[d]["end"]) for d in by[i].get("depends_on", [])] or [0.0])
        busy = sum(len(A[j]["accounts"]) for j in order
                   if j != i and A[j]["start"] * 60 <= ready + 1e-6 < A[j]["end"] * 60)
        rows4[i] = dict(start=st, end=en, ready=ready, wait=round(st - ready, 1),
                        accs=[(p["account"], ROLE.get(p["role"], p["role"])) for p in a["accounts"]],
                        busy=busy)
    span4 = max(r["end"] for r in rows4.values())
    max_agents = plan["max_agents"]
    # เส้นทางที่กำหนดเวลาจบของแผน: เริ่มจากบล็อกที่จบช้าสุด ย้อนไปหาบล็อกที่ต้องรอซึ่งจบช้าสุด
    cur = max(order, key=lambda i: rows4[i]["end"])
    tchain = [cur]
    while by[cur].get("depends_on"):
        cur = max(by[cur]["depends_on"], key=lambda d: rows4[d]["end"])
        tchain.append(cur)
    tchain.reverse()

    # ---------- แผน 2 agent
    A2 = plan2["assign"]
    st2 = {i: A2[i].get("status", "planned") for i in order}
    ok2 = [i for i in order if st2[i] == "planned"]
    span2 = max([mins(A2[i]["end"]) for i in ok2] or [0.0])
    unassigned = [i for i in order if st2[i] == "unassigned"]
    blocked = [i for i in order if st2[i] == "blocked"]

    files = [
        ("blocks.json", "บล็อกงานที่แตกจากโจทย์", True),
        ("dag.png", "DAG + rank + สายวิกฤต + บัญชีที่ได้งาน", True),
        ("gantt-plan.png", "Gantt แผน (agent สูงสุด 4)", True),
        ("PLAN.md", "ตารางแผนและเหตุผลที่ KC-QUEST เลือกบัญชี", True),
        ("ANSWER.md", "คำตอบ 4 ข้อ (ต้องเขียนเอง)", True),
        ("evidence/prompt.txt", "พรอมต์ของข้อนี้", False),
        ("evidence/run.log", "คำสั่งที่รันจริงและผลลัพธ์ทุกบรรทัด", False),
        ("evidence/PLAN-max2.md", "แผนเมื่อลด agent เหลือ 2", False),
        ("evidence/gantt-plan-max2.png", "Gantt เมื่อลด agent เหลือ 2", False),
        ("evidence/plan.json · plan-max2.json", "ข้อมูลดิบของทั้งสองแผน", False),
    ]

    H = []
    w = H.append
    w(f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(name)} · สรุปแผน</title>
<style>
:root {{
  --bg:#f6f7f9; --card:#ffffff; --text:#1c2230; --muted:#5b6475; --line:#e3e6ec;
  --accent:#e8590c; --accent-soft:#fff1e8; --ok:#1f8a4c; --ok-soft:#e6f6ec; --bad:#c62828; --bad-soft:#fdeaea;
  --head:#1f3a5f; --code:#f0f2f6;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#11141a; --card:#1a1f28; --text:#e6e9ef; --muted:#9aa3b2; --line:#2b3240;
    --accent:#ff8a4c; --accent-soft:#3a2418; --ok:#5cc98a; --ok-soft:#173326; --bad:#ff7b7b; --bad-soft:#3a1c1c;
    --head:#24466f; --code:#232a36;
  }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font-family:"Noto Sans Thai","Leelawadee UI","Sarabun",system-ui,sans-serif; line-height:1.65; font-size:16px; }}
header.top {{ background:var(--head); color:#fff; padding:28px 16px 22px; }}
header.top .in, main {{ max-width:1040px; margin:0 auto; }}
header.top h1 {{ margin:0 0 6px; font-size:26px; line-height:1.3; }}
header.top .goal {{ margin:0; opacity:.92; }}
.badges {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.badge {{ background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.25); border-radius:999px; padding:3px 12px; font-size:14px; }}
nav.toc {{ max-width:1040px; margin:0 auto; padding:12px 16px 0; display:flex; flex-wrap:wrap; gap:6px 14px; font-size:14px; }}
nav.toc a {{ color:var(--muted); text-decoration:none; }}
nav.toc a:hover {{ color:var(--accent); }}
main {{ padding:8px 16px 48px; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:20px; padding:20px 22px; margin-top:18px; }}
h2 {{ margin:0 0 12px; font-size:20px; }}
h3 {{ margin:18px 0 8px; font-size:16px; }}
p {{ margin:8px 0; }}
.muted {{ color:var(--muted); }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th, td {{ border-bottom:1px solid var(--line); padding:7px 8px; text-align:start; vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; white-space:nowrap; }}
.nw {{ white-space:nowrap; }}
table.wide {{ min-width:980px; }}
table.wide td.title {{ min-width:9em; }}
tr.crit td {{ background:var(--accent-soft); }}
code, .mono {{ font-family:ui-monospace,"Cascadia Code",Consolas,monospace; font-size:13px; }}
code {{ background:var(--code); padding:1px 5px; border-radius:6px; }}
.chip {{ display:inline-block; border-radius:999px; padding:1px 9px; font-size:13px; color:#fff; white-space:nowrap; }}
.sk-yolo {{ background:#7c3aed; }} .sk-cyolo {{ background:#059669; }} .sk-image {{ background:#db2777; }}
.sk-review {{ background:#2563eb; }} .sk-debate {{ background:#475569; }} .sk-best_of {{ background:#d97706; }}
.acc {{ display:inline-block; border:1px solid var(--line); border-radius:999px; padding:0 8px; margin:1px 2px; font-size:13px; white-space:nowrap; }}
.steps {{ list-style:none; padding:0; margin:0; counter-reset:s; }}
.steps li {{ position:relative; padding:4px 0 12px 44px; counter-increment:s; }}
.steps li::before {{ content:counter(s); position:absolute; inset-inline-start:0; top:2px; width:30px; height:30px; border-radius:50%;
  background:var(--head); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px; }}
.ok {{ color:var(--ok); font-weight:600; }} .bad {{ color:var(--bad); font-weight:600; }}
.callout {{ border-inline-start:4px solid var(--accent); background:var(--accent-soft); padding:10px 14px; border-radius:10px; margin:12px 0; }}
.fig {{ margin:12px 0; }}
.fig img {{ width:100%; height:auto; border:1px solid var(--line); border-radius:12px; background:#fff; display:block; }}
.fig figcaption {{ font-size:13px; color:var(--muted); margin-top:6px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.stat {{ border:1px solid var(--line); border-radius:14px; padding:12px 14px; }}
.stat .k {{ font-size:13px; color:var(--muted); }} .stat .v {{ font-size:22px; font-weight:700; }}
.qa {{ border:1px solid var(--line); border-radius:14px; padding:10px 14px; margin:10px 0; }}
.qa .q {{ font-weight:600; }}
a {{ color:var(--accent); }}
@media (max-width:640px) {{ .grid2 {{ grid-template-columns:1fr; }} header.top h1 {{ font-size:22px; }} section {{ padding:16px; }} }}
</style>
</head>
<body>
<header class="top"><div class="in">
<h1>{e(name)}</h1>
<p class="goal">โจทย์: {e(goal)}</p>
<div class="badges">
  <span class="badge">{len(blocks)} บล็อก</span>
  <span class="badge">dag: {"มี ERROR" if dag_error else "ไม่มี ERROR"}</span>
  <span class="badge">สายวิกฤต {num(crit_len)}M tok</span>
  <span class="badge">แผน {max_agents} agent ≈ {span4:.1f} นาที</span>
  <span class="badge">วางแผนเมื่อ {e(plan["created"][:16].replace("T", " "))}</span>
</div>
</div></header>
<nav class="toc">
  <a href="#what">เกิดอะไรขึ้น</a><a href="#blocks">บล็อกงาน</a><a href="#rank">DAG · rank · สายวิกฤต</a>
  <a href="#gantt">Gantt</a><a href="#decisions">เหตุผลตอนแตกบล็อก</a><a href="#max2">ลดเหลือ 2 agent</a>
  <a href="#files">ไฟล์</a><a href="#todo">ยังต้องทำเอง</a>
</nav>
<main>
""")

    # ---------- 1 สรุป + ขั้นตอน
    w(f"""<section id="what">
<h2>เกิดอะไรขึ้นบ้าง</h2>
<p>{e(notes.get("summary", ""))}</p>
<ol class="steps">
  <li><b>แตกโจทย์เป็น {len(blocks)} บล็อก</b> บอกสกิล ขนาด ความยาก ไฟล์ผล และเกณฑ์เสร็จ ของทุกบล็อก → <code>blocks.json</code></li>
  <li><b>สั่ง <code>dag</code></b> สกิลตรวจไฟล์บล็อก (วงวน id ซ้ำ สกิลที่ไม่รู้จัก) แล้วคิด rank และสายวิกฤต →
      {'<span class="bad">มี ERROR</span>' if dag_error else '<span class="ok">ผ่าน ไม่มี ERROR</span>'} · สายวิกฤต {" → ".join(crit)} ยาว {num(crit_len)}M tok</li>
  <li><b>สั่ง <code>plan --max-agents {max_agents}</code></b> KC-QUEST แจกบล็อกให้บัญชีจากโควตาสมมติ แล้วจำลองเวลา →
      แจกได้ {sum(1 for i in order if A[i].get("status", "planned") == "planned")}/{len(blocks)} บล็อก · ใช้ agent พร้อมกันสูงสุด {plan["peak_agents"]}/{max_agents} · ≈ {span4:.1f} นาที →
      <code>dag.png</code> <code>gantt-plan.png</code> <code>PLAN.md</code></li>
  <li><b>สั่ง <code>plan --max-agents 2</code></b> เป็นแผนแยกชื่อ <code>{e(name)}-a2</code> จะได้ไม่ทับไฟล์ของข้อ 3 →
      แจกได้ {len(ok2)}/{len(blocks)} บล็อก → <code>evidence/PLAN-max2.md</code></li>
  <li><b>หยุดที่แผน</b> ไม่ได้สั่ง <code>export</code> <code>run</code> <code>report</code> ตามที่อาจารย์กำหนด จึงไม่ใช้โทเคนของทีม</li>
</ol>
<p class="muted">โควตาที่ใช้เป็นค่าสมมติ <code>--accounts yolo1:80,yolo2:60,cyolo1:90,cyolo2:70</code> สกิลจึงไม่เรียกบัญชีจริงเลย
รันด้วย <code>dagplan.py</code> ตัวเดียวกับในสกิลบนเครื่อง Windows แทน <code>docker exec</code> เพราะตอนนั้น Docker Desktop ไม่ได้เปิดอยู่ (คำสั่งที่รันจริงอยู่ใน <a href="evidence/run.log">evidence/run.log</a>)</p>
{"".join(f'<p class="muted">⚠ {e(x)}</p>' for x in warns)}
</section>
""")

    # ---------- 2 ตารางบล็อก
    w('<section id="blocks"><h2>บล็อกงาน</h2><p class="muted">แถวสีส้มคือบล็อกบนสายวิกฤต · ขนาด S/M/L = 0.6/1.5/3 ล้านโทเคน · ความยาก 1–6 เลือกรุ่นและ effort ของโมเดล</p><div class="scroll"><table class="wide">')
    w("<tr><th>บล็อก</th><th>ชื่อ</th><th>สกิล</th><th>ขนาด</th><th>ยาก</th><th>ต้องรอ</th><th>rank</th><th>บัญชี (บทบาท)</th><th>นาที</th><th>ไฟล์ผล · เกณฑ์เสร็จ</th></tr>")
    for i in order:
        b, r = by[i], rows4[i]
        accs = "".join(f'<span class="acc">{e(a)} · {e(role)}</span>' for a, role in r["accs"])
        lock = " 🔒" if b.get("exclusive") else ""
        w(f'<tr class="{"crit" if i in crit_set else ""}"><td class="nw"><b>{e(i)}</b>{lock}</td><td class="title">{e(b["title"])}</td><td>{chip(b["skill"])}</td>'
          f'<td class="nw">{e(b["size"])} · {num(SIZE[b["size"]])}</td><td title="{e(DIFF.get(b.get("difficulty", 2), ""))}">{e(b.get("difficulty", 2))}</td>'
          f'<td>{e(", ".join(b.get("depends_on", [])) or "–")}</td><td><b>{num(rank[i])}</b></td><td>{accs}</td>'
          f'<td class="mono nw">{r["start"]:.1f}–{r["end"]:.1f}</td>'
          f'<td><code>{e(b["output"])}</code><br><span class="muted">{e(b["done"])}</span></td></tr>')
    w("</table></div></section>")

    # ---------- 3 DAG + rank
    first = crit[0]
    w(f"""<section id="rank">
<h2>DAG · rank · สายวิกฤต</h2>
<figure class="fig"><a href="dag.png"><img src="dag.png" alt="DAG ของ {e(name)}: กล่องคือบล็อก ลูกศรคือการรอ ขอบส้มคือสายวิกฤต {e(' → '.join(crit))}"></a>
<figcaption>กล่อง = บล็อก · ลูกศร A → B = B ต้องรอไฟล์ผลของ A · ป้ายสี = สกิล · ป้ายล่าง = บัญชีที่ได้งาน · ขอบส้ม = สายวิกฤต · 🔒 = รวมและทดสอบ รันคนเดียว (คลิกเพื่อดูภาพเต็ม)</figcaption></figure>
<h3>rank คิดอย่างไร</h3>
<p><b>rank = ขนาดของบล็อก + rank สูงสุดของบล็อกที่รอมันอยู่</b> คิดย้อนจากบล็อกสุดท้าย ใช้ <code>max</code> ไม่ใช่บวกทั้งหมด เพราะบล็อกที่รออยู่ทำพร้อมกันได้ (ตัวหนา = ตัวที่มากที่สุด)</p>
<div class="scroll"><table><tr><th>บล็อก</th><th>ขนาด</th><th>บล็อกที่รออยู่</th><th>คำนวณ</th><th>rank</th></tr>""")
    for i in sorted(order, key=lambda x: (rank[x], x)):
        w(f'<tr class="{"crit" if i in crit_set else ""}"><td><b>{e(i)}</b></td><td>{num(SIZE[by[i]["size"]])}</td>'
          f'<td>{e(", ".join(succ[i]) or "–")}</td><td class="mono">{calc[i][0]}</td><td><b>{num(rank[i])}</b></td></tr>')
    w(f"""</table></div>
<p>{'<span class="ok">✔ rank ที่คิดเองตรงกับที่สกิลคำนวณทุกบล็อก</span>' if rank_ok else '<span class="bad">✘ rank ที่คิดเองไม่ตรงกับสกิล ตรวจอีกครั้ง</span>'}</p>
<h3>สายวิกฤต</h3>
<p>เริ่มที่บล็อก rank สูงสุด แล้วเดินไปหาบล็อกที่รออยู่ซึ่ง rank สูงสุดทีละก้าว:
<b>{" → ".join(f"{i} ({num(rank[i])})" for i in crit)}</b></p>
<p>ความยาว = {" + ".join(num(SIZE[by[i]["size"]]) for i in crit)} = <b>{num(crit_len)}M tok</b> เท่ากับ rank ของ {e(first)} พอดี
บล็อกบนสายนี้ช้าเท่าไร ทั้งโปรเจกต์ช้าเท่านั้น จึงได้เลือกบัญชีก่อน</p>
</section>
""")

    # ---------- 4 Gantt
    waited = [i for i in order if rows4[i]["wait"] > 0.05]
    w(f"""<section id="gantt">
<h2>Gantt แผน (agent สูงสุด {max_agents})</h2>
<figure class="fig"><a href="gantt-plan.png"><img src="gantt-plan.png" alt="Gantt แผนของ {e(name)} รวมประมาณ {span4:.1f} นาที"></a>
<figcaption>แถว = บัญชี (บัญชีเดียวรับได้หลายงานพร้อมกันตาม slot จึงมีแถว #2) · แท่ง = บล็อก · เส้นประ = บล็อกเดียวกันที่ใช้หลายบัญชี · เวลา = โทเคนประเมิน ÷ ความเร็วของ CLI (Codex ช้ากว่า Claude)</figcaption></figure>
<h3>เริ่มงานรอบไหนบ้าง</h3>
<div class="scroll"><table><tr><th>นาทีที่</th><th>บล็อกที่เริ่ม</th></tr>""")
    for rd in plan["rounds"]:
        cells = ", ".join(f'{e(i)} → {e("+".join(a for a, _ in rows4[i]["accs"]))}' for i in rd["start"])
        w(f'<tr><td class="mono">{rd["t_min"]:g}</td><td>{cells}</td></tr>')
    w("</table></div>")
    if waited:
        w("<h3>บล็อกที่พร้อมแล้วแต่ต้องรอ</h3>"
          "<p class='muted'>“พร้อม” = บล็อกที่ต้องรอเสร็จครบแล้ว · ตัวเลข agent นับตอนที่บล็อกพร้อม รวมบล็อกที่ KC-QUEST เพิ่งจองในรอบเดียวกัน</p>"
          "<div class='scroll'><table><tr><th>บล็อก</th><th>พร้อมเมื่อ</th><th>เริ่มจริง</th><th>รอ</th><th>สาเหตุ</th></tr>")
        for i in waited:
            r = rows4[i]
            need = need_agents(by[i])
            full = r["busy"] + need > max_agents
            why = (f"agent ใช้อยู่ {r['busy']}/{max_agents} บล็อกนี้ต้องใช้ {need} จึงไม่พอ" if full
                   else f"agent ยังว่าง ({r['busy']}/{max_agents}) แต่บัญชีที่เหมาะยังไม่ว่าง")
            w(f'<tr><td class="nw"><b>{e(i)}</b> {chip(by[i]["skill"])}</td><td class="mono">{r["ready"]:.1f}</td><td class="mono">{r["start"]:.1f}</td>'
              f'<td class="mono nw">{r["wait"]:.1f} นาที</td><td>{why}</td></tr>')
        w("</table></div>")
    same = tchain == crit
    w(f'<h3>ทำไมแผนยาว {span4:.1f} นาที</h3>'
      f'<p>เส้นทางที่กำหนดเวลาจบของแผน (ย้อนจากบล็อกที่จบช้าสุด ไปหาบล็อกที่ต้องรอซึ่งจบช้าสุด): <b>{e(" → ".join(tchain))}</b> · '
      + ('<span class="ok">ตรงกับสายวิกฤตจาก rank</span>' if same else
         f'<span class="bad">ไม่ตรงกับสายวิกฤตจาก rank ({e(" → ".join(crit))})</span>') + '</p>'
      '<div class="scroll"><table><tr><th>บล็อก</th><th>สกิล</th><th>ขนาด</th><th>เริ่ม–จบ</th><th>ใช้เวลา</th><th>รอก่อนเริ่ม</th></tr>')
    for i in tchain:
        r = rows4[i]
        wait_txt = "–" if r["wait"] <= 0.05 else f'{r["wait"]:.1f} นาที'
        w(f'<tr class="{"crit" if i in crit_set else ""}"><td><b>{e(i)}</b></td><td>{chip(by[i]["skill"])}</td><td>{e(by[i]["size"])}</td>'
          f'<td class="mono nw">{r["start"]:.1f}–{r["end"]:.1f}</td><td class="mono nw">{r["end"] - r["start"]:.1f} นาที</td>'
          f'<td class="mono nw">{wait_txt}</td></tr>')
    w("</table></div>")
    if not same:
        w('<p class="muted">rank คิดจากขนาดโทเคนอย่างเดียว แต่เวลาใน Gantt ขึ้นกับอีก 3 อย่าง: ความเร็วของ CLI (Codex ช้ากว่า Claude) '
          'ขั้นตรวจหรือตัดสินที่ต่อท้าย (review · debate · best_of) และการรอ agent หรือบัญชีว่าง เส้นทางที่ทำให้จบช้าจริงจึงอาจไม่ใช่สายวิกฤต</p>')
    if notes.get("gantt_note"):
        w(f'<div class="callout">{e(notes["gantt_note"])}</div>')
    w("</section>")

    # ---------- 5 เหตุผล
    w('<section id="decisions"><h2>เหตุผลตอนแตกบล็อก</h2>')
    if notes.get("hints"):
        w('<h3>จุดที่อาจารย์ให้คิด</h3>')
        for h in notes["hints"]:
            w(f'<div class="qa"><div class="q">{e(h["q"])}</div><div>{e(h["a"])}</div></div>')
    if notes.get("skills"):
        w('<h3>เลือกสกิลอย่างไร</h3><div class="scroll"><table><tr><th>บล็อก</th><th>สกิล</th><th>เหตุผล</th></tr>')
        for s in notes["skills"]:
            w(f'<tr><td><b>{e(s["blocks"])}</b></td><td>{chip(s["skill"])}</td><td>{e(s["why"])}</td></tr>')
        w("</table></div>")
    if notes.get("arrows_needed") or notes.get("no_arrow"):
        w('<h3>ลูกศร</h3><div class="grid2"><div>')
        w('<p><b>ลูกศรที่ตัดไม่ได้</b></p>')
        for a in notes.get("arrows_needed", []):
            w(f'<div class="qa"><div class="q mono">{e(a["edge"])}</div><div>{e(a["why"])}</div></div>')
        w('</div><div><p><b>ตั้งใจไม่ใส่ลูกศร เพื่อให้ทำพร้อมกันได้</b></p>')
        for a in notes.get("no_arrow", []):
            w(f'<div class="qa"><div class="q mono">{e(a["pair"])}</div><div>{e(a["why"])}</div></div>')
        w("</div></div>")
    w("</section>")

    # ---------- 6 max 2
    w(f"""<section id="max2">
<h2>ถ้าลด agent สูงสุดจาก {max_agents} เหลือ 2</h2>
<div class="grid2">
  <div class="stat"><div class="k">agent สูงสุด {max_agents}</div><div class="v">{len(blocks)}/{len(blocks)} บล็อก · ≈ {span4:.1f} นาที</div><div class="muted">ทั้งโปรเจกต์เสร็จ</div></div>
  <div class="stat"><div class="k">agent สูงสุด 2</div><div class="v">{len(ok2)}/{len(blocks)} บล็อก{f' · ≈ {span2:.1f} นาที' if ok2 else ''}</div>
    <div class="{'bad' if len(ok2) < len(blocks) else 'ok'}">{'โปรเจกต์ไม่เสร็จ: เวลานี้นับเฉพาะบล็อกที่ได้ทำ' if len(ok2) < len(blocks) else 'ทั้งโปรเจกต์เสร็จ'}</div></div>
</div>""")
    if unassigned or blocked:
        w('<div class="scroll"><table><tr><th>บล็อก</th><th>สถานะ</th><th>เพราะอะไร</th></tr>')
        for i in unassigned:
            w(f'<tr><td><b>{e(i)}</b> {chip(by[i]["skill"])}</td><td class="bad">ไม่มีบัญชีรับ</td>'
              f'<td>สกิล {e(by[i]["skill"])} ต้องใช้ {need_agents(by[i])} agent พร้อมกัน แต่เพดานคือ 2</td></tr>')
        for i in blocked:
            deps = [d for d in by[i].get("depends_on", []) if st2[d] != "planned"]
            w(f'<tr><td><b>{e(i)}</b> {chip(by[i]["skill"])}</td><td class="bad">ถูกบล็อก</td>'
              f'<td>ต้องรอ {e(", ".join(deps))} ซึ่งไม่ได้ทำ</td></tr>')
        w("</table></div>")
    w(f"""<figure class="fig"><a href="evidence/gantt-plan-max2.png"><img src="evidence/gantt-plan-max2.png" alt="Gantt เมื่อจำกัด 2 agent"></a>
<figcaption>Gantt เมื่อจำกัด 2 agent (แผนแยกชื่อ {e(name)}-a2 · ไฟล์เต็มใน evidence/PLAN-max2.md)</figcaption></figure>
<p class="muted">บทเรียน: บล็อกที่ใช้หลายบัญชี (review 2 · debate 3 · best_of n+1) ต้องมีเพดาน agent พอ ไม่อย่างนั้นทั้งบล็อกนั้นและทุกบล็อกที่รอมันอยู่จะไม่ได้ทำเลย</p>
</section>
""")

    # ---------- 7 ไฟล์
    w('<section id="files"><h2>ไฟล์ในโฟลเดอร์นี้</h2><div class="scroll"><table><tr><th>ไฟล์</th><th>คืออะไร</th><th></th></tr>')
    for fn, desc, req in files:
        link = fn.split(" · ")[0]
        w(f'<tr><td><a href="{e(link)}"><code>{e(fn)}</code></a></td><td>{e(desc)}</td><td>{"ต้องส่ง" if req else "หลักฐาน"}</td></tr>')
    w("</table></div></section>")

    # ---------- 8 todo
    w(f"""<section id="todo">
<h2>ยังต้องทำเอง: ANSWER.md</h2>
<p>อาจารย์ให้เขียน <a href="ANSWER.md"><code>ANSWER.md</code></a> เอง ข้อละ 1–3 บรรทัด หน้านี้มีข้อมูลที่ใช้ตอบครบ:</p>
<div class="scroll"><table><tr><th>ข้อ</th><th>ถามอะไร</th><th>ดูที่</th></tr>
<tr><td>1</td><td>สายวิกฤต ยาวเท่าไร คิด rank ของบล็อกแรก ({e(first)}) ด้วยมือ</td><td><a href="#rank">DAG · rank · สายวิกฤต</a></td></tr>
<tr><td>2</td><td>บล็อกไหนใช้ review · debate · best_of · image เพราะอะไร</td><td><a href="#decisions">เลือกสกิลอย่างไร</a></td></tr>
<tr><td>3</td><td>ลูกศรที่ตัดไม่ได้ 1 เส้น และคู่ที่ตั้งใจไม่ใส่ลูกศร 1 คู่</td><td><a href="#decisions">ลูกศร</a></td></tr>
<tr><td>4</td><td>ลดเหลือ 2 agent แล้วเปลี่ยนอย่างไร</td><td><a href="#max2">ลดเหลือ 2 agent</a></td></tr>
</table></div>
</section>
</main>
</body>
</html>
""")
    out = os.path.join(hw_dir, "report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(H))
    print(f"report: {out} · rank ตรงกับสกิล: {rank_ok} · dag ERROR: {dag_error}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
