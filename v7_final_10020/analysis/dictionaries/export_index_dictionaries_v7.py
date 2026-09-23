# -*- coding: utf-8 -*-
"""L4 — 지표 계산에 쓰인 사전(키워드·도메인·별칭 목록)을 코드와 JSON에서 뽑아 데이터 파일로 고정한다.
손으로 옮긴 항목은 없다. 저장소 어디에도 없는 사전(광고 업종 키워드 전체, 결속 유형 키워드)은 '없음'으로 표에 적는다.

출처 (전부 ast/json 으로 읽음):
  run_lda_v6.py            MARKET_KEYWORDS(시장 6), ENTITY_CATEGORIES(엔티티 6), 언어 도메인 목록 5종 + 커뮤니티/위키 도메인, MEMBER_ALIASES(멤버 별칭 10그룹)
  analysis/build_notebooks_v7.py   REGION_KEYWORDS(국내 17개 시도), NEGATION(광고 부정 가드 7)
  data/v7_final/ad_commercial_index_v7.json   ad_signal_keywords(31), industries(20)
  data/v7_rounds/merge_log_r65.json           industry_keywords_added(r65에서 추가된 업종 브랜드 — 업종 사전의 '부분')
  data/v7_final/fandom_cohesion_index_v7.json categories(5) + D 게이트 공존어(methodology 문장에서 추출)
  data/v7_final/media_exposure_v7.json        subtags(4)
  analysis/build_notebooks_v7.py   ALL_LANGS / LANG_LABEL(14개 언어)

출력: 이 폴더 index_dictionaries_v7.csv (사전, 항목, 값, 출처) + DICTIONARIES_V7.md(사전별 유무·건수·출처 표)
실행: python v7_final_10020/analysis/dictionaries/export_index_dictionaries_v7.py
"""
import ast, csv, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
D = BASE / "data" / "v7_final"


def pull(path, names):
    """모듈 수준 대입은 ast로, 노트북 생성기처럼 코드가 문자열 안에 든 파일은 줄 시작의 `NAME = {…}`/`[…]` 블록을 정규식으로 잘라 실행."""
    src = Path(path).read_text(encoding="utf-8"); ns = {"re": re}
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in names:
            exec(ast.get_source_segment(src, n), ns)
    for name in names:
        if name in ns:
            continue
        m = re.search(r"^" + name + r" = (?=[\[{])", src, re.M)
        if m:
            # 줄 시작의 `NAME = {`/`[` 에서 괄호 짝이 맞는 지점까지만 잘라 실행 (문자열·마크다운 속 유사 텍스트는 건너뜀)
            start = m.end(); depth = 0; end = None
            for i in range(start, len(src)):
                ch = src[i]
                if ch in "[{(": depth += 1
                elif ch in "]})":
                    depth -= 1
                    if depth == 0: end = i + 1; break
            if end: exec(f"{name} = {src[start:end]}", ns)
    return {k: ns[k] for k in names if k in ns}


rows = []
def add(dictionary, key, value, source, note=""):
    rows.append({"사전": dictionary, "항목": key, "값": value, "출처": source, "비고": note})

# 1. Coverage Index (run_lda_v6.py)
r = pull(BASE / "run_lda_v6.py", ["MARKET_KEYWORDS", "ENTITY_CATEGORIES", "EN_GLOBAL_DOMAINS", "JP_DOMAINS", "CN_DOMAINS", "ES_DOMAINS", "FR_DOMAINS", "COMMUNITY_SOCIAL_DOMAINS", "WIKI_DOMAINS", "MEMBER_ALIASES"])
for k, v in r["MARKET_KEYWORDS"].items():
    for kw in v: add("Coverage·시장(MARKET_KEYWORDS)", k, kw, "run_lda_v6.py")
for k, v in r["ENTITY_CATEGORIES"].items():
    for kw in v: add("Coverage·엔티티(ENTITY_CATEGORIES)", k, kw, "run_lda_v6.py")
