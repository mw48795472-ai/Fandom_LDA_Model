# 시계열분석 — 근거문장 시점 태그 기반 팬덤×연도 패널 분석

루트 README의 본 분석과 **별개의 탐색 분석**이다. 해석 계층·점수 정의·순위표·보조지표는 손대지 않고, 근거문장 10,020건에 사건 연도를 붙여 같은 EvidenceScore 산식을 연도별로 다시 센다. 저장소의 다른 파일을 바꾸지 않는다.

| 파일 | 내용 |
|---|---|
| `시계열_패널분석_V7.md` | 결과 문서(스크립트가 생성): 시점 태깅 → 팬덤×연도 패널 → 연도별 횡단면 상관·팬덤별 추세·고정효과 회귀 → 수집 편향 → 경로 비중 연도 추이(근사) → 한계 |
| `시계열_패널분석_상세명세서.docx` | 데이터·규칙·산식·검증·산출물 명세 (`build_ts_spec.js`가 `output/summary_v7.json`에서 수치를 채움; Node.js `docx` 패키지 필요) |
| `timeseries_panel_v7.py` | 전체 파이프라인 (약 6초) → `output/` + 결과 MD |
| `build_timeseries_notebook_v7.py` → `시계열_패널분석_v7.ipynb` | 단계별 노트북(실행 결과 포함, `jupyter nbconvert --execute`) |
| `R/` · `시계열분석_R코드.zip` | base R 대응 코드(연도별 상관·고정효과 회귀·추세·부트스트랩). `Rscript 시계열분석/R/RUN_ALL.R` → `output/r_verify_summary.txt`. 이 환경에 R이 없어 미실행 |
| `output/` | CSV 8개(`sentence_time_tags`, `fandom_year_panel`, `year_summary`, `fandom_trend`, `bootstrap_year_cells`, `round_year_distribution`, `fandom_year_factor_share`, `persona_transition`) + `summary_v7.json` + 그림 4장 |

실행 순서: `python 시계열분석/timeseries_panel_v7.py` → `python 시계열분석/build_timeseries_notebook_v7.py` → (선택) `Rscript 시계열분석/R/RUN_ALL.R`.
