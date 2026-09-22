# -*- coding: utf-8 -*-
# =============================================================================
# SETUP_DATA.R — 원본(raw) 아카이브에서 검증에 필요한 JSON 7개만 골라 data/ 를 만든다
# =============================================================================
#   Rscript SETUP_DATA.R                        # 원본 폴더/zip 자동 탐색
#   Rscript SETUP_DATA.R <원본 폴더 또는 zip>    # 위치를 직접 지정
#   RStudio: 이 파일을 열고 Source
#
# 원본 = 「팬덤100_LDA_v7_데이터아카이브」 폴더(30여 개 파일) 또는 그 zip.
# 자동 탐색 범위: 이 폴더, 상위 폴더, Downloads, Desktop, Documents 와 그 하위 2단계.
# data/ 에 복사한 파일은 읽기 전용으로 표시한다(원본 아카이브이므로 수정 금지).

MARKER   <- "fandom_scores_live_reference_v7.json"
REQUIRED <- c(MARKER, "fandom_scores_v6.json", "member_mention_pilot_v7.json",
              "positioning_map_correlation_live_v7.json",
              "chart3d_correlation_live_v7.json", "k9_validation_v7.json",
              "member_pilot_mci_correlation_v7.json")

script_dir <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f) && nzchar(f[1]))
    return(tryCatch(dirname(normalizePath(f[1])), error = function(e) NA_character_))
  for (i in seq_len(sys.nframe())) {
    of <- tryCatch(sys.frame(i)$ofile, error = function(e) NULL)
    if (!is.null(of))
      return(tryCatch(dirname(normalizePath(of)), error = function(e) NA_character_))
  }
  if (requireNamespace("rstudioapi", quietly = TRUE)) {
    p <- tryCatch({
      if (rstudioapi::isAvailable()) rstudioapi::getSourceEditorContext()$path else ""
    }, error = function(e) "")
    if (nzchar(p))
      return(tryCatch(dirname(normalizePath(p)), error = function(e) NA_character_))
  }
  NA_character_
}

bail <- function(...) {
  cat("\n", ..., "\n\n", sep = "")
  if (interactive()) stop("SETUP_DATA 중단", call. = FALSE) else quit(status = 1)
}

HERE <- script_dir()
if (is.na(HERE)) HERE <- getwd()
DATA <- file.path(HERE, "data")
norm <- function(p) normalizePath(p, winslash = "/", mustWork = FALSE)

cat("\n[SETUP_DATA] 프로젝트:", norm(HERE), "\n")

have <- file.exists(file.path(DATA, REQUIRED))
if (all(have)) {
  cat("  data/ 준비됨 — 필요한 7개 파일이 모두 있습니다. 할 일 없음.\n")
  cat("  다음: Rscript RUN_ALL.R  (RStudio: RUN_ALL.R 열고 Source)\n\n")
} else {

  # ---- 1) 원본 후보 수집 --------------------------------------------------
  arg  <- commandArgs(trailingOnly = TRUE)
  arg  <- arg[nzchar(arg)]
  home <- Sys.getenv("USERPROFILE", unset = path.expand("~"))
  roots <- unique(c(HERE, dirname(HERE),
                    file.path(home, c("Downloads", "Desktop", "Documents")),
                    path.expand("~")))
  roots <- roots[dir.exists(roots)]
  sub1  <- function(r) list.dirs(r, recursive = FALSE)
  cand  <- unique(c(roots, unlist(lapply(roots, sub1))))
  cand  <- unique(c(cand, unlist(lapply(cand, sub1))))
  cand  <- cand[!grepl("[.]Rproj[.]user|node_modules|[.]git$", cand)]
  cand  <- cand[norm(cand) != norm(DATA)]
  zips  <- unlist(lapply(unique(c(roots, unlist(lapply(roots, sub1)))),
                         function(r) list.files(r, pattern = "[.]zip$", full.names = TRUE)))

  has_marker <- function(d) file.exists(file.path(d, MARKER))
  zip_has    <- function(z) tryCatch(MARKER %in% basename(unzip(z, list = TRUE)$Name),
                                     error = function(e) FALSE)

  from_zip <- function(z) {
    nm  <- unzip(z, list = TRUE)$Name
    pick <- nm[basename(nm) %in% REQUIRED]
    tmp <- file.path(tempdir(), "setup_data_zip")
    dir.create(tmp, showWarnings = FALSE, recursive = TRUE)
    unzip(z, files = pick, exdir = tmp, junkpaths = TRUE, overwrite = TRUE)
    tmp
  }

  # ---- 2) 원본 선택: 인자 > 폴더 > zip -------------------------------------
  SRC <- NA_character_; SRC_LABEL <- ""
  if (length(arg)) {
    p <- arg[1]
    if (dir.exists(p) && has_marker(p))        { SRC <- p;          SRC_LABEL <- norm(p) }
    else if (file.exists(p) && zip_has(p))      { SRC <- from_zip(p); SRC_LABEL <- paste0(norm(p), " (zip)") }
    else bail("  [중단] 지정한 위치에 ", MARKER, " 가 없습니다:\n    ", p)
  } else {
    hit <- cand[vapply(cand, has_marker, logical(1))]
    if (length(hit)) { SRC <- hit[1]; SRC_LABEL <- norm(hit[1]) }
    else {
      zhit <- zips[vapply(zips, zip_has, logical(1))]
      if (length(zhit)) { SRC <- from_zip(zhit[1]); SRC_LABEL <- paste0(norm(zhit[1]), " (zip)") }
    }
  }
  if (is.na(SRC))
    bail("  [중단] 원본 아카이브를 찾지 못했습니다.\n",
         "  찾은 곳: 이 폴더 · 상위 폴더 · Downloads · Desktop · Documents (하위 2단계)\n",
         "  해결: 원본 폴더(또는 zip) 경로를 직접 넘기세요.\n",
         "    Rscript SETUP_DATA.R \"C:/경로/팬덤100_LDA_v7_데이터아카이브\"\n",
         "    또는 원본 폴더를 START.bat 위로 끌어다 놓기")

  missing <- REQUIRED[!file.exists(file.path(SRC, REQUIRED))]
  if (length(missing))
    bail("  [중단] 원본에 다음 파일이 없습니다 (", SRC_LABEL, "):\n    ",
         paste(missing, collapse = "\n    "))

  # ---- 3) 복사 + 읽기 전용 -------------------------------------------------
  dir.create(DATA, showWarnings = FALSE)
  cat("  원본:", SRC_LABEL, "\n  복사 →", norm(DATA), "\n")
  for (f in REQUIRED) {
    to <- file.path(DATA, f)
    if (file.exists(to)) Sys.chmod(to, "0644")
    ok <- file.copy(file.path(SRC, f), to, overwrite = TRUE)
    Sys.chmod(to, "0444")
    cat(sprintf("    %-45s %8s bytes  %s\n", f, format(file.size(to), big.mark = ","),
                if (ok) "OK" else "실패"))
  }
  cat("\n  완료. 다음: Rscript RUN_ALL.R  (RStudio: RUN_ALL.R 열고 Source)\n",
      "  정상이면 마지막에  합계 238 238 0  이 나옵니다.\n\n")
}
