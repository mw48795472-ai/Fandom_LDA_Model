# 국내 대표 팬덤 100개 LDA 토픽모델링 — 팬충성도 × 파급효과 분석 저장소

「2026년 문화체육관광 통계 활용대회」 분석보고서(*K-팬덤의 지역관광 파급효과 분석*, 팀 데이터 오름)
2장 "국내 100대 팬덤 충성도×파급효과 유형 분석: LDA 토픽 모델링"의 데이터·코드·문서를 모아둔 저장소다.
제출본 PDF 2종(`(분석보고서)…최종.pdf`, `(요약보고서)…최종.pdf`)이 루트에 있으며, 저장소의 모든 수치는
이 PDF의 수치를 기준으로 정합성을 맞췄다.

> **2026-09-21 정리** — 그동안 이 저장소에는 v7 라운드22 스냅샷(근거문장 5,612건)만 있었고, 최종 제출본이
> 근거로 삼은 **라이브 코퍼스 10,020건과 최종 산출물은 없어서** 문서·코드 곳곳이 "10,020건은 이 세션에
> 없어 재현 불가"라고 적혀 있었다. 이번 정리에서 최종 코퍼스와 산출물을 `data/v7_final/`로 추가하고,
> 5,612건 스냅샷은 `data/v6_r22_snapshot/`으로 옮겨 두 데이터가 같은 파일명으로 섞이지 않게 했다.
> 최종 수치가 저장소 파일에서 실제로 재현되는지는 `verify_v7_final_consistency.py`가 항목별로 검증한다
> (현재 49/49 일치. 지난 정리에서 유일하게 재현되지 않던 χ² 값도 2026-09-22 추가 파일로 해소, 아래 "재현성 범위" 참고).

---

## 1. 데이터는 세 계층이다 — 파일을 열기 전에 반드시 구분할 것

최종 보고서는 **해석 계층은 동결 스냅샷(7,350건)**, **점수·구획·보조지표는 라이브 코퍼스(10,020건)**를
쓰는 이원 구조다(`METHODOLOGY.md` 4절 "실루엣 게이트 거버넌스"). 같은 팬덤의 loyalty_score가 파일마다
다르게 보이는 것은 오류가 아니라 이 구조 때문이다.

| 계층 | 코퍼스 | 이 계층에서 나온 수치 | 저장소 파일 |
|---|---|---|---|
| **동결 스냅샷 v7-40** (해석 계층) | 7,350건 | LDA K=10 → M=5 메타요인(실루엣 0.267), 팬덤별 F1~F5 비중, 페르소나 4유형(글로벌투어형 43·현장상업형 31·원정소비형 17·집단동원형 9), KEY_FINDINGS 하이라이트 표의 loyalty/spillover(BTS 0.931/1.000, 임영웅 0.899/0.702, 리센느 0.444/0.304) | `data/v7_final/fandom_scores_v6.csv` (activity 합 = 7,350), `data/v7_final/fan_persona_v7.json`, `data/v7_final/persona_decision_space_v7.json`, `Persona_결정공간.html` |
| **라이브 코퍼스 (최종)** | 10,020건 (14개 언어권) | 충성도·파급효과 점수(표본 평균 0.3710 / 0.2661), 4구획(핵심전략형 24·내부결속형 17·외부견인형 10·주변부 49), 상관·회귀·Cook's D 등 강건성 통계, 보조지표 7종, 언어·도메인 표, 3D 포지셔닝 맵, 게이트에 기각된 라이브 재적합(K=8, M=5, 실루엣 0.046) | `data/v7_final/fandoms_v3_100.json` (**근거문장 원본 10,020건**), `chart3d_payload_live_reference_v7.json`, `fandom_scores_live_reference_v7.csv`, `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`, `member_mention_index_v7.json`, `bullets_flat_v7_final.csv`, `3D_포지셔닝맵_국내100팬덤.html` |
| **v6 r22 스냅샷** (과거 시점) | 5,612건 | K=8, M=6, 실루엣 0.154 — 최종 수치가 아니다. 파이프라인이 실제로 어떻게 동작했는지 보여주는 실물 증거이며, 각 파일럿 노트북(`*/…_pilot.ipynb`)의 입력 | `data/v6_r22_snapshot/` 전체 |

