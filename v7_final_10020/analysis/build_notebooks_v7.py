# -*- coding: utf-8 -*-
"""v7_final_analysis 노트북 생성기 — 최종 코퍼스 10,020건 기준 분석 노트북 8개를 nbformat으로 만들고
jupyter nbconvert --execute 로 실행해 출력까지 저장한다.

archive/v6_r22_era/ 의 r22(5,612건) 노트북과 같은 절 구성을 유지하되, 입력은 전부 data/v7_final/ 의
최종 산출물이며 아카이브 파일은 수정하지 않는다(비교용으로 읽기만 한다).

실행: python v7_final_10020/analysis/build_notebooks_v7.py            # 생성 + 실행
      python v7_final_10020/analysis/build_notebooks_v7.py --no-exec  # 생성만
"""
import subprocess
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

HERE = Path(__file__).resolve().parent

PRE = '''import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.max_colwidth", 60)
pd.set_option("display.width", 140)


def find_repo_root():
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "data" / "v7_final" / "fandoms_v3_100.json").exists():
            return p
    raise FileNotFoundError("저장소 루트(data/v7_final/fandoms_v3_100.json)를 찾지 못함 — 저장소 안에서 실행하세요")


REPO = find_repo_root()
DATA_DIR = REPO / "data" / "v7_final"                       # 최종 산출물(10,020건 라이브 + 동결 스냅샷 7,350건)
ROUNDS_DIR = REPO / "data" / "v7_rounds"                    # 병합 로그 r1~r72
ARCHIVE_DIR = REPO / "archive" / "v6_r22_era" / "data" / "v6_r22_snapshot"   # r22(5,612건) 비교용, 읽기 전용


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_bullets(fandoms):
    rows = []
    for rec in fandoms:
        for kind in ("loyalty", "spillover"):
            for item in rec.get(kind, []):
                rows.append({"fandom": rec["fandom"], "category": rec.get("category"),
                             "bullet_type": kind, "text": item.get("t", "") or "", "url": item.get("u", "") or ""})
    return pd.DataFrame(rows)
'''

INTEGRITY_FS = '''
def check_factor_share(scores, label):
    sum_mismatch, dominant_mismatch = [], []
    for d in scores:
        shares = d["factor_share"]
        if abs(sum(shares.values()) - 1.0) > 0.001:
            sum_mismatch.append((d["fandom"], round(sum(shares.values()), 4)))
        if max(shares, key=shares.get) != d["dominant_factor"]:
            dominant_mismatch.append((d["fandom"], max(shares, key=shares.get), d["dominant_factor"]))
    print(f"[{label}] factor_share 합 != 1.0 인 팬덤 수: {len(sum_mismatch)} / {len(scores)}")
    print(f"[{label}] dominant_factor 재계산 불일치 팬덤 수: {len(dominant_mismatch)} / {len(scores)}")
    return sum_mismatch, dominant_mismatch
'''

HIGHLIGHT = '["BTS", "임영웅", "리센느(RESCENE)"]'


def md(s):
    return new_markdown_cell(s.strip("\n"))


def code(s):
    return new_code_cell(s.strip("\n"))


