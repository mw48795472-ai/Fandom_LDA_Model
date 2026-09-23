# -*- coding: utf-8 -*-
"""L16 — 사전 기반 매칭의 누락(재현율) 검수 도구.
보조지표 3종(광고·상업성, 미디어·콘텐츠 노출, 국내 지역)의 매칭 규칙을 그대로 재현해 '미매칭' 불릿을 뽑고,
  (1) 사전에 없는 유사 표현(근접 누락 어휘, 예: 다큐멘터리·라디오·OTT / 캠페인·화보·콜라보 / 사전 밖 시·군 이름)이 든 미매칭 불릿 수 = 누락 재현율의 하한 근거,
  (2) 사람 검수용 무작위 표본 200건 CSV(검수·사유 열 공란, seed 0),
  (3) --summarize: 검수 열이 채워진 CSV에서 표본 재현율 추정치(누락 비율)를 계산
을 만든다. 결속 지수는 유형별 키워드 사전이 저장소에 없어(L4) 재현·검수 대상에서 뺀다.
출력 (analysis/unmatched_audit/): unmatched_sample_{ad,media,region}_v7.csv, near_miss_stats_v7.json, UNMATCHED_AUDIT_V7.md
실행: python v7_final_10020/analysis/build_unmatched_audit_samples_v7.py            (표본·통계 생성)
      python v7_final_10020/analysis/build_unmatched_audit_samples_v7.py --summarize (CSV 검수 열 집계)
      python v7_final_10020/analysis/build_unmatched_audit_samples_v7.py --summarize-xlsx (저자가 O/X를 적은 unmatched_audit/review_sheet_v7.xlsx 집계)
"""
import csv, json, random, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]; D = REPO / "data" / "v7_final"; OUT = HERE / "unmatched_audit"; OUT.mkdir(exist_ok=True)
corpus = json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))
ad = json.load(open(D / "ad_commercial_index_v7.json", encoding="utf-8")); media = json.load(open(D / "media_exposure_v7.json", encoding="utf-8"))
src = (HERE / "build_notebooks_v7.py").read_text(encoding="utf-8")
def pull_dict(name):
    m = re.search(r"^%s = (?=[\[{])" % name, src, re.M); i = m.end(); depth = 0
    for j in range(i, len(src)):
        depth += src[j] in "[{"; depth -= src[j] in "]}"
        if depth == 0: return eval(src[i:j + 1])
REGION_KEYWORDS = pull_dict("REGION_KEYWORDS"); NEGATION = pull_dict("NEGATION"); SIGNALS = ad["ad_signal_keywords"]; SUBTAGS = media["subtags"]
REGION_ALL = [k for v in REGION_KEYWORDS.values() for k in v]

def is_ad(t):
    hits = [k for k in SIGNALS if k in t]
    return bool(hits) and not (set(hits) == {"협찬"} and any(n in t for n in NEGATION))
MATCH = {"ad": is_ad, "media": lambda t: any(s in t for s in SUBTAGS), "region": lambda t: any(k in t for k in REGION_ALL)}
HINTS = {"ad": ["캠페인", "화보", "콜라보", "컬래버", "협업", "스폰서", "후원사", "엠버서더", "브랜드 모델", "전속 모델", "CF", "론칭", "출시", "팝업스토어", "굿즈", "한정판", "단독 판매", "제품", "홍보", "쇼핑"],
         "media": ["다큐", "라디오", "팟캐스트", "OTT", "넷플릭스", "디즈니", "티빙", "웨이브", "쿠팡플레이", "웹드라마", "웹예능", "시트콤", "토크쇼", "뮤지컬", "연극", "틱톡", "숏폼", "브이라이브", "위버스", "애니메이션", "예능감", "방송 출연", "TV 출연", "고정 출연"],
         "region": ["고양", "일산", "용인", "파주", "평택", "여수", "광양", "군산", "익산", "안동", "통영", "사천", "밀양", "양산", "제천", "충주", "서산", "태안", "동해", "삼척", "평창", "정선", "인천공항", "김포", "수도권", "지방", "전국 투어", "지역 축제", "경기 광주", "고성"]}
HINTS = {k: [h for h in v if not any(h in kw or kw in h for kw in (SIGNALS if k == "ad" else SUBTAGS if k == "media" else REGION_ALL))] for k, v in HINTS.items()}
ORIG_TOTAL = {"ad": ad["total_ad_bullets"], "media": media["total_media_bullets"], "region": None}

