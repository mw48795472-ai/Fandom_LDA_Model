# =============================================================================
#  팬덤100 LDA v7 — 통계적 검증 전체 실행 (R 단일 파일)
# =============================================================================
#
#  【실행 방법】
#    RStudio에서 이 파일을 열고  Ctrl + Shift + S  (또는 우측 상단 Source 버튼).
#    그게 전부입니다. 패키지 설치부터 그림 저장까지 한 번에 진행됩니다.
#
#    ※ Run(Ctrl+Enter)은 '커서가 있는 줄만' 실행합니다. 전체 실행은 Source 입니다.
#    ※ 터미널에서는  Rscript RUN_ALL.R
#
#  【진행 순서】
#    [1/6] 패키지 설치 — jsonlite, car, ggplot2, ggrepel, patchwork 자동 설치
#    [2/6] 패키지 로드 + 한글 폰트 설정
#    [3/6] 데이터 탐색 및 로딩 (data/ 폴더 자동 탐색)
#    [4/6] 통계 검증 4절 — 보고서 2.1 · 2.2 · 3.8 · 7.4
#    [5/6] 진단 플롯 7종 (ggplot2) — RStudio Plots 창 + PNG 동시 출력
#    [6/6] 총괄 요약
#
#  【Plots 창에서 그림 보기】
#    Source 하면 7장이 차례로 Plots 창에 그려집니다. 마지막 그림만 보이므로
#    창 왼쪽 위 화살표(← →)로 앞 그림을 넘겨 보세요.
#      · 한 장씩 멈추며 보기 → 아래 [5/6]의 PAUSE_BETWEEN_PLOTS 를 TRUE 로
#      · 특정 그림만 다시 보기 → 실행 후 콘솔에  FIGS$fig4_influence_R
#      · 크게 보기 → Plots 창의 Zoom 버튼
#    그림은 전부 ggplot 객체라 콘솔에서 바로 고쳐 볼 수 있습니다. 예:
#      FIGS$fig1_positioning_scatter_R + labs(title = "내 제목")
#
#  【필요한 것】
#    이 파일과 같은 폴더에 data/ 폴더가 있어야 합니다.
#      RUN_ALL.R
#      data/  ├ fandom_scores_live_reference_v7.json
#             ├ fandom_scores_v6.json
#             ├ member_mention_pilot_v7.json
#             ├ positioning_map_correlation_live_v7.json
#             ├ chart3d_correlation_live_v7.json
#             ├ k9_validation_v7.json
#             └ member_pilot_mci_correlation_v7.json
#    폴더를 옮겼더라도 작업 디렉터리 아래에 있으면 자동으로 찾습니다.
#
#  【한글이 깨져 보인다면】
#    이 파일은 UTF-8 로 저장돼 있습니다. RStudio에서 주석이 '???' 나 '占쏙옙' 으로
#    보이면 File > Reopen with Encoding... > UTF-8 로 다시 연 뒤 Source 하세요.
#    (R 4.2 이상 Windows는 UTF-8이 기본이라 대개 그냥 열립니다.)
#    그림의 한글만 네모로 나오면 맑은 고딕 문제입니다 — [2/6]이 출력하는
#    '폰트:' 줄을 확인하세요. 계산 결과 238개 대조에는 영향이 없습니다.
#
#  【결과물】
#    outputs/plots/*.png   진단 플롯 7장
#    outputs/*.txt         절별 요약
#    콘솔                  절별 대조표 + 총괄 요약 (238개 항목 전부 일치해야 정상)
#
#  기준 자료: 팬덤100_LDA_v7_보고서(114쪽) · 팬덤100_LDA_v7_데이터아카이브
# =============================================================================

rm(list = ls())
t_start <- Sys.time()
cat("\n", strrep("=", 78), "\n", sep = "")
cat("  팬덤100 LDA v7 — 통계적 검증 전체 실행\n")
cat(strrep("=", 78), "\n\n", sep = "")


# =============================================================================
# [1/6] 패키지 설치
# =============================================================================
cat("[1/6] 패키지 확인 및 설치\n")

# jsonlite : JSON 로딩          car       : vif()
# ggplot2  : 진단 플롯 7종      ggrepel   : 겹치지 않는 점 라벨
# patchwork: 여러 패널 합치기
REQUIRED <- c("jsonlite", "car", "ggplot2", "ggrepel", "patchwork")

# CRAN 미러를 미리 지정해 둔다 — 지정하지 않으면 설치 시 미러 선택 창이 떠서
# Source 실행이 중간에 멈춘다.
if (is.null(getOption("repos")) || is.na(getOption("repos")["CRAN"]) ||
    getOption("repos")["CRAN"] == "@CRAN@") {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
}

# 쓰기 가능한 라이브러리 경로를 미리 확보한다 — 없으면 Windows에서
# "개인 라이브러리를 만들까요?" 모달이 떠서 Source 실행이 멈춘다.
ensure_libpath <- function() {
  if (any(file.access(.libPaths(), 2) == 0)) return(invisible(NULL))
  personal <- Sys.getenv("R_LIBS_USER")
  if (!nzchar(personal) || personal == "NULL")
    personal <- file.path(path.expand("~"), "R",
                          paste0(R.version$platform, "-library"),
                          paste(R.version$major,
                                strsplit(R.version$minor, ".", fixed = TRUE)[[1]][1],
                                sep = "."))
  dir.create(personal, recursive = TRUE, showWarnings = FALSE)
  if (dir.exists(personal)) {
    .libPaths(c(personal, .libPaths()))
    cat("      개인 라이브러리 사용:", personal, "\n")
  }
}

have <- vapply(REQUIRED, requireNamespace, logical(1), quietly = TRUE)
if (any(!have)) {
  miss <- REQUIRED[!have]
  cat("      설치 필요:", paste(miss, collapse = ", "), "\n")
  cat("      CRAN에서 내려받는 중입니다. car와 ggplot2는 의존 패키지가 많아\n")
  cat("      수 분 걸릴 수 있습니다 — 아래 진행 표시가 멈춘 게 아닙니다.\n\n")
  ensure_libpath()
  # quiet = FALSE: 설치 로그를 그대로 보여 준다. 조용히 두면 멈춘 것처럼 보인다.
  try(install.packages(miss, quiet = FALSE), silent = TRUE)
  cat("\n")
  have <- vapply(REQUIRED, requireNamespace, logical(1), quietly = TRUE)
}

if (any(!have)) {
  cat("\n")
  cat("  [중단] 다음 패키지를 설치하지 못했습니다:",
      paste(REQUIRED[!have], collapse = ", "), "\n")
  cat("  인터넷이 막힌 환경이라면 아래를 직접 실행해 보세요.\n")
  cat('    install.packages(c("jsonlite","car"))\n')
  cat("  Linux(Debian/Ubuntu)에서는 apt로도 됩니다:\n")
  cat("    sudo apt-get install -y r-cran-jsonlite r-cran-car\n\n")
  stop("필수 패키지 없음 — 위 안내를 참고하세요.", call. = FALSE)
}
cat("      완료 —", paste(sprintf("%s %s", REQUIRED,
    vapply(REQUIRED, function(p) as.character(utils::packageVersion(p)), "")),
    collapse = " · "), "\n\n")


# =============================================================================
# [2/6] 패키지 로드 + 한글 폰트
# =============================================================================
cat("[2/6] 패키지 로드 및 한글 폰트 설정\n")

suppressPackageStartupMessages({
  library(jsonlite)
  library(car)
  library(ggplot2)
  library(ggrepel)
  library(patchwork)
})

# ggplot2 3.4 미만은 linewidth 인자를 모른다 — 테마가 통째로 실패하므로 먼저 막는다
if (utils::packageVersion("ggplot2") < "3.4.0") {
  stop(sprintf(paste("ggplot2 %s 이 설치돼 있습니다. 3.4.0 이상이 필요합니다.\n",
                     "  install.packages(\"ggplot2\") 로 업데이트한 뒤 다시 실행하세요."),
               utils::packageVersion("ggplot2")), call. = FALSE)
}

# --- 한글 폰트 -----------------------------------------------------------
# 운영체제마다 쓰는 폰트가 달라, 설치돼 있는 것 중에서 고른다.
# 실패해도 계산에는 영향이 없고 그림의 한글만 네모로 보인다.
KO_FONT <- ""          # 그래픽 장치에 넘길 family 이름
PNG_TYPE <- NULL       # Windows에서 cairo를 쓸지 여부

setup_korean_font <- function() {
  os <- Sys.info()[["sysname"]]

  if (identical(.Platform$OS.type, "windows")) {
    # Windows: 맑은 고딕(Windows 7 이후 기본 탑재)
    #
    # 장치별로 폰트를 찾는 방식이 달라 두 경로를 모두 준비한다.
    #  · png(type = "cairo") — R 4.1 이후 Windows 기본값. 폰트를 시스템 이름
    #    "Malgun Gothic" 으로 직접 찾으므로 windowsFonts() 별칭은 통하지 않는다.
    #  · png(type = "windows") / RStudio Plots 창 — GDI face 이름을 그대로 받으므로
    #    "Malgun Gothic" 이 역시 그대로 통한다.
    # 따라서 별칭("KO")이 아니라 실제 이름을 family 로 넘기고, 별칭 등록은
    # 혹시 옛 코드가 "KO" 를 쓸 때를 대비한 보험으로만 남긴다.
    tryCatch({
      wf    <- get("windowsFonts", envir = asNamespace("grDevices"))
      wfont <- get("windowsFont",  envir = asNamespace("grDevices"))
      do.call(wf, stats::setNames(list(wfont("Malgun Gothic")), "KO"))
    }, error = function(e) NULL)
    KO_FONT <<- "Malgun Gothic"
    return(invisible("Malgun Gothic (Windows)"))

  } else if (identical(os, "Darwin")) {
    KO_FONT <<- "AppleGothic"
    return(invisible("AppleGothic (macOS)"))

  } else {
    # Linux: fc-list 로 설치된 한글 폰트를 찾는다
    cand <- c("NanumGothic", "NanumBarunGothic",
              "Noto Sans CJK KR", "Noto Sans CJK JP")
    hit <- tryCatch({
      fams <- system("fc-list :lang=ko family", intern = TRUE, ignore.stderr = TRUE)
      fams <- trimws(unique(unlist(strsplit(paste(fams, collapse = ","), ","))))
      h <- cand[cand %in% fams]
      if (length(h)) h[1] else NA_character_
    }, error = function(e) NA_character_)
    if (!is.na(hit)) { KO_FONT <<- hit; return(invisible(paste0(hit, " (Linux)"))) }
    KO_FONT <<- ""
    return(invisible("기본 폰트 — 한글이 네모로 보이면 fonts-nanum 설치 권장"))
  }
}
font_note <- setup_korean_font()