`fandom_scores_v6.csv`, `run_lda_v6.py` 등 이름의 **"v6"은 파이프라인 버전명**이지 데이터 시점이 아니다.
`data/v7_final/fandom_scores_v6.csv`(7,350건 동결 스냅샷 산출)와 `data/v6_r22_snapshot/fandom_scores_v6.csv`
(5,612건 r22 산출)는 이름만 같은 다른 파일이다.

## 2. 보고서 수치 ↔ 저장소 파일 대응 (verify_v7_final_consistency.py 결과)

| 보고서·KEY_FINDINGS 수치 | 근거 파일 | 검증 결과 |
|---|---|---|
| 팬덤 100개, 근거문장 10,020건 | `data/v7_final/fandoms_v3_100.json` | 일치 |
| 14개 언어권, 한국어 5,551(55.4%)·영어 2,195(21.9%)·일본어 520(5.2%)·중국어 458(4.6%) | `language_domain_summary_v7.json` (14개 언어 합 = 10,020) | 일치 |
| "704개 도메인" | 같은 파일의 **한국어권 도메인 수**(보고서 표 2-2 한국어 행). 14개 언어권 도메인 수 합은 1,149개, 코퍼스 URL 고유 호스트는 1,315개 | 일치(의미 명확화) |
| loyalty/spillover 100개 팬덤 점수, 평균 0.3710/0.2661, 4구획 24/17/10/49 | `fandoms_v3_100.json`에 `METHODOLOGY.md` 2-4절 EvidenceScore 산식을 그대로 적용 → `chart3d_payload_live_reference_v7.json`과 100/100 일치 | 일치 |
| Pearson 0.493·Spearman 0.380·Cook's D(BTS 0.5749, god 0.284, 이효리 0.2538)·R² 0.243→0.847·VIF 1.93·민감도·LOO·3D축 독립성(r 0.099/0.461, R² 0.234, VIF 1.321) | 라이브 점수(`chart3d_payload_live_reference_v7.json`) | 전부 일치 |
| K=10, M=5, 실루엣 0.267, 페르소나 43/31/17/9, 토픽→F 배정 | `fan_persona_v7.json`, `persona_decision_space_v7.json`, `fandom_scores_v6.csv` | 일치 |
| 라이브 재적합 K=8/M=5/실루엣 0.046 (게이트 기각) | `lda_v6_diagnostics_live_reference_v7.json` = 3D 맵 payload 값 | 일치 |
| 4분면 독립성 χ²=8.34, p=0.0039 (라이브) / χ²=10.2273, p=0.0014 (동결) | `positioning_map_correlation_live_v7.json`의 분할표 [[7,17],[4,72]] — 표본 평균 4구획이 아니라 **점수 0.5 초과 여부** 2×2표. 동결 CSV에 같은 0.5 기준을 적용하면 [[8,17],[4,71]] → 10.2273 | 일치 (2026-09-22 추가 파일로 해소) |
| K=10 토픽 명칭·대표 불릿·대표 팬덤 | `topic_cards_v7.json` (METHODOLOGY.md 2-1 표와 명칭 10/10 일치) | 일치 |
| MCI ↔ 충성도 r=-0.393 (45개 그룹) | `member_pilot_mci_correlation_v7.json` (MCI는 v7-55 시점 8,981건 기준). 저장소의 10,020건 MCI로 재계산하면 r=-0.385 | 근사 일치 |

## 3. 재현성 범위 — 정직하게

- **재현되는 것**: 위 표의 "일치" 항목 전부. 특히 충성도·파급효과 점수는 LDA와 무관한 원문 규칙 산식이라
  `fandoms_v3_100.json`만 있으면 소수점 셋째 자리까지 그대로 나온다.