bullets = [(fd["fandom"], tag, i, it["t"]) for fd in corpus for tag in ("loyalty", "spillover") for i, it in enumerate(fd[tag])]
if "--summarize-xlsx" in sys.argv:
    # 저자가 판정 옵션(A∼E)을 적은 unmatched_audit/review_sheet_v7.xlsx 집계: 확정 누락 = A+B, 경계(C)는 별도, 정의결정·사전후보 시트의 선택도 같이 출력
    from openpyxl import load_workbook
    wb = load_workbook(OUT / "review_sheet_v7.xlsx", data_only=True); res = {}
    for k, nm in (("ad", "광고"), ("media", "미디어"), ("region", "지역")):
        rows = list(wb[nm].iter_rows(min_row=2, values_only=True)); n = len(rows)
        cat = [(r[7] or "").strip()[:1] for r in rows]; cnt = {c: cat.count(c) for c in "ABCDE"}
        miss = (cnt["A"] + cnt["B"]) / n; miss_c = (cnt["A"] + cnt["B"] + cnt["C"]) / n
        matched = sum(1 for b_ in bullets if MATCH[k](b_[3])); un = len(bullets) - matched
        res[k] = {"judged": sum(cnt.values()), "counts": cnt, "terms_to_add": sorted({(r[8] or "").strip() for r in rows if (r[7] or "").startswith("A") and (r[8] or "").strip()}),
                  "miss_share": round(miss, 4), "miss_share_incl_borderline": round(miss_c, 4), "recall_estimate": round(matched / (matched + un * miss), 3), "recall_incl_borderline": round(matched / (matched + un * miss_c), 3)}
    res["definition_decisions"] = [{"q": r[1], "choice": r[5], "memo": r[6]} for r in wb["정의결정"].iter_rows(min_row=2, values_only=True) if r[1]]
    res["dictionary_candidates"] = [{"index": r[0], "terms": r[1], "action": r[5], "revised": r[6]} for r in wb["사전후보"].iter_rows(min_row=2, values_only=True) if r[1]]
    print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit()
if "--summarize" in sys.argv:
    res = {}
    for k in MATCH:
        rows = list(csv.DictReader(open(OUT / f"unmatched_sample_{k}_v7.csv", encoding="utf-8-sig"))); done = [r for r in rows if r["검수(Y=해당 지표에 잡혔어야 함, N=아님)"].strip()]
        y = sum(1 for r in done if r["검수(Y=해당 지표에 잡혔어야 함, N=아님)"].strip().upper() == "Y")
        res[k] = {"reviewed": len(done), "should_have_matched": y, "miss_share_in_unmatched": round(y / len(done), 4) if done else None}
    print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit()

