# 팬덤100 LDA v7 — 통계적 검증 재현 (R)

「팬덤100_LDA_v7_보고서」(114쪽)가 보고하는 통계적 검증을 원본 JSON에서 다시 계산해
대조하는 R 코드다. **보고서 수치가 재현되는지 확인하는 것이 목적**이며, 새 분석을
만드는 것이 아니다.

## 실행

```bash
Rscript RUN_ALL.R          # 전체: 패키지 설치 → 검증 238개 → 플롯 7종
cd R && Rscript verify_all.R    # 검증만 (Rscript 전용)
cd R && Rscript plots.R         # 플롯만 (Rscript 전용)
```

RStudio에서는 `RUN_ALL.R` 을 열고 **Source(Ctrl+Shift+S)**. Run(Ctrl+Enter)은 한 줄만
실행한다.

정상 출력은 `합계 238 238 0` 이다. 종료 코드 `0` = 전부 일치, `1` = 불일치.

## 절대 하지 말 것

**대조가 실패했을 때 기댓값(정답지 값)을 고쳐서 통과시키지 말 것.** 이 코드의 존재
이유가 "보고서 값과 다시 계산한 값이 같은가"를 보는 것이다. 불일치는 고칠 버그가
아니라 **보고할 발견**이다. 수치가 어긋나면 어느 쪽이 맞는지 근거를 찾아 사용자에게
알리고, 코드를 조용히 맞추지 않는다.

`data/` 안의 JSON은 원본 아카이브다. **읽기만 한다.** 절대 수정하지 않는다.

## 구조

```
RUN_ALL.R          단일 파일 전체 실행 (RStudio Source 용) — 아래 R/ 과 같은 코드
install_packages.R 패키지 설치만
SETUP_DATA.R       원본 아카이브(폴더/zip)를 자동 탐색해 필요한 JSON 7개만 data/ 에 복사(읽기 전용)
START.bat          더블클릭 원클릭 실행: SETUP_DATA.R → RUN_ALL.R (R만 있으면 됨. 원본 폴더 드래그 가능)
data/              원본 JSON 8개 (읽기 전용)
R/                 절별 스크립트 (Rscript 전용 — Source 버튼으로는 안 됨)
  common.R         로더 · Fisher z CI · OLS 요약 · 영향점 · 대조 기록기(ck)
  s01_positioning_correlation.R   보고서 2.1절 (78개 대조)
  s02_axis3d_independence.R       보고서 2.2절 (80개)
  s03_k9_validation.R             보고서 3.8절 (45개)
  s04_mci_explanatory_power.R     보고서 7.4절 (35개)
  verify_all.R     네 절 묶어 실행 + 총괄 요약
  plots.R          진단 플롯 7종 (ggplot2)
outputs/           산출물 — plots/*.png, verify_summary.txt
```

`RUN_ALL.R` 의 플롯 코드와 `R/plots.R` 은 **같은 코드**다(전자에서 뽑아 생성).
한쪽만 고치면 어긋난다 — 플롯을 수정했으면 양쪽을 맞추고, 두 경로가 만든 PNG가
동일한지 확인할 것.

## 이 프로젝트에서 반드시 알아야 할 것

### 1. 코퍼스 트랙이 둘이다 (가장 흔한 실수)

| 트랙 | 파일 | 규모 | 참조하는 절 |
|---|---|---|---|
| 라이브 | `fandom_scores_live_reference_v7.json` | 10,020건 | 2장·2.1·2.2·4장 |
| 동결(v7-40) | `fandom_scores_v6.json` | 7,350건 | 3·5·6장, 7.4절 outcome |

`load_scores("live")` / `load_scores("frozen")` 로 구분한다. **섞으면 값이 전부
달라진다.** 7.4절은 MCI(라이브)와 outcome(동결)을 대조하는 구조라 원래부터 시점이
섞여 있으며, 보고서 본문도 이 한계를 먼저 밝힌다 — 의도된 조합이므로 "고치지" 말 것.

### 2. 이미 발견해 기록한 문서-데이터 불일치 2건

실행하면 별도 블록으로 출력된다. **버그가 아니라 의도적으로 남긴 기록**이다.

- **3.8절 검증② 본문 서술.** 본문은 미디어 키워드 보유 토픽이 "T0 한 곳뿐"이라
  서술하지만, 원본 `k9_validation_v7.json` 기준 K=9는 T0·T3 두 곳, K=8은 T0·T3·T4
  세 곳이다. 결론(K=8 유지)은 검증①·③이 독립적으로 뒷받침하므로 바뀌지 않는다.
- **7.4절 드리프트.** 아카이브 입력에서 재계산하면 보고서 본문 표 24개 값과 전부
  일치하고, 같은 아카이브의 `member_pilot_mci_correlation_v7.json` 과는 어긋난다.
  그 JSON이 보고서 작성 이후 갱신된 코퍼스로 다시 계산된 별개 시점 산출물이다.
  **7.4절의 정답지는 보고서 본문**이며, JSON 값은 드리프트로만 기록한다.

### 3. 플롯 규칙 (ggplot2)

- 공통 테마 `theme_fandom()` 하나를 7장이 공유한다. 개별 그림에서 색·글꼴을 새로
  정하지 말고 테마와 팔레트 상수(`S1` 파랑 / `S2` 주황 / `CRIT` 빨강 / `GOOD` 초록)를
  쓴다.
