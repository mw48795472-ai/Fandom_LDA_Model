# -*- coding: utf-8 -*-
"""L12 — 조사 노출량(팬덤별 수집 불릿 수)을 공변량으로 다룬다.
L10의 축소 반복이 보였듯 팬충성도·파급효과 점수는 EvidenceScore '합'의 min-max 라 팬덤별 불릿 건수와 r≈0.9로 묶여 있다.
여기서는 같은 문장 점수에서 건수에 덜 의존하는 정의 두 가지를 만들어 원 지수와 나란히 둔다(원 지수는 바꾸지 않는다).
  (a) 원 지수         score = minmax(Σ EvidenceScore)                       — 건수 × 문장당 평균
  (b) 밀도 점수       score_density = minmax(mean EvidenceScore per sentence)  — 건수와 독립(문장이 얼마나 '근거다운가')
  (c) 노출량 통제 점수 score_resid = minmax(잔차: log(Σ) ~ log(n) 회귀)          — 같은 건수 대비 초과분
그리고 r(충성도, 파급효과)를 세 정의에서 비교하고(판별타당도), 활동(activity=총 불릿 수)을 통제한 편상관, 상위 15 순위의 이동을 적는다.
라이브는 문장 단위 CSV(L5)에서, 동결은 점수 JSON의 loyalty_raw·n 에서 계산한다.
출력 (이 폴더): exposure_adjusted_scores_v7.csv(팬덤 100 × 두 스냅샷), exposure_adjustment_summary_v7.json, EXPOSURE_ADJUSTMENT_V7.md
실행: python v7_final_10020/index_methodology/build_exposure_adjusted_scores_v7.py
"""
import csv, json
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]; D = REPO / "data" / "v7_final"
live = json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8")); frozen = json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))
mm = lambda v: (v - v.min()) / (v.max() - v.min())

def build(scores, label):
    names = [r["fandom"] for r in scores]
    rl = np.array([r["loyalty_raw"] for r in scores]); rs = np.array([r["spillover_raw"] for r in scores]); nl = np.array([r["n_loyalty_bullets"] for r in scores], float); ns = np.array([r["n_spillover_bullets"] for r in scores], float)
    L0 = np.array([r["loyalty_score"] for r in scores]); S0 = np.array([r["spillover_score"] for r in scores]); act = nl + ns
    assert np.allclose(mm(rl), L0, atol=6e-4) and np.allclose(mm(rs), S0, atol=6e-4)
    Ld, Sd = mm(rl / nl), mm(rs / ns)
    def resid(raw, n):
        b = np.polyfit(np.log(n), np.log(raw), 1); return np.log(raw) - np.polyval(b, np.log(n))
    Lr, Sr = mm(resid(rl, nl)), mm(resid(rs, ns))
    defs = {"original": (L0, S0), "density": (Ld, Sd), "exposure_residual": (Lr, Sr)}
    def pr(x, y): r, p = stats.pearsonr(x, y); return {"r": round(float(r), 4), "p": round(float(p), 6)}
    def partial(x, y, z):
        rx = x - np.polyval(np.polyfit(z, x, 1), z); ry = y - np.polyval(np.polyfit(z, y, 1), z); return pr(rx, ry)
    def top(v, k=15): return [names[i] for i in np.argsort(-v)[:k]]
    top_orig = top(L0 + S0); summ = {"label": label, "n": len(names), "definitions": {}}
    for k, (L, S) in defs.items():
        summ["definitions"][k] = {"r_loyalty_vs_n_loyalty": pr(L, nl)["r"], "r_spillover_vs_n_spillover": pr(S, ns)["r"], "r_loyalty_vs_activity": pr(L, act)["r"], "r_spillover_vs_activity": pr(S, act)["r"],
                                   "r_loyalty_spillover": pr(L, S), "partial_r_given_activity": partial(L, S, np.log(act)), "spearman_rank_vs_original_loyalty": round(float(stats.spearmanr(L, L0)[0]), 4),
                                   "spearman_rank_vs_original_spillover": round(float(stats.spearmanr(S, S0)[0]), 4), "top15_by_sum": top(L + S), "top15_overlap_with_original": len(set(top(L + S)) & set(top_orig))}
    rows = [{"snapshot": label, "fandom": names[i], "n_loyalty": int(nl[i]), "n_spillover": int(ns[i]), "activity": int(act[i]), "loyalty_raw": round(float(rl[i]), 3), "spillover_raw": round(float(rs[i]), 3),
             "loyalty_score": round(float(L0[i]), 3), "spillover_score": round(float(S0[i]), 3), "loyalty_density": round(float(Ld[i]), 3), "spillover_density": round(float(Sd[i]), 3),
             "loyalty_exposure_resid": round(float(Lr[i]), 3), "spillover_exposure_resid": round(float(Sr[i]), 3), "mean_evidence_loyalty": round(float(rl[i] / nl[i]), 3), "mean_evidence_spillover": round(float(rs[i] / ns[i]), 3)} for i in range(len(names))]
    return summ, rows
