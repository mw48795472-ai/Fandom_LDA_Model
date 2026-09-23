# 전수조사 기록 (2026-09-23) — 이번 개선 작업(L1∼L19, 게이트 v2 채택)의 재현성·정합성 점검

한계보고서 19개 항목을 실행한 뒤 저장소에 들어간 스크립트·문서·산출물을 한 번에 다시 검사했다. 저자가 검수 엑셀을 작성하는 동안 수행했고, 발견한 문제는 이 문서와 같은 커밋에서 고쳤다.

## 1. 범위

| 구분 | 대상 |
|---|---|
| 커밋 | cd50d64(난이도 하 1차) ∼ 40a98bd(검수 엑셀) 20개 + 이 문서의 커밋 |
| 스크립트 | 이번 작업에서 새로 만든 파이썬 17개 + 앞선 복원 작업의 스크립트 8개 + 검증기 2개 + 데이터 export 4개 = 30개 실행 |
| 문서 | 바뀐 MD 28개의 경로 참조, 저장소 전체 MD의 경로 참조, README 핵심 수치 15항목 |
| 제외 | 30분 이상 걸리는 재적합(`build_seed_stability_v7.py` 전체 실행, `build_frozen_model_bundle_v7_40.py`, `build_topic_phi_cosine_v7.py`, `run_lda_v6_live_reference_v7.py`)은 저장된 산출물을 쓰고 요약·문서 생성 단계만 재실행(`--report-only` 등). 노트북 10개는 이번 작업에서 바뀌지 않아 재실행하지 않음 |

## 2. 스크립트 재실행 (30개, 전부 종료 코드 0)

| 영역 | 스크립트 | 결과 |
|---|---|---|
| 데이터 export | `build_roster_history_v7.py`, `build_bullet_provenance_v7.py`, `build_bullets_flat_csv.py`, `build_lda_k_grid_csv.py`, `build_corpus_growth_history_csv.py`, `build_cohesion_media_index_csv.py` | 산출물 동일 |
| 지표 산식 | `export_evidence_score_sentences_v7.py`(100/100), `build_exposure_adjusted_scores_v7.py` | 산출물 동일 |
| 사전 | `export_index_dictionaries_v7.py` 생성 + `--check`(436행 일치) | 산출물 동일 |
| 모델·시드·대응 | `build_seed_stability_v7.py --report-only`, `build_topic_alignment_v7.py`(φ 문서 6절 표 재생성 동일), `build_frozen_bundle_md_v7_40.py`, `build_tokenizer_reconstruction_md_v7.py`, `verify_tokenizer_reconstruction_v7.py`(10,018/10,018·170,726/170,725·238/240) | 산출물 동일 |
| 통계 | `bootstrap_ci_v7.py`(seed 0), `robust_regression_v7.py`, `verify_r_sections_python.py`(238/238) | 산출물 동일 |
| 보조지표 | `build_mci_same_period_v7.py`, `build_body_language_classifier_v7.py`, `build_regional_mention_types_v7.py`(원 지수 100/100), `build_unmatched_audit_samples_v7.py`(+`--summarize`) | 산출물 동일 |
| 게이트·해석 계층 | `gate_policy_v2_v7.py`, `build_live_interpretive_layer_v7.py`, `build_live_layer_figures_v7.py`(PNG 4장), `build_review_sheet_v7.py`(xlsx) | 산출물 동일 |
| 동결 코퍼스 | `verify_frozen_corpus_candidate.py`(7,326건, 지문 97/100) | 동일 |
| 타임라인 | `build_silhouette_gate_timeline_v7.py` | 동일 |
| 검증기 | `verify_v7_final_consistency.py` | 107/107 (r73 채택 뒤 110/110) |

## 3. 발견한 문제와 조치

