# 지표 산정 방법 (Ⅲ장) — 정리 및 실제 데이터 검증

> **2026-09-21 갱신 주** — 이 문서가 "이번 세션에 없다 / 재현 불가"라고 적은 최종 라이브 코퍼스(10,020건)와 최종 산출물이 이제 `data/v7_final/`에 있다(`fandoms_v3_100.json` 10,020건, `fandom_scores_v6.csv`·`fan_persona_v7.json`(동결 스냅샷 7,350건 기준), `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`(라이브 재적합 K=8/M=5/실루엣 0.046), `chart3d_payload_live_reference_v7.json`, `member_mention_index_v7.json`). r22 스냅샷(5,612건)은 `archive/v6_r22_era/data/v6_r22_snapshot/`으로 옮겨졌고, 이 문서의 노트북·스크립트가 참조하는 `../archive/v6_r22_era/data/v6_r22_snapshot` 경로는 그대로 동작한다. 본문의 5,612건 기준 병행 분석은 그 시점의 기록으로 유지하며, 최종 수치와의 대응은 `README.md` 1∼3절 참고.
> 이 문서 관련: 식(1)∼(2) EvidenceScore·min-max 정규화를 최종 라이브 코퍼스 10,020건에 적용하면 3D 포지셔닝맵의 100개 팬덤 loyalty/spillover 점수가 전부 재현된다(`verify_v7_final_consistency.py` [C]). 언어 엔트로피의 `ln(14)` 분모가 가리키는 14개 언어 최종 분포는 `language_domain_summary_v7.json`. `verify_index_calculation_formulas.py`의 데이터 경로는 `archive/v6_r22_era/data/v6_r22_snapshot/fandom_scores_v6.json`(r22, M=6)으로 정리했다. 추가로 이 문서가 다룬 "ln(14) 정규화 분모" 문제는 세 시점 파일로 실측됐다: r22(10개 언어)·동결 v7-40 `data/v7_final/fandom_scores_v6.json`(13개 언어, 분모 ln(13), 아랍어 추가 전)·최종 라이브 `fandom_scores_live_reference_v7.json`(14개 언어, 분모 ln(14)). 각 파일의 language_coverage가 해당 분모로만 100/100 재현된다(`verify_v7_final_consistency.py` [V]·[Z]).


## 이 문서가 다루는 것

업로드해주신 문서(「Ⅲ. 지표 산정 방법 — Measurement of Loyalty, Spillover, Coverage, and
Factor-Diversity Indices」)를 정리하고, 이번 세션에 실제로 복구된
`archive/v6_r22_era/data/v6_r22_snapshot/fandom_scores_v6.json`(100개 팬덤)과 기존에 이미 재구성해 둔
`analysis/run_lda_v6_reconstructed.ipynb`(생성 스크립트 `scripts/notebook_generator/
build_notebook.py`)의 실제 구현 코드를 대조해, 문서가 서술하는 5개 지표(팬충성도·파급효과·
근거 커버리지·팩터 다양성·활동량) 산식이 이번 세션의 실측 데이터·기존 코드와 정확히
일치하는지, 혹은 어디서 갈라지는지를 전면 검증했다.

이 문서는 이 프로젝트의 최종 보고서(v7) 본문 Ⅲ장 자체이며, 지금까지 이 세션에서 여러
문서(`docs/METHODOLOGY.md`, `docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md`)에 흩어져 있던
지표 정의들의 **공식적인 수식 번호(식 1∼7)와 정확한 키워드 목록의 원본**에 해당한다.

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

### 기존 재구성 코드와의 대조 — 2건의 실제 불일치 발견

`scripts/notebook_generator/build_notebook.py`(재구성 노트북 생성기)에 이미 이 식과 거의
동일한 `evidence_score()` 함수가 구현되어 있다. 문서와 코드를 한 글자씩 대조한 결과, 다음
2건의 실제 불일치를 발견했다.

1. **충성도 키워드 1개가 다르다.** 이 문서(원본)는 **"창단"**(그룹·조직을 창설한다는 뜻,
   K-pop 그룹 결성 맥락에 맞음)을 19개 키워드 중 하나로 명시하는데, 기존 재구성 코드
   (`LOYALTY_BONUS_KW`)에는 **"창당"**(정당을 창설한다는 뜻, 이 문맥과 무관함)으로 되어
   있다. 나머지 18개 키워드는 완전히 일치한다. 발음이 비슷한 한 글자 차이(단→당)로,
   재구성 과정에서 생긴 오기로 추정된다.
