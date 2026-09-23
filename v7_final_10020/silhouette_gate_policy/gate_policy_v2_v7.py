# -*- coding: utf-8 -*-
"""L6 — 실루엣 게이트 개편안(v2)과 측정된 적합 4건에 대한 적용 결과.
현 정책(v1): 새 K→M 재군집화의 실루엣이 동결 스냅샷 0.267(시드 하나의 한 번 적합)을 넘지 못하면 기각. 28회 연속 기각.
L7·L3의 측정: 0.267은 저장소의 재료로는 어느 시드로도 재현되지 않고(40회 중 0회, 최대 0.192), 시드에 따라 최적 M이 4∼8, 토픽 상위 10단어가 60%쯤 바뀐다.
v2 제안 — '단일 실루엣 임계'를 '시드 분포 + 안정성 합의'로 바꾼다:
  (G1) 실루엣: 시드 ≥10개의 M=5(또는 채택 M) 실루엣 **중앙값**이 현직 모델의 같은 방식 중앙값 이상
  (G2) 토픽 안정성: 시드 쌍 상위 10단어 Jaccard 중앙값 ≥ 0.35
  (G3) M 합의: 시드별 최적 M의 최빈값이 채택 M과 같거나, 채택 M의 실루엣이 최빈 M 실루엣의 90% 이상
  (G4) 현직 기준의 재현 가능성: 현직 모델의 기준값은 저장소 재료로 같은 방식으로 다시 잴 수 있어야 한다 → 동결 0.267은 기준이 될 수 없으므로,
       재현 가능한 모델(동결 근사 재적합 K=10, 시드 중앙값 0.097)로 기준을 옮긴다.
이 스크립트는 seed_stability 결과(L7)로 네 적합(라이브 K=8/K=10, 동결 근사 K=8/K=10)에 v1·v2를 적용한 판정표를 만든다.
출력 (이 폴더): gate_policy_v2_decisions_v7.json, GATE_POLICY_V2_PROPOSAL_V7.md
실행: python v7_final_10020/silhouette_gate_policy/gate_policy_v2_v7.py
"""
import json, statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
S = json.load(open(REPO / "v7_final_10020" / "analysis" / "persona_decision_space" / "topic_phi_cosine" / "seed_stability" / "seed_stability_summary_v7.json", encoding="utf-8"))
res = S["results"]; V1 = 0.267; JAC = 0.35; ADOPT_M = 5
INCUMBENT = "frozen_approx_7326_K10"   # G4: 재현 가능한 기준
inc_med = res[INCUMBENT]["silhouette_M5"]["median"]
rows = {}
for key, v in res.items():
    m5 = v["silhouette_M5"]; bm = v["silhouette_best_M"]; mode_m = Counter(bm["best_M_by_seed"]).most_common(1)[0][0]
    # G3: 채택 M(5) 실루엣 중앙값 vs 최빈 M 실루엣 중앙값(최적 M 실루엣 중앙값을 대용)
    g1 = m5["median"] >= inc_med; g2 = v["topic_jaccard_top10"]["median"] >= JAC; g3 = (mode_m == ADOPT_M) or (m5["median"] >= 0.9 * bm["median"])
    v1_seed0 = m5["values"][0] >= V1
    rows[key] = {"corpus": v["corpus"], "K": v["K"], "seed0_M5": m5["values"][0], "v1_pass(seed0 ≥ 0.267)": v1_seed0, "v1_any_seed_pass": v["n_seeds_M5_ge_0267"] > 0,
                 "M5_median": m5["median"], "M5_range": [m5["min"], m5["max"]], "jaccard_median": v["topic_jaccard_top10"]["median"], "best_M_mode": mode_m, "best_M_by_seed": bm["best_M_by_seed"],
                 "G1_sil_median_ge_incumbent": g1, "G2_jaccard_ge_0.35": g2, "G3_M_consensus": g3, "v2_pass": bool(g1 and g2 and g3)}
out = {"v1": {"rule": "M 실루엣(시드 0 한 번) ≥ 0.267", "baseline": V1, "baseline_reproducible": False},
       "v2": {"G1": f"시드 ≥10 M=5 실루엣 중앙값 ≥ 현직({INCUMBENT}) 중앙값 {inc_med}", "G2": f"시드 쌍 토픽 Jaccard 중앙값 ≥ {JAC}", "G3": "시드별 최적 M 최빈값 = 채택 M, 또는 채택 M 중앙값 ≥ 최적 M 중앙값의 90%", "G4": "현직 기준값은 저장소 재료로 같은 방식으로 재측정 가능해야 함 → 기준을 동결 근사 재적합으로 이전"},
       "decisions": rows}
