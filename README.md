# 국내 대표 팬덤 100개 LDA 토픽모델링 — 팬충성도 × 파급효과 분석 저장소

"국내 100대 팬덤 충성도×파급효과 유형 분석: LDA 토픽 모델링"의 데이터·코드·문서를 모아둔 저장소다.
제출본 PDF 2종(`(분석보고서)…최종.pdf`, `(요약보고서)…최종.pdf`)이 루트에 있으며, 저장소의 모든 수치는
이 PDF의 수치를 기준으로 정합성을 맞췄다.

> 분석은 **최종 근거 코퍼스 10,020건**(`data/v7_final/fandoms_v3_100.json`, 100개 팬덤, 14개 언어권)과 그로부터 동결된
> 해석 계층 스냅샷(v7-40, 7,350건)을 기준으로 한다. 최종 수치가 저장소 파일에서 실제로 재현되는지는
> `verify_v7_final_consistency.py`가 항목별로 검증한다(101/101 일치, 아래 "재현성 범위" 참고).

---

## 1. 데이터는 두 계층이다 — 파일을 열기 전에 반드시 구분할 것

최종 보고서는 **해석 계층은 동결 스냅샷(7,350건)**, **점수·구획·보조지표는 라이브 코퍼스(10,020건)**를
쓰는 이원 구조다(`v7_final_10020/docs/METHODOLOGY.md` 4절 "실루엣 게이트 거버넌스"). 같은 팬덤의 loyalty_score가 파일마다
다르게 보이는 것은 오류가 아니라 이 구조 때문이다.

| 계층 | 코퍼스 | 이 계층에서 나온 수치 | 저장소 파일 |
|---|---|---|---|
| **동결 스냅샷 v7-40** (해석 계층) | 7,350건 | LDA K=10 → M=5 메타요인(실루엣 0.267), 팬덤별 F1∼F5 비중, 페르소나 4유형(글로벌투어형 43·현장상업형 31·원정소비형 17·집단동원형 9), KEY_FINDINGS 하이라이트 표의 loyalty/spillover(BTS 0.931/1.000, 임영웅 0.899/0.702, 리센느 0.444/0.304), 국내 지역 지수 표 15 | `data/v7_final/fandom_scores_v6.csv` / `.json` (activity 합 = 7,350; JSON에 raw 점수·coverage_detail), `fan_persona_v7.json`, `topic_cards_v7.json`, `lda_v6_diagnostics_frozen_v7_40.json`, `persona_decision_space_v7.json`, `Persona_결정공간.html` |
| **라이브 코퍼스 (최종)** | 10,020건 (14개 언어권) | 충성도·파급효과 점수(표본 평균 0.3710 / 0.2661), 4구획(핵심전략형 24·내부결속형 17·외부견인형 10·주변부 49), 상관·회귀·Cook's D 등 강건성 통계, 보조지표 7종, 언어·도메인 표, 3D 포지셔닝 맵, 게이트에 기각된 라이브 재적합(K=8, M=5, 실루엣 0.046) | `data/v7_final/fandoms_v3_100.json` (**근거문장 원본 10,020건**), `fandom_scores_live_reference_v7.csv/.json`(라이브 재적합 F 비중 포함), `chart3d_payload_live_reference_v7.json`, 지수 JSON 7종, `lda_excluded_bullets_v7.json`, `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`, `member_mention_index_v7.json`, `bullets_flat_v7_final.csv`, `3D_포지셔닝맵_국내100팬덤.html` |

**로스터 차이**: 동결 스냅샷의 100개 팬덤과 라이브 코퍼스의 100개 팬덤은 3개가 다르다(동결에만 한로로·pH-1·BE'O, 라이브에만
몬스타엑스·투어스(TWS)·빈지노 — v7 r58∼r63 로스터 교체). 페르소나·F1∼F5 비중은 동결 로스터, 점수·4구획·보조지표는 라이브 로스터 기준이다.

