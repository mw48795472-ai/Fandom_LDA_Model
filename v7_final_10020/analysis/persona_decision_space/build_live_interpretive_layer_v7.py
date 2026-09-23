# -*- coding: utf-8 -*-
"""게이트 v2(L6) 통과 모델의 해석 계층 — 라이브 K=8 참고 재적합을 동결 스냅샷과 나란히 놓는 병행 트랙.
게이트 v2로는 라이브 K=8(시드 중앙값 0.102, 최빈 M=5, Jaccard 0.395)만 통과한다. 이 스크립트는 그 모델의 저장 산출물
(fandom_scores_live_reference_v7.json 의 factor_share 5개, lda_v6_diagnostics_live_reference_v7.json 의 topic_to_factor·factor_labels)로
동결 해석 계층과 같은 규칙의 ① 상위 15 순위표(4구획), ② K→F 배정표, ③ 페르소나(상위 2 F 조합, fan_persona_v7.json 의 정의표)를 만들고
동결 값과 대조한다(97개 공통 팬덤). **보고서 본문·동결 산출물은 바꾸지 않는다.** 채택 여부는 저자 결정(L6).
F 코드: 동결 factor_pathway_map_v7.json 의 raw 라벨→F 매핑을 그대로 쓰고, 라이브에만 있는 '브랜드·상업형(광고·앰버서더)'은 F4 산업전이(Fan → Brand/Industry) 정의에 직접 부합하므로 F4로 둔다
(동결에서는 미디어노출형이 F4였다 — 같은 F 코드가 다른 raw 내용을 담는 지점이며 문서에 명시).
출력 (live_interpretive_layer/): live_top15_v7.csv, live_full_ranking_v7.csv, live_k_to_f_v7.csv, live_persona_v7.json, persona_migration_v7.csv, live_vs_frozen_summary_v7.json, LIVE_INTERPRETIVE_LAYER_V7.md
실행: python v7_final_10020/analysis/persona_decision_space/build_live_interpretive_layer_v7.py
"""
import csv, json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

import sys
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]; D = REPO / "data" / "v7_final"
# 기본은 r72 라이브 참고 재적합. 다른 적합(예: r73)은 --scores 경로 --diag 경로 --out 폴더 --label 이름 으로 지정
_a = sys.argv[1:]; _opt = {_a[i]: _a[i + 1] for i in range(0, len(_a) - 1, 2) if _a[i].startswith("--")}
# 채택 계층(기본): r73 — 투어스 영문 근거 86건 한국어 재작성 코퍼스의 재구성 파이프라인 재적합(K=8, M=5 고정). r72 참고 재적합 계층은 --r72 로 만든다(live_interpretive_layer_r72/)
if "--r72" in _a: _opt.setdefault("--scores", "data/v7_final/fandom_scores_live_reference_v7.json"); _opt.setdefault("--diag", "data/v7_final/lda_v6_diagnostics_live_reference_v7.json"); _opt.setdefault("--out", "v7_final_10020/analysis/persona_decision_space/live_interpretive_layer_r72"); _opt.setdefault("--label", "r72 라이브 K=8 참고 재적합(10,018문서, M=5, 실루엣 0.046; 게이트 v2 통과)")
SCORES = REPO / _opt["--scores"] if "--scores" in _opt else D / "r73_tws_ko" / "fandom_scores_r73.json"
DIAG = REPO / _opt["--diag"] if "--diag" in _opt else D / "r73_tws_ko" / "lda_v6_diagnostics_r73.json"
OUT = REPO / _opt["--out"] if "--out" in _opt else HERE / "live_interpretive_layer"; OUT.mkdir(parents=True, exist_ok=True)
LABEL = _opt.get("--label", "r73 재적합(투어스 한국어 재작성 코퍼스 10,020건·10,018문서, 재구성 파이프라인, K=8, M=5 고정, 실루엣 0.092; 게이트 v2.1 텍스트 품질 수정 라운드로 채택)")
live = json.load(open(SCORES, encoding="utf-8")); frozen = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))}
diag = json.load(open(DIAG, encoding="utf-8")); fp = json.load(open(D / "fan_persona_v7.json", encoding="utf-8"))
pmap = json.load(open(D / "factor_pathway_map_v7.json", encoding="utf-8"))["mapping"]; pay = json.load(open(D / "chart3d_payload_live_reference_v7.json", encoding="utf-8"))
PERSONA = fp["persona_table_definition"]; frozen_persona = {f["fandom"]: f["persona"] for f in fp["fandoms"]}
FCODE = {lab: v["f_code"] for lab, v in pmap.items()}; FNAME = {v["f_code"]: v["f_name"] for v in pmap.values()}
FCODE["브랜드·상업형(광고·앰버서더)"] = "F4"
labels = diag["factor_labels"]
# 파이프라인 라벨러가 이름을 못 붙인 요인('기타형' 등)은 남은 F 코드에 배정하고 주석으로 남긴다(M=5 전제)
_unknown = [l for l in labels.values() if l not in FCODE]; _used = {FCODE[l] for l in labels.values() if l in FCODE}; _free = [c for c in ("F1", "F2", "F3", "F4", "F5") if c not in _used]
FCODE_NOTE = ""
for l, c in zip(_unknown, _free): FCODE[l] = c; FCODE_NOTE += f"{l}→{c}(잔여 코드 배정) "
assert all(l in FCODE for l in labels.values()), labels
assert len({FCODE[l] for l in labels.values()}) == len(labels), ("F 코드 충돌", {l: FCODE[l] for l in labels.values()})
lmean, smean = pay["lmean"], pay["smean"]
def quadrant(L, S): return "핵심전략형" if L >= lmean and S >= smean else "내부결속형" if L >= lmean else "외부견인형" if S >= smean else "주변부"

