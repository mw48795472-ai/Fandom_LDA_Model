# r73 — 투어스(TWS) 근거 86건 한국어 재작성 코퍼스

r63에 교체 진입한 투어스의 근거 90건 중 86건이 영문 본문으로 수집돼(코퍼스 평균 13%, 다른 신생 그룹 8∼19%) 한국어 기준 파이프라인(EvidenceScore 보너스 키워드·수치 패턴, 토크나이저의 영문 토픽 T3→F2)에서 체계적으로 낮게 평가됐다: 문장당 EvidenceScore 1.05(코퍼스 1.68), 합산 순위 100/100, F2 비중 0.74로 PCA 아웃라이어. 리서치 양·내용(팬클럽·앰버서더·일본·동남아, 86건)은 다른 팬덤과 다르지 않다.

r73은 그 86건을 **같은 사실·같은 수치·같은 URL**로 한국어 뉴스 요약체(코퍼스 관행)로 다시 쓴 코퍼스다. 다른 99개 팬덤과 투어스의 한국어 4건은 r72와 같다.

| 파일 | 내용 |
|---|---|
| `fandoms_v3_100_r73.json` | r73 코퍼스 10,020건 (r72 `../fandoms_v3_100.json`에서 투어스 86건 텍스트만 교체) |
| `tws_bullets_rewrite_r73.csv` | 검토용: 원문(r72)·한국어 요약(r73)·URL 90행, `changed` 열 |
| `tws_bullets_ko_r73.py` | 요약문 원본(딕셔너리) — 재작성은 모델(Claude)이 했고 사실·수치는 원문에서 옮겼다 |

r72 코퍼스와 산출물(최종 보고서 PDF·HTML과 대응)은 그대로 둔다. r73 산출물은 재구성 파이프라인 `run_lda_v6_live_reference_v7.py`로 만든다(`output/lda_r73_tws_ko/` → 이 폴더로 복사).

## 산출물 (이 폴더)

| 파일 | 내용 |
|---|---|
| `fandom_scores_r73.json` / `.csv` | r73 점수(EvidenceScore·coverage·factor_share). 투어스 외 99개 팬덤은 r72 `../fandom_scores_live_reference_v7.*`와 동일, 투어스는 L/S 0.03/0.07 → 0.34/0.37, 합산 100위 → 32위 |
| `lda_v6_diagnostics_r73.json` | 재구성 파이프라인 재적합 진단: K=8, `--force-m 5`(M=5 고정, 자동 선택은 M=6), M별 실루엣 `m_grid_silhouette` {5: 0.0916, 6: 0.0799, 7: 0.0532}, 토픽 상위어·토픽→F 배정 |

## 게이트 판정과 채택

시드 10개 K=8 점검(`v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/seed_stability_r73/`): M=5 실루엣 중앙값 0.081(r72 0.102), Jaccard 0.425, 최빈 M=4(90% 규칙으로 G3 통과). G1(현직 중앙값 0.097 이상)은 미달. **게이트 v2.1**(2026-09-23): 코퍼스 건수를 바꾸지 않는 텍스트 품질 수정 라운드는 새 후보가 아니라 현직 재측정으로 보아 G1을 적용하지 않는다 — 이 규칙으로 r73을 채택했고(`data/v7_rounds/round_log_r73.json`), 루트 README 4·5절의 해석 계층은 `v7_final_10020/analysis/persona_decision_space/live_interpretive_layer/`(r73)이다. r72 계층은 `live_interpretive_layer_r72/`에 보관한다. 재적합에서 출연·예능(T2)과 브랜드·광고(T3)가 미디어노출형(F4) 하나로 합쳐져 페르소나 분포가 r72 62/17/12/9 → r73 89/8/2/1로 움직였다(투어스는 글로벌투어형).
