# 이 프로젝트에 적용된 파이썬 코드 총정리

이 저장소에 들어 있는 파이썬 스크립트·노트북 전체를 정리한다. 모든 코드는 최종 근거 코퍼스
10,020건(`data/v7_final/fandoms_v3_100.json`)과 그로부터 산출된 최종 파일(`data/v7_final/`),
그리고 해석 계층의 동결 스냅샷(v7-40, 7,350건)을 입력으로 삼으며, 각 스크립트는 실행 후
원본 JSON의 집계값과 대조하는 자체 검증 루틴을 포함한다(전부 통과 확인됨).

경로 규칙: 모든 스크립트는 `Path(__file__).resolve().parents[N]`으로 저장소 루트를 찾아
`data/v7_final/`을 읽고, 생성물은 `output/` 아래(또는 `data/v7_final/`의 파생 CSV)에 쓴다.
`analysis/` 노트북은 `data/v7_final/fandoms_v3_100.json`이 있는 상위 폴더를 루트로 잡으므로
어느 위치에서 실행해도 된다.

## 한눈에 보기

| 분류 | 스크립트 | 입력 | 출력·확인 |
|---|---|---|---|
| 정합성 검증(루트) | `verify_v7_final_consistency.py` | `data/v7_final/*` 전부 | 보고서·KEY_FINDINGS 수치 107개 항목을 파일에서 재계산해 일치/불일치 출력 (107/107; [AD]절 4항목이 동결 코퍼스 근사 복원본 검증) |
| 토크나이저 재구성 검증 ①② | `v7_final_10020/analysis/tokenizer/live_reference_tokenizer/verify_tokenizer_reconstruction_v7.py` | `run_lda_v6_live_reference_v7.py`의 토크나이저 절(마커 exec), 코퍼스 10,020건, `wordcloud_by_language_v7.json`, `lda_excluded_bullets_v7.json` | 문서 수·제외 2건·8개 버킷 통계·상위 30단어 카운트·자기인용 건수 대조 → `tokenizer_reconstruction_check_v7.json` (약 20초, wordfreq 필요) |
| 토크나이저 재구성 검증 ③ | 같은 폴더 `compare_live_reference_refit_v7.py` | `output/lda_live_reference_v7/` 산출물, `lda_v6_diagnostics_live_reference_v7.json`, `fandom_scores_live_reference_v7.json` | K-grid 7개 K 지표·선택 K/M/실루엣·토픽 상위어 대응·factor_diversity 상관 → `live_reference_refit_comparison_v7.json` |
| 토크나이저 재구성 문서 | 같은 폴더 `build_tokenizer_reconstruction_md_v7.py` | 위 두 JSON | `TOKENIZER_RECONSTRUCTION_V7.md` |
| 동결 모델 근방 재현 | `v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_frozen_model_bundle_v7_40.py` (`--era r40`) | 근사 코퍼스 7,326건, `run_lda_v6_live_reference_v7.py`의 토크나이저 절(마커 exec), 동결 진단·덴드로그램·점수 JSON | K=10 적합 → `frozen_v7_40/`에 라이브와 같은 구성의 모델 묶음(pickle·φ·코사인·병합·M-grid·manifest) + 동결 값 대조 JSON. 결과: M=5 실루엣 0.07(동결 0.267) — 재현되지 않음 (약 2분) |
| 동결 모델 근방 재현 문서 | 같은 폴더 `build_frozen_bundle_md_v7_40.py` | 위 대조 JSON 2개(최종·r40 설정) + 파이프라인 진단 | `frozen_v7_40/FROZEN_MODEL_REFIT_V7_40.md` |
| 동결 코퍼스 검사기 | `data/v7_final/frozen_snapshot_v7_40/verify_frozen_corpus_candidate.py` | 후보 코퍼스 JSON (인자 없으면 같은 폴더의 근사 복원본), `fandom_scores_v6.json`, r22 백업 zip, `verify_v7_final_consistency.py`의 EvidenceScore(ast) | 7항목 판정(구조·총 7,350·로스터·팬덤별 건수·EvidenceScore 지문 100/100·activity) + 라이브·r22 포함 관계 참고치. 근사 복원본은 3/7(97개 팬덤 지문 일치) |
| 파이프라인(루트) | `run_lda_v6.py` | 코퍼스 JSON (`--data`, 기본 `fandoms_v3_100.json`) | `output/lda_rerun/` — 토큰화→LDA K 탐색→K→M 재군집화→실루엣 게이트→점수·페르소나 |
| 차트 | `v7_final_10020/charts/build_cohesion_index_v7.py` | `fandom_cohesion_index_v7.json` | 팬덤결속 지수 좌우 2패널 PNG/SVG (`output/charts/`) |
| 차트 | `v7_final_10020/charts/build_cohesion_index_v7_right_only.py` | 〃 | 우측 패널(상위 25개 팬덤) 단독 PNG/SVG |
| 차트 | `v7_final_10020/charts/build_aux_indices_100_v7.py` | 보조지표 JSON 7종(광고·미디어 노출·결속·크로스오버·국내 지역·MCI·세계 언어) | 100개 팬덤 전체(MCI는 45개 그룹) 그래프 7장 → `assets/readme/100개_보조지표/` (README 6절의 상위 20·25 그림의 전체판, 1~50위/51~100위 두 패널·x축 공유) |
| 차트 | `v7_final_10020/charts/build_persona_map_v7.py` | `fandom_scores_v6.json`, `fan_persona_v7.json` (동결 스냅샷) | Fan Persona Map(팬충성도×파급효과, 페르소나 4유형 색) PNG 2종 — 강조 표시 있음/없음 |
| 차트 | `v7_final_10020/charts/build_persona_cluster_split_boxed.py` | `persona_decision_space_v7.json`(HTML 내장 병합 기록·shares; 동결 코사인 거리 행렬 파일 `topic_cosine_distance_frozen_v7_40.json`이 나중에 생기면 그것을 우선 — 원본 묶음에는 없음)·`fan_persona_v7.json` (동결 스냅샷) | 덴드로그램 PNG + PCA biplot PNG (2개 분리) |
| 차트 | `v7_final_10020/silhouette_gate_policy/build_silhouette_gate_timeline_v7.py` | `data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv` | 코퍼스 규모 vs 실루엣 이중축 타임라인 PNG/SVG, 게이트 구간 20회 기각·r=+0.15 자체 재계산 |
| 지수 CSV | `v7_final_10020/indices_csv/build_ad_commercial_index_csv.py` | `ad_commercial_index_v7.json` | `output/indices_csv/ad_commercial_index_v7.csv` |
| 지수 CSV | `v7_final_10020/indices_csv/build_domestic_regional_index_csv.py` | `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json` | `output/indices_csv/domestic_regional_index_v7.csv` |
| 지수 CSV | `v7_final_10020/indices_csv/build_worldwide_language_index_csv.py` | `worldwide_language_pilot_live_reference_v7.json` | `output/indices_csv/worldwide_language_index_v7.csv` |
| 데이터 export | `v7_final_10020/data_export/extract_html_payloads.py` | `3D_포지셔닝맵_국내100팬덤.html`, `Persona_결정공간.html` | HTML 내장 데이터 객체를 그대로 복사 → `chart3d_payload_live_reference_v7.json`, `persona_decision_space_v7.json` |
| 데이터 export | `v7_final_10020/data_export/build_roster_history_v7.py` | `data/v7_rounds/swap_log_r29·r34·r62·r63.json`, `merge_log_r58.json`, 라이브 코퍼스, 동결 점수 JSON | `data/v7_final/roster_history_v7.csv` 106행 (라이브 100 + 제거 6, 진입·제거 라운드·교체 상대·동결/라이브 포함) |
| 데이터 export | `v7_final_10020/data_export/build_bullet_provenance_v7.py` | `archive/v7_r13_corpus_5099.json`, `archive/v6_r22_era_backup.zip`의 r22 코퍼스, 동결 근사 복원본, 라이브 코퍼스, `roster_history_v7.csv` | `data/v7_final/bullet_provenance_v7.csv` 10,020행 — 불릿별 추가 라운드 구간(≤r13 / r14∼r22 / r23∼r39 / r41∼r72, 교체 진입 팬덤은 진입 라운드 하한). 구간 누적 합 = 스냅샷 건수 3/3 일치, 접두어 위반 0(여자친구 r56 수정 1건 허용) |
| 누락 검수 표본 | `v7_final_10020/analysis/build_unmatched_audit_samples_v7.py` | 코퍼스, 광고·미디어 지수 JSON(사전), `build_notebooks_v7.py`의 REGION_KEYWORDS·NEGATION | `analysis/unmatched_audit/` — 지표 3종 매칭 재현(광고 1,308 vs 원본 1,302, 미디어 1,025/1,025), 근접 누락 통계 JSON, 미매칭 표본 200건 × 3 CSV(모델 판독 Y/N 기록), `UNMATCHED_AUDIT_V7.md`(재현율 추정 광고 0.81·미디어 0.57·지역 0.78, 95% CI); `--summarize`로 검수 집계 |
| 해석 계층 그림 | `v7_final_10020/charts/build_live_layer_figures_v7.py` (글꼴은 `fonts/NotoSansCJKkr-*.otf` 또는 `KFONT_PATH`) | `live_interpretive_layer/` JSON·CSV, 3D payload | `assets/readme/fig05_persona_map.png`·`fig06_factor_specific_impact.png`·`fig07b_persona_pca.png`(2패널 PCA: 좌표 + 로딩) (K→F 배정은 README 5절 표) + `live_pca_v7.json` (동결 판은 `*_frozen_v7_40.png`) |
| 라이브 해석 계층 | `v7_final_10020/analysis/persona_decision_space/build_live_interpretive_layer_v7.py` | 라이브 점수 JSON(factor_share), 라이브 진단 JSON(topic_to_factor), `fan_persona_v7.json`(정의표), `factor_pathway_map_v7.json`, 3D payload(표본 평균) | `live_interpretive_layer/` — 라이브 순위표(4구획 24/17/10/49 재현)·K→F·페르소나 JSON·동결→라이브 이동표·요약 |
| 검수 엑셀 | `v7_final_10020/analysis/unmatched_audit/build_review_sheet_v7.py` | 표본 CSV 3개, 사전 후보 CSV, 근접 누락 통계 | `review_sheet_v7.xlsx` — 안내·정의결정(질문 12개, 선택지·영향·권장)·광고·미디어·지역(모델 판독·사유 + 판정 옵션 A∼E 드롭다운·추가할 표현)·사전후보(처리 옵션)·집계(수식) 시트 |
| 게이트 개편안 | `v7_final_10020/silhouette_gate_policy/gate_policy_v2_v7.py` | `seed_stability_summary_v7.json`(L7) | `gate_policy_v2_decisions_v7.json`·`GATE_POLICY_V2_PROPOSAL_V7.md` — v1(0.267 단일 시드)·v2(G1∼G4) 규칙과 적합 4건 판정표 |
| 노출량 공변량 | `v7_final_10020/index_methodology/build_exposure_adjusted_scores_v7.py` | 라이브·동결 점수 JSON(loyalty_raw·n_bullets) | `exposure_adjusted_scores_v7.csv`(팬덤 100 × 스냅샷 2: 원 점수·밀도·노출량 잔차), `exposure_adjustment_summary_v7.json`, `EXPOSURE_ADJUSTMENT_V7.md` — 정의별 건수 상관·판별타당도 r·활동 통제 편상관·순위 이동 |
| 강건 회귀 | `Statistics/robust_regression_v7.py` | 라이브·동결 점수 JSON | `Statistics/robust_regression_v7.json`·`ROBUST_REGRESSION_V7.md` — OLS / Huber RLM / 분위회귀(q=0.5) / 영향점 5개 제외 OLS 의 계수·SE·p와 부호·유의성 일치 여부 |
| 지역 언급 유형 | `v7_final_10020/analysis/domestic_regional_index/build_regional_mention_types_v7.py` | 코퍼스, `build_notebooks_v7.py`의 REGION_KEYWORDS(괄호 짝 추출), 원 지수 JSON | `region_mentions_by_type_v7.csv`(언급 1,226건: 매치 판정·엄격 지역·연고/활동/기타), `domestic_regional_index_by_type_v7.csv`(팬덤 100: 세 열 + 엄격 지수), `homonym_audit_v7.json`, `REGIONAL_MENTION_TYPES_V7.md` — 원 지수 100/100 재현 |
| 본문 언어 병행 판정 | `v7_final_10020/analysis/worldwide_language_index/build_body_language_classifier_v7.py` | 코퍼스, 라이브 점수 JSON(language_counts·language_coverage), tokenizer 폴더의 도메인 분류기(import) | `bullet_language_body_vs_domain_v7.csv` 10,020행(도메인 언어 vs 본문 언어), `body_language_summary_v7.json`, `BODY_LANGUAGE_V7.md` — 일치 49.2%, 본문 한국어 84.5%, 지수 상관 |
| 부트스트랩 CI | `Statistics/bootstrap_ci_v7.py` | 라이브·동결 점수 JSON, `index_methodology/evidence_score_by_sentence_v7.csv` | `Statistics/bootstrap_ci_v7.json`·`BOOTSTRAP_CI_V7.md`·`bootstrap_r_distributions_v7.png` — 팬덤 부트스트랩(B=2,000) r·회귀계수·χ² p 의 95% CI, 97개 공통 팬덤 r 차이 CI, 동결 건수로의 코퍼스 축소 반복(R=1,000)과 건수 구조 진단 |
| MCI 같은 시점 재산출 | `v7_final_10020/analysis/group_member_index/build_mci_same_period_v7.py` | `member_mention_index_v7.json`, `member_pilot_mci_correlation_v7.json`, 라이브·동결 점수 JSON, 코퍼스 | `member_mci_unified_v7.csv`(45개 그룹 MCI·하한·excess·HHI_norm), `member_mci_correlation_live_v7.json`(세 시점 조합 상관·회귀·VIF), `member_alias_audit_v7.csv`(273명 기록 vs 재계수), `MCI_SAME_PERIOD_V7.md` |
| 지표 사전 고정 | `v7_final_10020/analysis/dictionaries/export_index_dictionaries_v7.py` | `run_lda_v6.py`·`analysis/build_notebooks_v7.py`(ast/괄호 짝 추출), 보조지표 JSON 4종, `merge_log_r65.json` | `index_dictionaries_v7.csv` 436행(사전 19종) + `DICTIONARIES_V7.md`(지표별 사전 유무·건수·출처 표; 저장소에 없는 사전 2종은 '없음'으로 명시) |
| 토픽 대응 자동화 | `v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_alignment_v7.py` | 동결 진단 JSON(상위 10단어), 이 폴더 φ K=10/K=8, `frozen_v7_40/` φ, 라이브 원본 참고 진단, `topic_cards_v7.json` | `topic_alignment/` — 모델 쌍 6개의 토픽 대응(φ 코사인 또는 상위 10단어 Jaccard, 헝가리안 1:1 + 최근접) CSV·자동 라벨(상위 4단어) CSV·요약 JSON·MD, φ 문서 6절 표를 마커 사이에 재생성 |
| 시드 안정성 | `v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_seed_stability_v7.py` | 라이브 10,020건·동결 근사 7,326건, 재구성 토크나이저 마커 절 | `seed_stability/` — 코퍼스×K∈{8,10}×시드 0∼9 의 M=4∼8 실루엣 CSV, 시드 쌍별 토픽 Jaccard CSV, 요약 JSON, `SEED_STABILITY_V7.md` (약 30분) |
| 지표 중간 산출 | `v7_final_10020/index_methodology/export_evidence_score_sentences_v7.py` | 코퍼스 10,020건, `verify_v7_final_consistency.py`의 산식(ast), `run_lda_v6.py`의 `years_in`(ast) | `evidence_score_by_sentence_v7.csv` 10,020행 + `index_intermediate_values_v7.json`(코퍼스 연도 12개, 팬덤별 합 = raw 100/100, time_coverage 100/100) |
| 데이터 export | `v7_final_10020/data_export/build_bullets_flat_csv.py` | `fandoms_v3_100.json` (`--src`) | `bullets_flat_v7_final.csv` 10,020행 (`--expected`로 행 수 대조). 동결 근사 복원본의 `bullets_flat_v7_40_frozen_reconstructed.csv`(7,326행)도 `--src/--out/--expected 7326`으로 같은 스크립트가 만든다 |
| 데이터 export | `v7_final_10020/data_export/build_lda_k_grid_csv.py` | `lda_v6_diagnostics_live_reference_v7.json` (`--src`) | `lda_k_grid_live_reference_v7.csv` (K 후보별 perplexity·coherence·diversity·stability, `selected` 플래그) |
| 데이터 export | `v7_final_10020/data_export/build_corpus_growth_history_csv.py` | `data/v7_rounds/v6*_merge_log.json` + `merge_log_r*.json`·`swap_log_r*.json`·`round_log_r70.json` | `corpus_growth_history_v6_v7_full.csv` — v6 1차∼v7 r72(10,020건) 성장 이력, 체인 불연속을 `chain_gap`에 기록, 타임라인 CSV와 대조 |
| 데이터 export | `v7_final_10020/data_export/build_cohesion_media_index_csv.py` | `fandom_cohesion_index_v7.json`, `media_crossover_index_v7.json` | `fandom_cohesion_index_v7.csv`, `media_crossover_index_v7.csv` — 합계를 원본 집계 필드와 재대조 |
| 통계 검증(R 대조) | `Statistics/verify_r_sections_python.py` | `data/v7_final/` 점수·상관·K9 JSON, `Statistics/R_통계검증/data/member_mention_pilot_v7.json` | 보고서 2.1·2.2·3.8·7.4절 통계량 238개 항목을 scipy·statsmodels로 재계산 — `Statistics/R_통계검증/`(R)과 같은 항목·같은 정답지, 238/238 일치 |
| 지표 산정 노트북 | `v7_final_10020/index_methodology/build_index_calculation_notebook.py` → `index_calculation_v7.ipynb` + Spyder용 셀 스크립트 `index_calculation_v7.py` | 코퍼스 10,020건, 라이브 점수 JSON(coverage_detail·factor_share), 3D payload | 식(1)∼(7)로 100개 팬덤 지표를 직접 산정 → `index_calculation_v7_result.csv`(100×17), 최종 산출 파일과 8개 항목 100/100 일치(불일치 0) |
| 지표 산식 검증 | `v7_final_10020/index_methodology/verify_index_calculation_formulas.py` | `fandom_scores_live_reference_v7.json` | 식(2)(3)(6)(7) 재계산 불일치 0/100, 구현 시 주의점(창단 키워드·`n_num` 패턴 개수) 예시 출력 |
| 노트북 생성기 | `v7_final_10020/analysis/build_notebooks_v7.py` | (생성기) | 노트북 8개를 nbformat으로 생성하고 nbconvert로 실행해 출력 포함 저장. `python … [이름] [--no-exec]` |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py` | 라이브 점수 JSON, `language_domain_summary_v7.json`, 코퍼스 | 14개 언어 실측 합 = 요약(10,020), 도메인 분류기 재구성 1단계 83.3% → 2단계 95.9% |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py` | 코퍼스 (fugashi·jieba·pythainlp) | `analysis/tokenizer/csv/bullet_token_frequency_v7_final.csv` (43,162 토큰, 176,944 발생) |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/jieba_and_thai_engine_details_v7.py` | 위 CSV | 엔진 스펙 조회, HMM/newmm 데모, 중국어·태국어 버킷 재검증 불일치 0 |
| 페르소나 결정공간 | `v7_final_10020/analysis/persona_decision_space/build_persona_decision_space_notebook.py` → `persona_decision_space_v7.ipynb` + Spyder용 `.py` | `persona_decision_space_v7.json`(HTML 내장 데이터), `fan_persona_v7.json`, 동결 점수·진단, `factor_pathway_map_v7.json`, `Persona_결정공간.html` | HTML 로직 재현 — K→F 10/10, 덴드로그램 절단선·M=5 군집·잎 순서 일치, 페르소나 100/100, PCA 좌표 차이 5e-6, Factor-specific 0/1000 불일치. 결과 CSV + PNG 3장 |
| LDA φ·코사인 거리 | `v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_phi_cosine_v7.py` | 코퍼스 10,020건, `run_lda_v6.py`의 `tokenize()`(ast로 추출) | K=10·K=8 LDA(random_state=0) → φ CSV(10×12,253 / 8×12,253), 토픽 간 코사인 거리 K×K, average-linkage 병합 기록, M-grid 실루엣, 학습 모델 pickle(K별)·CountVectorizer pickle·단어 사전 CSV·문서 순서 CSV·manifest(시드·인자·버전·SHA-256, 재로드 검증), `TOPIC_PHI_COSINE_DISTANCE_V7.md` (약 1.5분) |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/stopwords/export_tokenizer_stopwords_v7.py` | `run_lda_v6.py`(ast), 토큰 빈도 스크립트(import), pythainlp | 코드에 정의된 불용어를 언어별로 추출 → `tokenizer_stopwords_by_language_v7.csv`(1,503행) + `TOKENIZER_STOPWORDS_BY_LANGUAGE.md` |

