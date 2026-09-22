# 이 프로젝트에 적용된 파이썬 코드 총정리

> **2026-09-21 갱신 주** — 이 문서의 표는 원래 `kpop-fandom-project` 저장소의 `scripts/…` 경로 기준으로 쓰였다.
> 현재 GitHub 저장소는 폴더를 한 단계 얕게 두고 있어(`scripts/charts/` → `charts/`, `scripts/indices_csv/` →
> `indices_csv/`, `scripts/tokenizer/` → `TOKENIZER/`), 아래 표의 경로는 그대로 두되 실제 위치는 이 대응으로 읽으면
> 된다. 모든 스크립트의 입력·출력 경로는 이전 세션 절대경로(`/home/claude/work/...`)에서 **저장소 상대경로**로
> 고쳤다: 최종 산출물 입력은 `data/v7_final/`, r22 스냅샷 입력은 `data/v6_r22_snapshot/`, 생성물은 `output/`.
> 데이터 파일이 두 곳(`data/v7_final/` 10,020건 최종, `data/v6_r22_snapshot/` 5,612건)으로 정리되면서 새로 추가된
> 스크립트는 맨 아래 "E. 2026-09-21 추가 스크립트" 절에 있다. 표의 "저장소 밖" 표시 파일(`build_notebook.py`,
> `run_lda_v6_reconstructed.ipynb`, `build_*_pilot_v6_csv.py`, `build_corpus_growth_history_csv.py`)은 여전히 이 GitHub
> 저장소에 없다(산출물 CSV만 `data/v6_r22_snapshot/csv/`에 있음).

이 세션(샌드박스 복구 이후)에서 실제로 작성·실행한 파이썬 코드 전체를 정리한다. 전부
`kpop-fandom-project` 저장소의 `scripts/` 아래에 커밋되어 있고, 각 스크립트는 실행 후 원본
JSON의 집계값과 대조하는 자체 검증 루틴을 포함한다(전부 통과 확인됨).

## 한눈에 보기

| 분류 | 스크립트 | 입력 | 출력 |
|---|---|---|---|
| 차트 | `scripts/charts/build_cohesion_index_v7.py` | `fandom_cohesion_index_v7.json` | 팬덤결속 지수 좌우 2패널 PNG/SVG |
| 차트 | `scripts/charts/build_cohesion_index_v7_right_only.py` | 〃 | 우측 패널(상위 25개 팬덤) 단독 PNG/SVG |
| 차트 | `scripts/charts/build_persona_cluster_split_boxed.py` | `factor_clustering_structure_v7.json`, `fan_persona_v7.json` | 덴드로그램 PNG + PCA biplot PNG (2개 분리) |
| 지수 CSV(v7 최종) | `scripts/indices_csv/build_domestic_regional_index_csv.py` | `domestic_regional_index_live_reference_v7.json` | `domestic_regional_index_v7.csv` |
| 지수 CSV(v7 최종) | `scripts/indices_csv/build_worldwide_language_index_csv.py` | `worldwide_language_index_live_reference_v7.json` | `worldwide_language_index_v7.csv` |
| 지수 CSV(v7 최종) | `scripts/indices_csv/build_ad_commercial_index_csv.py` | `ad_commercial_index_v7.json` | `ad_commercial_index_v7.csv` |
| 지수 CSV(v6 파일럿, 복구데이터) | `scripts/indices_csv/build_domestic_regional_pilot_v6_csv.py` | `data/v6_r22_snapshot/domestic_regional_pilot_v6.json` | `domestic_regional_pilot_v6.csv` |
| 지수 CSV(v6 파일럿, 복구데이터) | `scripts/indices_csv/build_member_mention_pilot_v6_csv.py` | `data/v6_r22_snapshot/member_mention_pilot_v6.json` | `member_concentration_pilot_v6.csv` + `member_mentions_pilot_v6_long.csv` |
| 데이터 export(복구데이터) | `scripts/data_export/build_lda_k_grid_csv.py` | `lda_v6_diagnostics.json` | `lda_k_grid_v6.csv` |
| 데이터 export(복구데이터) | `scripts/data_export/build_corpus_growth_history_csv.py` | 4개 병합로그 + `v7_progress.json` | `corpus_growth_history_v6_v7.csv` |
| 데이터 export(복구데이터) | `scripts/data_export/build_bullets_flat_csv.py` | `fandoms_v3_100.json` | `bullets_flat_v6_r22.csv` |
| 분석 파이프라인 | `analysis/run_lda_v6_reconstructed.ipynb` (생성기: `build_notebook.py`, 저장소 밖) | 없음(합성 데이터 자체 생성) | 노트북 12개 코드 셀, 실행검증완료 |