json.dump(out, open(HERE / "gate_policy_v2_decisions_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
md = ["# 실루엣 게이트 개편안 v2 (L6) — 단일 실루엣 임계에서 시드 분포·안정성 합의로\n",
      "현 정책(v1)은 새 재적합의 M 실루엣(시드 하나, 한 번)이 동결 0.267을 넘어야 해석 계층을 교체한다. 0.267은 저장소 재료로 어느 시드로도 재현되지 않고(L3·L7: 40회 중 0회, 최대 0.192), 실루엣 자체가 시드에 따라 두 배 가까이 움직인다. 이 문서는 개편안과, L7의 측정치로 네 적합에 v1·v2를 적용한 판정표다. **제안이며 보고서 본문·해석 계층은 바꾸지 않았다.** `gate_policy_v2_v7.py`가 만든다.\n",
      "## 1. 제안\n", "| 조건 | 내용 | 근거 |\n|---|---|---|",
      f"| G1 실루엣 | 시드 ≥10개의 채택 M 실루엣 **중앙값** ≥ 현직 모델의 같은 방식 중앙값 (현직 = 동결 근사 재적합 K=10, {inc_med}) | 단일 시드 값은 분포의 한 점(L7) |",
      f"| G2 토픽 안정성 | 시드 쌍 상위 10단어 Jaccard 중앙값 ≥ {JAC} | 측정된 네 적합이 0.39∼0.40; 그 아래면 토픽 라벨을 고정할 수 없다 |",
      "| G3 M 합의 | 시드별 최적 M의 최빈값이 채택 M이거나, 채택 M 실루엣 중앙값이 최적 M 중앙값의 90% 이상 | 최적 M이 시드마다 4∼8로 흔들림 |",
      "| G4 재현 가능한 기준 | 현직 기준값은 저장소 재료로 다시 잴 수 있어야 한다 | 0.267은 재현 불가 → 기준을 재현 가능한 모델로 이전 |",
      "| 표기 | 계층 표기를 파일명·컬럼명 수준으로 내린다(`*_frozen_v7_40`, `*_live_10020`) | 이미 대부분 적용됨 |\n",
      "## 2. 네 적합에 적용\n", "| 적합 | seed 0 M=5 | v1 (≥0.267) | v1 어느 시드라도 | M=5 중앙값 (범위) | Jaccard 중앙값 | 최적 M 최빈 (시드별) | G1 | G2 | G3 | **v2** |\n|---|---|---|---|---|---|---|---|---|---|---|"]
for k, r in rows.items():
    md.append(f"| {r['corpus']} K={r['K']} | {r['seed0_M5']} | {'통과' if r['v1_pass(seed0 ≥ 0.267)'] else '기각'} | {'통과' if r['v1_any_seed_pass'] else '기각'} | {r['M5_median']} ({r['M5_range'][0]}∼{r['M5_range'][1]}) | {r['jaccard_median']} | {r['best_M_mode']} ({r['best_M_by_seed']}) | {'○' if r['G1_sil_median_ge_incumbent'] else '×'} | {'○' if r['G2_jaccard_ge_0.35'] else '×'} | {'○' if r['G3_M_consensus'] else '×'} | **{'통과' if r['v2_pass'] else '기각'}** |")
passed = [k for k, r in rows.items() if r["v2_pass"]]
inc = rows[INCUMBENT]
md.append(f"\n현직으로 삼은 {INCUMBENT} 자체가 G3을 {'통과한다' if inc['G3_M_consensus'] else '통과하지 못한다'}: 시드별 최적 M 최빈값이 {inc['best_M_mode']}이고 M=5 중앙값 {inc['M5_median']}은 최적 M 중앙값의 {round(inc['M5_median'] / res[INCUMBENT]['silhouette_best_M']['median'] * 100)}%다. 즉 해석 계층의 M=5(페르소나 5개 F)는 시드 합의가 아니라 seed 0의 선택이었다.")
md.append(f"\nv1로는 네 적합 모두, 어느 시드로도 기각이다. v2로는 {', '.join(passed) if passed else '없음'} 이 통과한다. 통과의 뜻은 '현직(재현 가능한 기준)보다 나쁘지 않고 시드에 대해 안정적'이지, 좋은 군집이라는 뜻은 아니다(실루엣 0.1 수준은 여전히 약한 구조).\n")
md.append("## 3. 이원 구조에 대한 함의\n1. v2를 채택하면 라이브 K=8(시드 중앙값 0.102, 최빈 M=5)이 해석 계층 후보가 되고, 동결 스냅샷은 '재현되지 않는 역사 값'으로 표기해 보관한다. 상위 15 순위표·페르소나는 라이브로 다시 계산해야 하며, 그 값은 동결 값과 다를 것이다(L10·L12: 점수가 건수 구조에 좌우됨).\n2. v2를 채택하지 않으면 현 이원 구조가 남는다. 그 경우에도 0.267을 '기준선'이 아니라 '그 시점의 한 번 값'으로 표기하는 것은 필요하다(이미 README·게이트 정책 문서에 반영).\n3. 어느 쪽이든 게이트 판정 로그에는 시드별 실루엣·Jaccard·최적 M을 남긴다. `build_seed_stability_v7.py`가 그 형식이다.\n")
md.append("## 4. 한계\n1. G1의 현직 기준을 동결 근사 재적합으로 옮기는 것은 '재현 가능성'을 위해 기준을 낮추는 선택이다. 대안은 기준을 두지 않고 G2·G3만으로 안정성을 판정하는 것이다.\n2. 임계값 0.35(G2)·90%(G3)는 측정된 네 적합에서 정한 값이라 다른 코퍼스에서는 재조정이 필요하다.\n3. 페르소나 배정 일치율(시드 간)은 seed_stability에 저장하지 않아 이번 판정에 넣지 못했다. 다음 라운드에 추가한다.\n")
md.append("## 5. 파일\n| 파일 | 내용 |\n|---|---|\n| `gate_policy_v2_decisions_v7.json` | v1·v2 규칙과 네 적합의 판정 |\n| `gate_policy_v2_v7.py` | 이 문서를 만드는 스크립트 (입력: `../analysis/persona_decision_space/topic_phi_cosine/seed_stability/seed_stability_summary_v7.json`) |\n")
(HERE / "GATE_POLICY_V2_PROPOSAL_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
for k, r in rows.items(): print(k, "v1", r["v1_pass(seed0 ≥ 0.267)"], "G1", r["G1_sil_median_ge_incumbent"], "G2", r["G2_jaccard_ge_0.35"], "G3", r["G3_M_consensus"], "v2", r["v2_pass"])
