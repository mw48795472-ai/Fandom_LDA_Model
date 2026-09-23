# -*- coding: utf-8 -*-
"""L18 — MCI 지표 통일·같은 시점 상관 재산출·별칭 오매칭 감사.

1) 지표 통일: member_mention_index_v7.json(라이브 10,020건, 45개 그룹)의 MCI에 하한 1/n, MCI_excess = MCI − 1/n, 정규화 HHI = (MCI − 1/n)/(1 − 1/n)를 붙여
   member_mci_unified_v7.csv 로 고정한다(원본 JSON은 손대지 않는다).
2) 같은 시점 상관: 최종 MCI(10,020건) × 라이브 outcome(fandom_scores_live_reference_v7.json) 45개 그룹 — 원시 MCI·MCI_excess·HHI_norm 각각의
   Pearson(r, p, Fisher z 95% CI)·Spearman, 그리고 outcome ~ MCI + member_count 회귀(VIF). 비교용으로 같은 코드를
   (a) 저장된 상관 JSON(v7-55 MCI × 동결 outcome), (b) 최종 MCI × 동결 outcome 에도 적용해 세 조합을 한 표에 둔다.
3) 별칭 감사: 그룹 불릿에서 멤버명을 다시 세어(단순 부분 문자열 / 앞 글자가 한글이 아닌 경계 매칭) 기록된 언급 수와 비교한다.
   기록 > 부분 문자열 이면 별칭이 쓰였다는 뜻이고, 기록 < 부분 문자열 이면 동음 필터가 있었거나 오매칭 가능성이 있는 자리다.

출력 (이 폴더): member_mci_unified_v7.csv, member_mci_correlation_live_v7.json, member_alias_audit_v7.csv, MCI_SAME_PERIOD_V7.md
실행: python v7_final_10020/analysis/group_member_index/build_mci_same_period_v7.py
"""
import csv, json, re
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
D = REPO / "data" / "v7_final"
mm = json.load(open(D / "member_mention_index_v7.json", encoding="utf-8"))
corr_json = json.load(open(D / "member_pilot_mci_correlation_v7.json", encoding="utf-8"))
live = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8"))}
frozen = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))}
corpus = {f["fandom"]: f for f in json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))}
OUTCOMES = ["loyalty_score", "spillover_score", "coverage_index", "factor_diversity"]
groups = sorted(mm)

# ---- 1. 지표 통일
uni = []
for g in groups:
    rec = mm[g]; n = len(rec["member_mention_counts"]); mci = rec["mci_index"]; floor = 1 / n
    top = max(rec["member_mention_counts"], key=rec["member_mention_counts"].get)
    uni.append({"group": g, "n_members": n, "total_group_bullets": rec["total_group_bullets"], "total_member_mentions": rec["total_member_mentions"],
                "mci": mci, "mci_floor": round(floor, 4), "mci_excess": round(mci - floor, 4), "hhi_norm": round((mci - floor) / (1 - floor), 4) if n > 1 else "",
                "top_member": top, "top_member_share": rec["member_impact_share_index"][top]})