---

## A. 차트 생성 스크립트 (matplotlib)

세 스크립트 모두 같은 골격을 공유한다: `matplotlib.use("Agg")`로 헤드리스 렌더링 →
`NotoSansCJKkr-Regular.otf`를 `FontProperties`로 로드해 한글 깨짐 방지 → JSON 로드 → 색상표
상수 정의 → `matplotlib` 축 조작(barh/scatter/dendrogram) → PNG(400~450dpi)+SVG 저장.

**`build_cohesion_index_v7.py`** — 팬덤결속 지수(보조지표, LDA와 무관한 키워드매칭 지표) 2패널
Figure. 좌측은 5개 결속 활동 유형(A~E)별 근거문장 순위(`barh`, 내림차순), 우측은 상위 25개
팬덤의 유형 구성을 누적 막대(stacked barh)로 표시하며 막대 끝에 비중(%) 라벨을 붙인다. BTS·
임영웅·리센느는 y축 라벨을 굵게 강조.

**`build_cohesion_index_v7_right_only.py`** — 위 스크립트의 우측 패널만 별도 이미지로 분리한
버전. 집계·정렬 로직은 완전히 동일하게 복제하고(데이터는 건드리지 않음), figure 크기와 폰트
크기만 단독 이미지에 맞게 재조정했다.

**`build_persona_cluster_split_boxed.py`** — 가장 복잡한 차트 스크립트. 두 개의 독립된 분석을
각각 별도 PNG로 생성한다.
1. *왼쪽(덴드로그램)*: `factor_clustering_structure_v7.json`의 토픽 간 코사인거리 행렬을
   `scipy.cluster.hierarchy.linkage`(average-linkage)로 계층적 군집화하고, K→M 절단선을
   `fcluster`로 계산해 덴드로그램을 그린다. 가지 색상은 그 가지에 속한 토픽들이 전부 같은
   F코드를 공유하면 해당 F코드 색, 섞여 있으면 회색으로 칠하는 커스텀
   `link_color_func`를 직접 구현.
2. *오른쪽(PCA biplot)*: `fan_persona_v7.json`의 팬덤별 F1~F5 factor_share 5차원 벡터를
   `sklearn.decomposition.PCA(n_components=2)`로 2차원에 투영하고, 페르소나별로 색을 다르게
   산점도로 표시. loading 벡터(F1~F5 화살표)를 겹치지 않게 스케일링해서 함께 그리고, 하이라이트
   3개 팬덤(BTS·임영웅·리센느)은 밀집 영역 바깥 여백으로 라벨을 이동시켜 테두리 박스+화살표로
   표시(`ax.annotate` + `bbox`).

## B. 지수 CSV 산출 스크립트

**v7 최종본 3개**(`build_domestic_regional_index_csv.py`, `build_worldwide_language_index_csv.py`,
`build_ad_commercial_index_csv.py`) — 전부 같은 패턴: JSON 로드 → 팬덤별 행 구성(지수 고유
컬럼 + 세부 카테고리별 언급수를 가로로 펼친 컬럼들) → 지정된 기준으로 내림차순 정렬 → `csv.
DictWriter`로 `utf-8-sig`(엑셀 한글 깨짐 방지) 저장 → **세부 카테고리 합계를 원본 JSON의
집계 필드와 재대조**하는 무결성 검증을 스크립트 끝에서 자체 수행하고 결과를 출력한다(전부
불일치 0건 확인됨).

**v6 파일럿 2개**(이번 세션에서 복구된 실데이터용, `build_domestic_regional_pilot_v6_csv.py`,
`build_member_mention_pilot_v6_csv.py`) — 위와 동일한 패턴을 새로 업로드된 v6 파일럿 데이터에
적용. 멤버 언급 파일럿은 그룹별로 멤버 수가 다르므로 요약(그룹당 1행)과 long format(멤버당
1행) 두 개의 CSV로 나눠 산출했고, 멤버별 mention_count 합계와 impact_share 합계(≈1.0)를 각각
재검증했다.

## C. 데이터 export 스크립트 (복구된 v6/v7 라운드22 데이터 정리용)