1. **생성 문서에 손으로 덧붙인 내용이 재실행 때 사라졌다** — 5개 파일: `DICTIONARIES_V7.md`(사전 후보 안내), `FROZEN_MODEL_REFIT_V7_40.md`(시드 분포 문장), `GATE_POLICY_V2_PROPOSAL_V7.md`(채택 기록), `UNMATCHED_AUDIT_V7.md`(검수 결과 1-1절·저자 시트 안내·한계 3), `near_miss_stats_v7.json`(review_results). → 그 내용을 각 생성 스크립트 안으로 옮겨 재실행해도 유지되게 했다. `UNMATCHED_AUDIT`의 검수 결과는 표본 CSV의 검수 열을 읽어 자동 생성한다.
2. **표본 생성기가 재실행되면 표본 CSV의 판독 열(검수·사유·검수자)이 지워졌다.** → 같은 불릿(fandom·유형·idx)의 기존 판독을 보존하도록 고쳤다(seed 0 표본은 같으므로 전부 보존).
3. **검수 엑셀이 재실행마다 바이트가 달랐다**(문서 속성·zip 항목 시각). → 속성 시각과 zip 항목 시각을 고정해 두 번 실행한 md5가 같다.
4. README '검증 상태' 줄이 이번 작업 이전 수치(파이썬 26개·스크립트 22개)였다. → 갱신.

## 4. 정합성 검사 결과

| 검사 | 결과 |
|---|---|
| 파이썬 컴파일 | 52개 파일, 오류 0 |
| README 핵심 수치 ↔ 산출 JSON | 15/15 일치 — 페르소나 62/17/12/9, 상위 15 겹침 12/15, 순위 ρ 0.83, 같은 페르소나 49/97, 4구획 24/17/10/49, 시드 최대 0.192, 부트스트랩 CI 라이브 [0.25, 0.67]·동결 [0.46, 0.77]·차이 0.126, 재현율 추정 0.81/0.57/0.78, 밀도 r 0.43/0.40, 본문 한국어 84.5%, 토픽 대응 Jaccard 0.29/0.33, MCI 같은 시점 r −0.390, 게이트 v2 통과 = 라이브 K=8만 |
| 낡은 문구(제안이며·채택 전까지·검수는 아직·O/X 판정·본문 미변경) | 저장소 MD에 0건 |
| 경로 참조 | 바뀐 MD 28개 + 저장소 전체 MD: 실재하지 않는 참조 31건은 전부 글롭·패턴(`*.json`, `{k}`) 또는 원본 데이터 묶음·동봉 패키지의 파일을 '없다/외부'로 설명하는 문맥이었고, 실제 깨진 링크는 0건 |
| 데이터 정합성 | `verify_v7_final_consistency.py` 107/107(전수조사 시점; r73 채택 뒤 [AF]절 3항목이 더해져 110/110), R 대응 파이썬 238/238, 사전 CSV ↔ 코드 drift 0 |

## 5. 남은 주의점

- 최종 보고서 PDF의 4·5절(동결 해석 계층)과 README 4·5절(라이브 해석 계층)은 게이트 v2 채택으로 의도적으로 다르다(README 8절 명시). `REPORT_DOCX_VERIFICATION.md`의 47/58 대조는 PDF 기준 그대로다.
- 생성 문서는 앞으로도 스크립트를 고쳐서 바꾼다. 손으로 고친 문구는 다음 재실행 때 사라진다(이번에 확인된 함정).
- `build_live_layer_figures_v7.py`는 한글 폰트가 필요하다. 전수조사 뒤 저장소에 `fonts/NotoSansCJKkr-*.otf`(서브셋)를 넣어 기본으로 쓰고, `KFONT_PATH`는 대체 경로다.

## 6. 전수조사 이후 변경 (같은 날, r73 채택)

위 4절의 README 핵심 수치 15항목은 r72 라이브 해석 계층 기준이다. 전수조사 뒤 투어스(TWS) 영문 근거 86건을 한국어로 재작성한 r73 라운드가 게이트 v2.1(텍스트 품질 수정 라운드 = 현직 재측정)로 채택되어 README 4·5절이 r73 재적합 값으로 바뀌었다: 페르소나 89/8/2/1, 같은 페르소나 37/97, 4구획 24/17/11/48, 상위 15 겹침 12/15·ρ 0.83은 유지. r72 계층은 `analysis/persona_decision_space/live_interpretive_layer_r72/`에 보관하고, 검증은 `verify_v7_final_consistency.py` [AF]절(110/110)과 `data/v7_rounds/round_log_r73.json`이 맡는다.
- 재적합 4종(시드 전체 실행·동결 재적합·φ 묶음·재구성 토크나이저 재적합)은 이번 조사에서 다시 돌리지 않았다. 저장된 산출물은 앞선 세션의 실행 결과다.