- **χ²=8.34, p=0.0039 (라이브) / χ²=10.2273, p=0.0014 (동결)**: 2026-09-22에 추가된
  `positioning_map_correlation_live_v7.json`으로 재현이 확인됐다. 단, 이 검정의 분할표는 보고서 그림의 4구획
  (표본 평균 기준 24/17/10/49)이 아니라 **loyalty·spillover 각각 0.5 초과 여부**로 나눈 2×2표([[7,17],[4,72]])다.
  같은 0.5 기준을 동결 CSV에 적용하면 [[8,17],[4,71]]로 10.2273이 나온다. 즉 "4분면 독립성 검정"의 4분면과
  포지셔닝 맵의 4구획은 기준선이 다르다(평균 기준 24/17/10/49 표로 계산하면 χ²=16.84). 이 사실을 문서에 명시했다.
- **K=10 토픽 명칭**: `METHODOLOGY.md` 2-1 표의 명칭(출처: `topic_cards_v7.json`, 10/10 일치. 예: K1 동남아현지보도형)과
  `Persona_결정공간.html`에 내장된 명칭(예: K1 해외현지보도형)은 상위 4개 키워드가 일부 다르다. 둘 다 같은 7,350건 동결 스냅샷의
  K=10 적합이고 **토픽→F코드 배정은 10/10 동일**하다(HTML은 "재적합, 재현성 검증 10/10 통과"본). 명칭은
  φ분포 상위 키워드 자동 조합이라 재적합 시 순서가 바뀔 수 있다.
- **LDA 재적합 자체**: 최종 라이브 재적합을 만든 `run_lda_v6_live_reference_v7.py`(14개 언어 문자권별
  토크나이저 라우팅 반영본)는 소스가 남아있지 않다. 저장소의 `run_lda_v6.py`는 v6~r22 시점 파이프라인이라
  10,020건에 돌리면 문서 수가 9,954건(구 토크나이저 3토큰 미만 제외)으로 보고서의 10,018건과 다르고
  K-grid 수치도 다르다. 이 스크립트는 로직 참고용이며 최종 진단값의 재현 수단이 아니다.
- **보조지표 7종의 원본 JSON**(`ad_commercial_index_v7.json`, `fandom_cohesion_index_v7.json`,
  `domestic_regional_index_live_reference_v7.json`, `worldwide_language_index_live_reference_v7.json`,
  `factor_clustering_structure_v7.json`, 실루엣 타임라인 CSV)은 아직 저장소에 없다. 해당 스크립트는
  `data/v7_final/` 아래 그 파일명을 읽도록 경로만 정리해 두었으므로, 파일을 넣으면 바로 실행된다.
  단 `member_mention_index_v7.json`(멤버 집중도 지수, 45개 그룹, 10,020건 기준)과 MCI 상관 분석
  (`member_pilot_mci_correlation_v7.json`, MCI는 v7-55 시점 8,981건 기준이라 10,020건 MCI와 값이 조금 다름)은 있다.

## 4. 폴더 구성

