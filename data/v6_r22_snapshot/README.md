# data/v6_r22_snapshot — v7 라운드22 스냅샷 (근거문장 5,612건, 2026-09-04 시점)

최종 제출본 수치가 아니다. `v7_progress.json` 기준 코퍼스 5,612건(누적 배수 3.151×), 이 시점 LDA 재적합
`lda_v6_diagnostics.json`은 K=8, M=6, 실루엣 0.154. 최종 제출본(동결 스냅샷 7,350건 K=10/M=5/0.267, 라이브 10,020건)은
`data/v7_final/`에 있다. 이 폴더는 파이프라인이 실제로 어떻게 동작했는지 보여주는 실물 증거이자, 각 파일럿 노트북
(`../../*/…_pilot.ipynb`, `DATA_DIR = Path("../data/v6_r22_snapshot")`)의 입력이다.

| 파일 | 내용 |
|---|---|
| `fandoms_v3_100.json` | 근거문장 원본 코퍼스 5,612건 (100개 팬덤 × loyalty/spillover) |
| `fandom_scores_v6.json` / `.csv` | 팬덤별 점수·factor_share(M=6)·factor_diversity·coverage_index(+coverage_detail)·dominant_factor·activity |
| `lda_v6_diagnostics.json` | K-grid, selected_k=8, M=6, 실루엣 0.154, 토픽 상위어, 토픽→F 배정, F 라벨 |
| `chart3d_payload_v6.json` | 이 시점 3D 매트릭스 payload |
| `v7_progress.json` | 10배 확대 프로젝트 진행 추적 (라운드별 이력) |
| `v6_merge_log.json`, `v6_3_market_merge_log.json`, `v6_4_language_merge_log.json` | v6 단계 병합 로그 |
| `v7_rounds/merge_log_r1.json` ~ `r22.json` | v7 라운드별 병합 로그 (r21→r22 사이 1건, r22 after_total 5,613 vs 실제 5,612의 기록 오차는 상세명세서·실루엣 게이트 문서에 기록됨) |
| `domestic_regional_pilot_v6.json`, `member_mention_pilot_v6.json` | 국내 지역 지수·멤버 집중도 지수 파일럿 |
| `csv/` | 위 파일들에서 파생한 CSV: `bullets_flat_v6_r22.csv`(5,612행), `lda_k_grid_v6.csv`, `corpus_growth_history_v6_v7.csv`, `domestic_regional_pilot_v6.csv`, `member_concentration_pilot_v6.csv`, `member_mentions_pilot_v6_long.csv` |