# 한글 로케일(Windows에서 한글 문자열 폭 계산에 필요)
invisible(tryCatch(
  if (identical(.Platform$OS.type, "windows") && !isTRUE(l10n_info()$`UTF-8`)) Sys.setlocale("LC_CTYPE", "Korean")
  else if (!isTRUE(l10n_info()$`UTF-8`)) {
    for (lc in c("C.UTF-8", "en_US.UTF-8", "ko_KR.UTF-8"))
      if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", lc)))) break
  }, error = function(e) NULL))

cat("      폰트:", font_note, "\n")
cat("      R:", R.version.string, "|", Sys.info()[["sysname"]], "\n\n")


# =============================================================================
# [3/6] 데이터 탐색 및 로딩
# =============================================================================
cat("[3/6] 데이터 폴더 탐색\n")

MARKER <- "fandom_scores_live_reference_v7.json"   # data/ 판별용 기준 파일

# 이 스크립트가 있는 폴더를 알아낸다 (Rscript / RStudio Source / source() 모두 대응)
script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)                      # Rscript
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f) && nzchar(f[1]))
    return(tryCatch(dirname(normalizePath(f[1])), error = function(e) NA_character_))

  for (i in seq_len(sys.nframe())) {                          # source()
    of <- tryCatch(sys.frame(i)$ofile, error = function(e) NULL)
    if (!is.null(of))
      return(tryCatch(dirname(normalizePath(of)), error = function(e) NA_character_))
  }

  if (requireNamespace("rstudioapi", quietly = TRUE)) {       # RStudio Source 버튼
    p <- tryCatch({
      if (rstudioapi::isAvailable()) rstudioapi::getSourceEditorContext()$path else ""
    }, error = function(e) "")
    if (nzchar(p))
      return(tryCatch(dirname(normalizePath(p)), error = function(e) NA_character_))
  }
  NA_character_
}

# 저장소 안에서 실행할 때: data/ 에 없는 JSON 은 저장소 원본 data/v7_final 에서 복사해 채운다.
# (원본과 바이트 단위로 같은 파일을 두 곳에 두지 않기 위해 이 패키지의 data/ 에는
#  저장소에 없는 member_mention_pilot_v7.json 만 커밋되어 있다. 나머지는 여기서 채워진다.)
REPO_MAP <- c(fandom_scores_live_reference_v7.json      = "fandom_scores_live_reference_v7.json",
              fandom_scores_v6.json                      = "fandom_scores_v6.json",
              positioning_map_correlation_live_v7.json   = "positioning_map_correlation_live_v7.json",
              chart3d_correlation_live_v7.json           = "chart3d_correlation_live_v7.json",
              k9_validation_v7.json                      = "k9_validation_v7.json",
              member_pilot_mci_correlation_v7.json       = "member_pilot_mci_correlation_v7.json",
              lda_v6_diagnostics.json                    = "lda_v6_diagnostics_frozen_v7_40.json")
fill_data_from_repo <- function() {
  sd <- script_dir(); if (is.na(sd)) return(invisible(FALSE))
  repo_data <- file.path(sd, "..", "..", "data", "v7_final")
  if (!dir.exists(repo_data)) return(invisible(FALSE))
  dst <- file.path(sd, "data"); dir.create(dst, showWarnings = FALSE)
  n <- 0
  for (to in names(REPO_MAP)) {
    from <- file.path(repo_data, REPO_MAP[[to]])
    if (!file.exists(file.path(dst, to)) && file.exists(from)) { file.copy(from, file.path(dst, to)); n <- n + 1 }
  }
  if (n > 0) cat("      저장소 data/v7_final 에서", n, "개 파일을 data/ 로 복사\n")
  invisible(TRUE)
}
fill_data_from_repo()

find_data_dir <- function() {
  sd <- script_dir()
  cands <- character(0)
  if (!is.na(sd)) cands <- c(cands, file.path(sd, "data"), file.path(sd, "..", "data"), sd)
  cands <- c(cands,
             file.path(getwd(), "data"),
             file.path(getwd(), "fandom_stats_r", "data"),
             getwd())
  for (d in cands) {
    if (!is.na(d) && file.exists(file.path(d, MARKER)))
      return(normalizePath(d, winslash = "/"))
  }
  # 마지막 수단: 작업 디렉터리 아래를 훑는다
  hits <- list.files(getwd(), pattern = paste0("^", MARKER, "$"),
                     recursive = TRUE, full.names = TRUE)
  if (length(hits)) return(normalizePath(dirname(hits[1]), winslash = "/"))
  NA_character_
}

DATA_DIR <- find_data_dir()
if (is.na(DATA_DIR)) {
  cat("\n  [중단] data 폴더를 찾지 못했습니다.\n")
  cat("  이 스크립트와 같은 위치에 data 폴더가 있어야 합니다:\n")
  cat("     RUN_ALL.R\n     data/", MARKER, "\n", sep = "")
  cat("  현재 작업 디렉터리:", getwd(), "\n")
  cat("  RStudio라면 Session > Set Working Directory > To Source File Location 을\n")
  cat("  실행한 뒤 다시 Source 해 보세요.\n\n")
  stop("데이터 폴더 없음", call. = FALSE)
}

# 출력 폴더는 스크립트 옆에 만든다(없으면 작업 디렉터리)
OUT_BASE <- { sd <- script_dir(); if (is.na(sd)) getwd() else sd }
OUT_DIR  <- file.path(OUT_BASE, "outputs")
PLOT_DIR <- file.path(OUT_DIR, "plots")
dir.create(PLOT_DIR, recursive = TRUE, showWarnings = FALSE)

load_json <- function(name) fromJSON(file.path(DATA_DIR, name), simplifyVector = FALSE)

#' 팬덤 점수 스냅샷을 data.frame으로.
#'  "live"   = fandom_scores_live_reference_v7.json (10,020건 라이브 코퍼스)
#'  "frozen" = fandom_scores_v6.json (v7-40 실루엣 게이트 동결 스냅샷, 7,350건)
load_scores <- function(track = "live") {
  raw <- load_json(switch(track,
    live   = "fandom_scores_live_reference_v7.json",
    frozen = "fandom_scores_v6.json",
    stop("track must be 'live' or 'frozen'")))
  data.frame(
    fandom           = vapply(raw, function(x) x$fandom, character(1)),
    category         = vapply(raw, function(x) if (is.null(x$category)) "" else x$category, character(1)),
    loyalty_score    = vapply(raw, function(x) as.numeric(x$loyalty_score), numeric(1)),
    spillover_score  = vapply(raw, function(x) as.numeric(x$spillover_score), numeric(1)),
    factor_diversity = vapply(raw, function(x) as.numeric(x$factor_diversity), numeric(1)),
    coverage_index   = vapply(raw, function(x) as.numeric(x$coverage_index), numeric(1)),
    activity         = vapply(raw, function(x) as.numeric(x$activity), numeric(1)),
    stringsAsFactors = FALSE)
}

NEEDED <- c(MARKER, "fandom_scores_v6.json", "member_mention_pilot_v7.json",
            "positioning_map_correlation_live_v7.json",
            "chart3d_correlation_live_v7.json", "k9_validation_v7.json",
            "member_pilot_mci_correlation_v7.json")
absent <- NEEDED[!file.exists(file.path(DATA_DIR, NEEDED))]
if (length(absent)) {
  cat("\n  [중단] data 폴더에 다음 파일이 없습니다:\n    ",
      paste(absent, collapse = "\n     "), "\n\n", sep = "")
  stop("데이터 파일 누락", call. = FALSE)
}

DF_LIVE <- load_scores("live")
cat("      data:", DATA_DIR, "\n")
cat("      라이브 스냅샷", nrow(DF_LIVE), "개 팬덤 · 근거문장 합계",
    format(sum(DF_LIVE$activity), big.mark = ","), "건\n")
cat("      출력:", normalizePath(OUT_DIR, winslash = "/", mustWork = FALSE), "\n\n")


# =============================================================================
#  공용 통계 헬퍼
# =============================================================================
# Pearson r의 95% 신뢰구간 (Fisher z 변환)
pearson_ci95 <- function(r, n) {
  z <- atanh(r); se <- 1 / sqrt(n - 3)
  tanh(c(z - qnorm(0.975) * se, z + qnorm(0.975) * se))
}

# lm() 결과에서 보고서가 표로 실은 값들을 뽑아낸다
ols_summary <- function(fit) {
  s <- summary(fit); co <- s$coefficients
  list(names = rownames(co), coef = unname(co[, "Estimate"]),
       se = unname(co[, "Std. Error"]), t = unname(co[, "t value"]),
       p = unname(co[, "Pr(>|t|)"]),
       r_squared = s$r.squared, adj_r_squared = s$adj.r.squared,
       f_statistic = unname(s$fstatistic[1]),
       f_pvalue = unname(pf(s$fstatistic[1], s$fstatistic[2], s$fstatistic[3],
                            lower.tail = FALSE)))
}

# 표준화 잔차 · Cook's distance · leverage — R 표준 함수를 그대로 쓴다
influence_stats <- function(fit)
  list(std_resid = rstandard(fit), cooks_d = cooks.distance(fit),
       leverage = hatvalues(fit))

# --- 재현값 / 원본값 대조 기록기 -----------------------------------------
Checker <- function(title) {
  e <- new.env(parent = emptyenv()); e$title <- title; e$rows <- list(); e
}
.decimals <- function(x) {
  s <- format(x, scientific = FALSE, digits = 15)
  if (!grepl("\\.", s)) return(0L)
  nchar(sub("0+$", "", strsplit(s, "\\.")[[1]][2]))
}
ck <- function(env, label, got, want, tol = NULL, note = "") {
  ok <- NA
  if (!is.null(want)) {
    if (is.numeric(got) && is.numeric(want) && length(got) == 1 && length(want) == 1) {
      ok <- if (is.null(tol)) isTRUE(round(got, .decimals(want)) == round(want, .decimals(want)))
            else isTRUE(abs(got - want) <= tol)
    } else ok <- isTRUE(all(got == want) && length(got) == length(want))
  }
  env$rows[[length(env$rows) + 1]] <-
    list(label = label, got = got, want = want, ok = ok, note = note)
  invisible(ok)
}
.padr <- function(s, w) paste0(s, strrep(" ", max(0, w - nchar(s, type = "width"))))
.padl <- function(s, w) paste0(strrep(" ", max(0, w - nchar(s, type = "width"))), s)
.fmt <- function(v) {
  if (is.null(v)) return("—")
  if (is.numeric(v) && length(v) == 1) {
    if (v != 0 && abs(v) < 1e-4) return(formatC(v, format = "e", digits = 3))
    return(formatC(v, format = "g", digits = 6))
  }
  if (length(v) > 1) return(paste0("<", length(v), "개 값>"))
  as.character(v)
}
ck_report <- function(env) {
  labs <- vapply(env$rows, function(r) r$label, character(1))
  w <- max(nchar(labs, type = "width")) + 2
  cat(strrep("-", w + 52), "\n", env$title, "\n", strrep("-", w + 52), "\n", sep = "")
  cat(.padr("항목", w), .padl("재현값", 16), .padl("원본값", 16), "\n", sep = "")
  n_ok <- 0; n_tot <- 0
  for (r in env$rows) {
    mark <- if (is.na(r$ok)) "" else if (r$ok) "일치" else "불일치"
    if (!is.na(r$ok)) { n_tot <- n_tot + 1; n_ok <- n_ok + as.integer(r$ok) }
    cat(.padr(r$label, w), .padl(.fmt(r$got), 16), .padl(.fmt(r$want), 16),
        "  ", mark, "\n", sep = "")
    if (nzchar(r$note)) cat(.padr("", w), "  └ ", r$note, "\n", sep = "")
  }
  cat(strrep("-", w + 52), "\n", sep = "")
  cat(sprintf("대조 %d건 중 일치 %d건 / 불일치 %d건\n\n", n_tot, n_ok, n_tot - n_ok))
  invisible(c(ok = n_ok, total = n_tot))
}


