# data/v7_final — 최종 제출본 근거 데이터와 산출물

| 파일 | 계층 | 내용 |
|---|---|---|
| `fandoms_v3_100.json` | 라이브 10,020건 | 근거문장 원본 코퍼스. 100개 팬덤 × `loyalty`/`spillover` 배열, 원소 `{t: 문장, u: 출처 URL}` |
| `bullets_flat_v7_final.csv` | 라이브 10,020건 | 위 JSON을 `fandom, category, bullet_type, text, url` 평면 CSV로 펼친 것 (`data_export/build_bullets_flat_csv.py`) |
| `language_domain_summary_v7.json` | 라이브 10,020건 | 14개 언어권별 근거 건수·도메인 수·상위 도메인 (보고서 표 2-2). 합 10,020건 |
| `chart3d_payload_live_reference_v7.json` | 라이브 10,020건 | 3D 포지셔닝맵 HTML 내장 payload: 100개 팬덤 loyalty/spillover/diversity/coverage/activity/quadrant, 표본 평균 0.37103/0.26605, 4구획 24/17/10/49, 라이브 재적합 K=8/M=5/실루엣 0.046 (`data_export/extract_html_payloads.py`) |
| `fandom_scores_live_reference_v7.csv` | 라이브 10,020건 | **원본 산출물**: 팬덤별 loyalty/spillover/coverage/factor_diversity/dominant_factor/activity + 라이브 재적합(K=8→M=5) F 비중 5개(현장경제형·소비력형·결속형·브랜드·상업형·차트·확산형). 점수는 payload와 100/100 동일 |
| `fandom_scores_live_reference_v7.json` | 라이브 10,020건 | 위 CSV의 JSON 원본: loyalty_raw/spillover_raw, 불릿 수, factor_share, coverage_detail(14개 언어 카운트·시장·출처유형·연도·개체·가중치) 포함 |
| `worldwide_language_pilot_live_reference_v7.json` / `worldwide_language_index_v7.csv` | 라이브 10,020건 | 세계 언어 지수 원본(아카이브명) + `indices_csv/build_worldwide_language_index_csv.py` 산출 CSV |
| `wordcloud_by_language_v7.json` | 라이브 10,020건 | 최종 토크나이저(문자권별 라우팅) 실행 결과: 8개 버킷별 불릿 수·토큰 수·상위 30단어, 총 토큰 170,725 |
| `_explore_r45_meta_factor.json` | v7 r45 1차 (8,122건, K=12) | K=12 토픽 코사인거리 행렬·상위어·M 2~11 실루엣 그리드(최대 M=2, 0.136) — 게이트 기각 라운드의 실물 |
| `factor_pathway_map_v7.json` | 동결 스냅샷 7,350건 | raw Factor 라벨 5개 → F1~F5 경로(F 이름·경로·rationale) 매핑 |
| `chart3d_positioning_rows_live_v7.csv` | 라이브 10,020건 | payload rows를 CSV로 푼 파생 파일(4구획 컬럼 포함; `data_export/build_live_scores_csv.py`) |
| `lda_excluded_bullets_v7.json` | 라이브 10,020건 | LDA 재적합에서 제외된 3토큰 미만 불릿 2건 → 문서 10,018건 |
| `media_crossover_index_v7.json` / `.csv` | 라이브 10,020건 | 매체 크로스오버 지수: news_media 불릿 6,712건(67.0%), 코퍼스 고유 매체 1,298개, 팬덤별 매체 수·다양성 비율·상위 매체 |
| `media_exposure_v7.json` | 라이브 10,020건 | 미디어·콘텐츠 노출 지수: 예능/유튜브/영화/드라마 4종 서브태그 원문 매칭, 미디어 불릿 1,025건(10.2%), 팬덤별 서브태그 카운트·샘플 |
| `member_mention_pilot_v7.json` | 라이브 10,020건 | 멤버 언급 파일럿 v7 (아카이브 원본명). `member_mention_index_v7.json`과 값이 동일하고 키 이름만 pilot/index |
| `v7_progress.json` | v7 48라운드 시점(8,311건) | 10배 확대 프로젝트 진행 추적 후속본(r22판은 `data/v6_r22_snapshot/`). `current_total_note`가 동결/라이브 이원 구조를 명시 |
| `ARCHIVE_README_original.md` | — | 최종 보고서 docx가 읽은 원본 데이터 아카이브(zip)의 README 원문 — 파일 전량 목록. 저장소 미보유분 대조는 루트 README 3절 |
| `k9_validation_v7.json` | 중간 라운드 9,614문서 | K=9 추가 검증 실험(승자 K=8 유지, 미디어 토픽 분리 여부 M-grid) |
| `lda_v6_diagnostics_live_reference_v7.json` | 라이브 10,020건 | 라이브 재적합 진단: K-grid(8~30), selected_k=8, M=5, 실루엣 0.046, 토픽 상위어, 토픽→F 배정 — 실루엣 게이트에 기각되어 해석 계층에 미반영 |
| `lda_k_grid_live_reference_v7.csv` | 라이브 10,020건 | 위 k_grid를 CSV로 (`data_export/build_lda_k_grid_csv.py`) |
| `member_mention_index_v7.json` | 라이브 10,020건 | 멤버 집중도 지수(MCI) 45개 그룹 |
| `positioning_map_correlation_live_v7.json` | 라이브 10,020건 | 보고서 표 "통계 검증" 원본: Pearson/Spearman·정규성·다중회귀(+activity)·VIF·영향점 top5·민감도·LOO·설계기준(|r|<0.5)·**4분면 χ²의 분할표 [[7,17],[4,72]] (점수 0.5 초과 기준)** |
| `member_pilot_mci_correlation_v7.json` | MCI: v7-55 시점 8,981건 / outcome: 동결 7,350건 | MCI ↔ loyalty/spillover/coverage/diversity 상관·회귀·MCI_excess 재분석 (45개 그룹). 파일 자체 caveat대로 시점이 섞인 참고용 분석 |
| `member_mention_pilot_v6.json` | 동결 스냅샷 7,350건 | 멤버 언급 파일럿 23개 그룹 (BTS 170건 중 73건, MCI 0.24). r22판(BTS 125건)은 `data/v6_r22_snapshot/`에 별도 |
| `ad_commercial_index_v7.json` / `.csv` | 라이브 10,020건 | 광고·상업성 지수: 31개 광고신호 키워드 → 20개 업종 태깅. 광고성 불릿 1,302건(13.0%), 팬덤별 업종 카운트·샘플 불릿, v7-39~43 이력. CSV는 `indices_csv/build_ad_commercial_index_csv.py` 산출(검증 통과) |
| `fandom_cohesion_index_v7.json` / `.csv` | 라이브 10,020건 | 팬덤결속 지수: 5개 유형(A~E) 키워드 매칭, 결속 불릿 923건(9.2%), D(기부·후원) 팬덤 공존어 게이트 검증치 포함. `charts/build_cohesion_index_v7*.py` 입력 |
| `chart3d_correlation_live_v7.json` | 라이브 10,020건 | 3D 매트릭스 축 독립성: 3축 쌍별 상관·정규성·다중회귀(factor_diversity ~ loyalty + spillover)·VIF·영향점·LOO·민감도 |
| `topic_cards_v7.json` | 동결 스냅샷 7,350건 | K=10 토픽 카드: 명칭(METHODOLOGY.md 2-1 표와 동일)·상위 10개 키워드·대표 불릿 3건·대표 팬덤 5개·연결 F 경로 |
| `fandom_scores_v6.csv` | 동결 스냅샷 7,350건 | 팬덤별 loyalty/spillover/coverage/factor_diversity/dominant_factor/activity + F1~F5 비중(컬럼: 현장경제형=F3, 소비력형=F2, 미디어노출형=F4, 차트·확산형=F5, 결속형=F1). activity 합 = 7,350. 파일명의 v6은 파이프라인 버전 |
| `lda_v6_diagnostics_frozen_v7_40.json` | 동결 스냅샷 7,350건 | 동결 진단 원본(업로드 파일명 `lda_v6_diagnostics.json`): K-grid, selected_k=10, M=5, 실루엣 0.267, 토픽 상위어(=topic_cards), 토픽→F 배정 |
| `fandom_scores_v6.json` | 동결 스냅샷 7,350건 | 위 CSV의 JSON 원본: loyalty_raw/spillover_raw, 불릿 수, factor_share(M=5), coverage_detail(13개 언어 카운트 — 아랍어 추가 전, 언어 엔트로피 분모 ln(13)). r22판(5,612건, M=6)은 `data/v6_r22_snapshot/`에 별도 |
| `supplementary_csv/fandom_bullet_share_v6.csv` | v7 r17 (5,454건) | 팬덤별 근거문장 수·비중 (창모·사이먼도미닉·헤이즈 포함 구 로스터) |
| `supplementary_csv/domestic_regional_pilot_v6_top3.csv` | v7 r24 (5,998건) | 팬덤별 지역 언급·검출 지역 수·다양성·대표지역 top3 요약 (지역 값은 r22 파일럿과 99/100 동일) |
| `fan_persona_v7.json` | 동결 스냅샷 7,350건 | 페르소나 조합표(10개)·카운트(43/31/17/9)·팬덤별 top2 F·factor_specific_loyalty/spillover(= 비중 × 점수) |
| `persona_decision_space_v7.json` | 동결 스냅샷 7,350건 | Persona_결정공간.html 내장 데이터: K=10 토픽명·F코드·덴드로그램 병합 순서·PCA loading/좌표·팬덤별 F1~F5 비중 (`data_export/extract_html_payloads.py`) |

정합성 검증: 저장소 루트의 `verify_v7_final_consistency.py`.
실루엣 게이트 타임라인 CSV는 `../silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv`.
아직 없는 최종 산출물(넣으면 해당 스크립트가 바로 읽음): 국내 지역 지수 라이브판(아카이브명 `domestic_regional_pilot_v6.json` 또는
`domestic_regional_index_live_reference_v7.json`), `factor_clustering_structure_v7.json`. 그 밖의 아카이브 미보유분은 루트 README 3절.
