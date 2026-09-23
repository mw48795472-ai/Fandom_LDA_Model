# 핵심 수치 요약 (Quick Reference)

보고서에서 반복 인용되는 수치를 한곳에 모은 참고 문서. 각 수치의 근거 파일(`data/v7_final/`)과 계층(동결 스냅샷 7,350건 vs
라이브 10,020건)을 함께 적었고, `verify_v7_final_consistency.py`로 재계산해 대조했다(105/105 일치).

## 코퍼스 규모 — 라이브 코퍼스 `data/v7_final/fandoms_v3_100.json`
- 분석 대상 팬덤: 100개
- 근거 문장 총계: 10,020건 (데이터 파일 저장 기준) / 10,018건 (보고서 표 2-1 "LDA 실제 재적합 문서 수 기준") — 3토큰 미만
  2건 제외: ATEEZ 태국어 감탄문 1건, 레드벨벳 "맥도날드 조이 (2026)" 1건 (`lda_excluded_bullets_v7.json`, 코퍼스 위치 확인)
- 로스터: 동결 스냅샷(7,350건)과 라이브(10,020건)의 100개 팬덤은 3개가 다름 — 동결에만 한로로·pH-1·BE'O, 라이브에만
  몬스타엑스·투어스(TWS)·빈지노 (교체 로그 `data/v7_rounds/merge_log_r58.json`·`swap_log_r62.json`·`swap_log_r63.json`;
  그 이전 r29·r34에 사이먼도미닉→GOT7, 창모→김재중, 헤이즈→박서진 교체)
- 코퍼스 성장 이력(`data/v7_rounds/` 병합 로그 60개 → `corpus_growth_history_v6_v7_full.csv`): v6 2,403건 → r39 7,350(동결)
  → r59 9,042 → r66(2차) 9,680 → r68 아랍어·r69 프랑스어·r71 스페인어 보강 → **r72 10,020건**. after_total이 타임라인 CSV와 56건 전부 일치
- 언어권: 14개 (`language_domain_summary_v7.json`, 14개 언어 불릿 합 = 10,020). 같은 분류가 `fandom_scores_live_reference_v7.json`의
  팬덤별 coverage_detail.language_counts와 세계 언어 지수 원본에도 들어 있어 세 파일의 언어별 합이 일치
- 토크나이저 실행 결과(`wordcloud_by_language_v7.json`): 총 토큰 170,725개, 문자권별 불릿 수 한국어 8,942(89.2%)·영어 6,425·중국어 398·
  비영어(스페인어 등) 219·일본어 155·태국어 56·러시아어 45·베트남어 30 (토크나이저 보고서 표 2와 영어/비영어만 wordfreq 재분류로 차이)
- 한국어 55.4%(5,551건), 영어 21.9%(2,195건), 일본어 5.2%(520건), 중국어 4.6%(458건) 순
  (이전 판의 "일본어 5.3%(529건)"은 오기 — 보고서 표 2-2와 요약 JSON 모두 520건)
- 도메인: **한국어권 704개**(보고서 표 2-2 한국어 행). 요약보고서의 "14개 언어권 704개 도메인"은 이 한국어권
  값이며, 14개 언어권 도메인 수를 단순 합하면 1,149개(언어권 간 중복 포함), 코퍼스 URL 고유 호스트는 1,315개

## LDA 파이프라인 — 동결 스냅샷 v7-40 (7,350건) 기준 해석 계층
- K=10 (원 토픽), M=5 (메타요인, silhouette=0.267) — 진단 원본 `lda_v6_diagnostics_frozen_v7_40.json`(K-grid 7개 중 K=10이 합성순위
  최솟값 8, K=8은 9; 토픽 상위어는 `topic_cards_v7.json`과 동일), `persona_decision_space_v7.json`(Persona_결정공간.html 내장)
- K=9 추가 검증(`k9_validation_v7.json`, 9,614문서 중간 라운드): K=9를 그리드에 넣어도 승자는 K=8이며, 미디어 토픽은 M≥6에서만
  단독 메타팩터로 분리됨
- 페르소나 4유형: 글로벌투어형(F3+F5, n=43) · 현장상업형(F3+F4, n=31) · 원정소비형(F2+F3, n=17) ·
  집단동원형(F1+F3, n=9) — F3(현장경제 경로)가 4유형 전부의 공통 기반 — `fan_persona_v7.json`
