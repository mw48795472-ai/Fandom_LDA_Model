# Media Content Exposure Pilot — 정리 및 실제 데이터 병행 산출

> **2026-09-21 갱신 주** — 이 문서가 "이번 세션에 없다 / 재현 불가"라고 적은 최종 라이브 코퍼스(10,020건)와 최종 산출물이 이제 `data/v7_final/`에 있다(`fandoms_v3_100.json` 10,020건, `fandom_scores_v6.csv`·`fan_persona_v7.json`(동결 스냅샷 7,350건 기준), `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`(라이브 재적합 K=8/M=5/실루엣 0.046), `chart3d_payload_live_reference_v7.json`, `member_mention_index_v7.json`). r22 스냅샷(5,612건)은 `data/v6_r22_snapshot/`으로 옮겨졌고, 이 문서의 노트북·스크립트가 참조하는 `../data/v6_r22_snapshot` 경로는 그대로 동작한다. 본문의 5,612건 기준 병행 분석은 그 시점의 기록으로 유지하며, 최종 수치와의 대응은 `README.md` 1∼3절 참고.
> 이 문서 관련 (2026-09-22): 이 문서가 "별도 산출물이 없다"고 적은 미디어·콘텐츠 노출 지수의 원본 `data/v7_final/media_exposure_v7.json`이 추가됐다(10,020건 기준, 4종 서브태그 원문 매칭, 미디어 불릿 1,025건 10.2%, 팬덤별 서브태그 카운트). 팬덤별 합·서브태그별 합이 원본 집계와 전부 일치한다(`verify_v7_final_consistency.py` [R]).


## 이 문서가 다루는 것

"Media Content Exposure Pilot"은 `docs/METHODOLOGY.md` 5절("보조지표 7종")의 표에 있는
**"미디어·콘텐츠 노출 지수(Media/Content Exposure Index)"** 행에서 정리한 것이다.

| 지표명 | 정의 | 산정 방법 |
|---|---|---|
| 미디어·콘텐츠 노출 지수 (Media/Content Exposure Index) | 예능·유튜브·영화·드라마 등 미디어 콘텐츠에 노출된 정도 | 원문에서 예능/유튜브/영화/드라마 4종 서브태그 키워드 직접 매칭 |

Ad/Commercial Index·Fandom Cohesion Index와 달리, **이 지표는 이번 세션에 별도의 산출
스크립트(`build_*_index_csv.py`나 차트 스크립트)조차 전혀 남아있지 않다.** 저장소 전체를
검색해도 이 지표만을 위한 코드나 JSON 경로 참조는 발견되지 않았고, `docs/METHODOLOGY.md`
표의 이 한 줄이 유일하게 남은 정의다. 즉 Worldwide Language Pilot·Ad/Commercial Pilot보다도
한 단계 더 적은 흔적만 남아있는 경우다.

## 그런데 원재료(코퍼스)는 실제로 있다 — v7 10·11라운드

이 지표가 서술하는 "예능/유튜브/영화/드라마 4종 서브태그"는 우연히 이번 세션에 실제로
복구된 코퍼스 성장 이력과 정확히 일치한다. `data/v6_r22_snapshot/v7_rounds/`에 남아있는
실제 병합 로그가 이를 직접 증언한다.

- **v7 10라운드**(`merge_log_r10.json`, round id `v7_r10_media_crossover_research`) —
  설명: *"미디어 크로스오버 리서치 — 예능 출연/드라마 출연/영화 배역 출연/유튜브 활동 4개
  각도."* 4,747건 → 4,878건(순증 131건), 79개 팬덤 반영.
- **v7 11라운드**(`merge_log_r11.json`, round id `v7_r11_media_crossover_reinforcement`) —
  설명: *"v7 10라운드 미디어 크로스오버 리서치... 물량이 부족하다는 사용자 피드백에 따른
  2배 보강 라운드. 동일한 4개 각도로... 재조사했다."* 4,878건 → 5,021건(순증 143건),
  68개 팬덤 반영(22개 팬덤 0건, 10개 팬덤 세션 예산 소진으로 `NOT_ATTEMPTED_R11` 처리).