for name in ("EN_GLOBAL_DOMAINS", "JP_DOMAINS", "CN_DOMAINS", "ES_DOMAINS", "FR_DOMAINS", "COMMUNITY_SOCIAL_DOMAINS", "WIKI_DOMAINS"):
    for dmn in sorted(r[name]): add(f"Coverage·언어/출처유형 도메인({name})", name, dmn, "run_lda_v6.py", "구 판(6개 언어). 최종 14개 언어 도메인 허용목록은 원본 소스 유실")
for grp, members in r["MEMBER_ALIASES"].items():
    for m, aliases in members.items():
        for a in aliases: add("멤버 집중도(MEMBER_ALIASES)", f"{grp}/{m}", a, "run_lda_v6.py", "파일럿 10그룹 판. 최종 45그룹 별칭은 member_mention_index_v7.json 에 그룹별로 있음")
# 2. 국내 지역·광고 부정 가드 (build_notebooks_v7.py)
b = pull(BASE / "v7_final_10020" / "analysis" / "build_notebooks_v7.py", ["REGION_KEYWORDS", "NEGATION", "ALL_LANGS", "LANG_LABEL"])
for k, v in b["REGION_KEYWORDS"].items():
    for kw in v: add("국내 지역(REGION_KEYWORDS)", k, kw, "analysis/build_notebooks_v7.py")
for kw in b["NEGATION"]: add("광고·상업성 부정 가드(NEGATION)", "협찬 부정형", kw, "analysis/build_notebooks_v7.py")
for code in b["ALL_LANGS"]: add("세계 언어(ALL_LANGS)", code, b["LANG_LABEL"].get(code, ""), "analysis/build_notebooks_v7.py")
# 3. 광고·상업성 (JSON)
ad = json.load(open(D / "ad_commercial_index_v7.json", encoding="utf-8"))
for kw in ad["ad_signal_keywords"]: add("광고·상업성 신호(AD_SIGNAL_KEYWORDS)", "광고 신호", kw, "data/v7_final/ad_commercial_index_v7.json")
for ind in ad["industries"]: add("광고·상업성 업종 목록(INDUSTRIES)", "업종", ind, "data/v7_final/ad_commercial_index_v7.json", "업종별 브랜드·키워드 사전(INDUSTRY_KEYWORDS)은 저장소에 없음")
r65 = json.load(open(BASE / "data" / "v7_rounds" / "merge_log_r65.json", encoding="utf-8")).get("industry_keywords_added", {})
for ind, kws in r65.items():
    for kw in kws: add("광고·상업성 업종 키워드(INDUSTRY_KEYWORDS, r65 추가분만)", ind, kw, "data/v7_rounds/merge_log_r65.json", "부분 — 전체 사전 아님")
# 4. 팬덤 결속 (JSON)
co = json.load(open(D / "fandom_cohesion_index_v7.json", encoding="utf-8"))
for c in co["categories"]: add("팬덤 결속 유형(COHESION categories)", "유형", c, "data/v7_final/fandom_cohesion_index_v7.json", "유형별 키워드 목록은 저장소에 없음")
m = re.search(r"'([^']+)' 중 하나가 같은 문장에 공존", co["methodology"])
for kw in (m.group(1).split("/") if m else []): add("팬덤 결속 D 게이트 공존어", "D_기부·후원", kw, "fandom_cohesion_index_v7.json methodology")
# 5. 미디어 노출 (JSON)
me = json.load(open(D / "media_exposure_v7.json", encoding="utf-8"))
for t in me["subtags"]: add("미디어·콘텐츠 노출 서브태그(subtags)", "서브태그", t, "data/v7_final/media_exposure_v7.json", "서브태그별 확장 키워드는 저장소에 없음(서브태그명 문자열 매칭)")

