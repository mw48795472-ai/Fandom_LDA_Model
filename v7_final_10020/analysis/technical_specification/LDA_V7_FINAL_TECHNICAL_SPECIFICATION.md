# 기술 상세명세서 — 최종 제출본 (동결 스냅샷 7,350건 + 라이브 코퍼스 10,020건)

> 최종 제출본의 방법론·수치·근거 파일을 절별로 적는다. 모든 수치는 `verify_v7_final_consistency.py`(96/96)와 `v7_final_10020/analysis/*/*.ipynb`에서 재계산된 값이다. 산식 원문은 `v7_final_10020/docs/METHODOLOGY.md`, `v7_final_10020/index_methodology/`.

**국내 대표 팬덤 100개 LDA 토픽모델링 — 팬충성도 × 파급효과 × 팬 요인 다양성**
Meta Factor / Fan Factor Matrix / Coverage Index / 보조지표 7종 / 실루엣 게이트

## 0. 이 문서의 위치 — 세 계층

| 계층 | 코퍼스 | 결정된 것 | 근거 파일(`data/v7_final/`) |
|---|---|---|---|
| 해석 계층 | **동결 스냅샷 v7-40, 7,350건** (r39 병합 후) | K=10 → M=5, 실루엣 0.267, F1∼F5, 페르소나 4유형, Topic Card | `lda_v6_diagnostics_frozen_v7_40.json`, `fandom_scores_v6.json/.csv`, `fan_persona_v7.json`, `topic_cards_v7.json`, `factor_pathway_map_v7.json`, `persona_decision_space_v7.json` |
| 점수 계층 | **라이브 10,020건** (r72) | loyalty/spillover 점수, 4구획, 상관·회귀·강건성, 보조지표 7종 | `fandoms_v3_100.json`, `fandom_scores_live_reference_v7.*`, `chart3d_payload_live_reference_v7.json`, `positioning_map_correlation_live_v7.json`, `chart3d_correlation_live_v7.json`, 지수 JSON 7종 |
| 라이브 재적합(기각) | 10,020건 (LDA 문서 10,018) | K=8/M=5/실루엣 0.046 — 게이트 미통과 | `lda_v6_diagnostics_live_reference_v7.json`, `lda_excluded_bullets_v7.json`, `lda_k_grid_live_reference_v7.csv` |

## 1. 배경 및 목적

전략 문서(LDA v4 → v5 FPU, Fan Impact Pathway)의 제안 중 실제로 구현된 것은 Topic → Meta Factor 계층 압축, Fan Factor Matrix·Factor Diversity, Coverage Index 5요소,
K→F 영향경로·페르소나, 그룹–멤버 텍스트마이닝 지수, 그리고 LDA와 독립인 키워드/도메인 보조지표 7종이다. 미구현 항목은 8절.

## 2. 데이터 및 코퍼스

