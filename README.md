# K-팬덤의 지역관광 파급효과 분석 — 데이터오름

**「2026년 문화체육관광 통계 활용대회」 제출작**
세부 주제: *K-팬덤의 지역관광 파급효과 분석: 팬덤의 온라인 관심과 공연이 지역 방문·소비에 미치는 영향*
팀명: 데이터오름 (서목원, 고려대학교 학부생 외)

---

## ⚠️ 이 저장소에 대한 중요한 안내

이 저장소는 **여러 날에 걸친 Claude(Cowork) 세션에서 진행된 분석 대화 기록을 바탕으로 사후 재구성**한 것입니다.
작업이 이루어진 클라우드 샌드박스 컨테이너는 세션 종료/장시간 미사용 시 자동 회수되며, 이번 정리 작업 시점에는
`/home/claude/work` 아래 있던 원본 데이터(JSON), 중간 산출물, 최종 결과 파일이 이미 회수되어 남아있지 않았습니다.
따라서 이 저장소에 포함된 것과 포함되지 않은 것을 명확히 구분합니다.

**포함된 것 (대화 기록에 코드 전문이 남아 있어 그대로 재구성)**
- `scripts/charts/` — 팬덤결속 지수 차트, Persona 클러스터(덴드로그램+PCA biplot) 차트 생성 스크립트
- `scripts/indices_csv/` — 국내 지역 지수·세계 언어 지수·광고 상업성 지수 CSV 산출 스크립트
- `scripts/reports/` — 「2026년 문화체육관광 통계 활용대회」 요약보고서(docx) 빌드 스크립트
- `docs/` — 프로젝트 전체 방법론, 검증된 통계 수치, 최종 결과보고서(20p) 요약을 대화 기록에서 정리한 문서

**포함되지 않은 것 (원본이 유실되어 재현 불가, 재업로드 필요)**
- `data/` 아래 있던 원본 JSON 데이터 (예: `fandom_cohesion_index_v7.json`, `factor_clustering_structure_v7.json`,
  `positioning_map_correlation_live_v7.json`, `domestic_regional_index_live_reference_v7.json` 등) — 위 스크립트들은
  전부 이 데이터가 있어야 실행 가능합니다.
- 근거문장 원본 코퍼스(10,020건, 14개 언어권 704개 도메인 크롤링 결과)
- 렌더링된 최종 차트 PNG/SVG, 실루엣 계수 진단 보고서(docx), 최종 분석보고서 PDF(20p), 요약보고서 docx,
  이번 세션에서 만든 CSV 3종의 실제 출력 파일
- claude.ai에 게시된 아티팩트(Persona 결정 공간, 3D 포지셔닝 맵 등)의 소스 HTML

→ 위 파일들 중 사용자가 대화 중 SendUserFile로 전달받아 로컬에 저장해 둔 것이 있다면, 그것을 다시 첨부해 주시면
`data/`, `output/` 폴더에 넣어 커밋을 보강할 수 있습니다.

---

## 프로젝트 개요

K-POP·트로트 등 국내 대표 팬덤 100개를 대상으로, (1) LDA 토픽모델링 기반 텍스트마이닝으로 팬덤별 충성도×파급효과
유형을 분류하고, (2) 리센느(RESCENE) 홍보대사 위촉 사례와 BTS·임영웅 콘서트 사례를 이중차분법(DID)으로 검증하여,
"팬덤의 온라인 관심이 실제 지역 방문·소비로 전환되는 조건"을 실증적으로 분석했다. 분석 대상 100개 팬덤의 근거문장은
14개 언어권 704개 도메인에서 수집한 10,020건이며, 통계적 재군집화(LDA)와는 독립적으로 원문 키워드 매칭 기반
보조지표 7종을 병행 산출해 다각도로 분석을 보완했다.

세부 방법론과 검증된 수치는 `docs/METHODOLOGY.md`, `docs/KEY_FINDINGS.md`를 참고.

## 저장소 구조

```
kpop-fandom-project/
├── README.md                      (본 파일)
├── docs/
│   ├── METHODOLOGY.md             전체 분석 파이프라인 상세 설명
│   ├── KEY_FINDINGS.md            대화 중 검증된 모든 통계 수치 정리
│   └── FINAL_REPORT_SUMMARY.md    최종 분석보고서(20p) 챕터별 요약
├── scripts/
│   ├── charts/                    matplotlib 차트 생성 스크립트 (데이터 파일 필요)
│   ├── indices_csv/                보조지표 → CSV 산출 스크립트 (데이터 파일 필요)
│   └── reports/                   docx 요약보고서 빌드 스크립트 (docx npm 패키지 필요)
└── data/                          (비어 있음 — 원본 데이터 재업로드 필요, README 참고)
```

## 재현 방법 (데이터 재확보 후)

```bash
# 1) 차트 재생성 (원본 JSON을 data/ 아래 배치 후)
pip install matplotlib numpy scipy scikit-learn --break-system-packages
python3 scripts/charts/build_cohesion_index_v7.py
python3 scripts/charts/build_persona_cluster_split_boxed.py

# 2) 보조지표 CSV 재생성
python3 scripts/indices_csv/build_domestic_regional_index_csv.py
python3 scripts/indices_csv/build_worldwide_language_index_csv.py
python3 scripts/indices_csv/build_ad_commercial_index_csv.py

# 3) 요약보고서 docx 재생성
npm install docx
node scripts/reports/build_summary_report_2026_contest.js
```

## 데이터 무결성 원칙

이 프로젝트 전반에서 일관되게 지킨 원칙: 모든 차트·CSV 편집은 스타일(폰트 크기, 색상, 레이아웃)만 바꾸고 수치
계산 로직은 절대 건드리지 않으며, 매 산출물마다 원본 JSON을 다시 읽어 독립적으로 재계산한 값과 대조 검증한다.
(`scripts/` 내 각 스크립트 하단의 무결성 재검증 로직 참고.)