## A. 정합성 검증 — `verify_v7_final_consistency.py`

이 저장소의 중심 검증 스크립트다. 보고서·`KEY_FINDINGS.md`에 인용된 수치를 `data/v7_final/`의
파일에서 실제로 재계산해 항목별 일치/불일치를 출력하며, 어떤 수치도 맞추기 위해 조정하지
않는다. 핵심은 **충성도·파급효과 점수의 완전 재현**이다: `METHODOLOGY.md` 2-4절의 EvidenceScore
산식(문장당 1.0 + 0.5×수치표현 수 + 0.3×보너스 키워드 매치 수 → min-max 정규화)을
`fandoms_v3_100.json`(10,020건)에 그대로 적용하면 3D 맵 payload의 100개 팬덤 점수가 소수점 셋째
자리까지 전부 같고, 그 점수로 Pearson 0.493·Spearman 0.380·Cook's D(BTS 0.5749)·다중회귀
R² 0.847·VIF 1.93·민감도·LOO·3D축 독립성까지 KEY_FINDINGS 값이 그대로 나온다. 4분면
χ²(8.34/10.2273)도 점수 0.5 초과 여부 2×2표로 재현된다. 그 밖에 동결 스냅샷(activity 합 7,350,
페르소나 43/31/17/9), 라이브 참고 재적합(K=8/M=5/0.046 게이트 기각), 언어 커버리지 분모
ln(14)/ln(13), 보조지표 7종의 집계 합, 성장 이력·타임라인 CSV 대조, 동결 코퍼스 근사 복원본(97개 팬덤 지문·접두어·r22 교체분), 로스터 이력까지 107개 항목을 확인한다.

