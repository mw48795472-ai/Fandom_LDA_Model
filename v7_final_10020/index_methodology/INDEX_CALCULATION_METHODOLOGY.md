# 지표 산정 방법 (Ⅲ장) — 정리 및 실제 데이터 검증

## 이 문서가 다루는 것

최종 보고서 Ⅲ장(「지표 산정 방법 — Measurement of Loyalty, Spillover, Coverage, and
Factor-Diversity Indices」)이 정의하는 5개 지표(팬충성도·파급효과·근거 커버리지·팩터 다양성·
활동량)의 산식을 정리하고, 그 산식을 저장소의 최종 산출 데이터에 직접 적용해 저장된 값이
그대로 재현되는지 전량 검증한다. 검증 대상 파일은 두 계층이다.

| 파일 | 기준 | 팬덤 수 | 메타팩터(M) | 추적 언어 |
|---|---|---|---|---|
| `data/v7_final/fandom_scores_live_reference_v7.json` | 최종 근거 코퍼스 10,020건 (3D 포지셔닝맵·4구획의 원본) | 100 | 5 | 14 (ko·en·ja·zh·es·fr·th·id·vi·ru·tl·pt·tr·ar) |
| `data/v7_final/fandom_scores_v6.json` | 동결 스냅샷 v7-40 7,350건 (해석 계층·페르소나의 원본) | 100 | 5 | 13 (아랍어 추가 전) |

이 문서는 이 프로젝트의 지표 정의들(`docs/METHODOLOGY.md`, `analysis/LDA_V6_V7_TECHNICAL_
SPECIFICATION.md`)의 **공식적인 수식 번호(식 1∼7)와 정확한 키워드 목록의 원본**에 해당한다.

## 5개 지표 요약

| 지표 | 식 | 정의 |
|---|---|---|
| 팬충성도(Loyalty)·파급효과(Spillover) | (1)(2) | 근거문장별 원점수(숫자표현+보너스키워드 가중합) 합산 후 표본 내 min-max 정규화 |
| 근거 커버리지 지수(Coverage Index) | (3)(4) | 언어(0.30)·시장(0.25)·출처유형(0.20)·시간(0.15)·엔티티(0.10) 5개 하위지표 가중합 |
| 팩터 다양성(Factor Diversity) | (5)(6) | LDA 메타팩터별 비중(FactorShare) 분포의 정규화 섀넌 엔트로피 |
| 활동량(Activity) | (7) | 충성도+파급효과 근거문장 수의 단순 합(정규화하지 않은 원시 지표) |

## 1. 팬충성도·파급효과 — EvidenceScore와 min-max 정규화

```
EvidenceScore(f) = Σ [ 1.0 + 0.5·n_num(t) + 0.3·n_kx(t) ]                     (1)
Score(f) = (ScoreRaw(f) − min) / (max − min)                                  (2)
```

`n_num(t)`은 문장 t에 포함된 **수치표현 패턴**("120만 장", "1위" 등 만·억·조·%·명·장·위·회·
건·주·배·년 단위가 붙은 표현)의 개수, `n_kx(t)`는 지표별 보너스 키워드 집합과의 일치 횟수다.

**보너스 키워드 목록(원문)**

| 지표 | 키워드(n) |
|---|---|
| 충성도(Loyalty) | 기부·돌파·매진·출범·**창단**·결성·총공·역사·지속·확장·1위·최초·신기록·밀리언셀러·팬클럽·팬카페·결속·충성·세대 (n=19) |
| 파급효과(Spillover) | 경제효과·매출·관광·지자체·앰버서더·모델·브랜드·팝업·협업·관중·방문·상권·지역·홍보대사·수익·투어·콘서트·소비 (n=18) |

### 식(1) — 최종 코퍼스 10,020건으로 원점수 완전 재현

식(1)을 `data/v7_final/fandoms_v3_100.json`(10,020건)의 팬덤별 `loyalty`/`spillover` 근거문장에
그대로 적용하면(`verify_v7_final_consistency.py` [C]·[V]):

- `loyalty_raw`/`spillover_raw` 재계산 불일치: **0/100** (오차 1e-6 이내)
- 이를 식(2)로 정규화한 점수는 3D 포지셔닝맵 payload(`chart3d_payload_live_reference_v7.json`)의
  100개 팬덤 loyalty/spillover와 소수점 셋째 자리까지 전부 일치

즉 최종 점수는 저장소 안의 코퍼스와 이 문서의 산식만으로 처음부터 끝까지 재현된다.

### 구현 시 주의할 두 지점

산식을 코드로 옮길 때 실제로 결과를 바꾸는 지점이 둘 있다. 두 지점 모두
`verify_index_calculation_formulas.py`가 실행 시 예시 문장으로 차이를 출력한다.

1. **충성도 키워드는 "창단"(그룹·조직 창설)이다.** 발음이 비슷한 "창당"(정당 창설)으로 옮기면
   19개 중 1개가 어긋나 해당 단어가 든 문장의 점수가 달라진다.