- 대상: 국내 대표 팬덤 100개(K-pop 걸그룹 23 · 보이그룹 18 · 솔로 17 · 발라드 16 · 트로트 10 · 힙합 7 · 원로그룹 3 · 보이그룹/록 3 · 록 2 · 혼성 1).
- 근거문장: loyalty(팬 충성도) / spillover(파급효과) 두 태그, 각 문장은 원문 `t`와 출처 URL `u`. 최종 **10,020건**(100% URL 보유), LDA 문서 10,018건(3토큰 미만 2건 제외).
- 성장 이력(`data/v7_rounds/` 병합 로그 60개 + 스왑 로그 4개 → `corpus_growth_history_v6_v7_full.csv`): v3 1,035 → v6 2,674 → v6.4 3,154 → **r39 7,350(동결)** → r59 9,042 → r66 9,680 → r68 아랍어·r69 프랑스어·r71 스페인어 보강 → **r72 10,020**. after_total이 실루엣 타임라인 CSV와 56건 전부 일치.
- 로스터: 동결과 라이브의 100개 팬덤은 3개가 다르다(동결 한로로·pH-1·BE'O ↔ 라이브 몬스타엑스·투어스(TWS)·빈지노; r58·r62·r63). r29·r34에서 사이먼도미닉→GOT7, 창모→김재중, 헤이즈→박서진.
- 언어권 14개(출처 도메인 기준): 한국어 5,551(55.4%) · 영어 2,195(21.9%) · 일본어 520 · 중국어 458 · 스페인어 250 · 인도네시아어 210 · 태국어 209 · 필리핀어 137 · 프랑스어 101 · 포르투갈어 89 · 베트남어 85 · 아랍어 73 · 러시아어 71 · 튀르키예어 71. 한국어권 도메인 704개, 코퍼스 고유 호스트 1,315개.
- 출처 유형: news_media / community_social / reference_wiki(`source_type_of()`); 뉴스 매체 불릿 6,712건(67.0%), 고유 매체 1,298개.
- 전처리: 일반 경로(정규식, 공백 구분 언어 전부) + 문자권별 추가 경로(가나 → fugashi, 가나 없는 한자 → jieba, 태국 문자 → pythainlp newmm), 영문 기능어·순수 숫자 토큰 제거.
  원본 실행 결과 `wordcloud_by_language_v7.json`(토큰 170,725개; 문자권별 불릿 한국어 8,942 · 영어 6,425 · 중국어 398 · 비영어 219 · 일본어 155 · 태국어 56 · 러시아어 45 · 베트남어 30).
  최종 토크나이저 소스는 저장소에 없고, 병행 구현은 `v7_final_10020/analysis/tokenizer/`.

## 3. LDA 다중지표 K 선정 (동결 스냅샷 7,350건)

CountVectorizer(min_df=2, max_df=0.6), 후보 K={8,10,12,15,20,25,30}, 지표 4종(Perplexity↓, UMass Coherence↑, Topic Diversity↑, 3-seed Stability↑),
composite_rank_sum = rank_asc(perplexity) + rank_desc(coherence) + rank_desc(diversity) + rank_desc(stability).

| K | Perplexity | Coherence | Diversity | Stability | 종합순위합 |
|---|---:|---:|---:|---:|---:|
| 8 | 3046.2 | −2.398 | 0.900 | 0.420 | 9 |
| **10** | 3108.2 | −2.348 | 0.850 | 0.460 | **8** |
| 12 | 3134.4 | −2.361 | 0.842 | 0.371 | 14 |
| 15 | 3255.2 | −2.425 | 0.780 | 0.415 | 17 |
| 20 | 3423.6 | −2.312 | 0.750 | 0.352 | 19 |
| 25 | 3517.0 | −2.480 | 0.768 | 0.317 | 24 |
| 30 | 3636.8 | −2.245 | 0.767 | 0.288 | 21 |

K=10 채택. 라이브 10,020건 재적합에서는 K=8이 승자(5)이며 M=5 실루엣 0.046(4절 게이트). K=9 추가 검증(`k9_validation_v7.json`, 9,614문서): K=9를 넣어도 승자는 K=8, 미디어 토픽은 M≥6에서만 분리(실루엣 ≤0.081).

최종 토픽(Topic Card, `topic_cards_v7.json`):

| K | 명칭 | 상위어 | F |
|---|---|---|---|
| K0 | 음원차트기록형 | 기록·1위·발매·차트·데뷔·최초 | F5 |
| K1 | 동남아현지보도형 | 무대·보도·기사·인도네시아·매체 | F3 |
| K2 | 예능방송출연형 | 출연·예능·mbc·sbs·mc·kbs | F4 |
| K3 | 일본오리콘앨범형 | 앨범·1위·판매·일본·오리콘 | F5 |
| K4 | 글로벌음반판매형 | million·album·japan·chart·copies | F2 |
| K5 | 팬클럽공식기부형 | 공식·팬클럽·유튜브·채널·팬덤·기부 | F1 |
| K6 | 단독콘서트월드투어형 | 콘서트·공연·투어·단독 | F3 |
| K7 | 브랜드앰버서더형 | 브랜드·모델·광고·앰버서더·발탁 | F3 |
| K8 | 월드투어매진형 | tour·concert·fan·sold·world·seoul | F2 |
| K9 | 영화드라마출연형 | 드라마·ost·출연·예능·영화 | F4 |

## 4. Topic → Meta Factor 계층 압축과 실루엣 게이트

Phi(K×|V|) L2 정규화 → 코사인 거리 → AgglomerativeClustering(average) M∈{4..8} → 거리행렬 실루엣 최대 M 채택 → 라벨은 휴리스틱 키워드 규칙(자동).

| F | 영향경로(`factor_pathway_map_v7.json`) | raw 라벨(자동) | 구성 K |
|---|---|---|---|
| F1 | 팬덤결속 경로 (Fan → Fan) | 결속형(팬클럽·기부·커뮤니티) | K5 |
| F2 | 직접소비 경로 (Fan → Market) | 소비력형(초동·판매·앨범) | K4, K8 |
| F3 | 현장경제 경로 (Fan → Event → Local) | 현장경제형(콘서트·투어·매진) | K1, K6, K7 |
| F4 | 산업전이 경로 (Fan → Brand/Industry) | 미디어노출형(방송·조회수) | K2, K9 |
| F5 | 대중·글로벌 확산 경로 (Fan → Media → Mass/Global) | 차트·확산형(1위·빌보드·기록) | K0, K3 |

선정: **M=5, 실루엣 0.267**(동결). 덴드로그램 컷 높이 0.774.

**실루엣 게이트 거버넌스**: 동결 기준선 0.267 이후 라이브 재적합은 22개 실측 지점(`data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv`) 전부 0.267 미만(최대 0.148 r49, r64·r65 0.141, 최종 0.046) → 해석 계층은 동결 스냅샷을 유지하고 점수 계층만 라이브로 갱신한다.
라이브 재적합 라벨(K=8/M=5): 현장경제·소비력·결속·브랜드상업·차트확산 — 99개 팬덤이 현장경제형 우세, 투어스만 소비력형(참고용).

## 5. Fan Factor Matrix, Factor Diversity, Persona

- FactorShare(f, m) = Σ_d Σ_{t∈m} θ(d,t) / Σ_d Σ_t θ(d,t) — 문서-토픽 확률의 메타요인 합산·정규화. 100 × 5 행렬(`fandom_scores_v6.json` factor_share, 합 1.0 100/100).
- FactorDiversity(f) = −Σ_m share·ln(share) / ln(5) — 3D 맵 Z축. 라이브 점수와의 관계: Loyalty–Diversity r=0.099(n.s.), Spillover–Diversity r=0.461(p<.001), 다중회귀 R²=0.234, VIF 1.321.
- Factor-specific Impact = share × loyalty / share × spillover(`fan_persona_v7.json`, 500셀 재현).
- Persona = Top-2 Factor 조합(10개 가능): 글로벌투어형 F3+F5 **43** · 현장상업형 F3+F4 **31** · 원정소비형 F2+F3 **17** · 집단동원형 F1+F3 **9**. PCA 분산비 0.408/0.308.

## 6. Coverage Index (5요소, 라이브·동결 100/100 재현)

CoverageIndex = 0.30·언어 + 0.25·시장 + 0.20·출처유형 + 0.15·시간 + 0.10·개체 (전략 문서 권고 가중치, 미검증 채택).

| 요소 | 정의 | 최종 판 비고 |
|---|---|---|
| 언어 | −Σ p ln p / ln(N_lang), 출처 도메인 `language_of()` | 라이브 N=14(ln 14), 동결 N=13(아랍어 전, ln 13) — 각 파일이 해당 분모로만 100/100 |
| 시장 | 언급 시장 카테고리 수 / 6 (일본·중화권·미국북미·유럽·동남아·글로벌 키워드) | |
| 출처유형 | 관측 유형 수 / 3 | |
| 시간 | 관측 연도 수 / 12 (2015∼2026) | |
| 개체 | 언급 개체 카테고리 수 / 6 | |

## 7. 충성도 × 파급효과 점수 (라이브 10,020건) — `v7_final_10020/docs/METHODOLOGY.md` 2-4절

EvidenceScore = 1.0 + 0.5·n_num + 0.3·bonus_keyword, 팬덤별 합 → min-max 정규화. 100개 팬덤 전부 소수 셋째 자리까지 재현(`fandom_scores_live_reference_v7.csv`).
4구획(표본 평균 loyalty 0.3710 / spillover 0.2661): 핵심전략형 24 · 내부결속형 17 · 외부견인형 10 · 주변부 49.
상관: Pearson r=0.493(p<.001, 95% CI [0.329, 0.629]), Spearman ρ=0.380; +activity 통제 R² 0.243→0.847, loyalty 계수 −0.200(부호 반전), VIF 1.93.
χ²(2×2, 0.5 초과 기준 [[7,17],[4,72]]) = 8.34, p=0.0039(동결 10.2273, p=0.0014; 평균 기준 표로는 16.84). Cook's D 최댓값 BTS 0.575, LOO max|Δr| 0.062.

## 8. 보조지표 7종 (LDA와 독립, 라이브 10,020건) — `v7_final_10020/analysis/` 각 폴더

| 지수 | 방법 | 코퍼스 합계 | 노트북 검증 |
|---|---|---|---|
| 광고·상업성 | 31개 광고신호 키워드 + 부정 가드 → 20개 업종 태깅 | 1,302건(13.0%), 98개 팬덤, 업종 태깅 1,488 | 무결성 100/100, 키워드 재매칭 96/100 정확 일치 |
| 팬덤결속 | 5유형 키워드(멀티라벨), D는 팬덤 공존어 게이트 | 923건(9.2%), 99개 팬덤; A 480·D 198·B 190·E 173·C 122 | 무결성 100/100, 동결 LDA 결속형과 r=0.687 |
| 미디어·콘텐츠 노출 | 4개 서브태그 문자열 매칭 | 1,025건(10.2%); 드라마 313·예능 309·유튜브 286·영화 179 | 서브태그명 재매칭 100/100 |
| 매체 크로스오버 | news_media 고유 도메인 수 / 뉴스 불릿 수 | 6,712건(67.0%), 고유 매체 1,298 | 비율 재계산 100/100 |
| 국내 지역 | 17개 시/도 키워드 불릿 수, 다양성 = 검출 지역 수/17 | 최종: 1,226건, 검출 지역 합 469, 커버리지 99/100 (보고서 표 15는 동결 시점: 17/20행 재현) | 17개 시도 합 = total 100/100 |
| 세계 언어 | `language_counts` 재사용, 해외비중·해외언어다양성 | 14개 언어 합 10,020 | 8개 필드 불일치 0/100 |
| 멤버 집중도(MCI) | Σ share², 45개 그룹 | 멤버 언급 1,730, MCI 평균 0.261(NCT 0.111∼FTISLAND 0.660) | 재계산 불일치 0/45; r(MCI, 멤버 수) −0.728 |

## 9. 전략 문서 대비 구현 매트릭스

| 제안 | 상태 |
|---|---|
| Topic → Meta Factor 압축, Factor Diversity Z축 | 구현(동결) |
| K Topic 카드, K→F 영향경로, Persona 계층, Factor-specific Impact | 구현(동결), 500셀·43/31/17/9 재현 |
| Coverage Index 5요소 | 구현, 100/100 |
| 그룹–멤버: Impact Share·MCI | 텍스트마이닝 지수로 축소 구현(45개 그룹) |
| Unit 계층, Joint Evidence, Synergy, Activation Score, event_id 중복 제거 | 미구현 |
| 미디어 독립 메타요인 | K=9 검증에서 기각 → 키워드 지수로 대체 |
| 실루엣 게이트 | 운영(동결 0.267 유지, 라이브 0.046 기각) |

## 10. 금지해야 할 해석

- 보조지표는 LDA 토픽·F 경로가 아니다; "언급 0건"은 해당 활동이 없다는 뜻이 아니라 코퍼스에서 검출되지 않았다는 뜻이다.
- 매체 크로스오버 지수는 유입 경로·전환이 아니다. 국내 지역 지수는 연고와 활동을 구분하지 않는다. 세계 언어 지수는 출처 도메인 언어이지 본문 언어가 아니다.
- MCI는 멤버 수가 적을수록 구조적으로 높다(하한 1/n) — 원시 MCI만으로 "스타 집중"을 말하지 않는다.
- 동결(7,350)과 라이브(10,020) 수치를 한 표에 섞을 때는 계층을 명시한다(예: 표 15 국내 지역 = 동결, 광고 지수 = 라이브).

## 11. 데이터 스키마 (파일별 한 줄)

| 파일 | 내용 |
|---|---|
| `fandoms_v3_100.json` | 100 팬덤 × {fandom, fanclub, category, loyalty[{t,u}], spillover[{t,u}]} = 10,020건 |
| `fandom_scores_v6.json/.csv` | 동결: raw 점수, factor_share(5), factor_diversity, coverage_detail(13개 언어), loyalty/spillover_score, activity(합 7,350) |
| `fandom_scores_live_reference_v7.json/.csv` | 라이브: 같은 스키마, 라이브 재적합 factor_share(5), coverage_detail(14개 언어), activity 합 10,020 |
| `lda_v6_diagnostics_frozen_v7_40.json` / `..._live_reference_v7.json` | k_grid, selected_k/m, 실루엣, topics_top_words, topic_to_factor, factor_labels |
| `fan_persona_v7.json`, `topic_cards_v7.json`, `factor_pathway_map_v7.json`, `persona_decision_space_v7.json` | 해석 계층 산출물 |
| `chart3d_payload_live_reference_v7.json`, `positioning_map_correlation_live_v7.json`, `chart3d_correlation_live_v7.json` | 라이브 점수·통계 |
| `ad_commercial_index_v7`, `fandom_cohesion_index_v7`, `media_exposure_v7`, `media_crossover_index_v7`, `worldwide_language_pilot_live_reference_v7`, `member_mention_index_v7`, `member_pilot_mci_correlation_v7` | 보조지표 원본 |
| `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json` | 국내 지역 지수 최종 10,020건 산출본 |
| `language_domain_summary_v7.json`, `wordcloud_by_language_v7.json`, `lda_excluded_bullets_v7.json`, `k9_validation_v7.json` | 언어·토크나이저·검증 |
| `data/v7_rounds/` | 병합 로그 r1∼r72, 스왑 로그, 라운드 로그 |

## 12. 재현 절차

```bash
python verify_v7_final_consistency.py                 # 보고서 수치 ↔ data/v7_final 96/96
python v7_final_10020/analysis/build_notebooks_v7.py        # 노트북 8개 생성 + 실행(출력 포함)
python v7_final_10020/analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py
python v7_final_10020/analysis/tokenizer/build_bullet_token_frequency_csv_v7.py   # fugashi·jieba·pythainlp 필요
python v7_final_10020/analysis/tokenizer/jieba_and_thai_engine_details_v7.py
```
