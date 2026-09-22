# data/v7_final — 최종 제출본 근거 데이터와 산출물

| 파일 | 계층 | 내용 |
|---|---|---|
| `fandoms_v3_100.json` | 라이브 10,020건 | 근거문장 원본 코퍼스. 100개 팬덤 × `loyalty`/`spillover` 배열, 원소 `{t: 문장, u: 출처 URL}` |
| `bullets_flat_v7_final.csv` | 라이브 10,020건 | 위 JSON을 `fandom, category, bullet_type, text, url` 평면 CSV로 펼친 것 (`data_export/build_bullets_flat_csv.py`) |
| `language_domain_summary_v7.json` | 라이브 10,020건 | 14개 언어권별 근거 건수·도메인 수·상위 도메인 (보고서 표 2-2). 합 10,020건 |
| `chart3d_payload_live_reference_v7.json` | 라이브 10,020건 | 3D 포지셔닝맵 HTML 내장 payload: 100개 팬덤 loyalty/spillover/diversity/coverage/activity/quadrant, 표본 평균 0.37103/0.26605, 4구획 24/17/10/49, 라이브 재적합 K=8/M=5/실루엣 0.046 (`data_export/extract_html_payloads.py`) |
| `fandom_scores_live_reference_v7.csv` | 라이브 10,020건 | 위 payload rows를 CSV로 (`data_export/build_live_scores_csv.py`) |
| `lda_v6_diagnostics_live_reference_v7.json` | 라이브 10,020건 | 라이브 재적합 진단: K-grid(8~30), selected_k=8, M=5, 실루엣 0.046, 토픽 상위어, 토픽→F 배정 — 실루엣 게이트에 기각되어 해석 계층에 미반영 |
| `lda_k_grid_live_reference_v7.csv` | 라이브 10,020건 | 위 k_grid를 CSV로 (`data_export/build_lda_k_grid_csv.py`) |
| `member_mention_index_v7.json` | 라이브 10,020건 | 멤버 집중도 지수(MCI) 45개 그룹 |
| `fandom_scores_v6.csv` | 동결 스냅샷 7,350건 | 팬덤별 loyalty/spillover/coverage/factor_diversity/dominant_factor/activity + F1~F5 비중(컬럼: 현장경제형=F3, 소비력형=F2, 미디어노출형=F4, 차트·확산형=F5, 결속형=F1). activity 합 = 7,350. 파일명의 v6은 파이프라인 버전 |
| `fan_persona_v7.json` | 동결 스냅샷 7,350건 | 페르소나 조합표(10개)·카운트(43/31/17/9)·팬덤별 top2 F·factor_specific_loyalty/spillover(= 비중 × 점수) |
| `persona_decision_space_v7.json` | 동결 스냅샷 7,350건 | Persona_결정공간.html 내장 데이터: K=10 토픽명·F코드·덴드로그램 병합 순서·PCA loading/좌표·팬덤별 F1~F5 비중 (`data_export/extract_html_payloads.py`) |

정합성 검증: 저장소 루트의 `verify_v7_final_consistency.py`.
아직 없는 최종 산출물(넣으면 해당 스크립트가 바로 읽음): `ad_commercial_index_v7.json`, `fandom_cohesion_index_v7.json`,
`domestic_regional_index_live_reference_v7.json`, `worldwide_language_index_live_reference_v7.json`, `factor_clustering_structure_v7.json`.
