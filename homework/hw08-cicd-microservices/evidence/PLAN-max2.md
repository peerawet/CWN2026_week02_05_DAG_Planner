# PLAN · hw08-cicd-microservices

**โจทย์:** แยกระบบร้านค้าเดิม (monolith) เป็น 3 microservices มี API gateway CI/CD ด้วย GitHub Actions และ deploy ขึ้น Kubernetes ด้วย Helm

วางแผนเมื่อ 15/11/2026 14:10 · MAX_AGENTS 2 · บัญชี cyolo1, cyolo2, yolo1, yolo2 · ตัวปรับเวลา k (ยังไม่มี calib.json → k=1)

> แผนนี้ยังไม่ได้รันจริง — KC-QUEST เลือกบัญชีจากโควตา แล้วจำลองเวลาตาม dependency

## 1) โควตาของแต่ละบัญชี

| บัญชี | แพลน | ใช้ไป 5 ชม. | ใช้ไปสัปดาห์ | headroom | รีเซ็ต/หมดอายุ (ชม.) | U | slot | ที่มา |
|---|---|---|---|---|---|---|---|---|
| cyolo1 | default | 10% | 0% | **90%** | 168.0 | 0.125 | 3 | สมมติ (--accounts) |
| cyolo2 | default | 30% | 0% | **70%** | 168.0 | 0.125 | 3 | สมมติ (--accounts) |
| yolo1 | default | 20% | 0% | **80%** | 168.0 | 0.125 | 3 | สมมติ (--accounts) |
| yolo2 | default | 40% | 0% | **60%** | 168.0 | 0.125 | 3 | สมมติ (--accounts) |

- ⚠ ทุกบัญชีเป็นค่าสมมติ (--accounts มี % ครบ) → ไม่ได้เรียก team.py check/quota

## 2) DAG + สกิล + บัญชี

![DAG](dag.png)

**สายวิกฤต:** B01 → B02 → B04 → B10 · ยาว 6.6M tok

## 3) ตารางแจกงาน (เหตุผล KC-QUEST ทุกบล็อก)

| บล็อก | สกิล | ชื่อ | ขนาด · c | รอ | rank | บัญชี (บทบาท) | เริ่ม–จบ (นาที) | เหตุผล KC-QUEST |
|---|---|---|---|---|---|---|---|---|
| **B01** | ⚙️ cyolo | โครง monorepo + monolith เดิม | S · 0.6 | – | 6.6 | cyolo1 (ทำ) | 0.0–7.5 | ทำ: cyolo1 28.8 (U=0.125 F=0.002 S=0.884 S=0.7 L=0.0) · 0.60M ≈ 5ชม. 1.56% / สัปดาห์ 0.2% · อันดับ 2 cyolo2 25.8 |
| **B02** | ⚖️ debate | แบ่งขอบเขต 3 บริการ + สัญญา API | M · 1.5 | B01 | 6 | ❌ | unassigned | ไม่มีบัญชีชุดไหนปิดบล็อกนี้ได้ (แบ่งให้เล็กลง / เพิ่มบัญชี / ลด n) |
| **B04** | 🧠 yolo | บริการ order | L · 3 | B02 | 4.5 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B07 | ⚙️ cyolo | Helm chart | M · 1.5 | B02 | 4.5 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B08 | ⚙️ cyolo | CI (GitHub Actions) | M · 1.5 | B02 | 4.5 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B03 | ⚙️ cyolo | บริการ catalog | M · 1.5 | B02 | 3 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B05 | ⚙️ cyolo | บริการ user | M · 1.5 | B02 | 3 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B09 | 🔍 review | CD deploy ด้วย Helm | M · 1.5 | B07, B08 | 3 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| B06 | ⚙️ cyolo | API gateway | S · 0.6 | B02 | 2.1 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |
| **B10** | 🧠 yolo | รวม + ทดสอบ end-to-end | M · 1.5 | B03, B04, B05, B06, B09 | 1.5 | ❌ | blocked | รอบล็อกที่ไม่มีบัญชีรับ |

## 4) Gantt แผน

![Gantt](gantt-plan.png)

## 5) รอบแจกงาน

| นาทีที่ | บล็อกที่เริ่ม |
|---|---|
| 0 | B01→cyolo1 |

## 6) สรุป

- บล็อก 10 · แจกได้ 1 · agent พร้อมกันสูงสุด 1/2
- เวลาประมาณ 7.5 นาที (แท่ง Gantt) · ไฟล์ผลของทีม: `C:/CWN2026-homework/.work/plans\hw08-cicd-microservices-a2\app/`
- ⚠ บล็อกที่ไม่มีบัญชีรับ: B02, B03, B04, B05, B06, B07, B08, B09, B10 → แบ่งให้เล็กลง / เพิ่มบัญชี / ลด n

ต่อไป: `dagplan.py export hw08-cicd-microservices-a2` → `dagplan.py run hw08-cicd-microservices-a2` → `dagplan.py report hw08-cicd-microservices-a2`