# ---------------------------------------------------------------------------------------------
# 1. 광고·상업성 지수
# ---------------------------------------------------------------------------------------------
def nb_ad_commercial():
    cells = [
        md('''
# 광고·상업성 지수(Ad/Commercial Index) — 최종 코퍼스 10,020건 검증 노트북

r22(5,612건) 시점의 `archive/v6_r22_era/Ad_Commercial Pilot/ad_commercial_pilot.ipynb`는 원본 지수 JSON이 없어
LDA 메타요인 "브랜드·상업형(광고·앰버서더)" 비중을 대체 지표로 썼다. 이제 원본 `data/v7_final/ad_commercial_index_v7.json`
(10,020건 기준, 광고신호 키워드 31개·업종 20개)이 있으므로, 이 노트북은 **원본 지수 자체를 코퍼스와 대조해 재검증**하고,
아카이브 노트북이 했던 LDA 병행지표 비교는 마지막 절에서 최종 라이브 점수로 다시 수행한다.

| 입력 | 내용 |
|---|---|
| `ad_commercial_index_v7.json` | 팬덤별 광고성 불릿 수·비중·업종 카운트, 코퍼스 합계, 라운드별 이력(v7-39~43) |
| `fandoms_v3_100.json` | 근거문장 10,020건(키워드 재매칭·근거문장 수 대조용) |
| `fandom_scores_live_reference_v7.json` | 라이브 10,020건 LDA 재적합 점수(K=8/M=5, 게이트 미통과 — 참고용 병행지표) |
'''),
        code(PRE + '''
ad = load_json(DATA_DIR / "ad_commercial_index_v7.json")
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
live_scores = load_json(DATA_DIR / "fandom_scores_live_reference_v7.json")
bullets_df = flatten_bullets(fandoms)

print("근거문장 수(fandoms_v3_100.json):", len(bullets_df), "| JSON total_bullets:", ad["total_bullets"])
print("광고성 불릿:", ad["total_ad_bullets"], f"({ad['corpus_ad_share']:.1%})", "| 1건 이상 팬덤:", ad["n_fandoms_with_any_ad_bullet"])
print("업종 수:", len(ad["industries"]), "| 광고신호 키워드 수:", len(ad["ad_signal_keywords"]))
print("methodology:", ad["methodology"][:160], "...")
'''),
        md("## 1. 데이터 무결성 검증 — 코퍼스·합계·업종 카운트"),
        code('''
per_fandom_corpus = bullets_df.groupby("fandom").size().to_dict()
rows = []
n_total_mismatch = share_mismatch = top_mismatch = 0
for rec in ad["fandoms"]:
    if per_fandom_corpus.get(rec["fandom"]) != rec["n_total_bullets"]:
        n_total_mismatch += 1
    if abs(rec["n_ad_bullets"] / rec["n_total_bullets"] - rec["ad_share"]) > 0.0005:
        share_mismatch += 1
    if rec["industry_counts"] and rec["industry_counts"].get(rec["top_industry"], -1) != max(rec["industry_counts"].values()):
        top_mismatch += 1   # 동점 업종이 있을 수 있으므로 "최댓값 업종 중 하나인가"로 검사
    rows.append({"팬덤": rec["fandom"], "구분": rec["category"], "근거문장수": rec["n_total_bullets"],
                 "광고성문장수": rec["n_ad_bullets"], "광고비중": rec["ad_share"], "대표업종": rec["top_industry"],
                 "업종태깅합": sum(rec["industry_counts"].values())})
ad_df = pd.DataFrame(rows)

print(f"팬덤별 근거문장 수 != 코퍼스 실측: {n_total_mismatch} / {len(ad_df)}")
print(f"ad_share != n_ad/n_total (오차 > 0.0005): {share_mismatch} / {len(ad_df)}")
print(f"top_industry가 최다 업종(동점 포함)이 아닌 팬덤: {top_mismatch} / {len(ad_df)}")
print(f"광고성문장수 합 {ad_df['광고성문장수'].sum()} == total_ad_bullets {ad['total_ad_bullets']} :", ad_df["광고성문장수"].sum() == ad["total_ad_bullets"])
print(f"1건 이상 팬덤 {(ad_df['광고성문장수'] > 0).sum()} == n_fandoms_with_any_ad_bullet {ad['n_fandoms_with_any_ad_bullet']} :",
      (ad_df["광고성문장수"] > 0).sum() == ad["n_fandoms_with_any_ad_bullet"])

ind_sum = {}
for rec in ad["fandoms"]:
    for k, v in rec["industry_counts"].items():
        ind_sum[k] = ind_sum.get(k, 0) + v
print("업종별 합 == industry_totals :", ind_sum == ad["industry_totals"])
print(f"업종 태깅 합계 {sum(ind_sum.values())} (광고성 불릿 {ad['total_ad_bullets']}건 — 한 불릿에 복수 업종 허용)")
'''),
        md("## 2. 팬덤별 광고성 문장 수·비중 — 상위 15 (원본 CSV와 같은 광고성문장수 내림차순)"),
        code('''
ad_df = ad_df.sort_values(["광고성문장수", "광고비중"], ascending=[False, False]).reset_index(drop=True)
ad_df.index = ad_df.index + 1
print("강조 3팬덤:")
for name in ''' + HIGHLIGHT + ''':
    r = ad_df[ad_df["팬덤"] == name]
    print(f"  {name}: 광고성 {int(r['광고성문장수'].iloc[0])}건 / {int(r['근거문장수'].iloc[0])}건 = {r['광고비중'].iloc[0]:.1%} (순위 {r.index[0]}위, 대표업종 {r['대표업종'].iloc[0]})")
ad_df.head(15)
'''),
        md("## 3. 업종별 분포 — 20개 업종 중 어디에 광고 신호가 몰리는가"),
        code('''
ind_df = (pd.DataFrame([{"업종": k, "태깅건수": v} for k, v in ad["industry_totals"].items()])
          .sort_values("태깅건수", ascending=False).reset_index(drop=True))
ind_df["비중"] = (ind_df["태깅건수"] / ind_df["태깅건수"].sum()).round(4)
ind_df.index = ind_df.index + 1
missing = [i for i in ad["industries"] if i not in ad["industry_totals"]]
print("industries 목록에 있으나 태깅 0건인 업종:", missing)
ind_df
'''),
        md("## 4. 카테고리(장르)별 평균 광고비중"),
        code('''
cat_df = (ad_df.groupby("구분")["광고비중"].agg(["mean", "count"])
          .rename(columns={"mean": "평균 광고비중", "count": "팬덤 수"}).sort_values("평균 광고비중", ascending=False))
cat_df["평균 광고비중"] = cat_df["평균 광고비중"].round(4)
cat_df
'''),
        md('''
## 5. 광고신호 키워드 재매칭 — 원본 방법론을 코퍼스에 독립 재적용

원본 methodology: (1) 31개 광고신호 키워드 부분 문자열 매칭으로 광고성 불릿 판정, 단 `협찬`이 유일한 신호이고 "협찬 없이"류
부정형이면 제외(v7-40 부정 가드) → (2) 업종 키워드 태깅. 업종 키워드 사전은 JSON에 없으므로 (1)단계만 재현한다.
'''),
        code('''
SIGNALS = ad["ad_signal_keywords"]
NEGATION = ["협찬 없이", "협찬없이", "협찬을 받지", "협찬 없는", "협찬이 아닌", "무협찬", "협찬 아닌"]

def is_ad_bullet(text):
    hits = [k for k in SIGNALS if k in text]
    if not hits:
        return False
    if set(hits) == {"협찬"} and any(n in text for n in NEGATION):
        return False
    return True

bullets_df["ad_hit"] = bullets_df["text"].apply(is_ad_bullet)
recomp = bullets_df.groupby("fandom")["ad_hit"].sum().astype(int)
orig = {r["fandom"]: r["n_ad_bullets"] for r in ad["fandoms"]}
cmp = pd.DataFrame({"원본 n_ad_bullets": pd.Series(orig), "재매칭": recomp}).fillna(0).astype(int)
cmp["차이"] = cmp["재매칭"] - cmp["원본 n_ad_bullets"]
print(f"재매칭 광고성 불릿 합계: {int(cmp['재매칭'].sum())}건 (원본 {ad['total_ad_bullets']}건)")
print(f"팬덤별 정확 일치: {(cmp['차이'] == 0).sum()} / {len(cmp)}, |차이|<=2: {(cmp['차이'].abs() <= 2).sum()} / {len(cmp)}")
print("(정확히 일치하지 않는 팬덤은 원본이 부정 가드·키워드 경계를 추가 규칙으로 처리한 흔적 — 재현 한계로 기록)")
cmp.sort_values("차이", key=lambda s: s.abs(), ascending=False).head(10)
'''),
        md("## 6. LDA 병행지표와의 대조 — 아카이브 노트북의 접근을 최종 라이브 점수로 재수행"),
        code(INTEGRITY_FS + '''
check_factor_share(live_scores, "라이브 10,020건 K=8/M=5")
FACTOR = "브랜드·상업형(광고·앰버서더)"
live_share = {d["fandom"]: d["factor_share"].get(FACTOR, 0.0) for d in live_scores}
ad_df["LDA 브랜드·상업형 비중(라이브)"] = ad_df["팬덤"].map(live_share)
r_p = np.corrcoef(ad_df["광고비중"], ad_df["LDA 브랜드·상업형 비중(라이브)"])[0, 1]
r_s = ad_df[["광고비중", "LDA 브랜드·상업형 비중(라이브)"]].corr(method="spearman").iloc[0, 1]
print(f"Pearson r(키워드 광고비중, LDA 브랜드·상업형 비중) = {r_p:.4f} | Spearman rho = {r_s:.4f}")
n_dom = sum(1 for d in live_scores if d["dominant_factor"] == FACTOR)
print(f"라이브 점수에서 dominant_factor가 브랜드·상업형인 팬덤: {n_dom} / {len(live_scores)}")
print("주의: 동결 스냅샷(7,350건, K=10/M=5)의 5개 메타요인에는 브랜드·상업형 라벨이 없다(현장경제·소비력·미디어노출·차트확산·결속).")
print("      라이브 재적합(실루엣 0.046)은 게이트 미통과라 보고서 본문 지표가 아니며, 여기서는 병행 참고치로만 쓴다.")
ad_df[["팬덤", "광고비중", "LDA 브랜드·상업형 비중(라이브)"]].head(10)
'''),
        md("## 7. 라운드별 이력 — v7-39~43 시점 값(JSON 내장)과 최종값"),
        code('''
hist = []
for key in ["v7_39_before", "v7_40_before", "v7_41_before", "v7_42_before", "v7_43_before"]:
    h = ad[key]
    hist.append({"시점": key.replace("_before", ""), "total_bullets": h.get("total_bullets"), "total_ad_bullets": h["total_ad_bullets"],
                 "corpus_ad_share": h["corpus_ad_share"], "n_fandoms": h["n_fandoms_with_any_ad_bullet"], "기타(잔여)": h["industry_totals"].get("기타")})
hist.append({"시점": "최종(v7-72)", "total_bullets": ad["total_bullets"], "total_ad_bullets": ad["total_ad_bullets"],
             "corpus_ad_share": ad["corpus_ad_share"], "n_fandoms": ad["n_fandoms_with_any_ad_bullet"], "기타(잔여)": ad["industry_totals"].get("기타")})
print("residual_diagnosis:", ad["residual_diagnosis"]["note"][:120], "... total_residual =", ad["residual_diagnosis"]["total_residual"])
pd.DataFrame(hist)
'''),
        md('''
## 8. 한계

1. 업종 키워드 사전(20개 업종 × 브랜드 약 100개 추가)은 JSON에 저장돼 있지 않아 (2)단계 업종 태깅은 재현하지 않았다 — 5절은 광고신호 (1)단계만 재현한다.
2. 원본 `residual_diagnosis`(기타 79건의 원인 분류)는 Claude가 전수로 읽어 분류한 것으로, 키워드 매칭 수치와 분리된 별도 보고다.
3. 6절의 LDA 병행지표는 게이트를 통과하지 못한 라이브 재적합(실루엣 0.046)에서 나온 값이며, 보고서 본문의 F1~F5(동결 스냅샷)에는 브랜드·상업형 라벨 자체가 없다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 2. 팬덤결속 지수
# ---------------------------------------------------------------------------------------------
def nb_cohesion():
    cells = [
        md('''
# 팬덤결속 지수(Fandom Cohesion Index) — 최종 코퍼스 10,020건 검증 노트북

r22 노트북(`archive/v6_r22_era/Fandom Cohesion Pilot/`)은 LDA "결속형(팬클럽·기부·커뮤니티)" 비중을 대체 지표로 썼다.
이제 원본 `data/v7_final/fandom_cohesion_index_v7.json`(10,020건, 5개 결속 활동 유형 A~E, D 정밀도 게이트)이 있으므로 원본을
코퍼스와 대조해 재검증하고, 동결 스냅샷(7,350건, K=10/M=5)과 라이브(10,020건) 두 LDA 점수의 결속형 비중과도 대조한다.
'''),
        code(PRE + '''
coh = load_json(DATA_DIR / "fandom_cohesion_index_v7.json")
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")                 # 동결 v7-40 스냅샷 7,350건, K=10/M=5
live_scores = load_json(DATA_DIR / "fandom_scores_live_reference_v7.json")    # 라이브 10,020건, K=8/M=5(게이트 미통과)
bullets_df = flatten_bullets(fandoms)
print("근거문장:", len(bullets_df), "| JSON total_bullets:", coh["total_bullets"])
print("결속 불릿:", coh["total_cohesion_bullets"], f"({coh['corpus_cohesion_share']:.1%})", "| 1건 이상 팬덤:", coh["n_fandoms_with_any_cohesion_bullet"])
print("유형:", coh["categories"])
print("D 게이트 정밀도 검증:", coh["d_gate_precision_check"])
'''),
        md("## 1. 데이터 무결성 검증"),
        code('''
per_fandom_corpus = bullets_df.groupby("fandom").size().to_dict()
rows = []; n_mis = share_mis = top_mis = 0
for rec in coh["fandoms"]:
    if per_fandom_corpus.get(rec["fandom"]) != rec["n_total_bullets"]: n_mis += 1
    if abs(rec["n_cohesion_bullets"] / rec["n_total_bullets"] - rec["cohesion_share"]) > 0.0005: share_mis += 1
    if rec["category_counts"] and rec["category_counts"].get(rec["top_category"], -1) != max(rec["category_counts"].values()): top_mis += 1  # 동점 허용
    row = {"팬덤": rec["fandom"], "구분": rec["category"], "근거문장수": rec["n_total_bullets"], "결속문장수": rec["n_cohesion_bullets"],
           "결속비중": rec["cohesion_share"], "대표유형": rec["top_category"]}
    row.update({c: rec["category_counts"].get(c, 0) for c in coh["categories"]})
    rows.append(row)
coh_df = pd.DataFrame(rows)
cat_sum = {c: int(coh_df[c].sum()) for c in coh["categories"]}
print(f"근거문장 수 != 코퍼스 실측: {n_mis} / {len(coh_df)} | cohesion_share 재계산 불일치: {share_mis} | top_category가 최다 유형(동점 포함)이 아님: {top_mis}")
print(f"결속문장수 합 {coh_df['결속문장수'].sum()} == total_cohesion_bullets {coh['total_cohesion_bullets']} :", coh_df["결속문장수"].sum() == coh["total_cohesion_bullets"])
print("유형별 합 == category_totals :", cat_sum == coh["category_totals"], cat_sum)
print(f"1건 이상 팬덤: {(coh_df['결속문장수'] > 0).sum()} (JSON {coh['n_fandoms_with_any_cohesion_bullet']})")
'''),
        md("## 2. 팬덤별 결속 문장 수·비중 — 상위 15"),
        code('''
coh_df = coh_df.sort_values(["결속문장수", "결속비중"], ascending=[False, False]).reset_index(drop=True)
coh_df.index = coh_df.index + 1
coh_df.head(15)
'''),
        md("## 3. 강조 3팬덤 — BTS·임영웅·리센느(RESCENE) (KEY_FINDINGS: 15건 6.6% / 30건 23% 전체 1위 / 18건 21.2%)"),
        code('''
for name in ''' + HIGHLIGHT + ''':
    r = coh_df[coh_df["팬덤"] == name]
    print(f"{name}: 결속 {int(r['결속문장수'].iloc[0])}건 / {int(r['근거문장수'].iloc[0])}건 = {r['결속비중'].iloc[0]:.1%} "
          f"(결속문장수 {r.index[0]}위, 대표유형 {r['대표유형'].iloc[0]})")
rank_by_share = coh_df.sort_values("결속비중", ascending=False).reset_index(drop=True)
print("결속비중 1위:", rank_by_share.iloc[0]["팬덤"], f"{rank_by_share.iloc[0]['결속비중']:.1%}")
'''),
        md("## 4. 유형별(A~E) 분포와 카테고리별 평균"),
        code('''
type_df = pd.DataFrame([{"유형": c, "건수": coh["category_totals"][c]} for c in coh["categories"]]).sort_values("건수", ascending=False)
type_df["비중(멀티라벨 합 대비)"] = (type_df["건수"] / type_df["건수"].sum()).round(4)
print(type_df.to_string(index=False))
print()
cat_df = (coh_df.groupby("구분")["결속비중"].agg(["mean", "count"]).rename(columns={"mean": "평균 결속비중", "count": "팬덤 수"})
          .sort_values("평균 결속비중", ascending=False))
cat_df["평균 결속비중"] = cat_df["평균 결속비중"].round(4)
cat_df
'''),
        md("## 5. LDA 결속형 비중과의 대조 — 동결 스냅샷(보고서 본문)과 라이브 재적합 모두"),
        code(INTEGRITY_FS + '''
check_factor_share(frozen_scores, "동결 7,350건 K=10/M=5")
check_factor_share(live_scores, "라이브 10,020건 K=8/M=5")
FACTOR = "결속형(팬클럽·기부·커뮤니티)"
coh_df["LDA 결속형(동결)"] = coh_df["팬덤"].map({d["fandom"]: d["factor_share"].get(FACTOR, 0.0) for d in frozen_scores})
coh_df["LDA 결속형(라이브)"] = coh_df["팬덤"].map({d["fandom"]: d["factor_share"].get(FACTOR, 0.0) for d in live_scores})
for col in ["LDA 결속형(동결)", "LDA 결속형(라이브)"]:
    sub = coh_df.dropna(subset=[col])
    r_p = np.corrcoef(sub["결속비중"], sub[col])[0, 1]
    r_s = sub[["결속비중", col]].corr(method="spearman").iloc[0, 1]
    print(f"{col}: n={len(sub)}, Pearson r={r_p:.4f}, Spearman rho={r_s:.4f}")
print("동결 스냅샷 로스터에 없는 팬덤(라이브 전용):", sorted(set(coh_df["팬덤"]) - {d["fandom"] for d in frozen_scores}))
print("동결에서 dominant_factor가 결속형인 팬덤:", [d["fandom"] for d in frozen_scores if d["dominant_factor"] == FACTOR])
coh_df[["팬덤", "결속비중", "LDA 결속형(동결)", "LDA 결속형(라이브)"]].head(10)
'''),
        md('''
## 6. 한계

1. A~E 유형별 키워드 목록과 D 게이트 공존 키워드(팬클럽/팬카페/팬덤/팬들/함께/자발적/정회원/회원)는 methodology 문구로만 남아 있고 키워드 전체 사전은 JSON에 없어 키워드 재매칭은 수행하지 않았다.
2. 결속 지수는 키워드 매칭 지표이고 LDA 결속형 비중은 토픽 혼합비중이라 계산 방식이 다르다 — 5절 상관은 "같은 방향을 가리키는가"만 본다.
3. 동결 스냅샷 로스터(한로로·pH-1·BE'O 포함)와 라이브 로스터(몬스타엑스·투어스(TWS)·빈지노 포함)는 3개 팬덤이 다르다(README 로스터 절).
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 3. 미디어 콘텐츠 노출 지수 + 미디어 크로스오버(매체 확산) 지수
# ---------------------------------------------------------------------------------------------
def nb_media():
    cells = [
        md('''
# 미디어 콘텐츠 노출 지수 · 미디어 크로스오버 지수 — 최종 코퍼스 10,020건 검증 노트북

r22 노트북(`archive/v6_r22_era/Media Content Exposure Pilot/`)은 LDA "미디어노출형(방송·조회수)" 비중을 대체 지표로 쓰고
v7 10·11라운드 병합 로그와 교차검증했다. 최종 데이터에는 원본 지수 두 개가 있다.

| 입력 | 내용 |
|---|---|
| `media_exposure_v7.json` | 4개 서브태그(예능/유튜브/영화/드라마) 키워드 매칭 — 1,025건(10.2%), 99개 팬덤 |
| `media_crossover_index_v7.json` | news_media 출처 도메인 기준 고유 매체 수·매체다양성비율 — 6,712건(67.0%), 고유 매체 1,298개 |
| `k9_validation_v7.json` | "독립적인 미디어 토픽/메타요인이 있는가" K=9 검증(보고서 10.8절) |
| `data/v7_rounds/merge_log_r10.json`, `merge_log_r11.json` | 미디어 크로스오버 리서치 라운드(131건 + 143건) |
| `fandom_scores_v6.json` | 동결 스냅샷(7,350건, K=10/M=5) — 보고서 본문 미디어노출형 비중 |
'''),
        code(PRE + '''
media = load_json(DATA_DIR / "media_exposure_v7.json")
xover = load_json(DATA_DIR / "media_crossover_index_v7.json")
k9 = load_json(DATA_DIR / "k9_validation_v7.json")
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
r10 = load_json(ROUNDS_DIR / "merge_log_r10.json")
r11 = load_json(ROUNDS_DIR / "merge_log_r11.json")
bullets_df = flatten_bullets(fandoms)
print("근거문장:", len(bullets_df))
print("media_exposure:", media["total_media_bullets"], f"({media['corpus_media_share']:.1%})", media["subtag_totals"], "| 1건 이상 팬덤", media["n_fandoms_with_any_media_bullet"])
print("media_crossover: news_media", xover["total_news_media_bullets"], f"({xover['corpus_news_media_share']:.1%})", "| 고유 매체", xover["n_distinct_outlets_corpuswide"])
print("r10:", r10["round"], r10["net_new_bullets"], "건 /", r10["n_touched_fandoms"], "팬덤 | r11:", r11["round"], r11["net_new_bullets"], "건 /", r11["n_touched_fandoms"], "팬덤")
'''),
        md("## 1. 데이터 무결성 검증 — 두 지수 모두"),
        code('''
per_fandom_corpus = bullets_df.groupby("fandom").size().to_dict()
rows = []; n_mis = share_mis = 0
for rec in media["fandoms"]:
    if per_fandom_corpus.get(rec["fandom"]) != rec["n_total_bullets"]: n_mis += 1
    if abs(rec["n_media_bullets"] / rec["n_total_bullets"] - rec["media_share"]) > 0.0005: share_mis += 1
    row = {"팬덤": rec["fandom"], "구분": rec["category"], "근거문장수": rec["n_total_bullets"], "미디어문장수": rec["n_media_bullets"], "미디어비중": rec["media_share"]}
    row.update({s: rec["subtag_counts"].get(s, 0) for s in media["subtags"]})
    rows.append(row)
media_df = pd.DataFrame(rows)
sub_sum = {s: int(media_df[s].sum()) for s in media["subtags"]}
print(f"[노출] 근거문장 수 != 코퍼스: {n_mis} | media_share 불일치: {share_mis} | 합 {media_df['미디어문장수'].sum()} == {media['total_media_bullets']}: {media_df['미디어문장수'].sum() == media['total_media_bullets']} | 서브태그 합 == subtag_totals: {sub_sum == media['subtag_totals']}")

# 서브태그 키워드 재매칭(4개 서브태그명 그대로 부분 문자열) — 원본이 사용한 정확한 키워드 사전은 JSON에 없으므로 근사
for s in media["subtags"]:
    bullets_df[s] = bullets_df["text"].str.contains(s, regex=False)
bullets_df["media_hit"] = bullets_df[media["subtags"]].any(axis=1)
recomp = bullets_df.groupby("fandom")["media_hit"].sum().astype(int)
media_df["재매칭(서브태그명 단순 포함)"] = media_df["팬덤"].map(recomp)
diff = media_df["재매칭(서브태그명 단순 포함)"] - media_df["미디어문장수"]
print(f"[노출] 서브태그명 단순 포함 재매칭 합계 {int(recomp.sum())}건 vs 원본 {media['total_media_bullets']}건, 팬덤별 정확 일치 {(diff == 0).sum()}/100 (원본은 확장 키워드 사전 사용 — 근사 재현)")

rows = []; n_mis = ratio_mis = 0
for rec in xover["fandoms"]:
    if per_fandom_corpus.get(rec["fandom"]) != rec["n_total_bullets"]: n_mis += 1
    if rec["n_news_media_bullets"] and abs(rec["n_distinct_outlets"] / rec["n_news_media_bullets"] - rec["outlet_diversity_ratio"]) > 0.0005: ratio_mis += 1
    rows.append({"팬덤": rec["fandom"], "구분": rec["category"], "근거문장수": rec["n_total_bullets"], "뉴스매체문장수": rec["n_news_media_bullets"],
                 "뉴스매체비중": rec["news_media_share"], "고유매체수": rec["n_distinct_outlets"], "매체다양성비율": rec["outlet_diversity_ratio"],
                 "상위매체": ", ".join(o["domain"] for o in rec["top_outlets"][:3])})
xover_df = pd.DataFrame(rows)
print(f"[크로스오버] 근거문장 수 != 코퍼스: {n_mis} | outlet_diversity_ratio 불일치: {ratio_mis} | 뉴스매체문장 합 {xover_df['뉴스매체문장수'].sum()} == {xover['total_news_media_bullets']}: {xover_df['뉴스매체문장수'].sum() == xover['total_news_media_bullets']}")
'''),
        md("## 2. 팬덤별 미디어 노출 — 상위 15 (미디어문장수 순) / 매체 확산 폭 상위 10"),
        code('''
media_df = media_df.sort_values(["미디어문장수", "미디어비중"], ascending=[False, False]).reset_index(drop=True); media_df.index += 1
for name in ''' + HIGHLIGHT + ''':
    r = media_df[media_df["팬덤"] == name]; x = xover_df[xover_df["팬덤"] == name]
    print(f"{name}: 미디어 {int(r['미디어문장수'].iloc[0])}건 ({r['미디어비중'].iloc[0]:.1%}, {r.index[0]}위) | 고유매체 {int(x['고유매체수'].iloc[0])}개, 매체다양성비율 {x['매체다양성비율'].iloc[0]:.3f}")
display(media_df.head(15))
xover_df.sort_values("고유매체수", ascending=False).head(10).reset_index(drop=True)
'''),
        md("## 3. 코퍼스 증거와의 교차검증 — v7 10·11라운드 미디어 크로스오버 리서치 신규 근거 수와의 관계"),
        code('''
combined_new = {}
for log in (r10, r11):
    for fandom, n in log["per_group_added"].items():
        combined_new[fandom] = combined_new.get(fandom, 0) + n
media_df["r10+r11 신규 근거"] = media_df["팬덤"].map(combined_new).fillna(0).astype(int)
tot = sum(combined_new.values())
print(f"r10+r11 신규 근거 합 {tot}건 == {r10['net_new_bullets']}+{r11['net_new_bullets']}={r10['net_new_bullets'] + r11['net_new_bullets']} :", tot == r10["net_new_bullets"] + r11["net_new_bullets"])
r_cnt = np.corrcoef(media_df["r10+r11 신규 근거"], media_df["미디어문장수"])[0, 1]
r_shr = np.corrcoef(media_df["r10+r11 신규 근거"], media_df["미디어비중"])[0, 1]
print(f"Pearson r(신규 근거 수, 미디어문장수) = {r_cnt:.4f} | r(신규 근거 수, 미디어비중) = {r_shr:.4f}")
print("-> r22 노트북에서는 LDA 비중과 신규 건수의 상관이 약했다. 최종 키워드 지수는 그 라운드에서 들어온 문장을 직접 세므로 상관이 훨씬 높게 나오는 것이 정상이다.")
top_new = set(media_df.sort_values("r10+r11 신규 근거", ascending=False).head(10)["팬덤"])
top_cnt = set(media_df.head(10)["팬덤"])
print(f"신규 근거 상위 10 ∩ 미디어문장수 상위 10 = {len(top_new & top_cnt)}개: {sorted(top_new & top_cnt)}")
'''),
        md("## 4. LDA 미디어노출형 비중(동결 스냅샷, 보고서 본문)과 키워드 지수의 대조 + K=9 검증 요약"),
        code(INTEGRITY_FS + '''
check_factor_share(frozen_scores, "동결 7,350건 K=10/M=5")
FACTOR = "미디어노출형(방송·조회수)"
media_df["LDA 미디어노출형(동결)"] = media_df["팬덤"].map({d["fandom"]: d["factor_share"].get(FACTOR, 0.0) for d in frozen_scores})
sub = media_df.dropna(subset=["LDA 미디어노출형(동결)"])
print(f"n={len(sub)}, Pearson r(미디어비중, LDA 미디어노출형)={np.corrcoef(sub['미디어비중'], sub['LDA 미디어노출형(동결)'])[0, 1]:.4f}, "
      f"Spearman rho={sub[['미디어비중', 'LDA 미디어노출형(동결)']].corr(method='spearman').iloc[0, 1]:.4f}")
print("동결에서 dominant_factor=미디어노출형:", [d["fandom"] for d in frozen_scores if d["dominant_factor"] == FACTOR])
print()
print("K=9 검증(k9_validation_v7.json):", k9["methodology"][:90], "...")
print("  corpus_docs:", k9["corpus_docs"], "| K-grid 승자:", k9["k_grid_winner"], "| 기존 그리드에 K=9 없었음:", k9["existing_k_grid_never_tested_k9"])
print("  K=9 phi의 M-grid에서 media 토픽이 단독 메타요인으로 분리되는 M:", [m["m"] for m in k9["m_grid_on_k9_phi"] if m["media_topic_isolated"]],
      "| 각 M 실루엣:", {m["m"]: m["silhouette"] for m in k9["m_grid_on_k9_phi"]})
print("  서브태그 문서빈도(%):", {k: v["pct_of_docs"] for k, v in k9["subtag_doc_freq"].items()})
print("  -> 미디어 토픽이 분리되는 M=6~8에서 실루엣이 0.08 이하로 떨어져 통계적으로 독립된 미디어 메타요인은 채택되지 않았고, 키워드 지수(media_exposure_v7.json)로 대체됐다.")
pd.DataFrame(k9["k_grid"])
'''),
        md('''
## 5. 한계

1. 두 지수 모두 LDA와 무관한 문자열/도메인 매칭 보조지표다. 크로스오버 지수는 "팬 유입 경로"를 측정하지 않으며 매체 확산 폭의 대리치일 뿐이다(`scope_and_limits`).
2. 노출 지수의 확장 키워드 사전은 JSON에 없어 1절 재매칭은 서브태그명 단순 포함으로만 근사했다.
3. `domain_of()`/`source_type_of()`는 최종 토크나이저 소스(`run_lda_v6_live_reference_v7.py`, 저장소에 없음)의 정의를 쓴 것이므로 고유 매체 수는 원본 값을 그대로 검증 대상으로 삼았다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 4. 국내 지역 지수 (최종 코퍼스에 재적용 — 원본 라이브 JSON 미보유)
# ---------------------------------------------------------------------------------------------
REGION_KEYWORDS_SRC = '''
REGIONS = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원",
           "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
# r22 원본 JSON(archive)을 100개 팬덤 × 17개 지역 = 1,700셀 기준 1,698셀 재현하도록 역추적한 키워드 사전.
# 세종은 "세종문화회관" 오매칭 방지로 "세종시/세종특별자치시"만, 경기는 일상어 "경기"와의 충돌로 "경기도"+주요 시 명칭만 인정(원문서 2절 규칙).
REGION_KEYWORDS = {
    "서울": ["서울"], "부산": ["부산"], "대구": ["대구"], "인천": ["인천"], "광주": ["광주"], "대전": ["대전"], "울산": ["울산"],
    "세종": ["세종시", "세종특별자치시"],
    "경기": ["경기도", "수원", "성남", "부천", "안산", "화성", "의정부", "남양주"],
    "강원": ["강원", "춘천", "강릉", "원주", "속초"],
    "충북": ["충북", "청주"],
    "충남": ["충남", "천안", "아산", "보령"],
    "전북": ["전북", "전주"],
    "전남": ["전남", "목포", "순천", "진도", "전라남도"],
    "경북": ["경북", "포항", "경주", "김천", "구미", "울릉"],
    "경남": ["경남", "창원", "진주", "김해", "거제", "남해"],
    "제주": ["제주"],
}
NOTE = ("TEXT-MINING INDEX: 이미 수집된 근거문장 내 국내 지역명(17개 시/도 및 대표 도시) 언급 불릿 수 기반. "
        "Coverage Index의 market_coverage(해외 시장)와는 별개 지표이며, 지역 연고(고향)와 지역 활동(투어·행사)을 구분하지 않고 합산한 1차 신호다. "
        "2026-09-22 최종 코퍼스 10,020건에 r22 파일럿 규칙을 재적용해 산출(원본 라이브 JSON 미보유).")


def region_index(fandoms):
    out = {}
    for rec in fandoms:
        texts = [b.get("t", "") or "" for k in ("loyalty", "spillover") for b in rec.get(k, [])]
        counts = {r: sum(1 for t in texts if any(k in t for k in REGION_KEYWORDS[r])) for r in REGIONS}
        total = sum(counts.values())
        hit = sum(1 for v in counts.values() if v > 0)
        primary = max(counts, key=counts.get) if total else None
        out[rec["fandom"]] = {
            "total_group_bullets": len(texts), "region_mention_counts": counts, "total_region_mentions": total,
            "n_regions_hit": hit, "region_diversity": round(hit / 17, 3),
            "primary_region": primary, "primary_region_share": round(counts[primary] / total, 3) if total else 0.0,
            "note": NOTE,
        }
    return out
'''


def nb_domestic():
    cells = [
        md('''
# 국내 지역 지수(Domestic Regional Index) — 최종 코퍼스 10,020건 재산출 노트북

최종 라이브 국내 지역 지수 JSON(`domestic_regional_index_live_reference_v7.json`)은 저장소에 없다(README 3절). 대신 r22 시점 원본
`archive/v6_r22_era/data/v6_r22_snapshot/domestic_regional_pilot_v6.json`(5,612건)이 있으므로, 이 노트북은

1. r22 원본 JSON을 100개 팬덤 × 17개 지역 셀 단위로 재현하는 키워드 사전을 확정하고(1,698 / 1,700셀 일치, 나머지 2셀은 원본 JSON이 코퍼스보다 한 단계 오래된 흔적),
2. 그 규칙을 최종 코퍼스 10,020건에 그대로 적용해 `domestic_regional_index_v7.json` / `.csv`를 이 폴더에 새로 산출하며,
3. 보고서 본문 표 15(지역 언급 상위 20개 아티스트: BTS 17건·5지역·서울 47%·다양성 0.29, 리센느 19건·경남 58%·0.29, 임영웅 28건·12지역·서울 21%·0.71 전체 1위)가
   어느 코퍼스 시점의 값인지 확인한다 — 결론적으로 표 15는 **동결 스냅샷 v7-40(7,350건)** 값이며, 동결 코퍼스를 근사하면 20행 중 17행이 그대로 재현된다.
'''),
        code(PRE + REGION_KEYWORDS_SRC + '''
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
r22_fandoms = load_json(ARCHIVE_DIR / "fandoms_v3_100.json")
r22_drp = load_json(ARCHIVE_DIR / "domestic_regional_pilot_v6.json")
print("최종 코퍼스:", sum(len(f.get("loyalty", [])) + len(f.get("spillover", [])) for f in fandoms), "건 | r22 코퍼스:",
      sum(len(f.get("loyalty", [])) + len(f.get("spillover", [])) for f in r22_fandoms), "건 | r22 원본 JSON:", len(r22_drp), "팬덤")
'''),
        md("## 1. 규칙 검증 — r22 코퍼스에 적용해 r22 원본 JSON과 셀 단위 대조"),
        code('''
r22_re = region_index(r22_fandoms)
cells_total = cells_ok = 0; mism = []
for name, rec in r22_drp.items():
    for r in REGIONS:
        cells_total += 1
        a, b = rec["region_mention_counts"].get(r, 0), r22_re[name]["region_mention_counts"][r]
        if a == b: cells_ok += 1
        else: mism.append((name, r, a, b))
print(f"r22 셀 일치: {cells_ok} / {cells_total}")
print("불일치 셀(원본, 재계산):", mism)
print("-> 두 셀 모두 r22 코퍼스에 '강원 평창'·'강원 영월군' 문장이 실재하는데 원본 JSON에는 0으로 남아 있어, 원본 JSON이 마지막 병합 직전에 생성된 흔적으로 해석한다(병합 로그 r22의 +1 불일치와 같은 성격).")
tot_ok = sum(1 for n in r22_drp if r22_drp[n]["total_region_mentions"] == r22_re[n]["total_region_mentions"])
div_ok = sum(1 for n in r22_drp if abs(r22_drp[n]["region_diversity"] - r22_re[n]["region_diversity"]) < 0.001)
print(f"total_region_mentions 일치 팬덤: {tot_ok}/100 | region_diversity 일치: {div_ok}/100")
print(f"r22 원본: 검출 지역 수 합 {sum(v['n_regions_hit'] for v in r22_drp.values())} (문서 388/688), 커버리지 {sum(1 for v in r22_drp.values() if v['n_regions_hit'] > 0)}/100")
'''),
        md("## 2. 최종 코퍼스 10,020건에 재적용 — JSON/CSV 산출"),
        code('''
final = region_index(fandoms)
OUT_DIR = Path.cwd() if (Path.cwd() / "domestic_regional_index_v7.ipynb").exists() else REPO / "v7_final_10020" / "analysis" / "domestic_regional_index"
with open(OUT_DIR / "domestic_regional_index_v7.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
rows = []
for name, d in final.items():
    row = {"팬덤": name, "근거문장수": d["total_group_bullets"], "총지역언급": d["total_region_mentions"], "검출지역수": d["n_regions_hit"],
           "지역다양성": d["region_diversity"], "대표지역": d["primary_region"] or "", "대표지역비중": d["primary_region_share"]}
    row.update(d["region_mention_counts"]); rows.append(row)
dr_df = pd.DataFrame(rows).sort_values(["총지역언급", "팬덤"], ascending=[False, True]).reset_index(drop=True)
dr_df.to_csv(OUT_DIR / "domestic_regional_index_v7.csv", index=False, encoding="utf-8-sig")
dr_df.index += 1
n_zero = int((dr_df["총지역언급"] == 0).sum())
print(f"저장: {OUT_DIR / 'domestic_regional_index_v7.json'} / .csv")
print(f"팬덤 커버리지: {100 - n_zero}/100 (0건 팬덤 {n_zero}개: {list(dr_df[dr_df['총지역언급'] == 0]['팬덤'])})")
print(f"검출 지역 수 합계(n_regions_hit 합): {int(dr_df['검출지역수'].sum())} / 1,700 (r22 원본 388) | 총 지역언급 {int(dr_df['총지역언급'].sum())}건")
dr_df.head(18)
'''),
        md('''
## 3. 보고서 표 15(지역 언급 상위 20개)와의 대조 — 표 15는 동결 스냅샷(7,350건) 값

최종 10,020건 값은 표 15보다 큰 팬덤이 많다(god 16→28, 싸이 35→43 등). 동결 스냅샷 코퍼스 파일은 저장소에 없지만, 병합이 팬덤별로 뒤에 덧붙는
구조이므로 **각 팬덤의 loyalty/spillover 앞쪽 n건(동결 점수 JSON의 n_loyalty_bullets/n_spillover_bullets)**을 취하면 동결 코퍼스를 근사할 수 있다.
'''),
        code('''
REPORT_TABLE15 = {  # (총언급, 검출수, 대표지역, 비중, 다양성) — 분석보고서 표 15
    "싸이": (35, 10, "강원", 0.20, 0.59), "이승철": (32, 9, "서울", 0.13, 0.53), "임영웅": (28, 12, "서울", 0.21, 0.71), "송가인": (27, 6, "전남", 0.74, 0.35),
    "박서진": (22, 11, "서울", 0.23, 0.65), "악동뮤지션": (21, 9, "서울", 0.33, 0.53), "김연자": (21, 8, "광주", 0.33, 0.47), "나훈아": (20, 8, "서울", 0.35, 0.47),
    "조용필": (20, 6, "서울", 0.30, 0.35), "리센느(RESCENE)": (19, 5, "경남", 0.58, 0.29), "이영지": (18, 10, "서울", 0.39, 0.59), "다이나믹듀오": (18, 6, "서울", 0.28, 0.35),
    "영탁": (18, 7, "서울", 0.33, 0.41), "지드래곤 (G-Dragon)": (17, 4, "서울", 0.47, 0.23), "BTS": (17, 5, "서울", 0.47, 0.29), "god": (16, 4, "서울", 0.50, 0.23),
    "잭스키스": (15, 5, "부산", 0.53, 0.29), "로이킴": (15, 6, "서울", 0.53, 0.35), "김호중": (14, 6, "경북", 0.43, 0.35), "엄정화": (14, 3, "부산", 0.36, 0.18),
}
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")
fz = {d["fandom"]: d for d in frozen_scores}
frozen_approx_fandoms = []
for rec in fandoms:
    d = fz.get(rec["fandom"])
    if d is None:
        continue
    frozen_approx_fandoms.append({"fandom": rec["fandom"], "loyalty": rec["loyalty"][:d["n_loyalty_bullets"]], "spillover": rec["spillover"][:d["n_spillover_bullets"]]})
frozen_approx = region_index(frozen_approx_fandoms)
print(f"동결 근사 코퍼스: {sum(v['total_group_bullets'] for v in frozen_approx.values())}건 / {len(frozen_approx)}팬덤 (동결 점수 JSON activity 합 {sum(d['activity'] for d in frozen_scores)})")

rows = []; n_match_frozen = n_match_final = 0
for name, (tot, hit, reg, share, div) in REPORT_TABLE15.items():
    fa, fi = frozen_approx[name], final[name]
    m_f = fa["total_region_mentions"] == tot and fa["n_regions_hit"] == hit and fa["primary_region"] == reg and abs(fa["primary_region_share"] - share) < 0.011
    m_l = fi["total_region_mentions"] == tot and fi["n_regions_hit"] == hit and fi["primary_region"] == reg and abs(fi["primary_region_share"] - share) < 0.011
    n_match_frozen += m_f; n_match_final += m_l
    rows.append({"팬덤": name, "표15 총언급/검출/대표(비중)": f"{tot}/{hit}/{reg}({share:.0%})",
                 "동결근사": f"{fa['total_region_mentions']}/{fa['n_regions_hit']}/{fa['primary_region']}({fa['primary_region_share']:.0%})", "동결근사 일치": m_f,
                 "최종 10,020": f"{fi['total_region_mentions']}/{fi['n_regions_hit']}/{fi['primary_region']}({fi['primary_region_share']:.0%})", "최종 일치": m_l})
print(f"표 15 20행 중 정확 일치 — 동결 근사: {n_match_frozen}/20, 최종 10,020건: {n_match_final}/20")
print("-> 표 15는 동결 스냅샷 값이고, 나머지 3행(이영지·영탁·로이킴)은 근사 코퍼스가 앞쪽 n건 가정과 1~2건 어긋난 결과다(라운드 스왑·중복 제거 흔적).")
for name in ["BTS", "임영웅", "리센느(RESCENE)"]:
    d = final[name]
    print(f"최종 {name}: 총언급 {d['total_region_mentions']}, 검출 {d['n_regions_hit']}, 대표 {d['primary_region']}({d['primary_region_share']:.0%}), 다양성 {d['region_diversity']}")
top_div = dr_df.sort_values(["지역다양성", "총지역언급"], ascending=[False, False]).iloc[0]
print(f"최종 지역다양성 전체 1위: {top_div['팬덤']} ({top_div['지역다양성']})  (보고서: 임영웅 0.71 전체 1위)")
pd.DataFrame(rows)
'''),
        md("## 4. r22 → 최종: 상위 팬덤의 변화"),
        code('''
cmp = pd.DataFrame([{"팬덤": n, "r22 총언급": r22_drp[n]["total_region_mentions"], "최종 총언급": final[n]["total_region_mentions"],
                     "r22 검출지역": r22_drp[n]["n_regions_hit"], "최종 검출지역": final[n]["n_regions_hit"]}
                    for n in final if n in r22_drp]).sort_values("최종 총언급", ascending=False).reset_index(drop=True)
cmp["증가"] = cmp["최종 총언급"] - cmp["r22 총언급"]
print("r22 로스터에 없는 최종 팬덤:", [n for n in final if n not in r22_drp], "| 최종에 없는 r22 팬덤:", [n for n in r22_drp if n not in final])
cmp.head(15)
'''),
        md("## 5. 지역별 전국 분포"),
        code('''
region_totals = {r: int(dr_df[r].sum()) for r in REGIONS}
grand = sum(region_totals.values())
dist = pd.DataFrame([{"지역": r, "언급불릿수": c, "비중": round(c / grand, 4), "언급 팬덤 수": int((dr_df[r] > 0).sum())}
                     for r, c in sorted(region_totals.items(), key=lambda x: -x[1])])
print(f"전체 지역 언급 총계: {grand}건")
dist
'''),
        md('''
## 6. 한계

1. 원본 라이브 JSON이 없으므로 이 산출물은 **r22 규칙의 재적용본**이다. 키워드 사전은 r22 원본을 셀 단위로 재현하도록 역추적한 것이고, 3절에서 보고서 표 15(동결 스냅샷 시점)가 20행 중 17행 그대로 재현되므로 최종 파이프라인도 같은 규칙을 썼다고 판단한다.
2. 보고서 표 15·KEY_FINDINGS의 국내 지역 값은 **동결 스냅샷(7,350건)** 기준이며, 이 폴더의 `domestic_regional_index_v7.json`은 **최종 10,020건** 기준이라 상위 팬덤 수치가 더 크다(4절 비교표).
3. 부분 문자열 매칭이라 "광주"(경기 광주시 vs 광주광역시), "고성"(강원/경남) 같은 동음 지명은 구분하지 않는다(원문서와 동일한 한계). 고양·여주·완주·동해·예산처럼 일상어와 충돌하는 지명은 r22 원본이 의도적으로 제외했음이 역추적에서 확인됐다.
4. 언급 0건은 "이 코퍼스에서 검출되지 않았다"는 뜻이지 지역 연고가 없다는 뜻이 아니다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 5. 세계 언어 지수
# ---------------------------------------------------------------------------------------------
def nb_worldwide():
    cells = [
        md('''
# 세계 언어 지수(Worldwide Language Index) — 최종 코퍼스 10,020건 재현 노트북

r22 노트북은 10개 언어·`ln(10)` 분모로 `fandom_scores_v6.json`(r22)의 language_coverage를 재검증했다. 최종 데이터는 14개 언어다.

| 입력 | 내용 |
|---|---|
| `fandom_scores_live_reference_v7.json` | 라이브 10,020건 coverage_detail(14개 언어 language_counts, 분모 ln(14)) |
| `worldwide_language_pilot_live_reference_v7.json` / `worldwide_language_index_v7.csv` | 팬덤별 세계 언어 지수 원본과 CSV |
| `language_domain_summary_v7.json` | 14개 언어별 근거 건수·도메인 수(코퍼스 합계) |
| `fandom_scores_v6.json` | 동결 스냅샷 7,350건(13개 언어, 아랍어 없음, 분모 ln(13)) — 비교용 |
| `archive/.../fandom_scores_v6.json` | r22 5,612건(10개 언어, ln(10)) — 비교용 |
'''),
        code(PRE + '''
live_scores = load_json(DATA_DIR / "fandom_scores_live_reference_v7.json")
wl = load_json(DATA_DIR / "worldwide_language_pilot_live_reference_v7.json")
wl_csv = pd.read_csv(DATA_DIR / "worldwide_language_index_v7.csv", encoding="utf-8-sig")
lang_dom = load_json(DATA_DIR / "language_domain_summary_v7.json")
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")
r22_scores = load_json(ARCHIVE_DIR / "fandom_scores_v6.json")

ALL_LANGS = ["ko", "en", "ja", "zh", "es", "fr", "th", "id", "vi", "ru", "tl", "pt", "tr", "ar"]
LANG_LABEL = {"ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어", "es": "스페인어", "fr": "프랑스어", "th": "태국어",
              "id": "인도네시아어", "vi": "베트남어", "ru": "러시아어", "tl": "필리핀어", "pt": "포르투갈어", "tr": "튀르키예어", "ar": "아랍어"}
langs_present = set()
for rec in live_scores:
    langs_present.update(rec["coverage_detail"]["language_counts"].keys())
print("라이브 점수에 등장하는 언어:", sorted(langs_present), "| 14개 스키마 안에 있음:", langs_present <= set(ALL_LANGS), "| 개수:", len(langs_present))
print("worldwide JSON 팬덤 수:", len(wl), "| CSV 행:", len(wl_csv), "| language_domain_summary 언어 수:", len(lang_dom))
'''),
        md("## 1. LanguageCoverage 공식 재검증 — 세 시점 각각의 분모(ln(14) / ln(13) / ln(10))"),
        code('''
def shannon_diversity(counts, denom_langs):
    total = sum(counts.values())
    if total == 0 or denom_langs <= 1:
        return 0.0
    ent = -sum((c / total) * math.log(c / total) for c in counts.values() if c > 0)
    return ent / math.log(denom_langs)


def verify(scores, denom, label):
    sum_mis = cov_mis = 0
    for rec in scores:
        cd = rec["coverage_detail"]
        if sum(cd["language_counts"].values()) != cd["n_evidence"]: sum_mis += 1
        if abs(shannon_diversity(cd["language_counts"], denom) - cd["language_coverage"]) > 0.001: cov_mis += 1
    langs = set(); [langs.update(r["coverage_detail"]["language_counts"]) for r in scores]
    print(f"[{label}] 언어 수 {len(langs)}, 분모 ln({denom}): 언어합!=n_evidence {sum_mis}/{len(scores)}, language_coverage 불일치 {cov_mis}/{len(scores)}")

verify(live_scores, 14, "라이브 10,020건")
verify(frozen_scores, 13, "동결 7,350건")
verify(r22_scores, 10, "r22 5,612건")
print("(다른 분모를 쓰면 100/100 불일치 — verify_v7_final_consistency.py [V]·[Z]와 동일한 결론)")
'''),
        md("## 2. 세계 언어 지수 재계산 — 원본 스크립트 컬럼 스키마(14개 언어) 적용, JSON·CSV와 대조"),
        code('''
FOREIGN = [l for l in ALL_LANGS if l != "ko"]
rows = []; mism = {"n_languages_hit": 0, "language_diversity": 0, "foreign_bullets": 0, "foreign_ratio": 0,
                   "n_foreign_languages_hit": 0, "foreign_diversity": 0, "primary_foreign_language": 0, "primary_foreign_share": 0}
for rec in live_scores:
    cd = rec["coverage_detail"]
    counts = {l: cd["language_counts"].get(l, 0) for l in ALL_LANGS}
    total = sum(counts.values()); fc = {l: counts[l] for l in FOREIGN}; ft = sum(fc.values())
    prim = max(fc, key=fc.get) if ft else None
    calc = {"n_languages_hit": sum(1 for c in counts.values() if c > 0), "language_diversity": round(shannon_diversity(counts, 14), 3),
            "foreign_bullets": ft, "foreign_ratio": round(ft / total, 3) if total else 0.0,
            "n_foreign_languages_hit": sum(1 for c in fc.values() if c > 0), "foreign_diversity": round(shannon_diversity(fc, 13), 3),
            "primary_foreign_language": prim, "primary_foreign_share": round(fc[prim] / ft, 3) if ft else 0.0}
    orig = wl[rec["fandom"]]
    for k, v in calc.items():
        o = orig[k]
        if (isinstance(v, float) and abs(v - o) > 0.0015) or (not isinstance(v, float) and v != o):
            mism[k] += 1
    row = {"팬덤": rec["fandom"], "근거문장수": total, "검출언어수": calc["n_languages_hit"], "언어다양성": calc["language_diversity"],
           "해외근거문장수": ft, "해외비중": calc["foreign_ratio"], "검출해외언어수": calc["n_foreign_languages_hit"],
           "해외언어다양성": calc["foreign_diversity"], "대표해외언어": LANG_LABEL.get(prim, ""), "대표해외언어비중": calc["primary_foreign_share"]}
    row.update({LANG_LABEL[l]: counts[l] for l in ALL_LANGS}); rows.append(row)
pilot_df = pd.DataFrame(rows).sort_values(["해외근거문장수", "팬덤"], ascending=[False, True]).reset_index(drop=True)
print("원본 JSON 대비 필드별 불일치 팬덤 수:", mism)
merged = pilot_df.merge(wl_csv, on="팬덤", suffixes=("", "_csv"))
csv_mis = {c: int((merged[c] != merged[c + "_csv"]).sum()) for c in ["근거문장수", "해외근거문장수", "검출언어수", "검출해외언어수"]}
print("CSV(worldwide_language_index_v7.csv) 대비 정수 컬럼 불일치:", csv_mis)
bts = pilot_df[pilot_df["팬덤"] == "BTS"].iloc[0]
print(f"BTS: 해외 {int(bts['해외근거문장수'])}건 ({bts['해외비중']:.1%}), 해외언어다양성 {bts['해외언어다양성']} (KEY_FINDINGS: 135건 60%, 0.66)")
pilot_df.index += 1
pilot_df.head(15)
'''),
        md("## 3. 코퍼스 전체 언어 구성 — 세 시점 비교 + language_domain_summary 대조"),
        code('''
def totals(scores):
    t = {}
    for rec in scores:
        for l, c in rec["coverage_detail"]["language_counts"].items():
            t[l] = t.get(l, 0) + c
    return t
live_t, frozen_t, r22_t = totals(live_scores), totals(frozen_scores), totals(r22_scores)
ld = {r["lang_code"]: r for r in lang_dom}
comp = pd.DataFrame([{"언어": LANG_LABEL[l], "code": l, "라이브 10,020": live_t.get(l, 0), "language_domain_summary": ld[l]["total_bullets"] if l in ld else None,
                      "도메인 수(라이브)": ld[l]["total_domains"] if l in ld else None, "동결 7,350": frozen_t.get(l, 0), "r22 5,612": r22_t.get(l, 0)}
                     for l in ALL_LANGS]).sort_values("라이브 10,020", ascending=False).reset_index(drop=True)
comp["라이브 비중"] = (comp["라이브 10,020"] / comp["라이브 10,020"].sum()).round(4)
print("합계: 라이브", comp["라이브 10,020"].sum(), "| summary", comp["language_domain_summary"].sum(), "| 동결", comp["동결 7,350"].sum(), "| r22", comp["r22 5,612"].sum())
print("라이브 language_counts 합 == language_domain_summary total_bullets (언어별 전부):", all(comp["라이브 10,020"] == comp["language_domain_summary"]))
comp
'''),
        md('''
## 4. 한계

1. 언어는 출처 도메인 기준(`language_of()`)이며 본문 언어가 아니다 — 한국 매체의 영문 기사, 해외 매체의 한국어판 등은 도메인 언어로 분류된다(TOKENIZER 문서 참고).
2. 14개 언어 이외의 언어(예: 독일어·이탈리아어 매체)는 도메인 규칙에 없으면 기본값으로 흡수되므로 "검출언어수"는 하한이다.
3. 세 시점(r22 10개·동결 13개·라이브 14개)은 분모가 달라 language_coverage 절대치는 시점 간 비교할 수 없다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 6. 그룹-멤버 계층 지수 (Member Mention Index / MCI)
# ---------------------------------------------------------------------------------------------
def nb_group_member():
    cells = [
        md('''
# 그룹–멤버 계층 지수(Member Mention Index · MCI) — 최종 코퍼스 10,020건 검증 노트북

r22 노트북(`archive/v6_r22_era/Group_Member Pilot/group_member_fpu_pilot.ipynb`)은 23개 그룹 파일럿을 다뤘다. 최종 데이터는

| 입력 | 내용 |
|---|---|
| `member_mention_index_v7.json` | 45개 그룹, 최종 코퍼스 10,020건 기준 멤버명 언급 수·Impact Share·MCI |
| `member_mention_pilot_v6.json` | 동결 시점 23개 그룹 파일럿(7,350건 기준) — 비교용 |
| `member_pilot_mci_correlation_v7.json` | MCI ↔ 성과지표 상관·회귀 분석(v7-55 시점 8,981건 MCI × 동결 outcome) |
| `fandom_scores_live_reference_v7.json`, `fandom_scores_v6.json` | Coverage Index 가중식 검증(라이브·동결) |
'''),
        code(PRE + '''
mm = load_json(DATA_DIR / "member_mention_index_v7.json")
pilot23 = load_json(DATA_DIR / "member_mention_pilot_v6.json")
mci_corr = load_json(DATA_DIR / "member_pilot_mci_correlation_v7.json")
live_scores = load_json(DATA_DIR / "fandom_scores_live_reference_v7.json")
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
per_fandom_corpus = {f["fandom"]: len(f.get("loyalty", [])) + len(f.get("spillover", [])) for f in fandoms}
print(f"member_mention_index_v7.json: {len(mm)}개 그룹 | pilot v6: {len(pilot23)}개 | 상관분석 그룹 수: {mci_corr['n_groups']}")
print("index 그룹 == 상관분석 그룹:", set(mm) == set(mci_corr["groups"]), "| 23개 파일럿 ⊂ 45개 index:", set(pilot23) <= set(mm))
'''),
        md("## 1. Coverage Index 가중식 검증 (0.30 언어 + 0.25 시장 + 0.20 출처유형 + 0.15 시간 + 0.10 개체) — 라이브·동결"),
        code('''
DOC_WEIGHTS = {"language": 0.30, "market": 0.25, "source_type": 0.20, "time": 0.15, "entity": 0.10}
def check_cov(scores, label):
    w_mis = re_mis = 0
    for rec in scores:
        cd = rec["coverage_detail"]
        if cd["weights"] != DOC_WEIGHTS: w_mis += 1
        rec_v = sum(cd["weights"][k] * cd[f"{k}_coverage"] for k in DOC_WEIGHTS)
        if abs(rec_v - rec["coverage_index"]) > 0.001: re_mis += 1
    print(f"[{label}] 가중치 != 문서값: {w_mis}/{len(scores)} | coverage_index 재계산 불일치: {re_mis}/{len(scores)}")
check_cov(live_scores, "라이브 10,020건"); check_cov(frozen_scores, "동결 7,350건")
'''),
        md("## 2. Member Impact Share / MCI — 45개 그룹 재계산"),
        code('''
rows = []; mism = 0; tgb_mis = 0
for g, rec in mm.items():
    counts = rec["member_mention_counts"]; total = sum(counts.values())
    share = {m: (c / total if total else 0.0) for m, c in counts.items()}
    mci = sum(s ** 2 for s in share.values())
    if max(abs(share[m] - rec["member_impact_share_index"][m]) for m in counts) > 0.0015 or abs(mci - rec["mci_index"]) > 0.0015: mism += 1  # 소수 3자리 반올림 허용
    if total != rec["total_member_mentions"]: mism += 1
    if per_fandom_corpus.get(g) != rec["total_group_bullets"]: tgb_mis += 1
    rows.append({"group": g, "n_members": len(counts), "total_group_bullets": rec["total_group_bullets"], "total_mentions": total,
                 "mci_index": rec["mci_index"], "mci_recomputed": round(mci, 4), "mci_floor(1/n)": round(1 / len(counts), 4),
                 "mci_excess": round(rec["mci_index"] - 1 / len(counts), 4),
                 "top_member": max(counts, key=counts.get) if total else None, "top_member_share": round(max(share.values()), 4) if total else 0.0})
member_df = pd.DataFrame(rows).sort_values("mci_index", ascending=False).reset_index(drop=True)
print(f"Impact Share/MCI/total_member_mentions 재계산 불일치(반올림 0.0015 초과) 그룹: {mism} / {len(mm)} | total_group_bullets != 코퍼스: {tgb_mis} / {len(mm)}")
print(f"멤버 언급 총합: {member_df['total_mentions'].sum()}건 | MCI 평균 {member_df['mci_index'].mean():.4f}, 최소 {member_df['mci_index'].min()} ({member_df.loc[member_df['mci_index'].idxmin(), 'group']}), 최대 {member_df['mci_index'].max()} ({member_df.loc[member_df['mci_index'].idxmax(), 'group']})")
print("상관분석 JSON 기술통계(v7-55 시점):", mci_corr["mci_descriptives"])
member_df
'''),
        md("### 2-1. 빅뱅(BIGBANG) — 전략문서가 직접 예시로 든 그룹 (r22: 탑 0건 → 최종: 탑 1건)"),
        code('''
bb = mm["빅뱅"]; bb23 = pilot23["빅뱅"]
bb_detail = pd.DataFrame([{"member": m, "mentions(최종)": bb["member_mention_counts"][m], "impact_share(최종)": bb["member_impact_share_index"][m],
                           "mentions(동결 파일럿)": bb23["member_mention_counts"].get(m), "impact_share(동결 파일럿)": bb23["member_impact_share_pilot"].get(m)}
                          for m in bb["member_mention_counts"]]).sort_values("impact_share(최종)", ascending=False).reset_index(drop=True)
print(f"빅뱅 total_group_bullets {bb['total_group_bullets']} (동결 {bb23['total_group_bullets']}) | 멤버 언급 {bb['total_member_mentions']} (동결 {bb23['total_member_mentions']}) | MCI {bb['mci_index']} (동결 {bb23['mci_pilot']})")
print("문서 예시 4명(지드래곤/태양/대성/탑)과 일치:", set(bb["member_mention_counts"]) == {"지드래곤", "태양", "대성", "탑"})
bb_detail
'''),
        md("## 3. 동결 23개 파일럿 → 최종 45개 지수: 같은 그룹의 변화"),
        code('''
chg = pd.DataFrame([{"group": g, "bullets(동결)": pilot23[g]["total_group_bullets"], "bullets(최종)": mm[g]["total_group_bullets"],
                     "mentions(동결)": pilot23[g]["total_member_mentions"], "mentions(최종)": mm[g]["total_member_mentions"],
                     "MCI(동결)": pilot23[g]["mci_pilot"], "MCI(최종)": mm[g]["mci_index"]} for g in pilot23])
chg["ΔMCI"] = (chg["MCI(최종)"] - chg["MCI(동결)"]).round(3)
print("최종에서 새로 추가된 22개 그룹:", sorted(set(mm) - set(pilot23)))
print(f"23개 그룹 MCI 변화: 평균 Δ {chg['ΔMCI'].mean():+.4f}, |Δ|>0.05 인 그룹 {(chg['ΔMCI'].abs() > 0.05).sum()}개")
chg.sort_values("ΔMCI", key=lambda s: s.abs(), ascending=False)
'''),
        md("## 4. MCI ↔ 멤버 수·성과지표 상관 — 상관분석 JSON 값의 재현 (JSON은 v7-55 시점 MCI, 여기서는 최종 MCI로 재계산해 차이를 본다)"),
        code('''
from scipy import stats
frozen_by = {d["fandom"]: d for d in frozen_scores}
sub = member_df[member_df["group"].isin(frozen_by)].copy()
for col in ["loyalty_score", "spillover_score", "coverage_index", "factor_diversity"]:
    sub[col] = sub["group"].map({g: frozen_by[g][col] for g in frozen_by})
r_n, p_n = stats.pearsonr(sub["mci_index"], sub["n_members"])
print(f"n={len(sub)} (동결 로스터에 있는 그룹) | r(MCI, 멤버 수) = {r_n:.4f} (p={p_n:.2e})  ← JSON: {mci_corr['mci_vs_member_count']['pearson_r']}")
rows = []
for col in ["loyalty_score", "spillover_score", "coverage_index", "factor_diversity"]:
    r_raw, p_raw = stats.pearsonr(sub["mci_index"], sub[col]); r_ex, p_ex = stats.pearsonr(sub["mci_excess"], sub[col])
    rows.append({"outcome(동결)": col, "r(MCI 최종)": round(r_raw, 4), "p": round(p_raw, 4), "JSON r(MCI v7-55)": mci_corr["correlations_mci_raw"][col]["pearson_r"],
                 "r(MCI_excess 최종)": round(r_ex, 4), "JSON r(MCI_excess)": mci_corr["correlations_mci_excess"][col]["pearson_r"]})
print("verdict(JSON):", mci_corr["verdict"]["summary_ko"][:200], "...")
print("caveat:", mci_corr["caveat_temporal_mismatch"][:150], "...")
pd.DataFrame(rows)
'''),
        md("## 5. MCI 해석 구간(예시 임계값 0.30/0.45 — 문서에 정확한 컷오프 없음) + FPU JSON 스키마 예시"),
        code('''
def classify_mci(m):
    return "분산형(Distributed)" if m < 0.30 else ("다극형(Multi-node)" if m < 0.45 else "스타중심형(Star-centered)")
member_df["mci_bucket_illustrative"] = member_df["mci_index"].apply(classify_mci)
print("⚠️ 버킷 경계값(0.30 / 0.45)은 예시 설정이다.")
print(member_df["mci_bucket_illustrative"].value_counts())

def build_fpu_example(group):
    rec = mm[group]; live = next((r for r in live_scores if r["fandom"] == group), None)
    return {"fpu_id": f"fpu_{group}", "schema_version": "v5.0_index",
            "group_core": {"name": group, "total_group_bullets": rec["total_group_bullets"], "coverage_index(live)": live["coverage_index"] if live else None},
            "unit_hierarchy": None, "unit_hierarchy_status": "not_yet_computable",
            "member_nodes": [{"node_type": "member", "name": m, "mentions": c, "impact_share": rec["member_impact_share_index"][m],
                              "activation_score": None, "activation_status": "not_yet_computable"} for m, c in rec["member_mention_counts"].items()],
            "mci_index": rec["mci_index"], "joint_evidence": None, "synergy_score": None, "dedup_applied": False, "source_note": rec["note"]}
print(json.dumps(build_fpu_example("빅뱅"), ensure_ascii=False, indent=2))
'''),
        md('''
## 6. 한계 — 아직 계산할 수 없는 것

1. 멤버별 독립 리서치가 아니라 그룹 단위 근거문장 안의 멤버명 언급 수 기반 텍스트마이닝 지수다(각 레코드 `note`).
2. Unit 계층(NCT 유닛 등), Joint Evidence 분리, Group–Member Synergy, Member Activation Score, 중복 집계 방지(event_id)는 여전히 미구현이다.
3. 상관분석 JSON은 v7-55 시점(8,981건) MCI × 동결 outcome이며, 4절의 최종 MCI 재계산값과는 소폭 다르다 — 결론(멤버 수 통제 시 설명력 소멸)은 유지되는지 4절 표로 확인한다.
4. MCI의 구조적 하한 1/n 때문에 멤버 수가 적은 그룹은 MCI가 높게 나온다 — `mci_excess`를 함께 본다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 7. Fan Impact Pathway (K→F→Persona) — 최종 산출물 적용
# ---------------------------------------------------------------------------------------------
def nb_fan_impact():
    cells = [
        md('''
# Fan Impact Pathway 온톨로지(K→F→Persona) — 최종 산출물 적용 노트북

r22 노트북(`archive/v6_r22_era/fan_impact_ontology/fan_impact_pathway_ontology.ipynb`)은 K=8/M=6/실루엣 0.154 스냅샷으로 전략문서를
시연했다. 최종 제출본은 **동결 스냅샷 v7-40(7,350건, K=10 → M=5, 실루엣 0.267)**에서 F1~F5·페르소나를 확정했고, 라이브 10,020건
재적합(K=8/M=5/0.046)은 실루엣 게이트를 통과하지 못해 loyalty/spillover 점수만 라이브로 갱신했다(README 3층 구조).

| 입력 | 내용 |
|---|---|
| `lda_v6_diagnostics_frozen_v7_40.json` | 동결 진단(K-grid, K=10 상위어, topic_to_factor, factor 라벨) |
| `factor_pathway_map_v7.json` | raw Factor 라벨 → F1~F5 영향경로 매핑 + QA |
| `topic_cards_v7.json` | K0~K9 Topic Card(상위어·대표 문장·대표 팬덤) |
| `fan_persona_v7.json` | 팬덤별 Top-2 Factor 페르소나(43/31/17/9) + Factor-specific Impact |
| `persona_decision_space_v7.json` | PCA(분산비)·덴드로그램(컷 높이) |
| `fandom_scores_v6.json` | 동결 점수(factor_share 5개) |
| `lda_v6_diagnostics_live_reference_v7.json`, `lda_excluded_bullets_v7.json` | 라이브 재적합 진단(게이트 미통과)과 LDA 제외 불릿 2건 |
'''),
        code(PRE + '''
diag = load_json(DATA_DIR / "lda_v6_diagnostics_frozen_v7_40.json")
diag_live = load_json(DATA_DIR / "lda_v6_diagnostics_live_reference_v7.json")
pathway = load_json(DATA_DIR / "factor_pathway_map_v7.json")
cards = load_json(DATA_DIR / "topic_cards_v7.json")
persona = load_json(DATA_DIR / "fan_persona_v7.json")
space = load_json(DATA_DIR / "persona_decision_space_v7.json")
frozen_scores = load_json(DATA_DIR / "fandom_scores_v6.json")
excluded = load_json(DATA_DIR / "lda_excluded_bullets_v7.json")
scores_by = {d["fandom"]: d for d in frozen_scores}
print(f"동결 진단: K={diag['selected_k']}, M={diag['selected_m_meta_factors']}, silhouette={diag['meta_factor_silhouette']} | 근거문장 합 {sum(d['activity'] for d in frozen_scores)}")
print(f"라이브 재적합: K={diag_live['selected_k']}, M={diag_live['selected_m_meta_factors']}, silhouette={diag_live['meta_factor_silhouette']} (게이트 미통과)")
print(f"LDA 문서 수: {excluded['lda_document_count']} = {excluded['total_bullets']} - 제외 {excluded['excluded_count']}건(3토큰 미만)")
'''),
        md("## 1. 온톨로지 정의 — F Impact Pathway(전략보고서 3.1절) ↔ 최종 매핑 파일"),
        code('''
F_IMPACT_PATHWAY = pd.DataFrame([
    {"F": "F1", "명칭": "팬덤결속 경로", "경로": "Fan → Fan", "대표신호": "팬클럽·기부·응원"},
    {"F": "F2", "명칭": "직접소비 경로", "경로": "Fan → Market", "대표신호": "앨범·티켓·굿즈·판매"},
    {"F": "F3", "명칭": "현장경제 경로", "경로": "Fan → Event → Local", "대표신호": "콘서트·투어·관객·숙박·교통"},
    {"F": "F4", "명칭": "산업전이 경로", "경로": "Fan → Brand/Industry", "대표신호": "광고·브랜드·앰버서더"},
    {"F": "F5", "명칭": "대중·글로벌 확산 경로", "경로": "Fan → Media → Mass/Global", "대표신호": "차트·방송·유튜브·해외활동"},
])
map_df = pd.DataFrame([{"raw factor 라벨(동결 LDA)": k, "F": v["f_code"], "명칭": v["f_name"], "경로": v["f_path"]} for k, v in pathway["mapping"].items()]).sort_values("F")
print("QA:", pathway["qa"])
print("전략문서 F명칭 == 매핑 파일 F명칭:", dict(zip(F_IMPACT_PATHWAY["F"], F_IMPACT_PATHWAY["명칭"])) == dict(zip(map_df["F"], map_df["명칭"])))
map_df.reset_index(drop=True)
'''),
        md("## 2. K→F 매핑 현황 — 동결 진단(K=10) 그대로"),
        code('''
label_to_f = {k: v["f_code"] for k, v in pathway["mapping"].items()}
rows = []
for t, fid in diag["topic_to_factor"].items():
    lab = diag["factor_labels"][str(fid)]
    rows.append({"topic_id": f"K{int(t)}", "topic_keywords": "·".join(diag["topics_top_words"][t][:6]), "raw factor": lab, "F": label_to_f[lab]})
mapping_df = pd.DataFrame(rows).sort_values("topic_id").reset_index(drop=True)
n_topics, n_mapped = len(diag["topics_top_words"]), len(diag["topic_to_factor"])
print(f"QA: 매핑률 = {n_mapped}/{n_topics} ({n_mapped / n_topics:.0%}), 미매핑 Topic = {n_topics - n_mapped}개")
print("F별 구성 토픽 수:", mapping_df["F"].value_counts().sort_index().to_dict())
print("Topic Card 이름:", {c["topic_id"]: c["topic_name"] for c in cards})
print("덴드로그램 컷 높이:", round(space["dendro"]["cut_height"], 4), "| PCA 분산비:", [round(v, 3) for v in space["pca"]["var_ratio"]])
mapping_df
'''),
        md("## 3. Topic Card — 최종 `topic_cards_v7.json` 포맷 확인 (문장이 가장 많이 배정된 카드 1개 출력)"),
        code('''
def card_summary(c):
    return {"topic_id": c["topic_id"], "topic_name": c["topic_name"], "top_keywords": c["top_keywords"][:10],
            "connected": (c.get("connected_factor_label"), c.get("connected_f_pathway")),
            "대표_근거문장(최대3)": [b["text"][:80] + "…" for b in c["representative_bullets"][:3]],
            "대표_팬덤_Top5": {f["fandom"]: f["avg_topic_weight"] for f in c["representative_fandoms_top5"]}}
import pprint
print("카드 수:", len(cards), "| 카드별 대표 팬덤 수:", {c["topic_id"]: len(c["representative_fandoms_top5"]) for c in cards})
pprint.pprint(card_summary(cards[0]), width=140)
'''),
        md("## 4. Factor-specific Impact (전략문서 7절: share × loyalty / share × spillover) — `fan_persona_v7.json` 값 재현"),
        code('''
mism_l = mism_s = 0; rows = []
for p in persona["fandoms"]:
    d = scores_by[p["fandom"]]
    for lab, share in d["factor_share"].items():
        f = label_to_f[lab]
        fl, fs = round(share * d["loyalty_score"], 4), round(share * d["spillover_score"], 4)
        if abs(fl - p["factor_specific_loyalty"][f]) > 0.0015: mism_l += 1
        if abs(fs - p["factor_specific_spillover"][f]) > 0.0015: mism_s += 1
        rows.append({"fandom": p["fandom"], "F": f, "factor_share": round(share, 4), "factor_specific_loyalty": fl, "factor_specific_spillover": fs})
fi = pd.DataFrame(rows)
print(f"factor_specific_loyalty 불일치 (팬덤×F 셀): {mism_l}/{len(fi)} | factor_specific_spillover 불일치: {mism_s}/{len(fi)}")
for name in ''' + HIGHLIGHT + ''':
    d = scores_by[name]; p = next(x for x in persona["fandoms"] if x["fandom"] == name)
    print(f"\\n=== {name} === loyalty={d['loyalty_score']}, spillover={d['spillover_score']}, dominant={d['dominant_factor']} → persona {p['persona']} "
          f"(Top-2: {p['top2_factors'][0]['f_code']} {p['top2_factors'][0]['share']}, {p['top2_factors'][1]['f_code']} {p['top2_factors'][1]['share']})")
    print(fi[fi["fandom"] == name].sort_values("factor_share", ascending=False).head(3).to_string(index=False))
'''),
        md("## 5. Fan Persona(Top-2 Factor 조합) — persona_counts 43/31/17/9 재현"),
        code('''
table = persona["persona_table_definition"]
combo_counts = {}; name_mis = 0
for p in persona["fandoms"]:
    d = scores_by[p["fandom"]]
    top2 = sorted(sorted(d["factor_share"].items(), key=lambda kv: -kv[1])[:2], key=lambda kv: label_to_f[kv[0]])
    key = "|".join(label_to_f[k] for k, _ in top2)
    if table[key] != p["persona"]: name_mis += 1
    combo_counts[table[key]] = combo_counts.get(table[key], 0) + 1
print(f"페르소나 명칭 재계산 불일치: {name_mis}/{len(persona['fandoms'])}")
print("재계산 persona_counts:", dict(sorted(combo_counts.items(), key=lambda x: -x[1])), "| JSON:", persona["persona_counts"], "| PCA JSON:", space["pca"]["persona_counts"])
print(f"이론상 조합 수 (M=5, 2개 조합) = {5 * 4 // 2}개, 실제 실현 = {len(combo_counts)}개")
pd.DataFrame([{"top2_factor_combo": k, "persona": v, "n_fandoms": combo_counts.get(v, 0)} for k, v in table.items()]).sort_values("n_fandoms", ascending=False).reset_index(drop=True)
'''),
        md("## 6. 실루엣 게이트 — 라이브 10,020건 재적합이 동결 스냅샷을 대체하지 못한 이유 (진단 대조)"),
        code('''
grid = pd.DataFrame(diag["k_grid"]).assign(snapshot="동결 7,350").merge(pd.DataFrame(diag_live["k_grid"]).assign(snapshot="라이브 10,020"), how="outer")
print("라이브 K→factor:", diag_live["topic_to_factor"], "| 라이브 factor 라벨:", diag_live["factor_labels"])
print(f"게이트: 동결 실루엣 {diag['meta_factor_silhouette']} vs 라이브 {diag_live['meta_factor_silhouette']} → 라이브 재적합은 보고서 본문 지표로 채택되지 않음.")
grid.pivot(index="k", columns="snapshot", values=["perplexity", "coherence", "diversity", "stability", "composite_rank_sum"])
'''),
        md('''
## 7. QA 요약 (전략문서 11절 체크리스트)

| 항목 | 결과 |
|---|---|
| K→F 매핑률 | 10/10 (미매핑 0) — `factor_pathway_map_v7.json` qa |
| Factor-specific Impact 재현 | 4절: 불일치 0셀이면 `fan_persona_v7.json` 값이 동결 점수에서 그대로 재계산됨 |
| 페르소나 분포 | 5절: 글로벌투어형 43 · 현장상업형 31 · 원정소비형 17 · 집단동원형 9 (10개 조합 중 4개 실현) |
| 실루엣 게이트 | 동결 0.267 채택, 라이브 0.046 기각 |

## 최종 노트 — r22 노트북과 다른 지점

- r22: K=8/M=6/0.154, "브랜드·상업형"·"미디어노출형" 두 라벨 모두 존재. 최종 동결: K=10/M=5/0.267, F4 산업전이 경로에 raw 라벨 "미디어노출형(방송·조회수)"이 매핑됨(`factor_pathway_map_v7.json` rationale 참고) — 라벨 자동 부여 규칙의 결과이며 광고 신호는 별도 키워드 지수(`ad_commercial_index_v7.json`)로 보완됐다.
- 라이브 재적합은 K-grid 승자가 K=8로 바뀌고 실루엣이 0.046으로 떨어져 게이트를 넘지 못했다 — 최종 보고서는 loyalty/spillover만 라이브로 쓴다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
# 8. 토크나이저 문자권 라우팅
# ---------------------------------------------------------------------------------------------
def nb_tokenizer_routing():
    cells = [
        md('''
# Tokenizer Script-Routing — 최종 코퍼스 10,020건 문자권 분기 검증 노트북

r22 노트북(`archive/v6_r22_era/TOKENIZER_WORDCLOUD_REPORT/tokenizer_script_routing_pilot.ipynb`)은 5,612건에 문자 범위 분기를 적용해
보고서 표 2(10,020건)와 "방향성만" 비교했다. 이제 같은 코퍼스(10,020건)와 원본 토크나이저 실행 결과(`wordcloud_by_language_v7.json`)가
있으므로 절대 수치로 대조한다.

- 원본(`wordcloud_by_language_v7.json`)의 버킷 집계는 **한 불릿이 여러 버킷에 들어갈 수 있는 다중 라벨**("해당 버킷 토큰이 1개 이상 있는 불릿 수")이다.
- 이 노트북은 ① 단일 버킷 배정(r22 노트북 방식)과 ② 다중 라벨 재현 두 가지를 모두 계산한다.
'''),
        code(PRE + '''
import re
fandoms = load_json(DATA_DIR / "fandoms_v3_100.json")
wc = load_json(DATA_DIR / "wordcloud_by_language_v7.json")
bullets_df = flatten_bullets(fandoms)
print(f"평탄화된 불릿 수: {len(bullets_df)} | wordcloud JSON total_bullets: {wc['total_bullets']} | total_tokens: {wc['total_tokens']}")
print("원본 버킷:", [(b["bucket"], b["n_bullets_with_any_token"]) for b in wc["buckets"]])
'''),
        md("## 1. 문자 범위 기반 스크립트 분기 — 단일 버킷 배정 (r22 노트북과 동일 규칙)"),
        code('''
RE_HANGUL = re.compile(r"[가-힣]")
RE_KANA = re.compile(r"[぀-ゟ゠-ヿ]")
RE_HANZI = re.compile(r"[一-鿿]")
RE_THAI = re.compile(r"[฀-๿]")
RE_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
RE_VIET = re.compile(r"[đơưĐƠƯ]|[Ḁ-ỿ]")
RE_LATIN_EXT = re.compile(r"[À-ɏ]")
RE_ASCII_LATIN = re.compile(r"[A-Za-z]")

BK_KO, BK_EN, BK_OTHER, BK_RU, BK_VI, BK_JA, BK_ZH, BK_TH = [b["bucket"] for b in wc["buckets"]]

def classify_single(text):
    if RE_KANA.search(text): return BK_JA
    if RE_HANZI.search(text): return BK_ZH
    if RE_THAI.search(text): return BK_TH
    if RE_HANGUL.search(text): return BK_KO
    if RE_CYRILLIC.search(text): return BK_RU
    if RE_VIET.search(text): return BK_VI
    if RE_LATIN_EXT.search(text): return BK_OTHER
    if RE_ASCII_LATIN.search(text): return BK_EN
    return "기타/미분류"

bullets_df["script_bucket"] = bullets_df["text"].apply(classify_single)
bullets_df["script_bucket"].value_counts()
'''),
        md("## 2. 다중 라벨 재현 — 원본 `tokenize()` 분기(가나→ja, 한자(가나 없음)→zh, 태국문자→th) + 일반 경로 토큰의 사후 재분류"),
        code('''
WORD_RE = re.compile(r"[^\\s\\.,;:!?\\"'“”‘’()\\[\\]{}<>·•\\-–—/\\\\|~`^*+=_@#$%&《》「」『』]+")

RE_CJK_RUN = re.compile(r"[一-鿿]{2,}")   # jieba 토큰은 2자 이상만 남긴다고 보고 1자 한자만 있는 불릿은 중국어 토큰 없음으로 처리

def buckets_of(text):
    hit = set()
    if RE_KANA.search(text): hit.add(BK_JA)
    elif RE_CJK_RUN.search(text): hit.add(BK_ZH)
    if RE_THAI.search(text): hit.add(BK_TH)
    for tok in WORD_RE.findall(text):
        if re.fullmatch(r"[\\d,\\.%]+", tok): continue
        if RE_HANGUL.search(tok): hit.add(BK_KO)
        elif RE_CYRILLIC.search(tok): hit.add(BK_RU)
        elif RE_VIET.search(tok): hit.add(BK_VI)
        elif RE_KANA.search(tok) or RE_HANZI.search(tok) or RE_THAI.search(tok): continue   # 형태소 경로가 처리
        elif tok.isascii():
            if RE_ASCII_LATIN.search(tok): hit.add(BK_EN)
        else: hit.add(BK_OTHER)   # 악센트 라틴·×·기타 비ASCII 기호 토큰 → 비영어(원본 top_30에 '2×'가 있는 것과 같은 규칙)
    return hit

bullets_df["buckets_multi"] = bullets_df["text"].apply(buckets_of)
multi_counts = {b["bucket"]: int(bullets_df["buckets_multi"].apply(lambda s: b["bucket"] in s).sum()) for b in wc["buckets"]}
single_counts = bullets_df["script_bucket"].value_counts().to_dict()
comparison = pd.DataFrame([{"문자권": b["bucket"], "원본(다중라벨)": b["n_bullets_with_any_token"], "원본 비중": b["bullet_share"],
                            "재현(다중라벨)": multi_counts[b["bucket"]], "차이": multi_counts[b["bucket"]] - b["n_bullets_with_any_token"],
                            "단일버킷 배정": single_counts.get(b["bucket"], 0)} for b in wc["buckets"]])
print("다중 라벨 재현 — 절대오차 합:", int(comparison["차이"].abs().sum()), "| 정확 일치 버킷:", int((comparison["차이"] == 0).sum()), "/ 8")
print("(태국어·러시아어·베트남어는 정확 일치. 일본어·중국어는 분기 조건은 같지만 원본이 형태소 결과에서 불용어·1자 토큰을 걸러 토큰 0개가 된 불릿만큼 +3~4건 차이,")
print(" 영어·비영어·한국어는 원본 불용어 목록·토큰 정규식이 저장소에 없어 그 차이만큼 근사 — 순위·비중 구조는 동일)")
comparison
'''),
        md("## 3. 소수 언어권 순위 — 원본 vs 재현"),
        code('''
minor = [BK_JA, BK_ZH, BK_TH, BK_RU, BK_VI]
mc = comparison[comparison["문자권"].isin(minor)].copy()
mc["원본 순위"] = mc["원본(다중라벨)"].rank(ascending=False).astype(int); mc["재현 순위"] = mc["재현(다중라벨)"].rank(ascending=False).astype(int)
print(f"소수 언어권 5개 중 순위 동일: {(mc['원본 순위'] == mc['재현 순위']).sum()} / 5")
mc[["문자권", "원본(다중라벨)", "원본 순위", "재현(다중라벨)", "재현 순위"]]
'''),
        md("## 4. 실제 불릿 예시 — 문자권별 1건씩 + 원본 상위 단어"),
        code('''
top_words = {b["bucket"]: [w["word"] for w in b["top_30"][:8]] for b in wc["buckets"]}
for b in wc["buckets"]:
    sample = bullets_df[bullets_df["buckets_multi"].apply(lambda s: b["bucket"] in s)]
    if len(sample) == 0:
        print(f"[{b['bucket']}] 없음\\n"); continue
    row = sample.iloc[0]
    print(f"[{b['bucket']}] 원본 상위어: {'·'.join(top_words[b['bucket']])}")
    print(f"   예시({row['fandom']}): {row['text'][:90]}{'…' if len(row['text']) > 90 else ''}\\n")
'''),
        md('''
## 5. 한계

1. 원본 토크나이저 소스(`run_lda_v6_live_reference_v7.py`)는 저장소에 없다. 일본어·중국어·태국어 버킷은 분기 조건 자체를 재현한 것이고, 일반 경로 4개 버킷은 원본의 불용어·토큰 정규식이 달라 근사치다.
2. 이 노트북은 토큰 빈도(형태소 분석)를 다루지 않는다 — 10,020건 토큰 빈도 CSV는 `v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py`가 산출한다.
'''),
    ]
    return cells


# ---------------------------------------------------------------------------------------------
NOTEBOOKS = {
    "ad_commercial_index/ad_commercial_index_v7.ipynb": nb_ad_commercial,
    "fandom_cohesion_index/fandom_cohesion_index_v7.ipynb": nb_cohesion,
    "media_content_exposure_index/media_content_exposure_v7.ipynb": nb_media,
    "domestic_regional_index/domestic_regional_index_v7.ipynb": nb_domestic,
    "worldwide_language_index/worldwide_language_index_v7.ipynb": nb_worldwide,
    "group_member_index/group_member_index_v7.ipynb": nb_group_member,
    "fan_impact_pathway/fan_impact_pathway_v7.ipynb": nb_fan_impact,
    "tokenizer/tokenizer_script_routing_v7.ipynb": nb_tokenizer_routing,
}


def main(execute=True, only=None):
    for rel, builder in NOTEBOOKS.items():
        if only and not any(o in rel for o in only):
            continue
        path = HERE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        nb = new_notebook(cells=builder(), metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                                     "language_info": {"name": "python"}})
        nbformat.write(nb, path)
        print("wrote", path.relative_to(HERE.parent))
        if execute:
            cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                   "--ExecutePreprocessor.timeout=1800", str(path)]
            subprocess.run(cmd, check=True, cwd=path.parent)
            print("executed", rel)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(execute="--no-exec" not in args, only=[a for a in args if not a.startswith("--")] or None)
