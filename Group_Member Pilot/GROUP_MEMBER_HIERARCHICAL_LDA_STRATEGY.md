# 팬덤 LDA 분석 고도화 전략 보고서 — Group–Unit–Member Hierarchical LDA (v4 → v5 FPU)

**Language Coverage Equalization × Group–Unit–Member Hierarchical LDA**
100개 팬덤 · 1,035건 근거문장 · JSON Evidence · 3D Positioning 고도화안
기존 분석자료 기반 설계 업데이트 / 2026.08

> 목원님이 업로드하신 두 docx(`v4.docx`, `v5_Composite_Fandom.docx`)를 정리한 문서다. v5는
> v4 전체 내용에 **"개정안 V5 — Composite Fandom Unit(FPU) 아키텍처"** 섹션을 추가로 덧붙인
> 버전이라, 두 파일을 중복 없이 하나로 합쳐 v4 본문 뒤에 v5의 추가분을 이어 붙였다. 원본은
> 「fandom100_LDA_report_v3_1.docx / fandom100_source_bullets.json /
> chart3d_fandom_map_v3_100_1.html」(1,035건 근거문장, K=8 LDA 채택)을 기준 자료로 삼는
> **설계 제안서**이며, 이번 프로젝트의 최종 제출본(10,020건, K=10) 및 이번 세션에서 복구된
> v6 스냅샷(5,612건, K=8)과는 또 다른, 더 이전 시점(1,035건)의 자료를 기준으로 한다는 점에
> 유의할 것 — 세부 수치는 서로 비교 대상이 아니라 각자 다른 코퍼스 단계의 기록이다.

## NOTE

본 보고서는 현재 업로드된 fandom100_LDA_report_v3_1.docx, fandom100_source_bullets.json,
chart3d_fandom_map_v3_100_1.html을 출발점으로 하며, 기존 분석에서 확인된 사실과 향후 실행을
위한 설계 제안을 구분한다.

## Executive Summary

기존 100개 팬덤 분석은 100개 팬덤에서 총 1,035건의 근거 문장을 수집하고, 국문 검색을
기본으로 하되 69개 팬덤에 영문·로마자 검색을 추가했다. 기존 보고서는 나머지 31개 팬덤에서
영문 보강이 완료되지 않았고, 특히 리센느(RESCENE)의 순위·점수에는 실제 영향력과 데이터
Coverage 차이가 혼재할 수 있음을 명시한다. [기존 보고서 근거]

또한 기존 3D 그래프의 Z축은 실제 트래픽이 아니라 팬충성도·파급효과 근거문장의 총량을
근사치로 사용했으며, 이 값이 X/Y 점수에도 사용되어 세 축이 독립적이지 않다는 한계가 HTML에
명시되어 있다. [기존 3D HTML 근거]

이번 고도화는 두 문제를 동시에 해결한다. 첫째, Language Coverage를 Impact와 분리하여 영문
자료가 많은 글로벌 팬덤과 자료가 적은 신흥 팬덤 사이의 관측 격차를 정량화한다. 둘째, Group →
Unit → Member → Evidence의 계층형 Entity를 도입하여 BIGBANG·BLACKPINK·소녀시대뿐 아니라
BTS·NCT·EXO·슈퍼주니어·SHINee·(여자)아이들·MAMAMOO·IVE·TWICE 등 개인 영향력이 뚜렷한 그룹을
멤버 단위로 확장한다.

최종 모델은 100 Fandoms → Group/Unit/Member → Evidence → Language/Market Coverage → Topic →
Meta Factor → Loyalty/Spillover → Industry/Region으로 발전하며, Member Impact Share·Member
Concentration Index(MCI)·Group–Member Synergy를 핵심 지표로 추가한다.

## 1. 기존 분석 구조와 진단

| 구성요소 | 현재 구조 | 고도화 방향 |
|---|---|---|
| 분석 대상 | 100개 팬덤 | 유지 |
| 근거문장 | 1,035건 | Entity/언어/시장/이벤트 메타데이터 추가 |
| LDA | K=8 최종 | K=5~30 + coherence/stability 검증 |
| 충성도·파급효과 | 근거문장+정량지표+핵심어 | Impact와 Coverage 분리 |
| 3D Z축 | 근거문장 총량 | Member Concentration/Factor Diversity 또는 외부 engagement |
| Entity | 팬덤/아티스트 중심 | Group→Unit→Member 계층 |

기존 스코어링은 근거문장 1건당 1.0점, 정량지표 단위당 +0.5점, 핵심어 일치당 +0.3점을 부여한
뒤 100개 팬덤 전체에서 0~1로 정규화하는 구조다. 이는 버전 간 비교에 유리하지만 자료량이 많은
팬덤에 구조적 이점을 줄 수 있다. [기존 보고서 근거]

> **NOTE** 고도화의 핵심은 기존 Raw Score를 폐기하는 것이 아니라 Raw Evidence →
> Quality/Independence → Coverage → Adjusted Impact의 순서로 확장하는 것이다.

## 2. 고도화 전략 I — Language Coverage Equalization

### 2.1 Impact와 Coverage의 분리

| 개념 | 정의 | 해석 |
|---|---|---|
| Impact | 수집된 근거가 보여주는 실질적 영향력 | 충성도·파급효과의 크기 |
| Coverage | 영향력을 관측할 수 있는 자료의 범위·균형 | 자료 부족/언어 편중 |
| Quality | 출처의 신뢰도·독립성·정량성 | Evidence 신뢰도 |

RESCENE은 Coverage Bias를 검증하기 위한 대표 사례로 활용한다. 기존 보고서가 지적했듯 영문
보강 미완료 상태에서 순위 하락을 실제 영향력 하락으로 해석하면 안 된다. 따라서 보강 후에는
Raw Impact와 Coverage Index를 동시에 제시한다.

### 2.2 언어·시장별 수집 매트릭스