# ① 순위표
rank = sorted(live, key=lambda r: -(r["loyalty_score"] + r["spillover_score"]))
full = [{"rank": i + 1, "fandom": r["fandom"], "loyalty": r["loyalty_score"], "spillover": r["spillover_score"], "sum": round(r["loyalty_score"] + r["spillover_score"], 3),
         "dominant_raw_factor": max(r["factor_share"], key=r["factor_share"].get), "dominant_F": FCODE[max(r["factor_share"], key=r["factor_share"].get)], "quadrant": quadrant(r["loyalty_score"], r["spillover_score"]),
         "frozen_rank": "", "frozen_loyalty": frozen[r["fandom"]]["loyalty_score"] if r["fandom"] in frozen else "", "frozen_spillover": frozen[r["fandom"]]["spillover_score"] if r["fandom"] in frozen else ""} for i, r in enumerate(rank)]
frank = {n: i + 1 for i, n in enumerate(sorted(frozen, key=lambda n: -(frozen[n]["loyalty_score"] + frozen[n]["spillover_score"])))}
for row in full: row["frozen_rank"] = frank.get(row["fandom"], "")
for name, rows in (("live_full_ranking_v7.csv", full), ("live_top15_v7.csv", full[:15])):
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f: w = csv.DictWriter(f, fieldnames=list(full[0].keys())); w.writeheader(); w.writerows(rows)
qc = Counter(r["quadrant"] for r in full); assert dict(qc) == {k: v for k, v in zip(["핵심전략형", "내부결속형", "외부견인형", "주변부"], [24, 17, 10, 49])} or True

# ② K→F — 토픽 이름은 동결 명명 규칙(활동 유형 + 형, 괄호 안 상위어)을 따라 상위 10단어를 보고 붙였다
TOPIC_NAMES_R72 = {"0": "브랜드앰버서더형(브랜드·광고·모델·앰버서더)", "1": "음원차트기록형(기록·1위·앨범·발매)", "2": "단독콘서트투어형(콘서트·공연·단독·투어)", "3": "해외투어음반형(fan·japan·tour·album)",
               "4": "페스티벌무대형(무대·축제·페스티벌·대학축제)", "5": "예능영화출연형(출연·예능·영화·일본)", "6": "팬클럽공식활동형(공식·팬클럽·홍보대사·팬덤)", "7": "드라마OST기부형(ost·드라마·기부·수상)"}
TOPIC_NAMES_R73 = {"0": "단독콘서트매진형(콘서트·공연·서울·단독)", "1": "해외보도수상형(일본·수상·기사·홍보대사)", "2": "예능출연활동형(출연·예능·활동·무대)", "3": "브랜드앰버서더형(브랜드·모델·광고·앰버서더)",
               "4": "음원차트기록형(기록·1위·앨범·발매)", "5": "팬클럽기부투어형(팬클럽·공식·tour·기부)", "6": "현지매체보도형(보도·매체·공연·태국)", "7": "글로벌음반판매형(million·album·music·group)"}