**`build_lda_k_grid_csv.py`** — `lda_v6_diagnostics.json`의 `k_grid`(K 후보 7개별 perplexity·
coherence·diversity·stability·composite_rank_sum 비교표)를 CSV로 풀고, `selected_k`와 일치하는
행에 `selected=True` 플래그를 붙인다.

**`build_corpus_growth_history_csv.py`** — 4개의 서로 다른 스키마를 가진 병합 로그(v6 1·2차
라운드, v6.3 시장 다양화, v6.4 언어 다양화, v7 라운드1~22)를 공통 스키마(`stage, fired_at,
before_total, after_total, net_new_bullets, n_touched_fandoms, note`)로 정규화해 하나의
시계열 CSV로 이어붙인다. 각 행의 `after_total`이 다음 행의 `before_total`과 정확히 이어지는지
체인 연속성을 자체 검증하며, 라운드21→22 사이 실제 1건 간극을 숨기지 않고 그대로 출력한다.

**`build_bullets_flat_csv.py`** — `fandoms_v3_100.json`(팬덤별 `loyalty`/`spillover` 중첩 배열)을
`fandom, category, bullet_type, text, url` 5개 컬럼의 단일 평면 CSV(5,612행)로 펼친다. 행 수를
`v7_progress.json`의 `current_total`과 대조 검증.

## D. 분석 파이프라인 재구성 노트북

`run_lda_v6_reconstructed.ipynb`는 원본 `run_lda_v6_live_reference_v7.py`의 소스코드 자체가
유실된 상태에서, `docs/METHODOLOGY.md`에 문서화된 방법론을 근거로 로직만 동일하게 재구현한
**재구성본**이다(생성 스크립트 `build_notebook.py`는 `nbformat`으로 셀을 조립해 `.ipynb`를
써내는 별도 파이썬 파일이며, 저장소가 아니라 세션 작업 디렉터리에만 있음). 노트북 안의 12개
코드 셀이 구현하는 것:

1. 합성 코퍼스 생성(`sklearn`이 필요로 하는 스키마를 맞춘 더미 근거문장)
2. `sklearn.decomposition.LatentDirichletAllocation(n_components=10)`로 K=10 토픽화 +
   φ분포 상위 4키워드 자동 명명
3. 토픽 φ분포 코사인거리 → `AgglomerativeClustering(metric="precomputed", linkage="average")`로
   M={5,6,7,8} 후보 중 `silhouette_score` 최댓값 선정
4. `LABEL_RULES` 8버킷 키워드매칭 + 라벨 중복시 구분 키워드 부착 로직(`label_for_factor()`)
5. `persona_table_definition` 10콤보 사전정의 매핑으로 persona 배정
6. `EvidenceScore` 가중합 산식(숫자 포함·보너스 키워드 매치 기반) → min-max 정규화 →
   Loyalty×Spillover 4구획 분류
7. 강건성 검증 — `scipy.stats.shapiro/pearsonr/spearmanr`, `statsmodels`
   다중회귀+VIF(`variance_inflation_factor`), Cook's Distance(`OLSInfluence`),
   leave-one-out 민감도
8. `silhouette_gate()` — 새 라운드 실루엣이 동결 기준선(0.267)을 못 넘으면 자동 기각하는
   거버넌스 함수

12개 셀 전부 `jupyter nbconvert --execute`로 끝까지 실행해 에러 0건 확인. 이번 세션에서 복구된
`data/v6_r22_snapshot/`의 실데이터(특히 `fandoms_v3_100.json`, `lda_v6_diagnostics.json`)로
1번 데이터 로딩 셀을 교체하면, 합성 데이터가 아닌 실측 파이프라인 결과를 보여주는 노트북으로
업그레이드할 수 있다(아직 미적용 — 이 노트북 자체는 현재 GitHub 저장소에 없다).

실제 원본 파이프라인 `run_lda_v6.py`(v6~v7 r22 시점, 재구성본이 아닌 실물)는 저장소 루트에 있다.
2026-09-21 정리에서 `--data`/`--out` 인자를 붙여 두 코퍼스 어디에나 돌릴 수 있게 했고(기본값: r22 스냅샷 →
`output/lda_rerun/`), 파이프라인 로직은 건드리지 않았다. 단 최종 라이브 재적합(10,020건, K=8/M=5/실루엣 0.046)을
만든 `run_lda_v6_live_reference_v7.py`(14개 언어 토크나이저 라우팅 반영본)는 소스가 없어, 이 스크립트로
10,020건을 돌리면 문서 수 9,954건(구 토크나이저 기준)으로 보고서의 10,018건과 다르다.