| Layer | KR | EN/Global | JP | CN/중화권 | 기타 |
|---|---|---|---|---|---|
| 공식자료 | 필수 | 필수 | 활동 시 | 활동 시 | 선택 |
| 언론 | 필수 | 필수 | 일본 활동 시 | 중화권 활동 시 | 선택 |
| 차트·판매 | 필수 | 필수 | 필수 | 필수 | 선택 |
| 공연·투어 | 필수 | 필수 | 필수 | 필수 | 선택 |
| 브랜드·광고 | 필수 | 필수 | 시장별 | 시장별 | 선택 |
| 관광·지역경제 | 필수 | 글로벌 도시 | 시장별 | 시장별 | 선택 |
| SNS·플랫폼 | 필수 | 필수 | 시장별 | 시장별 | 선택 |

### 2.3 Coverage Index 권고식

```
Coverage Index = 0.30×Language Balance + 0.25×Market Coverage
               + 0.20×Source-Type Coverage + 0.15×Time Coverage
               + 0.10×Entity Coverage
```

이 가중치는 기존 분석에서 실제 산출된 값이 아니라 실행을 위한 권고 설계값이다. 실제
적용에서는 민감도 분석을 통해 가중치의 안정성을 검증한다.

> **정리자 주** — 이 정확한 가중치(0.30/0.25/0.20/0.15/0.10, Language/Market/Source-Type/
> Time/Entity)는 이번 세션에서 복구된 `fandom_scores_v6.json`의 `coverage_detail.weights`에
> **그대로 채택되어 실제 산출된 것으로 확인된다.** 즉 이 설계 제안은 실제로 실행에 반영됐다
> — 자세한 검증은 함께 제공하는 노트북 2번 셀 참고.

### 2.4 Evidence 보정

```
Adjusted Evidence = Raw Score × Source Quality × Independence × Coverage Adjustment
```

- Source Quality: 공식/기관/주요언론/산업자료/2차자료 등급화
- Independence: 동일 사건을 반복 보도한 기사 중복 방지
- Coverage Adjustment: 자료 부족을 영향력 0으로 해석하지 않고 불확실성으로 표시

## 3. 고도화 전략 II — Group–Unit–Member Hierarchical Entity

그룹의 영향력은 그룹 자체 활동뿐 아니라 멤버의 음악·연기·예능·패션·브랜드·광고·글로벌 활동을
통해 발생한다. 기존 JSON에도 NCT의 유닛·개인 결집 특성이 명시되어 있고, ATEEZ에는 산·성화의
멤버별 패션 앰버서더 근거가 별도로 존재한다. 따라서 멤버 단위 분해는 선택적 장식이 아니라
데이터 귀속 정확도를 높이는 핵심 단계다.

권고 구조: `Fandom → Group → (Unit) → Member → Evidence → Topic → Meta Factor`

| 필드 | 예시 | 용도 |
|---|---|---|
| group_id | G_BIGBANG | 그룹 고유 ID |
| unit_id | U_NCT127 | 유닛 구조 |
| member_id | M_GDRAGON | 멤버 고유 ID |
| entity_type | group/unit/member | Evidence 귀속 |
| canonical_name | G-DRAGON | 표준명 |
| aliases | 지드래곤, GD, 권지용 | 검색 확장 |
| official_url | 공식/소속사 링크 | Seed |
| activity_domains | music/fashion/acting | 산업 분류 |
| active_period | 기간 | 시점 통제 |

## 4. 100개 팬덤 중 Member-level Research 우선순위

S/A/B는 영향력 순위가 아니라 '멤버 단위 조사 필요성'의 등급이다. 멤버명과 공식 링크는 실제
수집 단계에서 공식·소속사 자료로 최종 검증한다.

| Tier | 그룹 | 조사 멤버/단위 | 권고 |
|---|---|---|---|
| S | BTS | RM, Jin, SUGA, j-hope, Jimin, V, Jungkook | 전원 |
| S | BIGBANG | G-DRAGON, TAEYANG, DAESUNG, T.O.P | 전원 |
| S | BLACKPINK | JISOO, JENNIE, ROSÉ, LISA | 전원 |
| S | NCT | 127/DREAM/WayV/WISH + 핵심 멤버 | 핵심 유닛/멤버 |
| S | EXO | D.O., Baekhyun, Kai, Suho, Chanyeol, Sehun, Xiumin 등 | 전수 |
| S | 슈퍼주니어 | 규현, 희철, 이특, 신동, 은혁, 동해, 시원, 예성 등 | 전수 |
| S | SHINee | TAEMIN, KEY, MINHO, ONEW | 전수 |
| S | 소녀시대 | TAEYEON, YOONA, SOOYOUNG, YURI, SEOHYUN, TIFFANY, HYOYEON 등 | 전수 |
| S | (여자)아이들 | 전소연, 미연, 민니, 우기, 슈화 | 전수 |
| S | MAMAMOO | 화사, 솔라, 문별, 휘인 | 전수 |
| S | IVE | 장원영, 안유진, 레이 등 | 핵심 전수 |
| A | TWICE | 나연, 사나, 모모, 미나, 쯔위, 지효 등 | 핵심 |
| A | SEVENTEEN | 민규, 정한, 호시, 우지, 승관, 디에잇, 도겸 등 | 핵심 |
| A | Stray Kids | 현진, 필릭스, 방찬, 창빈, 한, 리노 등 | 핵심 |
| A | 동방신기 | 유노윤호, 최강창민 | 전수 |
| A | BTOB | 육성재, 이창섭, 서은광, 이민혁 | 전수 |
| A | CNBLUE | 정용화, 강민혁, 이정신 | 전수 |
| A | FTISLAND | 이홍기, 이재진, 최민환 | 핵심 |
| A | Red Velvet | 아이린, 슬기, 웬디, 조이, 예리 | 핵심 |
| A | NewJeans | 민지, 하니, 다니엘, 해린, 혜인 | 전수 |
| A | aespa | 카리나, 윈터, 닝닝, 지젤 | 핵심 |
| A | LE SSERAFIM | 사쿠라, 김채원, 카즈하, 허윤진 등 | 핵심 |
| B+ | ATEEZ | 산, 성화 등 | 핵심 |
| B+ | RIIZE | 원빈, 성찬, 은석, 쇼타로 등 | 핵심 |
| B+ | ITZY | 예지, 류진, 유나, 채령 등 | 핵심 |
| B+ | STAYC | 시은, 윤, 세은 등 | 핵심 |
| B+ | OH MY GIRL | 아린, 유아, 미미, 승희 등 | 핵심 |
| B | Apink | 정은지, 윤보미, 김남주 등 | 2~3명 |
| B | 여자친구 | 예린, 유주, 신비, 엄지, 은하 등 | 주요 |
| B | iKON | BOBBY, 송윤형, DK 등 | 핵심 |
| B | DAY6 | Young K, 원필, 성진 등 | 주요 |
| B | QWER | 쵸단, 마젠타, 히나, 시연 | 특수 |
| B | BABYMONSTER | 아현, 루카, 라미, 파리타 등 | 모니터링 |

