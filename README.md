# CWN2026 · Week 02 · การบ้านบท 05 DAG Planner

วางแผน 10 โจทย์ด้วยสกิล `dag-planner` (DAG + Gantt · วางแผนเท่านั้น ยังไม่รันจริง)
โจทย์และเกณฑ์ฉบับเต็ม: `Teaching_CWN2026/01_week02/05_DAG_Planner/homework/README.md`

**เริ่มอ่านที่ [`homework/index.html`](homework/index.html)** ตารางรวมทั้ง 10 ข้อ คลิกชื่อแผนเพื่อเปิด `report.html` ที่อธิบายว่าข้อนั้นเกิดอะไรขึ้นบ้าง

## สถานะ

| ข้อ | ชื่อแผน | บล็อก | 4 ไฟล์จากสกิล | ANSWER.md |
|---|---|---|---|---|
| 1 | [`hw01-catfood-next`](homework/hw01-catfood-next/report.html) | 10 | ✅ | ☐ เขียนเอง |
| 2 | [`hw02-gov-rag-k8s`](homework/hw02-gov-rag-k8s/report.html) | 11 | ✅ | ☐ เขียนเอง |
| 3 | [`hw03-clinic-line-queue`](homework/hw03-clinic-line-queue/report.html) | 10 | ✅ | ☐ เขียนเอง |
| 4 | [`hw04-iot-farm-dashboard`](homework/hw04-iot-farm-dashboard/report.html) | 9 | ✅ | ☐ เขียนเอง |
| 5 | [`hw05-receipt-ocr-api`](homework/hw05-receipt-ocr-api/report.html) | 10 | ✅ | ☐ เขียนเอง |
| 6 | [`hw06-churn-ml-pipeline`](homework/hw06-churn-ml-pipeline/report.html) | 10 | ✅ | ☐ เขียนเอง |
| 7 | [`hw07-expense-mobile`](homework/hw07-expense-mobile/report.html) | 11 | ✅ | ☐ เขียนเอง |
| 8 | [`hw08-cicd-microservices`](homework/hw08-cicd-microservices/report.html) | 10 | ✅ | ☐ เขียนเอง |
| 9 | [`hw09-course-media`](homework/hw09-course-media/report.html) | 9 | ✅ | ☐ เขียนเอง |
| 10 | [`hw10-ai-autograder`](homework/hw10-ai-autograder/report.html) | 10 | ✅ | ☐ เขียนเอง |

## ในแต่ละโฟลเดอร์

```text
homework/hw01-catfood-next/
├── blocks.json  dag.png  gantt-plan.png  PLAN.md   ← สกิลสร้าง (ต้องส่ง)
├── ANSWER.md                                        ← คำตอบ 4 ข้อ เขียนเอง (ต้องส่ง)
├── report.html                                      ← หน้าอธิบายผลสำหรับอ่านเอง
└── evidence/
    ├── prompt.txt                  ← พรอมต์ของข้อนี้
    ├── run.log                     ← คำสั่งที่รันจริงและผลลัพธ์ทุกบรรทัด
    ├── PLAN-max2.md  gantt-plan-max2.png  plan-max2.json   ← แผนเมื่อลดเหลือ 2 agent (ใช้ตอบข้อ 4)
    └── plan.json                   ← ข้อมูลดิบของแผนหลัก
```

## ทำมาอย่างไร

1. แตกโจทย์เป็นบล็อก → `tools/src/<แผน>.json` และเหตุผลตอนแตกบล็อก → `tools/src/<แผน>.notes.json`
2. `bash tools/run_hw.sh <แผน>` รัน `dagplan.py dag` และ `plan --max-agents 4` แล้วรันแผนแยกชื่อ `<แผน>-a2` ด้วย `--max-agents 2` (จะได้ไม่ทับไฟล์ของแผนหลัก) จากนั้นคัดลอกผลมาไว้ที่ `homework/<แผน>/` และสร้าง `report.html`
3. `py -3 tools/build_index.py` สร้าง `homework/index.html`

- ใช้โควตาสมมติ `--accounts yolo1:80,yolo2:60,cyolo1:90,cyolo2:70` ตามที่อาจารย์ให้ไว้ สกิลจึงไม่เรียกบัญชีจริงและไม่ใช้โทเคนของทีม
- รัน `dagplan.py` ของ base skill (`06_KC_QUEST/base_skills/dag-planner` ชุดเดียวกับ `05_DAG_Planner/_solution/skills/dag-planner`) บนเครื่อง Windows แทน `docker exec` เพราะตอนทำ Docker Desktop ไม่ได้เปิดอยู่ ผลแผนเหมือนกันเพราะใช้โควตาสมมติ
- ไม่ได้สั่ง `export` `run` หรือ `report`
- ต้องมี: Python 3 (`py -3`) · Google Chrome (ใช้วาด PNG) · repo ของวิชาที่ `C:/Teaching_CWN2026` (เปลี่ยนได้ด้วยตัวแปร `COURSE`)

## ตรวจก่อนส่ง (ข้อละ 10 คะแนน)

| เกณฑ์ | คะแนน | สถานะ |
|---|---|---|
| ไฟล์ครบ 5 ไฟล์ และ `dag` ไม่มี ERROR | 2 | `dag` ผ่านทุกข้อ · รอ ANSWER.md |
| 8–12 บล็อก ไม่มีบล็อกใหญ่เกิน L ทุกบล็อกมีไฟล์ผลและเกณฑ์เสร็จที่ตรวจได้ | 2 | ✅ 9–11 บล็อก |
| ลูกศรไม่ขาดและไม่เกิน บล็อกสุดท้ายเป็นรวมและทดสอบแบบ `exclusive` 🔒 | 2 | ✅ ทุกเส้นทางจบที่บล็อกรวม |
| เลือกสกิลเหมาะกับงาน ใช้ `review` · `debate` · `best_of` เฉพาะที่คุ้ม | 2 | ✅ เหตุผลอยู่ใน report.html |
| `ANSWER.md` ตอบครบ 4 ข้อ และคิด rank ด้วยมือถูก | 2 | ☐ เขียนเอง |