## E. 2026-09-21 추가 스크립트 — 최종 코퍼스(10,020건) 정합성·파생 파일

| 스크립트 | 입력 | 출력 |
|---|---|---|
| `verify_v7_final_consistency.py` (루트) | `data/v7_final/*` 전부 | 보고서·KEY_FINDINGS 수치 91개 항목을 파일에서 재계산해 일치/불일치 출력 (현재 91/91 일치. χ²는 `positioning_map_correlation_live_v7.json`의 0.5 임계값 분할표로 재현) |
| `data_export/extract_html_payloads.py` | `3D_포지셔닝맵_국내100팬덤.html`, `Persona_결정공간.html` | HTML에 리터럴로 내장된 데이터 객체를 그대로 복사 → `data/v7_final/chart3d_payload_live_reference_v7.json`(라이브 100개 팬덤 점수·4구획·라이브 재적합 진단), `persona_decision_space_v7.json`(동결 K=10 토픽명·F코드·PCA·F1~F5 비중) |
| `data_export/build_bullets_flat_csv.py` | `fandoms_v3_100.json` (`--src`, 기본 v7_final) | `bullets_flat_v7_final.csv` 10,020행 (r22에 쓰면 기존 `bullets_flat_v6_r22.csv`와 바이트 단위 동일 결과) |
| `data_export/build_lda_k_grid_csv.py` | LDA 진단 JSON (`--src`, 기본 라이브 참고 재적합) | `lda_k_grid_live_reference_v7.csv` (r22에 쓰면 기존 `lda_k_grid_v6.csv`와 동일) |
| `data_export/build_cohesion_media_index_csv.py` | `fandom_cohesion_index_v7.json`, `media_crossover_index_v7.json` | `fandom_cohesion_index_v7.csv`, `media_crossover_index_v7.csv` — 팬덤별 유형/매체 집계 CSV, 합계를 원본 집계 필드와 재대조 |
| `data_export/build_live_scores_csv.py` | `chart3d_payload_live_reference_v7.json` | `chart3d_positioning_rows_live_v7.csv` — 라이브 점수·다양성·커버리지·activity·4구획; activity 합 10,020, 평균·4구획 카운트 재대조 (원본 산출물 `fandom_scores_live_reference_v7.csv`가 추가되면서 파생 파일명을 변경) |

`verify_v7_final_consistency.py`가 확인하는 핵심은 **충성도·파급효과 점수의 완전 재현**이다: `METHODOLOGY.md`
2-4절의 EvidenceScore 산식(문장당 1.0 + 0.5×수치표현 수 + 0.3×보너스 키워드 매치 수 → min-max 정규화)을
`fandoms_v3_100.json`(10,020건)에 그대로 적용하면 3D 맵 payload의 100개 팬덤 점수가 소수점 셋째 자리까지 전부
같고, 그 점수로 Pearson 0.493·Spearman 0.380·Cook's D(BTS 0.5749)·다중회귀 R² 0.847·VIF 1.93·민감도·LOO·3D축
독립성까지 KEY_FINDINGS 값이 그대로 나온다. 4분면 χ²(8.34/10.2273)도 점수 0.5 초과 여부 2×2표로 재현된다(README 3절).

## 공통적으로 쓰인 패턴

- **무결성 자체검증**: 모든 산출 스크립트가 "세부 항목의 합 == 원본 JSON의 집계 필드"를
  스크립트 끝에서 재계산해 출력한다. 결과를 사람이 눈으로 믿는 대신 매번 프로그램이 스스로
  대조하도록 만든 것.
- **한글 인코딩**: CSV는 전부 `utf-8-sig`로 저장(엑셀에서 한글이 깨지지 않도록), 차트는
  `NotoSansCJKkr-Regular.otf`를 명시적으로 폰트매니저에 등록.
- **데이터 미변형 원칙**: 패널 분리·라벨 위치 변경 등 순수 표현(presentation) 변경 스크립트는
  주석에 "집계 로직은 전혀 바꾸지 않았다"를 명시하고, 실제로 원본과 동일한 정렬·필터 로직을
  그대로 복제한 뒤 결과만 다시 검증한다.