## 5. Research Agent 수집 프로토콜

1. Entity Discovery — 공식 그룹/아티스트 자료에서 그룹명·영문명·멤버명·별칭 확인
2. Entity Registry — group_id/unit_id/member_id 생성 후 검색 시작
3. Group Search — 그룹 자체의 음악·공연·팬덤·브랜드·지역경제 자료 수집
4. Member Search — 개인 음악·연기·예능·패션·광고·브랜드·글로벌 활동 별도 검색
5. Language Search — KR→EN→실질 활동시장 언어 순으로 검색
6. Evidence Attribution — entity_type/entity_id를 문장 단위로 기록
7. Event Deduplication — 동일 사건에 event_id를 부여
8. Quality/Confidence — 출처 등급·정량성·날짜·독립성 기록
9. Coverage Audit — 언어·시장·출처 유형 공백 계산
10. LDA Corpus Build — Group/Member/Integrated corpus 생성

### 5.1 Agent 명령문

모든 팬덤을 Group/Unit/Member Entity로 분리해 조사한다. 그룹 공식명·영문명·별칭을 확인한 후
Entity Registry를 먼저 생성한다. 독립적인 솔로·배우·예능·패션·브랜드·글로벌 활동이 확인되는
멤버는 Member Entity로 등록한다. 그룹 활동과 멤버 활동을 동일 Evidence로 중복 귀속하지
않는다. NCT 등 유닛 구조가 있는 경우 Unit Entity를 생성한다. 각 Evidence에는 entity_type,
entity_id, language, market, source_type, date, url, event_id를 기록한다. KR과 EN을 모두
검색하고 실제 활동시장이 있는 경우 JP/CN 등 현지 언어 자료를 추가한다. 자료가 부족하면 0점
처리하지 말고 coverage_gap으로 기록한다. 확인되지 않는 사실은 생성하지 않는다.

## 6. JSON v4.1 권고 스키마

현재 fandom/loyalty/spillover 구조를 보존하되 Evidence의 원자 단위에 Entity와 Coverage
메타데이터를 추가한다.

```json
{
  "group_id": "G_BIGBANG",
  "members": [{"member_id": "M_GDRAGON", "member_name": "G-DRAGON",
               "aliases": ["지드래곤", "GD", "권지용"]}],
  "evidence": [{"event_id": "EV_000123", "entity_type": "member", "entity_id": "M_GDRAGON",
                "dimension": "spillover", "language": "en", "market": "US",
                "source_type": "media", "date": "YYYY-MM-DD", "text": "...", "url": "...",
                "quantitative": true, "quality": 0.90}],
  "coverage": {"kr": 12, "en": 10, "jp": 5, "cn": 0, "coverage_index": 0.78}
}
```

## 7. Hierarchical LDA 분석 설계

| Corpus | 단위 | 목적 | 산출물 |
|---|---|---|---|
| Group Corpus | 그룹 Evidence | 그룹 공통 서사 | Group Topics |
| Member Corpus | 멤버 Evidence | 개인 활동반경 | Member Topics |
| Integrated Corpus | Group+Member | 전체 생태계 | Cross-level Topics/Factors |

기존 LDA는 K=8,10,12,14,16,18,20을 비교해 perplexity가 가장 낮은 K=8을 최종 채택했다.
고도화에서는 K=5~30에서 perplexity뿐 아니라 coherence, topic diversity, seed stability,
bootstrap stability, human interpretability를 함께 검증한다.

| 지표 | 목적 | 기준 |
|---|---|---|
| Perplexity | 모형 적합 | 낮을수록 유리 |
| Coherence | 토픽 응집 | 높을수록 유리 |
| Topic Diversity | 토픽 중복 | 높을수록 유리 |
| Seed/Bootstrap Stability | 재현성 | 높을수록 유리 |
| Human Interpretability | 해석 가능성 | 높을수록 유리 |

### 7.1 Topic → Meta Factor

| Meta Factor | 주요 Topic | 해석 |
|---|---|---|
| Fan Commitment | 팬클럽·기부·총공 | 내부 결속 |
| Consumption Power | 초동·음반·티켓 | 직접 소비 |
| Live Economy | 콘서트·투어 | 현장경제 |
| Brand & Commercial | 광고·앰버서더·팝업 | 상업 파급 |
| Global Reach | 빌보드·해외투어 | 국제 확산 |
| Content/IP | OST·드라마·방송 | 콘텐츠 확장 |
| Creator/Member Power | 개인 창작·연기·패션 | 개인 확장 |
| Regional Spillover | 관광·지자체·지역매출 | 공간적 전이 |

## 8. Member Impact 정량화

### 8.1 Member Impact Share

```
Member Impact Share_i = Adjusted Member Impact_i
                       / (Adjusted Group Impact + Σ Adjusted Member Impact_i)
```

Group-only, Member-only, Joint Evidence를 먼저 분리하고 중복을 제거한 뒤 계산한다.

### 8.2 Member Concentration Index (MCI)

```
p_i = Member Impact_i / Σ Member Impact_i
MCI = Σ p_i²
```

