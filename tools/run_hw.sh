#!/usr/bin/env bash
# รันการบ้าน 1 ข้อด้วย dagplan.py บนเครื่อง (โควตาสมมติ ไม่แตะบัญชีใด ไม่ใช้โทเคนของทีม)
# usage: bash tools/run_hw.sh <ชื่อแผน>
#   อ่าน  tools/src/<ชื่อแผน>.json        (blocks ที่แตกจากโจทย์)
#         tools/src/<ชื่อแผน>.notes.json  (เหตุผลตอนแตกบล็อก ใช้ทำ report.html)
#   เขียน homework/<ชื่อแผน>/            (5 ไฟล์ที่ต้องส่ง + report.html + evidence/)
set -euo pipefail
NAME=$1
ROOT=$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)
COURSE=${COURSE:-C:/Teaching_CWN2026/01_week02}
export DAGPLAN_DIR=$ROOT/.work/plans          # absolute (Chrome ต้องใช้) · อยู่ใน .gitignore
export DAGPLAN_BASE_SKILLS=$COURSE/06_KC_QUEST/base_skills
export DAGPLAN_CHROME=${DAGPLAN_CHROME:-"C:/Program Files/Google/Chrome/Application/chrome.exe"}
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
D=$COURSE/06_KC_QUEST/base_skills/dag-planner/scripts/dagplan.py
ACC=yolo1:80,yolo2:60,cyolo1:90,cyolo2:70
SRC=$ROOT/tools/src/$NAME.json
OUT=$ROOT/homework/$NAME
EV=$OUT/evidence
mkdir -p "$DAGPLAN_DIR" "$EV"
LOG=$EV/run.log

clean() { sed -e 's#\\#/#g' -e "s#$DAGPLAN_DIR/#plans/#g; s#$ROOT/##g; s#$COURSE#<course>#g"; }

run() {  # $1 = คำสั่งที่แสดงใน log, ที่เหลือ = คำสั่งจริง · exit code ≠ 0 ไม่หยุดสคริปต์ แต่บันทึกไว้
  local shown=$1; shift
  echo "\$ $shown" >>"$LOG"
  set +e
  "$@" 2>&1 | clean | tee -a "$LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  echo "(exit $rc)" >>"$LOG"
  echo >>"$LOG"
}

{
  echo "# run.log · $NAME"
  echo "# วันเวลา: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "# สกิล: dag-planner (base skill จาก 06_KC_QUEST/base_skills · ไฟล์ชุดเดียวกับ 05_DAG_Planner/_solution/skills/dag-planner)"
  echo "# สภาพแวดล้อม: รัน dagplan.py บนเครื่อง Windows ($(py -3 --version)) + Chrome headless วาด PNG"
  echo "#   ไม่ได้รันใน container multi-account เพราะ Docker Desktop ไม่ได้เปิด · ผลแผนเหมือนกันเพราะใช้โควตาสมมติ"
  echo "# โควตาสมมติ: --accounts $ACC (สกิลจึงไม่เรียกบัญชีใดเลย ไม่ใช้โทเคนของทีม)"
  echo "# ไม่ได้สั่ง export / run / report"
  echo
} >"$LOG"

# รอบหลัก: agent สูงสุด 4
run "python dagplan.py dag $NAME --blocks $NAME.json" py -3 "$D" dag "$NAME" --blocks "$SRC"
run "python dagplan.py plan $NAME --max-agents 4 --accounts $ACC" py -3 "$D" plan "$NAME" --max-agents 4 --accounts "$ACC"
P=$DAGPLAN_DIR/$NAME
cp "$P/blocks.json" "$P/dag.png" "$P/gantt-plan.png" "$P/PLAN.md" "$OUT/"
cp "$P/plan.json" "$EV/plan.json"

# รอบเทียบ (คำถามข้อ 4): แผนชื่อใหม่ จะได้ไม่ทับไฟล์ของรอบหลัก
A2=$NAME-a2
run "python dagplan.py dag $A2 --blocks $NAME.json" py -3 "$D" dag "$A2" --blocks "$SRC"
run "python dagplan.py plan $A2 --max-agents 2 --accounts $ACC" py -3 "$D" plan "$A2" --max-agents 2 --accounts "$ACC"
cp "$DAGPLAN_DIR/$A2/PLAN.md" "$EV/PLAN-max2.md"
cp "$DAGPLAN_DIR/$A2/gantt-plan.png" "$EV/gantt-plan-max2.png"
cp "$DAGPLAN_DIR/$A2/plan.json" "$EV/plan-max2.json"

# พรอมต์ของโจทย์ข้อนี้ (ตามแบบของอาจารย์)
GOAL=$(py -3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['goal'])" "$SRC")
cat >"$EV/prompt.txt" <<EOF
โจทย์: $GOAL
ชื่อแผน: $NAME
จำนวน agent สูงสุด: 4

ใช้ทีมเอเจนต์ใน container multi-account วางแผนงานนี้ ทำงานใน container ผ่าน docker exec เท่านั้น ห้ามแก้ไฟล์ตั้งค่า ห้ามล็อกอินแทนฉัน
ก่อนเริ่ม ดูว่าใน container มีสกิลที่ช่วยงานนี้ได้หรือไม่ (/root/ai-accounts/.Claude/shared/skills) ถ้ามีให้อ่านและใช้
1. แตกโจทย์เป็นบล็อกงาน 8–12 บล็อก แต่ละบล็อกบอกสกิลที่ใช้ทำ ความยาก ไฟล์ผล และเกณฑ์เสร็จ
2. วาด DAG แล้ววางแผนว่าบล็อกไหนให้บัญชีไหน เมื่อไร (Gantt) จากโควตาจริง
วางแผนเท่านั้น ห้ามสั่ง export run หรือ report
ใช้โควตาสมมติ: --accounts $ACC
เสร็จแล้วคัดลอก blocks.json dag.png gantt-plan.png และ PLAN.md ของแผนนี้มาไว้ที่ ./homework/$NAME/ บนเครื่อง
ตอบภาษาไทยสั้น ๆ: ตาราง บล็อก | ชื่อ | สกิล | ความยาก | ต้องรอ | rank · สายวิกฤตพร้อมเหตุผล 1 บรรทัด · ตาราง บล็อก | บัญชี | เริ่ม–จบ (นาที)

# หมายเหตุ: Docker Desktop ไม่ได้เปิด จึงรัน dagplan.py ตัวเดียวกันบนเครื่องแทน docker exec (รายละเอียดใน run.log)
EOF

# หน้าอธิบายผลสำหรับอ่านเอง
py -3 "$ROOT/tools/build_report.py" "$OUT" "$ROOT/tools/src/$NAME.notes.json"
echo "DONE $NAME"
