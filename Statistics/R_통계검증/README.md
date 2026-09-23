# 팬덤100 LDA v7 — 통계적 검증 재현 코드 (R)

「팬덤100_LDA_v7_보고서」가 보고하는 통계적 검증을, 보고서가 실제로 읽어들인 원본
JSON에서 **R 표준 통계 함수로 다시 계산해 대조**하는 코드다. 동봉된 Python 패키지와
같은 입력·같은 정답지를 쓰며, **두 언어의 결과가 서로 일치하는지까지가 검증 범위**다.

검증 결과: **238개 대조 항목 전부 일치** (Python 구현은 235개 전부 일치).


## 처음 시작하기 — raw 데이터만 있을 때

원본 아카이브 폴더(`팬덤100_LDA_v7_데이터아카이브`, 30여 개 파일) 또는 그 zip만 있으면
된다. Claude Code·RStudio 없이 **R만** 있으면 된다.

1. R 설치: https://cran.r-project.org
2. **`START.bat` 더블클릭.** 원본을 자동으로 찾아 필요한 JSON 7개만 `data/` 에 복사하고,
   패키지 설치 → 검증 238개 → 플롯 7종까지 한 번에 돈다.
   못 찾으면 원본 폴더(또는 zip)를 `START.bat` **위로 끌어다 놓으면** 그 위치를 쓴다.
3. 마지막 줄이 `합계 238 238 0` 이면 끝. 그림은 `outputs/plots/`.

터미널: `Rscript SETUP_DATA.R [원본경로]` → `Rscript RUN_ALL.R`.
RStudio: `SETUP_DATA.R` Source → `RUN_ALL.R` Source.

## 무엇을 검증하는가

| 절 | 내용 | 정답지 | 대조 |
|---|---|---|---|
| 2.1 | 포지셔닝 맵 두 축(팬충성도 × 파급효과) 상관계수 분석 및 통계적 검증 | `positioning_map_correlation_live_v7.json` | 78 |
| 2.2 | 3D 포지셔닝 맵 Z축(팬 요인 다양성) 독립성 검증 | `chart3d_correlation_live_v7.json` | 80 |
| 3.8 | K9(미디어·콘텐츠 확장)/F6 제안 검증 | `k9_validation_v7.json` | 45 |
| 7.4 | 멤버 집중도(MCI)의 그룹 지표 설명력 검증 | 보고서 7.4절 본문 표 | 35 |

## 쓰는 패키지와 함수

이 코드는 **필수 패키지를 두 개로 줄이고, 통계량은 R 표준 함수를 그대로 쓴다.**
직접 구현한 것이 적을수록 "R로도 같은 값이 나온다"는 교차 검증의 의미가 커지기
때문이다.

| 패키지 | 용도 | 필수 |
|---|---|---|
| `jsonlite` | 원본 JSON 로딩 (`fromJSON`) | 필수 |
| `car` | `vif()` — 분산팽창지수 | 필수 |
| `ggplot2` | 진단 플롯 7종 | 필수 |
| `ggrepel` | 겹치지 않는 점 라벨 (영향점·강조 팬덤 이름) | 필수 |
| `patchwork` | 여러 패널을 한 장으로 합치기 (`p1 + p2`) | 필수 |
| `broom` | 회귀 결과 tidy 변환 | 선택 |

R 표준 `stats` 패키지에서 그대로 쓰는 함수:

| 함수 | 재현하는 통계량 |
|---|---|
| `cor.test()` | Pearson r · Spearman ρ · p-value |
| `shapiro.test()` | Shapiro-Wilk W · p |
| `lm()` / `summary()` | OLS 계수 · 표준오차 · t · p · R² · adj R² · F · F p |
| `rstandard()` | 표준화(내부 스튜던트화) 잔차 |
| `cooks.distance()` | Cook's distance |
| `hatvalues()` | leverage |
| `chisq.test(correct = TRUE)` | 카이제곱 독립성 검정 (Yates 연속성 보정) |
| `rank(ties.method = "first")` | K-그리드 합성순위합 |

Pearson 95% 신뢰구간만 Fisher z 변환으로 직접 계산한다(`common.R`의
`pearson_ci95`). `cor.test()`도 같은 CI를 주지만, Python 구현과 동일한 경로로 맞춰
두 언어의 값을 비교하기 위해서다 — 결과는 같다.

## 실행 — 파일 하나, 버튼 하나