| 구조 | MCI | 해석 |
|---|---|---|
| Distributed Influence | 낮음 | 멤버별 영향 분산 |
| Multi-node Influence | 중간 | 복수 핵심 멤버가 산업별 역할 |
| Star-centered Influence | 높음 | 소수 스타가 그룹 파급 견인 |

### 8.3 Group–Member Synergy

```
Synergy = Joint Evidence Impact / (Group-only Impact + Member-only Impact + Joint Evidence Impact)
```

Member Impact Share가 높다고 해서 Group–Member Synergy가 높은 것은 아니다. 전자는 개인
비중, 후자는 상호 강화 정도를 측정한다.

## 9. 3D 포지셔닝 고도화

기존 HTML의 Z축은 실제 웹 트래픽·검색량이 아니라 근거문장 총량을 근사치로 사용했고, X/Y
산정에도 같은 총량이 쓰여 세 축이 독립적이지 않다는 한계가 명시돼 있다. 따라서 고도화에서는
Z축을 Member Concentration, Factor Diversity 또는 독립적인 실제 engagement 데이터로
교체한다.

| 축 | 권고 변수 | 의미 |
|---|---|---|
| X | Group Loyalty | 팬덤 내부 결속 |
| Y | Group Spillover | 외부 산업·지역 전이 |
| Z | Member Concentration / Factor Diversity | 개인 영향 구조 |

| 유형 | 특징 | 검증 사례 | 질문 |
|---|---|---|---|
| Group-centric | 그룹 효과 높음·MCI 낮음 | 그룹 중심 팬덤 | 그룹 자체가 자원을 만드는가? |
| Star-centric | MCI 높음 | BIGBANG 등 | 개인 스타가 그룹을 견인하는가? |
| Multi-node | MCI 중간·Factor 다양 | 소녀시대·EXO·SHINee | 개인 산업 분화가 확산을 키우는가? |
| Emerging | Coverage 낮음·특정 Factor 성장 | RESCENE 등 | 관측 부족과 성장세를 어떻게 구분할까? |

## 10. 네트워크·산업 확장

Entity 구조가 갖춰지면 `Group → Member → Topic → Meta Factor → Industry → Region`의 전이
네트워크를 구성할 수 있다.

- Node: Group/Unit/Member/Topic/Factor/Industry/Region
- Edge: evidence/co-mention/event/brand/concert/tourism
- Weight: Adjusted Evidence 또는 Event-level Impact
- Centrality: 여러 산업을 연결하는 핵심 멤버 탐색
- Community Detection: 산업·지역별 영향권 분리

### 10.1 핵심 연구 질문

- 그룹 경제적 파급력 중 개인 멤버가 설명하는 비중은 얼마인가?
- 특정 멤버는 음악 외 어떤 산업으로 가장 강하게 spillover하는가?
- 글로벌 팬덤의 영어 자료 우위는 실제 영향력과 얼마나 분리되는가?
- 팬덤이 그룹 중심에서 개인 스타 중심으로 이동하는 패턴이 존재하는가?
- 개인 활동이 그룹 팬덤의 소비·관광·브랜드 파급으로 연결되는가?

## 11. 단계별 실행 로드맵

| Phase | 작업 | 산출물 | 검증 |
|---|---|---|---|
| 1 | 100개 Entity Registry | group/unit/member master | 중복·동명이인 |
| 2 | KR/EN/활동시장 보강 | evidence_v4.json | Coverage audit |
| 3 | Event dedup + Quality | event/evidence table | 중복 사건 |
| 4 | Corpus 분리 | 3 corpus | 분포 확인 |
| 5 | LDA K=5~30 | topic matrix | coherence/stability |
| 6 | Topic→Factor | factor matrix | 해석성 |
| 7 | Score 재산출 | Loyalty/Spillover | Coverage 비교 |
| 8 | Member metrics | Share/MCI/Synergy | 민감도 |
| 9 | 3D/Network | HTML | 축 독립성 |
| 10 | 최종 보고서 | Fandom-omics v4 | Human validation |

## 12. 품질관리

- Entity validation
- Source/URL validation
- Event deduplication
- Language tagging validation
- Member attribution validation
- LDA seed/bootstrap validation
- 2인 이상 Human labeling
- Coverage·가중치 민감도 분석

### 12.1 금지해야 할 해석

- 영문 자료가 적다는 이유만으로 글로벌 영향력이 낮다고 단정
- 멤버 이름이 등장했다는 이유만으로 효과를 전부 개인에게 귀속
- 동일 사건을 그룹과 멤버에게 중복 집계
- 기존 3D Z축 근거문장 총량을 실제 트래픽으로 표현
- LDA 단어 목록만으로 경제적 인과관계 주장

## 13. 최종 산출물

| 산출물 | 핵심 내용 | 목적 |
|---|---|---|
| Figure 1 | 100개 Loyalty×Spillover | 기존 2D 연속성 |
| Figure 2 | Language Coverage Map | 자료 편중 진단 |
| Figure 3 | Group–Unit–Member Tree | Entity 구조 |
| Figure 4 | 100×Meta Factor Heatmap | 팬덤별 구조 |
| Figure 5 | Member Impact Share | 개인 영향력 |
| Figure 6 | 3D Loyalty×Spillover×MCI | 구조 유형 |
| Figure 7 | Member→Industry→Region Network | 산업·지역 전이 |
| Table 1 | S/A/B Research Priority | Agent 범위 |
| Table 2 | Coverage Audit | 자료 신뢰도 |
| Table 3 | Topic/Factor Validation | 모델 품질 |

## 14. 결론 — Fandom-omics v4

이번 고도화의 핵심은 LDA를 무작정 복잡하게 만드는 것이 아니라 분석 단위를 정확하게
정의하고, 자료 관측 편향을 측정하며, 그룹과 개인의 영향력을 분리한 뒤 다시 연결하는 것이다.

기존 모델이 '100개 팬덤 → 근거문장 → LDA → Loyalty/Spillover'였다면, 고도화 모델은 '100개
팬덤 → Group/Unit/Member → Evidence → Language/Market Coverage → Topic → Meta Factor →
Loyalty/Spillover → Industry/Region'으로 발전한다.

