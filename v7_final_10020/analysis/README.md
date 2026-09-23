# v7_final_10020/analysis — 최종 코퍼스(10,020건) 기준 분석 노트북·문서·코드

최종 데이터(`data/v7_final/`: 라이브 10,020건 + 동결 스냅샷 7,350건, `data/v7_rounds/`: 병합 로그)를 입력으로 보조지표 7종·해석 계층·토크나이저를
재검증하는 노트북과 문서·코드다. 노트북은 `build_notebooks_v7.py`가 nbformat으로 생성한 뒤 nbconvert로 실행해 출력을 포함한 상태로 커밋했다.

| 폴더 | 내용 |
|---|---|
| `ad_commercial_index/` | `AD_COMMERCIAL_INDEX_V7.md` + `ad_commercial_index_v7.ipynb` — 원본 지수 무결성, 키워드 재매칭(96/100), LDA 대조 |
| `fandom_cohesion_index/` | `FANDOM_COHESION_INDEX_V7.md` + `fandom_cohesion_index_v7.ipynb` |
| `media_content_exposure_index/` | `MEDIA_CONTENT_EXPOSURE_V7.md` + `media_content_exposure_v7.ipynb` — 노출·크로스오버 지수, r10·r11 교차검증, K=9 |
| `domestic_regional_index/` | `DOMESTIC_REGIONAL_INDEX_V7.md` + `domestic_regional_index_v7.ipynb` + **`domestic_regional_index_v7.json/.csv`(최종 10,020건 산출본)**. `REGIONAL_MENTION_TYPES_V7.md` + `build_regional_mention_types_v7.py` — 동음 지명 감사·연고/활동 분리·엄격 지수 |
| `worldwide_language_index/` | `WORLDWIDE_LANGUAGE_INDEX_V7.md` + `worldwide_language_index_v7.ipynb` — 14개 언어·ln(14). `BODY_LANGUAGE_V7.md` + `build_body_language_classifier_v7.py` — 불릿 10,020건 본문 언어 병행 판정(문자권 + wordfreq), 도메인 기준과 불일치율·지수 상관 |
| `group_member_index/` | `GROUP_MEMBER_INDEX_V7.md` + `group_member_index_v7.ipynb` — 45개 그룹 MCI, 상관 재현. `MCI_SAME_PERIOD_V7.md` + `build_mci_same_period_v7.py` — 같은 시점(라이브×라이브) 상관 재산출, 지표 통일 CSV(MCI_excess·HHI_norm), 별칭·동음 감사 CSV |
| `fan_impact_pathway/` | `FAN_IMPACT_PATHWAY_V7.md` + `fan_impact_pathway_v7.ipynb` — 동결 K=10/M=5 해석 계층 재현 |
| `persona_decision_space/` | `persona_decision_space_v7.ipynb`(+ Spyder용 `.py`) — `Persona_결정공간.html`의 로직 재현: K→F 배정 10/10, 덴드로그램 절단·군집·잎 순서·가지 색, 상위 2 F → 페르소나 100/100(43/31/17/9), PCA 좌표·loading, 레이더 평균, Factor-specific 500/500. 결과 CSV·그림 3장. 하위 `topic_phi_cosine/`: 최종 코퍼스 10,020건에 K=10·K=8 LDA를 적합해 산출한 φ(토픽×어휘)·토픽 간 코사인 거리 행렬·average-linkage 병합 기록·M-grid 실루엣 CSV + 방법·코드 MD |
| `persona_decision_space/live_interpretive_layer/` | `LIVE_INTERPRETIVE_LAYER_V7.md` + `../build_live_interpretive_layer_v7.py` — 게이트 v2 통과 모델(라이브 K=8 참고 재적합)의 상위 15·K→F·페르소나를 동결과 같은 규칙으로 만들어 대조한 병행 트랙(채택 전까지 본문 미변경) |
| `tokenizer/` | 스크립트 3종(`*_v7.py`), 문서 2종(`*_V7.md`), `tokenizer_script_routing_v7.ipynb`, `csv/bullet_token_frequency_v7_final.csv`(43,162 토큰), `stopwords/`(언어별 불용어 MD·CSV + 코드에서 추출하는 스크립트) |
| `dictionaries/` | `export_index_dictionaries_v7.py` + `index_dictionaries_v7.csv`(436행) + `DICTIONARIES_V7.md` — 보조지표·Coverage 계산에 쓰인 키워드·도메인·별칭 사전을 코드/JSON에서 추출해 한 파일로 고정(`--check`로 코드↔CSV drift 검사), 저장소에 없는 사전 2종(업종 키워드 전체·결속 유형 키워드)은 '없음' 표기 |
| `unmatched_audit/` | `UNMATCHED_AUDIT_V7.md` + `near_miss_stats_v7.json` + 지표별 미매칭 표본 200건 CSV(검수 열 공란) — 광고·미디어·지역 지수의 매칭을 재현해 사전 밖 유사 표현이 든 미매칭 불릿을 세고 사람 검수 표본을 둔다(`../build_unmatched_audit_samples_v7.py`, `--summarize`로 검수 집계) |
| `technical_specification/` | `LDA_V7_FINAL_TECHNICAL_SPECIFICATION.md` — 최종 제출본 기준 방법론·수치·근거 파일 |

## 실행

```bash
pip install nbformat nbconvert ipykernel pandas numpy scipy          # 노트북
pip install fugashi unidic-lite jieba pythainlp                       # tokenizer/ 스크립트 (jieba·unidic-lite는 sdist 수동 설치가 필요할 수 있음)
python v7_final_10020/analysis/build_notebooks_v7.py                        # 8개 노트북 생성+실행 (약 2~3분)
python v7_final_10020/analysis/build_notebooks_v7.py domestic --no-exec     # 특정 노트북만 생성
```

노트북은 저장소 어느 위치에서 실행해도 되도록 `data/v7_final/fandoms_v3_100.json`을 찾아 저장소 루트를 결정한다.

## 이 폴더가 새로 확정한 것

- 국내 지역 지수 키워드 규칙을 최종 10,020건에 적용한 JSON/CSV를 산출했다. 보고서 표 15의 국내 지역 값은 동결 스냅샷(7,350건) 시점임을 확인했다(동결 근사 코퍼스로 20행 중 17행 재현).
- 광고 지수의 31개 광고신호 키워드 + 부정 가드를 코퍼스에 재적용하면 팬덤별 96/100 정확 일치.
- 세 시점 언어 커버리지 분모(ln 10 / ln 13 / ln 14)와 언어 구성표, 45개 그룹 MCI와 상관 재현, 페르소나 43/31/17/9·Factor-specific Impact 500셀 재현.
- 최종 코퍼스 10,020건은 전부 URL을 가지며 URL 필드 오염(도구 문구 혼입)이 없다.
