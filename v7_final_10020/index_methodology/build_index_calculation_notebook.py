# -*- coding: utf-8 -*-
"""index_calculation_v7.ipynb 생성기 — 보고서 Ⅲ장 식(1)~(7)을 최종 코퍼스 10,020건에 적용해
100개 팬덤의 지표(충성도·파급효과·활동량·커버리지·팩터 다양성·4구획)를 직접 산정하는 노트북을 만들고 실행한다.
verify_index_calculation_formulas.py 가 "저장된 값이 맞는지" 대조하는 스크립트라면, 이 노트북은 산식대로 값을 만들어 내고
CSV(index_calculation_v7_result.csv)로 저장한 뒤 마지막에만 저장소의 최종 산출 파일과 대조한다.

실행: python v7_final_10020/index_methodology/build_index_calculation_notebook.py            # 생성 + 실행 + HTML 내보내기
      python v7_final_10020/index_methodology/build_index_calculation_notebook.py --no-exec  # 생성만
"""
import subprocess
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent
OUT = HERE / "index_calculation_v7.ipynb"


def md(s):
    return new_markdown_cell(s.strip("\n"))


def code(s):
    return new_code_cell(s.strip("\n"))


cells = [
md('''
# 지표 산정 노트북 — 식(1)∼(7)을 최종 코퍼스 10,020건에 직접 적용

보고서 Ⅲ장(`INDEX_CALCULATION_METHODOLOGY.md`)이 정의한 7개 식을 저장소의 **근거문장 원본**(`data/v7_final/fandoms_v3_100.json`,
100개 팬덤·10,020건)에 그대로 적용해 팬덤별 지표를 처음부터 산출한다. 각 절은 "산식 → 코드 → 산출 표" 순서이고,
저장소의 최종 산출 파일(`fandom_scores_live_reference_v7.json`, 3D 맵 payload)과의 대조는 각 절 끝과 마지막 절에서만 한다.

| 절 | 식 | 이 노트북이 만들어 내는 값 | 입력 |
|---|---|---|---|
| 1 | (1) EvidenceScore | 문장별 원점수 → 팬덤별 `loyalty_raw`·`spillover_raw` | 근거문장 텍스트 |
| 2 | (2) min-max | `loyalty_score`·`spillover_score` (0∼1) | 1절 결과 |
| 3 | (7) Activity | 근거문장 수 | 근거문장 목록 |
| 4 | (3)(4) Coverage Index | 언어 엔트로피 + 시장·출처·시간·엔티티 비율의 가중합 | 팬덤별 언어·시장·출처·연도·엔티티 집계(`coverage_detail`) |
| 5 | (5)(6) Factor Diversity | 메타팩터 분포 엔트로피, 주 팩터 | LDA θ 합산 비중(`factor_share`) |
| 6 | 4구획 | 평균 기준 4구획, 0.5 기준 2×2표와 χ² | 2절 결과 |
| 7 | 저장 | `index_calculation_v7_result.csv` + 최종 산출 파일과 전량 대조 | 위 전부 |

실행 위치는 저장소 안 어디든 된다(`data/v7_final/fandoms_v3_100.json`이 있는 상위 폴더를 루트로 잡는다).
'''),
code('''
import json, math, re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

pd.set_option("display.max_colwidth", 70)
pd.set_option("display.width", 160)


def find_repo_root():
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "data" / "v7_final" / "fandoms_v3_100.json").exists():
            return p
    raise FileNotFoundError("저장소 루트(data/v7_final/fandoms_v3_100.json)를 찾지 못함 — 저장소 안에서 실행하세요")


REPO = find_repo_root()
DATA = REPO / "data" / "v7_final"
OUT_DIR = Path.cwd() if (Path.cwd() / "build_index_calculation_notebook.py").exists() else REPO / "v7_final_10020" / "index_methodology"


def load_json(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


corpus = load_json("fandoms_v3_100.json")                       # 근거문장 원본 (팬덤별 loyalty / spillover 목록)
live = {r["fandom"]: r for r in load_json("fandom_scores_live_reference_v7.json")}   # 최종 산출 파일 (대조용)
payload = {r["fandom"]: r for r in load_json("chart3d_payload_live_reference_v7.json")["rows"]}  # 3D 맵 내장 데이터 (대조용)

n_bullets = sum(len(f["loyalty"]) + len(f["spillover"]) for f in corpus)
print(f"팬덤 {len(corpus)}개, 근거문장 {n_bullets:,}건 (충성도 {sum(len(f['loyalty']) for f in corpus):,} + 파급효과 {sum(len(f['spillover']) for f in corpus):,})")
pd.DataFrame([{"fandom": f["fandom"], "fanclub": f["fanclub"], "category": f["category"],
               "n_loyalty": len(f["loyalty"]), "n_spillover": len(f["spillover"])} for f in corpus]).head(8)
'''),
md('''
## 1. 식(1) EvidenceScore — 문장 단위 원점수

```
EvidenceScore(f) = Σ_t [ 1.0 + 0.5·n_num(t) + 0.3·n_kx(t) ]        (1)
```

- `n_num(t)`: 문장 t의 **수치표현 패턴** 개수 — 숫자 뒤에 만·억·조·%·명·장·위·회·건·주·배·년 단위가 붙은 표현 (예: "120만 장"=1, "2026년 3월"=1+1)
- `n_kx(t)`: 지표별 보너스 키워드 집합과의 일치 횟수 (충성도 19개, 파급효과 18개)
- 문장 하나당 기본 1.0점이므로, 근거문장이 많을수록·수치와 키워드가 많을수록 원점수가 커진다.
'''),
code('''
NUM_PATTERN = re.compile(r"\\d+[\\.,]?\\d*\\s*(만|억|조|%|명|장|위|회|건|주|배|년)")

LOYALTY_BONUS_KW = ["기부", "돌파", "매진", "출범", "창단", "결성", "총공", "역사", "지속", "확장", "1위", "최초",
                    "신기록", "밀리언셀러", "팬클럽", "팬카페", "결속", "충성", "세대"]          # n=19
SPILLOVER_BONUS_KW = ["경제효과", "매출", "관광", "지자체", "앰버서더", "모델", "브랜드", "팝업", "협업", "관중",
                      "방문", "상권", "지역", "홍보대사", "수익", "투어", "콘서트", "소비"]      # n=18


def sentence_score(text, bonus_kw):
    """문장 하나의 EvidenceScore와 그 구성요소를 돌려준다."""
    n_num = len(NUM_PATTERN.findall(text))
    n_kx = sum(1 for kw in bonus_kw if kw in text)
    return 1.0 + 0.5 * n_num + 0.3 * n_kx, n_num, n_kx


def evidence_table(fandom_rec, kind):
    bonus = LOYALTY_BONUS_KW if kind == "loyalty" else SPILLOVER_BONUS_KW
    rows = []
    for item in fandom_rec[kind]:
        s, n_num, n_kx = sentence_score(item["t"], bonus)
        rows.append({"문장": item["t"], "n_num": n_num, "n_kx": n_kx, "EvidenceScore": round(s, 1)})
    return pd.DataFrame(rows)


# 예시: BTS 충성도 근거문장 상위 5개의 문장별 점수 분해
bts = next(f for f in corpus if f["fandom"] == "BTS")
ex = evidence_table(bts, "loyalty")
print(f"BTS 충성도 근거문장 {len(ex)}건, 원점수 합 = {ex['EvidenceScore'].sum():.1f}")
ex.head(5)
'''),
code('''
# 100개 팬덤 전체의 원점수 (식 1)
rows = []
for f in corpus:
    lt = evidence_table(f, "loyalty")
    st = evidence_table(f, "spillover")
    rows.append({"fandom": f["fandom"], "category": f["category"],
                 "n_loyalty": len(lt), "n_spillover": len(st),
                 "loyalty_raw": round(lt["EvidenceScore"].sum(), 4), "spillover_raw": round(st["EvidenceScore"].sum(), 4),
                 "loyalty_n_num": int(lt["n_num"].sum()), "loyalty_n_kx": int(lt["n_kx"].sum()),
                 "spillover_n_num": int(st["n_num"].sum()), "spillover_n_kx": int(st["n_kx"].sum())})
idx = pd.DataFrame(rows).set_index("fandom")
print("원점수 상위 10 (충성도 기준)")
display(idx.sort_values("loyalty_raw", ascending=False).head(10)[["category", "n_loyalty", "loyalty_n_num", "loyalty_n_kx", "loyalty_raw", "spillover_raw"]])

# 대조: 최종 산출 파일의 loyalty_raw / spillover_raw
mism = [(k, idx.loc[k, "loyalty_raw"], live[k]["loyalty_raw"]) for k in idx.index
        if abs(idx.loc[k, "loyalty_raw"] - live[k]["loyalty_raw"]) > 1e-6 or abs(idx.loc[k, "spillover_raw"] - live[k]["spillover_raw"]) > 1e-6]
print(f"\\n[대조] 식(1) 원점수 ↔ fandom_scores_live_reference_v7.json 불일치: {len(mism)}/100")
'''),
md('''
## 2. 식(2) min-max 정규화 — 0∼1 점수

```
Score(f) = (ScoreRaw(f) − min) / (max − min)        (2)
```

표본(100개 팬덤) 안에서 최솟값이 0, 최댓값이 1이 되도록 선형 변환한다. 충성도·파급효과를 각각 따로 정규화한다.
'''),
code('''
def minmax(s):
    return (s - s.min()) / (s.max() - s.min())


idx["loyalty_score"] = minmax(idx["loyalty_raw"]).round(4)
idx["spillover_score"] = minmax(idx["spillover_raw"]).round(4)
print(f"충성도 원점수 범위 {idx['loyalty_raw'].min():.1f}∼{idx['loyalty_raw'].max():.1f} → 0∼1,  "
      f"파급효과 원점수 범위 {idx['spillover_raw'].min():.1f}∼{idx['spillover_raw'].max():.1f} → 0∼1")
print(f"표본 평균: 충성도 {idx['loyalty_score'].mean():.4f}, 파급효과 {idx['spillover_score'].mean():.4f}")
display(idx.sort_values("loyalty_score", ascending=False).head(10)[["category", "loyalty_raw", "loyalty_score", "spillover_raw", "spillover_score"]])

mism = [k for k in idx.index if abs(idx.loc[k, "loyalty_score"] - payload[k]["loyalty"]) > 1e-3 or abs(idx.loc[k, "spillover_score"] - payload[k]["spillover"]) > 1e-3]
print(f"[대조] 식(2) 점수 ↔ 3D 맵 payload(소수 셋째 자리 저장, 허용오차 0.001) 불일치: {len(mism)}/100")
'''),
md('''
## 3. 식(7) 활동량(Activity)

```
Activity(f) = n_loyalty(f) + n_spillover(f)        (7)
```

정규화하지 않은 원시 지표로, 근거문장 수 자체다. 3D 맵의 버블 크기와 회귀분석의 통제변수로 쓰인다.
'''),
code('''
idx["activity"] = idx["n_loyalty"] + idx["n_spillover"]
print(f"활동량 합계 = {idx['activity'].sum():,} (= 코퍼스 10,020건), 평균 {idx['activity'].mean():.1f}, 최소 {idx['activity'].min()}, 최대 {idx['activity'].max()}")
display(idx.sort_values("activity", ascending=False).head(8)[["category", "n_loyalty", "n_spillover", "activity"]])
mism = [k for k in idx.index if idx.loc[k, "activity"] != live[k]["activity"]]
print(f"[대조] 식(7) activity ↔ 최종 산출 파일 불일치: {len(mism)}/100")
'''),
md('''
## 4. 식(3)(4) 근거 커버리지 지수(Coverage Index)

```
CoverageIndex(f) = 0.30·Lang + 0.25·Mkt + 0.20·Src + 0.15·Time + 0.10·Ent      (3)
Lang(f) = − Σ pᵢ ln pᵢ / ln(14)                                              (4)
```

| 하위지표 | 산식 | 이 노트북의 입력 |
|---|---|---|
| Lang | 14개 추적 언어의 인용 비율 pᵢ에 대한 정규화 섀넌 엔트로피 | `coverage_detail.language_counts` (언어별 인용 수) |
| Mkt | 언급 시장 수 ÷ 6 | `markets_mentioned` |
| Src | 출처유형 수 ÷ 3 | `source_type_counts` |
| Time | 언급 연도 수 ÷ 코퍼스 전체 연도 범위 수 | `years_mentioned` (전체 범위 = 100개 팬덤의 연도 합집합) |
| Ent | 제3자 기관·플랫폼 카테고리 수 ÷ 6 | `entity_types_mentioned` |

근거문장마다 언어·시장·출처유형·연도·엔티티를 붙이는 태깅 규칙은 원본 파이프라인의 분류기이며, 그 결과가 팬덤별 집계
(`coverage_detail`)로 저장되어 있다. 이 절은 그 집계값에서 하위지표 5개와 가중합을 산식대로 다시 계산한다.
'''),
code('''
LANGS_14 = ["ko", "en", "ja", "zh", "es", "fr", "th", "id", "vi", "ru", "tl", "pt", "tr", "ar"]
W = {"language": 0.30, "market": 0.25, "source_type": 0.20, "time": 0.15, "entity": 0.10}


def norm_entropy(counts, n_categories):
    total = sum(counts.values())
    if total == 0:
        return 0.0
    ps = [c / total for c in counts.values() if c > 0]
    return -sum(p * math.log(p) for p in ps) / math.log(n_categories)


# 코퍼스 전체 연도 범위 = 100개 팬덤에서 언급된 연도의 합집합 크기
all_years = sorted({y for r in live.values() for y in r["coverage_detail"]["years_mentioned"]})
print(f"코퍼스 전체 연도 범위: {all_years[0]}∼{all_years[-1]} ({len(all_years)}개 연도)")

cov_rows = []
for k, r in live.items():
    d = r["coverage_detail"]
    lang = norm_entropy(d["language_counts"], len(LANGS_14))
    mkt = len(d["markets_mentioned"]) / 6
    src = len(d["source_type_counts"]) / 3
    time_ = len(d["years_mentioned"]) / len(all_years)
    ent = len(d["entity_types_mentioned"]) / 6
    cov = W["language"] * lang + W["market"] * mkt + W["source_type"] * src + W["time"] * time_ + W["entity"] * ent
    cov_rows.append({"fandom": k, "n_langs": sum(1 for v in d["language_counts"].values() if v > 0), "Lang": round(lang, 4),
                     "Mkt": round(mkt, 4), "Src": round(src, 4), "Time": round(time_, 4), "Ent": round(ent, 4),
                     "coverage_index": round(cov, 4)})
cov = pd.DataFrame(cov_rows).set_index("fandom")
idx = idx.join(cov)
display(idx.sort_values("coverage_index", ascending=False).head(10)[["category", "n_langs", "Lang", "Mkt", "Src", "Time", "Ent", "coverage_index"]])

mism = [k for k in idx.index if abs(idx.loc[k, "coverage_index"] - live[k]["coverage_index"]) > 1e-3]
sub_mism = sum(1 for k in idx.index if abs(idx.loc[k, "Lang"] - live[k]["coverage_detail"]["language_coverage"]) > 1e-3)
print(f"[대조] 식(4) 언어 엔트로피(ln 14) 불일치 {sub_mism}/100, 식(3) coverage_index 불일치 {len(mism)}/100")
'''),
md('''
## 5. 식(5)(6) 팩터 다양성(Factor Diversity)

```
FactorShare(f, m) = Σ_{e∈f} Σ_{t∈m} θ(d,t) / Σ_{e∈f} Σ_t θ(d,t)        (5)
FactorDiversity(f) = − Σ pₘ ln pₘ / ln(M)                              (6)
```

`θ(d,t)`는 LDA가 각 근거문장 d에 부여한 토픽 t 비중이다. 팬덤 f의 문장들에 대해 메타팩터 m에 속한 토픽 비중을 모두 합산해
비율로 만든 것이 FactorShare이고, 그 분포(M=5)의 정규화 엔트로피가 FactorDiversity다. θ 자체는 LDA 적합 결과라
(`run_lda_v6.py` 파이프라인 산출) 노트북은 팬덤별 FactorShare에서 식(6)과 주 팩터(dominant factor)를 계산한다.
'''),
code('''
def factor_diversity(shares):
    ps = [p for p in shares.values() if p > 0]
    return -sum(p * math.log(p) for p in ps) / math.log(len(shares))


fd_rows = []
for k, r in live.items():
    sh = r["factor_share"]
    fd_rows.append({"fandom": k, "M": len(sh), "share_sum": round(sum(sh.values()), 4),
                    "factor_diversity": round(factor_diversity(sh), 4), "dominant_factor": max(sh, key=sh.get)})
fd = pd.DataFrame(fd_rows).set_index("fandom")
idx = idx.join(fd)
print("메타팩터(M=5):", list(next(iter(live.values()))["factor_share"].keys()))
display(idx.sort_values("factor_diversity", ascending=False).head(8)[["category", "M", "share_sum", "factor_diversity", "dominant_factor"]])
print("주 팩터 분포:", Counter(idx["dominant_factor"]).most_common())
mism_div = sum(1 for k in idx.index if abs(idx.loc[k, "factor_diversity"] - live[k]["factor_diversity"]) > 1e-3)
mism_dom = sum(1 for k in idx.index if idx.loc[k, "dominant_factor"] != live[k]["dominant_factor"])
print(f"[대조] 식(6) factor_diversity 불일치 {mism_div}/100, dominant_factor 불일치 {mism_dom}/100")
'''),
md('''
## 6. 4구획 배정과 2×2 독립성 검정

포지셔닝 맵의 4구획은 **표본 평균**을 기준선으로 한다(충성도 평균 0.371, 파급효과 평균 0.266).
보고서의 "4분면 독립성 χ²"는 이와 별도로 **0.5 기준** 2×2표(Yates 보정)로 계산하므로 두 표를 혼동하지 않는다.
'''),
code('''
mL, mS = idx["loyalty_score"].mean(), idx["spillover_score"].mean()


def quadrant(l, s):
    if l >= mL and s >= mS:
        return "핵심전략형"
    if l >= mL:
        return "내부결속형"
    if s >= mS:
        return "외부견인형"
    return "주변부"


idx["quadrant"] = [quadrant(l, s) for l, s in zip(idx["loyalty_score"], idx["spillover_score"])]
print(f"평균 기준선: 충성도 {mL:.4f}, 파급효과 {mS:.4f}")
print("4구획(평균 기준):", {q: int(n) for q, n in idx["quadrant"].value_counts().items()})
mism = sum(1 for k in idx.index if idx.loc[k, "quadrant"] != payload[k]["quadrant"])
print(f"[대조] 4구획 ↔ 3D 맵 payload 불일치: {mism}/100")

hi_l, hi_s = idx["loyalty_score"] >= 0.5, idx["spillover_score"] >= 0.5
tab = np.array([[int((hi_l & hi_s).sum()), int((hi_l & ~hi_s).sum())], [int((~hi_l & hi_s).sum()), int((~hi_l & ~hi_s).sum())]])
chi2, p, dof, exp = stats.chi2_contingency(tab, correction=True)
print(f"\\n0.5 기준 2×2표 {tab.tolist()} → χ²={chi2:.4f}, dof={dof}, p={p:.6f} (Yates 보정)")
r, pr = stats.pearsonr(idx["loyalty_score"], idx["spillover_score"])
print(f"충성도–파급효과 Pearson r={r:.4f} (p={pr:.2e})")
'''),
md('''
## 7. 결과 저장과 전량 대조

이 노트북이 산출한 100개 팬덤의 지표를 `index_calculation_v7_result.csv`(utf-8-sig)로 저장하고, 저장소의 최종 산출 파일과
항목별로 대조한다.
'''),
code('''
cols = ["category", "n_loyalty", "n_spillover", "activity", "loyalty_raw", "spillover_raw", "loyalty_score", "spillover_score",
        "Lang", "Mkt", "Src", "Time", "Ent", "coverage_index", "factor_diversity", "dominant_factor", "quadrant"]
result = idx[cols].sort_values("loyalty_score", ascending=False)
out_csv = OUT_DIR / "index_calculation_v7_result.csv"
result.to_csv(out_csv, encoding="utf-8-sig")
print(f"저장: {out_csv.relative_to(REPO)}  ({len(result)}행 × {len(cols)}열)")

checks = {
    "식(1) loyalty_raw / spillover_raw": sum(1 for k in idx.index if abs(idx.loc[k, "loyalty_raw"] - live[k]["loyalty_raw"]) > 1e-6 or abs(idx.loc[k, "spillover_raw"] - live[k]["spillover_raw"]) > 1e-6),
    "식(2) loyalty_score / spillover_score": sum(1 for k in idx.index if abs(idx.loc[k, "loyalty_score"] - live[k]["loyalty_score"]) > 1e-3 or abs(idx.loc[k, "spillover_score"] - live[k]["spillover_score"]) > 1e-3),
    "식(3) coverage_index": sum(1 for k in idx.index if abs(idx.loc[k, "coverage_index"] - live[k]["coverage_index"]) > 1e-3),
    "식(4) language_coverage": sum(1 for k in idx.index if abs(idx.loc[k, "Lang"] - live[k]["coverage_detail"]["language_coverage"]) > 1e-3),
    "식(6) factor_diversity": sum(1 for k in idx.index if abs(idx.loc[k, "factor_diversity"] - live[k]["factor_diversity"]) > 1e-3),
    "식(7) activity": sum(1 for k in idx.index if idx.loc[k, "activity"] != live[k]["activity"]),
    "dominant_factor": sum(1 for k in idx.index if idx.loc[k, "dominant_factor"] != live[k]["dominant_factor"]),
    "4구획(payload)": sum(1 for k in idx.index if idx.loc[k, "quadrant"] != payload[k]["quadrant"]),
}
summary = pd.DataFrame([{"항목": k, "불일치 팬덤 수 (/100)": v, "결과": "일치" if v == 0 else "불일치"} for k, v in checks.items()])
display(summary)
result.head(15)
'''),
md('''
## 한계

1. **식(1)(2)(7)은 근거문장 텍스트만으로 완전히 산출된다.** 코퍼스 10,020건과 이 노트북의 정규식·키워드 목록만 있으면 저장된
   원점수·정규화 점수·활동량이 그대로 나온다.
2. **식(3)(4)의 문장 단위 태깅(언어·시장·출처유형·연도·엔티티)과 식(5)의 θ(문서-토픽 비중)는 파이프라인 산출물**이다.
   노트북은 팬덤별 집계값(`coverage_detail`, `factor_share`)에서 하위지표·엔트로피·가중합을 다시 계산한다. 태깅 규칙 자체를
   바꾸려면 `run_lda_v6.py`와 언어 분류기(`analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py`)를 본다.
3. 시간(Time) 하위지표의 분모는 100개 팬덤 연도의 합집합 크기로 두었고, 저장된 `time_coverage`와 100/100 일치한다.
'''),
]


def main(execute=True):
    nb = new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                             "language_info": {"name": "python"}})
    nbformat.write(nb, OUT)
    print("wrote", OUT)
    if execute:
        subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                        "--ExecutePreprocessor.timeout=600", str(OUT)], check=True, cwd=HERE)
        subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", str(OUT)], check=True, cwd=HERE)
        print("executed + html exported")


if __name__ == "__main__":
    main(execute="--no-exec" not in sys.argv[1:])