## B. 원본 파이프라인 — `run_lda_v6.py`

v6∼v7 파이프라인 실물이다(재구성본이 아님). 토큰화 → `LatentDirichletAllocation` K 탐색
(perplexity·coherence·diversity·stability 복합 순위) → 토픽 φ분포 코사인거리 계층 군집화로 M 선정
→ 실루엣 게이트(동결 기준선 0.267 미달 시 기각) → EvidenceScore·Coverage·FactorDiversity 산출 →
페르소나 배정 순으로 동작하며, `--data`/`--out` 인자로 코퍼스와 출력 폴더를 지정한다(기본값:
최종 코퍼스 → `output/lda_rerun/`). 단 이 파일의 토크나이저는 14개 언어 문자권 라우팅
(fugashi·jieba·pythainlp 추가 경로) 이전 판이라, 최종 참고 재적합(10,020건 → 3토큰 미만 제외
후 10,018건, K=8/M=5/실루엣 0.046)을 만든 `run_lda_v6_live_reference_v7.py`와 문서 수가 다르다
(이 스크립트로 10,020건을 돌리면 9,954건). 라우팅 판의 원본 소스는 저장소에 없고, 그 실행 결과는
`lda_v6_diagnostics_live_reference_v7.json`·`wordcloud_by_language_v7.json`으로 남아 있다. 이 실행 결과를 목표값으로
라우팅 토크나이저를 다시 붙인 재구성본이 저장소 루트의 `run_lda_v6_live_reference_v7.py`다(아래 B-1).