`fandom_scores_v6.csv`, `run_lda_v6.py` 등 이름의 **"v6"은 파이프라인 버전명**이지 데이터 시점이 아니다.

## 2. 보고서 수치 ↔ 저장소 파일 대응 (verify_v7_final_consistency.py 결과)

| 보고서·KEY_FINDINGS 수치 | 근거 파일 | 검증 결과 |
|---|---|---|
| 팬덤 100개, 근거문장 10,020건 / LDA 재적합 문서 10,018건 | `data/v7_final/fandoms_v3_100.json`; 10,018은 3토큰 미만 2건(ATEEZ 태국어 1건, 레드벨벳 '맥도날드 조이 (2026)') 제외 — `lda_excluded_bullets_v7.json` | 일치 |
| 14개 언어권, 한국어 5,551(55.4%)·영어 2,195(21.9%)·일본어 520(5.2%)·중국어 458(4.6%) | `language_domain_summary_v7.json` (14개 언어 합 = 10,020) | 일치 |
| "704개 도메인" | 같은 파일의 **한국어권 도메인 수**(보고서 표 2-2 한국어 행). 14개 언어권 도메인 수 합은 1,149개, 코퍼스 URL 고유 호스트는 1,315개 | 일치(의미 명확화) |
| loyalty/spillover 100개 팬덤 점수, 평균 0.3710/0.2661, 4구획 24/17/10/49 | `fandoms_v3_100.json`에 `v7_final_10020/docs/METHODOLOGY.md` 2-4절 EvidenceScore 산식을 그대로 적용 → `chart3d_payload_live_reference_v7.json`과 100/100 일치 | 일치 |
| Pearson 0.493·Spearman 0.380·Cook's D(BTS 0.5749, god 0.284, 이효리 0.2538)·R² 0.243→0.847·VIF 1.93·민감도·LOO·3D축 독립성(r 0.099/0.461, R² 0.234, VIF 1.321) | 라이브 점수(`chart3d_payload_live_reference_v7.json`), `positioning_map_correlation_live_v7.json`, `chart3d_correlation_live_v7.json` | 전부 일치 |
| K=10, M=5, 실루엣 0.267, 페르소나 43/31/17/9, 토픽→F 배정 | `lda_v6_diagnostics_frozen_v7_40.json`(K-grid에서 K=10 rank_sum 8 < K=8 9), `fan_persona_v7.json`, `persona_decision_space_v7.json`, `fandom_scores_v6.csv` | 일치 |
| 동결 스냅샷 점수 JSON: min-max 정규화·F 다양성·coverage 가중합 재현, 언어 커버리지 분모 ln(13) | `fandom_scores_v6.json` (동결 7,350건 언어 분포 ko 4,183·en 1,751·ja 333 … 아랍어 없음) | 일치 |
| 세계 언어 지수: BTS 해외 근거 135건(60%), 해외언어다양성 0.66; 14개 언어 합 = 언어 표 | `worldwide_language_pilot_live_reference_v7.json` → `worldwide_language_index_v7.csv` (스크립트 재실행, 불일치 0) | 일치 |
| 라이브 점수 원본 JSON의 raw 점수·coverage_index 5요소 가중합·언어 엔트로피 ln(14) | `fandom_scores_live_reference_v7.json` | 일치 |
| 토크나이저 출력 토큰 170,725개, 문자권별 불릿 수(한국어 8,942 …) | `wordcloud_by_language_v7.json` | 일치 |
| r45(1차) K=12, M=2, 실루엣 0.136 | `_explore_r45_meta_factor.json` (코사인거리 행렬로 M 2∼11 실루엣 전부 재현) | 일치 |
| 미디어·콘텐츠 노출 1,025건(10.2%), 서브태그 예능·유튜브·영화·드라마 | `media_exposure_v7.json` (팬덤별·서브태그별 합 전부 일치) | 일치 |
| 매체 크로스오버 6,712건(67.0%), 고유 매체 1,298개 | `media_crossover_index_v7.json` | 일치 |
| 코퍼스 성장 이력: v6 2,403건 → v7 r72 10,020건, 로스터 교체 6건 | `data/v7_rounds/` 병합·교체 로그 전량 → `corpus_growth_history_v6_v7_full.csv` (타임라인 CSV와 56건 일치) | 일치 |
| 라이브 재적합 K=8/M=5/실루엣 0.046 (게이트 기각) | `lda_v6_diagnostics_live_reference_v7.json` = 3D 맵 payload 값 | 일치 |
| 4분면 독립성 χ²=8.34, p=0.0039 (라이브) / χ²=10.2273, p=0.0014 (동결) | `positioning_map_correlation_live_v7.json`의 분할표 [[7,17],[4,72]] — 표본 평균 4구획이 아니라 **점수 0.5 초과 여부** 2×2표. 동결 CSV에 같은 0.5 기준을 적용하면 [[8,17],[4,71]] → 10.2273 | 일치 |
| K=10 토픽 명칭·대표 불릿·대표 팬덤 | `topic_cards_v7.json` (METHODOLOGY 2-1 표와 명칭 10/10 일치) | 일치 |
| 광고·상업성 1,302건(13.0%) / 팬덤결속 923건(9.2%), 하이라이트 결속 15·18·30건 | `ad_commercial_index_v7.json`, `fandom_cohesion_index_v7.json` (팬덤별 합·업종/유형별 합 전부 원본 집계와 일치) | 일치 |
| 국내 지역 지수 표 15(BTS 17건·서울 47%·다양성 0.29, 임영웅 28건·12지역·0.71 전체 1위) | 키워드 규칙을 10,020건에 적용한 `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json`; 표 15는 동결 시점 값(동결 코퍼스 근사로 20행 중 17행 재현) | 일치 |
| 동결 기준선 0.267 이후 실측 재적합 전부 기각 | `data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv` (v4 종료∼r66 2차, 실측 지점 전부 < 0.267), 최종 r77 0.046 | 일치 |
| MCI ↔ 충성도 r=-0.393 (45개 그룹) | `member_pilot_mci_correlation_v7.json` (MCI는 v7-55 시점 8,981건 기준). 최종 10,020건 MCI로 재계산하면 r=-0.385(상세 보고서 7.4절 값) | 일치 |

