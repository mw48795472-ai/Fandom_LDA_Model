# -*- coding: utf-8 -*-
"""L16 저자 검수 엑셀 — O/X 대신 판단 옵션을 고르게 한다.
시트
  안내      판정 옵션 설명
  정의결정  지표 정의 자체에 대한 결정 질문 12개(예: 영문 상업 신호를 사전에 넣을지, 라디오를 미디어 노출로 볼지, 영문 지명을 지역 언급으로 볼지) — 선택지·영향·권장
  광고/미디어/지역  표본 200건씩: 문장·힌트어·모델 판독·사유 + [저자 판정] 드롭다운 5옵션 + [추가할 표현] + [메모]
  사전후보  후보 9묶음: [처리] 드롭다운(추가/수정해서 추가/제외/보류) + [수정안]
  집계      판정 옵션별 건수와 재현율 추정(수식)
판정 옵션
  A 누락·사전추가   이 지표에 잡혔어야 하고, '추가할 표현'을 사전에 넣으면 잡힌다
  B 누락·사전제외   잡혔어야 하지만 표현이 일회성이라 사전에는 넣지 않는다(누락으로만 집계)
  C 경계·정의결정   지표 정의를 넓히면 포함되는 사례(라디오·영문·군 단위 등) — 정의결정 시트의 답에 따른다
  D 아님           지표 대상이 아니다(사전이 맞게 안 잡음)
  E 보류           판단 유보
출력: review_sheet_v7.xlsx.  실행: python v7_final_10020/analysis/unmatched_audit/build_review_sheet_v7.py
집계: python v7_final_10020/analysis/build_unmatched_audit_samples_v7.py --summarize-xlsx
"""
import csv, json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
NAMES = {"ad": "광고", "media": "미디어", "region": "지역"}
OPTS = ["A 누락·사전추가", "B 누락·사전제외", "C 경계·정의결정", "D 아님", "E 보류"]
OPT_STR = '"' + ",".join(OPTS) + '"'
hdr = Font(bold=True); fill = PatternFill("solid", fgColor="E8EEF3"); yfill = PatternFill("solid", fgColor="FFF4CC"); gfill = PatternFill("solid", fgColor="EAF3E6")
wrap = Alignment(wrap_text=True, vertical="top")
wb = Workbook(); ws = wb.active; ws.title = "안내"
lines = [("보조지표 사전 매칭 누락 검수 — 저자 판정 시트 (옵션 판정판)", True), ("", False),
         ("무엇을 보는가", True),
         ("광고·미디어·지역 시트의 문장은 그 지수의 사전에 '잡히지 않은' 불릿 중 무작위 200건이다(seed 0). '모델 판독'은 Claude가 읽고 적은 Y(잡혔어야 함)/N. 노란 행이 Y다.", False),
         ("", False), ("행마다 고르는 판정 옵션 (열 H, 드롭다운)", True),
         ("A 누락·사전추가 — 이 지표에 잡혔어야 하고, 열 I '추가할 표현'에 적은 말을 사전에 넣으면 잡힌다. 예: '런닝맨', 'brand ambassador'.", False),
         ("B 누락·사전제외 — 잡혔어야 하지만 표현이 일회성·고유명이라 사전에는 넣지 않는다. 누락으로만 집계한다(재현율 추정에 반영).", False),
         ("C 경계·정의결정 — 지표 정의를 넓히면 포함되는 사례. 예: 라디오 출연을 '미디어 노출'로 볼지, 영문 지명을 '국내 지역 언급'으로 볼지. 정의결정 시트의 답에 따라 자동으로 A 또는 D로 취급한다.", False),
         ("D 아님 — 지표 대상이 아니다. 사전이 맞게 안 잡은 것.", False),
         ("E 보류 — 판단 유보. 집계에서는 누락 아님으로 센다.", False),
         ("", False), ("정의결정 시트", True),
         ("표본을 읽다 보면 개별 문장보다 '이 지표가 무엇을 재는가'를 정해야 하는 질문이 반복된다. 그 질문 12개를 모아 선택지와 영향을 적었다. 여기 답이 C 판정의 처리와 사전 후보의 채택 범위를 정한다. 권장안은 참고일 뿐이다.", False),
         ("", False), ("사전후보 시트", True),
         ("표본 판독에서 나온 후보 9묶음. '처리' 열에서 추가 / 수정해서 추가(수정안 열에 적기) / 제외 / 보류 를 고른다.", False),
         ("", False), ("집계 시트", True),
         ("판정 옵션별 건수, 표본 누락 비율, 재현율 추정을 수식으로 계산한다(A+B = 확정 누락, C는 '경계 포함 시' 열에 따로).", False),
         ("", False), ("되돌려 주는 법", True),
         ("이 파일을 같은 이름으로 채워 주면 --summarize-xlsx 로 집계하고, A로 확정된 표현과 채택된 후보를 사전 CSV에 넣어 보조지표를 재산출한다. 정의결정 시트의 답은 그 재산출 규칙이 된다.", False)]