즉 **"미디어·콘텐츠 노출 지수"라는 이름의 독립 채점 결과물(JSON)은 없지만, 그 지수가
채점하려 했던 원문(예능·드라마·영화·유튜브 언급 근거문장) 자체는 두 차례에 걸쳐 실제로
수집되어 현재 코퍼스(`fandoms_v3_100.json`, 5,612건)에 이미 녹아들어 있다.** 다만 이
근거문장들은 개별 팬덤 레코드 안에 loyalty/spillover 두 배열 중 하나로만 존재할 뿐(각
문장에 "이건 미디어 노출 유형이다"라는 태그가 붙어있지 않음), 별도로 채점된 지수 값으로
남아있지는 않다.

## 실제 데이터 병행 산출 — LDA 메타요인으로 대체

Ad/Commercial Pilot·Fandom Cohesion Pilot과 같은 논리로, `data/v6_r22_snapshot/
fandom_scores_v6.json`의 K=8/M=6 LDA 메타요인 `factor_share` 중 가장 개념이 가까운 것은
F5다.

```
"미디어노출형(방송·조회수)"
```

`docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md` 4장 LABEL_RULES 표의 정의:

| 코드 | 라벨 | 매칭 키워드 |
|---|---|---|
| F5 | 미디어노출형(방송·조회수) | 예능, 출연, 드라마, 지역, 에서, 프로그램, 출연해, 참여 |

원본 지수의 4종 서브태그(예능/유튜브/영화/드라마) 중 "예능"·"드라마" 2개는 F5의 매칭
키워드와 문자 그대로 겹치고, 나머지 "유튜브"·"영화"는 F5 키워드 목록에 직접 등장하지는
않지만 라벨 자체의 괄호 설명("방송·**조회수**")이 유튜브 조회수 등 온라인 시청 지표를
포괄하는 것으로 해석된다. 원본만큼 정확히 같은 개념은 아니지만, Ad/Commercial·Fandom
Cohesion Pilot과 동일한 수준의 "가장 가까운 실측 대체 지표"로 다룬다.

## 이 문서와 함께 보는 파일

- `analysis/media_content_exposure_pilot.ipynb` — `fandom_scores_v6.json`의 F5
  "미디어노출형(방송·조회수)" 비중을 무결성 검증 후 100개 팬덤 순위화하고, **v7 10·11라운드
  병합 로그의 실제 팬덤별 신규 근거문장 수(per_group_added)와 F5 비중 사이의 상관관계**를
  직접 계산해, 두 개의 서로 다른 실측 데이터가 실제로 얼마나 일치하는지(또는 하지
  않는지) 정직하게 보여주는 노트북.

## 한계 — 이번 파일럿이 재현하지 않는 것

1. **채점된 지수 자체가 이번 세션에 존재한 적이 없다.** Ad/Commercial·Fandom Cohesion
   지수는 최소한 스크립트(컬럼 스키마)라도 남아있었지만, 이 지수는 `docs/METHODOLOGY.md`의
   한 줄 정의 외에 코드 흔적이 전혀 없다.
2. **v7 10·11라운드 병합 로그는 "이 지수의 원재료가 실존한다"는 근거일 뿐, 지수 값 자체는
   아니다.** `per_group_added`는 그 라운드에 "새로 추가된" 근거문장 수일 뿐, 그 팬덤이
   이전부터 이미 갖고 있던 미디어 노출 관련 문장은 포함하지 않는다 — 따라서 이 값을 "팬덤별
   미디어 노출 총량"으로 오독하면 안 된다.
3. **F5 비중과 실제 신규 근거문장 수의 상관관계는 약하다(아래 노트북에서 직접 계산, r≈0.19).**
   이는 자연스러운 결과다 — F5 비중은 코퍼스 전체(loyalty+spillover 5,612건) 대비 상대
   비율인 반면, r10·r11 신규 건수는 두 라운드에서만 추가된 절대 건수이기 때문이다. 이
   불일치를 숨기지 않고 그대로 보고한다.
4. 코퍼스 규모·계산 방법이 원본과 다르므로, 이 노트북의 표는 round22 기준의 **독립적인
   병행 산출물**이지 원본 Media/Content Exposure Index의 재현이 아니다.
