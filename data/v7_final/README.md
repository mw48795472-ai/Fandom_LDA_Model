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
| `positioning_map_correlation_live_v7.json` | 라이브 10,020건 | 보고서 표 "통계 검증" 원본: Pearson/Spearman·정규성·다중회귀(+activity)·VIF·영향점 top5·민감도·LOO·설계기준(|r|<0.5)·**4분면 χ²의 분할표 [[7,17],[4,72]] (점수 0.5 초과 기준)** |
| `member_pilot_mci_correlation_v7.json` | MCI: v7-55 시점 8,981건 / outcome: 동결 7,350건 | MCI ↔ loyalty/spillover/coverage/diversity 상관·회귀·MCI_excess 재분석 (45개 그룹). 파일 자체 caveat대로 시점이 섞인 참고용 분석 |
| `member_mention_pilot_v6.json` | 동결 스냅샷 7,350건 | 멤버 언급 파일럿 23개 그룹 (BTS 170건 중 73건, MCI 0.24). r22판(BTS 125건)은 `data/v6_r22_snapshot/`에 별도 |
| `ad_commercial_index_v7.json` / `.csv` | 라이브 10,020건 | 광고·상업성 지수: 31개 광고신호 키워드 → 20개 업종 태깅. 광고성 불릿 1,302건(13.0%), 팬덤별 업종 카운트·샘플 불릿, v7-39~43 이력. CSV는 `indices_csv/build_ad_commercial_index_csv.py` 산출(검증 통과) |
| `fandom_cohesion_index_v7.json` | 라이브 10,020건 | 팬덤결속 지수: 5개 유형(A~E) 키워드 매칭, 결속 불릿 923건(9.2%), D(기부·후원) 팬덤 공존어 게이트 검증치 포함. `charts/build_cohesion_index_v7*.py` 입력 |
| `chart3d_correlation_live_v7.json` | 라이브 10,020건 | 3D 매트릭스 축 독립성: 3축 쌍별 상관·정규성·다중회귀(factor_diversity ~ loyalty + spillover)·VIF·영향점·LOO·민감도 |
| `topic_cards_v7.json` | 동결 스냅샷 7,350건 | K=10 토픽 카드: 명칭(METHODOLOGY.md 2-1 표와 동일)·상위 10개 키워드·대표 불릿 3건·대표 팬덤 5개·연결 F 경로 |
| `fandom_scores_v6.csv` | 동결 스냅샷 7,350건 | 팬덤별 loyalty/spillover/coverage/factor_diversity/dominant_factor/activity + F1~F5 비중(컬럼: 현장경제형=F3, 소비력형=F2, 미디어노출형=F4, 차트·확산형=F5, 결속형=F1). activity 합 = 7,350. 파일명의 v6은 파이프라인 버전 |
| `fan_persona_v7.json` | 동결 스냅샷 7,350건 | 페르소나 조합표(10개)·카운트(43/31/17/9)·팬덤별 top2 F·factor_specific_loyalty/spillover(= 비중 × 점수) |
| `persona_decision_space_v7.json` | 동결 스냅샷 7,350건 | Persona_결정공간.html 내장 데이터: K=10 토픽명·F코드·덴드로그램 병합 순서·PCA loading/좌표·팬덤별 F1~F5 비중 (`data_export/extract_html_payloads.py`) |

정합성 검증: 저장소 루트의 `verify_v7_final_consistency.py`.
실루엣 게이트 타임라인 CSV는 `../silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv`.
아직 없는 최종 산출물(넣으면 해당 스크립트가 바로 읽음): `domestic_regional_index_live_reference_v7.json`,
`worldwide_language_index_live_reference_v7.json`, `factor_clustering_structure_v7.json`.