2. **`n_num`의 정의 자체가 다르게 구현되어 있다.** 문서는 `n_num(t)`을 "수치표현 **패턴**의
   개수"로 정의한다 — 즉 "2026년"이나 "120만 장"처럼 숫자+단위가 붙은 표현 하나를 1건으로
   센다. 그러나 기존 재구성 코드는 `n_num = len(re.findall(r"\d", text))`로 구현되어 있어,
   **문장에 등장하는 개별 숫자 문자(digit) 수를 그대로 센다.** 예를 들어 "2026년 3월"이라는
   구절은 문서 정의로는 수치표현 2건(2026년, 3월)이지만, 코드 구현으로는 숫자 문자 5개
   (2,0,2,6,3)로 계산되어 EvidenceScore가 부풀려진다. 두 방식은 근거문장에 큰 숫자나
   연도가 많이 등장할수록 격차가 벌어지는 구조적 차이다.

파급효과 보너스 키워드 18개는 문서와 코드가 **완전히 일치**한다(전수 대조, 불일치 0건).

이 두 불일치는 재구성 코드가 "완전히 새로 지어낸 것"이 아니라 "원본 공식을 거의 정확히
재현했지만 세부 구현에서 미세하게 갈라진 것"임을 보여준다 — 100개 팬덤의 최종
`loyalty_raw`/`spillover_raw`/`loyalty_score`/`spillover_score` 값 자체는 원본 파이프라인
(이번 세션에 소스코드가 없음)이 계산한 실측값이므로 이 불일치의 영향을 받지 않지만, 만약
이 재구성 코드로 EvidenceScore를 처음부터 다시 계산하려 한다면 두 지점 모두 원문 정의대로
고쳐야 한다.

### min-max 정규화(식 2) — 실측 100개 팬덤 전체 재검증

`fandom_scores_v6.json`의 `loyalty_raw`/`spillover_raw`(원점수)로부터 표본 min-max를
계산해, 저장된 `loyalty_score`/`spillover_score`와 다시 대조했다.

- **loyalty_score 재계산 불일치: 0/100**
- **spillover_score 재계산 불일치: 0/100**

식 (2)는 실측 데이터에 정확히 그대로 적용되어 있음이 확인된다.

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

이 가중치(0.30/0.25/0.20/0.15/0.10)와 시장 6분류·엔티티 6분류 정의는 이번 세션에서 이미
`fandom_scores_v6.json`의 `coverage_detail.weights` 필드(100개 팬덤 전원 가중치 불일치
0건, 이전 `group_member_fpu_pilot.ipynb`에서 검증됨) 및 `docs/LDA_V6_V7_TECHNICAL_
SPECIFICATION.md`의 엔티티 정의 문구와 **정확히 일치함을 이미 확인한 바 있다** — 이번
업로드 문서는 그 값들의 원본 출처(Ⅲ장 식 3, 표 2)를 그대로 확인시켜 준다.

**언어 엔트로피 정규화 분모(식 4)에 대한 참고**: 이 문서는 14개 언어 기준 `ln(14)`로
정규화한다고 명시한다. 그러나 이번 세션에 복구된 round22 스냅샷은 14개가 아니라 **10개
언어**만 실제로 관측되며(`docs/WORLDWIDE_LANGUAGE_PILOT.md`에서 이미 확인), 이 스냅샷의
`language_coverage` 필드는 `ln(14)`가 아니라 `ln(10)`으로 정규화되어 있다(100개 팬덤
전원 일치, 이미 검증 완료). 이는 이번 문서 발견으로 생긴 새로운 모순이 아니라, "최종 v7
리포트(14개 언어 완성 시점) 기준 공식"과 "이번 세션이 실제로 가진 round22 스냅샷(10개
언어만 도달한 중간 시점)" 사이의 **시점 차이**로 이미 설명되어 있던 것이며, 이번 업로드
문서가 바로 그 "14개 언어 기준" 최종 공식의 원본임을 확인시켜 준다.

## 3. 팩터 다양성 — LDA 메타팩터 분포의 엔트로피

```
FactorShare(f, m) = Σ_{e∈f} Σ_{t∈m} θ(d,t) / Σ_{e∈f} Σ_t θ(d,t)               (5)
FactorDiversity(f) = − Σ pₘ ln pₘ / ln(M)                                     (6)
```