## B-1. 라우팅 토크나이저 재구성본 — `run_lda_v6_live_reference_v7.py`

`run_lda_v6.py`와 파이프라인이 같고 토크나이저 절(`# === TOKENIZER BEGIN/END ===`)만 다르다: 도메인 조각 제거 →
일반 경로(정규식 `[가-힣A-Za-z0-9À-ɏḀ-ỿЀ-ӿ]{2,}`, 조사 접미사, 한국어 41·영어 118+확장·7개 라틴어권·러시아어 불용어,
순수 숫자 제외, 등록 도메인 라벨 기준 자기인용 슬러그 제거) → 가나/한자/태국 문자 분기로 fugashi·jieba·pythainlp 추가.
검증은 `v7_final_10020/analysis/tokenizer/live_reference_tokenizer/`의 세 스크립트가 한다(표 A 참고). 원본과의 대조:
문서 10,018/10,018, 제외 2건 일치, 총 토큰 170,726/170,725, 8개 버킷 상위 30단어 238/240, 선택 K=8(원본 8)·M=6(원본 5)·
실루엣 0.081(원본 0.046). 기본 출력 `output/lda_live_reference_v7/`, 약 30분(K-grid 7개 × 시드 안정성 3회).

## C. 차트 생성 스크립트 (matplotlib)