for i, (t, b) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t); c.alignment = wrap
    if b: c.font = Font(bold=True, size=12 if i > 1 else 14)
ws.column_dimensions["A"].width = 130

# 정의결정
DECISIONS = [
 ("광고", "Q1 영문 불릿의 상업 계약 신호(brand ambassador, endorsement, brand model, spokesmodel, promotional face)를 사전에 넣는가", ["넣는다(영문 신호 추가)", "넣지 않는다(한국어 근거만 집계)", "보류"],
  "표본에서 광고 누락 7건 중 6건이 영문 불릿. 넣으면 광고 불릿 약 +150∼300건(재현율 0.81→0.9대), 영문 근거가 많은 글로벌 팬덤(BTS·BLACKPINK·TWS·aespa 등)의 광고 지수가 오른다.", "넣는다 — 지수 정의(상업 계약 신호)와 같고 언어만 다르므로"),
 ("광고", "Q2 '화보 공개·화보 촬영·매거진 커버'를 상업 신호로 보는가(현재 '화보 촬영'만)", ["브랜드와 함께한 화보만 포함", "화보 전부 포함", "화보 제외(현행 유지: '화보 촬영'만)"],
  "패션·뷰티 브랜드 화보는 사실상 광고 계약이지만 잡지 표지·컴백 화보는 홍보 활동이다. '브랜드+화보'만 넣으면 소수(표본 1건), 전부 넣으면 미디어 노출과 겹친다.", "브랜드와 함께한 화보만 포함"),
 ("광고", "Q3 '협업·콜라보·컬래버'(브랜드 협업 상품, 굿즈, 팝업스토어)를 광고·상업성으로 보는가", ["브랜드·기업 협업만 포함(음악 협업 제외)", "전부 제외(현행)", "보류"],
  "'협업'은 미매칭 근접 어휘 1위(154건)지만 대부분 음악 협업(피처링)이다. 브랜드 협업만 넣으려면 '브랜드/기업/제품 + 협업' 같은 조건부 규칙이 필요하다.", "브랜드·기업 협업만 포함 — 단, 조건부 규칙이라 오탐 검수 필요"),
 ("광고", "Q4 광고 지수 재산출 시 원본 JSON(ad_commercial_index_v7.json)을 교체하는가, 병행 파일로 두는가", ["병행 파일(v7_1)로 두고 README 표는 병기", "원본 교체(verify 항목 갱신)", "보류"],
  "원본 교체는 verify 107항목·README 6절·기술명세 수치가 함께 바뀐다. 병행은 두 판이 공존한다.", "병행 파일 — 최종 보고서 PDF 수치와의 대응을 유지"),
 ("미디어", "Q5 라디오(라디오 DJ·출연·진행)를 미디어·콘텐츠 노출로 보는가", ["포함(서브태그 '라디오' 신설)", "제외(현행: 예능/유튜브/영화/드라마만)", "보류"],
  "표본 17건 중 2건, 미매칭 근접 어휘 47건. 서브태그를 하나 늘리면 지수 정의(4종)가 5종이 된다.", "포함 — 방송 매체 노출이라는 지수 취지와 같음"),
 ("미디어", "Q6 서브태그 단어 없이 프로그램명만 나오는 예능·서바이벌(런닝맨·아는 형님·나는 가수다·쇼미더머니·히든싱어·미스터트롯 …)을 어떻게 잡는가", ["프로그램명 목록을 사전에 추가(목록 유지 필요)", "'출연/MC/심사위원/우승' + 방송사(KBS/MBC/SBS/JTBC/tvN/Mnet) 조합 규칙", "둘 다", "현행 유지(안 잡음)"],
  "표본 누락 17건 중 11건이 이 유형. 재현율 0.57의 주원인. 목록은 정확하지만 새 프로그램마다 갱신해야 하고, 조합 규칙은 갱신이 없지만 오탐(뉴스 보도 문장)이 생긴다.", "둘 다 — 목록으로 정확도, 규칙으로 갱신 부담 완화"),
 ("미디어", "Q7 영문·일문 방송 표현(documentary, variety show, singing-competition show, late show, バラエティ番組)을 넣는가", ["넣는다", "넣지 않는다", "보류"], "표본 4건. 광고 Q1과 같은 성격(언어만 다름).", "넣는다"),
 ("미디어", "Q8 OTT·웹예능·웹드라마·뮤지컬·연극·팟캐스트를 미디어 노출로 보는가", ["OTT·웹예능·웹드라마 포함, 뮤지컬·연극·팟캐스트 제외", "전부 포함", "전부 제외(현행)"],
  "OTT 드라마는 '드라마'로 이미 잡히는 경우가 많다. 뮤지컬·연극은 공연(F3 현장경제)에 가깝다.", "OTT·웹예능·웹드라마 포함, 뮤지컬·연극·팟캐스트 제외"),
 ("지역", "Q9 영문 지명(Seoul, Incheon, Daegu, Busan, Uijeongbu …)을 국내 지역 언급으로 보는가", ["넣는다(17개 시·도 + 주요 도시 영문 표기)", "넣지 않는다", "보류"], "표본 6건 중 3건. 영문 불릿의 국내 투어 기사가 잡힌다.", "넣는다"),
 ("지역", "Q10 사전 밖 군 단위(봉화·철원·해남 …)와 도 전체명(경상북도·전라남도 …)을 넣는가", ["행정구역 전체 목록(시·군·구 + 도 전체명)으로 교체", "표본에서 나온 것만 추가", "현행 유지"],
  "전체 목록은 동음 지명(광주·고성·경주·전주·진주·화성 …)이 늘어 L17의 배제 규칙을 함께 넓혀야 한다.", "표본에서 나온 것만 추가 + 도 전체명 — 동음 확대를 피함"),
 ("지역", "Q11 대학·경기장·시설명(고려대·잠실·올림픽공원·KSPO돔 …)으로 지역을 유추하는가", ["유추하지 않는다(현행)", "주요 시설 → 지역 매핑표를 둔다", "보류"], "시설 매핑은 정확하지만 표를 만들어야 하고 '서울' 편중이 더 커진다.", "유추하지 않는다"),
 ("공통", "Q12 재산출 결과를 어디까지 반영하는가", ["지수 JSON/CSV 병행 파일만", "병행 파일 + README 6절 표 병기", "원본 교체 + README·verify 갱신"], "README 6절의 광고 1,302·미디어 1,025 같은 수치와 검증 107항목이 걸려 있다.", "병행 파일 + README 6절 표 병기")]