BIGBANG·BLACKPINK·소녀시대는 Group–Member Hierarchical LDA의 대표 검증 사례가 되고,
BTS·NCT·EXO·슈퍼주니어·SHINee·(여자)아이들·MAMAMOO·IVE·TWICE 등은 확장 표본이 된다. 특히
NCT는 Group→Unit→Member 구조의 검증 사례로 별도 처리해야 한다. ATEEZ는 기존 JSON에서 멤버
산·성화의 앰버서더 근거가 이미 확보되어 있어 Member-level attribution의 실증 테스트에
활용할 수 있다.

최종 목표는 '누가 인기 있는가'를 넘어 '팬덤의 영향력이 그룹·개인·콘텐츠·브랜드·관광·
지역경제 중 어디에서 발생하고 어떻게 전이되는가'를 설명하는 Fandom-omics 분석 체계를
구축하는 것이다.

## 부록 A. 핵심 변수 사전

| 변수 | 형식 | 의미 |
|---|---|---|
| group_member_flag | 0/1 | 멤버 분석 필요 여부 |
| member_research_level | S/A/B/C | 조사 강도 |
| member_count | int | 조사 대상 멤버 수 |
| unit_structure | 0/1 | 유닛 존재 여부 |
| coverage_gap | 0~1 | 관측 부족 |
| member_independence | 0~1 | 개인 활동 독립성 |
| member_industry_count | int | 활동 산업 수 |
| member_impact_share | 0~1 | 개인 영향 비중 |
| mci | 0~1 | 멤버 영향 집중도 |
| synergy | 0~1 | 그룹-개인 결합효과 |

## 부록 B. 기반 자료 및 근거 메모

① fandom100_LDA_report_v3_1.docx: 100개 팬덤, 1,035건 근거문장, K=8 LDA, Loyalty×Spillover
스코어링, 영문 보강 69개/31개 미완료 및 RESCENE Coverage 문제.
② fandom100_source_bullets.json: 팬덤별 loyalty/spillover 근거문장과 URL. NCT의 유닛·개인
결집, ATEEZ의 멤버별 앰버서더 등 Member-level 확장의 출발점.
③ chart3d_fandom_map_v3_100_1.html: 기존 3D X/Y/Z 정의와 Z축 비독립성 한계.
④ 본 보고서의 S/A/B 우선순위, Coverage Index, Member Impact Share, MCI, Synergy, Agent
프로토콜은 기존 자료를 기반으로 한 고도화 설계 제안이며 실제 데이터 재수집·검증 후 확정한다.

---

# 개정안 V5 — Composite Fandom Unit(FPU) 아키텍처

**이번 개정의 핵심은 100개 팬덤을 단순히 '그룹 100개'로 보는 것이 아니라, 각 팬덤을 하나의
팬덤 포트폴리오(Fandom Portfolio)로 정의하는 것이다.** 그룹 내 개인 멤버가 독립적인 팬덤과
영향력을 갖는 경우, 해당 팬덤은 [그룹 자체 팬덤] + [영향력 있는 개인 멤버 팬덤]의 구조로
표현한다.

따라서 대표적인 BIGBANG의 분석 단위는 'BIGBANG 하나'가 아니라 다음과 같이 구성된다.

```
BIGBANG FPU = BIGBANG Core + G-DRAGON + TAEYANG + DAESUNG + T.O.P
```

동일한 원칙을 BLACKPINK에는 BLACKPINK Core + JISOO + JENNIE + ROSÉ + LISA, 소녀시대에는
소녀시대 Core + TAEYEON + YOONA + 기타 활성 Member Nodes와 같이 적용한다.

다만 이 구조를 단순 합산으로 처리해서는 안 된다. 동일 팬이 그룹과 개인 멤버를 동시에 지지할
수 있고, 동일 사건이 그룹과 멤버의 공동 영향으로 발생할 수 있기 때문이다. 따라서 '합집합
구조'를 데이터 모델의 기본으로 하고, 중복과 공동 효과는 별도 Node/Evidence로 관리한다.

## 1. FPU의 기본 구조

| 계층 | Entity | 예시 | 분석 역할 |
|---|---|---|---|
| Fandom Portfolio | FPU | F_BIGBANG | 100개 팬덤 중 하나의 최상위 분석 단위 |
| Group Core | group_core | G_BIGBANG | 그룹 자체 팬덤·음반·공연·그룹 브랜드 |
| Unit | unit | U_NCT127 | 유닛 자체 팬덤·활동이 독립적인 경우 |
| Member | member | M_GDRAGON | 개인 팬덤·솔로·패션·광고·연기 등 |
| Joint | joint | J_BIGBANG_GD | 그룹+멤버 공동 효과 및 중복 통제 |
| Evidence | evidence | EV_0001 | 실제 근거문장·수치·출처 |

핵심은 FPU가 100개라는 점이다. 즉 100개 팬덤 간 비교는 FPU 단위에서 수행하고, FPU 내부를
Group Core·Unit·Member로 분해하여 '그 팬덤의 영향력이 어디에서 발생하는가'를 분석한다.

## 2. 100개 팬덤의 구성 유형

| 유형 | 구성 | 적용 조건 | 분석 |
|---|---|---|---|
| Type A — Group-only | [Group Core] | 개인 멤버의 독립 영향력이 낮음 | Group LDA + FPU LDA |
| Type B — Composite | [Group Core]+[Members] | 복수 멤버가 독립적인 팬덤/활동 보유 | Group + Member + FPU LDA |
| Type C — Hierarchical | [Group Core]+[Units]+[Members] | 유닛과 개인 모두 독립 영향 | Group + Unit + Member + FPU LDA |
| Type D — Emerging Composite | [Group Core]+[핵심 Member] | 성장 단계에서 개인 영향력이 빠르게 형성 | Coverage 보강 + Member 추적 |

## 3. '개인 멤버를 포함한다'의 정확한 의미

