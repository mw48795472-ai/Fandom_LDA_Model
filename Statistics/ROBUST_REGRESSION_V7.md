# 강건 회귀 병기 (L11) — OLS 결론이 추정 방법에 따라 달라지는가

팬충성도(W=0.954, p=0.0015)·파급효과(W=0.861, p<.001)는 정규성을 위반하고 n=100이다. 보고서의 OLS 두 개를 Huber M-추정·중위수 분위회귀·영향점 5개 제외 OLS로 다시 적합해 계수 부호와 유의성(p<0.05)이 같은지 본다. `robust_regression_v7.py`가 만든다.

## 0. 결론

- live_10020 · spillover ~ loyalty + activity: loyalty_score: 부호 일치·유의성 일치; activity: 부호 일치·유의성 일치
- live_10020 · factor_diversity ~ loyalty + spillover: loyalty_score: 부호 일치·유의성 일치; spillover_score: 부호 일치·유의성 일치
- frozen_7350 · spillover ~ loyalty + activity: loyalty_score: 부호 일치·유의성 일치; activity: 부호 일치·유의성 일치
- frozen_7350 · factor_diversity ~ loyalty + spillover: loyalty_score: 부호 일치·유의성 일치; spillover_score: 부호 일치·유의성 일치

## 1. 계수 표 (계수, SE, p)

### live_10020 — spillover ~ loyalty + activity

| 방법 | n | loyalty_score 계수 (SE, p) | activity 계수 (SE, p) |
|---|---|---|---|
| OLS | 100 | -0.1996 (0.0429, 1e-05) | 0.0064 (0.0003, 0.0) |
| Huber(RLM) | 100 | -0.2037 (0.0409, 0.0) | 0.0063 (0.0003, 0.0) |
| Quantile(q=0.5) | 100 | -0.1965 (0.0541, 0.00045) | 0.0063 (0.0004, 0.0) |
| OLS w/o Cook's top5 | 95 | -0.2128 (0.0419, 0.0) | 0.0063 (0.0003, 0.0) |

영향점 제외 5개: 이효리, 임영웅, 투어스(TWS), SEVENTEEN, TWICE

### live_10020 — factor_diversity ~ loyalty + spillover

| 방법 | n | loyalty_score 계수 (SE, p) | spillover_score 계수 (SE, p) |
|---|---|---|---|
| OLS | 100 | -0.073 (0.044, 0.10036) | 0.3008 (0.0564, 0.0) |
| Huber(RLM) | 100 | -0.0698 (0.0462, 0.13042) | 0.2948 (0.0592, 0.0) |
| Quantile(q=0.5) | 100 | -0.0982 (0.0677, 0.15018) | 0.3251 (0.0869, 0.00031) |
| OLS w/o Cook's top5 | 95 | -0.0693 (0.0473, 0.14613) | 0.3604 (0.0631, 0.0) |

영향점 제외 5개: god, 이효리, BTS, 투어스(TWS), 지드래곤 (G-Dragon)

### frozen_7350 — spillover ~ loyalty + activity

| 방법 | n | loyalty_score 계수 (SE, p) | activity 계수 (SE, p) |
|---|---|---|---|
| OLS | 100 | -0.3136 (0.065, 1e-05) | 0.0087 (0.0005, 0.0) |
| Huber(RLM) | 100 | -0.3117 (0.0617, 0.0) | 0.0085 (0.0005, 0.0) |
| Quantile(q=0.5) | 100 | -0.3348 (0.078, 4e-05) | 0.0085 (0.0006, 0.0) |
| OLS w/o Cook's top5 | 95 | -0.2917 (0.0619, 1e-05) | 0.0083 (0.0005, 0.0) |

영향점 제외 5개: 임영웅, SEVENTEEN, 이효리, TWICE, 지드래곤 (G-Dragon)

### frozen_7350 — factor_diversity ~ loyalty + spillover

| 방법 | n | loyalty_score 계수 (SE, p) | spillover_score 계수 (SE, p) |
|---|---|---|---|
| OLS | 100 | 0.0267 (0.0371, 0.47257) | -0.043 (0.0412, 0.29938) |
| Huber(RLM) | 100 | 0.0308 (0.0363, 0.39732) | -0.0442 (0.0404, 0.27366) |
| Quantile(q=0.5) | 100 | 0.0688 (0.0419, 0.10412) | -0.0561 (0.0466, 0.23163) |
| OLS w/o Cook's top5 | 95 | 0.0301 (0.0352, 0.3952) | -0.0533 (0.0397, 0.18308) |

영향점 제외 5개: 지드래곤 (G-Dragon), 레드벨벳, pH-1, 임영웅, 에픽하이

## 2. 한계
1. Huber·분위회귀의 p값은 점근 근사라 n=100에서 정확하지 않다. 부호·유의성의 '일치 여부'만 읽는다.
2. 영향점 제외는 Cook's D 상위 5개의 기계적 제외이며, BTS·god·이효리처럼 실제로 극단인 팬덤을 빼는 것이 분석 목적에 맞는지는 별개 문제다.
3. 종속변수가 0∼1 min-max 점수라 분위회귀가 더 자연스러운 선택일 수 있으나, 보고서 본문은 OLS를 유지하고 이 문서를 병기한다.

## 3. 파일
| 파일 | 내용 |
|---|---|
| `robust_regression_v7.json` | 라이브·동결 × 모형 2 × 방법 4의 계수·SE·p·일치 여부 |
| `robust_regression_v7.py` | 이 문서를 만드는 스크립트 |