**`RUN_ALL.R` 만 열고 Source 하면 끝난다.** 패키지 설치부터 PNG 저장까지 전부 한
파일에 들어 있다.

```
RStudio → RUN_ALL.R 열기 → Ctrl + Shift + S   (또는 우측 상단 [Source] 버튼)
터미널  → Rscript RUN_ALL.R
```

> **Run(Ctrl+Enter)이 아니라 Source(Ctrl+Shift+S)다.** Run은 커서가 놓인 줄만
> 실행한다. 전체 실행은 Source이며, 버튼 이름도 `Source`다.

`RUN_ALL.R` 이 순서대로 하는 일:

| 단계 | 내용 |
|---|---|
| [1/6] | `jsonlite`·`car`·`ggplot2`·`ggrepel`·`patchwork` 확인 후 없으면 **자동 설치** (CRAN 미러 미리 지정 · 개인 라이브러리 자동 생성) |
| [2/6] | 패키지 로드 + **한글 폰트 자동 설정** (Windows 맑은 고딕 / macOS AppleGothic / Linux 나눔고딕) |
| [3/6] | `data/` 폴더 자동 탐색 후 원본 JSON 로딩 |
| [4/6] | 보고서 2.1 · 2.2 · 3.8 · 7.4절 통계 검증 — **238개 항목 대조** |
| [5/6] | 진단 플롯 7종 (**ggplot2**) — RStudio **Plots 창** + `outputs/plots/*.png` 동시 출력 |
| [6/6] | 총괄 요약표 + `outputs/verify_summary.txt` |

### Plots 창에서 그림 보기

`render()` 가 그림마다 `ggsave()` 로 PNG를 저장하고, 대화형 세션이면 `print(p)` 로
Plots 창에도 띄운다. **ggplot 객체는 함수 안에서 저절로 출력되지 않기 때문에
`print()` 가 반드시 필요하다** — Plots 창이 비는 가장 흔한 원인이 이것이다.

| 하고 싶은 것 | 방법 |
|---|---|
| 7장을 앞뒤로 넘겨 보기 | Plots 창 왼쪽 위 화살표 `←` `→` |
| 한 장씩 멈추며 보기 | `RUN_ALL.R` 의 `PAUSE_BETWEEN_PLOTS <- TRUE` 로 바꾸고 다시 Source |
| 특정 그림만 다시 보기 | 실행 후 콘솔에 `FIGS$fig4_influence_R` |
| 크게 보기 | Plots 창의 `Zoom` |
| 직접 고쳐 보기 | `FIGS$fig1_positioning_scatter_R + labs(title = "내 제목")` |

실행이 끝나면 7장이 `FIGS` 리스트에 ggplot 객체 그대로 남는다. 테마·라벨·축을
`+` 로 덧붙여 바로 수정할 수 있고, 수정본을 `ggsave()` 로 따로 저장해도 된다.

한 파일로 만든 이유는 실행 경로를 하나로 줄이기 위해서다. 아래 상황을 모두
통과하도록 작성했고, 네 경우 전부 `238 / 238 일치`로 실제 확인했다.

| 실행 방식 | 스크립트 위치 파악 경로 | 확인 |
|---|---|---|
| `Rscript RUN_ALL.R` (패키지 폴더에서) | `commandArgs("--file=")` | ✅ |
| `Rscript /전체/경로/RUN_ALL.R` (다른 폴더에서) | `commandArgs("--file=")` | ✅ |
| RStudio **Source** 버튼 = `source()` | `sys.frame()$ofile` | ✅ |
| 콘솔에 전체 붙여넣기 (경로 정보 없음) | 작업 디렉터리 기준 재귀 탐색 | ✅ |

`data/` 를 못 찾으면 멈추는 대신 **어디를 찾았는지와 무엇을 하면 되는지**를 출력한다
(RStudio라면 `Session > Set Working Directory > To Source File Location`).

### 절별로 따로 돌리고 싶다면

`R/` 폴더에 절별 스크립트가 그대로 남아 있다. 내용은 `RUN_ALL.R` 과 같다.

```bash
Rscript install_packages.R      # jsonlite, car 설치
cd R
Rscript verify_all.R            # 수치 검증 — 절별 상세 + 총괄 요약
Rscript verify_all.R --quiet    # 총괄 요약만
Rscript s01_positioning_correlation.R   # 절 하나만
Rscript plots.R                 # 진단 플롯 7종 → ../outputs/plots/*_R.png
```