# =============================================================================
# [4/6] 통계 검증
# =============================================================================
HIGHLIGHT <- c("BTS", "임영웅", "리센느(RESCENE)")

# --- 2.1절 : 포지셔닝 맵 두 축 상관계수 분석 ---------------------------------
verify_21 <- function(df) {
  truth <- load_json("positioning_map_correlation_live_v7.json"); n <- nrow(df)
  e <- Checker(sprintf("보고서 2.1절 — 포지셔닝 맵 상관계수 분석 및 통계적 검증 (n=%d)", n))
  ck(e, "n", n, truth$n)

  pt <- cor.test(df$loyalty_score, df$spillover_score)
  ci <- pearson_ci95(unname(pt$estimate), n)
  ck(e, "Pearson r", round(unname(pt$estimate), 4), truth$pearson$r)
  ck(e, "Pearson p", pt$p.value, truth$pearson$p_value, tol = 1e-12)
  ck(e, "Pearson 95%CI 하한", round(ci[1], 4), truth$pearson$ci95[[1]])
  ck(e, "Pearson 95%CI 상한", round(ci[2], 4), truth$pearson$ci95[[2]])
  ck(e, "결정계수 R²", round(unname(pt$estimate)^2, 4), truth$pearson$r_squared)

  st <- suppressWarnings(cor.test(df$loyalty_score, df$spillover_score, method = "spearman"))
  ck(e, "Spearman ρ", round(unname(st$estimate), 4), truth$spearman$rho)
  ck(e, "Spearman p", st$p.value, truth$spearman$p_value, tol = 1e-6,
     note = "타이 보정 근사식 차이로 허용오차 1e-6")

  for (k in c("loyalty_score", "spillover_score")) {
    sw <- shapiro.test(df[[k]]); tt <- truth$normality[[k]]
    ck(e, sprintf("Shapiro-Wilk W — %s", k), round(unname(sw$statistic), 4), tt$W)
    ck(e, sprintf("Shapiro-Wilk p — %s", k), sw$p.value, tt$p_value, tol = 1e-6)
    ck(e, sprintf("정규성 유지(α=.05) — %s", k), sw$p.value > 0.05, tt$normal_at_0.05)
  }

  for (pr in list(c("loyalty_score", "loyalty_score_vs_activity"),
                  c("spillover_score", "spillover_score_vs_activity"))) {
    p <- cor.test(df[[pr[1]]], df$activity); tt <- truth$each_score_vs_activity[[pr[2]]]
    ck(e, sprintf("r — %s", pr[2]), round(unname(p$estimate), 4), tt$r)
    ck(e, sprintf("p — %s", pr[2]), p$p.value, tt$p_value, tol = 1e-12)
  }

  fit <- lm(spillover_score ~ loyalty_score + activity, data = df)
  s <- ols_summary(fit); mr <- truth$multiple_regression_spillover_on_loyalty_activity
  ck(e, "다중회귀 R²", round(s$r_squared, 4), mr$r_squared)
  ck(e, "다중회귀 adj R²", round(s$adj_r_squared, 4), mr$adj_r_squared)
  ck(e, "다중회귀 F", round(s$f_statistic, 3), mr$f_statistic)
  ck(e, "다중회귀 F p", s$f_pvalue, mr$f_pvalue, tol = 1e-12)
  jn <- c("intercept", "loyalty_score", "activity")
  for (i in seq_along(jn)) {
    cc <- mr$coefficients[[jn[i]]]; dec <- if (jn[i] == "activity") 6 else 4
    ck(e, sprintf("계수 — %s", jn[i]), round(s$coef[i], dec), cc$coef)
    ck(e, sprintf("SE — %s", jn[i]), round(s$se[i], dec), cc$se)
    ck(e, sprintf("t — %s", jn[i]), round(s$t[i], 3), cc$t)
    ck(e, sprintf("p — %s", jn[i]), s$p[i], cc$p, tol = 1e-12)
  }
  v <- vif(fit)
  for (nm in names(v))
    ck(e, sprintf("VIF — %s (car::vif)", nm), round(unname(v[nm]), 3), mr$vif[[nm]])

  fit1 <- lm(spillover_score ~ loyalty_score, data = df)
  ck(e, "단순회귀 기울기", round(unname(coef(fit1)[2]), 4),
     truth$regression_spillover_on_loyalty$slope)
  ck(e, "단순회귀 절편", round(unname(coef(fit1)[1]), 4),
     truth$regression_spillover_on_loyalty$intercept)
  inf <- influence_stats(fit1); ord <- order(inf$cooks_d, decreasing = TRUE)
  thr <- 4 / n
  ck(e, "Cook's D 임계값 4/n", round(thr, 4), truth$cooks_d_threshold_4_over_n)
  ck(e, "임계값 초과 영향점 수", sum(inf$cooks_d > thr), truth$n_high_influence_points)
  for (rk in 1:5) {
    i <- ord[rk]; tt <- truth$influence_top5[[rk]]
    ck(e, sprintf("영향점%d 팬덤", rk), df$fandom[i], tt$fandom)
    ck(e, sprintf("영향점%d 표준화잔차", rk), round(unname(inf$std_resid[i]), 3), tt$std_residual)
    ck(e, sprintf("영향점%d Cook's D", rk), round(unname(inf$cooks_d[i]), 4), tt$cooks_d)
    ck(e, sprintf("영향점%d leverage", rk), round(unname(inf$leverage[i]), 4), tt$leverage)
  }

  for (f in names(truth$sensitivity_remove_highlighted)) {
    tt <- truth$sensitivity_remove_highlighted[[f]]; sub <- df[df$fandom != f, ]
    p <- cor.test(sub$loyalty_score, sub$spillover_score)
    ck(e, sprintf("민감도 r (제외: %s)", f), round(unname(p$estimate), 4), tt$r_without)
    ck(e, sprintf("민감도 p (제외: %s)", f), p$p.value, tt$p_without, tol = 1e-12)
  }

  r0 <- unname(pt$estimate)
  d <- vapply(seq_len(n), function(i)
    abs(cor(df$loyalty_score[-i], df$spillover_score[-i]) - r0), numeric(1))
  loo <- truth$leave_one_out
  ck(e, "LOO 최대 |Δr|", round(max(d), 4), loo$max_abs_delta_r)
  ck(e, "LOO 최대 변화 팬덤", df$fandom[which.max(d)], loo$max_delta_fandom)
  ck(e, "LOO 평균 |Δr|", round(mean(d), 5), loo$mean_abs_delta_r)

  hl <- df$loyalty_score >= 0.5; hs <- df$spillover_score >= 0.5
  tab <- matrix(c(sum(hl & hs), sum(hl & !hs), sum(!hl & hs), sum(!hl & !hs)),
                nrow = 2, byrow = TRUE)
  cs <- suppressWarnings(chisq.test(tab, correct = TRUE))   # Yates 연속성 보정
  q <- truth$quadrant_chi_square
  ck(e, "4분면 [1,1] 핵심전략", tab[1, 1], q$table[[1]][[1]])
  ck(e, "4분면 [1,2] 내부결속", tab[1, 2], q$table[[1]][[2]])
  ck(e, "4분면 [2,1] 외부견인", tab[2, 1], q$table[[2]][[1]])
  ck(e, "4분면 [2,2] 주변부",   tab[2, 2], q$table[[2]][[2]])
  ck(e, "χ²", round(unname(cs$statistic), 4), q$chi2)
  ck(e, "자유도", unname(cs$parameter), q$dof)
  ck(e, "χ² p", cs$p.value, q$p_value, tol = 1e-12)
  ck(e, "기댓값 [1,1]", round(cs$expected[1, 1], 2), q$expected[[1]][[1]])

  dc <- truth$design_criterion
  ck(e, "판별타당도 |r| < 0.5 충족", abs(r0) < dc$target_abs_r_below, dc$meets_criterion,
     note = sprintf("|r|=%.4f vs 기준 %.1f", abs(r0), dc$target_abs_r_below))
  ck_report(e)
}

