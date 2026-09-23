# 02 — 팬덤·연도 이원 고정효과 회귀와 충성도–파급효과 패널 계수
v <- panel[panel$valid_cell == 1, ]; v$fandom <- factor(v$fandom); v$year_f <- factor(v$year)
logline("== 02 고정효과 회귀")
for (ax in c("loyalty_density", "spillover_density")) {
  d <- v[!is.na(v[[ax]]), ]
  m0 <- lm(as.formula(paste(ax, "~ fandom")), d); m1 <- lm(as.formula(paste(ax, "~ fandom + year_f")), d); m2 <- lm(as.formula(paste(ax, "~ fandom + year_f + late_round_share")), d)
  a <- anova(m0, m1)
  logline(sprintf("%s: n=%d  R2(fandom FE)=%.4f  R2(two-way)=%.4f  연도효과 F=%.3f p=%.4g  late_round_share 계수=%.4f p=%.4g",
                  ax, nrow(d), summary(m0)$r.squared, summary(m1)$r.squared, a$F[2], a$`Pr(>F)`[2], coef(m2)["late_round_share"], summary(m2)$coefficients["late_round_share", 4]))
}
d2 <- v[!is.na(v$loyalty_density) & !is.na(v$spillover_density), ]
mb <- lm(spillover_density ~ loyalty_density, d2); mw <- lm(spillover_density ~ loyalty_density + fandom + year_f, d2)
logline(sprintf("S ~ L: 통합 계수=%.4f p=%.4g | 팬덤·연도 FE 계수=%.4f p=%.4g | n=%d",
                coef(mb)[2], summary(mb)$coefficients[2, 4], coef(mw)["loyalty_density"], summary(mw)$coefficients["loyalty_density", 4], nrow(d2)))
d3 <- v; d3$log_n <- log(d3$n_total); m3 <- lm(log_n ~ fandom + year_f, d3)
ye <- coef(m3)[grep("^year_f", names(coef(m3)))]; logline("log 문장 수 연도 효과(2015 대비): ", paste(sprintf("%s %+.2f", sub("year_f", "", names(ye)), ye), collapse = ", "))
if (requireNamespace("jsonlite", quietly = TRUE)) {
  S <- jsonlite::fromJSON(file.path(OUT, "summary_v7.json"))
  logline(sprintf("파이썬 대조: 충성도 연도효과 F %.3f / 파급효과 F %.3f / within 계수 %.4f", S$regressions$loyalty_density$year_fe_F, S$regressions$spillover_density$year_fe_F, S$regressions$loyalty_spillover_panel$within_coef_two_way_fe))
}