- 팬덤별 F1∼F5 비중과 동결 스냅샷 점수: `fandom_scores_v6.csv` / `.json` (activity 합 = 7,350). JSON의 raw 점수·coverage_detail로
  min-max 정규화·F 다양성·coverage 가중합이 재현되며, 동결 시점 언어 커버리지 분모는 ln(13)(아랍어 추가 전; 라이브는 ln(14)).
  동결 7,350건 언어 분포: ko 4,183 · en 1,751 · ja 333 · id 193 · th 181 · zh 153 · tl 133 · es 121 · pt 87 · ru 72 · vi 71 · tr 68 · fr 4
- 라이브 코퍼스(10,020건) 재적합은 K=8, M=5, silhouette=0.046으로 게이트 기각 → 해석 계층에 미반영
  (`lda_v6_diagnostics_live_reference_v7.json`). 그 재적합의 팬덤별 F 비중 5개(현장경제·소비력·결속·브랜드상업·차트확산)와
  factor_diversity·coverage_index·dominant_factor 원본은 `fandom_scores_live_reference_v7.csv` — 99개 팬덤이 현장경제형 우세, 투어스만 소비력형

## 충성도 × 파급효과 — 라이브 코퍼스 (10,020건) 기준
- 4구획(Loyalty×Spillover): 핵심전략형(N=24) · 내부결속형(N=17) · 외부견인형(N=10) · 주변부(N=49)
- Loyalty 평균 = 0.3710, Spillover 평균 = 0.2661 (표본 기준선) — `chart3d_payload_live_reference_v7.json`
- 위 점수는 `METHODOLOGY.md` 2-4절 EvidenceScore 산식을 `fandoms_v3_100.json`에 적용하면 100개 팬덤 전부
  소수점 셋째 자리까지 재현됨 (`fandom_scores_live_reference_v7.csv`)

## 상관/회귀 — 라이브 점수 기준 (전부 재현 확인)
- Pearson r = 0.493 (p<.001, R²=0.243)
- Spearman ρ = 0.380 (p<.001)
- 다중회귀 R² (+activity 통제) = 0.243 → 0.847
- 충성도 회귀계수(+activity 통제) = -0.200 (p<.001, 부호 반전 → 트레이드오프)
- VIF (다중공선성) = 1.93
- 4분면 독립성 χ² = 8.34, p = 0.0039 (라이브) / χ² = 10.2273, p = 0.0014 (프로즌 스냅샷) — 재현 확인
  (`positioning_map_correlation_live_v7.json`). **주의**: 이 검정의 2×2표는 loyalty·spillover 각각 **0.5 초과 여부**
  기준([[7,17],[4,72]], 동결은 [[8,17],[4,71]])이며, 포지셔닝 맵의 표본 평균 기준 4구획(24/17/10/49)과는 기준선이
  다르다(평균 기준 표로는 χ²=16.84).
- R 교차검증: `Statistics/R_통계검증/`이 위 상관·회귀·정규성·VIF·영향점·민감도·LOO·χ²를 R 표준 함수로 재계산해
  2.1절 78·2.2절 80·3.8절 45·7.4절 35 = 238개 항목 전부 일치(`outputs/verify_summary.txt`). 같은 항목을
  `Statistics/verify_r_sections_python.py`(scipy·statsmodels)로 돌려도 238/238 일치
- 부가 통계(같은 파일): Pearson 95% CI [0.329, 0.629], 회귀선 spillover = 0.1234 + 0.3844·loyalty,
  loyalty∼activity r=0.694, spillover∼activity r=0.9019, 이효리 표준화 잔차 +3.59