모든 그룹 멤버를 자동으로 팬덤 구성요소에 넣는 것은 아니다. Member Node는 '그룹에 속해
있다는 사실'이 아니라 '그룹과 별도로 관측되는 영향력'을 기준으로 활성화한다.

- 개인 솔로 활동이 반복적으로 관측되는가?
- 개인 팬미팅·솔로 공연·솔로 앨범 등 독립 소비가 존재하는가?
- 개인 광고·앰버서더·패션·브랜드 활동이 존재하는가?
- 연기·예능·방송·콘텐츠 등 그룹 외 산업으로 독립적인 파급이 존재하는가?
- 해외 시장에서 개인 이름으로 독립적인 활동·성과가 관측되는가?
- 개인 중심 Evidence가 일정 기간 반복되어 일시적 언급을 넘어서는가?

이 조건을 충족하면 Member Node를 '활성화'하고, 그렇지 않으면 멤버명은 검색 Alias/Reference로만 관리한다.

## 4. BIGBANG형 FPU를 실제 데이터 구조로 표현

| Node | 귀속 Evidence | 예시 활동영역 | 중복 처리 |
|---|---|---|---|
| BIGBANG Core | 그룹 전체 활동 | 그룹 음반·공연·팬덤·그룹 브랜드 | Member-only 효과 제외 |
| G-DRAGON | 개인 활동 | 솔로 음악·패션·브랜드·글로벌 | 독립 Evidence |
| TAEYANG | 개인 활동 | 솔로 음악·공연·브랜드 | 독립 Evidence |
| DAESUNG | 개인 활동 | 솔로 음악·방송·공연 | 독립 Evidence |
| T.O.P | 개인 활동 | 솔로/연기/예술/브랜드 | 활동기간 통제 |
| Joint | 공동 활동 | 그룹+특정 멤버 공동 프로젝트 | Group/Member에 이중 집계 금지 |

이 구조에서 BIGBANG의 최종 영향력은 단순히 'BIGBANG 점수 + G-DRAGON 점수 + TAEYANG 점수 +
DAESUNG 점수 + T.O.P 점수'가 아니다. Group Core와 Member의 독립적인 Incremental Impact를
계산하고, 공동 활동은 Joint Impact로 분리한 뒤 중복을 제거하여 FPU Impact를 산출한다.

## 5. FPU Impact 집계식

```
Raw FPU Impact = Group Core Impact + Σ Member Incremental Impact
                + Σ Unit Incremental Impact + Joint Impact
Adjusted FPU Impact = Raw FPU Impact × Quality Adjustment × Coverage Adjustment
```

여기서 Member Incremental Impact는 단순 멤버 언급량이 아니라 '그 멤버가 독립적인 영향력
노드로서 추가적으로 설명하는 효과'를 의미한다.

Joint Impact는 그룹과 멤버 모두의 원인으로 판단되는 사건을 별도 계산하는 항목이며, 같은
Evidence를 Group Core와 Member에 중복해서 더하지 않는다.

## 6. 중복 집계 방지 규칙

- 모든 사건에 event_id를 부여한다.
- 동일 사건을 여러 언론이 보도한 경우 source_cluster_id로 묶어 독립 사건과 단순 재인용을
  구분한다.
- 그룹과 멤버가 함께 원인이 되는 사건은 entity_scope='joint'로 기록한다.
- 그룹 앨범의 멤버 참여는 원칙적으로 Group Core에 귀속하고, 별도의 개인 활동에서 발생한
  효과만 Member Node로 귀속한다.
- 동일 팬이 그룹과 멤버를 동시에 지지할 수 있다는 점은 '팬 수의 합'으로 계산하지 않고 FPU의
  구성 구조와 overlap 변수로 관리한다.

## 7. Group–Member Overlap 변수

| 변수 | 정의 | 용도 |
|---|---|---|
| member_fan_overlap | 그룹 팬덤과 개인 팬덤의 중첩 정도 | 중복 소비/팬덤 구조 |
| cross_member_overlap | 멤버 팬덤 간 중첩 | 멀티멤버 지지 여부 |
| group_member_synergy | 그룹과 개인 활동이 함께 강화되는 정도 | 상호 강화 효과 |
| member_independence | 개인 활동의 독립성 | Member Node 활성화 |
| member_concentration | 개인 영향력의 집중도 | Star-centric 여부 |

## 8. Member Impact Share와 MCI의 역할 재정의

Member Impact Share는 '그룹 팬덤 전체 중 개인 팬덤의 팬 수가 몇 %인가'를 의미하지 않는다.
데이터에서 관측된 FPU 영향 중 어떤 비중이 Member Node의 독립 활동으로 설명되는지를
의미한다.

```
Member Impact Share_i = Adjusted Member Incremental Impact_i / Adjusted FPU Impact
```

MCI(Member Concentration Index)는 멤버 영향력이 몇 명에게 집중되어 있는지를 측정한다.
`p_i = Member Incremental Impact_i / Σ Member Incremental Impact_i`, `MCI = Σ p_i²`.

| 패턴 | MCI | 해석 |
|---|---|---|
| Group-centric | 낮음 | 그룹 자체 효과가 중심 |
| Multi-member | 중간 | 복수 멤버가 산업별로 분화 |
| Star-centric | 높음 | 소수 멤버가 FPU를 강하게 견인 |
| Hybrid | 중간+높은 Synergy | 그룹과 개인이 상호 강화 |

## 9. LDA 분석 단위도 FPU 구조에 맞춰 3단계로 변경

| Corpus | 문서 구성 | 핵심 질문 | 산출물 |
|---|---|---|---|
| Node Corpus | Group Core / Unit / Member 각각 | 각 Node의 핵심 서사는? | Node Topics |
| FPU Corpus | 한 팬덤의 모든 Node Evidence | 하나의 팬덤 포트폴리오는 무엇으로 구성되는가? | FPU Topics |
| Cross-FPU Corpus | 100개 FPU 비교 | 어떤 Topic/Factor가 팬덤 유형을 구분하는가? | 100-FPU Topic Matrix |

