# 그룹–멤버 계층 지수(Member Mention Index · MCI) — 최종 코퍼스 10,020건 판

> `archive/v6_r22_era/Group_Member Pilot/`(전략 보고서 v4→v5 FPU 726행 + 23개 그룹 파일럿 노트북)의 **10,020건 기준 새 판**.
> 전략 문서 본문(설계 제안)은 아카이브에 그대로 두고, 이 문서는 최종 데이터에서 **실제로 구현·재현된 부분**만 정리한다.
> 입력: `member_mention_index_v7.json`(45개 그룹), `member_mention_pilot_v6.json`(동결 23개), `member_pilot_mci_correlation_v7.json`. 실행 노트북: `group_member_index_v7.ipynb`.

## 1. 정의 (상세명세서 7장, 그대로)

```
MemberImpactShare(member) = 그룹 근거문장 내 멤버명 언급 횟수 ÷ 그룹 전체 멤버명 언급 총횟수
MCI                       = Σ_member MemberImpactShare(member)²      (허핀달-허시만 형태, 하한 1/멤버수)
MCI_excess                = MCI − 1/멤버수                            (구조적 하한 보정)
CoverageIndex             = 0.30·언어 + 0.25·시장 + 0.20·출처유형 + 0.15·시간 + 0.10·개체
```

## 2. 노트북이 확인한 것

1. **Coverage Index 가중식** — 라이브 10,020건 100/100, 동결 7,350건 100/100 (가중치·재계산 불일치 0).
2. **45개 그룹 MCI 재계산** — Impact Share·MCI·멤버 언급 합 불일치 0/45(소수 3자리 반올림 허용), `total_group_bullets` = 코퍼스 45/45.
   멤버 언급 총합 1,730건. MCI 평균 0.261, 최소 NCT 0.111, 최대 FTISLAND 0.660.
   상위: FTISLAND 0.660(2명) · 동방신기 0.512(2명) · CNBLUE 0.504 · CORTIS 0.459 · 빅뱅 0.364 — 보고서 표 17과 동일.
3. **빅뱅** — 근거 97건(동결 72), 멤버 언급 32(동결 24), MCI 0.364(동결 0.389); 지드래곤 0.469 · 태양 0.344 · 대성 0.156 · 탑 0.031(동결 파일럿에서는 0건).
4. **동결 23개 → 최종 45개** — 신규 22개 그룹(A-pink·ATEEZ·BTOB·CNBLUE·DAY6·FTISLAND·GOT7·HOT·IKON·ITZY·QWER·STAYC·god·동방신기·레드벨벳·리센느·아이오아이·여자친구·오마이걸·워너원·잭스키스·프로미스나인).
   공통 23개 그룹의 MCI는 평균 −0.090 감소(멤버 전수 리서치 r53~55로 언급이 분산): Hearts2Hearts 1.000→0.289, CORTIS 1.000→0.459, RIIZE 0.621→0.358.
5. **MCI ↔ 멤버 수·성과지표** — 최종 MCI로 재계산: r(MCI, 멤버 수) = −0.728 (JSON v7-55 시점 −0.749); MCI~loyalty(동결) r = −0.385 (JSON −0.393),
   MCI_excess~loyalty r = −0.044 (JSON −0.069), MCI_excess~spillover 0.214 (JSON 0.189). → 멤버 수를 통제하면 설명력이 사라진다는 JSON `verdict`가 최종 MCI로도 유지된다.
6. **MCI 해석 구간(예시 임계값 0.30/0.45)** — 분산형 36 · 다극형 5 · 스타중심형 4. FPU JSON 스키마 예시(빅뱅)는 노트북 5절.

## 3. 전략 문서 대비 구현 매트릭스 (최종)

| 전략 문서 제안 | 최종 데이터에서의 상태 |
|---|---|
| Coverage Index 5요소 가중합 | 구현·재현 (100/100) |
| Member Impact Share / MCI | 45개 그룹 텍스트마이닝 지수로 구현 (멤버별 독립 리서치 아님 — 각 레코드 `note`) |
| MCI 구조적 하한 보정(MCI_excess) | 상관분석 JSON에 구현, 노트북에서 재계산 |
| Unit 계층(NCT 유닛 등), Joint Evidence, Group–Member Synergy, Member Activation Score, event_id 중복 제거 | 미구현 (`not_yet_computable`) |

## 4. 한계

1. 멤버명 언급 수 기반 텍스트마이닝 지수다. 별칭·동음 오매칭(r22 문서의 SEVENTEEN "준"→"기준" 사례) 가능성은 최종 파이프라인의 별칭 처리에 의존한다.
2. 상관분석 JSON은 v7-55 시점(8,981건) MCI × 동결 outcome이라 최종 MCI 재계산값과 소폭 다르다(위 5).
3. 2인 그룹(FTISLAND·동방신기)은 MCI 하한이 0.5라 원시 MCI 순위가 구조적으로 높다 — `mci_excess`를 함께 본다.
