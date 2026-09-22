# data/v7_rounds — v7 라운드별 병합·교체 로그 전량 (r1 ∼ r74)

원본 로그 69개(원본 데이터 묶음 README 7절의 `v7_rounds/` 전량). 최종 보고서가 라운드별
진행 서술에 인용하는 파일들이며, 파일명의 숫자가 라운드 번호(v7 N)다.

| 파일 | 내용 |
|---|---|
| `v6_merge_log.json`, `v6_3_market_merge_log.json`, `v6_4_language_merge_log.json` | v6 단계 병합 로그(1·2차, 시장 보강, 언어 보강) — 성장 이력 CSV의 앞부분 |
| `merge_log_r1.json` ∼ `merge_log_r72.json` (60개) | 리서치 병합 로그. r36∼r59는 `before_total_bullets`/`after_total_bullets` 키, 나머지는 `before_total`/`after_total` 키. r58은 `round_type=roster_swap`(BE'O→빈지노). 마지막 r72가 9,939 → **10,020건**(최종 라이브 코퍼스) |
| `swap_log_r29.json`, `swap_log_r34.json`, `swap_log_r62.json`, `swap_log_r63.json` | 로스터 교체: 사이먼도미닉→GOT7(r29), 창모→김재중·헤이즈→박서진(r34), 한로로→몬스타엑스(r62), pH-1→투어스(TWS)(r63). r58(BE'O→빈지노)과 합쳐 동결 스냅샷(7,350건)과 라이브 로스터의 3개 차이를 설명 |
| `round_log_r70.json` | 언어별 도메인 표 갱신 라운드(순증 0, 빈지노 프랑스어 위키 1건 재분류) |
| `member_pilot_r53_compare.json` ∼ `r55` | 멤버 전수조사 라운드 전후 MCI 비교 |
| `schema_audit_r74.json` | 최종 코퍼스 스키마 감사: 10,020건, 팬덤 100, LDA 3토큰 미만 제외 2건 |

검증(`verify_v7_final_consistency.py` [AB]): 병합 로그의 after_total이 실루엣 타임라인 CSV의 같은 라운드 코퍼스와 56건 전부
일치. 체인 불연속은 로그 자체 기록대로 4곳(r21→r22 +1, r22→r23 -1, r39→r41 사이 7,350→7,513, r59→r62 사이 9,042→9,440)이며
`v7_final_10020/data_export/build_corpus_growth_history_csv.py`가 만드는 `data/v7_final/corpus_growth_history_v6_v7_full.csv`의 `chain_gap` 컬럼에 그대로 적혀 있다.
