# archive/v6_r22_era — v7 라운드22 시점(근거문장 5,612건) 자료 보관

2026-09-22 정리에서 루트에서 옮긴, **최종 코퍼스(10,020건) 이전 시점** 자료다. 최종 제출본 수치의 근거가 아니며,
최종 데이터가 들어오기 전 세션에서 r22 스냅샷만으로 수행한 병행 분석·재구성 기록이다. 삭제하지 않고 보관하는 이유는
파이프라인이 실제로 어떻게 동작했는지 보여주는 실물 증거이고, 각 문서 상단 "2026-09-21 갱신 주"에 최종 자료와의
대응이 적혀 있기 때문이다. 필요 없으면 이 폴더 전체를 지우면 된다(루트의 스크립트·검증은 `data/v6_r22_snapshot/csv/
corpus_growth_history_v6_v7.csv`와 `domestic_regional_pilot_v6.json` 두 파일만 참조).

**10,020건 기준 새 판**: 이 폴더의 문서·노트북·스크립트를 최종 코퍼스·동결 스냅샷 기준으로 새로 구성한 판은 `v7_final_10020/analysis/`에 있다(2026-09-22). 이 폴더는 그 이후에도 수정하지 않는다.

| 항목 | 내용 |
|---|---|
| `data/v6_r22_snapshot/` | r22 코퍼스 5,612건, 점수(K=8·M=6·실루엣 0.154), 진단, 3D payload, v7_progress(r22), 파일럿 JSON, 파생 CSV. 폴더 README 참고 |
| `Ad_Commercial Pilot/`, `Fandom Cohesion Pilot/`, `Media Content Exposure Pilot/`, `Domestic Regional Pilot/`, `Worldwide Language Pilot/`, `Group_Member Pilot/` | 보조지표별 정리 문서 + r22 데이터 병행 분석 노트북(`DATA_DIR = ../data/v6_r22_snapshot`, 이 폴더 안에서 그대로 동작). 최종 원본 JSON은 `data/v7_final/`에 있다 |
| `fan_impact_ontology/` | K→F→Persona 고도화 전략 문서(5,794건 시점 기준) + r22 재적합 노트북 |
| `TOKENIZER/` | 다국어 불릿 언어 분류·토큰 빈도·jieba/pythainlp 스펙 문서와 스크립트(r22 코퍼스 기준, `BASE`는 이 폴더) |
| `TOKENIZER_WORDCLOUD_REPORT/tokenizer_script_routing_pilot.ipynb` | 문자권 라우팅 로직을 r22 코퍼스에 적용한 노트북 (보고서 본문·이미지는 `v7_final_10020/tokenizer_wordcloud_report/`에 유지) |
| `상세명세서/` | v6∼r22 기술 상세명세서(실제 방법론 문서, 5,612건·K=8·M=6 시점) |

동일 내용이 두 곳에 있던 파일은 정리 시 삭제했다: r1∼r22 병합 로그 사본(→ `data/v7_rounds/`), v6 단계 병합 로그 3개(→ `data/v7_rounds/`).