# --- 2.2절 : 3D 맵 Z축(팬 요인 다양성) 독립성 검증 ----------------------------
verify_22 <- function(df) {
  truth <- load_json("chart3d_correlation_live_v7.json"); n <- nrow(df)
  e <- Checker(sprintf("보고서 2.2절 — 3D Z축(팬 요인 다양성) 독립성 검증 (n=%d)", n))
  ck(e, "n", n, truth$n)

  prs <- list(loyalty_vs_spillover   = c("loyalty_score", "spillover_score"),
              loyalty_vs_diversity   = c("loyalty_score", "factor_diversity"),
              spillover_vs_diversity = c("spillover_score", "factor_diversity"))
  for (k in names(prs)) {
    a <- df[[prs[[k]][1]]]; b <- df[[prs[[k]][2]]]; tt <- truth$pairwise[[k]]
    pt <- cor.test(a, b); ci <- pearson_ci95(unname(pt$estimate), n)
    st <- suppressWarnings(cor.test(a, b, method = "spearman"))
    ck(e, sprintf("r — %s", k), round(unname(pt$estimate), 4), tt$r)
    ck(e, sprintf("p — %s", k), pt$p.value, tt$p_value, tol = 1e-12)
    ck(e, sprintf("CI하한 — %s", k), round(ci[1], 4), tt$ci95[[1]])
    ck(e, sprintf("CI상한 — %s", k), round(ci[2], 4), tt$ci95[[2]])
    ck(e, sprintf("R² — %s", k), round(unname(pt$estimate)^2, 4), tt$r_squared)
    ck(e, sprintf("ρ — %s", k), round(unname(st$estimate), 4), tt$spearman_rho)
    ck(e, sprintf("ρ p — %s", k), st$p.value, tt$spearman_p, tol = 1e-6)
  }

  for (k in c("loyalty_score", "spillover_score", "factor_diversity")) {
    sw <- shapiro.test(df[[k]]); tt <- truth$normality[[k]]
    ck(e, sprintf("Shapiro-Wilk W — %s", k), round(unname(sw$statistic), 4), tt$W)
    ck(e, sprintf("Shapiro-Wilk p — %s", k), sw$p.value, tt$p_value, tol = 1e-6)
    ck(e, sprintf("정규성 유지(α=.05) — %s", k), sw$p.value > 0.05, tt$normal_at_0.05)
  }

  fit <- lm(factor_diversity ~ loyalty_score + spillover_score, data = df)
  s <- ols_summary(fit); mr <- truth$multiple_regression_diversity_on_loyalty_spillover
  ck(e, "다중회귀 R²", round(s$r_squared, 4), mr$r_squared)
  ck(e, "다중회귀 adj R²", round(s$adj_r_squared, 4), mr$adj_r_squared)
  ck(e, "다중회귀 F", round(s$f_statistic, 3), mr$f_statistic)
  ck(e, "다중회귀 F p", s$f_pvalue, mr$f_pvalue, tol = 1e-12)
  jn <- c("intercept", "loyalty_score", "spillover_score")
  for (i in seq_along(jn)) {
    cc <- mr$coefficients[[jn[i]]]
    ck(e, sprintf("계수 — %s", jn[i]), round(s$coef[i], 4), cc$coef)
    ck(e, sprintf("SE — %s", jn[i]), round(s$se[i], 4), cc$se)
    ck(e, sprintf("t — %s", jn[i]), round(s$t[i], 3), cc$t)
    ck(e, sprintf("p — %s", jn[i]), s$p[i], cc$p, tol = 1e-12)
  }
  v <- vif(fit)
  for (nm in names(v))
    ck(e, sprintf("VIF — %s (car::vif)", nm), round(unname(v[nm]), 3), mr$vif[[nm]])

  inf <- influence_stats(fit); ord <- order(inf$cooks_d, decreasing = TRUE); thr <- 4 / n
  ck(e, "Cook's D 임계값 4/n", round(thr, 4), truth$cooks_d_threshold_4_over_n)
  ck(e, "임계값 초과 영향점 수", sum(inf$cooks_d > thr), truth$n_high_influence_points)
  for (rk in 1:5) {
    i <- ord[rk]; tt <- truth$influence_top5[[rk]]
    ck(e, sprintf("영향점%d 팬덤", rk), df$fandom[i], tt$fandom)
    ck(e, sprintf("영향점%d 표준화잔차", rk), round(unname(inf$std_resid[i]), 3), tt$std_residual)
    ck(e, sprintf("영향점%d Cook's D", rk), round(unname(inf$cooks_d[i]), 4), tt$cooks_d)
    ck(e, sprintf("영향점%d leverage", rk), round(unname(inf$leverage[i]), 4), tt$leverage)
  }

  for (f in names(truth$sensitivity_remove_highlighted)) {
    tt <- truth$sensitivity_remove_highlighted[[f]]; sub <- df[df$fandom != f, ]
    fw <- lm(factor_diversity ~ loyalty_score + spillover_score, data = sub)
    ck(e, sprintf("민감도 충성도계수 (제외: %s)", f),
       round(unname(coef(fw)[2]), 4), tt$loyalty_coef_without)
    ck(e, sprintf("민감도 R² (제외: %s)", f),
       round(summary(fw)$r.squared, 4), tt$r_squared_without)
  }

  base <- unname(coef(fit)[2])
  d <- vapply(seq_len(n), function(i) {
    fw <- lm(factor_diversity ~ loyalty_score + spillover_score, data = df[-i, ])
    abs(unname(coef(fw)[2]) - base)
  }, numeric(1))
  loo <- truth$leave_one_out_loyalty_coef
  ck(e, "LOO 최대 |Δ계수|", round(max(d), 4), loo$max_abs_delta_coef)
  ck(e, "LOO 최대 변화 팬덤", df$fandom[which.max(d)], loo$max_delta_fandom)
  ck(e, "LOO 평균 |Δ계수|", round(mean(d), 5), loo$mean_abs_delta_coef)
  ck_report(e)
}

# --- 3.8절 : K9/F6 제안 검증 -------------------------------------------------
MEDIA_KEYWORDS <- c("예능", "유튜브", "영화", "드라마", "방송", "출연")

verify_38 <- function() {
  truth <- load_json("k9_validation_v7.json")
  e <- Checker("보고서 3.8절 — K9/F6 제안 검증")
  ck(e, "코퍼스 문서 수", truth$corpus_docs, 9614,
     note = "v7 26라운드 시점 = v7 24라운드와 동일 코퍼스")
  ck(e, "어휘 수", truth$vocab_size, 11924)
  ck(e, "기존 K-그리드에 K=9 부재", truth$existing_k_grid_never_tested_k9, TRUE)

  g <- truth$k_grid
  ks   <- vapply(g, function(x) x$k, numeric(1))
  perp <- vapply(g, function(x) x$perplexity, numeric(1))
  coh  <- vapply(g, function(x) x$coherence, numeric(1))
  divv <- vapply(g, function(x) x$diversity, numeric(1))
  stab <- vapply(g, function(x) x$stability, numeric(1))
  want <- vapply(g, function(x) x$composite_rank_sum, numeric(1))

  # 합성순위합: perplexity는 낮을수록, 나머지 셋은 높을수록 상위.
  # 동점은 그리드 등장 순서로 가른다(ties.method="first").
  r_perp <- rank( perp, ties.method = "first")
  r_coh  <- rank(-coh,  ties.method = "first")
  r_div  <- rank(-divv, ties.method = "first")
  r_stab <- rank(-stab, ties.method = "first")
  comp <- r_perp + r_coh + r_div + r_stab

  cat("K-그리드 합성순위 재현 (낮을수록 상위)\n")
  cat(sprintf("  %4s%10s%9s%8s%8s%16s%7s%7s\n",
              "K", "Perp", "Coher", "Div", "Stab", "순위(P/C/D/S)", "합계", "원본"))
  for (i in seq_along(ks))
    cat(sprintf("  %4d%10.1f%9.3f%8.3f%8.3f%16s%7d%7d\n", ks[i], perp[i], coh[i],
                divv[i], stab[i],
                sprintf("%d/%d/%d/%d", r_perp[i], r_coh[i], r_div[i], r_stab[i]),
                comp[i], want[i]))
  cat("\n")

  for (i in seq_along(ks)) ck(e, sprintf("합성순위합 K=%d", ks[i]), comp[i], want[i])
  ck(e, "채택 K (합성순위합 최소)", ks[which.min(comp)], truth$k_grid_winner$k,
     note = "K=9를 후보에 넣어도 채택값은 바뀌지 않는다")
  ck(e, "K=9 합성순위합", comp[which(ks == 9)], 13)
  ck(e, "K=8 합성순위합", comp[which(ks == 8)], 9)
  ck(e, "K=9가 K=8보다 상위인가", comp[which(ks == 9)] < comp[which(ks == 8)], FALSE,
     note = "K=9는 순위합 13으로 K=8(9)·K=12(10)에 밀린다")

  for (pr in list(c("K=9", "topics_k9", "2"), c("K=8", "topics_k8", "3"))) {
    tag <- pr[1]; topics <- truth[[pr[2]]]; n_with <- 0
    for (tp in topics) {
      hits <- intersect(unlist(tp$top10), MEDIA_KEYWORDS)
      ck(e, sprintf("%s T%d 미디어 키워드 수(top10)", tag, tp$topic),
         length(hits), tp$n_media_hits_top10)
      if (length(hits) > 0) n_with <- n_with + 1
    }
    ck(e, sprintf("%s 미디어 키워드가 등장한 토픽 수", tag), n_with, as.numeric(pr[3]))
  }
  ov <- intersect(unlist(truth$topics_k9[[1]]$top10), unlist(truth$topics_k8[[1]]$top10))
  ck(e, "K=9 T0 ∩ K=8 T0 단어 수", length(ov), NULL,
     note = paste("겹치는 단어:", paste(sort(ov), collapse = ", ")))

  # [불일치 기록] 보고서 3.8절 검증② 본문 서술 대 원본 JSON
  cat("[불일치 기록] 보고서 3.8절 검증② 본문 서술 대 원본 JSON\n")
  for (pr in list(c("K=9", "topics_k9"), c("K=8", "topics_k8"))) {
    real <- Filter(function(tp) tp$n_media_hits_top10 > 0, truth[[pr[2]]])
    cat(sprintf("  %s: 본문 서술 = T0 한 곳뿐 / 원본 JSON = %d개 토픽 %s\n", pr[1],
        length(real),
        paste(vapply(real, function(tp) sprintf("T%d(%d개: %s)", tp$topic,
              tp$n_media_hits_top10, paste(unlist(tp$media_hits_top10), collapse = "·")),
              character(1)), collapse = ", ")))
  }
  cat(sprintf("  → K=9 T3 상위10단어: %s\n",
              paste(unlist(truth$topics_k9[[4]]$top10), collapse = ", ")))
  cat("     사실상 '방송출연' 성격의 토픽이며, 본문이 '나머지 7개 토픽은 0건'이라고\n")
  cat("     서술한 것과 원본 데이터가 어긋난다. 다만 K=8 유지라는 결론 자체는\n")
  cat("     검증①(합성순위합 13 vs 9)과 검증③(실루엣 0.099→0.081)이 독립적으로\n")
  cat("     뒷받침하므로 바뀌지 않는다.\n\n")
  ck(e, "본문 '나머지 7개 토픽 0건' 서술이 원본과 일치",
     sum(vapply(truth$topics_k9, function(tp) tp$n_media_hits_top10 > 0, logical(1))) == 1,
     FALSE, note = "원본 JSON 기준 K=9에서 미디어 키워드 보유 토픽은 T0·T3 두 곳")

  docs <- truth$corpus_docs
  for (tag in names(truth$subtag_doc_freq)) {
    v <- truth$subtag_doc_freq[[tag]]
    ck(e, sprintf("서브태그 비중 — %s", tag), round(v$doc_freq / docs * 100, 2), v$pct_of_docs)
  }

  mg <- truth$m_grid_on_k9_phi
  sil <- vapply(mg, function(x) x$silhouette, numeric(1))
  ms  <- vapply(mg, function(x) x$m, numeric(1))
  iso <- vapply(mg, function(x) isTRUE(x$media_topic_isolated), logical(1))
  bi <- which.max(sil); fi <- min(which(iso))
  ck(e, "실루엣 최댓값 M", ms[bi], 5)
  ck(e, "실루엣 최댓값", sil[bi], 0.099)
  ck(e, "T0가 단독 분리되는 최소 M", ms[fi], 6)
  ck(e, "그때의 실루엣", sil[fi], 0.081)
  ck(e, "M=5 → M=6 실루엣 손실", round(sil[bi] - sil[fi], 3), 0.018,
     note = "F6을 얻는 대가로 군집 품질이 떨어지는 트레이드오프")
  ck(e, "T0 분리가 실루엣 최댓값과 양립하는가", iso[bi], FALSE)
  ck_report(e)
}

