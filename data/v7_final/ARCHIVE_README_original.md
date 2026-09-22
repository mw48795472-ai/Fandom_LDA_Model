# 팬덤 100개 LDA v7 분석 — 데이터 아카이브

이 zip은 `팬덤100_LDA_v7_보고서.docx` / `팬덤100_LDA_v7_핵심요약(별도보고서).docx`가 실제로 읽어들여 표·그래프를
만드는 데 쓰인 원본 JSON/CSV 데이터 전량입니다(두 빌드 스크립트의 `fs.readFileSync` 호출 대상을 그대로
추출했습니다). 라운드별 진행 중 만들어졌던 백업(.bak_*)·실험용 스크래치 파일·프롬프트 원문 등은 최종
결과에 쓰이지 않아 제외했습니다.

## 1. 코퍼스 원본
- `fandoms_v3_100.json` — 100개 팬덤별 loyalty/spillover 근거문장 원문 전체(현재 라이브 코퍼스, 2026-09 기준).

## 2. 팬덤 점수 — 두 스냅샷 체계
- `fandom_scores_v6.json` / `.csv` — **v7 40 시점 고정(freeze) 스냅샷**(7,350건). 보고서 3·5·6장·전체
  순위표가 참조하는 "공식" 점수.
- `lda_v6_diagnostics.json` — 위 고정 스냅샷의 LDA/Meta Factor 진단(K=10·M=5·실루엣=0.267).
- `fandom_scores_live_reference_v7.json` / `.csv` — **매 라운드 재계산되는 라이브 참고용** 점수(게이트 미검증,
  2·3장·4장이 참조).
- `lda_v6_diagnostics_live_reference_v7.json` — 라이브 코퍼스 기준 LDA/Meta Factor 진단(현재 K/M/실루엣).
- `lda_excluded_bullets_v7.json` — LDA 재적합 시 제외된 문장 목록(코퍼스 저장 건수 vs 실제 학습 문서 수 차이 근거).

## 3. 통계적 가설검정
- `positioning_map_correlation_live_v7.json` — 팬충성도×파급효과 상관/회귀/정규성/영향점 분석(라이브 기준).
- `chart3d_correlation_live_v7.json` — 3D 맵 Z축(팬 요인 다양성) 독립성 검증(라이브 기준).
- `chart3d_correlation_v7.json` — 위와 동일 검증의 v7 40 스냅샷 버전(대비용, 참고).
- `k9_validation_v7.json`, `_explore_r45_meta_factor.json` — 본문에 인용된 부가 진단(K/M 그리드 재탐색 등).

## 4. 보조지표(LDA와 무관, 원문 키워드/도메인 매칭)
- `ad_commercial_index_v7.json` — 광고·상업성 지수(업종별 근거문장 집계).
- `fandom_cohesion_index_v7.json` — 팬덤결속 지수(공식 팬클럽·팬카페·기부 캠페인 등).
- `media_exposure_v7.json` — 미디어·콘텐츠 노출 지수(예능/유튜브/영화/드라마).
- `media_crossover_index_v7.json` — 매체 크로스오버 지수(뉴스 도메인 매칭).
- `language_domain_summary_v7.json` — 언어별 근거 출처 도메인 요약.
- `wordcloud_by_language_v7.json` — 언어(문자권)별 토크나이저 실행 결과(워드클라우드 소스).

## 5. 파일럿(별도 트랙)
- `domestic_regional_pilot_v6.json` — Domestic Regional Pilot(국내 17개 시/도 지역명 언급).
- `worldwide_language_pilot_live_reference_v7.json` — Worldwide Language Pilot(해외언어 비중/다양성).
- `member_mention_pilot_v7.json`(현재)/`member_mention_pilot_v6.json`(구버전, 대비용) — Member Mention Pilot.
- `member_pilot_mci_correlation_v7.json` — MCI(멤버 집중도)와 그룹 outcome 지표 상관 검증.

## 6. K→F→Persona 해석 계층
- `topic_cards_v7.json` — K(LDA 토픽) 카드.
- `factor_pathway_map_v7.json` — F(Meta Factor→파급경로) 매핑.
- `fan_persona_v7.json` — Persona 유형(F1∼F5 조합) 및 Factor-specific Impact.

## 7. v7_rounds/ — 라운드별 병합·교체 로그
`merge_log_r*.json`(리서치 병합)·`swap_log_r*.json`(팬덤 로스터 교체)·`round_log_r70.json`·
`member_pilot_r53~55_compare.json` 등, 보고서가 라운드별 진행 서술에 실제로 인용하는 원본 로그 전량입니다.
파일명의 숫자가 라운드 번호(v7 N)입니다.

## 8. supplementary_csv/ — 보조 CSV
- `domestic_regional_pilot_v6_top3.csv` — 팬덤별 지역 top3 요약.
- `팬덤100_언어비중.csv` — 팬덤별 언어 비중.
- `fandom_bullet_share_v6.csv` — 팬덤별 근거문장 비중.

---
문의: 각 파일의 필드 의미와 산식은 원본 상세 보고서(팬덤100_LDA_v7_보고서.docx) 및 상세명세서
(팬덤100_LDA_v7_상세명세서.docx)에 절 번호와 함께 설명되어 있습니다.
