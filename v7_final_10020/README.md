# v7_final_10020 — 최종 근거 코퍼스 10,020건 기준 문서·코드·노트북

최종 근거 코퍼스(라이브 10,020건)와 그로부터 동결된 해석 계층(v7-40 스냅샷 7,350건)을 기준으로 집계된 **모든 MD·파이썬 코드·노트북**을
이 폴더 하나에 둔다. 데이터 파일은 `data/v7_final/`·`data/v7_rounds/`에 있고, 루트에는 README·제출 PDF·HTML 2종·`verify_v7_final_consistency.py`·`run_lda_v6.py`만 둔다.

| 하위 폴더 | 내용 |
|---|---|
| `docs/` | `KEY_FINDINGS.md`(인용 수치·근거 파일), `METHODOLOGY.md`(방법론), `FINAL_REPORT_SUMMARY.md`(보고서 요약), `PYTHON_CODE_SUMMARY.md`(코드 총정리) |
| `analysis/` | 보조지표 7종·Fan Impact Pathway·토크나이저 라우팅 **노트북 8개(실행 결과 포함) + 문서**, `Persona_결정공간.html` 로직 재현 노트북(`persona_decision_space/`), `build_notebooks_v7.py` 생성기, 토크나이저 스크립트 3종·토큰 빈도 CSV, 최종 기술 상세명세서, 국내 지역 지수 JSON/CSV |
| `charts/` | 최종 보고서 그림 스크립트(팬덤결속 지수 2종, 페르소나 덴드로그램·PCA) |
| `indices_csv/` | 지수 CSV 산출(광고·상업성, 국내 지역, 세계 언어) |
| `data_export/` | HTML 내장 데이터 추출, 코퍼스 평탄화, K-grid·결속/크로스오버 CSV, 성장 이력 CSV |
| `silhouette_gate_policy/` | 실루엣 게이트 정책 문서 + 타임라인 차트 스크립트 |
| `tokenizer_wordcloud_report/` | 토크나이저·워드클라우드 보고서(10,020건 실행 결과) + 이미지 |
| `index_methodology/` | 지표 산식 문서 + 식(1)∼(7)로 지표를 직접 산정하는 노트북(`index_calculation_v7.ipynb` + Spyder용 `.py`, 결과 CSV) + 식(2)(3)(6)(7) 재검증 스크립트 |
| `report_scripts/` | 요약보고서 docx 빌드 스크립트(Node.js) + JS 정리 문서 |

## 경로 규칙

- 모든 파이썬 스크립트는 `Path(__file__).resolve().parents[N]`으로 저장소 루트를 찾아 `data/v7_final/`을 읽고 `output/` 아래에 쓴다(원본 데이터를 덮지 않음).
  `analysis/` 노트북은 `data/v7_final/fandoms_v3_100.json`이 있는 상위 폴더를 루트로 잡으므로 어느 위치에서 실행해도 된다.
- 문서 안의 경로는 전부 저장소 루트 기준(`v7_final_10020/…`, `data/v7_final/…`)이다.

## 실행 (저장소 루트에서)

```bash
python verify_v7_final_consistency.py                                        # 보고서 수치 ↔ data/v7_final 정합성 (101/101)
python v7_final_10020/analysis/build_notebooks_v7.py                          # 노트북 8개 생성+실행
python v7_final_10020/indices_csv/build_ad_commercial_index_csv.py            # -> output/indices_csv/
python v7_final_10020/data_export/build_corpus_growth_history_csv.py          # -> data/v7_final/corpus_growth_history_v6_v7_full.csv (동일 결과)
python v7_final_10020/index_methodology/verify_index_calculation_formulas.py  # 식(2)(3)(6)(7) 0/100 불일치
python v7_final_10020/index_methodology/build_index_calculation_notebook.py    # 지표 산정 노트북 생성+실행
python v7_final_10020/silhouette_gate_policy/build_silhouette_gate_timeline_v7.py
python v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py   # fugashi·jieba·pythainlp 필요
```
