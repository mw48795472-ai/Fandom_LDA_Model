# 03 — 팬덤별 Spearman 추세(유효 연도 4개 이상)와 상위 팬덤 연도 칸 부트스트랩 CI
logline("== 03 팬덤별 추세")
tr_py <- read_utf8("fandom_trend_v7.csv"); v <- panel[panel$valid_cell == 1, ]
res <- do.call(rbind, lapply(split(v, v$fandom), function(d) {
  if (nrow(d) < 4) return(NULL)
  d <- d[order(d$year), ]; rv <- cor(d$year, d$n_total, method = "spearman")
  dl <- d[!is.na(d$loyalty_density), ]; rl <- if (nrow(dl) >= 4) cor(dl$year, dl$loyalty_density, method = "spearman") else NA
  ds <- d[!is.na(d$spillover_density), ]; rs <- if (nrow(ds) >= 4) cor(ds$year, ds$spillover_density, method = "spearman") else NA
  data.frame(fandom = d$fandom[1], n = nrow(d), rho_volume = rv, rho_loyalty = rl, rho_spillover = rs)
}))
logline(sprintf("추세 팬덤 %d | 규모 ρ 중앙값 %.3f (양수 %d) | 충성도 밀도 ρ 중앙값 %.3f | 파급효과 밀도 ρ 중앙값 %.3f",
                nrow(res), median(res$rho_volume), sum(res$rho_volume > 0), median(res$rho_loyalty, na.rm = TRUE), median(res$rho_spillover, na.rm = TRUE)))
m <- merge(res, tr_py[, c("fandom", "rho_volume")], by = "fandom", suffixes = c("_r", "_py")); logline("규모 ρ 파이썬 일치: ", sum(abs(m$rho_volume_r - m$rho_volume_py) < 5e-4), "/", nrow(m))
# 부트스트랩: 문장 단위 재표집 (파이썬과 같은 규칙, 시드는 다르므로 CI 폭만 비교)
tags <- read_utf8("sentence_time_tags_v7.csv"); ev <- read.csv(file.path(dirname(dirname(RDIR)), "v7_final_10020", "index_methodology", "evidence_score_by_sentence_v7.csv"), fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
stopifnot(nrow(tags) == nrow(ev)); tags$score <- ev$evidence_score; tags <- tags[!is.na(tags$event_year) & tags$event_year >= 2015, ]
bt_py <- read_utf8("bootstrap_year_cells_v7.csv"); set.seed(0); B <- 1000; wid <- c()
for (i in seq_len(nrow(bt_py))) {
  s <- tags$score[tags$fandom == bt_py$fandom[i] & tags$event_year == bt_py$year[i] & tags$bullet_type == "loyalty"]
  if (length(s) < 3 || is.na(bt_py$loyalty_lo[i])) next
  draws <- replicate(B, mean(sample(s, length(s), replace = TRUE))); ci <- quantile(draws, c(.025, .975))
  wid <- c(wid, (ci[2] - ci[1]) / (bt_py$loyalty_hi[i] - bt_py$loyalty_lo[i]))
}
logline(sprintf("부트스트랩 CI 폭 비(R/파이썬, 충성도 밀도) 중앙값 %.3f (칸 %d)", median(wid), length(wid)))