네 스크립트 모두 같은 골격을 공유한다: `matplotlib.use("Agg")`로 헤드리스 렌더링 →
`NotoSansCJKkr-Regular.otf`를 `FontProperties`로 로드해 한글 깨짐 방지 → JSON/CSV 로드 → 색상표
상수 정의 → `matplotlib` 축 조작 → PNG(300∼450dpi)+SVG를 `output/charts/`에 저장.

**`build_cohesion_index_v7.py`** — 팬덤결속 지수(보조지표, LDA와 무관한 키워드매칭 지표) 2패널
Figure. 좌측은 5개 결속 활동 유형(A∼E)별 근거문장 순위(`barh`, 내림차순), 우측은 상위 25개
팬덤의 유형 구성을 누적 막대로 표시하며 막대 끝에 비중(%) 라벨을 붙인다. BTS·임영웅·리센느는
y축 라벨을 굵게 강조.

**`build_cohesion_index_v7_right_only.py`** — 위 스크립트의 우측 패널만 별도 이미지로 분리한
버전. 집계·정렬 로직은 완전히 동일하게 복제하고(데이터는 건드리지 않음), figure 크기와 폰트
크기만 단독 이미지에 맞게 재조정했다.

**`build_persona_cluster_split_boxed.py`** — 두 개의 독립된 분석을 각각 별도 PNG로 생성한다.
1. *덴드로그램*: 동결 스냅샷의 토픽 간 코사인거리 행렬(`topic_cosine_distance_frozen_v7_40.json` — 원본 데이터 묶음에 없던 파일이며, 동결 코퍼스 복원 후 재적합하면 이 이름으로 둔다)이 있으면
   `scipy.cluster.hierarchy.linkage`로 병합 트리를 계산하고, 없으면 `persona_decision_space_v7.json`의 average-linkage 병합 기록을
   linkage 행렬로 옮겨 같은 덴드로그램을 그린다. 이어서
   (average-linkage)로 계층적 군집화하고, K→M 절단선을 `fcluster`로 계산해 덴드로그램을 그린다.
   가지 색상은 그 가지에 속한 토픽들이 전부 같은 F코드를 공유하면 해당 F코드 색, 섞여 있으면
   회색으로 칠하는 커스텀 `link_color_func`를 직접 구현.
