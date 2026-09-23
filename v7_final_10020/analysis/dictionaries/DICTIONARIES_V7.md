# 지표 사전 모음 — 코드·JSON에서 추출 (L4)

보조지표·Coverage Index 계산에 쓰이는 키워드·도메인·별칭 사전을 한 파일(`index_dictionaries_v7.csv`)로 고정했다. 전부 `export_index_dictionaries_v7.py`가 저장소의 코드와 JSON에서 ast/json으로 읽어 쓴 것이라 손으로 옮긴 값이 없다. **원본 파이프라인에만 있었고 저장소에 남지 않은 사전은 아래 표에 '없음'으로 적었다** — 그 지표는 저장된 집계값만 재현·검증하고 태깅 자체는 다시 하지 않는다.

| 지표 | 사전 | 저장소 유무 | 건수 | 출처 |
|---|---|---|---|---|
| Coverage Index | 시장 키워드 6권역 | 있음 | 53 | `run_lda_v6.py` |
| Coverage Index | 엔티티 카테고리 6종 | 있음 | 46 | `run_lda_v6.py` |
| Coverage Index / 세계 언어 | 언어·출처유형 도메인 허용목록 | 구 판만 있음 (6개 언어) | 65 | `run_lda_v6.py` — 최종 14개 언어 판은 `run_lda_v6_live_reference_v7.py` 원본 유실, 라이브 언어 집계값은 `language_domain_summary_v7.json` |
| 국내 지역 지수 | 17개 시도 지명 키워드 | 있음 | 48 | `analysis/build_notebooks_v7.py` |
| 광고·상업성 지수 | 광고 신호 키워드 31 | 있음 | 31 | `ad_commercial_index_v7.json` |
| 광고·상업성 지수 | 부정 가드 7 | 있음 | 7 | `analysis/build_notebooks_v7.py` |
| 광고·상업성 지수 | 업종 목록 20 | 있음 | 20 | `ad_commercial_index_v7.json` |
| 광고·상업성 지수 | 업종별 브랜드·키워드 사전(INDUSTRY_KEYWORDS) | **없음** (r65 추가분 일부만) | 13 | `merge_log_r65.json`(r65 추가분만) |
| 팬덤 결속 지수 | 유형 5종 | 있음 | 5 | `fandom_cohesion_index_v7.json` |
| 팬덤 결속 지수 | 유형별 키워드 목록 | **없음** | — | — |
| 팬덤 결속 지수 | D(기부·후원) 게이트 공존어 | 있음 | 8 | `fandom_cohesion_index_v7.json` methodology |
| 미디어·콘텐츠 노출 지수 | 서브태그 4 | 있음 | 4 | `media_exposure_v7.json` |
| 멤버 집중도(MCI) | 멤버 별칭 (파일럿 10그룹) | 있음 | 122 | `run_lda_v6.py` — 최종 45그룹은 `member_mention_index_v7.json` 그룹별 항목 |
| 세계 언어 지수 | 14개 언어 코드·라벨 | 있음 | 14 | `analysis/build_notebooks_v7.py` |
| 토크나이저 | 언어별 불용어 | 있음 | 1,503+ | `analysis/tokenizer/stopwords/` (별도 정리) + 재구성본 `run_lda_v6_live_reference_v7.py` |

합계 436행. 없음으로 표시된 두 사전(광고 업종 키워드 전체, 결속 유형 키워드)은 원본 산출물 JSON에 집계값만 남아 있어 복원할 수 없다. 다음 라운드부터는 지수 스크립트가 이 CSV를 읽도록 하고, 사전을 바꿀 때 CSV를 함께 커밋하는 것이 L4의 남은 절반이다.

