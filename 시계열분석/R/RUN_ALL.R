# 시계열 패널 분석 — R 대응 코드 (파이썬 timeseries_panel_v7.py 의 핵심 통계를 base R로 다시 계산)
# 실행: 저장소 루트 또는 이 폴더에서  Rscript 시계열분석/R/RUN_ALL.R
# 입력: ../output/*.csv (파이썬이 만든 패널·태그 CSV). 결과: ../output/r_verify_summary.txt
# 필요 패키지: base R만 (jsonlite가 있으면 summary_v7.json과 자동 대조)
find_dir <- function() {
  for (cand in c("시계열분석/R", "R", ".")) if (file.exists(file.path(cand, "01_year_summary.R"))) return(normalizePath(cand))
  stop("R 폴더를 찾지 못했습니다")
}
RDIR <- find_dir(); OUT <- file.path(dirname(RDIR), "output")
read_utf8 <- function(f) read.csv(file.path(OUT, f), fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE, na.strings = c("", "NA"))
LOG <- file.path(OUT, "r_verify_summary.txt"); cat("시계열 패널 분석 — R 재계산\n", file = LOG)
logline <- function(...) { s <- paste0(..., collapse = ""); cat(s, "\n"); cat(s, "\n", file = LOG, append = TRUE) }
source(file.path(RDIR, "01_year_summary.R")); source(file.path(RDIR, "02_panel_fe.R")); source(file.path(RDIR, "03_trend_bootstrap.R"))
logline("완료: ", LOG)