sh = wb.create_sheet("정의결정"); sh.append(["지표", "결정 질문", "선택지", "선택 시 영향", "권장(참고)", "저자 선택", "메모"])
for c in range(1, 8): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
for i, (idx, q, opts, eff, rec) in enumerate(DECISIONS, 2):
    sh.append([idx, q, "\n".join(f"· {o}" for o in opts), eff, rec, "", ""])
    dv = DataValidation(type="list", formula1='"' + ",".join(opts) + '"', allow_blank=True); sh.add_data_validation(dv); dv.add(f"F{i}")
    for c in range(1, 8): sh.cell(row=i, column=c).alignment = wrap
    sh.cell(row=i, column=6).fill = gfill
for col, w in zip("ABCDEFG", [8, 55, 40, 55, 34, 34, 25]): sh.column_dimensions[col].width = w
sh.freeze_panes = "B2"

# 표본 시트
COL = "검수(Y=해당 지표에 잡혔어야 함, N=아님)"; stats = {}
for k, nm in NAMES.items():
    rows = list(csv.DictReader(open(HERE / f"unmatched_sample_{k}_v7.csv", encoding="utf-8-sig")))
    sh = wb.create_sheet(nm); head = ["번호", "팬덤", "유형", "문장", "힌트어(사전 밖 유사 표현)", "모델 판독(Y/N)", "판독 사유", "저자 판정(A∼E)", "추가할 표현(A일 때)", "메모"]
    sh.append(head)
    for c in range(1, len(head) + 1): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
    for i, r in enumerate(rows, 1):
        sh.append([i, r["fandom"], r["bullet_type"], r["text"], r["hint_terms_found"], r[COL], r["사유·놓친 표현"], "", "", ""])
        if r[COL] == "Y":
            for c in range(1, len(head) + 1): sh.cell(row=i + 1, column=c).fill = yfill
        sh.cell(row=i + 1, column=4).alignment = wrap; sh.cell(row=i + 1, column=8).fill = gfill if r[COL] != "Y" else yfill
    dv = DataValidation(type="list", formula1=OPT_STR, allow_blank=True); sh.add_data_validation(dv); dv.add(f"H2:H{len(rows) + 1}")
    for col, w in zip("ABCDEFGHIJ", [6, 16, 10, 88, 18, 12, 38, 20, 24, 28]): sh.column_dimensions[col].width = w
    sh.freeze_panes = "E2"; sh.auto_filter.ref = f"A1:J{len(rows) + 1}"; stats[nm] = len(rows)