다만 `R/` 의 파일들은 **터미널(`Rscript`) 실행 전용**이다. `common.R` 을 찾는 데
`commandArgs("--file=")` 를 쓰기 때문에 RStudio Source 버튼으로는 동작하지 않는다.
RStudio에서 쓸 때는 `RUN_ALL.R` 을 쓰면 된다.

종료 코드 `0` = 모든 대조 일치, `1` = 불일치 존재.

CRAN 접근이 막힌 환경이라면 Debian/Ubuntu에서는 apt로도 설치된다:

```bash
sudo apt-get install -y r-cran-jsonlite r-cran-car
```

### 한글이 깨져 보이면

- **주석·출력이 `???` 나 `占쏙옙`** → RStudio `File > Reopen with Encoding... > UTF-8`
  후 다시 Source. (R 4.2 이상 Windows는 UTF-8이 기본이라 대개 그냥 열린다.)
- **그림의 한글만 네모** → 맑은 고딕 문제다. `[2/6]` 이 출력하는 `폰트:` 줄을
  확인하면 어떤 폰트가 잡혔는지 알 수 있다. 계산 결과 238개 대조에는 영향이 없다.

## 실행 결과

```
절    검증 항목                                   대조    일치  불일치
2.1   포지셔닝 맵 상관계수 분석 및 통계적 검증      78      78       0
2.2   3D 포지셔닝 맵 Z축 독립성 검증                80      80       0
3.8   K9/F6 제안 검증                               45      45       0
7.4   멤버 집중도(MCI) 설명력 검증                  35      35       0
합계                                               238     238       0
```

## 구성

```
fandom_stats_r/
├── README.md
├── RUN_ALL.R                                  ★ 이 파일 하나만 Source 하면 전부 실행
├── install_packages.R
├── data/                                      검증 입력 JSON. 저장소에서는 member_mention_pilot_v7.json 만 커밋되어 있고,
│                                              나머지 7개는 RUN_ALL.R·SETUP_DATA.R 이 저장소 원본 data/v7_final 에서 자동 복사한다(중복 보관 금지)
│   ├── fandom_scores_live_reference_v7.json   라이브 참고용 점수 (n=100)
│   ├── fandom_scores_v6.json                  v7-40 동결 스냅샷 — 7.4절 outcome
│   ├── member_mention_pilot_v7.json           45개 그룹 멤버별 언급·MCI
│   ├── positioning_map_correlation_live_v7.json
│   ├── chart3d_correlation_live_v7.json
│   ├── k9_validation_v7.json
│   ├── member_pilot_mci_correlation_v7.json
│   └── lda_v6_diagnostics.json
├── R/                                         절별로 나눠 보고 싶을 때 (Rscript 전용)
│   ├── common.R                     로더 · CI · OLS 요약 · 영향점 · 대조 기록기
│   ├── s01_positioning_correlation.R
│   ├── s02_axis3d_independence.R
│   ├── s03_k9_validation.R
│   ├── s04_mci_explanatory_power.R
│   ├── verify_all.R
│   └── plots.R                      진단 플롯 7종 (ggplot2, RUN_ALL.R과 동일 코드)
└── outputs/
    ├── *.txt                        절별 요약
    └── plots/*_R.png                진단 플롯
```

## 진단 플롯 7종

`Rscript plots.R` 가 `outputs/plots/` 에 PNG 7장을 만든다(파일명 끝의 `_R` 로 Python
산출물과 구분). 동봉된 Python 패키지의 `src/plots.py` 가 같은 7종을 같은 데이터로
그린다.

| 파일 | 내용 |
|---|---|
| `fig1_positioning_scatter_R` | 2.1 포지셔닝 맵 — 두 축 산점도 + 회귀선 + 4분면 |
| `fig2_sign_reversal_R` | 2.1 **핵심 발견** — 활동량 통제 시 부호 반전 |
| `fig3_qq_normality_R` | 2.1·2.2 Q-Q plot 3종 (`qqnorm`/`qqline`) |
| `fig4_influence_R` | 2.1·2.2 영향점 진단 (`hatvalues`/`rstandard`/`cooks.distance`) |
| `fig5_axis3d_pairs_R` | 2.2 3D 세 축 쌍별 산점도 |
| `fig6_k9_grid_R` | 3.8 K-그리드 합성순위 · M-그리드 실루엣 |
| `fig7_mci_R` | 7.4 MCI 구조적 하한(1/n) · 설명력 R² 비교 |

