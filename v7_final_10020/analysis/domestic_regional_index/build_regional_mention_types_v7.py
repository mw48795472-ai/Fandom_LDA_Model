# -*- coding: utf-8 -*-
"""L17 — 국내 지역 지수의 동음 지명 감사와 연고/활동 분리.
원 지수(analysis/build_notebooks_v7.py REGION_KEYWORDS, 부분 문자열, 불릿 단위)를 그대로 재현한 뒤(100/100 대조) 두 가지를 더한다.
  1) 동음·일반어 감사: 광주(경기 광주시/광주광역시), 진주(보석), 화성(행성), 경주(레이스), 전주(前奏), 구미(구미가 당기다), 진도(진도율), 남해(남해안), 청주(술), 대구(생선), 김천·구미·포항 등
     키워드마다 매치 불릿을 '지명 문맥 확인 / 일반어·타지역 / 불확실'로 나눈다. 규칙: 배제 패턴(예: 진도율, 경주마, 전주가) → 일반어; 지명 접미·문맥어(시·군·광역시·에서·공연·콘서트·출신·고향 …) → 확인; 나머지 → 불확실.
     광주는 '경기 광주'·'광주시'(광역시 아님) → 경기로 재배정.
  2) 언급 유형: 지역 언급 불릿마다 문맥어로 연고(출신·고향·태어난 …) / 활동(콘서트·공연·투어·행사·촬영 …) / 기타 를 붙이고 팬덤별로 세 열로 나눈다(합 = 원 total_region_mentions).
     '엄격' 지수(일반어·비지명만 배제, 광주 재배정 반영; 불확실은 남김)도 같이 계산해 원 지수와의 차이(지역 수·다양성·대표 지역 변경)를 적는다.
출력 (이 폴더): region_mentions_by_type_v7.csv(언급 단위), domestic_regional_index_by_type_v7.csv(팬덤 단위), homonym_audit_v7.json, REGIONAL_MENTION_TYPES_V7.md
실행: python v7_final_10020/analysis/domestic_regional_index/build_regional_mention_types_v7.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]; D = REPO / "data" / "v7_final"
src = (REPO / "v7_final_10020" / "analysis" / "build_notebooks_v7.py").read_text(encoding="utf-8")
m = re.search(r"^REGION_KEYWORDS = (?=\{)", src, re.M); i = m.end(); depth = 0
for j in range(i, len(src)):
    depth += src[j] == "{"; depth -= src[j] == "}"
    if depth == 0: break
REGION_KEYWORDS = eval(src[i:j + 1]); REGIONS = list(REGION_KEYWORDS)
orig = json.load(open(HERE / "domestic_regional_index_v7.json", encoding="utf-8"))
corpus = json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))

EXCLUDE = {"진주": [r"진주\s*(목걸이|귀걸이|반지|장식|색|빛|알|층)", r"흑진주", r"진주(같|처럼)"], "화성": [r"화성(인|탐사|에\s*가|착륙|행성)"], "경주": [r"경주(마|로|용|를|에서\s*우승|\s*대회)", r"(자동차|카트|요트|보트|말)\s*경주"],
           "전주": [r"전주(가|부터|만|를|에서부터|\s*부분|\s*멜로디|\s*연주|\s*파트)", r"곡의\s*전주", r"전주\s*(대비|보다|에\s*비해|와\s*비교)"], "구미": [r"구미(를|가)\s*(당|돋)", r"구미\s*당"], "진도": [r"진도(율|가|를|로|에\s*따|\s*체크|를\s*나가)"],
           "청주": [r"청주(를|한\s*잔|와|·|,)\s*(마|막걸리|소주)"], "대전": [r"(가요|음악|연말|시상|마지막|일요|가수)\s*대전", r"대전\s*(대비|에\s*비해)"], "대구": [r"대구(탕|찜|살|포|전|매운탕)"], "남해": [r"남해\s*바다", r"남해에서\s*잡"], "김천": [], "포항": [r"포항(제철|스틸러스)"]}
PLACE_CTX = re.compile(r"(시|군|구|광역시|도|특별시|에서|에\s*위치|공연|콘서트|페스티벌|행사|팬미팅|투어|출신|고향|방문|지역|경기장|아레나|스타디움|체육관|공연장|축제|문화|시청|시장|시민|시내|일대|권|앞|역|공항|항|지역구|연고|시내)")
AMBIG = ["대전", "광주", "진주", "화성", "경주", "전주", "구미", "진도", "남해", "청주", "대구", "김천", "포항", "김해", "거제", "울릉", "성남", "안산", "보령", "아산", "순천", "제주", "울산"]
HOME = re.compile(r"(출신|고향|태어|나고\s*자|출생|연고|토박이|자란\s*|고향\s*이|에서\s*나고|출신지|본가|본적)")
ACT = re.compile(r"(콘서트|공연|투어|페스티벌|행사|팬미팅|무대|개최|열린|열려|열리|축제|방문|촬영|홍보대사|경기장|아레나|스타디움|체육관|공연장|팬사인회|쇼케이스|시상식|위문|봉사|기부|공연장|시구|시축|행사장|참석|참여|출연|방송|촬영지|촬영을|무대에|투어를)")

def gwangju_region(t, pos):
    win = t[max(0, pos - 6):pos + 8]
    if re.search(r"(경기\s*도?\s*광주|광주시(?!광역)|광주\s*시\b)", win) and "광역" not in win: return "경기"
    return "광주"

def classify_match(kw, t, pos):
    if any(re.search(p, t) for p in EXCLUDE.get(kw, [])): return "일반어·비지명"
    after = t[pos + len(kw):pos + len(kw) + 6]; before = t[max(0, pos - 6):pos]
    if PLACE_CTX.match(after) or PLACE_CTX.search(before + kw + after): return "지명 확인"
    return "불확실"

rows, per_f, audit = [], {}, defaultdict(Counter); mism = 0
for fd in corpus:
    name = fd["fandom"]; texts = [(tag, idx, it["t"]) for tag in ("loyalty", "spillover") for idx, it in enumerate(fd[tag])]
    counts = {r: 0 for r in REGIONS}; strict = {r: 0 for r in REGIONS}; types = {"연고": 0, "활동": 0, "기타": 0}
    for tag, idx, t in texts:
        for r in REGIONS:
            hits = [(kw, mm.start()) for kw in REGION_KEYWORDS[r] for mm in re.finditer(re.escape(kw), t)]
            if not hits: continue
            counts[r] += 1
            kind = "연고" if HOME.search(t) else ("활동" if ACT.search(t) else "기타"); types[kind] += 1
            cls = [classify_match(kw, t, p) for kw, p in hits]; best = "지명 확인" if "지명 확인" in cls else ("불확실" if "불확실" in cls else "일반어·비지명")
            for kw, p in hits:
                if kw in AMBIG: audit[kw][classify_match(kw, t, p)] += 1
            target = r
            if r == "광주": target = gwangju_region(t, hits[0][1])
            if best != "일반어·비지명": strict[target] += 1   # 엄격 지수: 일반어만 배제, 불확실은 남긴다(광주 재배정 반영)
            rows.append({"fandom": name, "bullet_type": tag, "idx": idx, "region": r, "keywords": "|".join(sorted({kw for kw, _ in hits})), "match_class": best, "strict_region": target if best != "일반어·비지명" else "", "mention_type": kind, "snippet": t[max(0, hits[0][1] - 20):hits[0][1] + 25].replace("\n", " ")})
    total = sum(counts.values()); o = orig[name]
    if counts != o["region_mention_counts"] or total != o["total_region_mentions"]: mism += 1
    st = sum(strict.values()); hit_s = sum(v > 0 for v in strict.values()); prim_s = max(strict, key=strict.get) if st else None
    per_f[name] = {"fandom": name, "total_region_mentions": total, "mentions_hometown": types["연고"], "mentions_activity": types["활동"], "mentions_other": types["기타"],
                   "n_regions_hit": o["n_regions_hit"], "region_diversity": o["region_diversity"], "primary_region": o["primary_region"],
                   "strict_total": st, "strict_n_regions_hit": hit_s, "strict_region_diversity": round(hit_s / 17, 3), "strict_primary_region": prim_s, "primary_changed": int(prim_s != o["primary_region"]), "regions_hit_delta": hit_s - o["n_regions_hit"]}
assert mism == 0, mism
with open(HERE / "region_mentions_by_type_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(HERE / "domestic_regional_index_by_type_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(next(iter(per_f.values())).keys())); w.writeheader(); w.writerows(per_f.values())
cls_tot = Counter(r["match_class"] for r in rows); type_tot = Counter(r["mention_type"] for r in rows)
gj = Counter(r["strict_region"] for r in rows if r["region"] == "광주" and r["strict_region"])
n_prim = sum(v["primary_changed"] for v in per_f.values()); n_hit_delta = sum(1 for v in per_f.values() if v["regions_hit_delta"] != 0)
json.dump({"reproduction_of_original": "100/100 팬덤 region_mention_counts·total 일치", "match_class_totals": dict(cls_tot), "mention_type_totals": dict(type_tot), "homonym_audit_by_keyword": {k: dict(v) for k, v in audit.items()},
           "gwangju_reassignment": dict(gj), "strict_index_effect": {"fandoms_primary_region_changed": n_prim, "fandoms_n_regions_hit_changed": n_hit_delta, "total_mentions_original": sum(v["total_region_mentions"] for v in per_f.values()), "total_mentions_strict": sum(v["strict_total"] for v in per_f.values())},
           "rules": {"exclude_patterns": {k: v for k, v in EXCLUDE.items() if v}, "place_context": PLACE_CTX.pattern, "hometown": HOME.pattern, "activity": ACT.pattern}},
          open(HERE / "homonym_audit_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

N = len(rows)
md = ["# 국내 지역 지수 — 동음 지명 감사와 연고/활동 분리 (L17)\n",
      "원 지수는 17개 시·도 키워드의 부분 문자열 매칭이라 동음 지명·일반어를 구분하지 않고 지역 연고와 지역 활동을 합산한다. 이 문서는 원 지수를 100/100 재현한 뒤 두 가지를 덧붙인다. `build_regional_mention_types_v7.py`가 만든다.\n", "## 0. 결론\n",
      f"- 지역 언급 {N:,}건(불릿×지역) 중 지명 문맥이 확인되는 것 {cls_tot['지명 확인']:,}({cls_tot['지명 확인']/N:.1%}), 일반어·비지명으로 배제되는 것 {cls_tot.get('일반어·비지명', 0):,}({cls_tot.get('일반어·비지명', 0)/N:.1%}), 문맥이 없어 불확실한 것 {cls_tot.get('불확실', 0):,}({cls_tot.get('불확실', 0)/N:.1%}).",
      f"- 일반어·비지명을 빼고 광주를 재배정한 '엄격' 지수로 바꾸면 대표 지역이 바뀌는 팬덤 {n_prim}개, 검출 지역 수가 바뀌는 팬덤 {n_hit_delta}개(100개 중). 광주 매치 중 경기 광주로 재배정된 것 {gj.get('경기', 0)}건, 광주광역시로 남은 것 {gj.get('광주', 0)}건. 즉 동음 지명 문제의 실제 크기는 작다. 다만 문맥이 없는 '불확실' {cls_tot.get('불확실', 0):,}건({cls_tot.get('불확실', 0)/N:.1%})은 사람 검수 없이는 지명인지 확정할 수 없는 상한이다.",
      f"- 언급 유형: 연고 {type_tot['연고']:,}({type_tot['연고']/N:.1%}) / 활동 {type_tot['활동']:,}({type_tot['활동']/N:.1%}) / 기타 {type_tot['기타']:,}({type_tot['기타']/N:.1%}). 지역 언급은 대부분 활동(공연·행사·촬영)이고, 연고 언급은 소수라 두 열을 합친 원 지수는 사실상 '지역 활동 지수'다.\n",
      "## 1. 동음·일반어 키워드 감사\n", "| 키워드 | 지명 확인 | 일반어·비지명 | 불확실 |\n|---|---|---|---|"]
for kw in AMBIG:
    if audit[kw]: md.append(f"| {kw} | {audit[kw].get('지명 확인', 0)} | {audit[kw].get('일반어·비지명', 0)} | {audit[kw].get('불확실', 0)} |")
md.append("\n배제 패턴(예: 진도율·경주마·전주가·전주 대비·가요대전·구미가 당기다·화성 탐사)에 걸리면 일반어, 지명 접미·문맥어(시·군·광역시·에서·공연·콘서트·출신·고향 …)가 붙으면 확인, 둘 다 아니면 불확실이다. 불확실은 원 지수와 엄격 지수 모두에 남긴다. 사람 검수 표본을 뽑을 자리다.\n")
md.append("## 2. 연고/활동 분리 — 팬덤별 (원 총계 상위 15)\n")
md.append("| 팬덤 | 원 총계 | 연고 | 활동 | 기타 | 대표 지역 | 엄격 총계 | 엄격 대표 지역 | 지역 수 Δ |\n|---|---|---|---|---|---|---|---|---|")
for v in sorted(per_f.values(), key=lambda v: -v["total_region_mentions"])[:15]:
    md.append(f"| {v['fandom']} | {v['total_region_mentions']} | {v['mentions_hometown']} | {v['mentions_activity']} | {v['mentions_other']} | {v['primary_region']} | {v['strict_total']} | {v['strict_primary_region']} | {v['regions_hit_delta']:+d} |")
md.append("\n전체 100개 팬덤은 `domestic_regional_index_by_type_v7.csv`. 연고+활동+기타 = 원 total_region_mentions 가 100/100 성립한다.\n")
md.append("## 3. 한계\n1. 연고/활동은 같은 불릿의 문맥어로 나눈 것이라 한 문장에 둘 다 있으면 연고를 우선한다. 사람 검수는 하지 않았다.\n2. 배제·확인 규칙은 이 코퍼스에서 눈에 띈 패턴으로 만든 것이라 다른 코퍼스에서는 보강이 필요하다. 규칙은 `homonym_audit_v7.json`에 있다.\n3. 원 지수 JSON·CSV는 바꾸지 않았다. 엄격 지수를 본 지수로 올리려면 verify 항목과 README 표를 함께 옮겨야 한다.\n")
md.append("## 4. 파일\n| 파일 | 내용 |\n|---|---|\n| `region_mentions_by_type_v7.csv` | 언급 단위: 팬덤·불릿·지역·키워드·매치 판정·엄격 지역·언급 유형·문맥 |\n| `domestic_regional_index_by_type_v7.csv` | 팬덤 단위: 원 지수 + 연고/활동/기타 + 엄격 지수 |\n| `homonym_audit_v7.json` | 키워드별 감사 집계·규칙 |\n| `build_regional_mention_types_v7.py` | 이 문서를 만드는 스크립트 |\n")
(HERE / "REGIONAL_MENTION_TYPES_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("mentions", N, dict(cls_tot), dict(type_tot), "primary changed", n_prim, "hit delta", n_hit_delta, "gwangju", dict(gj))
for kw in AMBIG:
    if audit[kw]: print(" ", kw, dict(audit[kw]))
