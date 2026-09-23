# -*- coding: utf-8 -*-
"""재구성 run_lda_v6_live_reference_v7.py 를 최종 코퍼스에 실제로 돌린 산출물(output/lda_live_reference_v7/)을
저장소의 원본 라이브 참고 재적합 결과와 대조한다.

  진단: output/.../lda_v6_diagnostics.json  vs  data/v7_final/lda_v6_diagnostics_live_reference_v7.json
        (K-grid 7개 K 의 perplexity·coherence·diversity·stability, 선택 K·M·실루엣, 토픽 상위어 겹침)
  점수: output/.../fandom_scores_v6.json     vs  data/v7_final/fandom_scores_live_reference_v7.json
        (loyalty_raw/spillover_raw 는 토크나이저와 무관하므로 100/100 이어야 함; factor_share·factor_diversity 는 재적합 결과)

실행: python compare_live_reference_refit_v7.py [output 폴더]   (먼저 python run_lda_v6_live_reference_v7.py 실행, 30분 내외)
출력: 같은 폴더 live_reference_refit_comparison_v7.json + 콘솔 표
"""
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "output" / "lda_live_reference_v7"
D = REPO / "data" / "v7_final"

diag_r = json.load(open(OUT / "lda_v6_diagnostics.json", encoding="utf-8"))
diag_o = json.load(open(D / "lda_v6_diagnostics_live_reference_v7.json", encoding="utf-8"))
sc_r = {r["fandom"]: r for r in json.load(open(OUT / "fandom_scores_v6.json", encoding="utf-8"))}
sc_o = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8"))}

rows = []
go = {g["k"]: g for g in diag_o["k_grid"]}
for g in diag_r["k_grid"]:
    o = go.get(g["k"])
    if not o:
        continue
    rows.append({"k": g["k"], **{m: [g[m], o[m], round(g[m] - o[m], 3)] for m in ("perplexity", "coherence", "diversity", "stability")},
                 "composite_rank_sum": [g.get("composite_rank_sum"), o.get("composite_rank_sum")]})
sel = {"selected_k": [diag_r["selected_k"], diag_o["selected_k"]], "selected_m": [diag_r["selected_m_meta_factors"], diag_o["selected_m_meta_factors"]],
       "silhouette": [diag_r["meta_factor_silhouette"], diag_o["meta_factor_silhouette"]]}
# 토픽 상위어 겹침 (번호는 적합마다 바뀌므로 최적 대응으로)
tr = {int(k): v for k, v in diag_r["topics_top_words"].items()}; to = {int(k): v for k, v in diag_o["topics_top_words"].items()}
align = []
for k, words in to.items():
    best = max(tr.items(), key=lambda kv: len(set(kv[1]) & set(words)))
    align.append({"orig_topic": k, "orig_words": words[:6], "best_recon_topic": best[0], "overlap10": len(set(best[1]) & set(words)), "recon_words": best[1][:6]})
raw_ok = sum(1 for f in sc_o if f in sc_r and abs(sc_r[f]["loyalty_raw"] - sc_o[f]["loyalty_raw"]) < 1e-6 and abs(sc_r[f]["spillover_raw"] - sc_o[f]["spillover_raw"]) < 1e-6)
fd_r = np.array([sc_r[f]["factor_diversity"] for f in sc_o if f in sc_r]); fd_o = np.array([sc_o[f]["factor_diversity"] for f in sc_o if f in sc_r])
fd_corr = float(np.corrcoef(fd_r, fd_o)[0, 1]) if len(fd_r) > 2 else None
dom_ok = sum(1 for f in sc_o if f in sc_r and sc_r[f].get("dominant_factor") == sc_o[f].get("dominant_factor"))
res = {"k_grid": rows, "selection": sel, "topic_alignment": align, "scores": {"loyalty_spillover_raw_match": [raw_ok, len(sc_o)],
       "factor_diversity_pearson": fd_corr, "factor_diversity_mean": [round(float(fd_r.mean()), 4), round(float(fd_o.mean()), 4)], "dominant_factor_label_match": [dom_ok, len(sc_o)]}}
json.dump(res, open(HERE / "live_reference_refit_comparison_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("K-grid (재구성 / 원본 / 차이)")
for r in rows:
    print(f"  K={r['k']:>2}  perp {r['perplexity'][0]:.1f}/{r['perplexity'][1]:.1f} ({r['perplexity'][2]:+.1f})  coh {r['coherence'][0]:.3f}/{r['coherence'][1]:.3f} ({r['coherence'][2]:+.3f})  div {r['diversity'][0]:.3f}/{r['diversity'][1]:.3f}  stab {r['stability'][0]:.3f}/{r['stability'][1]:.3f}  rank {r['composite_rank_sum']}")
print("선택:", sel)
print("토픽 대응(원본 토픽 → 가장 가까운 재구성 토픽, 상위10 겹침):")
for a in align:
    print(f"  T{a['orig_topic']} {a['orig_words']} → T{a['best_recon_topic']} ({a['overlap10']}/10) {a['recon_words']}")
print("점수:", res["scores"])