2. **`n_num`은 "수치표현 패턴의 개수"이지 "숫자 문자의 개수"가 아니다.** "2026년 3월"은
   패턴 2건(2026년, 3월)이지 숫자 문자 5개가 아니다. 숫자 문자를 세면 연도·큰 숫자가 많은
   문장의 EvidenceScore가 구조적으로 부풀려져 원점수가 재현되지 않는다.

### min-max 정규화(식 2) — 실측 100개 팬덤 전체 재검증

`fandom_scores_live_reference_v7.json`의 `loyalty_raw`/`spillover_raw`(원점수)로부터 표본
min-max를 계산해, 저장된 `loyalty_score`/`spillover_score`와 다시 대조했다
(`verify_index_calculation_formulas.py`).

- **loyalty_score 재계산 불일치: 0/100**
- **spillover_score 재계산 불일치: 0/100**

## 2. 근거 커버리지 지수 — 5개 하위지표 가중합

```
CoverageIndex(f) = 0.30·Lang + 0.25·Mkt + 0.20·Src + 0.15·Time + 0.10·Ent      (3)
Lang(f) = − Σ pᵢ ln pᵢ / ln(14)        (pᵢ: 14개 추적 언어 중 언어 i의 인용 비율)    (4)
```

| 하위지표 | 가중치 | 정의 |
|---|---|---|
| 언어(Language) | 0.30 | 14개 언어(ko·en·ja·zh·es·fr·th·id·vi·ru·tl·pt·tr·ar) 인용 분포의 정규화 섀넌 엔트로피 |
| 시장(Market) | 0.25 | 언급 지역 수 ÷ 6 (일본·중화권·미국/북미·유럽·동남아·글로벌) |
| 출처유형(Source Type) | 0.20 | 출처유형 수 ÷ 3 (뉴스매체·커뮤니티/SNS·위키/레퍼런스) |
| 시간(Time) | 0.15 | 언급 연도 수 ÷ 코퍼스 전체 연도 범위 수 |
| 엔티티(Entity) | 0.10 | 제3자 기관·플랫폼 카테고리 수 ÷ 6 (방송사·국내음원차트·해외차트/시상식·글로벌플랫폼·대형공연장·매체/어워드) |

**식(3) 재검증**: 두 점수 파일 모두 `coverage_detail.weights` 필드가 0.30/0.25/0.20/0.15/0.10으로
100개 팬덤 전원 일치하며, 하위지표 5개의 가중합이 저장된 `coverage_index`와 일치한다
(불일치 0/100). 시장 6분류·엔티티 6분류 정의는 `coverage_detail.markets_mentioned`·
`entity_types_mentioned`에 실제로 등장하는 값과 기술 상세명세서의 정의 문구가 일치한다.

**식(4) 정규화 분모 — 두 계층에서 각각 재현**: `language_coverage`를 `language_counts`로부터
정규화 엔트로피로 재계산하면(`verify_v7_final_consistency.py` [V]·[Z]),

| 파일 | 실제 관측 언어 수 | 분모 | 재현 |
|---|---|---|---|
| `fandom_scores_live_reference_v7.json` (최종 10,020건) | 14 | ln(14) | 100/100 |
| `fandom_scores_v6.json` (동결 v7-40) | 13 | ln(13) | 100/100 (ln(14)로는 0/100) |

동결 스냅샷은 아랍어(ar)가 코퍼스에 추가되기 전 시점이라 13개 언어로 정규화되어 있다. 14개
언어의 최종 분포는 `data/v7_final/language_domain_summary_v7.json`에 있다.

## 3. 팩터 다양성 — LDA 메타팩터 분포의 엔트로피

```
FactorShare(f, m) = Σ_{e∈f} Σ_{t∈m} θ(d,t) / Σ_{e∈f} Σ_t θ(d,t)               (5)
FactorDiversity(f) = − Σ pₘ ln pₘ / ln(M)                                     (6)
```

`θ(d,t)`는 문서 d의 토픽 t에 대한 LDA 토픽 비중이다. 이 정의는 점수 파일의 `factor_share`가
왜 정수 카운트가 아니라 연속값인지(토픽-문서 혼합비중의 합이기 때문)를 설명한다 — 광고·상업성,
팬덤 결속, 미디어 노출 지수 노트북에서 확인되는 "activity×factor_share가 정수에 맞아떨어지지
않는" 현상이 이 식(5)으로 설명된다.

**식(6) 재검증**: `factor_share`(M=5개 메타팩터) 분포로부터 `−Σp·ln(p)/ln(5)`를 직접
재계산해 저장된 `factor_diversity`와 대조했다.

- **factor_diversity 재계산 불일치: 0/100**

최종 파일의 메타팩터 5개는 현장경제형·소비력형·결속형·브랜드·상업형·차트·확산형(최종 코퍼스
참고 재적합 K=8→M=5), 동결 파일의 5개는 현장경제형·소비력형·미디어노출형·차트·확산형·결속형
(동결 K=10→M=5)이다. 두 파일의 M은 같지만 팩터 구성이 다르므로 `factor_share`를 파일 간에
직접 비교하면 안 된다.