이 구조를 적용하면 'BIGBANG의 LDA Topic'과 'G-DRAGON의 LDA Topic'을 각각 도출한 뒤, 두
결과를 BIGBANG FPU의 Composite Topic Profile로 통합할 수 있다.

## 10. Topic → Meta Factor → Node 구조

| Meta Factor | 가능 Topic | 주요 Node |
|---|---|---|
| Fan Commitment | 팬클럽·총공·기부·커뮤니티 | Group/Member |
| Consumption Power | 초동·앨범·티켓·MD | Group/Member |
| Live Economy | 콘서트·투어·공연 | Group/Member |
| Brand & Commercial | 광고·앰버서더·팝업 | Member 중심 |
| Global Reach | 빌보드·해외투어·글로벌 차트 | Group/Member |
| Content/IP | OST·드라마·방송·웹콘텐츠 | Member 중심 |
| Creator/Artist Power | 작곡·프로듀싱·연출 | Member 중심 |
| Regional Spillover | 관광·지자체·지역매출 | Group/Member/Joint |

## 11. 100개 팬덤의 Research Agent 수집 프로토콜

① FPU 생성: 100개 팬덤 각각에 fandom_id와 fpu_id를 부여한다.
② Group Core 생성: 공식 그룹명·영문명·별칭 및 그룹 자체 활동을 등록한다.
③ Member Discovery: 독립 활동·팬덤·상업적 영향력이 확인되는 멤버를 후보군으로 만든다.
④ Member Activation: Member Activation Score를 계산하여 활성 Member Node를 확정한다.
⑤ Unit Discovery: 유닛 팬덤과 활동이 독립적인 그룹은 Unit Node를 생성한다.
⑥ Evidence 수집: Group / Unit / Member / Joint를 구분하여 문장 단위로 저장한다.
⑦ 다국어 수집: 한국어 → 영어 → 실제 활동시장 언어 순으로 확장한다.
⑧ Event Deduplication: event_id와 source_cluster_id를 이용해 중복을 제거한다.
⑨ Coverage Audit: 언어·시장·출처·시점별 빈 공간을 계산한다.
⑩ LDA: Node Corpus → FPU Corpus → Cross-FPU Corpus 순으로 분석한다.

## 12. Member Activation Score

100개 팬덤 전체 멤버를 동일 강도로 조사하면 데이터 비용과 노이즈가 증가한다. 따라서 아래
지표를 이용해 'FPU의 구성요소로 포함할 가치가 있는 멤버'를 선별한다.

| 항목 | 권고 가중치 | 판정 기준 |
|---|---|---|
| 독립 활동 Evidence | 25% | 솔로 음악·연기·예능·개인 콘텐츠 |
| 개인 상업/브랜드 | 20% | 광고·앰버서더·패션·팝업 |
| 개인 소비 Evidence | 20% | 솔로 앨범·공연·팬미팅 등 |
| 글로벌/시장 확장 | 15% | 해외 활동·현지 시장 성과 |
| 산업 다양성 | 10% | 음악 외 산업 연결 |
| Evidence 안정성 | 10% | 기간·출처·독립성 |

초기 100개 팬덤 파일럿에서 이 가중치와 활성화 기준을 민감도 분석한 후 최종 확정한다.
따라서 위 값은 실행을 위한 권고 설계값이며 현재 데이터에서 검증된 사실값은 아니다.

## 13. JSON v5.0 권고 구조

```json
{
  "fpu_id": "F_BIGBANG",
  "fandom_name": "BIGBANG",
  "composition_type": "composite",
  "nodes": [
    {"entity_type": "group_core", "entity_id": "G_BIGBANG", "active": true},
    {"entity_type": "member", "entity_id": "M_GDRAGON", "active": true},
    {"entity_type": "member", "entity_id": "M_TAEYANG", "active": true},
    {"entity_type": "member", "entity_id": "M_DAESUNG", "active": true},
    {"entity_type": "member", "entity_id": "M_TOP", "active": true}
  ],
  "evidence": [
    {"event_id": "EV_001", "entity_scope": "member", "entity_id": "M_GDRAGON",
     "source_cluster_id": "SC_001", "language": "en", "market": "global",
     "source_type": "media", "quantitative": true, "quality": 0.90,
     "text": "...", "url": "..."}
  ],
  "aggregation": {"group_core_impact": 0, "member_incremental_impact": 0,
                  "joint_impact": 0, "coverage_adjustment": 0, "fpu_impact": 0}
}
```

## 14. 기존 3D 그래프의 개정

기존 3D 그래프의 Z축이 근거문장 총량을 사용했다는 점을 고려하면, FPU 구조에서는 Z축을
'Member Concentration' 또는 'Member Diversity'로 변경하는 것이 더 적절하다. 그러면 X·Y의
FPU Loyalty/Spillover와 Z의 내부 구성 구조가 서로 다른 질문을 측정하게 된다.

| 축 | 변수 | 질문 |
|---|---|---|
| X | FPU Loyalty | 팬덤 내부 결속은 얼마나 강한가? |
| Y | FPU Spillover | 산업·지역으로 얼마나 확산되는가? |
| Z | MCI / Member Diversity | 그 영향력이 개인 멤버에 얼마나 집중되는가? |

3D 점 하나는 100개 FPU 중 하나를 의미하며, 점을 클릭하면 Group Core → Member Nodes →
Topic → Meta Factor로 Drill-down하는 구조를 권고한다.

## 15. FPU 내부 Drill-down 화면 설계

| 레이어 | 표현 | 사용자 질문 |
|---|---|---|
| Level 0 | 100 FPU 3D Map | 어떤 팬덤이 어떤 유형인가? |
| Level 1 | FPU 구성 막대 | 그룹과 개인 중 누가 영향력을 구성하는가? |
| Level 2 | Member Contribution | 어떤 멤버가 핵심인가? |
| Level 3 | Topic/Factor | 그 멤버의 영향은 어떤 산업에서 발생하는가? |
| Level 4 | Evidence | 실제 근거는 무엇인가? |
| Level 5 | Source/Language | 어떤 언어·시장·출처에서 확인됐는가? |