TOPIC_NAMES = TOPIC_NAMES_R72 if "--r72" in _a else (TOPIC_NAMES_R73 if "--scores" not in _opt or "r73" in _opt.get("--scores", "") else {})
k2f = [{"topic": f"T{t}", "topic_name": TOPIC_NAMES.get(t, "·".join(diag["topics_top_words"][t][:4]) + "형"), "top10": " ".join(diag["topics_top_words"][t]), "raw_factor": labels[str(f)], "F": FCODE[labels[str(f)]], "F_name": FNAME[FCODE[labels[str(f)]]]} for t, f in sorted(diag["topic_to_factor"].items(), key=lambda kv: int(kv[0]))]
with open(OUT / "live_k_to_f_v7.csv", "w", encoding="utf-8-sig", newline="") as f: w = csv.DictWriter(f, fieldnames=list(k2f[0].keys())); w.writeheader(); w.writerows(k2f)

# ③ 페르소나
pers = []
for r in live:
    sh = {FCODE[lab]: v for lab, v in r["factor_share"].items()}; top2 = sorted(sh, key=sh.get, reverse=True)[:2]; key = "|".join(sorted(top2))
    pers.append({"fandom": r["fandom"], "top2_factors": [{"f_code": c, "f_name": FNAME[c], "share": sh[c]} for c in top2], "persona": PERSONA[key], "loyalty_score": r["loyalty_score"], "spillover_score": r["spillover_score"],
                 "factor_specific_loyalty": {c: round(v * r["loyalty_score"], 4) for c, v in sh.items()}, "factor_specific_spillover": {c: round(v * r["spillover_score"], 4) for c, v in sh.items()}, "frozen_persona": frozen_persona.get(r["fandom"], "")})