```
README.md / KEY_FINDINGS.md / METHODOLOGY.md / FINAL_REPORT_SUMMARY.md / PYTHON_CODE_SUMMARY.md
(분석보고서)…최종.pdf, (요약보고서)…최종.pdf         제출본
3D_포지셔닝맵_국내100팬덤.html + plotly-bundle.js    라이브 10,020건 3D 맵 (같은 폴더에서 열면 동작)
Persona_결정공간.html                                동결 스냅샷 K=10→M=5 덴드로그램·PCA·레이더
verify_v7_final_consistency.py                       최종 수치 ↔ 파일 정합성 검증 (49개 항목)
run_lda_v6.py                                        LDA 파이프라인(v6~r22 시점) — --data/--out 인자
data/
  v7_final/            최종 라이브 코퍼스 10,020건 + 최종 산출물 (1절 표 참고)
  v6_r22_snapshot/     v7 라운드22 스냅샷 5,612건 (+ v7_rounds/ 병합로그, csv/ 파생 CSV)
data_export/           코퍼스 평탄화·K-grid·라이브 점수 CSV·HTML 내장 데이터 추출 스크립트
charts/ indices_csv/   최종 보고서 그림·지수 CSV 스크립트 (입력 JSON은 data/v7_final/ 에서 읽음)
Silhoett Gate Policy/  실루엣 게이트 정책 문서 + 타임라인 차트 스크립트
TOKENIZER/, TOKENIZER_WORDCLOUD_REPORT/   토크나이저·언어 분류 문서와 스크립트·노트북
Ad_Commercial Pilot/ Fandom Cohesion Pilot/ Media Content Exposure Pilot/ Domestic Regional Pilot/
Worldwide Language Pilot/ Group_Member Pilot/ fan_impact_ontology/ 지표 산정 방법론/ 상세명세서/
                       각 보조지표·전략 문서와 r22 스냅샷 기반 병행 분석 노트북
reports/, 보고서 스크립트 작성/   요약보고서 docx 빌드 스크립트(Node.js, 동일 파일 2부)
kpop-fandom-project.tar.gz        초기 저장소 구조(scripts/docs/data) 원본 아카이브
```

## 5. 재현 절차

```bash
pip install numpy scipy statsmodels scikit-learn pandas matplotlib

# 1) 최종 수치 정합성 검증 — 보고서 수치가 data/v7_final/ 파일에서 재계산되는지 항목별 확인
python verify_v7_final_consistency.py

# 2) 파생 파일 재생성 (이미 커밋되어 있음; 다시 만들면 같은 결과)
python data_export/extract_html_payloads.py      # HTML 2종 내장 데이터 -> data/v7_final/*.json
python data_export/build_bullets_flat_csv.py     # fandoms_v3_100.json -> bullets_flat_v7_final.csv (10,020행)
python data_export/build_lda_k_grid_csv.py       # 라이브 재적합 k_grid -> lda_k_grid_live_reference_v7.csv
python data_export/build_live_scores_csv.py      # 3D 맵 payload -> fandom_scores_live_reference_v7.csv
#   r22 스냅샷에도 동일 스크립트 사용 가능:
python data_export/build_bullets_flat_csv.py --src data/v6_r22_snapshot/fandoms_v3_100.json \
       --out data/v6_r22_snapshot/csv/bullets_flat_v6_r22.csv --expected 5612

# 3) LDA 파이프라인(v6~r22 로직) — 기본값은 r22 스냅샷, 결과는 output/ 아래(원본 산출물을 덮지 않음)
python run_lda_v6.py                                     # data/v6_r22_snapshot -> output/lda_rerun/
python run_lda_v6.py --data data/v7_final/fandoms_v3_100.json --out output/lda_rerun_v7_final
```

한글 폰트가 필요한 차트 스크립트는 `KFONT_PATH=/path/to/NotoSansCJKkr-Regular.otf`를 지정하거나
`fonts/NotoSansCJKkr-Regular.otf`에 두면 된다(없으면 경고 후 기본 폰트로 진행).

## 6. 문서 안내

- `KEY_FINDINGS.md` — 보고서 인용 수치 요약 + 각 수치의 근거 파일·계층
- `METHODOLOGY.md` — 데이터 수집, K→M→Persona→Impact 4단계, 강건성 검증, 실루엣 게이트, 보조지표, DID
- `FINAL_REPORT_SUMMARY.md` — 분석보고서 20페이지 챕터 요약
- `PYTHON_CODE_SUMMARY.md` — 저장소 파이썬 스크립트 총정리(입력·출력·경로)
- 각 폴더의 `*_PILOT.md`, `*_STRATEGY.md`, `*_SPECIFICATION.md` — 문서 상단의 "2026-09-21 갱신 주"가
  10,020건 코퍼스 추가 이후 달라진 점을 밝힌다. 본문 중 "이번 세션에 없다/재현 불가"라는 서술은
  r22 스냅샷만 있던 시점의 기록이다.