## 16. 100개 팬덤을 비교하는 최종 분석 프레임

| 분석 질문 | 핵심 지표 | 비교 단위 |
|---|---|---|
| 팬덤 전체 영향력 | FPU Impact | 100 FPU |
| 그룹 자체 효과 | Group Core Impact | Group Core |
| 개인 기여 | Member Impact Share | Member |
| 개인 집중도 | MCI | FPU |
| 그룹-개인 결합 | Synergy | FPU |
| 언어 편향 | Coverage Index | FPU |
| 핵심 서사 | Topic/Meta Factor | FPU/Node |
| 산업 확산 | Industry Spillover | FPU→Industry |
| 지역 확산 | Regional Spillover | FPU→Region |

## 17. Research Agent 최종 명령문 — FPU 버전

각 팬덤을 하나의 FPU(Fandom Portfolio Unit)로 정의하라. 먼저 Group Core를 생성하고, 그룹
내 개인 멤버 중 독립적인 팬덤·활동·상업적 영향력이 확인되는 멤버를 Member Node로
활성화하라. BIGBANG은 BIGBANG Core + G-DRAGON + TAEYANG + DAESUNG + T.O.P와 같이 구성한다.
BLACKPINK, 소녀시대 등도 동일 원칙을 적용한다. NCT와 같이 유닛이 독립적인 경우 Group Core +
Unit + Member의 3단 계층을 사용한다.

각 Evidence에는 fandom_id, fpu_id, entity_type, entity_id, entity_scope, event_id,
source_cluster_id, language, market, source_type, date, quantitative, quality, text,
url을 기록하라. 그룹과 멤버가 함께 원인이 되는 사건은 Joint Evidence로 기록하고 Group Core와
Member Node에 이중 점수화하지 말라. 동일 팬이 그룹과 개인을 동시에 지지할 수 있으므로 팬
수를 단순 합산하지 말고 overlap 구조로 관리하라. 자료 부족은 영향력 0이 아니라
coverage_gap으로 기록하라.

LDA는 Node Corpus, FPU Corpus, Cross-FPU Corpus의 세 층으로 수행하라. 최종적으로 Group
Core Impact + Member Incremental Impact + Unit Incremental Impact + Joint Impact의 구조로
FPU Impact를 산출하되 중복을 제거하라. 최종 결과에는 FPU Score, Group Core Contribution,
Member Impact Share, MCI, Group–Member Synergy, Coverage Index, Topic/Meta Factor
Profile을 포함하라.

## 18. 최종 결론

이번 개정에서 가장 중요한 변화는 '100개의 팬덤'을 '100개의 팬덤 포트폴리오'로 재정의하는
것이다. 100개 팬덤 간 비교는 동일한 FPU 레벨에서 수행하지만, 각 FPU 내부에서는 그룹 자체
효과와 개인 멤버의 독립 효과를 동시에 관찰한다.

따라서 BIGBANG은 [BIGBANG Core + G-DRAGON + TAEYANG + DAESUNG + T.O.P], BLACKPINK는
[BLACKPINK Core + JISOO + JENNIE + ROSÉ + LISA], 소녀시대는 [소녀시대 Core + TAEYEON +
YOONA + 활성 Member Nodes]와 같은 형태로 표현된다.

이 구조의 장점은 '그룹이 인기 있다'는 단일 결론을 넘어, 그 팬덤의 경제적·사회적 영향력이
그룹 자체에서 발생하는지, 특정 개인 스타에서 발생하는지, 여러 멤버에게 분산되는지, 또는
그룹과 개인의 상호작용에서 발생하는지를 정량적으로 설명할 수 있다는 것이다.

결과적으로 LDA는 단순한 키워드 군집 분석을 넘어, '100개 팬덤 포트폴리오 → Group/Unit/
Member → Topic → Meta Factor → Industry/Region'이라는 계층적 Fandom-omics 분석 체계로
발전한다.

---

## 정리자 주 — 이번 세션에서 이미 실행된 부분과 아직 없는 부분

이번 세션에서 복구된 실제 데이터(`data/v6_r22_snapshot/`)를 이 문서의 제안과 대조해보면:

- **이미 실행된 것**: Coverage Index 5-가중치 공식(2.3절)은 `fandom_scores_v6.json`의
  `coverage_detail.weights`에 정확히 같은 값(Language 0.30/Market 0.25/Source-Type 0.20/
  Time 0.15/Entity 0.10)으로 실제 반영되어 있다. Member Impact Share와 MCI(8.1~8.2절,
  v5의 8절)도 `member_mention_pilot_v6.json`에 23개 그룹에 대해 실제 파일럿 형태로 이미
  존재한다 — 다만 이 파일 자체가 "그룹 단위로 이미 수집된 근거문장 내 멤버명 언급 횟수
  기반"이라고 명시하듯, 멤버별 **독립 리서치**(Group Corpus와 분리된 Member Corpus)는 아직
  수행되지 않은 1차 신호다.
- **아직 없는 것**: Group-Only/Member-Only/Joint Evidence 분리, event_id/source_cluster_id
  기반 중복 제거, Group–Member Synergy 산식에 필요한 Joint Impact, Unit 계층(NCT 등),
  Member Activation Score의 6개 세부 항목별 근거, FPU 전체 스키마(JSON v5.0). 이 문서가
  제안하는 계층 구조 중 "Member 언급 횟수 집계" 단계까지는 실행됐고, 그 이후(독립 Member
  Corpus 구축, Joint/Synergy 계산)는 아직 설계 단계에 머물러 있다.

함께 제공하는 `analysis/group_member_fpu_pilot.ipynb`는 이 두 가지("이미 있는 것"과 "아직
없는 것")를 명확히 구분해서, 실행 가능한 부분은 실제 데이터로 계산하고 불가능한 부분은
왜 안 되는지와 무엇이 더 필요한지를 셀별로 명시한다.