## 3. 재현성 범위 — 정직하게

- **재현되는 것**: 위 표의 "일치" 항목 전부. 특히 충성도·파급효과 점수는 LDA와 무관한 원문 규칙 산식이라
  `fandoms_v3_100.json`만 있으면 소수점 셋째 자리까지 그대로 나온다.
- **χ² 검정의 분할표**: 보고서 그림의 4구획(표본 평균 기준 24/17/10/49)이 아니라 **loyalty·spillover 각각 0.5 초과 여부**로 나눈
  2×2표([[7,17],[4,72]])다. 같은 0.5 기준을 동결 CSV에 적용하면 [[8,17],[4,71]]로 10.2273이 나온다. 즉 "4분면 독립성 검정"의 4분면과
  포지셔닝 맵의 4구획은 기준선이 다르다(평균 기준 표로 계산하면 χ²=16.84).
- **K=10 토픽 명칭**: METHODOLOGY 2-1 표의 명칭(출처: `topic_cards_v7.json`, 예: K1 동남아현지보도형)과 `Persona_결정공간.html`에
  내장된 명칭(예: K1 해외현지보도형)은 상위 4개 키워드가 일부 다르다. 둘 다 같은 7,350건 동결 스냅샷의 K=10 적합이고
  **토픽→F코드 배정은 10/10 동일**하다. 명칭은 φ분포 상위 키워드 자동 조합이라 재적합 시 순서가 바뀔 수 있다.
