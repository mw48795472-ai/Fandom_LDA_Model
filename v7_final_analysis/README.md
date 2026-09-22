# v7_final_analysis — 최종 코퍼스(10,020건) 기준 분석 노트북·문서·코드

`archive/v6_r22_era/`에 보관된 r22(5,612건) 시점 자료를 **최종 데이터 기준으로 새로 구성**한 폴더다(2026-09-22).
아카이브 파일은 한 줄도 수정하지 않았고, 모든 입력은 `data/v7_final/`(라이브 10,020건 + 동결 스냅샷 7,350건)과 `data/v7_rounds/`이며,
아카이브 데이터는 비교 목적으로만 읽는다. 노트북은 `build_notebooks_v7.py`가 nbformat으로 생성한 뒤 nbconvert로 실행해 출력을 포함한 상태로 커밋했다.

| 폴더 | 아카이브 대응 | 내용 |
|---|---|---|
| `ad_commercial_index/` | Ad_Commercial Pilot | `AD_COMMERCIAL_INDEX_V7.md` + `ad_commercial_index_v7.ipynb` — 원본 지수 무결성, 키워드 재매칭(96/100), LDA 대조 |
| `fandom_cohesion_index/` | Fandom Cohesion Pilot | `FANDOM_COHESION_INDEX_V7.md` + `fandom_cohesion_index_v7.ipynb` |
| `media_content_exposure_index/` | Media Content Exposure Pilot | `MEDIA_CONTENT_EXPOSURE_V7.md` + `media_content_exposure_v7.ipynb` — 노출·크로스오버 지수, r10·r11 교차검증, K=9 |
| `domestic_regional_index/` | Domestic Regional Pilot | `DOMESTIC_REGIONAL_INDEX_V7.md` + `domestic_regional_index_v7.ipynb` + **`domestic_regional_index_v7.json/.csv`(최종 재산출본)** |
| `worldwide_language_index/` | Worldwide Language Pilot | `WORLDWIDE_LANGUAGE_INDEX_V7.md` + `worldwide_language_index_v7.ipynb` — 14개 언어·ln(14) |
| `group_member_index/` | Group_Member Pilot | `GROUP_MEMBER_INDEX_V7.md` + `group_member_index_v7.ipynb` — 45개 그룹 MCI, 상관 재현 |
| `fan_impact_pathway/` | fan_impact_ontology | `FAN_IMPACT_PATHWAY_V7.md` + `fan_impact_pathway_v7.ipynb` — 동결 K=10/M=5 해석 계층 재현 |
| `tokenizer/` | TOKENIZER + TOKENIZER_WORDCLOUD_REPORT 노트북 | 스크립트 3종(`*_v7.py`), 문서 2종(`*_V7.md`), `tokenizer_script_routing_v7.ipynb`, `csv/bullet_token_frequency_v7_final.csv`(43,162 토큰) |
| `technical_specification/` | 상세명세서 | `LDA_V7_FINAL_TECHNICAL_SPECIFICATION.md` — 최종 제출본 기준 방법론·수치·근거 파일 |

## 실행

```bash
pip install nbformat nbconvert ipykernel pandas numpy scipy          # 노트북
pip install fugashi unidic-lite jieba pythainlp                       # tokenizer/ 스크립트 (jieba·unidic-lite는 sdist 수동 설치가 필요할 수 있음)
python v7_final_analysis/build_notebooks_v7.py                        # 8개 노트북 생성+실행 (약 2~3분)
python v7_final_analysis/build_notebooks_v7.py domestic --no-exec     # 특정 노트북만 생성
```

노트북은 저장소 어느 위치에서 실행해도 되도록 `data/v7_final/fandoms_v3_100.json`을 찾아 저장소 루트를 결정한다.

## 이 폴더가 새로 확정한 것

- 국내 지역 지수 규칙(키워드 사전)을 r22 원본 1,700셀 중 1,698셀 재현으로 확정하고, 최종 10,020건에 재적용한 JSON/CSV를 산출했다.
  보고서 표 15의 국내 지역 값은 동결 스냅샷(7,350건) 시점임을 확인했다(동결 근사 코퍼스로 20행 중 17행 재현).
- 광고 지수의 31개 광고신호 키워드 + 부정 가드를 코퍼스에 재적용하면 팬덤별 96/100 정확 일치.
- 세 시점 언어 커버리지 분모(ln 10 / ln 13 / ln 14)와 언어 구성표, 45개 그룹 MCI와 상관 재현, 페르소나 43/31/17/9·Factor-specific Impact 500셀 재현.
- 최종 코퍼스에는 r22에서 발견됐던 데이터 오염(Agent 핸드백 문구 5건, URL 없는 참고문구 64건)이 없다.