stats = {}; random.seed(0)
for k, fn in MATCH.items():
    matched = [b for b in bullets if fn(b[3])]; unmatched = [b for b in bullets if not fn(b[3])]
    near = [(b, [h for h in HINTS[k] if h in b[3]]) for b in unmatched]; near = [(b, hs) for b, hs in near if hs]
    hint_cnt = Counter(h for _, hs in near for h in hs)
    stats[k] = {"matched": len(matched), "matched_original_json": ORIG_TOTAL[k], "unmatched": len(unmatched), "near_miss_unmatched_with_hint": len(near), "near_miss_share_of_unmatched": round(len(near) / len(unmatched), 4),
                "recall_upper_bound_if_all_near_miss_are_true": round(len(matched) / (len(matched) + len(near)), 4), "hint_terms": dict(hint_cnt.most_common()), "hint_lexicon": HINTS[k]}
    sample = random.sample(unmatched, 200)
    with open(OUT / f"unmatched_sample_{k}_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["index", "fandom", "bullet_type", "idx", "text", "hint_terms_found", "검수(Y=해당 지표에 잡혔어야 함, N=아님)", "사유·놓친 표현"])
        for b in sample: w.writerow([k, b[0], b[1], b[2], b[3], "|".join(h for h in HINTS[k] if h in b[3]), "", ""])
json.dump(stats, open(OUT / "near_miss_stats_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
NAMES = {"ad": "광고·상업성 (31개 신호 + 부정 가드)", "media": "미디어·콘텐츠 노출 (예능/유튜브/영화/드라마)", "region": "국내 지역 (17개 시·도 48개 키워드)"}
md = ["# 사전 기반 매칭 누락 검수 (L16) — 재현율 추정을 위한 도구와 근접 누락 통계\n",
      "보조지표는 사전 문자열 매칭이라 사전 밖 표현을 놓친다. '언급 0건'은 검출 안 됨이지 활동 없음이 아니다. 이 폴더는 세 지표의 매칭을 그대로 재현해 미매칭 불릿을 뽑고, 사전에 없는 유사 표현(근접 누락 어휘)이 든 미매칭 불릿을 세어 누락의 크기를 가늠하며, 사람 검수용 표본 200건씩을 둔다. `build_unmatched_audit_samples_v7.py`가 만든다.\n",
      "## 0. 근접 누락 통계\n", "| 지표 | 매칭(재현 / 원본 JSON) | 미매칭 | 근접 누락 어휘 포함 미매칭 | 미매칭 중 비율 | 근접 누락이 전부 참일 때 재현율 상한 |\n|---|---|---|---|---|---|"]
for k, s in stats.items(): md.append(f"| {NAMES[k]} | {s['matched']:,} / {s['matched_original_json'] if s['matched_original_json'] is not None else '(불릿 단위 총계 없음)'} | {s['unmatched']:,} | {s['near_miss_unmatched_with_hint']:,} | {s['near_miss_share_of_unmatched']:.1%} | {s['recall_upper_bound_if_all_near_miss_are_true']:.3f} |")
md.append(f"\n광고 지수 재현 매칭 {stats['ad']['matched']:,}건은 원본 JSON {stats['ad']['matched_original_json']:,}건과 {stats['ad']['matched'] - stats['ad']['matched_original_json']:+d}건 차이가 있다(광고 지수 문서에 적힌 4개 팬덤 재매칭 차이). 국내 지역은 원본이 지역별 언급(불릿×지역 1,226)이라 불릿 단위 총계가 없다.")
md.append("\n'근접 누락 어휘'는 사전에 없지만 그 지표가 잡았어야 할 법한 표현 목록(아래)이다. 그 표현이 있다고 반드시 누락은 아니므로(예: '방송'은 예능이 아닐 수 있다) 사람 검수 전까지는 상한·하한의 재료일 뿐이다.\n")
for k, s in stats.items():
    md.append(f"### {NAMES[k]} — 근접 누락 어휘별 미매칭 불릿 수\n"); md.append("| 어휘 | 불릿 수 |\n|---|---|")
    for h, c in list(s["hint_terms"].items())[:15]: md.append(f"| {h} | {c} |")
    md.append("")
md.append("## 1. 사람 검수 절차\n1. `unmatched_sample_{ad,media,region}_v7.csv`(각 200건, seed 0 무작위)의 `검수` 열에 Y(그 지표에 잡혔어야 함) / N 을 적고, Y면 `사유·놓친 표현`에 표현을 적는다.\n2. `python build_unmatched_audit_samples_v7.py --summarize` 가 표본별 누락 비율을 낸다. 누락 재현율 추정 = 매칭 / (매칭 + 미매칭 × 누락 비율).\n3. `사유·놓친 표현` 열의 표현을 모아 사전에 넣고(`analysis/dictionaries/index_dictionaries_v7.csv`, L4) 지수를 다시 산출한다.\n")
md.append("## 2. 한계\n1. 결속 지수는 유형별 키워드 사전이 저장소에 없어 미매칭을 정의할 수 없다. 광고 지수의 업종 태깅(2단계)도 같은 이유로 1단계(광고 판정)만 다룬다.\n2. 근접 누락 어휘는 이 코퍼스를 보고 고른 목록이라 완전하지 않다. 검수 결과가 나오면 갱신한다.\n3. 검수는 아직 하지 않았다(표본 CSV의 검수 열은 공란). 문서의 재현율은 '상한'뿐이다.\n")
md.append("## 3. 파일\n| 파일 | 내용 |\n|---|---|\n| `unmatched_sample_ad_v7.csv` 등 3개 | 지표별 미매칭 무작위 200건 + 검수 열 |\n| `near_miss_stats_v7.json` | 매칭·미매칭·근접 누락 통계와 어휘 목록 |\n| `../build_unmatched_audit_samples_v7.py` | 생성·집계 스크립트 |\n")
(OUT / "UNMATCHED_AUDIT_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
for k, s in stats.items(): print(k, {kk: v for kk, v in s.items() if kk not in ("hint_terms", "hint_lexicon")}, list(s["hint_terms"].items())[:6])
