# v6 + v7 라운드22 스냅샷 — 실제 복구 데이터

목원님이 2026-09-20에 업로드해주신 `100_LDA_v7_...5.zip`의 내용물이다. **합성(synthetic) 데이터가
아니라 실제 프로젝트에서 수집·산출된 원본 데이터**이며, `analysis/run_lda_v6_reconstructed.ipynb`가
합성 데이터로 대체했던 바로 그 근거문장 코퍼스와 LDA 산출물이다.

## 이 스냅샷이 정확히 어느 시점인가

`v7_progress.json` 기준:

- 프로젝트: `v7_incremental_10x_expansion` — "근거 표본 10배 확대"(1,781건 → 17,810건 목표)를
  여러 세션에 걸쳐 단계적으로 달성하는 진행 추적
- 이 스냅샷 시점 코퍼스 총량: **5,612건** (누적 배수 3.151×)
- 마지막 완료 라운드: **v7 라운드22** (2026-09-02 기준, `v7_rounds/merge_log_r22.json`)
- 이 시점 LDA 재적합 결과(`lda_v6_diagnostics.json`): `selected_k=8`, `selected_m_meta_factors=6`,
  `meta_factor_silhouette=0.154`

## ⚠️ 최종 제출 보고서 수치와는 다르다

`docs/KEY_FINDINGS.md`·`docs/METHODOLOGY.md`에 기록된 최종 제출본 수치(코퍼스 10,020건, K=10,
M=5, 동결 스냅샷 silhouette=0.267)는 이 v7 라운드22 이후 라운드23~65(및 추가 라운드)를 거쳐
도달한 **더 나중 시점**의 결과다. 즉:

| | 이 스냅샷(v7 r22) | 최종 제출본(v7-40 동결) |
|---|---|---|
| 코퍼스 총량 | 5,612건 | 7,350건(동결) / 10,020건(최종 라이브) |
| K (원토픽) | 8 | 10 |
| M (메타요인) | 6 | 5 |
| silhouette | 0.154 | 0.267 |

이 스냅샷을 "최종 데이터"로 오인해 보고서 수치를 이걸로 바꾸면 안 된다 — 어디까지나 **원본
데이터가 유실되기 전, 파이프라인이 실제로 어떻게 동작했는지 보여주는 실물 증거**로서 가치가 있다.
v7 라운드23 이후~최종본까지의 원본 파일이 남아있다면 그것도 찾아서 추가해주시면 가장 좋다.

## 파일 구성

| 파일 | 내용 |
|---|---|
| `fandoms_v3_100.json` | **근거문장 원본 코퍼스.** 100개 팬덤 × `loyalty`/`spillover` 배열, 각 원소는 `{t: 문장텍스트, u: 출처URL}`. 이 스냅샷 시점 전체 근거문장의 실제 원문. |
| `fandom_scores_v6.json` / `.csv` | 팬덤별 산출 점수 — `loyalty_score`, `spillover_score`, `factor_share`(F코드별 비중), `factor_diversity`, `coverage_index`(+ 세부 `coverage_detail`), `dominant_factor`, `activity` |
| `lda_v6_diagnostics.json` | **실제 LDA 재적합 결과.** `k_grid`(K 후보별 perplexity/coherence/diversity/stability 비교), `selected_k`, `selected_m_meta_factors`, `meta_factor_silhouette`, `topic_to_factor`, `factor_labels`, `factor_top_words` — 이전에 합성 데이터로 대체했던 바로 그 정보 |
| `chart3d_payload_v6.json` | 이 시점의 3D 매트릭스 아티팩트용 payload(현재 배포된 아티팩트의 v7 최신판과는 다른, 이 스냅샷 당시 버전) |
| `v7_progress.json` | 10배 확대 프로젝트 진행 추적 — 라운드별 이력(`history`), 목표/현재 총량 |
| `v6_merge_log.json`, `v6_3_market_merge_log.json`, `v6_4_language_merge_log.json` | v6 단계 병합 로그(라운드 이전 1차/시장 다양화/언어 다양화 라운드) |
| `v7_rounds/merge_log_r1.json` ~ `r22.json` | v7 라운드별 병합 로그(라운드 설명, 순증 문장 수, 중복 스킵, 대상 팬덤 등) |
| `domestic_regional_pilot_v6.json` | 국내 지역 지수의 파일럿 버전(트로트/힙합/원로그룹 등 25개 팬덤 대상, 최종 v7 버전 이전 단계) |
| `member_mention_pilot_v6.json` | 멤버 집중도 지수(MCI)의 파일럿 버전(다국적 멤버 보유 23개 그룹 대상) |

## 기존 스크립트와의 관계

`scripts/` 아래 기존 스크립트들은 최종 제출본 파일명(`factor_clustering_structure_v7.json`,
`fan_persona_v7.json`, `ad_commercial_index_v7.json` 등)을 기대하도록 짜여 있어서, 이 스냅샷
파일을 그대로 넣어도 바로 동작하지는 않는다(파일명·스키마가 다름). 대신 이 스냅샷은
`analysis/run_lda_v6_reconstructed.ipynb`의 1번 데이터 로딩 셀(현재 합성 데이터)을 실데이터로
교체하는 데 바로 쓸 수 있다 — `fandoms_v3_100.json`이 그 노트북이 가정한 스키마(팬덤별 근거문장)와
사실상 같은 정보를 담고 있고, `lda_v6_diagnostics.json`은 노트북이 재현하려 했던 LDA/재군집화 결과의
실측 비교값을 제공한다.