sl, rl_ = build(live, "live_10020"); sf, rf_ = build(frozen, "frozen_7350")
with open(HERE / "exposure_adjusted_scores_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rl_[0].keys())); w.writeheader(); w.writerows(rl_ + rf_)
json.dump({"definitions": {"original": "minmax(Σ EvidenceScore)", "density": "minmax(mean EvidenceScore per sentence)", "exposure_residual": "minmax(residual of log Σ on log n)"}, "live_10020": sl, "frozen_7350": sf},
          open(HERE / "exposure_adjustment_summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def sec(s):
    d = s["definitions"]; o, de, re_ = d["original"], d["density"], d["exposure_residual"]
    return [f"| {s['label']} | 원 지수 | {o['r_loyalty_vs_n_loyalty']} / {o['r_spillover_vs_n_spillover']} | {o['r_loyalty_spillover']['r']} (p {o['r_loyalty_spillover']['p']:.2g}) | {o['partial_r_given_activity']['r']} | 1.0 / 1.0 | 15/15 |",
            f"| {s['label']} | 밀도 | {de['r_loyalty_vs_n_loyalty']} / {de['r_spillover_vs_n_spillover']} | {de['r_loyalty_spillover']['r']} (p {de['r_loyalty_spillover']['p']:.2g}) | {de['partial_r_given_activity']['r']} | {de['spearman_rank_vs_original_loyalty']} / {de['spearman_rank_vs_original_spillover']} | {de['top15_overlap_with_original']}/15 |",
            f"| {s['label']} | 노출량 잔차 | {re_['r_loyalty_vs_n_loyalty']} / {re_['r_spillover_vs_n_spillover']} | {re_['r_loyalty_spillover']['r']} (p {re_['r_loyalty_spillover']['p']:.2g}) | {re_['partial_r_given_activity']['r']} | {re_['spearman_rank_vs_original_loyalty']} / {re_['spearman_rank_vs_original_spillover']} | {re_['top15_overlap_with_original']}/15 |"]
o, de = sl["definitions"]["original"], sl["definitions"]["density"]
md = ["# 조사 노출량 공변량 (L12) — 점수에서 '몇 건 모았는가'를 걷어내면 무엇이 남는가\n",
      "팬충성도·파급효과 점수는 문장 EvidenceScore 합의 min-max 라 팬덤별 수집 불릿 수(조사 노출량)와 거의 같이 움직인다(L10). 이 문서는 같은 문장 점수에서 건수에 덜 의존하는 정의 두 가지(밀도·노출량 잔차)를 만들어 원 지수와 나란히 둔다. 원 지수·README 표는 바꾸지 않았다. `build_exposure_adjusted_scores_v7.py`가 만든다.\n",
      "## 0. 결론\n",
      f"- 라이브 원 지수는 건수와 r = {o['r_loyalty_vs_n_loyalty']}(충성도) / {o['r_spillover_vs_n_spillover']}(파급효과). 활동(총 불릿 수)을 통제한 충성도·파급효과 편상관은 {o['partial_r_given_activity']['r']}(원 r {o['r_loyalty_spillover']['r']}).",
      f"- 밀도 점수(문장당 평균 EvidenceScore)는 건수와 r = {de['r_loyalty_vs_n_loyalty']} / {de['r_spillover_vs_n_spillover']}로 독립에 가깝고, 충성도·파급효과 r = {de['r_loyalty_spillover']['r']}(p {de['r_loyalty_spillover']['p']:.2g}). 원 지수와의 순위 상관은 {de['spearman_rank_vs_original_loyalty']} / {de['spearman_rank_vs_original_spillover']}, 상위 15 겹침 {de['top15_overlap_with_original']}/15 — 노출량을 걷어내면 순위표가 크게 달라진다.",
      f"- **판별타당도 반전은 건수 구조의 산물이다.** 밀도 정의에서는 r(충성도, 파급효과)가 라이브 {de['r_loyalty_spillover']['r']}·동결 {sf['definitions']['density']['r_loyalty_spillover']['r']}로 두 스냅샷 모두 |r|<0.5 이고 크기 순서도 뒤집히지 않는다. 노출량 잔차 정의도 라이브 {sl['definitions']['exposure_residual']['r_loyalty_spillover']['r']}·동결 {sf['definitions']['exposure_residual']['r_loyalty_spillover']['r']}로 같다. 원 지수의 활동 통제 편상관이 음수(라이브 {o['partial_r_given_activity']['r']}, 동결 {sf['definitions']['original']['partial_r_given_activity']['r']})인 것은 두 점수가 같은 건수를 나눠 갖는 구조(합의 min-max)에서 오는 인공물이다.",
      f"- 동결도 같은 방향이다(아래 표). 즉 보고서의 순위표·판별타당도는 상당 부분 '얼마나 많이 수집됐는가'의 순위이고, '근거 한 건의 밀도'로 보면 다른 그림이 나온다. 두 정의는 서로 다른 질문(규모 vs 밀도)에 답하므로 하나로 대체하기보다 병기하는 것이 맞다.\n",
      "## 1. 세 정의 비교\n", "| 스냅샷 | 정의 | 건수와의 r (충성도 / 파급효과) | r(충성도, 파급효과) | 활동 통제 편상관 | 원 지수와 순위 상관 (충성도 / 파급효과) | 상위 15 겹침 |\n|---|---|---|---|---|---|---|"]
md += sec(sl) + sec(sf)
md.append("\n## 2. 상위 15 — 원 지수 vs 밀도 (라이브)\n| 순위 | 원 지수(충성도+파급효과) | 밀도 점수 | 노출량 잔차 |\n|---|---|---|---|")
for i in range(15): md.append(f"| {i+1} | {o['top15_by_sum'][i]} | {de['top15_by_sum'][i]} | {sl['definitions']['exposure_residual']['top15_by_sum'][i]} |")
md.append("\n팬덤 100개 × 두 스냅샷의 전체 값은 `exposure_adjusted_scores_v7.csv`(원 점수·밀도·잔차·문장당 평균 EvidenceScore·건수).\n")
md.append("## 3. 정의\n| 정의 | 식 | 뜻 |\n|---|---|---|\n| 원 지수 | minmax(Σ EvidenceScore) | 규모: 근거가 많고 수치·키워드가 풍부할수록 높다. 건수에 비례 |\n| 밀도 | minmax(mean EvidenceScore) | 문장 한 건이 얼마나 근거다운가(수치 표현·보너스 키워드 밀도). 건수와 독립 |\n| 노출량 잔차 | minmax(log Σ − 회귀 예측(log n)) | 같은 건수를 가진 팬덤 대비 초과분. 로그-로그 회귀 잔차 |\n")
md.append("## 4. 한계\n1. 밀도 점수는 문장 길이·수치 표현 습관(매체별 문체)에 민감하다. 건수 편향을 없애는 대신 문체 편향을 들인다.\n2. 잔차 점수는 회귀선을 100개 팬덤에서 추정하므로 표본 의존적이다.\n3. 원 지수를 바꾸지 않았다. 순위표를 밀도 기준으로 병기하려면 README 4절 표와 verify 항목을 함께 손봐야 한다. 근본 해법은 수집 단계에서 팬덤별 목표 건수를 통제하거나(층화 수집) 노출량을 명시적 공변량으로 보고하는 것이다.\n")
md.append("## 5. 파일\n| 파일 | 내용 |\n|---|---|\n| `exposure_adjusted_scores_v7.csv` | 팬덤 100 × 스냅샷 2: 원 점수·밀도·잔차·문장당 평균·건수 |\n| `exposure_adjustment_summary_v7.json` | 정의별 상관·편상관·순위 상관·상위 15 |\n| `build_exposure_adjusted_scores_v7.py` | 이 문서를 만드는 스크립트 |\n")
(HERE / "EXPOSURE_ADJUSTMENT_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
for s in (sl, sf):
    for k, v in s["definitions"].items(): print(s["label"], k, "r_n", v["r_loyalty_vs_n_loyalty"], v["r_spillover_vs_n_spillover"], "r_LS", v["r_loyalty_spillover"]["r"], "partial", v["partial_r_given_activity"]["r"], "rank", v["spearman_rank_vs_original_loyalty"], v["spearman_rank_vs_original_spillover"], "top15", v["top15_overlap_with_original"])