# 사전후보
sh = wb.create_sheet("사전후보"); sh.append(["지표", "후보 표현(|로 구분)", "근거", "표본에서 본 건수", "관련 정의결정", "처리", "수정안(수정해서 추가일 때)", "메모"])
for c in range(1, 9): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
cands = list(csv.reader(open(HERE.parents[0] / "dictionaries" / "dictionary_candidates_from_audit_v7.csv", encoding="utf-8-sig")))[1:]
QMAP = {"brand ambassador": "Q1", "화보": "Q2", "런닝맨": "Q6", "라디오": "Q5", "서바이벌": "Q6", "documentary": "Q7", "방송 출연": "Q6", "Seoul": "Q9", "봉화": "Q10"}
for r in cands:
    q = next((v for kk, v in QMAP.items() if kk in r[1]), "")
    sh.append([NAMES.get(r[0], r[0]), r[1], r[2], int(r[3]), q, "", "", ""])
dv2 = DataValidation(type="list", formula1='"추가,수정해서 추가,제외,보류"', allow_blank=True); sh.add_data_validation(dv2); dv2.add(f"F2:F{len(cands) + 1}")
for i in range(2, len(cands) + 2):
    for c in (2, 3): sh.cell(row=i, column=c).alignment = wrap
    sh.cell(row=i, column=6).fill = gfill
for col, w in zip("ABCDEFGH", [8, 60, 40, 10, 12, 16, 30, 25]): sh.column_dimensions[col].width = w

# 집계
st = json.load(open(HERE / "near_miss_stats_v7.json", encoding="utf-8"))
sh = wb.create_sheet("집계"); sh.append(["지표", "표본", "모델 Y", "A 누락·사전추가", "B 누락·사전제외", "C 경계", "D 아님", "E 보류", "미판정", "확정 누락(A+B)", "표본 누락 비율", "경계 포함 시 비율", "매칭", "미매칭", "재현율 추정", "경계 포함 시 재현율"])
for c in range(1, 17): sh.cell(row=1, column=c).font = hdr; sh.cell(row=1, column=c).fill = fill
for i, (k, nm) in enumerate(NAMES.items(), 2):
    n = stats[nm]; rf = f"'{nm}'!F2:F{n + 1}"; rh = f"'{nm}'!H2:H{n + 1}"
    sh.append([nm, n, f'=COUNTIF({rf},"Y")'] + [f'=COUNTIF({rh},"{o}")' for o in OPTS] + [f'={n}-SUM(D{i}:H{i})', f'=D{i}+E{i}', f'=J{i}/B{i}', f'=(J{i}+F{i})/B{i}', st[k]["matched"], st[k]["unmatched"], f'=M{i}/(M{i}+N{i}*K{i})', f'=M{i}/(M{i}+N{i}*L{i})'])
    for c in (11, 12): sh.cell(row=i, column=c).number_format = "0.0%"
    for c in (15, 16): sh.cell(row=i, column=c).number_format = "0.000"
sh.cell(row=6, column=1, value="확정 누락 = A + B. C(경계)는 정의결정에서 '포함'을 고른 경우에만 누락으로 세며, 그 상한이 '경계 포함 시' 열이다. E·미판정은 누락 아님으로 계산된다. 재현율 = 매칭 / (매칭 + 미매칭 × 표본 누락 비율).")
for col, w in zip("ABCDEFGHIJKLMNOP", [8, 6, 8, 14, 14, 8, 8, 8, 8, 14, 12, 14, 8, 8, 12, 16]): sh.column_dimensions[col].width = w
wb.save(HERE / "review_sheet_v7.xlsx"); print("wrote review_sheet_v7.xlsx", stats, "decisions", len(DECISIONS))