## 3D 매트릭스 축 독립성 — 라이브 점수 기준 (재현 확인)
- 원본 파일 `chart3d_correlation_live_v7.json` (회귀 계수 절편 0.7168 / loyalty -0.073(p=0.10) / spillover 0.3008(p<.001),
  factor_diversity는 Shapiro p=0.058로 정규성 유지, Cook's D 상위 god 0.246 · 이효리 0.181 · BTS 0.160, LOO 최대 |Δβ|=0.036(god))
- Loyalty-Diversity r = 0.099 (p=0.327, 유의하지 않음)
- Spillover-Diversity r = 0.461 (p<.001, 유의함)
- 다중회귀 R² = 0.234 (F=14.83, p<.001)
- VIF(3축) = 1.321

## 영향점/강건성 — 라이브 점수 기준 (재현 확인)
- Cook's D 최댓값: BTS 0.5749 (2위 god 0.284, 3위 이효리 0.2538, 4위 TWICE 0.2315, 5위 BLACKPINK 0.094)
- 민감도(하이라이트 제거): BTS 제외 r=0.4314 / 임영웅 제외 r=0.4761 / 리센느 제외 r=0.4932
- Leave-one-out: max|Δr|=0.0618(BTS), mean|Δr|=0.00516

## 실루엣 게이트 거버넌스
- 동결 기준선(v7-40 스냅샷): 7,350건, K=10, M=5, silhouette=0.267
- 누적 게이트 기각: 28회 연속 (v7-46∼v7-77, 최종 보고서 docx 기준; 제출 PDF 시점은 26회·v7-65 0.141). 실측 타임라인
  `data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv`(v4 종료 1,781건 → r66 2차 9,680건)에서 v7-40
  이후 실측 재적합 22개 지점(r45 변형 2개 포함)이 전부 0.267 미만(최대 0.148, r49). r68∼r77의 8회는 CSV 범위 밖이며
  최종 라이브 코퍼스 10,020건 시점(r77) 재적합 silhouette=0.046 (K=8, M=5)만 `lda_v6_diagnostics_live_reference_v7.json`·3D 맵 payload로 확인된다

## 하이라이트 3사례 비교

| 지표 | BTS | 리센느(RESCENE) | 임영웅 |
|---|---|---|---|
| Persona (동결 스냅샷) | 글로벌투어형(F3+F5) | 글로벌투어형(F3+F5) | 집단동원형(F3+F1) |
| loyalty_score — 동결 스냅샷 `fandom_scores_v6.csv` | 0.931 | 0.444 | 0.899 |
| spillover_score — 동결 스냅샷 `fandom_scores_v6.csv` | 1.000 | 0.304 | 0.702 |
| loyalty_score — 라이브 10,020건 (3D 맵) | 0.972 | 0.359 | 0.950 |
| spillover_score — 라이브 10,020건 (3D 맵) | 1.000 | 0.262 | 0.517 |
| 근거문장 수 (라이브 / 동결) | 227 / 170 | 85 / 66 | 131 / 112 |
| Cook's D (라이브) | 0.575(최댓값) | — | — |
| 세계언어지수 | 해외비중 60%, 135건, 해외언어다양성 0.66 | — | — |
| 국내지역지수 — 동결 스냅샷 시점(보고서 표 15) | 17건·5지역, 대표지역 서울(47%), 다양성 0.29 | 19건·5지역, 대표지역 경남(58%), 다양성 0.29 | 28건·12지역, 대표지역 서울(21%), 다양성 0.71(전체 1위) |
| 국내지역지수 — 최종 10,020건 (`v7_final_10020/analysis/domestic_regional_index/`) | 17건·5지역, 서울(47%), 0.29 | 22건·5지역, 경남(64%), 0.29 | 28건·12지역, 서울(21%), 0.71(전체 1위) |
| 팬덤결속지수 | 15건(6.6%) | 18건(21.2%) | 30건(23%, 전체 1위) |

팬덤결속·세계언어 지수 행은 `fandom_cohesion_index_v7.json`·`worldwide_language_pilot_live_reference_v7.json`에서 재현 확인.
국내지역 지수: 17개 시/도 키워드 규칙을 최종 코퍼스에 적용한 JSON이 `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json`에 있다.
보고서 표 15는 동결 스냅샷(7,350건) 시점 값으로, 동결 코퍼스를 근사하면 20행 중 17행이 재현된다.

## 보조지표 (라이브 10,020건 기준)
- 광고·상업성 지수 (`ad_commercial_index_v7.json` → `ad_commercial_index_v7.csv`): 광고성 불릿 1,302건(13.0%), 98개 팬덤에
  1건 이상, 20개 업종 태깅 합 1,488(불릿당 복수 업종). 상위: aespa 47건·이효리 47건(비중 39.2%)·TWICE·BTS(37건, 16.3%)·NewJeans.
  업종별 상위: 복지/행정 228, 패션/의류 209, 미용 177, 식음료 169. v7-39(795건, 기타 33%) → v7-40 '기타' 전수 재분류 후 기타 79건.
  스크립트 `v7_final_10020/indices_csv/build_ad_commercial_index_csv.py` 재실행: 팬덤별 합 = 1,302, 업종별 합 = industry_totals 전부 일치
- 팬덤결속 지수 (`fandom_cohesion_index_v7.json`): 결속 불릿 923건(9.2%), 99개 팬덤. 유형별 A 공식팬클럽 480 · D 기부·후원(팬덤주도)
  198 · B 팬카페 190 · E 오프라인결집 173 · C 정체성·문화 122. D는 팬덤 공존어 게이트로 기부 언급 364건 중 166건(45.6%) 제외.
  하이라이트: 임영웅 30건(22.9%, 전체 1위) · 리센느 18건(21.2%) · BTS 15건(6.6%) — 차트 스크립트 2종 재실행 확인
- 미디어·콘텐츠 노출 지수 (`media_exposure_v7.json`): 4종 서브태그 원문 매칭, 미디어 불릿 1,025건(10.2%), 99개 팬덤. 서브태그별
  드라마 313 · 예능 309 · 유튜브 286 · 영화 179(불릿당 복수 태그). 상위 임영웅 27건(20.6%, 1위) · 카더가든 26 · 오마이걸 21 · SEVENTEEN 20;
  리센느 10건, BTS 13건(5.7%). methodology 원문: LDA 토픽/메타팩터가 아니며 K9/F6 검증에서 독립 미디어 토픽이 확인되지 않아 도입
- 매체 크로스오버 지수 (`media_crossover_index_v7.json`): news_media 출처 불릿 6,712건(67.0%), 코퍼스 전체 고유 매체 1,298개
  (상위 v.daum.net 377, starnewskorea.com 251, sports.khan.co.kr 216). BTS 매체 96개(뉴스 불릿 177건, 다양성 0.54), 임영웅 60개(0.50),
  리센느 36개(0.53). SNS·커뮤니티·위키는 매체로 세지 않음; 유입경로가 아닌 매체 확산 폭의 대리 지표
- 세계 언어 지수 (`worldwide_language_pilot_live_reference_v7.json` → `worldwide_language_index_v7.csv`): 팬덤별 14개 언어 언급수,
  언어다양성, 해외비중(ko 제외), 해외언어다양성, 대표해외언어. 14개 언어 합이 언어 표(10,020건)와 정확히 같고 스크립트 재실행 결과
  불일치 0. 해외 근거문장수 상위: BLACKPINK·BTS(135건, 59.5%→60%, 해외언어다양성 0.66)·Stray Kids·TWICE·SEVENTEEN
- 국내 지역 지수: `v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json`(최종 10,020건: 지역 언급 1,226건,
  검출 지역 합 469, 커버리지 99/100 — 투어스(TWS)만 0건; 상위 싸이 43·이승철 38·박서진 31·송가인 31·나훈아 30·god 28·임영웅 28).
  보고서 표 15(동결 시점) 17/20행 재현. 17개 시도별 언급수 합 ↔ total_region_mentions 100/100
- 멤버 집중도 지수(MCI): `data/v7_final/member_mention_index_v7.json` — 45개 그룹, 10,020건 코퍼스 기준
  (예: BTS 근거문장 227건 중 멤버명 언급 101건, MCI=0.241).
  동결 스냅샷(7,350건) 시점 파일럿(23개 그룹, BTS 170건 중 73건, MCI 0.24)은 `member_mention_pilot_v6.json`
- MCI ↔ outcome 상관(`member_pilot_mci_correlation_v7.json`, 45개 그룹, MCI는 v7-55 시점 8,981건): 원시 MCI∼loyalty
  r=-0.393(p=0.008, R²=0.155)이 가장 크지만 MCI∼멤버 수 r=-0.749로, 멤버 수를 뺀 MCI_excess 기준으로는 어떤 outcome과도
  유의하지 않음(최대 R²=0.036). 최종 10,020건 MCI로 재계산하면 r=-0.385, MCI∼멤버 수 r=-0.728, MCI_excess 최대 R²=0.046
  (상세 보고서 7.4절 표와 전부 일치 — `Statistics/R_통계검증/` 7.4절 35/35. 그 패키지의 `data/member_mention_pilot_v7.json`은
  `member_mention_index_v7.json`과 값이 같고 키 이름만 `mci_pilot`/`mci_index`로 다르다)
- K=10 토픽 카드(`topic_cards_v7.json`): 토픽별 상위 키워드·대표 불릿 3건·대표 팬덤 5개·연결 F 경로. 명칭은 METHODOLOGY.md
  2-1 표와 동일