- **LDA 재적합 자체**: 최종 라이브 재적합을 만든 `run_lda_v6_live_reference_v7.py`(14개 언어 문자권별 토크나이저 라우팅 반영본)는
  저장소에 없다. `run_lda_v6.py`는 그 이전 판 토크나이저의 파이프라인이라 10,020건에 돌리면 문서 수가 9,954건으로 보고서의
  10,018건과 다르고 K-grid 수치도 다르다. 로직 참고용이며 최종 진단값의 재현 수단이 아니다.
- **저장소에 없는 최종 산출물**: 국내 지역 지수 라이브 JSON(대신 규칙을 재적용한 산출본이 `v7_final_10020/analysis/domestic_regional_index/`에 있음),
  `factor_clustering_structure_v7.json`(K→M 코사인거리 행렬 — 페르소나 덴드로그램 차트 스크립트 입력), `chart3d_correlation_v7.json`(3D 축 검증의 동결판),
  v7-55 시점 MCI 파일, `supplementary_csv/팬덤100_언어비중.csv`. 원본 데이터 아카이브의 파일 전량 목록은 `data/v7_final/ARCHIVE_README_original.md`.
- **광고 지수 키워드**: `ad_commercial_index_v7.json`의 광고신호 키워드는 31개다(보고서 본문의 "24개"는 신설 당시 수).

## 4. 폴더 구성

루트에는 README·제출 PDF·HTML 2종·검증/파이프라인 스크립트 2개와 `data/`만 두고, **10,020건·동결 스냅샷 기준으로
집계된 모든 MD·코드·노트북은 `v7_final_10020/`** 한 폴더에 둔다.

```
README.md                                            이 문서
(분석보고서)…최종.pdf, (요약보고서)…최종.pdf         제출본
3D_포지셔닝맵_국내100팬덤.html + plotly-bundle.js    라이브 10,020건 3D 맵 (같은 폴더에서 열면 동작)
Persona_결정공간.html                                동결 스냅샷 K=10→M=5 덴드로그램·PCA·레이더
qr_codes/                                            위 HTML 2종의 QR 코드 이미지 + 아티팩트 링크·해시 대조 (폴더 README)
verify_v7_final_consistency.py                       최종 수치 ↔ 파일 정합성 검증 (101/101)
run_lda_v6.py                                        LDA 파이프라인 참고 구현(--data/--out 인자; 기본 입력 = 최종 코퍼스)
data/
  v7_final/            최종 라이브 코퍼스 10,020건 + 최종 산출물 + 동결 스냅샷 산출물 (1절 표, 폴더 README 참고)
  v7_rounds/           v6 단계 로그 3개 + v7 병합·교체 로그 전량 r1~r74 (마지막 r72가 10,020건)
  silhouette_gate_timeline/  실루엣 게이트 타임라인 CSV (v4 종료~r66 2차)
v7_final_10020/        ★ 10,020건 기준 문서·코드·노트북 전부 (폴더 README 참고)
  docs/                  KEY_FINDINGS.md · METHODOLOGY.md · FINAL_REPORT_SUMMARY.md · PYTHON_CODE_SUMMARY.md · REPORT_DOCX_VERIFICATION.md
  analysis/              보조지표 7종·Fan Impact Pathway·토크나이저 라우팅 노트북 8개(실행 결과 포함)+문서, build_notebooks_v7.py,
                         토크나이저 스크립트 3종+문서 2종+토큰 빈도 CSV, 기술 상세명세서, 국내 지역 지수 JSON/CSV
  charts/  indices_csv/  최종 보고서 그림·지수 CSV 스크립트 (입력 JSON은 data/v7_final/, 출력은 output/)
  data_export/           HTML 내장 데이터 추출, 코퍼스 평탄화, K-grid·지수·성장 이력 CSV 산출 스크립트
  silhouette_gate_policy/     실루엣 게이트 정책 문서 + 타임라인 차트 스크립트
  tokenizer_wordcloud_report/ 토크나이저·워드클라우드 보고서(10,020건 실행 결과) + 이미지
  index_methodology/     지표 산식 문서 + 라이브 점수 JSON으로 식(2)(3)(6)(7) 재검증 스크립트
  report_scripts/        요약보고서 docx 빌드 스크립트(Node.js) + JS 정리 문서
archive/v6_r22_era_backup.zip   최종 코퍼스 확정 이전(v7 r22, 5,612건) 시점 자료의 압축 백업 — 저장소 본문은 참조하지 않음 (안의 NOTES_특이사항.md 참고)
```