# --- 7.4절 : 멤버 집중도(MCI) 설명력 검증 -------------------------------------
OUTCOMES <- c("loyalty_score", "spillover_score", "coverage_index", "factor_diversity")
# 보고서 7.4절 본문 표 — (원시 r, 원시 R², 원시 p, excess r, excess R², excess p)
DOC_TABLE <- list(
  loyalty_score    = c(-0.385, 0.148, 0.009, -0.044, 0.002, 0.773),
  spillover_score  = c(-0.066, 0.004, 0.665,  0.214, 0.046, 0.159),
  coverage_index   = c(-0.056, 0.003, 0.715,  0.128, 0.016, 0.404),
  factor_diversity = c(-0.062, 0.004, 0.685, -0.157, 0.025, 0.304))

verify_74 <- function() {
  pilot <- load_json("member_mention_pilot_v7.json")
  frozen <- load_scores("frozen")
  archive <- load_json("member_pilot_mci_correlation_v7.json")
  e <- Checker("보고서 7.4절 — MCI 설명력 검증 (1차 정답지: 보고서 본문 표)")

  g <- sort(intersect(names(pilot), frozen$fandom))
  ck(e, "분석 그룹 수", length(g), 45)
  ck(e, "그룹 명단 == 아카이브 JSON 명단", g, sort(unlist(archive$groups)))

  mci <- vapply(g, function(x) as.numeric(pilot[[x]]$mci_pilot), numeric(1))
  mc  <- vapply(g, function(x) length(pilot[[x]]$member_mention_counts), numeric(1))
  excess <- mci - 1 / mc
  idx <- match(g, frozen$fandom)
  Y <- lapply(OUTCOMES, function(o) frozen[[o]][idx]); names(Y) <- OUTCOMES

  bad <- sum(vapply(g, function(x) {
    sh <- unlist(pilot[[x]]$member_impact_share_pilot)
    abs(round(sum(sh^2), 3) - as.numeric(pilot[[x]]$mci_pilot)) > 0.0015
  }, logical(1)))
  ck(e, "MCI = Σ(점유율)² 재계산 불일치", bad, 0,
     note = "점유율이 소수 3자리로 저장돼 있어 허용오차 0.0015")
  ck(e, "점유율 합 = 1 불일치",
     sum(vapply(g, function(x) abs(sum(unlist(pilot[[x]]$member_impact_share_pilot)) - 1) > 0.005,
                logical(1))), 0)
  ck(e, "구조적 하한 MCI ≥ 1/멤버수 위반", sum(mci < 1 / mc - 1e-9), 0)

  pmc <- cor.test(mci, mc)
  ck(e, "r — MCI × 멤버수", round(unname(pmc$estimate), 3), -0.728,
     note = "MCI가 '집중도'보다 '멤버 수'를 상당 부분 대리한다는 근거")

  for (o in OUTCOMES) {
    d <- DOC_TABLE[[o]]
    preds <- list("원시MCI" = mci, MCI_excess = excess)
    wants <- list("원시MCI" = d[1:3], MCI_excess = d[4:6])
    for (lab in names(preds)) {
      p <- cor.test(preds[[lab]], Y[[o]]); w <- wants[[lab]]
      ck(e, sprintf("%s r — %s", lab, o), round(unname(p$estimate), 3), w[1])
      ck(e, sprintf("%s R² — %s", lab, o), round(unname(p$estimate)^2, 3), w[2])
      ck(e, sprintf("%s p — %s", lab, o), round(p$p.value, 3), w[3])
    }
  }
  r2ex <- vapply(OUTCOMES, function(o) cor(excess, Y[[o]])^2, numeric(1))
  ck(e, "MCI_excess 최고 설명 outcome", OUTCOMES[which.max(r2ex)], "spillover_score")
  ck(e, "MCI_excess 최고 R²", round(max(r2ex), 4), 0.0457)

  cat("다중회귀 outcome ~ MCI + member_count\n")
  cat(sprintf("  %-18s%8s%9s%11s%9s%7s%9s\n",
              "Outcome", "R²", "F", "MCI 계수", "MCI p", "VIF", "MCI 유의"))
  any_sig <- FALSE; max_vif <- 0
  for (o in OUTCOMES) {
    dd <- data.frame(y = Y[[o]], mci = mci, member_count = mc)
    fit <- lm(y ~ mci + member_count, data = dd); s <- ols_summary(fit)
    v <- unname(vif(fit)["mci"]); max_vif <- max(max_vif, v)
    sig <- s$p[2] < 0.05; any_sig <- any_sig || sig
    cat(sprintf("  %-18s%8.4f%9.3f%11.4f%9.4f%7.3f%9s\n", o, s$r_squared,
                s$f_statistic, s$coef[2], s$p[2], v, if (sig) "예" else "아니오"))
  }
  cat("\n")
  ck(e, "MCI 편회귀계수가 유의한 outcome 존재", any_sig, FALSE,
     note = "본문 서술 '어느 outcome 지표에서도 유의하지 않았다'와 일치")
  ck(e, "VIF < 10 (심각 기준 미달)", max_vif < 10, TRUE)

  cat("Shapiro-Wilk 정규성 (모두 α=.05에서 정규분포 기각 예상)\n")
  vars <- c(list(mci = mci, mci_excess = excess), Y)
  for (nm in names(vars)) {
    sw <- shapiro.test(vars[[nm]])
    cat(sprintf("  %-18s W=%.4f  p=%.6f  %s\n", nm, unname(sw$statistic), sw$p.value,
                if (sw$p.value < 0.05) "정규 기각" else "정규 유지"))
  }
  cat("\n")

  o <- "loyalty_score"
  fit <- lm(y ~ mci, data = data.frame(y = Y[[o]], mci = mci))
  inf <- influence_stats(fit); thr <- 4 / length(g)
  ck(e, "Cook's D 임계값 4/n", round(thr, 4), 0.0889)
  ord <- order(inf$cooks_d, decreasing = TRUE)
  cat(sprintf("영향점 상위 5 (회귀: %s ~ MCI, 임계값 4/n=%.4f)\n", o, thr))
  for (rk in 1:5) {
    i <- ord[rk]
    cat(sprintf("  %d. %-14s MCI=%.3f %s=%.3f 멤버수=%2d 표준화잔차=%+.3f Cook's D=%.4f\n",
                rk, g[i], mci[i], o, Y[[o]][i], mc[i],
                unname(inf$std_resid[i]), unname(inf$cooks_d[i])))
  }
  r0 <- cor(mci, Y[[o]])
  dl <- vapply(seq_along(g), function(i) abs(cor(mci[-i], Y[[o]][-i]) - r0), numeric(1))
  cat(sprintf("\nLeave-one-out (%s ~ MCI): 최대 |Δr|=%.4f (%s) · 평균 |Δr|=%.5f\n\n",
              o, max(dl), g[which.max(dl)], mean(dl)))

  res <- ck_report(e)

  # [드리프트 기록] 보고서 본문 vs 아카이브 JSON
  cat("[드리프트 기록] 같은 지표의 세 시점 값\n")
  cat(.padr("  항목", 28), .padl("재현(아카이브 입력)", 22), .padl("보고서 본문", 14),
      .padl("아카이브 JSON", 16), "\n", sep = "")
  rows <- list(list("MCI × 멤버수 r", round(unname(pmc$estimate), 4), -0.728,
                    archive$mci_vs_member_count$pearson_r))
  for (o2 in OUTCOMES)
    rows[[length(rows) + 1]] <- list(sprintf("원시MCI × %s r", o2),
      round(cor(mci, Y[[o2]]), 4), DOC_TABLE[[o2]][1],
      archive$correlations_mci_raw[[o2]]$pearson_r)
  rows[[length(rows) + 1]] <- list("MCI 평균", round(mean(mci), 4), NA,
                                   archive$mci_descriptives$mean)
  rows[[length(rows) + 1]] <- list("MCI 최댓값", round(max(mci), 3), NA,
                                   archive$mci_descriptives$max)
  for (r in rows)
    cat(.padr(paste0("  ", r[[1]]), 28), .padl(format(r[[2]]), 22),
        .padl(if (is.na(r[[3]])) "—" else format(r[[3]]), 14),
        .padl(format(r[[4]]), 16), "\n", sep = "")
  cat("  → 재현값은 보고서 본문과 일치하고 아카이브 JSON과는 어긋난다.\n")
  cat("     아카이브 JSON은 자체 caveat대로 v7 55 시점(8,981건) MCI로 계산된 이전 시점 산출물이며,\n")
  cat("     본문 표는 최종 코퍼스(10,020건) MCI 기준이다. 결론은 두 시점 모두 동일하다.\n\n")
  res
}


# =============================================================================
# [5/6] 진단 플롯 7종 — ggplot2
# =============================================================================
# 그림은 두 곳에 동시에 나간다.
#   (1) RStudio Plots 창  — ggplot 객체를 print() 한다
#   (2) outputs/plots/*.png — ggsave() 로 저장한다
#
# ※ ggplot 객체는 콘솔에 '저절로' 찍히지만 함수 안에서는 안 찍힌다.
#    그래서 render() 가 print(p) 를 명시적으로 호출한다. 이게 빠지면
#    Plots 창에 아무것도 안 나오는 가장 흔한 원인이다.
#
# ※ 7장이 차례로 그려지므로 Plots 창에는 마지막 그림만 보인다.
#    창 왼쪽 위 화살표(← →)로 앞 그림을 넘겨 볼 수 있다.
#    한 장씩 확인하고 싶으면 아래 PAUSE_BETWEEN_PLOTS 를 TRUE 로 바꾼다.
PAUSE_BETWEEN_PLOTS <- FALSE

# 팔레트 (light 모드)
SURFACE <- "#fcfcfb"; INK <- "#0b0b0b"; INK2 <- "#52514e"; MUTED <- "#898781"
GRIDC <- "#e1e0d9"; AXISC <- "#c3c2b7"
S1 <- "#2a78d6"   # 파랑 — 기본 계열
S2 <- "#eb6834"   # 주황 — 강조
CRIT <- "#d03b3b" # 빨강 — 음(−) 방향
GOOD <- "#0ca30c" # 초록 — 정규성 유지