2. *PCA biplot*: `fan_persona_v7.json`의 팬덤별 F1∼F5 factor_share 5차원 벡터를
   `sklearn.decomposition.PCA(n_components=2)`로 2차원에 투영하고, 페르소나별로 색을 다르게
   산점도로 표시. loading 벡터(F1∼F5 화살표)를 함께 그리고, 하이라이트 3개 팬덤(BTS·임영웅·
   리센느)은 밀집 영역 바깥 여백으로 라벨을 이동시켜 테두리 박스+화살표로 표시.

**`build_silhouette_gate_timeline_v7.py`** — 코퍼스 규모(막대)와 실루엣(선)의 이중축
타임라인. 실측 행과 "[추정·선형보간]" 행을 구분해 그리고, 게이트 구간(r46∼마지막 실측)의
라운드 수·상관계수·성장률을 그리기 전에 재계산해 출력한다. 상세는
`silhouette_gate_policy/SILHOUETTE_GATE_POLICY.md`.

## D. 지수 CSV 산출 스크립트

세 스크립트 전부 같은 패턴: JSON 로드 → 팬덤별 행 구성(지수 고유 컬럼 + 세부 카테고리별
언급수를 가로로 펼친 컬럼들) → 지정된 기준으로 내림차순 정렬 → `csv.DictWriter`로 `utf-8-sig`
(엑셀 한글 깨짐 방지) 저장 → **세부 카테고리 합계를 원본 JSON의 집계 필드와 재대조**하는
무결성 검증을 스크립트 끝에서 자체 수행하고 결과를 출력한다(전부 불일치 0건 확인됨). 국내
지역 지수의 입력 JSON은 `analysis/domestic_regional_index/domestic_regional_index_v7.ipynb`가
최종 코퍼스 10,020건에서 산출한 것이다.

