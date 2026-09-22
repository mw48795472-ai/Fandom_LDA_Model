# 이 프로젝트에 적용된 파이썬 코드 총정리

이 저장소에 들어 있는 파이썬 스크립트·노트북 전체를 정리한다. 모든 코드는 최종 근거 코퍼스
10,020건(`data/v7_final/fandoms_v3_100.json`)과 그로부터 산출된 최종 파일(`data/v7_final/`),
그리고 해석 계층의 동결 스냅샷(v7-40, 7,350건)을 입력으로 삼으며, 각 스크립트는 실행 후
원본 JSON의 집계값과 대조하는 자체 검증 루틴을 포함한다(전부 통과 확인됨).

경로 규칙: 모든 스크립트는 `Path(__file__).resolve().parents[N]`으로 저장소 루트를 찾아
`data/v7_final/`을 읽고, 생성물은 `output/` 아래(또는 `data/v7_final/`의 파생 CSV)에 쓴다.
`analysis/` 노트북은 `data/v7_final/fandoms_v3_100.json`이 있는 상위 폴더를 루트로 잡으므로
어느 위치에서 실행해도 된다.

## 한눈에 보기

| 분류 | 스크립트 | 입력 | 출력·확인 |
|---|---|---|---|
| 정합성 검증(루트) | `verify_v7_final_consistency.py` | `data/v7_final/*` 전부 | 보고서·KEY_FINDINGS 수치 101개 항목을 파일에서 재계산해 일치/불일치 출력 (101/101) |
| 파이프라인(루트) | `run_lda_v6.py` | 코퍼스 JSON (`--data`, 기본 `fandoms_v3_100.json`) | `output/lda_rerun/` — 토큰화→LDA K 탐색→K→M 재군집화→실루엣 게이트→점수·페르소나 |
| 차트 | `v7_final_10020/charts/build_cohesion_index_v7.py` | `fandom_cohesion_index_v7.json` | 팬덤결속 지수 좌우 2패널 PNG/SVG (`output/charts/`) |
| 차트 | `v7_final_10020/charts/build_cohesion_index_v7_right_only.py` | 〃 | 우측 패널(상위 25개 팬덤) 단독 PNG/SVG |
| 차트 | `v7_final_10020/charts/build_persona_cluster_split_boxed.py` | `factor_clustering_structure_v7.json`(코사인거리 행렬, 저장소 미포함)·`fan_persona_v7.json` (동결 스냅샷) | 덴드로그램 PNG + PCA biplot PNG (2개 분리) — 입력 1이 없어 저장소만으로는 실행 불가 |
| 차트 | `v7_final_10020/silhouette_gate_policy/build_silhouette_gate_timeline_v7.py` | `data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv` | 코퍼스 규모 vs 실루엣 이중축 타임라인 PNG/SVG, 게이트 구간 20회 기각·r=+0.15 자체 재계산 |
| 지수 CSV | `v7_final_10020/indices_csv/build_ad_commercial_index_csv.py` | `ad_commercial_index_v7.json` | `output/indices_csv/ad_commercial_index_v7.csv` |
| 지수 CSV | `v7_final_10020/indices_csv/build_domestic_regional_index_csv.py` | `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json` | `output/indices_csv/domestic_regional_index_v7.csv` |
| 지수 CSV | `v7_final_10020/indices_csv/build_worldwide_language_index_csv.py` | `worldwide_language_pilot_live_reference_v7.json` | `output/indices_csv/worldwide_language_index_v7.csv` |
| 데이터 export | `v7_final_10020/data_export/extract_html_payloads.py` | `3D_포지셔닝맵_국내100팬덤.html`, `Persona_결정공간.html` | HTML 내장 데이터 객체를 그대로 복사 → `chart3d_payload_live_reference_v7.json`, `persona_decision_space_v7.json` |
| 데이터 export | `v7_final_10020/data_export/build_bullets_flat_csv.py` | `fandoms_v3_100.json` (`--src`) | `bullets_flat_v7_final.csv` 10,020행 (`--expected`로 행 수 대조) |
| 데이터 export | `v7_final_10020/data_export/build_lda_k_grid_csv.py` | `lda_v6_diagnostics_live_reference_v7.json` (`--src`) | `lda_k_grid_live_reference_v7.csv` (K 후보별 perplexity·coherence·diversity·stability, `selected` 플래그) |
| 데이터 export | `v7_final_10020/data_export/build_corpus_growth_history_csv.py` | `data/v7_rounds/v6*_merge_log.json` + `merge_log_r*.json`·`swap_log_r*.json`·`round_log_r70.json` | `corpus_growth_history_v6_v7_full.csv` — v6 1차∼v7 r72(10,020건) 성장 이력, 체인 불연속을 `chain_gap`에 기록, 타임라인 CSV와 대조 |
| 데이터 export | `v7_final_10020/data_export/build_cohesion_media_index_csv.py` | `fandom_cohesion_index_v7.json`, `media_crossover_index_v7.json` | `fandom_cohesion_index_v7.csv`, `media_crossover_index_v7.csv` — 합계를 원본 집계 필드와 재대조 |
| 통계 검증(R 대조) | `Statistics/verify_r_sections_python.py` | `data/v7_final/` 점수·상관·K9 JSON, `Statistics/R_통계검증/data/member_mention_pilot_v7.json` | 보고서 2.1·2.2·3.8·7.4절 통계량 238개 항목을 scipy·statsmodels로 재계산 — `Statistics/R_통계검증/`(R)과 같은 항목·같은 정답지, 238/238 일치 |
| 지표 산정 노트북 | `v7_final_10020/index_methodology/build_index_calculation_notebook.py` → `index_calculation_v7.ipynb` | 코퍼스 10,020건, 라이브 점수 JSON(coverage_detail·factor_share), 3D payload | 식(1)∼(7)로 100개 팬덤 지표를 직접 산정 → `index_calculation_v7_result.csv`(100×17), 최종 산출 파일과 8개 항목 0/100 불일치 |
| 지표 산식 검증 | `v7_final_10020/index_methodology/verify_index_calculation_formulas.py` | `fandom_scores_live_reference_v7.json` | 식(2)(3)(6)(7) 재계산 불일치 0/100, 구현 시 주의점(창단 키워드·`n_num` 패턴 개수) 예시 출력 |
| 노트북 생성기 | `v7_final_10020/analysis/build_notebooks_v7.py` | (생성기) | 노트북 8개를 nbformat으로 생성하고 nbconvert로 실행해 출력 포함 저장. `python … [이름] [--no-exec]` |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py` | 라이브 점수 JSON, `language_domain_summary_v7.json`, 코퍼스 | 14개 언어 실측 합 = 요약(10,020), 도메인 분류기 재구성 1단계 83.3% → 2단계 95.9% |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py` | 코퍼스 (fugashi·jieba·pythainlp) | `analysis/tokenizer/csv/bullet_token_frequency_v7_final.csv` (43,162 토큰, 176,944 발생) |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/jieba_and_thai_engine_details_v7.py` | 위 CSV | 엔진 스펙 조회, HMM/newmm 데모, 중국어·태국어 버킷 재검증 불일치 0 |
| 토크나이저 | `v7_final_10020/analysis/tokenizer/stopwords/export_tokenizer_stopwords_v7.py` | `run_lda_v6.py`(ast), 토큰 빈도 스크립트(import), pythainlp | 코드에 정의된 불용어를 언어별로 추출 → `tokenizer_stopwords_by_language_v7.csv`(1,503행) + `TOKENIZER_STOPWORDS_BY_LANGUAGE.md` |

## A. 정합성 검증 — `verify_v7_final_consistency.py`

이 저장소의 중심 검증 스크립트다. 보고서·`KEY_FINDINGS.md`에 인용된 수치를 `data/v7_final/`의
파일에서 실제로 재계산해 항목별 일치/불일치를 출력하며, 어떤 수치도 맞추기 위해 조정하지
않는다. 핵심은 **충성도·파급효과 점수의 완전 재현**이다: `METHODOLOGY.md` 2-4절의 EvidenceScore
산식(문장당 1.0 + 0.5×수치표현 수 + 0.3×보너스 키워드 매치 수 → min-max 정규화)을
`fandoms_v3_100.json`(10,020건)에 그대로 적용하면 3D 맵 payload의 100개 팬덤 점수가 소수점 셋째
자리까지 전부 같고, 그 점수로 Pearson 0.493·Spearman 0.380·Cook's D(BTS 0.5749)·다중회귀
R² 0.847·VIF 1.93·민감도·LOO·3D축 독립성까지 KEY_FINDINGS 값이 그대로 나온다. 4분면
χ²(8.34/10.2273)도 점수 0.5 초과 여부 2×2표로 재현된다. 그 밖에 동결 스냅샷(activity 합 7,350,
페르소나 43/31/17/9), 라이브 참고 재적합(K=8/M=5/0.046 게이트 기각), 언어 커버리지 분모
ln(14)/ln(13), 보조지표 7종의 집계 합, 성장 이력·타임라인 CSV 대조까지 101개 항목을 확인한다.

## B. 원본 파이프라인 — `run_lda_v6.py`

v6∼v7 파이프라인 실물이다(재구성본이 아님). 토큰화 → `LatentDirichletAllocation` K 탐색
(perplexity·coherence·diversity·stability 복합 순위) → 토픽 φ분포 코사인거리 계층 군집화로 M 선정
→ 실루엣 게이트(동결 기준선 0.267 미달 시 기각) → EvidenceScore·Coverage·FactorDiversity 산출 →
페르소나 배정 순으로 동작하며, `--data`/`--out` 인자로 코퍼스와 출력 폴더를 지정한다(기본값:
최종 코퍼스 → `output/lda_rerun/`). 단 이 파일의 토크나이저는 14개 언어 문자권 라우팅
(fugashi·jieba·pythainlp 추가 경로) 이전 판이라, 최종 참고 재적합(10,020건 → 3토큰 미만 제외
후 10,018건, K=8/M=5/실루엣 0.046)을 만든 `run_lda_v6_live_reference_v7.py`와 문서 수가 다르다
(이 스크립트로 10,020건을 돌리면 9,954건). 라우팅 판의 소스는 저장소에 없고, 그 실행 결과는
`lda_v6_diagnostics_live_reference_v7.json`·`wordcloud_by_language_v7.json`으로 남아 있다.

## C. 차트 생성 스크립트 (matplotlib)

네 스크립트 모두 같은 골격을 공유한다: `matplotlib.use("Agg")`로 헤드리스 렌더링 →
`NotoSansCJKkr-Regular.otf`를 `FontProperties`로 로드해 한글 깨짐 방지 → JSON/CSV 로드 → 색상표
상수 정의 → `matplotlib` 축 조작 → PNG(300∼450dpi)+SVG를 `output/charts/`에 저장.

**`build_cohesion_index_v7.py`** — 팬덤결속 지수(보조지표, LDA와 무관한 키워드매칭 지표) 2패널
Figure. 좌측은 5개 결속 활동 유형(A∼E)별 근거문장 순위(`barh`, 내림차순), 우측은 상위 25개
팬덤의 유형 구성을 누적 막대로 표시하며 막대 끝에 비중(%) 라벨을 붙인다. BTS·임영웅·리센느는
y축 라벨을 굵게 강조.

**`build_cohesion_index_v7_right_only.py`** — 위 스크립트의 우측 패널만 별도 이미지로 분리한
버전. 집계·정렬 로직은 완전히 동일하게 복제하고(데이터는 건드리지 않음), figure 크기와 폰트
크기만 단독 이미지에 맞게 재조정했다.

**`build_persona_cluster_split_boxed.py`** — 두 개의 독립된 분석을 각각 별도 PNG로 생성한다.
1. *덴드로그램*: 동결 스냅샷의 토픽 간 코사인거리 행렬(`factor_clustering_structure_v7.json` — 이 파일은
   저장소에 없고, `persona_decision_space_v7.json`에는 병합 순서·PCA 좌표만 있어 행렬을 대신하지 못한다)을
   `scipy.cluster.hierarchy.linkage`
   (average-linkage)로 계층적 군집화하고, K→M 절단선을 `fcluster`로 계산해 덴드로그램을 그린다.
   가지 색상은 그 가지에 속한 토픽들이 전부 같은 F코드를 공유하면 해당 F코드 색, 섞여 있으면
   회색으로 칠하는 커스텀 `link_color_func`를 직접 구현.
2. *PCA biplot*: `fan_persona_v7.json`의 팬덤별 F1∼F5 factor_share 5차원 벡터를
   `sklearn.decomposition.PCA(n_components=2)`로 2차원에 투영하고, 페르소나별로 색을 다르게
   산점도로 표시. loading 벡터(F1∼F5 화살표)를 함께 그리고, 하이라이트 3개 팬덤(BTS·임영웅·
   리센느)은 밀집 영역 바깥 여백으로 라벨을 이동시켜 테두리 박스+화살표로 표시.

**`build_silhouette_gate_timeline_v7.py`** — 코퍼스 규모(막대)와 실루엣(선)의 이중축
타임라인. 실측 행과 "[추정·선형보간]" 행을 구분해 그리고, 게이트 구간(r46∼마지막 실측)의
라운드 수·상관계수·성장률을 그리기 전에 재계산해 출력한다. 상세는
`silhouette_gate_policy/SILHOUETTE_GATE_POLICY.md`.

## D. 지수 CSV 산출 스크립트

세 스크립트 전부 같은 패턴: JSON 로드 → 팬덤별 행 구성(지수 고유 컬럼 + 세부 카테고리별
언급수를 가로로 펼친 컬럼들) → 지정된 기준으로 내림차순 정렬 → `csv.DictWriter`로 `utf-8-sig`
(엑셀 한글 깨짐 방지) 저장 → **세부 카테고리 합계를 원본 JSON의 집계 필드와 재대조**하는
무결성 검증을 스크립트 끝에서 자체 수행하고 결과를 출력한다(전부 불일치 0건 확인됨). 국내
지역 지수의 입력 JSON은 `analysis/domestic_regional_index/domestic_regional_index_v7.ipynb`가
최종 코퍼스 10,020건에서 산출한 것이다.

## E. 데이터 export 스크립트

**`extract_html_payloads.py`** — HTML 2종에 `const payload = {...}` / `const DATA = {...}`로
내장된 데이터 객체를 문자열 그대로 잘라내 JSON으로 저장한다. 3D 맵 payload는 최종 코퍼스
10,020건 점수·4구획(24/17/10/49)·라이브 재적합 진단, Persona는 동결 K=10 토픽명·F코드·PCA·
F1∼F5 비중을 담는다.

**`build_bullets_flat_csv.py`** — `fandoms_v3_100.json`(팬덤별 `loyalty`/`spillover` 중첩 배열)을
`fandom, category, bullet_type, text, url` 5개 컬럼의 단일 평면 CSV(10,020행)로 펼친다.

**`build_lda_k_grid_csv.py`** — 진단 JSON의 `k_grid`(K 후보별 perplexity·coherence·diversity·
stability·composite_rank_sum 비교표)를 CSV로 풀고, `selected_k`와 일치하는 행에
`selected=True` 플래그를 붙인다.

**`build_corpus_growth_history_csv.py`** — 서로 다른 스키마를 가진 병합·교체 로그(v6 1·2차,
v6.3 시장 다양화, v6.4 언어 다양화, v7 r1∼r72; r36∼r59는 키 이름이 다름)를 공통 스키마
(`stage, kind, before_total, after_total, net_new_bullets, n_touched_fandoms, roster_change, note`)로
정규화해 하나의 시계열 CSV로 이어붙인다. 각 행의 `after_total`이 다음 행의 `before_total`과
이어지는지 체인 연속성을 검증하며, 로그 자체의 기록 오차(r21→r22 +1 등)는 숨기지 않고
`chain_gap` 컬럼에 그대로 적는다. 마지막 `after_total`이 10,020인지 확인한다.

**`build_cohesion_media_index_csv.py`** — 팬덤결속·미디어 크로스오버 지수 JSON을 팬덤별
유형/매체 집계 CSV로 펼치고 합계를 원본 집계 필드와 재대조한다.

## F. `v7_final_10020/analysis/` — 노트북 8개와 토크나이저 스크립트

`build_notebooks_v7.py`가 nbformat으로 셀을 조립하고 `jupyter nbconvert --execute`로 끝까지
실행해 출력이 포함된 `.ipynb`를 저장한다(에러 0건). 각 노트북은 최종 코퍼스 10,020건 또는
동결 스냅샷을 읽어 해당 지수 JSON의 값을 독립적으로 재계산·대조한다.

| 노트북 | 입력 | 확인 결과 |
|---|---|---|
| `ad_commercial_index/ad_commercial_index_v7.ipynb` | `ad_commercial_index_v7.json`, 코퍼스, 라이브 점수 | 무결성 100/100, 광고신호 키워드 재매칭 96/100 정확 일치, LDA 브랜드·상업형 비중과 r=0.834 |
| `fandom_cohesion_index/fandom_cohesion_index_v7.ipynb` | `fandom_cohesion_index_v7.json`, 동결·라이브 점수 | 무결성 100/100, 동결 LDA 결속형과 r=0.687 |
| `media_content_exposure_index/media_content_exposure_v7.ipynb` | 노출·크로스오버 지수, `k9_validation_v7.json`, r10·r11 로그 | 무결성 100/100, r10+r11 274건 일치, 서브태그 재매칭 100/100 |
| `domestic_regional_index/domestic_regional_index_v7.ipynb` | 코퍼스 10,020건, 동결 점수 JSON | 17개 지역 사전으로 **`domestic_regional_index_v7.json/.csv` 산출**(언급 1,226건, 적중 팬덤 469), 보고서 표 15 동결 근사 17/20행 재현 |
| `worldwide_language_index/worldwide_language_index_v7.ipynb` | 라이브 점수 JSON, 세계 언어 지수 JSON/CSV, 언어 요약 | ln(14)/ln(13) 각 100/100, 8개 필드 불일치 0 |
| `group_member_index/group_member_index_v7.ipynb` | `member_mention_index_v7.json`, 파일럿 v6, 상관 JSON | MCI 재계산 0/45 불일치, r(MCI, 멤버 수) −0.728 |
| `fan_impact_pathway/fan_impact_pathway_v7.ipynb` | 동결 진단·페르소나·토픽 카드·경로 맵·결정공간 | 매핑 10/10, Factor-specific Impact 500/500, 페르소나 43/31/17/9 |
| `tokenizer/tokenizer_script_routing_v7.ipynb` | 코퍼스, `wordcloud_by_language_v7.json` | 문자권 다중 라벨 재현(태국·러시아·베트남 정확 일치, 소수 언어 순위 5/5) |

토크나이저 스크립트 3종(`build_multilingual_bullet_language_classifier_v7.py`,
`build_bullet_token_frequency_csv_v7.py`, `jieba_and_thai_engine_details_v7.py`)은 fugashi
(unidic-lite)·jieba·pythainlp를 실제로 실행한다. 원본 파이프라인의 불용어 목록은 저장소에 없어
토큰 빈도 CSV는 독자 정의 불용어를 쓴 병행 산출물이며, 상세는
`tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` "재현 범위" 참고.

## 공통적으로 쓰인 패턴

- **무결성 자체검증**: 모든 산출 스크립트가 "세부 항목의 합 == 원본 JSON의 집계 필드"를
  스크립트 끝에서 재계산해 출력한다. 결과를 사람이 눈으로 믿는 대신 매번 프로그램이 스스로
  대조하도록 만든 것.
- **한글 인코딩**: CSV는 전부 `utf-8-sig`로 저장(엑셀에서 한글이 깨지지 않도록), 차트는
  `NotoSansCJKkr-Regular.otf`를 명시적으로 폰트매니저에 등록.
- **데이터 미변형 원칙**: 패널 분리·라벨 위치 변경 등 순수 표현(presentation) 변경 스크립트는
  주석에 "집계 로직은 전혀 바꾸지 않았다"를 명시하고, 실제로 원본과 동일한 정렬·필터 로직을
  그대로 복제한 뒤 결과만 다시 검증한다.
- **원본 데이터 불변**: 어떤 스크립트도 `data/v7_final/`의 원본 JSON을 덮어쓰지 않는다. 생성물은
  `output/` 또는 파생 CSV 파일로만 나간다.
