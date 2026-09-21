# Worldwide Language Pilot — 정리 및 실제 데이터 재현

## 이 문서가 다루는 것

"Worldwide Language Pilot"이라는 이름은 이번 세션이 직접 만든 것이 아니라,
두 곳에서 이미 언급되어 있던 것을 정리한 것입니다.

1. `docs/TOKENIZER_WORDCLOUD_REPORT.md`(업로드해주신 토크나이저 보고서)가
   "원본 상세 보고서 7.6절 Worldwide Language Pilot의 해외언어 비중 서술과
   같은 방향이다"라고 각주로 언급합니다 — 이 "원본 상세 보고서"는
   `팬덤100_LDA_v7_보고서.docx`로, 최종 제출 스냅샷(10,020건, K=10·M=5·
   실루엣=0.267) 기준 문서이며, **이번 세션에는 존재하지 않습니다.**
2. 저장소에 이미 `scripts/indices_csv/build_worldwide_language_index_csv.py`
   스크립트가 있습니다 — 이전 세션에서 "적용된 파이썬 코드 총정리" 작업 중
   함께 정리된 것으로, 원래 입력이었던
   `worldwide_language_index_live_reference_v7.json` 파일도 **이번 세션에는
   존재하지 않습니다**(경로가 `/home/claude/work/data/...`로, 이 프로젝트가
   시작하기 이전, 소실된 원본 작업 디렉터리를 가리킵니다).

즉 "Worldwide Language Pilot"의 정확한 원본 서술과 원본 산출 JSON은 이번
세션에 없습니다. 하지만 이 지표가 정확히 무엇을 계산하는지는 남아있는
스크립트의 컬럼 스키마로 알 수 있고, 그 계산에 필요한 원재료(언어별 근거
문장 수)는 이번 세션에 실제로 복구된 `data/v6_r22_snapshot/fandom_scores_v6.json`의
`coverage_detail.language_counts`에 100개 팬덤 전원 실제로 들어있습니다.
그래서 이 문서와 첨부 노트북은 **"원본 재현"이 아니라, 남아있는 스크립트의
정의를 그대로 이번 세션의 실제 데이터(v7 라운드22 스냅샷)에 적용한 병행
파일럿**입니다.

## 원본 스크립트가 정의하는 지표 (컬럼 스키마)

`scripts/indices_csv/build_worldwide_language_index_csv.py`의 주석과 코드가
정의하는 컬럼은 다음과 같습니다.

| 컬럼 | 정의 |
|---|---|
| 근거문장수 | 해당 팬덤의 전체 근거 문장 수 (`total_group_bullets`) |
| 총언어언급 | 14개 언어별 언급 수의 합 |
| 검출언어수 | 언급이 1건 이상인 언어의 개수 (`n_languages_hit`) |
| 언어다양성 | 언어 분포의 정규화 섀넌 엔트로피 (`language_diversity`) |
| 해외근거문장수 | 한국어(ko)를 제외한 언어의 언급 수 합 (`foreign_bullets`) |
| 해외비중 | 해외근거문장수 ÷ 근거문장수 (`foreign_ratio`) |
| 검출해외언어수 | 한국어를 제외하고 언급이 1건 이상인 언어 수 (`n_foreign_languages_hit`) |
| 해외언어다양성 | 한국어를 제외한 언어 분포만의 정규화 엔트로피 (`foreign_diversity`) |
| 대표해외언어 | 한국어를 제외하고 가장 많이 언급된 언어 (`primary_foreign_language`) |
| 대표해외언어비중 | 그 언어가 해외 언급 중 차지하는 비중 (`primary_foreign_share`) |

원본 스크립트는 14개 언어(ko/en/ja/zh/es/fr/th/id/vi/ru/tl/pt/tr/ar)를
다뤘습니다 — 이는 최종 v7 리포트(10,020건) 시점 기준입니다.

## 실제 복구된 round22 데이터와의 관계

`docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md` 6.1절(언어 커버리지)이 명시하는
공식은 다음과 같고, 이번 세션이 실제로 복구한 `fandom_scores_v6.json`에서
100개 팬덤 전원에 대해 정확히 일치함을 이미 확인했습니다(아래 첨부 노트북
1절에서 다시 직접 재검증합니다):

```
LanguageCoverage(f) = -Σ_l p(l)·ln(p(l)) / ln(10)   (l ∈ {ko,en,ja,zh,es,fr,th,id,vi,ru})
```

round22 스냅샷은 14개가 아니라 **10개 언어**만 다룹니다(최종 v7 리포트가 이후
라운드에서 필리핀어(tl)·포르투갈어(pt)·튀르키예어(tr)·아랍어(ar) 4개를 더
추가한 것으로 보이며, 그 확장 라운드는 이번 세션에 복구되지 않았습니다). 이
문서의 "언어다양성" 계산은 원본 스크립트의 14개 언어 기준이 아니라, 이번
세션이 실제로 가진 10개 언어 기준(`ln(10)` 정규화)을 그대로 사용합니다 —
따라서 이 노트북이 계산하는 "언어다양성" 값은 `fandom_scores_v6.json`의
`coverage_detail.language_coverage` 필드와 정확히 같은 값입니다(같은 공식,
같은 데이터). "해외언어다양성"(ko 제외)은 원본 스크립트에 정확한 정규화
분모가 명시되어 있지 않아, 이 노트북은 "가능한 9개 해외 언어"를 기준으로
`ln(9)`를 사용합니다 — 이는 원본 공식을 추정 확장한 것이며, 원본 문서에
명시된 값이 아님을 분명히 밝힙니다.

## 이 문서와 함께 보는 파일

- `analysis/worldwide_language_pilot.ipynb` — 아래 공식을 실제 100개 팬덤
  데이터에 적용해 표를 산출하고, 원본 `coverage_detail.language_coverage`
  필드와 재계산 결과를 대조 검증하는 노트북.
- `scripts/indices_csv/build_worldwide_language_index_csv.py` — 원본
  스크립트(원본 JSON 없이는 실행 불가, 컬럼 스키마 참고용으로 남겨둠).

## 한계 — 이번 파일럿이 재현하지 않는 것

1. **14개 언어 중 4개(tl/pt/tr/ar)는 round22 데이터에 아예 존재하지
   않습니다.** 최종 v7 리포트가 이 4개 언어를 언제, 어떤 라운드에서
   추가했는지는 이번 세션에 복구된 라운드 로그(v7 1~22라운드)에 나타나지
   않습니다.
2. **근거문장수·언어별 언급수의 절대값 자체가 다릅니다** — round22는
   100개 팬덤 5,612건 기준이고, 최종 v7 리포트는 10,020건 기준입니다. 이
   노트북의 표는 round22 기준의 **독립적인 병행 산출물**이지, 원본
   `worldwide_language_index_v7.csv`의 재현이 아닙니다.
3. **"해외언어다양성"의 정확한 정규화 분모**는 원본 스크립트·문서 어디에도
   명시되어 있지 않아, 이 노트북이 `ln(9)`로 추정한 것입니다.