**ggplot2로 그린다.** 공통 테마 `theme_fandom()` 하나를 모든 그림이 공유하므로
색·격자·글꼴 규칙이 7장에 똑같이 적용된다. 패널이 여러 개인 그림은 축 이름이
패널마다 같으면 `facet_wrap()`, 다르면 `patchwork`(`p1 + p2`)로 붙인다 — fig5처럼
패널마다 x·y 이름이 다른 경우 facet은 쓸 수 없다.

점 라벨은 전부 `ggrepel` 이 자동 배치한다. 다만 ggrepel은 **점만 피하고 회귀선이나
다른 레이어의 주석은 모른다.** 그래서 fig1에서는 (1) 잔차 부호 방향으로 라벨을 미리
밀어 회귀선을 비켜 가게 하고 (2) `xlim`/`ylim` 으로 라벨 영역을 데이터 범위 안에
묶어 모서리의 4분면 도수 주석과 겹치지 않게 했다.

플롯에 찍히는 수치는 전부 그 자리에서 다시 계산한 값이다 — fig1의 4분면 도수
(7·17·4·72)와 카이제곱(χ²=8.3439, p=0.0039)도 하드코딩이 아니라 데이터에서 다시
센다.

한글 폰트는 실행 환경에 맞춰 자동 설정한다 — Windows 맑은 고딕, macOS AppleGothic,
Linux는 `fc-list :lang=ko` 탐색(NanumGothic 우선). 없으면
`sudo apt-get install -y fonts-nanum`. 폰트가 없어도 **238개 대조 결과에는 영향이
없다.**

## Python 구현과의 차이

두 구현은 같은 값을 내지만, 대조 항목 수가 다르고(238 vs 235) 몇 군데 구현 경로가
다르다. 의도된 차이이며 아래에 그대로 밝힌다.

| 항목 | Python | R |
|---|---|---|
| OLS | `common.py`에 직접 구현 (numpy 정규방정식) | `lm()` / `summary()` |
| VIF | 직접 구현 (각 예측변수를 나머지에 회귀) | `car::vif()` |
| Cook's D · 표준화 잔차 | 직접 구현 | `cooks.distance()` · `rstandard()` |
| 카이제곱 4분면 | 2×2 표 전체를 한 항목으로 대조 | 네 칸을 각각 대조 (항목 3개 증가) |
| Spearman p | `scipy.stats.spearmanr` 정확/근사 | `cor.test(method="spearman")` 타이 보정 근사 |

**Spearman p-value와 Shapiro-Wilk p-value는 구현별로 소수 여섯째 자리 수준의 차이가
날 수 있어** 해당 항목만 허용오차 `1e-6`으로 비교한다(나머지는 원본 JSON이 기록한
유효자릿수 그대로 비교). 그 밖의 값은 전부 자릿수까지 일치한다.

## 강건 회귀 병기 (Python, 추가 분석)

보고서의 OLS 두 개(spillover ~ loyalty + activity, factor_diversity ~ loyalty + spillover)를 Huber M-추정·중위수 분위회귀·Cook's D 상위 5개 제외 OLS로 다시 적합한 결과는 `../ROBUST_REGRESSION_V7.md`·`../robust_regression_v7.json`(`../robust_regression_v7.py`)에 있다. 라이브·동결 모두 계수 부호와 유의성(p<0.05)이 네 방법에서 같다.

## 부트스트랩 신뢰구간 (Python, 추가 분석)

이 패키지의 238개 항목은 점추정을 재현한다. 판별타당도 r(0.493 vs 동결 0.638)에 표본 변동 폭을 붙인 팬덤 부트스트랩(B=2,000)과 코퍼스 축소 반복(R=1,000)은 `../bootstrap_ci_v7.py`가 만들고 결과는 `../BOOTSTRAP_CI_V7.md`·`../bootstrap_ci_v7.json`에 있다. R 쪽 `plots.R`에 CI 띠를 넣는 일은 아직 하지 않았다.

## 코퍼스 트랙 구분

이 프로젝트에는 두 트랙이 공존하며, `load_scores()`의 인자로 구분한다.

- `load_scores("live")` — `fandom_scores_live_reference_v7.json`. 매 라운드 재계산되는
  라이브 참고용 점수(10,020건 코퍼스). 보고서 2장·2.1·2.2·4장이 참조한다.
- `load_scores("frozen")` — `fandom_scores_v6.json`. v7-40 실루엣 게이트 동결
  스냅샷(7,350건). 보고서 3·5·6장과 7.4절 outcome 지표가 참조한다.