# 공통 테마 — 모든 그림이 같은 규칙을 쓰도록 한 곳에 모아 둔다
theme_fandom <- function(base_size = 11) {
  theme_minimal(base_size = base_size, base_family = KO_FONT) +
    theme(
      plot.background   = element_rect(fill = SURFACE, colour = NA),
      panel.background  = element_rect(fill = SURFACE, colour = NA),
      panel.grid.major  = element_line(colour = GRIDC, linewidth = 0.35),
      panel.grid.minor  = element_blank(),
      axis.line         = element_line(colour = AXISC, linewidth = 0.4),
      axis.ticks        = element_line(colour = AXISC, linewidth = 0.4),
      axis.ticks.length = unit(2.5, "pt"),
      axis.text         = element_text(colour = MUTED, size = rel(0.84)),
      axis.title        = element_text(colour = INK2, size = rel(0.90)),
      plot.title        = element_text(colour = INK, face = "bold",
                                       size = rel(1.00), hjust = 0,
                                       margin = margin(b = 6)),
      plot.subtitle     = element_text(colour = INK2, size = rel(0.80),
                                       margin = margin(b = 6)),
      plot.caption      = element_text(colour = MUTED, size = rel(0.70),
                                       hjust = 0, margin = margin(t = 8)),
      plot.caption.position = "plot",
      plot.title.position   = "plot",
      strip.text        = element_text(colour = INK, face = "bold",
                                       size = rel(0.92), margin = margin(b = 5)),
      legend.title      = element_blank(),
      legend.text       = element_text(colour = INK2, size = rel(0.80)),
      legend.background = element_rect(fill = SURFACE, colour = NA),
      legend.key        = element_rect(fill = SURFACE, colour = NA),
      legend.margin     = margin(0, 0, 0, 0),
      plot.margin       = margin(10, 14, 8, 10)
    )
}
theme_set(theme_fandom())

# 모서리에 주석을 놓는 helper — -Inf/Inf 를 쓰면 facet마다 알아서 자리를 잡는다
ann <- function(label, x = -Inf, y = Inf, hjust = -0.05, vjust = 1.25,
                colour = INK2, size = 3.0, fontface = "plain", ...) {
  annotate("text", x = x, y = y, label = label, hjust = hjust, vjust = vjust,
           colour = colour, size = size, fontface = fontface,
           family = KO_FONT, lineheight = 1.15, ...)
}

# patchwork 로 붙인 그림의 공통 제목·꼬리말
wrap_title <- function(p, title, caption) {
  p + plot_annotation(
    title = title, caption = caption,
    theme = theme_fandom() + theme(
      plot.title   = element_text(colour = INK, face = "bold", size = rel(1.12)),
      plot.caption = element_text(colour = MUTED, size = rel(0.70), hjust = 0)))
}

# 같은 그림을 (1) PNG 파일 (2) RStudio Plots 창 에 각각 내보낸다
render <- function(name, w_px, h_px, p) {
  path <- file.path(PLOT_DIR, paste0(name, ".png"))
  ggsave(path, plot = p, width = w_px / 200, height = h_px / 200,
         units = "in", dpi = 200, bg = SURFACE, limitsize = FALSE)
  cat(sprintf("      %s.png\n", name))
  if (interactive()) {
    print(p)                       # ← 이 줄이 Plots 창에 그림을 띄운다
    if (isTRUE(PAUSE_BETWEEN_PLOTS))
      invisible(readline(sprintf("      [%s] 확인 후 Enter... ", name)))
  }
  invisible(p)
}


# --- fig1 : 2.1절 포지셔닝 맵 ------------------------------------------------
build_fig1 <- function(df) {
  ct  <- cor.test(df$loyalty_score, df$spillover_score)
  fit <- lm(spillover_score ~ loyalty_score, data = df); b <- coef(fit)

  # 4분면 도수와 카이제곱은 하드코딩이 아니라 여기서 다시 센다
  L <- df$loyalty_score >= 0.5; S <- df$spillover_score >= 0.5
  tb <- table(factor(L, c(TRUE, FALSE)), factor(S, c(TRUE, FALSE)))
  ch <- suppressWarnings(chisq.test(tb, correct = TRUE))
  quad <- data.frame(
    x   = c(1.06, 1.06, -0.03, -0.03),
    y   = c(1.06, -0.03, 1.06, -0.03),
    hj  = c(1, 1, 0, 0), vj = c(1, 0, 1, 0),
    lab = c(sprintf("핵심전략형 %d", sum(L & S)),
            sprintf("내부결속형 %d", sum(L & !S)),
            sprintf("외부견인형 %d", sum(!L & S)),
            sprintf("주변부 %d",     sum(!L & !S))))

  df$hl <- df$fandom %in% HIGHLIGHT
  hi <- df[df$hl, , drop = FALSE]
  # ggrepel 은 '점'만 피하고 회귀선은 모르기 때문에, 라벨이 선 위에 얹히는 일이
  # 생긴다. 잔차 부호 방향(선에서 멀어지는 쪽)으로 미리 밀어 두고 나머지는
  # ggrepel 에 맡긴다.
  hi$nudge <- ifelse(resid(fit)[df$hl] >= 0, 0.075, -0.075)

  ggplot(df, aes(loyalty_score, spillover_score)) +
    geom_vline(xintercept = 0.5, colour = AXISC, linewidth = 0.4, linetype = 2) +
    geom_hline(yintercept = 0.5, colour = AXISC, linewidth = 0.4, linetype = 2) +
    geom_text(data = quad, aes(x, y, label = lab, hjust = hj, vjust = vj),
              inherit.aes = FALSE, colour = MUTED, size = 2.7, family = KO_FONT) +
    geom_point(data = df[!df$hl, ], shape = 21, fill = alpha(S1, 0.62),
               colour = SURFACE, stroke = 0.5, size = 2.4) +
    geom_abline(intercept = b[1], slope = b[2], colour = INK, linewidth = 0.95) +
    geom_point(data = hi, shape = 21, fill = S2, colour = SURFACE,
               stroke = 0.9, size = 4.2) +
    ggrepel::geom_text_repel(
      data = hi, aes(label = fandom), family = KO_FONT, fontface = "bold",
      size = 3.1, colour = INK, seed = 1, box.padding = 0.7,
      point.padding = 0.5, min.segment.length = 0.3, max.overlaps = Inf,
      nudge_y = hi$nudge, direction = "both",
      # 모서리의 4분면 도수 주석은 별도 레이어라 ggrepel 이 모른다.
      # 라벨이 놓일 영역을 데이터 범위 안으로 묶어 모서리를 비워 둔다.
      xlim = c(NA, 1.00), ylim = c(NA, 1.00),
      segment.colour = AXISC, segment.size = 0.4) +
    ann(sprintf("회귀선  y = %.4f + %.4f·x", b[1], b[2]),
        y = 0.94, vjust = 1, size = 2.9) +
    ann(sprintf("Pearson r = %.4f  (p = %.2e)\nR² = %.4f   n = %d",
                ct$estimate, ct$p.value, ct$estimate^2, nrow(df)),
        y = 0.87, vjust = 1, size = 2.9) +
    coord_cartesian(xlim = c(-0.03, 1.06), ylim = c(-0.03, 1.06), clip = "off") +
    labs(x = "팬충성도 (loyalty_score)", y = "파급효과 (spillover_score)",
         title = "2.1절 — 포지셔닝 맵 두 축의 관계 (라이브 코퍼스, n=100)",
         caption = sprintf(paste("4분면 기준선 0.5 · 주황 = 보고서 강조 3개 팬덤 ·",
                                 "카이제곱 χ²=%.4f, df=%d, p=%.4f"),
                           ch$statistic, ch$parameter, ch$p.value))
}


# --- fig2 : 2.1절 부호 반전 --------------------------------------------------
build_fig2 <- function(df) {
  f_raw <- lm(spillover_score ~ loyalty_score, data = df)
  r_raw <- cor(df$loyalty_score, df$spillover_score)
  rx <- resid(lm(loyalty_score   ~ activity, data = df))   # activity 성분 제거
  ry <- resid(lm(spillover_score ~ activity, data = df))
  f_par  <- lm(ry ~ rx); ct_par <- cor.test(rx, ry)
  full   <- lm(spillover_score ~ loyalty_score + activity, data = df)
  s      <- summary(full)$coefficients

  p1 <- ggplot(df, aes(loyalty_score, spillover_score)) +
    geom_point(shape = 21, fill = alpha(S1, 0.60), colour = SURFACE,
               stroke = 0.45, size = 2.2) +
    geom_abline(intercept = coef(f_raw)[1], slope = coef(f_raw)[2],
                colour = S1, linewidth = 1.15) +
    ann(sprintf("기울기 = %+.4f\nr = %+.4f", coef(f_raw)[2], r_raw), size = 3.1) +
    labs(x = "팬충성도", y = "파급효과", title = "① 원자료 — 양(+)의 상관") +
    theme(plot.title = element_text(colour = S1, face = "bold"))

  p2 <- ggplot(data.frame(rx, ry), aes(rx, ry)) +
    geom_hline(yintercept = 0, colour = AXISC, linewidth = 0.4) +
    geom_vline(xintercept = 0, colour = AXISC, linewidth = 0.4) +
    geom_point(shape = 21, fill = alpha(CRIT, 0.60), colour = SURFACE,
               stroke = 0.45, size = 2.2) +
    geom_abline(intercept = coef(f_par)[1], slope = coef(f_par)[2],
                colour = CRIT, linewidth = 1.15) +
    ann(sprintf("기울기 = %+.4f\n부분상관 r = %+.4f  (p = %.2e)",
                coef(f_par)[2], ct_par$estimate, ct_par$p.value), size = 3.1) +
    labs(x = "팬충성도 잔차 (activity 제거)", y = "파급효과 잔차 (activity 제거)",
         title = "② 활동량 통제 후 — 음(−)의 관계") +
    theme(plot.title = element_text(colour = CRIT, face = "bold"))

  wrap_title(p1 + p2,
    "2.1절 핵심 발견 — 활동량을 통제하면 충성도 계수의 부호가 뒤집힌다",
    sprintf(paste("부분회귀 기울기는 다중회귀 spillover ~ loyalty + activity 의",
                  "충성도 계수와 같다 (%+.4f, p = %.2e) · VIF = 1.929"),
            s[2, 1], s[2, 4]))
}


