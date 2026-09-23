# -*- coding: utf-8 -*-
"""frozen_v7_40/FROZEN_MODEL_REFIT_V7_40.md 를 대조 결과 JSON에서 생성한다 (수치를 손으로 옮기지 않기 위해).
  입력: frozen_v7_40/frozen_refit_comparison_v7_40.json (최종 토크나이저 설정), frozen_refit_comparison_v7_40_r40tok.json (r40 시점 설정),
        frozen_v7_40/lda_v6_diagnostics_frozen_refit_v7_40.json (run_lda_v6_live_reference_v7.py 를 근사 코퍼스에 돌린 K-grid, 있으면)
실행: python build_frozen_bundle_md_v7_40.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "frozen_v7_40"
REPO = HERE.parents[3]
C = json.load(open(OUT / "frozen_refit_comparison_v7_40.json", encoding="utf-8"))
C40 = json.load(open(OUT / "frozen_refit_comparison_v7_40_r40tok.json", encoding="utf-8"))
fdiag = json.load(open(REPO / "data/v7_final/lda_v6_diagnostics_frozen_v7_40.json", encoding="utf-8"))
pipe_p = OUT / "lda_v6_diagnostics_frozen_refit_v7_40.json"
P = json.load(open(pipe_p, encoding="utf-8")) if pipe_p.exists() else None
F, R = C["frozen_reference"], C["reconstruction"]

md = []
md.append("# 동결 스냅샷(v7-40) 모델 근방 재현 시도 — `frozen_v7_40/`\n")
md.append("## 0. 결론부터\n")
md.append(f"근사 복원 코퍼스(7,326/7,350건)와 재구성 라우팅 토크나이저로 K=10을 다시 적합했다. **동결 스냅샷의 핵심값(M=5 실루엣 {F['silhouette']})은 재현되지 않았다** — "
          f"같은 M=5에서 실루엣 {R['m5_silhouette']}, 최적 M은 {R['best_m']}(실루엣 {R['best_silhouette']})이다. 토픽은 10개 중 {C['topic_alignment_summary']['overlap_ge8']}개가 상위 10단어 8개 이상, "
          f"{C['topic_alignment_summary']['overlap_ge5']}개가 5개 이상 겹치고(평균 {C['topic_alignment_summary']['mean_overlap']}), 팬덤별 F 비중은 일부 F에서만 상관이 높다(3절).\n")
md.append("그래서 이 폴더의 모델 묶음은 **동결 모델의 대체물이 아니라 '재구성 입력으로는 여기까지 온다'는 기록**이다. 보고서 해석 계층(K=10→M=5, 실루엣 0.267, 페르소나 43/31/17/9)은 "
          "여전히 `data/v7_final/`의 저장된 동결 값을 그대로 쓴다. 원 저자도 동기화된 코드로 동결 스냅샷 재현을 시도해 10개 토픽 중 0개가 일치했다고 기록했다"
          "(`tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` 6절) — 이번 시도는 그보다는 가깝지만 같은 결론에 닿는다.\n")

md.append("## 1. 입력과 설정\n")
md.append("| 항목 | 값 |\n|---|---|")
md.append(f"| 코퍼스 | `{C['corpus']['file']}` {C['corpus']['n_bullets']:,}건 → 3토큰 이상 문서 {C['corpus']['n_docs']:,}건, 어휘 {C['corpus']['n_vocab']:,} |")
md.append("| 토크나이저 | `run_lda_v6_live_reference_v7.py`의 마커 절(재구성본, 최종 시점 설정) |")
md.append("| 벡터라이저·LDA | `CountVectorizer(max_df=0.6, min_df=2)`, `LatentDirichletAllocation(n_components=10, random_state=0, max_iter=50, batch)` — 파이프라인과 동일 |")
md.append("| 대조 대상 | `lda_v6_diagnostics_frozen_v7_40.json`(토픽 상위 10단어·토픽→F), `persona_decision_space_v7.json`(병합 높이·절단 높이·실루엣), `fandom_scores_v6.json`(F 비중·다양성) |\n")

md.append("## 2. 군집 구조 대조\n")
md.append("| 구분 | 동결 스냅샷 | 재구성(최종 토크나이저) | 재구성(r40 시점 토크나이저) |\n|---|---|---|---|")
R40 = C40["reconstruction"]
md.append(f"| M=5 실루엣 | {F['silhouette']} | {R['m5_silhouette']} | {R40['m5_silhouette']} |")
md.append(f"| 최적 M / 실루엣 | 5 / {F['silhouette']} | {R['best_m']} / {R['best_silhouette']} | {R40['best_m']} / {R40['best_silhouette']} |")
md.append(f"| 절단 높이(M=5) | {F['cut_height']:.4f} | {R['m5_cut_height']} | {R40['m5_cut_height']} |")
md.append(f"| 병합 높이(오름차순) | {F['merge_heights']} | {R['merge_heights']} | {R40['merge_heights']} |")
md.append(f"| perplexity | — | {R['perplexity']} | {R40['perplexity']} |")
md.append(f"| 동결에서 같은 F였던 토픽 쌍 {C['m5_cluster_structure']['frozen_same_factor_pairs']}개 중 재구성 M=5에서도 같은 군집 | — | {C['m5_cluster_structure']['also_same_cluster_in_recon']} | {C40['m5_cluster_structure']['also_same_cluster_in_recon']} |\n")
md.append("r40 시점 설정은 v7 76·77 라운드 이전 동작(일본어 불용어 없음, 가나+한자 불릿에 fugashi·jieba 모두 실행, 자기인용 슬러그 제거 없음)으로 되돌린 것이다. "
          "동결 시점이 그 변경들 이전이라는 가설을 시험한 것인데, 결과는 최종 설정보다 오히려 멀다. 그래서 최종 설정의 묶음을 이 폴더에 두고 r40 설정은 대조 JSON만 남겼다.\n")

md.append("## 3. 토픽·F 비중 대조 (최종 토크나이저 설정)\n")
md.append("동결 토픽 K0∼K9 각각에 상위 10단어 겹침이 가장 큰 재구성 토픽을 1:1로 붙였다.\n")
md.append("| 동결 토픽 | 동결 상위어 | 재구성 토픽 | 겹침 | 재구성 상위어 |\n|---|---|---|---|---|")
for a in C["topic_alignment"]:
    md.append(f"| K{a['frozen_topic']} {a['frozen_name']} | {', '.join(a['frozen_words'][:6])} | T{a['recon_topic']} | {a['overlap10']}/10 | {', '.join(a['recon_words'][:6])} |")
md.append("")
md.append("| F (동결 라벨) | 팬덤별 F 비중 Pearson r (100개 팬덤) |\n|---|---|")
for k, v in C["fandom_factor_share"]["pearson_by_factor"].items():
    md.append(f"| {k} | {v if v is not None else '대응 군집 없음'} |")
fd = C["factor_diversity"]
md.append(f"\n팬덤 요인 다양성: r = {fd['pearson']} (평균 {fd['mean_recon']} / 동결 {fd['mean_frozen']}). '대응 군집 없음'은 재구성 M=5 군집 중 어느 것도 다수결로 그 F에 배정되지 않았다는 뜻이다.\n")

if P:
    md.append("## 4. 파이프라인 전체 실행 — K 선택 대조\n")
    md.append("`run_lda_v6_live_reference_v7.py --data …/fandoms_v7_40_frozen_reconstructed.json`으로 K-grid부터 돌린 결과(`lda_v6_diagnostics_frozen_refit_v7_40.json`)와 동결 진단의 K-grid.\n")
    md.append("| K | perplexity 재구성/동결 | coherence | diversity | stability | rank_sum |\n|---|---|---|---|---|---|")
    fg = {g["k"]: g for g in fdiag["k_grid"]}
    for g in P["k_grid"]:
        o = fg.get(g["k"])
        if o:
            md.append(f"| {g['k']} | {g['perplexity']} / {o['perplexity']} | {g['coherence']} / {o['coherence']} | {g['diversity']} / {o['diversity']} | {g['stability']} / {o['stability']} | {g['composite_rank_sum']} / {o['composite_rank_sum']} |")
    md.append(f"\n선택 K = **{P['selected_k']}** (동결 {fdiag['selected_k']}), M = **{P['selected_m_meta_factors']}** (동결 {fdiag['selected_m_meta_factors']}), 실루엣 = **{P['meta_factor_silhouette']}** (동결 {fdiag['meta_factor_silhouette']}).\n")

md.append(f"## {5 if P else 4}. 파일\n")
md.append("| 파일 | 내용 |\n|---|---|")
md.append("| `lda_model_k10_v7_40.pkl`, `count_vectorizer_v7_40.pkl`, `lda_vocabulary_v7_40.csv`, `lda_document_index_v7_40.csv` | 라이브 묶음과 같은 구성의 모델 묶음 (K=10, 최종 토크나이저 설정) |")
md.append("| `lda_phi_k10_v7_40.csv`, `lda_phi_top50_k10_v7_40.csv`, `topic_cosine_distance_k10_v7_40.csv`, `topic_linkage_average_k10_v7_40.csv`, `m_grid_silhouette_k10_v7_40.csv` | φ·코사인 거리·병합 기록·M-grid |")
md.append("| `frozen_refit_comparison_v7_40.json` / `…_r40tok.json` | 동결 값과의 대조 (최종 설정 / r40 시점 설정) |")
if P:
    md.append("| `lda_v6_diagnostics_frozen_refit_v7_40.json` | 파이프라인 전체 실행의 진단(K-grid·선택 K·M·실루엣) |")
md.append("| `frozen_model_bundle_manifest_v7_40.json` | 입력 SHA-256·설정·패키지 버전·파일별 SHA-256 |")
md.append("| `../build_frozen_model_bundle_v7_40.py`, `../build_frozen_bundle_md_v7_40.py` | 이 묶음과 이 문서를 만드는 스크립트 (`--era r40`으로 r40 설정) |\n")

md.append(f"## {6 if P else 5}. 왜 재현되지 않았나 — 가능한 원인\n")
md.append("1. **입력이 원본과 같지 않다.** 코퍼스는 3개 팬덤 24건이 빠져 있고, 토크나이저는 재구성본이라 저빈도 불용어가 다를 수 있다. LDA는 DTM의 작은 차이에도 토픽 경계가 움직인다.\n"
          "2. **동결 스냅샷 자체가 특정 실행의 값이다.** 실루엣 0.267은 시드 하나(random_state=0)의 한 번 적합에서 나온 값이며, 원 저자의 동기화 코드 재현 시도에서도 0/10 토픽이 일치했다. "
          "당시 코퍼스 상태(r39 직후)·토크나이저 판·패키지 버전 중 어느 것이 지금과 다른지 확정할 수 없다.\n"
          "3. **군집 구조는 재현되고 실루엣만 낮을 가능성.** 토픽 3∼4개는 내용이 거의 같고 두 F(현장경제형·차트확산형)의 팬덤별 비중은 r≈0.75∼0.82로 따라온다. 실루엣이 0.267에 못 미치는 것은 "
          "나머지 토픽들이 더 섞여 있기 때문이며, 이는 라이브 재적합(0.046∼0.081)과 같은 방향이다.\n")
md.append("따라서 해석 계층의 수치는 저장된 동결 값을 인용하되 '재현되지 않은 스냅샷 값'이라는 단서를 붙이는 것이 정직하다. 이 폴더의 묶음은 그 단서의 근거다.\n")
(OUT / "FROZEN_MODEL_REFIT_V7_40.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT / "FROZEN_MODEL_REFIT_V7_40.md")