## E. 데이터 export 스크립트

**`extract_html_payloads.py`** — HTML 2종에 `const payload = {...}` / `const DATA = {...}`로
내장된 데이터 객체를 문자열 그대로 잘라내 JSON으로 저장한다. 3D 맵 payload는 최종 코퍼스
10,020건 점수·4구획(24/17/10/49)·라이브 재적합 진단, Persona는 동결 K=10 토픽명·F코드·PCA·
F1∼F5 비중을 담는다.

**`build_bullets_flat_csv.py`** — `fandoms_v3_100.json`(팬덤별 `loyalty`/`spillover` 중첩 배열)을
`fandom, category, bullet_type, text, url` 5개 컬럼의 단일 평면 CSV(10,020행)로 펼친다.

**`build_lda_k_grid_csv.py`** — 진단 JSON의 `k_grid`(K 후보별 perplexity·coherence·diversity·
stability·composite_rank_sum 비교표)를 CSV로 풀고, `selected_k`와 일치하는 행에
`selected=True` 플래그를 붙인다.

**`build_corpus_growth_history_csv.py`** — 서로 다른 스키마를 가진 병합·교체 로그(v6 1·2차,
v6.3 시장 다양화, v6.4 언어 다양화, v7 r1∼r72; r36∼r59는 키 이름이 다름)를 공통 스키마
(`stage, kind, before_total, after_total, net_new_bullets, n_touched_fandoms, roster_change, note`)로
정규화해 하나의 시계열 CSV로 이어붙인다. 각 행의 `after_total`이 다음 행의 `before_total`과
이어지는지 체인 연속성을 검증하며, 로그 자체의 기록 오차(r21→r22 +1 등)는 숨기지 않고
`chain_gap` 컬럼에 그대로 적는다. 마지막 `after_total`이 10,020인지 확인한다.