# --- fig3 : 2.1·2.2절 Q-Q --------------------------------------------------
build_fig3 <- function(df) {
  items <- list(c("팬충성도" = "loyalty_score"), c("파급효과" = "spillover_score"),
                c("팬 요인 다양성" = "factor_diversity"))
  pts <- do.call(rbind, lapply(items, function(it) {
    lab <- names(it); v <- df[[unname(it)]]
    q <- qqnorm(v, plot.it = FALSE)
    data.frame(panel = lab, theo = q$x, samp = q$y,
               ok = shapiro.test(v)$p.value > 0.05)
  }))
  # qqline 과 동일한 사분위 기준 직선을 패널마다 계산한다
  lines_df <- do.call(rbind, lapply(items, function(it) {
    lab <- names(it); v <- df[[unname(it)]]
    yq <- quantile(v, c(0.25, 0.75), names = FALSE)
    xq <- qnorm(c(0.25, 0.75))
    sl <- diff(yq) / diff(xq)
    data.frame(panel = lab, slope = sl, intercept = yq[1] - sl * xq[1])
  }))
  labs_df <- do.call(rbind, lapply(items, function(it) {
    lab <- names(it); sw <- shapiro.test(df[[unname(it)]])
    ok <- sw$p.value > 0.05
    data.frame(panel = lab, ok = ok,
               lab = sprintf("W = %.4f\np = %.4g\n%s", sw$statistic, sw$p.value,
                             if (ok) "정규 유지" else "정규 기각"))
  }))
  lv <- vapply(items, names, "")
  pts$panel <- factor(pts$panel, lv)
  lines_df$panel <- factor(lines_df$panel, lv)
  labs_df$panel  <- factor(labs_df$panel, lv)

  ggplot(pts, aes(theo, samp)) +
    geom_abline(data = lines_df, aes(intercept = intercept, slope = slope),
                colour = AXISC, linewidth = 0.75) +
    geom_point(aes(fill = ok), shape = 21, colour = SURFACE,
               stroke = 0.4, size = 2.0, show.legend = FALSE) +
    geom_text(data = labs_df, aes(x = -Inf, y = Inf, label = lab, colour = ok),
              hjust = -0.08, vjust = 1.18, size = 3.1, fontface = "bold",
              family = KO_FONT, lineheight = 1.15, inherit.aes = FALSE,
              show.legend = FALSE) +
    scale_fill_manual(values  = c(`TRUE` = alpha(S1, 0.70), `FALSE` = alpha(CRIT, 0.70))) +
    scale_colour_manual(values = c(`TRUE` = GOOD, `FALSE` = CRIT)) +
    facet_wrap(~ panel, nrow = 1, scales = "free") +
    labs(x = "이론 분위수", y = "표본 분위수",
         title = "2.1·2.2절 — Shapiro-Wilk 정규성 진단 (α = .05)",
         caption = paste("세 변수 모두 우측 꼬리에서 이론선을 이탈한다 —",
                         "min-max 정규화가 원 분포의 우측 쏠림을 보존하기 때문.",
                         "붉은색 = 정규분포 기각"))
}


# --- fig4 : 2.1·2.2절 영향점 ------------------------------------------------
build_fig4 <- function(df) {
  fits <- list("2.1절  파급효과 ~ 충성도" = lm(spillover_score ~ loyalty_score, data = df),
               "2.2절  다양성 ~ 충성도 + 파급효과" =
                 lm(factor_diversity ~ loyalty_score + spillover_score, data = df))
  thr <- 4 / nrow(df)
  dd <- do.call(rbind, lapply(names(fits), function(nm) {
    fit <- fits[[nm]]
    data.frame(panel = nm, fandom = df$fandom, hat = hatvalues(fit),
               sr = rstandard(fit), cd = cooks.distance(fit),
               row.names = NULL)
  }))
  dd$big <- dd$cd > thr
  dd$panel <- factor(dd$panel, names(fits))
  # 라벨은 패널마다 Cook's D 상위 5개만 — 위치는 ggrepel 이 알아서 피해 준다
  lab_df <- do.call(rbind, lapply(split(dd, dd$panel), function(s)
    s[order(s$cd, decreasing = TRUE)[1:5], ]))
  note_df <- do.call(rbind, lapply(split(dd, dd$panel), function(s)
    data.frame(panel = s$panel[1],
               lab = sprintf("버블 크기 = Cook's D · 임계값 4/n = %.2f 초과 %d개",
                             thr, sum(s$big)))))

  ggplot(dd, aes(hat, sr)) +
    geom_hline(yintercept = 0, colour = AXISC, linewidth = 0.4) +
    geom_hline(yintercept = c(-2, 2), colour = AXISC, linewidth = 0.45, linetype = 2) +
    geom_point(aes(size = cd, fill = big), shape = 21, colour = SURFACE,
               stroke = 0.45, show.legend = FALSE) +
    ggrepel::geom_text_repel(
      data = lab_df, aes(label = fandom), family = KO_FONT, fontface = "bold",
      size = 2.75, colour = INK, seed = 7, box.padding = 0.55,
      point.padding = 0.5, min.segment.length = 0.3, max.overlaps = Inf,
      segment.colour = AXISC, segment.size = 0.35) +
    geom_text(data = note_df, aes(x = -Inf, y = Inf, label = lab),
              hjust = -0.04, vjust = 1.3, size = 2.75, colour = INK2,
              family = KO_FONT, inherit.aes = FALSE) +
    # 작은 Cook's D 도 점이 보여야 하므로 최소 크기를 준다 (scale_size_area 는 0→0)
    scale_size(range = c(0.9, 11)) +
    scale_fill_manual(values = c(`TRUE` = alpha(S2, 0.75), `FALSE` = alpha(S1, 0.45))) +
    scale_y_continuous(expand = expansion(mult = 0.18)) +
    facet_wrap(~ panel, nrow = 1, scales = "free") +
    labs(x = "leverage (hat)", y = "표준화 잔차",
         title = "2.1·2.2절 — 영향점 진단 (Cook's distance)",
         caption = paste("주황 = 임계값 초과 · 점선 = 표준화 잔차 ±2 ·",
                         "Leave-one-out 결과 두 회귀 모두 소수 극단값에 좌우되지 않음",
                         "(최대 |Δr| 0.0618 / 최대 |Δ계수| 0.0360)"))
}


# --- fig5 : 2.2절 세 축 쌍별 독립성 -----------------------------------------
build_fig5 <- function(df) {
  prs <- list(c("팬충성도", "loyalty_score", "파급효과", "spillover_score"),
              c("팬충성도", "loyalty_score", "팬 요인 다양성", "factor_diversity"),
              c("파급효과", "spillover_score", "팬 요인 다양성", "factor_diversity"))
  # 패널마다 축 이름이 다르므로 facet 이 아니라 patchwork 로 붙인다.
  # (facet_wrap 은 모든 패널이 축 이름을 공유해서 여기서는 쓸 수 없다.)
  panels <- lapply(prs, function(pr) {
    d <- data.frame(x = df[[pr[2]]], y = df[[pr[4]]])
    ct <- cor.test(d$x, d$y); sig <- ct$p.value < 0.05
    col <- if (sig) S1 else MUTED
    ggplot(d, aes(x, y)) +
      geom_point(shape = 21, fill = alpha(col, 0.60), colour = SURFACE,
                 stroke = 0.4, size = 1.9) +
      geom_smooth(method = "lm", formula = y ~ x, se = FALSE,
                  colour = col, linewidth = 1.05) +
      ann(sprintf("r = %+.4f\np = %.3g\n%s", ct$estimate, ct$p.value,
                  if (sig) "유의 — 독립 아님" else "유의하지 않음 — 독립"),
          colour = if (sig) CRIT else INK2, size = 3.0,
          fontface = if (sig) "bold" else "plain") +
      scale_y_continuous(expand = expansion(mult = c(0.05, 0.24))) +
      labs(x = pr[1], y = pr[3], title = sprintf("%s × %s", pr[1], pr[3]))
  })

  wrap_title(panels[[1]] + panels[[2]] + panels[[3]],
    "2.2절 — 3D 맵 세 축의 쌍별 독립성 (라이브 코퍼스, n=100)",
    paste("각주가 주장한 «세 축은 서로 독립적»은 라이브 기준으로 성립하지 않는다",
          "— 회색 = 독립(충성도×다양성), 파랑 = 유의한 관계"))
}


# --- fig6 : 3.8절 K9/F6 -----------------------------------------------------
build_fig6 <- function() {
  k <- load_json("k9_validation_v7.json"); g <- k$k_grid
  kd <- data.frame(k   = vapply(g, function(x) x$k, numeric(1)),
                   rs  = vapply(g, function(x) x$composite_rank_sum, numeric(1)))
  kd <- kd[order(kd$rs), ]
  kd$lab  <- factor(paste0("K=", kd$k), levels = rev(paste0("K=", kd$k)))
  kd$role <- ifelse(kd$k == 9, "신규 후보(K=9)",
                    ifelse(kd$k == 8, "채택(K=8)", "그 외"))

  p1 <- ggplot(kd, aes(rs, lab, fill = role)) +
    geom_col(width = 0.72) +
    geom_text(aes(label = rs), hjust = -0.35, size = 2.9, colour = INK2,
              family = KO_FONT) +
    scale_fill_manual(values = c("채택(K=8)" = S1, "신규 후보(K=9)" = S2,
                                 "그 외" = MUTED),
                      breaks = c("채택(K=8)", "신규 후보(K=9)")) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
    # 막대가 아래로 갈수록 길어지므로 범례는 비어 있는 오른쪽 위에 둔다
    theme(panel.grid.major.y = element_blank(),
          legend.position = c(0.99, 0.99), legend.justification = c(1, 1)) +
    labs(x = "합성순위합 (낮을수록 상위)", y = NULL,
         title = "검증 ① K-그리드 재평가")

  mg <- k$m_grid_on_k9_phi
  md <- data.frame(m   = vapply(mg, function(x) x$m, numeric(1)),
                   sil = vapply(mg, function(x) x$silhouette, numeric(1)),
                   iso = vapply(mg, function(x) isTRUE(x$media_topic_isolated), logical(1)))
  md <- md[order(md$m), ]
  drop <- md[md$m %in% c(5, 6), ]                 # 품질 손실 구간
  d_sil <- diff(drop$sil)

  p2 <- ggplot(md, aes(m, sil)) +
    geom_line(colour = S1, linewidth = 1.0) +
    geom_line(data = drop, colour = CRIT, linewidth = 1.15) +
    geom_point(data = md[md$iso, ], shape = 21, fill = NA, colour = S2,
               stroke = 1.0, size = 5.4) +
    geom_point(shape = 21, fill = S1, colour = SURFACE, stroke = 0.9, size = 2.7) +
    # 값 라벨이 꺾은선·점 위에 얹히지 않도록 ggrepel 에 자리를 맡긴다
    # (min.segment.length = Inf → 지시선은 그리지 않는다)
    ggrepel::geom_text_repel(aes(label = sprintf("%.3f", sil)),
                             size = 2.8, colour = INK2, family = KO_FONT,
                             seed = 11, box.padding = 0.55, point.padding = 0.4,
                             min.segment.length = Inf, max.overlaps = Inf) +
    annotate("text", x = 5.46, y = mean(drop$sil), hjust = 1,
             label = sprintf("실루엣 %+.3f", d_sil), colour = CRIT,
             fontface = "bold", size = 3.0, family = KO_FONT) +
    ann("주황 테두리 =\n미디어 토픽(T0) 단독 분리",
        x = Inf, hjust = 1.05, vjust = 1.9, size = 2.8) +
    scale_x_continuous(breaks = md$m, expand = expansion(mult = 0.09)) +
    scale_y_continuous(expand = expansion(mult = 0.16)) +
    labs(x = "메타팩터 수 M", y = "실루엣 계수",
         title = "검증 ③ M-그리드 트레이드오프")

  wrap_title(p1 + p2,
    "3.8절 — K9/F6 제안 검증: 채택값은 바뀌지 않고, F6은 품질을 대가로 요구한다",
    sprintf(paste("K=9는 합성순위합 %d으로 K=8(%d)·K=12(%d)에 밀린다 ·",
                  "T0 단독 분리는 M=6부터 가능하나 실루엣이 최댓값 %.3f에서",
                  "%.3f로 하락한다"),
            kd$rs[kd$k == 9], kd$rs[kd$k == 8], kd$rs[kd$k == 12],
            max(md$sil), md$sil[md$m == 6]))
}


