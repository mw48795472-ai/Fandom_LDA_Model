# 세계 언어 지수(Worldwide Language Index) — 최종 코퍼스 10,020건 판

> `archive/v6_r22_era/Worldwide Language Pilot/WORLDWIDE_LANGUAGE_PILOT.md`(r22, 10개 언어, `ln(10)`)의 **10,020건·14개 언어 기준 새 판**.
> 입력은 최종 원본 `worldwide_language_pilot_live_reference_v7.json`(+CSV)과 라이브 점수 JSON의 `coverage_detail`. 실행 노트북: `worldwide_language_index_v7.ipynb`.

## 지표 정의 (원본 스크립트 컬럼 스키마, 14개 언어 ko/en/ja/zh/es/fr/th/id/vi/ru/tl/pt/tr/ar)

| 컬럼 | 정의 |
|---|---|
| 근거문장수 / 총언어언급 | 팬덤 근거문장 수 = 14개 언어별 언급 수의 합 (`language_counts`, 출처 도메인 기준 `language_of()`) |
| 검출언어수 | 언급 1건 이상인 언어 수 |
| 언어다양성 | 정규화 섀넌 엔트로피 −Σ p ln p / **ln(14)** |
| 해외근거문장수 / 해외비중 | ko 제외 합 / 근거문장수 |
| 검출해외언어수 / 해외언어다양성 | ko 제외 13개 언어 기준, 분모 ln(13) |
| 대표해외언어 / 비중 | ko 제외 최다 언어와 해외 언급 중 비중 |

## 노트북이 확인한 것

1. **LanguageCoverage 공식 재검증 — 세 시점 각각의 분모** — 라이브 10,020건(14개 언어, ln(14)) 100/100 · 동결 7,350건(13개, 아랍어 없음, ln(13)) 100/100 ·
   r22 5,612건(10개, ln(10)) 100/100. 다른 분모를 쓰면 100/100 불일치(`verify_v7_final_consistency.py` [V]·[Z]와 같은 결론).
2. **지수 재계산 vs 원본 JSON·CSV** — 8개 필드 모두 불일치 0/100, CSV 정수 컬럼 불일치 0. BTS 해외 135건(59.5% → 보고서 60%), 해외언어다양성 0.66.
   해외 근거문장수 상위: BLACKPINK 135(69.2%, 14개 언어 전부 검출) · BTS 135 · Stray Kids 129(79.1%) · TWICE 116 · SEVENTEEN 111 · NewJeans 108 · NCT 101 · LE SSERAFIM 97 · aespa 79 · ATEEZ 78.
3. **코퍼스 언어 구성 세 시점 비교** (팬덤별 `language_counts` 합; 라이브 값은 `language_domain_summary_v7.json`과 14개 언어 전부 일치)

| 언어 | 라이브 10,020 | 동결 7,350 | r22 5,612 |
|---|---:|---:|---:|
| 한국어 ko | 5,551 (55.4%) | 4,183 | 2,956 |
| 영어 en | 2,195 (21.9%) | 1,751 | 1,561 |
| 일본어 ja | 520 | 333 | 304 |
| 중국어 zh | 458 | 153 | 152 |
| 스페인어 es | 250 | 121 | 121 |
| 인도네시아어 id | 210 | 193 | 192 |
| 태국어 th | 209 | 181 | 181 |
| 필리핀어 tl | 137 | 133 | 0 |
| 프랑스어 fr | 101 | 4 | 4 |
| 포르투갈어 pt | 89 | 87 | 0 |
| 베트남어 vi | 85 | 71 | 72 |
| 아랍어 ar | 73 | 0 | 0 |
| 러시아어 ru | 71 | 72 | 69 |
| 튀르키예어 tr | 71 | 68 | 0 |

r39→r72 사이의 증가는 r68 아랍어·r69 프랑스어·r71 스페인어 보강 라운드(`data/v7_rounds/`)와 대응한다(README 성장 이력).

## 이 문서와 함께 보는 파일

- `data/v7_final/worldwide_language_pilot_live_reference_v7.json`, `worldwide_language_index_v7.csv`, `language_domain_summary_v7.json`, `fandom_scores_live_reference_v7.json`.
- `v7_final_10020/indices_csv/build_worldwide_language_index_csv.py` — CSV 산출 스크립트(불일치 0).
- `../tokenizer/build_multilingual_bullet_language_classifier_v7.py` — 도메인→언어 분류의 재구성·검증.

## 한계

1. 언어는 **출처 도메인** 기준이며 본문 언어가 아니다(한국 매체의 영문판, 해외 매체의 한국어판은 도메인 언어로 분류).
2. 14개 언어 외(독일어·이탈리아어 등)는 규칙이 없으면 기본값으로 흡수되므로 검출언어수는 하한이다.
3. 세 시점은 분모가 달라 language_coverage 절대치를 시점 간 비교할 수 없다.