**`build_cohesion_media_index_csv.py`** — 팬덤결속·미디어 크로스오버 지수 JSON을 팬덤별
유형/매체 집계 CSV로 펼치고 합계를 원본 집계 필드와 재대조한다.

## F. `v7_final_10020/analysis/` — 노트북 8개와 토크나이저 스크립트

`build_notebooks_v7.py`가 nbformat으로 셀을 조립하고 `jupyter nbconvert --execute`로 끝까지
실행해 출력이 포함된 `.ipynb`를 저장한다(에러 0건). 각 노트북은 최종 코퍼스 10,020건 또는
동결 스냅샷을 읽어 해당 지수 JSON의 값을 독립적으로 재계산·대조한다.

| 노트북 | 입력 | 확인 결과 |
|---|---|---|
| `ad_commercial_index/ad_commercial_index_v7.ipynb` | `ad_commercial_index_v7.json`, 코퍼스, 라이브 점수 | 무결성 100/100, 광고신호 키워드 재매칭 96/100 정확 일치, LDA 브랜드·상업형 비중과 r=0.834 |
| `fandom_cohesion_index/fandom_cohesion_index_v7.ipynb` | `fandom_cohesion_index_v7.json`, 동결·라이브 점수 | 무결성 100/100, 동결 LDA 결속형과 r=0.687 |
| `media_content_exposure_index/media_content_exposure_v7.ipynb` | 노출·크로스오버 지수, `k9_validation_v7.json`, r10·r11 로그 | 무결성 100/100, r10+r11 274건 일치, 서브태그 재매칭 100/100 |
| `domestic_regional_index/domestic_regional_index_v7.ipynb` | 코퍼스 10,020건, 동결 점수 JSON | 17개 지역 사전으로 **`domestic_regional_index_v7.json/.csv` 산출**(언급 1,226건, 적중 팬덤 469), 보고서 표 15 동결 근사 17/20행 재현 |
| `worldwide_language_index/worldwide_language_index_v7.ipynb` | 라이브 점수 JSON, 세계 언어 지수 JSON/CSV, 언어 요약 | ln(14)/ln(13) 각 100/100, 8개 필드 불일치 0 |
| `group_member_index/group_member_index_v7.ipynb` | `member_mention_index_v7.json`, 파일럿 v6, 상관 JSON | MCI 재계산 0/45 불일치, r(MCI, 멤버 수) −0.728 |
| `fan_impact_pathway/fan_impact_pathway_v7.ipynb` | 동결 진단·페르소나·토픽 카드·경로 맵·결정공간 | 매핑 10/10, Factor-specific Impact 500/500, 페르소나 43/31/17/9 |
| `tokenizer/tokenizer_script_routing_v7.ipynb` | 코퍼스, `wordcloud_by_language_v7.json` | 문자권 다중 라벨 재현(태국·러시아·베트남 정확 일치, 소수 언어 순위 5/5) |

토크나이저 스크립트 3종(`build_multilingual_bullet_language_classifier_v7.py`,
`build_bullet_token_frequency_csv_v7.py`, `jieba_and_thai_engine_details_v7.py`)은 fugashi
(unidic-lite)·jieba·pythainlp를 실제로 실행한다. 원본 파이프라인의 불용어 목록은 저장소에 없어
토큰 빈도 CSV는 독자 정의 불용어를 쓴 병행 산출물이며, 상세는
`tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` "재현 범위" 참고.

## 공통적으로 쓰인 패턴

- **무결성 자체검증**: 모든 산출 스크립트가 "세부 항목의 합 == 원본 JSON의 집계 필드"를
  스크립트 끝에서 재계산해 출력한다. 결과를 사람이 눈으로 믿는 대신 매번 프로그램이 스스로
  대조하도록 만든 것.
- **한글 인코딩**: CSV는 전부 `utf-8-sig`로 저장(엑셀에서 한글이 깨지지 않도록), 차트는
  `NotoSansCJKkr-Regular.otf`를 명시적으로 폰트매니저에 등록.
- **데이터 미변형 원칙**: 패널 분리·라벨 위치 변경 등 순수 표현(presentation) 변경 스크립트는
  주석에 "집계 로직은 전혀 바꾸지 않았다"를 명시하고, 실제로 원본과 동일한 정렬·필터 로직을
  그대로 복제한 뒤 결과만 다시 검증한다.
- **원본 데이터 불변**: 어떤 스크립트도 `data/v7_final/`의 원본 JSON을 덮어쓰지 않는다. 생성물은
  `output/` 또는 파생 CSV 파일로만 나간다.
