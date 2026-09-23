# 01 — 연도별 횡단면 상관 (팬덤×연도 패널, 5문장 이상 칸, 그해 20개 이상 팬덤)
panel <- read_utf8("fandom_year_panel_v7.csv"); ys_py <- read_utf8("year_summary_v7.csv")
logline("== 01 연도별 횡단면 상관")
logline("칸 ", nrow(panel), " | 유효 칸 ", sum(panel$valid_cell == 1))
for (y in 2015:2026) {
  d <- panel[panel$year == y & panel$valid_cell == 1 & !is.na(panel$loyalty_density) & !is.na(panel$spillover_density), ]
  if (nrow(d) < 20) next
  r <- cor(d$loyalty_density, d$spillover_density); rho <- cor(d$loyalty_density, d$spillover_density, method = "spearman")
  py <- ys_py[ys_py$year == y, ]
  logline(sprintf("%d  n=%d  r=%.4f (py %.4f)  rho=%.4f (py %.4f)  %s", y, nrow(d), r, py$r_density, rho, py$rho_density, ifelse(abs(r - py$r_density) < 5e-4 & abs(rho - py$rho_density) < 5e-4, "일치", "불일치")))
}
