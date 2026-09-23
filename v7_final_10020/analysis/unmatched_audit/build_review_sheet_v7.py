# -*- coding: utf-8 -*-
"""L16 검수 엑셀 — 표본 600건(광고·미디어·지역 각 200)에 모델 판독(Y/N)과 사유를 넣고, 저자가 O/X를 적을 열을 둔다.
  O = 모델 판독이 맞다,  X = 틀리다 (모델이 Y라 했는데 아니거나, N이라 했는데 잡혔어야 함)
시트: 안내 / 광고 / 미디어 / 지역 / 사전후보 / 집계(O·X 수식)
출력: review_sheet_v7.xlsx (이 폴더).  실행: python v7_final_10020/analysis/unmatched_audit/build_review_sheet_v7.py
되돌리기: O/X를 채운 파일을 같은 이름으로 두고  python v7_final_10020/analysis/build_unmatched_audit_samples_v7.py --summarize-xlsx  (또는 집계 시트의 수식).
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
NAMES = {"ad": "광고", "media": "미디어", "region": "지역"}
DESC = {"ad": "광고·상업성 지수(31개 신호 + 부정 가드)에 잡혔어야 하는 문장인가 — 브랜드 앰버서더·광고 모델·협찬·파트너십 같은 상업 계약 신호",
        "media": "미디어·콘텐츠 노출 지수(예능/유튜브/영화/드라마 서브태그)에 잡혔어야 하는 문장인가 — 방송·예능·라디오·영화·드라마·서바이벌 출연",
        "region": "국내 지역 지수(17개 시·도 48개 키워드)에 잡혔어야 하는 문장인가 — 국내 지역·도시 이름 언급"}
wb = Workbook(); ws = wb.active; ws.title = "안내"
hdr = Font(bold=True); fill = PatternFill("solid", fgColor="E8EEF3"); yfill = PatternFill("solid", fgColor="FFF4CC")
lines = ["보조지표 사전 매칭 누락 검수 — 저자 판정 시트", "",
         "각 시트의 문장은 해당 지수의 사전에 '잡히지 않은' 불릿 중 무작위 200건이다(seed 0).",
         "'모델 판독' 열은 Claude가 읽고 적은 것: Y = 이 지표에 잡혔어야 함(사전 누락), N = 아님.",
         "'저자 판정' 열에 O(판독이 맞다) 또는 X(틀리다)를 적는다. X이면 '메모'에 이유를 적어 주면 사전 갱신에 쓴다.",
         "Y 행(노란색)만 봐도 되고, N 행 중 잡혔어야 할 것이 보이면 X를 적어 준다.",
         "집계 시트가 O/X 수를 세고, 표본 누락 비율·재현율 추정치를 다시 계산한다.", "",
         "시트별 질문:"] + [f"  {NAMES[k]}: {v}" for k, v in DESC.items()]
for i, t in enumerate(lines, 1): ws.cell(row=i, column=1, value=t)
ws["A1"].font = Font(bold=True, size=13); ws.column_dimensions["A"].width = 120
COL = "검수(Y=해당 지표에 잡혔어야 함, N=아님)"
stats = {}
for k, nm in NAMES.items():
    rows = list(csv.DictReader(open(HERE / f"unmatched_sample_{k}_v7.csv", encoding="utf-8-sig")))
    sh = wb.create_sheet(nm); head = ["번호", "팬덤", "유형", "문장", "힌트어(사전 밖 유사 표현)", "모델 판독(Y/N)", "판독 사유", "저자 판정(O/X)", "메모"]
    sh.append(head)
    for c in range(1, len(head) + 1): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
    for i, r in enumerate(rows, 1):
        sh.append([i, r["fandom"], r["bullet_type"], r["text"], r["hint_terms_found"], r[COL], r["사유·놓친 표현"], "", ""])
        if r[COL] == "Y":
            for c in range(1, len(head) + 1): sh.cell(row=i + 1, column=c).fill = yfill
        sh.cell(row=i + 1, column=4).alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"O,X"', allow_blank=True); sh.add_data_validation(dv); dv.add(f"H2:H{len(rows) + 1}")
    for col, w in zip("ABCDEFGHI", [6, 16, 10, 90, 18, 12, 40, 12, 30]): sh.column_dimensions[col].width = w
    sh.freeze_panes = "E2"; sh.auto_filter.ref = f"A1:I{len(rows) + 1}"
    stats[nm] = len(rows)
# 사전 후보
sh = wb.create_sheet("사전후보"); sh.append(["지표", "후보 표현(|로 구분)", "근거", "표본에서 본 건수", "저자 판정(O=사전에 넣음/X=제외)", "메모"])
for c in range(1, 7): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
cands = list(csv.reader(open(HERE.parents[0] / "dictionaries" / "dictionary_candidates_from_audit_v7.csv", encoding="utf-8-sig")))[1:]
for r in cands: sh.append([NAMES.get(r[0], r[0]), r[1], r[2], int(r[3]), "", ""])
dv2 = DataValidation(type="list", formula1='"O,X"', allow_blank=True); sh.add_data_validation(dv2); dv2.add(f"E2:E{len(cands) + 1}")
for col, w in zip("ABCDEF", [8, 70, 40, 10, 22, 30]): sh.column_dimensions[col].width = w
# 집계
import json
st = json.load(open(HERE / "near_miss_stats_v7.json", encoding="utf-8"))
sh = wb.create_sheet("집계"); sh.append(["지표", "표본", "모델 Y", "저자 O", "저자 X", "미판정", "Y 중 O", "N 중 X(추가 누락)", "저자 확정 누락 수", "표본 누락 비율", "매칭", "미매칭", "재현율 추정(저자 판정 기준)"])
for c in range(1, 14): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
for i, (k, nm) in enumerate(NAMES.items(), 2):
    n = stats[nm]; rng = f"'{nm}'!F2:F{n + 1}"; rngo = f"'{nm}'!H2:H{n + 1}"
    sh.append([nm, n, f'=COUNTIF({rng},"Y")', f'=COUNTIF({rngo},"O")', f'=COUNTIF({rngo},"X")', f'={n}-D{i}-E{i}',
               f'=COUNTIFS({rng},"Y",{rngo},"O")', f'=COUNTIFS({rng},"N",{rngo},"X")', f'=G{i}+H{i}', f'=I{i}/B{i}', st[k]["matched"], st[k]["unmatched"], f'=K{i}/(K{i}+L{i}*J{i})'])
    sh.cell(row=i, column=10).number_format = "0.0%"; sh.cell(row=i, column=13).number_format = "0.000"
sh.cell(row=6, column=1, value="저자 확정 누락 수 = (모델 Y 중 O) + (모델 N 중 X). 미판정 행은 누락 아님으로 계산된다. 재현율 = 매칭 / (매칭 + 미매칭 × 표본 누락 비율).")
for col, w in zip("ABCDEFGHIJKLM", [8, 6, 8, 8, 8, 8, 8, 16, 16, 12, 8, 8, 22]): sh.column_dimensions[col].width = w
wb.save(HERE / "review_sheet_v7.xlsx"); print("wrote review_sheet_v7.xlsx", stats)