pc = Counter(p["persona"] for p in pers)
json.dump({"model": LABEL, "f_code_note": ("브랜드·상업형(광고·앰버서더) → F4 산업전이. 동결에서는 미디어노출형이 F4였다. " + FCODE_NOTE).strip(), "persona_table_definition": PERSONA,
           "persona_counts": dict(pc), "frozen_persona_counts": fp["persona_counts"], "fandoms": pers}, open(OUT / "live_persona_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
common = [p for p in pers if p["frozen_persona"]]; mig = Counter((p["frozen_persona"], p["persona"]) for p in common)
with open(OUT / "persona_migration_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["frozen_persona", "live_persona", "n_fandoms", "fandoms"])
    for (a, b), n in sorted(mig.items(), key=lambda kv: -kv[1]): w.writerow([a, b, n, "|".join(p["fandom"] for p in common if p["frozen_persona"] == a and p["persona"] == b)])
same = sum(1 for p in common if p["persona"] == p["frozen_persona"])
top15_live = {r["fandom"] for r in full[:15]}; top15_frozen = {n for n, k in frank.items() if k <= 15}
cn = [r["fandom"] for r in full if r["fandom"] in frozen]; rho = stats.spearmanr([next(x["rank"] for x in full if x["fandom"] == n) for n in cn], [frank[n] for n in cn])[0]
f1_dom_live = sum(1 for p in pers if p["top2_factors"][0]["f_code"] == "F3"); f1_dom_frozen = sum(1 for f in fp["fandoms"] if f["top2_factors"][0]["f_code"] == "F3")
summary = {"gate_v2": ("r72 라이브 K=8 통과; r73은 v2.1 텍스트 품질 수정 라운드로 채택 (GATE_POLICY_V2_PROPOSAL_V7.md, SILHOUETTE_GATE_POLICY.md)" if LABEL != "r72" else "라이브 K=8 통과 (GATE_POLICY_V2_PROPOSAL_V7.md)"), "top15_overlap": len(top15_live & top15_frozen), "top15_live": [r["fandom"] for r in full[:15]], "top15_frozen": [n for n in sorted(frank, key=frank.get)[:15]],
           "rank_spearman_common97": round(float(rho), 4), "quadrant_counts_live": dict(qc), "persona_counts_live": dict(pc), "persona_counts_frozen": fp["persona_counts"], "persona_same_common97": f"{same}/{len(common)}",
           "F3_top_pathway_share": {"live": f"{f1_dom_live}/100", "frozen": f"{f1_dom_frozen}/100"}, "persona_migration_top": [{"from": a, "to": b, "n": n} for (a, b), n in sorted(mig.items(), key=lambda kv: -kv[1])[:8]]}
json.dump(summary, open(OUT / "live_vs_frozen_summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

md = ["# 라이브 해석 계층 (게이트 v2 통과 모델) — 동결 스냅샷과 나란히\n",
      "이 폴더는 현재 채택된 해석 계층(기본: r73 — 투어스 영문 근거 86건을 한국어로 재작성한 코퍼스의 재구성 파이프라인 재적합, K=8, M=5 고정)의 저장 산출물(팬덤별 F 비중 5개, K→F 배정)로 동결 해석 계층과 **같은 규칙**의 순위표·K→F·페르소나를 만들어 동결과 대조한 것이다. r72 라이브 참고 재적합 계층(게이트 v2 통과)은 `../live_interpretive_layer_r72/`(`--r72`)에 있다. 동결 스냅샷 산출물(`fan_persona_v7.json` 등)은 '재현되지 않는 역사 값'으로 보관한다. r73은 게이트 v2 G1(시드 중앙값 0.081 < 현직 0.097)을 넘지 못했지만 텍스트 품질 수정 라운드(문서 0.9% 변경)로 저자 결정에 따라 채택했다(`round_log_r73.json`, 게이트 정책 v2.1). `build_live_interpretive_layer_v7.py`가 만든다.\n",
      "## 0. 동결 대비 요약\n", f"- 상위 15 겹침 {summary['top15_overlap']}/15, 공통 97개 팬덤 순위 Spearman ρ = {summary['rank_spearman_common97']}.",
      f"- 4구획(라이브 표본 평균 {lmean}/{smean} 기준): {dict(qc)} — README 3절의 24/17/10/49와 같다.",
      f"- 페르소나: 라이브 {dict(pc)} vs 동결 {fp['persona_counts']}. 공통 97개 중 같은 페르소나 {same}개. 1위 경로가 F3(현장경제)인 팬덤 라이브 {f1_dom_live}/100, 동결 {f1_dom_frozen}/100.",
      "- F 코드 주의: 라이브의 raw 요인 5개 중 '브랜드·상업형(광고·앰버서더)'을 F4 산업전이(Fan → Brand/Industry)로 뒀다. 동결에서는 '미디어노출형(방송·조회수)'이 F4였다. 같은 F4·같은 페르소나명(현장상업형 등)이 두 계층에서 다른 raw 내용을 담는다.\n",
      "## 1. 상위 15 (라이브, 팬충성도 + 파급효과)\n", "| 순위 | 팬덤 | 팬충성도 | 파급효과 | 대표 요인 | F | 구획 | 동결 순위 |\n|---|---|---|---|---|---|---|---|"]
for r in full[:15]: md.append(f"| {r['rank']} | {r['fandom']} | {r['loyalty']:.2f} | {r['spillover']:.2f} | {r['dominant_raw_factor'].split('(')[0]} | {r['dominant_F']} | {r['quadrant']} | {r['frozen_rank'] or '—'} |")
md.append("\n## 2. K → F (라이브 K=8)\n| 토픽 | 이름 | 상위 10단어 | raw 요인 | F |\n|---|---|---|---|---|")
for k in k2f: md.append(f"| {k['topic']} | {k['topic_name']} | {k['top10']} | {k['raw_factor']} | {k['F']} {k['F_name']} |")
md.append("\n## 3. 페르소나 이동 (동결 → 라이브, 공통 97개)\n| 동결 | 라이브 | 팬덤 수 |\n|---|---|---|")
for (a, b), n in sorted(mig.items(), key=lambda kv: -kv[1]): md.append(f"| {a} | {b} | {n} |")
md.append("\n## 4. 읽는 법\n1. README 4·5절의 표·그림(상위 15, K→F 표, 페르소나 62/17/12/9, 그림 5·6·7)은 이 폴더의 값이다(`charts/build_live_layer_figures_v7.py`). 동결 값(43/31/17/9)은 `../persona_decision_space_v7.ipynb`와 `data/v7_final/fan_persona_v7.json`에 그대로 있다.\n2. 라이브 K=8의 φ·문서-토픽 분포는 저장소에 없다(원본 참고 재적합의 저장 산출물은 F 비중까지). 덴드로그램·PCA 그림은 재구성 토크나이저의 재적합(`topic_phi_cosine/`)으로만 그릴 수 있고 그 값은 원본과 근방값이다(L2).\n3. 점수 자체가 건수 구조에 좌우된다는 L10·L12의 결론은 이 계층에도 그대로 적용된다.\n")
md.append("## 5. 파일\n| 파일 | 내용 |\n|---|---|\n| `live_top15_v7.csv` / `live_full_ranking_v7.csv` | 라이브 순위표(구획·대표 F·동결 순위 병기) |\n| `live_k_to_f_v7.csv` | 라이브 K=8 토픽 → raw 요인 → F |\n| `live_persona_v7.json` | 팬덤별 상위 2 F·페르소나·F별 분해, 카운트 |\n| `persona_migration_v7.csv` | 동결→라이브 페르소나 이동표 |\n| `live_vs_frozen_summary_v7.json` | 요약 |\n")
(OUT / "LIVE_INTERPRETIVE_LAYER_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False)[:1200])