# --- fig7 : 7.4절 MCI -------------------------------------------------------
build_fig7 <- function() {
  pilot <- load_json("member_mention_pilot_v7.json"); frozen <- load_scores("frozen")
  g <- sort(intersect(names(pilot), frozen$fandom))
  mci <- vapply(g, function(x) as.numeric(pilot[[x]]$mci_pilot), numeric(1))
  mc  <- vapply(g, function(x) length(pilot[[x]]$member_mention_counts), numeric(1))
  excess <- mci - 1 / mc; idx <- match(g, frozen$fandom)
  outs <- c("loyalty_score", "spillover_score", "coverage_index", "factor_diversity")
  labs4 <- c("팬충성도", "파급효과", "커버리지", "요인다양성")
  Y <- lapply(outs, function(o) frozen[[o]][idx]); names(Y) <- outs

  ct <- cor.test(mci, mc)
  pts <- data.frame(fandom = g, mc = mc, mci = mci)
  curve_df <- data.frame(mc = seq(min(mc), max(mc), length.out = 200))
  curve_df$mci <- 1 / curve_df$mc
  mark <- pts[pts$fandom %in% c("FTISLAND", "NCT", "SEVENTEEN"), ]

  p1 <- ggplot(pts, aes(mc, mci)) +
    geom_point(shape = 21, fill = alpha(S1, 0.62), colour = SURFACE,
               stroke = 0.5, size = 2.5) +
    geom_line(data = curve_df, colour = CRIT, linewidth = 1.0, linetype = 2) +
    annotate("segment", x = 3.15, xend = 4.4, y = 1 / 3.15, yend = 0.45,
             colour = CRIT, linewidth = 0.4) +
    annotate("text", x = 4.5, y = 0.45, label = "이론적 하한 1/n", hjust = 0,
             colour = CRIT, fontface = "bold", size = 3.0, family = KO_FONT) +
    ggrepel::geom_text_repel(data = mark, aes(label = fandom), family = KO_FONT,
                             fontface = "bold", size = 2.9, colour = INK, seed = 3,
                             box.padding = 0.65, point.padding = 0.45,
                             min.segment.length = 0.3, segment.colour = AXISC,
                             segment.size = 0.35) +
    ann(sprintf("r = %+.4f  (p = %.2e)\nn = %d개 그룹",
                ct$estimate, ct$p.value, length(g)),
        x = Inf, hjust = 1.05, size = 3.0) +
    coord_cartesian(ylim = c(0.05, max(mci) + 0.03)) +
    labs(x = "멤버 수", y = "MCI (허핀달-허쉬만)",
         title = "MCI는 「집중도」보다 「멤버 수」를 대리한다")

  bars <- data.frame(
    outcome = factor(rep(labs4, 2), levels = labs4),
    kind    = factor(rep(c("원시 MCI", "MCI_excess (멤버 수 통제)"), each = 4),
                     levels = c("원시 MCI", "MCI_excess (멤버 수 통제)")),
    r2      = c(vapply(outs, function(o) cor(mci,    Y[[o]])^2, numeric(1)),
                vapply(outs, function(o) cor(excess, Y[[o]])^2, numeric(1))))

  p2 <- ggplot(bars, aes(outcome, r2, fill = kind)) +
    geom_col(position = position_dodge(width = 0.78), width = 0.7) +
    geom_text(aes(label = sprintf("%.3f", r2)),
              position = position_dodge(width = 0.78), vjust = -0.7,
              size = 2.8, colour = INK2, family = KO_FONT) +
    scale_fill_manual(values = c("원시 MCI" = S1,
                                 "MCI_excess (멤버 수 통제)" = S2)) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.22))) +
    theme(panel.grid.major.x = element_blank(),
          legend.position = c(0.99, 0.99), legend.justification = c(1, 1)) +
    labs(x = NULL, y = "결정계수 R²",
         title = "멤버 수를 통제하면 설명력이 사라진다")

  wrap_title(p1 + p2,
    "7.4절 — 멤버 집중도(MCI)의 그룹 지표 설명력",
    paste("원시 MCI 최고 R²는 팬충성도 0.148(14.8%)이고, 멤버 수를 통제하면",
          "최고가 파급효과 0.046(4.6%)으로 떨어지며 그마저 유의하지 않다(p=0.159)"))
}


# =============================================================================
#  메인 실행
# =============================================================================
cat("[4/6] 통계 검증 — 보고서 2.1 · 2.2 · 3.8 · 7.4절\n\n")
res <- list(
  c(sec = "2.1", run = verify_21(DF_LIVE)),
  c(sec = "2.2", run = verify_22(DF_LIVE)),
  c(sec = "3.8", run = verify_38()),
  c(sec = "7.4", run = verify_74()))
totals <- vapply(res, function(x) as.numeric(x[["run.total"]]), numeric(1))
oks    <- vapply(res, function(x) as.numeric(x[["run.ok"]]), numeric(1))

cat("[5/6] 진단 플롯 7종 생성 (ggplot2)\n")
PLOTS <- list(
  fig1_positioning_scatter_R = list(1480, 1180, function() build_fig1(DF_LIVE)),
  fig2_sign_reversal_R       = list(2100,  980, function() build_fig2(DF_LIVE)),
  fig3_qq_normality_R        = list(2200,  840, function() build_fig3(DF_LIVE)),
  fig4_influence_R           = list(2100, 1040, function() build_fig4(DF_LIVE)),
  fig5_axis3d_pairs_R        = list(2260,  860, function() build_fig5(DF_LIVE)),
  fig6_k9_grid_R             = list(2160, 1000, build_fig6),
  fig7_mci_R                 = list(2160, 1020, build_fig7))

# 만든 ggplot 객체를 FIGS 에 남겨 둔다 — 실행이 끝난 뒤 콘솔에서
#   FIGS$fig4_influence_R      ← 다시 크게 보기
#   FIGS$fig1_positioning_scatter_R + theme_gray()   ← 테마만 바꿔 보기
# 처럼 한 장씩 꺼내 볼 수 있다.
FIGS <- list()
for (nm in names(PLOTS)) {
  spec <- PLOTS[[nm]]
  FIGS[[nm]] <- render(nm, spec[[1]], spec[[2]], spec[[3]]())
}
if (interactive())
  cat("      → Plots 창 좌측 상단 화살표(← →)로 7장을 넘겨 볼 수 있습니다.\n",
      "       한 장씩 보려면 PAUSE_BETWEEN_PLOTS <- TRUE 로 바꾸고 다시 Source 하세요.\n",
      "       특정 그림만 다시 보려면 예: FIGS$fig4_influence_R\n", sep = "")
cat("\n")

cat("[6/6] 총괄 요약\n")
titles <- c("포지셔닝 맵 상관계수 분석 및 통계적 검증", "3D 포지셔닝 맵 Z축 독립성 검증",
            "K9/F6 제안 검증", "멤버 집중도(MCI) 설명력 검증")
secs <- c("2.1", "2.2", "3.8", "7.4")
cat(strrep("=", 88), "\n", sep = "")
cat(.padr("절", 6), .padr("검증 항목", 42), .padl("대조", 8), .padl("일치", 8),
    .padl("불일치", 8), "\n", sep = "")
cat(strrep("-", 88), "\n", sep = "")
for (i in seq_along(secs))
  cat(.padr(secs[i], 6), .padr(titles[i], 42), .padl(totals[i], 8),
      .padl(oks[i], 8), .padl(totals[i] - oks[i], 8), "\n", sep = "")
cat(strrep("-", 88), "\n", sep = "")
cat(.padr("합계", 48), .padl(sum(totals), 8), .padl(sum(oks), 8),
    .padl(sum(totals) - sum(oks), 8), "\n", sep = "")
cat(strrep("=", 88), "\n\n", sep = "")

dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
writeLines(c(sprintf("%s절: %d/%d 일치", secs, oks, totals),
             sprintf("합계: %d/%d 일치", sum(oks), sum(totals))),
           file.path(OUT_DIR, "verify_summary.txt"))

if (sum(oks) == sum(totals)) {
  cat("모든 대조 항목이 원본과 일치합니다 — 보고서의 통계적 검증은\n")
  cat("아카이브 데이터에서 전부 재현 가능합니다.\n\n")
} else {
  cat(sprintf("불일치 %d건 — 위 절별 출력의 '불일치' 행을 확인하세요.\n\n",
              sum(totals) - sum(oks)))
}
cat("[재현 과정에서 발견해 기록한 두 가지 문서-데이터 불일치]\n")
cat("  · 3.8절 검증② 본문은 미디어 키워드 보유 토픽을 'T0 한 곳뿐'이라 서술하지만,\n")
cat("    원본 JSON 기준 K=9는 T0·T3 두 곳, K=8은 T0·T3·T4 세 곳입니다.\n")
cat("    (결론인 K=8 유지는 검증①·③이 독립적으로 뒷받침하므로 바뀌지 않습니다.)\n")
cat("  · 7.4절은 보고서 본문 값과 아카이브 JSON 값이 서로 다릅니다. 아카이브 입력에서\n")
cat("    재계산하면 본문과 일치하므로, 아카이브 JSON은 보고서 이후 시점의 재계산본입니다.\n\n")

cat("산출물\n")
cat("  ", normalizePath(PLOT_DIR, winslash = "/", mustWork = FALSE), "  (PNG 7장)\n", sep = "")
cat("  ", normalizePath(file.path(OUT_DIR, "verify_summary.txt"), winslash = "/",
                        mustWork = FALSE), "\n", sep = "")
cat(sprintf("\n총 소요 %.1f초 · 완료 %s\n\n",
            as.numeric(difftime(Sys.time(), t_start, units = "secs")),
            format(Sys.time(), "%Y-%m-%d %H:%M:%S")))








# 포지셔닝 산점도
FIGS$fig1_positioning_scatter_R


# 부호반전전
FIGS$fig2_sign_reversal_R



# Q-Q 정규성성


# Cook's Distance
FIGS$fig4_influence_R
