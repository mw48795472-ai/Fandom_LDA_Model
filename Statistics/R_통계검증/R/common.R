# -*- coding: utf-8 -*-
# =============================================================================
# 공통 로더 · 통계 헬퍼 (R)
# =============================================================================
# 팬덤100 LDA v7 보고서의 통계적 검증을 R로 재현하기 위한 공통 스크립트.
# 동봉된 Python 패키지와 같은 입력·같은 정답지를 쓰며, 두 언어의 결과가 서로
# 일치하는지까지가 검증 범위다.
#
# 사용 패키지
#   jsonlite : 원본 JSON 로딩
#   car      : vif() — 분산팽창지수
#   (base/stats: cor.test, shapiro.test, lm, chisq.test, cooks.distance,
#                rstandard, hatvalues — R 표준 함수를 그대로 쓴다)

suppressPackageStartupMessages({
  library(jsonlite)
  library(car)
})

# 한글 라벨·팬덤명이 <U+....> 로 깨지지 않도록 UTF-8 로케일을 확보한다.
# (컨테이너/CI처럼 LC_CTYPE=C 인 환경에서 필요. 실패해도 계산 결과에는 영향 없음.)
if (!isTRUE(l10n_info()$`UTF-8`)) {
  for (loc in c("C.UTF-8", "C.utf8", "en_US.UTF-8", "ko_KR.UTF-8")) {
    if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", loc)))) break
  }
}

`%||%` <- function(a, b) if (is.null(a)) b else a

.here <- function() {
  # Rscript 실행 시 스크립트 경로를 찾아 data/ 위치를 정한다.
  args <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", args[grep("^--file=", args)])
  if (length(f)) dirname(normalizePath(f)) else getwd()
}

DATA_DIR <- file.path(dirname(.here()), "data")
OUT_DIR  <- file.path(dirname(.here()), "outputs")

# -----------------------------------------------------------------------------
# 데이터 로딩
# -----------------------------------------------------------------------------
load_json <- function(name) {
  fromJSON(file.path(DATA_DIR, name), simplifyVector = FALSE)
}

#' 팬덤 점수 스냅샷을 data.frame으로.
#' track = "live"   → fandom_scores_live_reference_v7.json (라이브, 10,020건 코퍼스)
#' track = "frozen" → fandom_scores_v6.json (v7-40 동결 스냅샷, 7,350건)
load_scores <- function(track = "live") {
  name <- switch(track,
                 live   = "fandom_scores_live_reference_v7.json",
                 frozen = "fandom_scores_v6.json",
                 stop("track must be 'live' or 'frozen'"))
  raw <- load_json(name)
  data.frame(
    fandom           = vapply(raw, function(x) x$fandom, character(1)),
    category         = vapply(raw, function(x) x$category %||% "", character(1)),
    loyalty_score    = vapply(raw, function(x) as.numeric(x$loyalty_score), numeric(1)),
    spillover_score  = vapply(raw, function(x) as.numeric(x$spillover_score), numeric(1)),
    factor_diversity = vapply(raw, function(x) as.numeric(x$factor_diversity), numeric(1)),
    coverage_index   = vapply(raw, function(x) as.numeric(x$coverage_index), numeric(1)),
    activity         = vapply(raw, function(x) as.numeric(x$activity), numeric(1)),
    stringsAsFactors = FALSE
  )
}

# -----------------------------------------------------------------------------
# 통계 헬퍼 — 보고서가 쓴 것과 동일한 정의
# -----------------------------------------------------------------------------

#' Fisher z 변환 기반 Pearson r의 95% 신뢰구간.
#' 주의: R의 cor.test()도 같은 CI를 주지만, Python 쪽과 동일 경로로 맞추기 위해
#' 직접 계산한다(결과는 같다).
pearson_ci95 <- function(r, n) {
  z  <- atanh(r)
  se <- 1 / sqrt(n - 3)
  tanh(c(z - qnorm(0.975) * se, z + qnorm(0.975) * se))
}

#' OLS 적합 결과에서 보고서가 표로 실은 값들을 뽑아낸다.
ols_summary <- function(fit) {
  s <- summary(fit)
  co <- s$coefficients
  list(
    names         = rownames(co),
    coef          = unname(co[, "Estimate"]),
    se            = unname(co[, "Std. Error"]),
    t             = unname(co[, "t value"]),
    p             = unname(co[, "Pr(>|t|)"]),
    r_squared     = s$r.squared,
    adj_r_squared = s$adj.r.squared,
    f_statistic   = unname(s$fstatistic[1]),
    f_pvalue      = unname(pf(s$fstatistic[1], s$fstatistic[2], s$fstatistic[3],
                              lower.tail = FALSE))
  )
}

#' 표준화(내부 스튜던트화) 잔차 · Cook's distance · leverage
#' R 표준 함수 rstandard()/cooks.distance()/hatvalues()를 그대로 쓴다 —
#' Python 쪽 구현과 정의가 같음을 교차 확인하는 것이 이 패키지의 목적 중 하나다.
influence_stats <- function(fit) {
  list(std_resid = rstandard(fit),
       cooks_d   = cooks.distance(fit),
       leverage  = hatvalues(fit))
}

# -----------------------------------------------------------------------------
# 원본 대조 기록
# -----------------------------------------------------------------------------
Checker <- function(title) {
  env <- new.env(parent = emptyenv())
  env$title <- title
  env$rows <- list()
  env
}

#' tol이 NULL이면 want가 기록된 유효 소수 자릿수까지만 비교한다.
ck_check <- function(env, label, got, want, tol = NULL, note = "") {
  ok <- NA
  if (!is.null(want)) {
    if (is.numeric(got) && is.numeric(want) && length(got) == 1 && length(want) == 1) {
      if (is.null(tol)) {
        dec <- .decimals(want)
        ok <- isTRUE(round(got, dec) == round(want, dec))
      } else {
        ok <- isTRUE(abs(got - want) <= tol)
      }
    } else {
      ok <- isTRUE(all(got == want) && length(got) == length(want))
    }
  }
  env$rows[[length(env$rows) + 1]] <- list(label = label, got = got, want = want,
                                           ok = ok, note = note)
  invisible(ok)
}

.decimals <- function(x) {
  s <- format(x, scientific = FALSE, digits = 15)
  if (!grepl("\\.", s)) return(0L)
  nchar(sub("0+$", "", strsplit(s, "\\.")[[1]][2]))
}

.fmt <- function(v) {
  if (is.null(v)) return("—")
  if (is.numeric(v) && length(v) == 1) {
    if (v != 0 && abs(v) < 1e-4) return(formatC(v, format = "e", digits = 3))
    return(formatC(v, format = "g", digits = 6))
  }
  if (length(v) > 1) return(paste0("<", length(v), "개 값>"))
  as.character(v)
}

# 한글은 표시 폭이 2칸이므로 sprintf("%-*s")로는 정렬이 어긋난다.
# 표시 폭(nchar type="width") 기준으로 직접 패딩한다.
.padr <- function(s, w) paste0(s, strrep(" ", max(0, w - nchar(s, type = "width"))))
.padl <- function(s, w) paste0(strrep(" ", max(0, w - nchar(s, type = "width"))), s)

ck_report <- function(env) {
  labs <- vapply(env$rows, function(r) r$label, character(1))
  w <- max(nchar(labs, type = "width")) + 2
  line <- strrep("=", w + 52)
  cat(line, "\n", env$title, "\n", line, "\n", sep = "")
  cat(.padr("항목", w), .padl("재현값", 16), .padl("원본값", 16), "\n", sep = "")
  cat(strrep("-", w + 52), "\n", sep = "")
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