**주 팩터(dominant factor)** 정의(FactorShare 최댓값)는 `dominant_factor` 필드를 재계산해
100개 팬덤 전원 일치를 확인했다(보조지표 노트북 3종).

## 4. 활동량(Activity)

```
Activity(f) = n_loyalty(f) + n_spillover(f)                                    (7)
```

`activity` 필드가 `n_loyalty_bullets + n_spillover_bullets`와 정확히 같은지 재검증했다.

- **activity 재계산 불일치: 0/100** (100개 팬덤 합계 = 10,020건)

## 종합

1. **식(1)∼(7) 전부 저장소 데이터로 재현된다.** EvidenceScore(식 1)는 최종 코퍼스 10,020건에서
   원점수를 100/100 일치(불일치 0)로 재현하고, min-max(식 2)·Coverage 가중합(식 3)·언어 엔트로피(식 4)·
   FactorDiversity(식 6)·Activity(식 7)는 최종·동결 두 점수 파일 모두에서 100개 팬덤 전량 일치한다.
2. **식(4)의 분모만 계층에 따라 다르다.** 최종 10,020건은 ln(14), 동결 v7-40은 ln(13). 보고서
   Ⅲ장의 "14개 언어"는 최종 코퍼스 기준이다.
3. **구현 시 주의점은 "창단" 키워드와 `n_num`의 패턴 개수 정의** 두 가지이며, 둘 중 하나라도
   다르게 구현하면 식(1)의 원점수가 재현되지 않는다.

## 이 문서와 함께 보는 파일

- `index_calculation_v7.ipynb` (같은 폴더, 실행 결과 포함; Jupyter 없이 Spyder·VS Code에서 열려면 같은 내용의 `# %%` 셀 스크립트 `index_calculation_v7.py`) — 식(1)∼(7)을
  코퍼스 10,020건에 직접 적용해 100개 팬덤의 지표를 **산정**하는 노트북. 문장별 EvidenceScore 분해 예시, min-max, 활동량,
  커버리지 하위지표 5개와 가중합, 팩터 다양성·주 팩터, 4구획·χ²까지 만들어 `index_calculation_v7_result.csv`(100행×17열)로 저장하고
  마지막 절에서 최종 산출 파일과 전량 대조한다(8개 항목 전부 100/100 일치, 불일치 0). 생성기는 `build_index_calculation_notebook.py`.
- `verify_index_calculation_formulas.py` (같은 폴더) — 위 7개 식을 함수로 정리하고,
  `fandom_scores_live_reference_v7.json` 100개 팬덤 전체에 대해 식(2)(3)(6)(7) 재검증을 재현하는
  스크립트. 구현 시 주의점 두 가지(창단/창당, `n_num` 정의)를 예시 문장으로 함께 출력한다.
- `verify_v7_final_consistency.py` (저장소 루트) — [C]·[V]·[Z] 항목에서 식(1)의 원점수 재현과
  ln(14)/ln(13) 분모를 코퍼스·점수 파일로 직접 확인한다.
- `data/v7_final/README.md` — 두 점수 파일과 코퍼스 파일의 계층 구분.
- `EXPOSURE_ADJUSTMENT_V7.md` + `build_exposure_adjusted_scores_v7.py` (같은 폴더, L12) — 같은 문장 점수에서 건수에 덜 의존하는 정의(밀도·노출량 잔차)를 만들어 원 지수와 나란히 둔 병행 분석과 `exposure_adjusted_scores_v7.csv`.

## 한계

1. 식(1)의 문장 단위 중간 결과(개별 근거문장의 EvidenceScore)는 원 산출물에는 없었다. 지금은
   `export_evidence_score_sentences_v7.py`가 `evidence_score_by_sentence_v7.csv`(10,020행: 수치표현 수·보너스 키워드·문장 점수·연도)로
   저장하며, 팬덤별 합이 `loyalty_raw`/`spillover_raw`와 100/100 일치함을 스크립트가 확인한다.
2. 시간(Time) 하위지표의 분모("코퍼스 전체 연도 범위 수")도 원 산출물에는 `years_mentioned`만 있었다. 같은 스크립트가
   `index_intermediate_values_v7.json`에 코퍼스 연도 목록(2015∼2026, 12개)과 `time_coverage` 재현 100/100을 기록한다.
3. **식(1)·(2)의 점수는 조사 노출량(팬덤별 수집 불릿 수)에 비례한다.** 합의 min-max 라 점수와 건수의 r이 라이브 0.90(충성도)·0.96(파급효과), 동결 0.94·0.96이다. 활동을 통제한 충성도·파급효과 편상관은 음수(−0.38)로, 판별타당도 r(0.49 vs 동결 0.64)의 반전은 건수 구조의 산물이다. 문장당 평균 EvidenceScore(밀도) 정의로 보면 r은 라이브 0.43·동결 0.40으로 두 스냅샷 모두 기준(|r|<0.5)을 만족하고 상위 15 순위는 5/15만 겹친다(`EXPOSURE_ADJUSTMENT_V7.md`). 원 지수는 '규모', 밀도는 '근거 한 건의 밀도'라는 다른 질문이므로 병기한다.
