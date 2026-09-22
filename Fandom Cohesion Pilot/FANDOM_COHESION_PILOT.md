# Fandom Cohesion Pilot — 정리 및 실제 데이터 병행 산출

> **2026-09-21 갱신 주** — 이 문서가 "이번 세션에 없다 / 재현 불가"라고 적은 최종 라이브 코퍼스(10,020건)와 최종 산출물이 이제 `data/v7_final/`에 있다(`fandoms_v3_100.json` 10,020건, `fandom_scores_v6.csv`·`fan_persona_v7.json`(동결 스냅샷 7,350건 기준), `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`(라이브 재적합 K=8/M=5/실루엣 0.046), `chart3d_payload_live_reference_v7.json`, `member_mention_index_v7.json`). r22 스냅샷(5,612건)은 `data/v6_r22_snapshot/`으로 옮겨졌고, 이 문서의 노트북·스크립트가 참조하는 `../data/v6_r22_snapshot` 경로는 그대로 동작한다. 본문의 5,612건 기준 병행 분석은 그 시점의 기록으로 유지하며, 최종 수치와의 대응은 `README.md` 1~3절 참고.
> 이 문서 관련: 팬덤결속 지수 원본 `fandom_cohesion_index_v7.json`은 아직 저장소에 없다. `charts/build_cohesion_index_v7*.py`는 `data/v7_final/fandom_cohesion_index_v7.json`을 읽도록 경로를 정리했다.


## 이 문서가 다루는 것

"Fandom Cohesion Pilot"(팬덤결속 지수, Fandom Cohesion Index)은 저장소에 남아있는 차트
스크립트 2개로부터 정리한 것이다.

- `scripts/charts/build_cohesion_index_v7.py` (좌우 2패널 통합본)
- `scripts/charts/build_cohesion_index_v7_right_only.py` (우측 패널만 분리한 단독본)

두 스크립트 모두 맨 위 주석에 이 지수의 정체를 명확히 밝히고 있다: **"LDA 토픽/K→M→F
재군집화와 무관한 원문 키워드 매칭 보조지표"**이며, v7 45라운드(2차, 후속)에 신설되어
`ad_commercial_index_v7.py`(광고·상업성 지수, 3.9절)의 차트 쌍과 "나란히 비교할 수 있도록
일부러 동일한 시각화 방식"으로 맞췄다고 명시되어 있다. 입력은
`/home/claude/work/data/fandom_cohesion_index_v7.json`인데, 이 경로는 이전 세션의 소실된
작업 디렉터리를 가리키며 **이번 세션에는 존재하지 않는다** — Ad/Commercial Pilot과 정확히
같은 상황이다.

## 원본 스크립트가 정의하는 5개 결속 활동 유형(A~E)

`build_ad_commercial_index_csv.py`(업종 20개를 원본 JSON에서만 읽어와 코드에 전혀 남지
않았던 경우)와 달리, 이 차트 스크립트는 **5개 카테고리 정의 자체가 코드에 하드코딩되어
있어 그대로 복구된다.**

| 코드 | 유형 | 차트 색상(hex) |
|---|---|---|
| A | 공식 팬클럽·회원제 | `#2a78d6` |
| B | 팬카페·온라인 커뮤니티 | `#4fb3a9` |
| C | 팬덤 정체성·문화 | `#8e6fc2` |
| D | 기부·후원 캠페인(팬덤 주도) | `#e0863f` |
| E | 오프라인 결집·이벤트 | `#c0392b` |

원본 차트가 실제로 그리는 것은 ① 좌측 패널 — 이 5개 유형별 근거문장 순위(수평 막대,
전체 대비 비중% 라벨 포함), ② 우측 패널 — 상위 25개 팬덤의 유형 구성을 누적 막대로 표시
(BTS·임영웅·리센느(RESCENE) 3개 팬덤은 축 라벨을 굵게 강조), 그리고 상단 부제목에
"전체 X문장 중 Y건(Z%)이 팬덤결속 신호 포함, N/100개 팬덤에서 1건 이상 등장"이라는 코퍼스
전체 커버리지 문구를 표시한다. 이 값들(`category_totals`, `total_cohesion_bullets`,
`total_bullets`, `corpus_cohesion_share`, `n_fandoms_with_any_cohesion_bullet`,
팬덤별 `category_counts`/`n_cohesion_bullets`/`cohesion_share`)은 전부 원본 JSON 안에
있던 것이라, **이번 세션에서는 실제 수치를 하나도 복구할 수 없다.**