`θ(d,t)`는 문서 d의 토픽 t에 대한 LDA 토픽 비중이다. 이 정의는 `fandom_scores_v6.json`의
`factor_share`가 왜 정수 카운트가 아니라 연속값인지(토픽-문서 혼합비중의 합이기 때문)를
공식적으로 설명해준다 — Ad/Commercial Pilot·Fandom Cohesion Pilot·Media Content Exposure
Pilot 문서에서 이미 "activity×factor_share가 정수에 가깝게 맞아떨어지지 않는다"고 실측으로
확인했던 현상이, 이 식(5)으로 정확히 설명된다.

**식(6) 재검증**: `fandom_scores_v6.json`의 `factor_diversity` 필드를, 각 팬덤의
`factor_share`(M=6개 메타팩터) 분포로부터 `-Σp·ln(p)/ln(6)`을 직접 재계산해 대조했다.

- **factor_diversity 재계산 불일치: 0/100**

이번 세션에서 처음으로 이 필드의 산식 자체를 공식으로 확인·재검증했다(기존에는 이
필드가 존재한다는 것만 알고 있었을 뿐, 정확한 산식은 이번 업로드 문서로 처음 확인됨).

**주 팩터(dominant factor)** 정의(FactorShare 최댓값)도 이미 여러 파일럿 문서(Ad/Commercial·
Fandom Cohesion·Media Content Exposure)에서 `dominant_factor` 필드를 재계산해 100개 팬덤
전원 일치를 확인한 바 있다.

## 4. 활동량(Activity)

```
Activity(f) = n_loyalty(f) + n_spillover(f)                                    (7)
```

`fandom_scores_v6.json`의 `activity` 필드가 `n_loyalty_bullets + n_spillover_bullets`와
정확히 같은지 재검증했다.

- **activity 재계산 불일치: 0/100**

## 종합 — 이 문서로 새로 확인/발견된 것

1. **새로 확인된 것(0건 불일치)**: min-max 정규화(식 2), Coverage Index 가중치(식 3, 기존
   확인 재확인), FactorDiversity 엔트로피 공식(식 6, **이번에 처음 공식 확인**), Activity
   정의(식 7) — 전부 100개 팬덤 전량 재계산 결과 실측 데이터와 정확히 일치.
2. **새로 발견된 것(2건의 실제 불일치)**: 기존 재구성 코드(`build_notebook.py`)의
   `LOYALTY_BONUS_KW`에 있는 "창당"이 원본 문서의 "창단"과 다르다는 것, 그리고 `n_num`
   구현이 원본의 "수치표현 패턴 개수"가 아니라 "숫자 문자 개수"로 되어 있다는 것 — 둘 다
   재구성 당시 세부 구현에서 생긴 차이이며, 100개 팬덤의 실측 최종 지표값 자체에는 영향을
   주지 않지만(원본 파이프라인이 이미 계산해 둔 값을 그대로 쓰고 있으므로), 이 재구성
   코드로 값을 처음부터 다시 산출하려 할 경우 반드시 고쳐야 하는 지점이다.

## 이 문서와 함께 보는 파일

- `scripts/methodology/verify_index_calculation_formulas.py` — 위 7개 식을 함수로
  정리하고, `fandom_scores_v6.json` 100개 팬덤 전체에 대해 이 문서에서 수행한 모든 재검증
  (식 2·4·6·7)을 그대로 재현하는 스크립트. 발견된 2건의 불일치(창당/창단, n_num 정의)도
  코드 주석과 실행 시 출력으로 함께 표시한다.

## 한계

1. 이 문서의 식(1) EvidenceScore·보너스 키워드 매칭은 **원본 파이프라인의 문장 단위
   원시 계산 로직**을 서술한 것이며, 그 계산이 실제로 적용된 문장 단위 중간 결과(개별
   근거문장의 EvidenceScore)는 이번 세션에 남아있지 않다 — 팬덤별 최종 합산값
   (`loyalty_raw`/`spillover_raw`)만 실측으로 존재한다. 따라서 위에서 발견한 2건의
   불일치가 실제 원본 파이프라인에도 있었는지, 아니면 이번 세션의 재구성 과정에서만
   생긴 것인지는 검증할 수 없다(원본 소스코드 자체가 소실됨).
2. 언어 엔트로피(식 4)의 `ln(14)` 정규화는 최종 v7 리포트(14개 언어 완성 시점) 기준이며,
   이번 세션이 가진 round22 스냅샷(10개 언어)에는 `ln(10)`이 적용되어 있다 — 이는 이미
   `docs/WORLDWIDE_LANGUAGE_PILOT.md`에 문서화된 시점 차이이지 새로운 오류가 아니다.
