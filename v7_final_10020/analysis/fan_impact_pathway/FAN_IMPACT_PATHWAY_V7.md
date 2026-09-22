# Fan Impact Pathway 온톨로지(K→F→Persona) — 최종 산출물 적용판

> `archive/v6_r22_era/fan_impact_ontology/FANDOM_LDA_ONTOLOGY_STRATEGY.md`(전략 문서, 5,794건 시점) + `fan_impact_pathway_ontology.ipynb`(r22 K=8/M=6 재적합)의
> **최종 산출물 기준 새 판**. 전략 문서 본문은 아카이브에 두고, 여기서는 최종 제출본이 그 전략을 어떻게 구현했는지와 재현 결과만 정리한다.
> 실행 노트북: `fan_impact_pathway_v7.ipynb`.

## 1. 세 계층 — 어느 코퍼스에서 무엇이 확정됐나

| 계층 | 코퍼스 | 확정된 것 |
|---|---|---|
| 해석 계층(K→F→Persona) | **동결 스냅샷 v7-40, 7,350건** | K=10 → M=5, 실루엣 0.267; F1∼F5; 페르소나 4유형(43/31/17/9); Topic Card 10장 |
| 점수 계층 | 라이브 10,020건 | loyalty/spillover(3D 맵), 보조지표 7종 |
| 라이브 재적합 | 10,020건(LDA 문서 10,018) | K=8/M=5/실루엣 0.046 — 게이트 기각, 해석 계층 미반영 |

## 2. 온톨로지 ↔ 최종 매핑 (`factor_pathway_map_v7.json`, QA 10/10 매핑, 미매핑 0)

| F | 명칭 | 경로 | raw Factor 라벨(동결 LDA) | 구성 K 토픽 |
|---|---|---|---|---|
| F1 | 팬덤결속 경로 | Fan → Fan | 결속형(팬클럽·기부·커뮤니티) | K5 |
| F2 | 직접소비 경로 | Fan → Market | 소비력형(초동·판매·앨범) | K4, K8 |
| F3 | 현장경제 경로 | Fan → Event → Local | 현장경제형(콘서트·투어·매진) | K1, K6, K7 |
| F4 | 산업전이 경로 | Fan → Brand/Industry | 미디어노출형(방송·조회수) | K2, K9 |
| F5 | 대중·글로벌 확산 경로 | Fan → Media → Mass/Global | 차트·확산형(1위·빌보드·기록) | K0, K3 |

Topic Card 명칭(`topic_cards_v7.json`): K0 음원차트기록형 · K1 동남아현지보도형 · K2 예능방송출연형 · K3 일본오리콘앨범형 · K4 글로벌음반판매형 · K5 팬클럽공식기부형 ·
K6 단독콘서트월드투어형 · K7 브랜드앰버서더형 · K8 월드투어매진형 · K9 영화드라마출연형. 덴드로그램 컷 높이 0.774, PCA 분산비 0.408/0.308(`persona_decision_space_v7.json`).

## 3. 노트북이 재현한 것

1. **Factor-specific Impact(전략 7절: share × loyalty, share × spillover)** — `fan_persona_v7.json` 값이 동결 점수(`fandom_scores_v6.json`)에서 100팬덤 × 5F = 500셀 전부 재계산됨(불일치 0).
   BTS: F3 0.512 → loyalty 0.477 / spillover 0.512, persona 글로벌투어형(F3+F5). 임영웅: F3 0.363 + F1 0.202 → 집단동원형. 리센느: F3 0.469 + F5 0.249 → 글로벌투어형.
2. **Fan Persona(Top-2 Factor 조합)** — 명칭 재계산 불일치 0/100. 글로벌투어형 43 · 현장상업형 31 · 원정소비형 17 · 집단동원형 9 (10개 가능 조합 중 4개 실현, F3이 전 유형의 공통 기반).
3. **K→F 매핑 QA** — 10/10, F별 토픽 수 F1 1 · F2 2 · F3 3 · F4 2 · F5 2.
4. **실루엣 게이트** — K-grid 대조: 동결은 K=10이 합성순위 최솟값(8, K=8은 9)이지만 라이브는 K=8이 승자(5)이고 M=5 실루엣이 0.046으로 떨어져 게이트를 넘지 못했다.
   LDA 문서 수 10,018 = 10,020 − 3토큰 미만 2건(`lda_excluded_bullets_v7.json`).

## 4. QA 요약 (전략 문서 11절 체크리스트)

| 항목 | 결과 |
|---|---|
| K→F 매핑률 | 10/10 |
| Factor-specific Impact 재현 | 500/500 셀 |
| 페르소나 분포 | 43/31/17/9 (JSON·PCA JSON·재계산 일치) |
| 실루엣 게이트 | 동결 0.267 채택 / 라이브 0.046 기각 |

## 5. r22 판과 달라진 점

- r22: K=8/M=6/실루엣 0.154, 라벨에 "브랜드·상업형"과 "미디어노출형"이 모두 있었다. 최종 동결: K=10/M=5/0.267, F4(산업전이 경로)의 raw 라벨은 "미디어노출형(방송·조회수)"이며 K7 브랜드앰버서더형은 F3에 묶였다(`factor_pathway_map_v7.json` rationale). 광고·브랜드 신호는 별도 키워드 지수(`ad_commercial_index_v7.json`)로 보완됐다.
- r22 노트북의 "M=6 기준 Top-2 조합" 절은 M=5 기준으로 바뀌었고, 결과는 `fan_persona_v7.json`과 동일하다.