- 패널 결합: 축 이름이 패널마다 **같으면** `facet_wrap()`, **다르면** `patchwork`
  (`p1 + p2`). fig5는 패널마다 x·y 이름이 달라 facet을 쓸 수 없다 — 한 번 facet으로
  바꿨다가 축 이름이 전부 사라진 적이 있다.
- 점 라벨은 `ggrepel` 이 배치한다. 단 **ggrepel은 같은 레이어의 점만 피하고 회귀선이나
  다른 레이어의 주석은 모른다.** fig1은 그래서 (1) 잔차 부호 방향으로 라벨을 미리 밀고
  (2) `xlim`/`ylim` 으로 라벨 영역을 묶어 모서리 주석을 비켜 간다.
- 플롯에 찍는 수치는 **그 자리에서 다시 계산한다.** 상수를 박아 넣지 않는다
  (fig1의 4분면 도수 7·17·4·72, 카이제곱 χ²=8.3439 포함).
- **플롯을 고쳤으면 PNG를 실제로 열어서 눈으로 확인할 것.** 라벨 겹침·범례가 막대를
  가리는 문제는 코드만 읽어서는 보이지 않는다. 실제로 이 방식으로 다섯 군데를 잡았다.

### 4. R 코드 작성 시 주의

- **한글을 변수명·리스트 이름으로 쓰지 말 것.** 문자열 리터럴 안에서만 쓴다.
  `list(원시MCI = x)` 는 `Rscript` 로는 통과하지만 `source()`(= RStudio Source 버튼)
  에서 파싱 실패한다. 반드시 `list("원시MCI" = x)` 로 쓴다. 실제로 겪은 버그다.
- **UTF-8 BOM을 붙이지 말 것.** 비-UTF8 로케일에서 `invalid multibyte character in
  parser` 로 파싱이 깨진다.
- `RUN_ALL.R` 은 **자기 완결형**이어야 한다. `R/` 의 어떤 파일도 `source()` 하지
  않는다 — 그게 RStudio Source 버튼으로 돌아가는 유일한 파일인 이유다.
- `R/` 의 파일들은 `commandArgs("--file=")` 로 `common.R` 을 찾으므로 `Rscript`
  전용이다. 이걸 RStudio에서 쓰게 만들려 하지 말 것 — 그 용도가 `RUN_ALL.R` 이다.

### 5. 환경

- 사용자 환경: **Windows** + RStudio. 한글 폰트는 맑은 고딕.
  `png()` 기본 장치가 R 4.1 이후 Windows에서 cairo이므로 `windowsFonts()` 별칭이
  통하지 않는다 — `family` 에 실제 이름 `"Malgun Gothic"` 을 넘긴다(cairo·GDI 양쪽 동작).
- 필수 패키지: `jsonlite` `car` `ggplot2` `ggrepel` `patchwork` (선택: `broom`).
  `RUN_ALL.R` [1/6] 단계가 자동 설치한다.
- 폰트가 없어도 **238개 대조 결과에는 영향이 없다** — 그림 글자만 달라진다.
- **R이 이미 UTF-8 로케일이면 `Sys.setlocale("LC_CTYPE", "Korean")` 을 호출하지 말 것.**
  이 PC(`Programming`)의 R 4.5.3은 `Korean_Korea.utf8`(코드페이지 65001)로 뜬다. 여기서
  "Korean"(CP949)으로 바꾸면 `Rscript` 가 그 줄 이후의 한글 리터럴 파싱에 실패하고
  (`unexpected symbol in "cat(...`), 한글 경로의 `outputs/` 파일을 못 열며, 7.4절
  한글 키 비교가 1건 어긋나 `238 237 1` 이 나온다. `RUN_ALL.R`·`R/plots.R` 은
  `!isTRUE(l10n_info()$"UTF-8")` 일 때만 로케일을 바꾸도록 되어 있다. 실제로 겪은 버그다.

## 참고: 동봉 Python 구현

같은 검증을 Python(numpy·scipy·matplotlib)으로도 구현했고 **235개 전부 일치**한다.
대조 항목 수 차이(238 vs 235)는 카이제곱 4분면 표를 R이 네 칸으로, Python이 한 항목으로
대조하기 때문이며 검증 내용은 같다. 두 언어의 값이 일치하는지까지가 검증 범위다.

Spearman p-value와 Shapiro-Wilk p-value만 구현별로 소수 여섯째 자리 차이가 날 수 있어
해당 항목은 허용오차 `1e-6` 으로 비교한다. 나머지는 원본 JSON의 유효자릿수 그대로
비교한다.

## 알려진 한계

**3.8절은 LDA를 다시 돌리지 않는다.** perplexity·coherence·stability는 원본
`run_lda_v6.py` 와 동일한 코퍼스·토크나이저·벡터라이저를 요구한다. 이 코드는 원본이
기록한 4개 지표값에서 **합성순위 규칙과 결론 도출 과정**을 재현한다 — 즉 "지표값이
주어졌을 때 K=8이 채택되는가"까지다.

> `run_lda_v6.py` 는 아카이브 zip에는 없지만 상위 프로젝트 폴더
> (`Desktop\Data Project\문화체육관광\run_lda_v6.py`)에 있다. 이걸 쓰면 3.8절도
> 완전 재현으로 올릴 수 있다 — 다만 토크나이저·코퍼스 원본이 함께 필요하다.