## 이번 세션에 실제로 있는 것 — 대체 가능한 실데이터

Ad/Commercial Pilot과 같은 논리로, 이번 세션에 복구된 `data/v6_r22_snapshot/
fandom_scores_v6.json`의 K=8/M=6 LDA 메타요인 `factor_share`에는 개념적으로 가장 가까운
실수치가 이미 들어있다.

```
"결속형(팬클럽·기부·커뮤니티)"
```

`docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md` 4장 LABEL_RULES 표가 이 메타요인(F4)의 정의를
그대로 보존하고 있다.

| 코드 | 라벨 | 매칭 키워드 |
|---|---|---|
| F4 | 결속형(팬클럽·기부·커뮤니티) | 공식, 팬클럽, 팬덤, 데뷔, 기부, 2025년, 활동, 2026년 |

두 지표의 키워드 어휘 자체가 상당히 겹친다는 점("공식", "팬클럽", "기부"가 원본 A/D 유형
정의와도 겹친다)이 흥미롭지만, 이는 **우연이 아니라 두 지표가 같은 개념(팬클럽 활동·기부·
결속)을 가리키기 때문**이며, 계산 방법은 여전히 다르다(원본은 키워드 매칭 기반 카테고리
분류, 이번 세션의 것은 LDA 토픽 혼합비중 기반 메타요인). 따라서 이 파일럿도 Ad/Commercial
Pilot과 동일하게 **재현이 아니라 병행 산출물**로 다룬다.

## 이 문서와 함께 보는 파일

- `analysis/fandom_cohesion_pilot.ipynb` — `fandom_scores_v6.json`의 `factor_share`
  무결성을 재검증하고, "결속형(팬클럽·기부·커뮤니티)" 비중을 원본의 "팬덤결속 지수"에
  대응하는 값으로 취급해 100개 팬덤 전체를 순위화·분포 분석하며, 원본 차트가 강조했던
  BTS·임영웅·리센느(RESCENE) 3개 팬덤의 값도 직접 대조한다.
- `scripts/charts/build_cohesion_index_v7.py`,
  `scripts/charts/build_cohesion_index_v7_right_only.py` — 원본 차트 스크립트(원본 JSON
  없이는 실행 불가, 5개 유형 스키마·색상·레이아웃 참고용으로 남겨둠).

## 한계 — 이번 파일럿이 재현하지 않는 것

1. **5개 유형(A~E)별 원문 키워드 매칭 결과는 전혀 복구되지 않는다.** 유형 이름과 색상은
   코드에 남아있지만, "어떤 키워드로 어떻게 매칭했는지"(정확한 키워드 사전, 멀티라벨 규칙)
   자체는 원본 JSON 생성 스크립트가 아니라 이 시각화 스크립트에는 들어있지 않다.
2. **"팬덤결속 근거문장 수"(정수 카운트, 멀티라벨 포함 가능)와 "결속형 비중"(LDA 연속
   혼합비중)은 계산 기반이 다르다.** Ad/Commercial Pilot 문서에서 확인한 것과 동일한 이유로,
   `activity × factor_share`를 정수 카운트의 근사치로 역산하지 않는다.
3. **코퍼스 전체 커버리지 수치**(전체 문장 대비 팬덤결속 신호 비중, 신호가 1건이라도 있는
   팬덤 수)는 원본 JSON에만 있던 집계값이라 이번 세션에서 재계산할 수 없다 — LDA
   `factor_share`는 애초에 100개 팬덤 전원에 대해 6개 메타요인 비중 합이 1.0이 되도록
   정규화되어 있어(즉 "결속형 신호가 0인 팬덤"이라는 개념 자체가 없어), 원본의 "N/100개
   팬덤에서 1건 이상 등장"과 같은 형태의 통계를 만들 수 없다.
4. 코퍼스 규모(5,612건, round22)가 원본 v7 45라운드 시점의 코퍼스 규모와 다르므로, 이
   노트북의 표는 round22 기준의 **독립적인 병행 산출물**이지 원본 차트/CSV의 재현이 아니다.