## 5. 재현 절차

```bash
pip install numpy scipy statsmodels scikit-learn pandas matplotlib

# 1) 최종 수치 정합성 검증 — 보고서 수치가 data/v7_final/ 파일에서 재계산되는지 항목별 확인
python verify_v7_final_consistency.py

# 2) 파생 파일 재생성 (이미 커밋되어 있음; 다시 만들면 같은 결과)
python v7_final_10020/data_export/extract_html_payloads.py      # HTML 2종 내장 데이터 -> data/v7_final/*.json
python v7_final_10020/data_export/build_bullets_flat_csv.py     # fandoms_v3_100.json -> bullets_flat_v7_final.csv (10,020행)
python v7_final_10020/data_export/build_lda_k_grid_csv.py       # 라이브 재적합 k_grid -> lda_k_grid_live_reference_v7.csv
python v7_final_10020/data_export/build_cohesion_media_index_csv.py   # 팬덤결속·매체 크로스오버 지수 JSON -> CSV 2종
python v7_final_10020/indices_csv/build_ad_commercial_index_csv.py    # 광고·상업성 지수 JSON -> output/indices_csv/ad_commercial_index_v7.csv
python v7_final_10020/data_export/build_corpus_growth_history_csv.py  # data/v7_rounds 로그 -> corpus_growth_history_v6_v7_full.csv

# 2-1) 분석 노트북·토크나이저 스크립트 (v7_final_10020/analysis/, README 참고)
pip install nbformat nbconvert ipykernel && python v7_final_10020/analysis/build_notebooks_v7.py   # 노트북 8개 생성+실행
python v7_final_10020/analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py
python v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py                   # fugashi·jieba·pythainlp 필요

# 3) LDA 파이프라인 참고 실행 — 결과는 output/ 아래(원본 산출물을 덮지 않음)
python run_lda_v6.py                                     # data/v7_final/fandoms_v3_100.json -> output/lda_rerun/
```

한글 폰트가 필요한 차트 스크립트는 `KFONT_PATH=/path/to/NotoSansCJKkr-Regular.otf`를 지정하거나
`fonts/NotoSansCJKkr-Regular.otf`에 두면 된다(없으면 경고 후 기본 폰트로 진행).

## 6. 문서 안내

- `v7_final_10020/docs/KEY_FINDINGS.md` — 보고서 인용 수치 요약 + 각 수치의 근거 파일·계층
- `v7_final_10020/docs/METHODOLOGY.md` — 데이터 수집, K→M→Persona→Impact 4단계, 강건성 검증, 실루엣 게이트, 보조지표, DID
- `v7_final_10020/docs/FINAL_REPORT_SUMMARY.md` — 분석보고서 챕터 요약
- `v7_final_10020/docs/PYTHON_CODE_SUMMARY.md` — 파이썬 스크립트 총정리(입력·출력·경로)
- `v7_final_10020/docs/REPORT_DOCX_VERIFICATION.md` — 보고서 docx 2종의 표·수치를 저장소 데이터와 대조한 기록
- `data/v7_final/README.md`, `data/v7_rounds/README.md` — 데이터 파일별 계층·내용
- `v7_final_10020/analysis/README.md` — 분석 노트북·문서·코드, `technical_specification/LDA_V7_FINAL_TECHNICAL_SPECIFICATION.md`가 상세명세서