with open(HERE / "index_dictionaries_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["사전", "항목", "값", "출처", "비고"]); w.writeheader(); w.writerows(rows)

from collections import Counter, OrderedDict
cnt = Counter(r["사전"] for r in rows)
md = ["# 지표 사전 모음 — 코드·JSON에서 추출 (L4)\n",
      "보조지표·Coverage Index 계산에 쓰이는 키워드·도메인·별칭 사전을 한 파일(`index_dictionaries_v7.csv`)로 고정했다. 전부 `export_index_dictionaries_v7.py`가 저장소의 코드와 JSON에서 ast/json으로 읽어 쓴 것이라 손으로 옮긴 값이 없다. "
      "**원본 파이프라인에만 있었고 저장소에 남지 않은 사전은 아래 표에 '없음'으로 적었다** — 그 지표는 저장된 집계값만 재현·검증하고 태깅 자체는 다시 하지 않는다.\n",
      "| 지표 | 사전 | 저장소 유무 | 건수 | 출처 |\n|---|---|---|---|---|"]
def row(idx, name, key, src, status=None):
    n = cnt.get(key, 0); md.append(f"| {idx} | {name} | {status or ('있음' if n else '없음')} | {n or '—'} | {src} |")
row("Coverage Index", "시장 키워드 6권역", "Coverage·시장(MARKET_KEYWORDS)", "`run_lda_v6.py`")
row("Coverage Index", "엔티티 카테고리 6종", "Coverage·엔티티(ENTITY_CATEGORIES)", "`run_lda_v6.py`")
n_dom = sum(v for k, v in cnt.items() if "도메인(" in k); md.append(f"| Coverage Index / 세계 언어 | 언어·출처유형 도메인 허용목록 | 구 판만 있음 (6개 언어) | {n_dom} | `run_lda_v6.py` — 최종 14개 언어 판은 `run_lda_v6_live_reference_v7.py` 원본 유실, 라이브 언어 집계값은 `language_domain_summary_v7.json` |")
row("국내 지역 지수", "17개 시도 지명 키워드", "국내 지역(REGION_KEYWORDS)", "`analysis/build_notebooks_v7.py`")
row("광고·상업성 지수", "광고 신호 키워드 31", "광고·상업성 신호(AD_SIGNAL_KEYWORDS)", "`ad_commercial_index_v7.json`")
row("광고·상업성 지수", "부정 가드 7", "광고·상업성 부정 가드(NEGATION)", "`analysis/build_notebooks_v7.py`")
row("광고·상업성 지수", "업종 목록 20", "광고·상업성 업종 목록(INDUSTRIES)", "`ad_commercial_index_v7.json`")
row("광고·상업성 지수", "업종별 브랜드·키워드 사전(INDUSTRY_KEYWORDS)", "광고·상업성 업종 키워드(INDUSTRY_KEYWORDS, r65 추가분만)", "`merge_log_r65.json`(r65 추가분만)", status="**없음** (r65 추가분 일부만)")
row("팬덤 결속 지수", "유형 5종", "팬덤 결속 유형(COHESION categories)", "`fandom_cohesion_index_v7.json`")
row("팬덤 결속 지수", "유형별 키워드 목록", "—", "—", status="**없음**")
row("팬덤 결속 지수", "D(기부·후원) 게이트 공존어", "팬덤 결속 D 게이트 공존어", "`fandom_cohesion_index_v7.json` methodology")
row("미디어·콘텐츠 노출 지수", "서브태그 4", "미디어·콘텐츠 노출 서브태그(subtags)", "`media_exposure_v7.json`")
row("멤버 집중도(MCI)", "멤버 별칭 (파일럿 10그룹)", "멤버 집중도(MEMBER_ALIASES)", "`run_lda_v6.py` — 최종 45그룹은 `member_mention_index_v7.json` 그룹별 항목")
row("세계 언어 지수", "14개 언어 코드·라벨", "세계 언어(ALL_LANGS)", "`analysis/build_notebooks_v7.py`")
md.append("| 토크나이저 | 언어별 불용어 | 있음 | 1,503+ | `analysis/tokenizer/stopwords/` (별도 정리) + 재구성본 `run_lda_v6_live_reference_v7.py` |")
md.append(f"\n합계 {len(rows)}행. 없음으로 표시된 두 사전(광고 업종 키워드 전체, 결속 유형 키워드)은 원본 산출물 JSON에 집계값만 남아 있어 복원할 수 없다. "
          "다음 라운드부터는 지수 스크립트가 이 CSV를 읽도록 하고, 사전을 바꿀 때 CSV를 함께 커밋하는 것이 L4의 남은 절반이다.\n")
(HERE / "DICTIONARIES_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} rows;", dict(cnt))