7.4절은 **MCI(라이브)** 와 **outcome 지표(동결)** 를 대조하는 구조라 시점이 섞여 있다.
보고서 본문도 이 한계를 먼저 밝히고 있으며, 이 코드는 같은 조합을 그대로 쓴다.

## 재현 과정에서 발견한 문서-데이터 불일치 2건

두 건 모두 코드가 실행 시 별도 블록으로 출력한다.

**① 3.8절 검증② 본문 서술.** 본문은 "미디어 키워드가 등장한 토픽은 T0 한 곳(3개)과
T1 한 곳(0개)뿐이었고, 나머지 7개 토픽은 0건"이라고 서술한다. 원본
`k9_validation_v7.json` 기준으로는:

- **K=9**: T0(드라마·유튜브·영화)와 **T3(출연·예능·방송)** 두 곳. T3의 상위 10단어는
  `출연·예능·출연해·mbc·무대·방송·프로그램·에서·함께·가수`로 사실상 "방송출연" 토픽이다.
- **K=8**: T0(4개)에 더해 **T3(출연·예능)**, **T4(유튜브)** 까지 세 곳.

본문 서술과 데이터가 어긋난다. 다만 **결론(K=8 골격 유지)은 바뀌지 않는다** — 검증①
(K=9 합성순위합 13 > K=8 9)과 검증③(T0 단독 분리는 M=6부터 가능하나 실루엣이
0.099→0.081로 하락)이 독립적으로 같은 결론을 지지하기 때문이다.

**② 7.4절 본문 값과 아카이브 JSON 값의 드리프트.**

| 항목 | 재현값 | 보고서 본문 | 아카이브 JSON |
|---|---|---|---|
| MCI × 멤버수 r | −0.7280 | −0.728 | −0.7489 |
| 원시 MCI × 충성도 r | −0.3849 | −0.385 | −0.3932 |
| 원시 MCI × 충성도 R² | 0.1481 | 0.148 | 0.1546 |
| MCI_excess 최고 R² | 0.0457 | 0.0457 | 0.0357 |

`data/member_mention_pilot_v7.json`에서 재계산하면 **보고서 본문 표와 전부 일치**하고
`member_pilot_mci_correlation_v7.json`과는 어긋난다. 두 파일의 시점이 다르기 때문이다.
`member_pilot_mci_correlation_v7.json`은 자체 `caveat_temporal_mismatch` 필드대로 **v7 55
시점 라이브 코퍼스(8,981건)** MCI로 계산된 이전 시점 산출물이고,
`member_mention_pilot_v7.json`은 최종 코퍼스 10,020건 기준이다(저장소
`data/v7_final/member_mention_index_v7.json`과 45개 그룹 전부 값이 같고 키 이름만
`mci_pilot`/`mci_index`로 다르다. 그룹별 `total_group_bullets`도 최종 라이브 점수의
`activity`와 45/45 일치). 즉 보고서 본문 표가 최종 코퍼스 값이고, JSON이 더 이른 시점이다.
결론(MCI는 그룹 outcome을 유의하게 설명하지 못한다 — 원시 최고 R² 15% 안팎, 멤버 수
통제 후 5% 미만)은 두 시점 모두 동일하다.

## 한계

1. **3.8절은 LDA를 다시 돌리지 않는다.** perplexity·coherence·stability는 원본
   `run_lda_v6.py`와 동일한 코퍼스·토크나이저·벡터라이저를 요구하는데 그 파일이
   아카이브에 없다. 이 코드는 원본이 기록한 4개 지표값에서 **합성순위 규칙과 결론
   도출 과정**을 재현한다.
2. **2.1·2.2절은 그 반대로 원자료에서 완전 재계산한다.** 100개 팬덤 점수가 그대로
   남아 있어 상관·회귀·영향점·LOO를 전부 처음부터 산출한다.
3. **인과가 아니라 연관이다.** 2.1절의 "활동량 통제 시 충성도 계수 부호 반전"은 관측
   데이터의 구조이지 인과 효과의 추정이 아니다.
4. `chisq.test()`가 "Chi-squared approximation may be incorrect" 경고를 낸다 — 2×2 표의
   기댓값 하나가 2.64로 5 미만이기 때문이다. 보고서도 같은 표에 같은 검정을 적용했고,
   이 경고 자체가 4분면 분류의 셀 하나가 희소하다는 사실을 그대로 보여준다.