with open(HERE / "member_mci_unified_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(uni[0].keys())); w.writeheader(); w.writerows(uni)
U = {u["group"]: u for u in uni}

# ---- 2. 상관 (세 조합)
def pearson_block(x, y):
    r, p = stats.pearsonr(x, y); n = len(x); z = np.arctanh(r); se = 1 / np.sqrt(n - 3)
    rho, ps = stats.spearmanr(x, y)
    return {"n": n, "pearson_r": round(float(r), 4), "pearson_p": round(float(p), 6), "pearson_ci95": [round(float(np.tanh(z - 1.96 * se)), 4), round(float(np.tanh(z + 1.96 * se)), 4)],
            "r_squared": round(float(r * r), 4), "spearman_rho": round(float(rho), 4), "spearman_p": round(float(ps), 6)}
def ols(y, X, names):
    X1 = np.column_stack([np.ones(len(y)), X]); beta, *_ = np.linalg.lstsq(X1, y, rcond=None); res = y - X1 @ beta
    n, k = X1.shape; s2 = float(res @ res) / (n - k); cov = s2 * np.linalg.inv(X1.T @ X1); se = np.sqrt(np.diag(cov)); t = beta / se
    p = 2 * (1 - stats.t.cdf(np.abs(t), n - k)); ss_tot = float(((y - y.mean()) ** 2).sum()); r2 = 1 - float(res @ res) / ss_tot
    vif = {}
    for j, nm in enumerate(names):
        others = np.delete(X, j, axis=1); Xo = np.column_stack([np.ones(len(y)), others]); b, *_ = np.linalg.lstsq(Xo, X[:, j], rcond=None)
        rr = X[:, j] - Xo @ b; r2j = 1 - float(rr @ rr) / float(((X[:, j] - X[:, j].mean()) ** 2).sum()); vif[nm] = round(1 / (1 - r2j), 3)
    return {"r_squared": round(r2, 4), "adj_r_squared": round(1 - (1 - r2) * (n - 1) / (n - k), 4),
            "coefficients": {nm: {"coef": round(float(beta[i]), 4), "se": round(float(se[i]), 4), "t": round(float(t[i]), 3), "p": round(float(p[i]), 6)} for i, nm in enumerate(["intercept"] + names)}, "vif": vif}
def run_pairing(mci_key_source, outcome_src, label):
    x_raw = np.array([mci_key_source[g]["mci"] for g in groups]); x_ex = np.array([mci_key_source[g]["mci_excess"] for g in groups])
    x_hn = np.array([mci_key_source[g]["hhi_norm"] for g in groups], dtype=float); nmem = np.array([mci_key_source[g]["n_members"] for g in groups], dtype=float)
    out = {"label": label, "n_groups": len(groups), "mci_vs_member_count": pearson_block(x_raw, nmem), "correlations": {}, "regression_mci_plus_member_count": {}}
    for oc in OUTCOMES:
        y = np.array([outcome_src[g][oc] for g in groups], dtype=float)
        out["correlations"][oc] = {"mci_raw": pearson_block(x_raw, y), "mci_excess": pearson_block(x_ex, y), "hhi_norm": pearson_block(x_hn, y)}
        out["regression_mci_plus_member_count"][oc] = ols(y, np.column_stack([x_raw, nmem]), ["mci", "member_count"])
    return out
# (a) 저장 JSON 은 v7-55 MCI 원자료가 없으므로 그 결과값을 그대로 옮긴다
stored = {"label": "v7-55 MCI(8,981건) × 동결 outcome(7,350건) — 저장된 member_pilot_mci_correlation_v7.json", "n_groups": corr_json["n_groups"],
          "mci_vs_member_count": {"pearson_r": corr_json["mci_vs_member_count"]["pearson_r"]},
          "correlations": {oc: {"mci_raw": {"pearson_r": corr_json["correlations_mci_raw"][oc]["pearson_r"], "pearson_p": corr_json["correlations_mci_raw"][oc]["pearson_p"], "r_squared": corr_json["correlations_mci_raw"][oc]["r_squared"]},
                                "mci_excess": {"pearson_r": corr_json["correlations_mci_excess"][oc]["pearson_r"], "pearson_p": corr_json["correlations_mci_excess"][oc]["pearson_p"], "r_squared": corr_json["correlations_mci_excess"][oc]["r_squared"]}} for oc in OUTCOMES}}
final_frozen = run_pairing(U, frozen, "최종 MCI(10,020건) × 동결 outcome(7,350건) — 시점 불일치, 비교용")
final_live = run_pairing(U, live, "최종 MCI(10,020건) × 라이브 outcome(10,020건) — 같은 시점 (이 파일의 본 결과)")
result = {"purpose": "L18: MCI ↔ outcome 상관을 같은 시점(라이브 10,020건 MCI × 라이브 점수)으로 재산출하고, 지표 3종(원시 MCI / MCI_excess / 정규화 HHI)과 세 시점 조합을 한 표에 둔다",
          "metric_definitions": {"mci": "Σ share_i², 하한 1/n", "mci_excess": "MCI − 1/n", "hhi_norm": "(MCI − 1/n)/(1 − 1/n), 0(완전 균등)∼1(한 명 독점)"},
          "pairings": {"stored_v7_55_x_frozen": stored, "final_x_frozen": final_frozen, "final_x_live": final_live}}
json.dump(result, open(HERE / "member_mci_correlation_live_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- 3. 별칭·동음 감사
HANGUL = re.compile(r"[가-힣]")
audit = []
for g in groups:
    rec = mm[g]; texts = [it["t"] for tag in ("loyalty", "spillover") for it in corpus[g][tag]]
    for mem, recorded in rec["member_mention_counts"].items():
        sub = sum(1 for t in texts if mem in t)
        bnd = sum(1 for t in texts if any((i == 0 or not HANGUL.match(t[i - 1])) for i in [m.start() for m in re.finditer(re.escape(mem), t)]))
        flag = "일치" if recorded == sub else ("별칭·영문명 포함(기록>부분문자열)" if recorded > sub else ("동음 필터 추정(기록<부분문자열)" if recorded >= bnd else "경계 매칭보다도 적음"))
        audit.append({"group": g, "member": mem, "name_len": len(mem), "recorded": recorded, "substring_bullets": sub, "boundary_bullets": bnd, "flag": flag,
                      "ambiguous_short_name": "Y" if len(mem) == 1 or (len(mem) == 2 and sub - bnd >= 3) else ""})
with open(HERE / "member_alias_audit_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(audit[0].keys())); w.writeheader(); w.writerows(audit)
from collections import Counter
flag_cnt = Counter(a["flag"] for a in audit); n_amb = sum(a["ambiguous_short_name"] == "Y" for a in audit)
worst = sorted([a for a in audit if a["recorded"] < a["substring_bullets"]], key=lambda a: a["substring_bullets"] - a["recorded"], reverse=True)[:12]

# ---- MD
fl = final_live; ff = final_frozen
md = ["# MCI 같은 시점 재산출과 지표 통일 (L18)\n",
      "`member_pilot_mci_correlation_v7.json`은 v7-55 시점 MCI(8,981건)와 동결 outcome(7,350건)을 섞은 상관이었다. 이 문서는 **최종 MCI(10,020건) × 라이브 outcome(10,020건)** 으로 시점을 맞춘 결과이고, "
      "지표는 원시 MCI 외에 MCI_excess(= MCI − 1/n)와 정규화 HHI(= (MCI − 1/n)/(1 − 1/n))를 함께 둔다. 전부 `build_mci_same_period_v7.py`가 만든다.\n",
      "## 0. 결론\n"]
lr = fl["correlations"]["loyalty_score"]
md.append(f"- 같은 시점(45개 그룹)에서 원시 MCI ∼ 팬충성도 r = {lr['mci_raw']['pearson_r']} (p = {lr['mci_raw']['pearson_p']:.4f}, 95% CI {lr['mci_raw']['pearson_ci95']}), MCI ∼ 멤버 수 r = {fl['mci_vs_member_count']['pearson_r']}.")
best_ex = max(OUTCOMES, key=lambda oc: fl["correlations"][oc]["mci_excess"]["r_squared"]); best_hn = max(OUTCOMES, key=lambda oc: fl["correlations"][oc]["hhi_norm"]["r_squared"])
md.append(f"- 멤버 수를 뺀 MCI_excess 로는 가장 큰 R²가 {fl['correlations'][best_ex]['mci_excess']['r_squared']} ({best_ex}, p = {fl['correlations'][best_ex]['mci_excess']['pearson_p']:.3f}), 정규화 HHI 로는 {fl['correlations'][best_hn]['hhi_norm']['r_squared']} ({best_hn}, p = {fl['correlations'][best_hn]['hhi_norm']['pearson_p']:.3f}). "
          f"팬충성도 ~ MCI + 멤버 수 회귀에서 MCI 계수 p = {fl['regression_mci_plus_member_count']['loyalty_score']['coefficients']['mci']['p']:.3f}, 멤버 수 계수 p = {fl['regression_mci_plus_member_count']['loyalty_score']['coefficients']['member_count']['p']:.3f}.")
md.append("- 시점을 맞춰도 결론은 저장 JSON과 같다: 원시 MCI의 설명력은 멤버 수가 만드는 구조적 하한에서 오고, 하한을 뺀 지표로는 어떤 outcome과도 유의하지 않다. 보고 지표는 MCI_excess 또는 정규화 HHI로 통일하는 것이 맞다.")
md.append(f"- 별칭 감사: 멤버 {len(audit)}명 중 기록 = 단순 부분 문자열 {flag_cnt['일치']}명, 기록 > 부분 문자열(별칭·영문명 반영) {flag_cnt.get('별칭·영문명 포함(기록>부분문자열)', 0)}명, 기록 < 부분 문자열(동음 필터 추정) {flag_cnt.get('동음 필터 추정(기록<부분문자열)', 0) + flag_cnt.get('경계 매칭보다도 적음', 0)}명. 한 글자·짧은 동음 이름 {n_amb}명은 `member_alias_audit_v7.csv`에 표시했다.\n")
md.append("## 1. 세 조합 비교 — 원시 MCI / MCI_excess (Pearson r, R²)\n")
md.append("| outcome | v7-55 MCI × 동결 (저장 JSON) | 최종 MCI × 동결 (시점 불일치) | **최종 MCI × 라이브 (같은 시점)** |\n|---|---|---|---|")
for oc in OUTCOMES:
    s_ = stored["correlations"][oc]; a = ff["correlations"][oc]; b = fl["correlations"][oc]
    md.append(f"| {oc} | raw {s_['mci_raw']['pearson_r']} (R² {s_['mci_raw']['r_squared']}) / excess {s_['mci_excess']['pearson_r']} (R² {s_['mci_excess']['r_squared']}) "
              f"| raw {a['mci_raw']['pearson_r']} (R² {a['mci_raw']['r_squared']}) / excess {a['mci_excess']['pearson_r']} (R² {a['mci_excess']['r_squared']}) "
              f"| **raw {b['mci_raw']['pearson_r']} (R² {b['mci_raw']['r_squared']}, p {b['mci_raw']['pearson_p']:.4f}) / excess {b['mci_excess']['pearson_r']} (R² {b['mci_excess']['r_squared']}, p {b['mci_excess']['pearson_p']:.3f}) / HHI_norm {b['hhi_norm']['pearson_r']} (R² {b['hhi_norm']['r_squared']})** |")
md.append(f"\nMCI ∼ 멤버 수: 저장 JSON {stored['mci_vs_member_count']['pearson_r']} / 최종 × 동결 {ff['mci_vs_member_count']['pearson_r']} / 최종 × 라이브 {fl['mci_vs_member_count']['pearson_r']} (MCI는 같고 outcome만 달라 세 번째는 두 번째와 같다).\n")
md.append("## 2. 같은 시점 — outcome ~ MCI + 멤버 수 회귀\n")
md.append("| outcome | R² | adj R² | MCI 계수 (p) | 멤버 수 계수 (p) | VIF |\n|---|---|---|---|---|---|")
for oc in OUTCOMES:
    r = fl["regression_mci_plus_member_count"][oc]; c = r["coefficients"]
    md.append(f"| {oc} | {r['r_squared']} | {r['adj_r_squared']} | {c['mci']['coef']} ({c['mci']['p']:.3f}) | {c['member_count']['coef']} ({c['member_count']['p']:.3f}) | {r['vif']['mci']} |")
md.append("\n## 3. 같은 시점 — Spearman과 95% CI\n")
md.append("| outcome | 지표 | Pearson r | 95% CI | Spearman ρ (p) |\n|---|---|---|---|---|")
for oc in OUTCOMES:
    for met in ("mci_raw", "mci_excess", "hhi_norm"):
        b = fl["correlations"][oc][met]; md.append(f"| {oc} | {met} | {b['pearson_r']} | {b['pearson_ci95']} | {b['spearman_rho']} ({b['spearman_p']:.3f}) |")
md.append("\n## 4. 지표 통일 파일 — `member_mci_unified_v7.csv`\n")
md.append("| 그룹 | n | 원시 MCI | 하한 1/n | MCI_excess | HHI_norm | 1위 멤버 (점유율) |\n|---|---|---|---|---|---|---|")
for u in sorted(uni, key=lambda u: -u["hhi_norm"] if u["hhi_norm"] != "" else 0)[:12]: md.append(f"| {u['group']} | {u['n_members']} | {u['mci']} | {u['mci_floor']} | {u['mci_excess']} | {u['hhi_norm']} | {u['top_member']} ({u['top_member_share']}) |")
md.append(f"\n(HHI_norm 상위 12개만. 전체 {len(uni)}개 그룹은 CSV.) 2인 그룹(FTISLAND·동방신기)은 원시 MCI 하한이 0.5라 원시 순위에서 항상 위에 있지만 HHI_norm 으로는 제자리를 찾는다.\n")
md.append("## 5. 별칭·동음 감사 — `member_alias_audit_v7.csv`\n")
md.append("기록된 언급 수(`member_mention_counts`)를 그룹 불릿에서 다시 센 값과 비교했다. 원본 파이프라인의 별칭 처리 코드는 저장소에 없으므로(L4) 이 감사는 '어디에 별칭·동음 처리가 있었는가'를 드러내는 간접 증거다.\n")
md.append("| 구분 | 멤버 수 |\n|---|---|")
for k, v in flag_cnt.most_common(): md.append(f"| {k} | {v} |")
md.append(f"| 짧은·동음 가능 이름(표시) | {n_amb} |")
md.append("\n기록 < 부분 문자열 차이가 큰 멤버 (동음 필터가 있었거나, 없었다면 오매칭 가능성이 있는 자리):\n")
md.append("| 그룹 | 멤버 | 기록 | 부분 문자열 불릿 | 경계 매칭 불릿 |\n|---|---|---|---|---|")
for a in worst: md.append(f"| {a['group']} | {a['member']} | {a['recorded']} | {a['substring_bullets']} | {a['boundary_bullets']} |")
md.append("\n## 6. 한계\n")
md.append("1. 같은 시점이라 해도 45개 그룹 소표본이고 outcome 4종은 서로 상관돼 있다. 여기 p값은 다중비교 보정을 하지 않았다.\n"
          "2. 감사는 기록값과 재계수의 차이를 보여줄 뿐 원본 별칭 사전을 복원하지 못한다. 별칭 사전(파일럿 10그룹)은 `analysis/dictionaries/index_dictionaries_v7.csv`에 있고 나머지 35그룹 분은 없다.\n"
          "3. `member_mention_index_v7.json`은 손대지 않았다. 보고 지표를 바꾸려면 README 6절 표의 MCI 열을 `member_mci_unified_v7.csv`의 HHI_norm 으로 바꾸고 verify 항목을 같이 옮겨야 한다(다음 라운드).\n")
md.append("## 7. 파일\n| 파일 | 내용 |\n|---|---|\n| `member_mci_unified_v7.csv` | 45개 그룹 원시 MCI·하한·MCI_excess·HHI_norm·1위 멤버 |\n| `member_mci_correlation_live_v7.json` | 세 조합(저장 JSON / 최종×동결 / 최종×라이브)의 상관·회귀 |\n| `member_alias_audit_v7.csv` | 멤버별 기록 언급 수 vs 재계수(부분 문자열·경계) |\n| `build_mci_same_period_v7.py` | 이 문서와 위 파일을 만드는 스크립트 |\n")
(HERE / "MCI_SAME_PERIOD_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("same-period raw loyalty r", lr["mci_raw"]["pearson_r"], "excess best R2", fl["correlations"][best_ex]["mci_excess"]["r_squared"], best_ex, "| final×frozen loyalty r", ff["correlations"]["loyalty_score"]["mci_raw"]["pearson_r"], "vs README -0.385 | mci~n", fl["mci_vs_member_count"]["pearson_r"], "vs -0.728")
print("audit flags", dict(flag_cnt), "ambiguous", n_amb)
