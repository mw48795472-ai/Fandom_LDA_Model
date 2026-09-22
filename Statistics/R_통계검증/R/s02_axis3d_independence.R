# -*- coding: utf-8 -*-
# =============================================================================
# 보고서 2.2절 — 3D 포지셔닝 맵 Z축(팬 요인 다양성) 독립성 검증
# =============================================================================
# 정답지: data/chart3d_correlation_live_v7.json

source(file.path(dirname(sub("^--file=", "",
       commandArgs(trailingOnly = FALSE)[grep("^--file=",
       commandArgs(trailingOnly = FALSE))])), "common.R"))

run_s02 <- function() {
  df    <- load_scores("live")
  truth <- load_json("chart3d_correlation_live_v7.json")
  n     <- nrow(df)

  ck <- Checker(sprintf("보고서 2.2절 — 3D Z축(팬 요인 다양성) 독립성 검증 (n=%d)", n))
  ck_check(ck, "n", n, truth$n)

  # ---- (1) 쌍별 상관 --------------------------------------------------------
  pairs <- list(
    loyalty_vs_spillover   = c("loyalty_score",   "spillover_score"),
    loyalty_vs_diversity   = c("loyalty_score",   "factor_diversity"),
    spillover_vs_diversity = c("spillover_score", "factor_diversity")
  )
  for (key in names(pairs)) {
    a <- df[[pairs[[key]][1]]]; b <- df[[pairs[[key]][2]]]
    tt <- truth$pairwise[[key]]
    pt <- cor.test(a, b)
    ci <- pearson_ci95(unname(pt$estimate), n)
    st <- suppressWarnings(cor.test(a, b, method = "spearman"))
    ck_check(ck, sprintf("r — %s", key), round(unname(pt$estimate), 4), tt$r)
    ck_check(ck, sprintf("p — %s", key), pt$p.value, tt$p_value, tol = 1e-12)
    ck_check(ck, sprintf("CI하한 — %s", key), round(ci[1], 4), tt$ci95[[1]])
    ck_check(ck, sprintf("CI상한 — %s", key), round(ci[2], 4), tt$ci95[[2]])
    ck_check(ck, sprintf("R² — %s", key), round(unname(pt$estimate)^2, 4), tt$r_squared)
    ck_check(ck, sprintf("ρ — %s", key), round(unname(st$estimate), 4), tt$spearman_rho)
    ck_check(ck, sprintf("ρ p — %s", key), st$p.value, tt$spearman_p, tol = 1e-6)
  }

  # ---- (2) Shapiro-Wilk -----------------------------------------------------
  for (key in c("loyalty_score", "spillover_score", "factor_diversity")) {
    sw <- shapiro.test(df[[key]]); tt <- truth$normality[[key]]
    ck_check(ck, sprintf("Shapiro-Wilk W — %s", key),
             round(unname(sw$statistic), 4), tt$W)
    ck_check(ck, sprintf("Shapiro-Wilk p — %s", key), sw$p.value, tt$p_value, tol = 1e-6)
    ck_check(ck, sprintf("정규성 유지(α=.05) — %s", key),
             sw$p.value > 0.05, tt$normal_at_0.05)
  }

  # ---- (3) 다중회귀 ---------------------------------------------------------
  fit <- lm(factor_diversity ~ loyalty_score + spillover_score, data = df)
  s   <- ols_summary(fit)
  mr  <- truth$multiple_regression_diversity_on_loyalty_spillover
  ck_check(ck, "다중회귀 R²", round(s$r_squared, 4), mr$r_squared)
  ck_check(ck, "다중회귀 adj R²", round(s$adj_r_squared, 4), mr$adj_r_squared)
  ck_check(ck, "다중회귀 F", round(s$f_statistic, 3), mr$f_statistic)
  ck_check(ck, "다중회귀 F p", s$f_pvalue, mr$f_pvalue, tol = 1e-12)

  json_names <- c("intercept", "loyalty_score", "spillover_score")
  for (i in seq_along(json_names)) {
    cc <- mr$coefficients[[json_names[i]]]
    ck_check(ck, sprintf("계수 — %s", json_names[i]), round(s$coef[i], 4), cc$coef)
    ck_check(ck, sprintf("SE — %s", json_names[i]), round(s$se[i], 4), cc$se)
    ck_check(ck, sprintf("t — %s", json_names[i]), round(s$t[i], 3), cc$t)
    ck_check(ck, sprintf("p — %s", json_names[i]), s$p[i], cc$p, tol = 1e-12)
  }

  # ---- (4) VIF --------------------------------------------------------------
  v <- vif(fit)
  for (nm in names(v)) {
    ck_check(ck, sprintf("VIF — %s (car::vif)", nm), round(unname(v[nm]), 3), mr$vif[[nm]])
  }

  # ---- (5) 영향점 -----------------------------------------------------------
  inf <- influence_stats(fit)
  ord <- order(inf$cooks_d, decreasing = TRUE)
  thr <- 4 / n
  ck_check(ck, "Cook's D 임계값 4/n", round(thr, 4), truth$cooks_d_threshold_4_over_n)
  ck_check(ck, "임계값 초과 영향점 수", sum(inf$cooks_d > thr), truth$n_high_influence_points)
  for (rk in 1:5) {
    idx <- ord[rk]; tt <- truth$influence_top5[[rk]]
    ck_check(ck, sprintf("영향점%d 팬덤", rk), df$fandom[idx], tt$fandom)
    ck_check(ck, sprintf("영향점%d 표준화잔차", rk),
             round(unname(inf$std_resid[idx]), 3), tt$std_residual)
    ck_check(ck, sprintf("영향점%d Cook's D", rk),
             round(unname(inf$cooks_d[idx]), 4), tt$cooks_d)
    ck_check(ck, sprintf("영향점%d leverage", rk),
             round(unname(inf$leverage[idx]), 4), tt$leverage)
  }

  # ---- (6) 민감도 -----------------------------------------------------------
  for (f in names(truth$sensitivity_remove_highlighted)) {
    tt  <- truth$sensitivity_remove_highlighted[[f]]
    sub <- df[df$fandom != f, ]
    fw  <- lm(factor_diversity ~ loyalty_score + spillover_score, data = sub)
    ck_check(ck, sprintf("민감도 충성도계수 (제외: %s)", f),
             round(unname(coef(fw)[2]), 4), tt$loyalty_coef_without)
    ck_check(ck, sprintf("민감도 R² (제외: %s)", f),
             round(summary(fw)$r.squared, 4), tt$r_squared_without)
  }

  # ---- (7) Leave-one-out (충성도 계수) ---------------------------------------
  base <- unname(coef(fit)[2])
  d <- vapply(seq_len(n), function(i) {
    fw <- lm(factor_diversity ~ loyalty_score + spillover_score, data = df[-i, ])
    abs(unname(coef(fw)[2]) - base)
  }, numeric(1))
  loo <- truth$leave_one_out_loyalty_coef
  ck_check(ck, "LOO 최대 |Δ계수|", round(max(d), 4), loo$max_abs_delta_coef)
  ck_check(ck, "LOO 최대 변화 팬덤", df$fandom[which.max(d)], loo$max_delta_fandom)
  ck_check(ck, "LOO 평균 |Δ계수|", round(mean(d), 5), loo$mean_abs_delta_coef)

  res <- ck_report(ck)
  dir.create(OUT_DIR, showWarnings = FALSE)
  writeLines(sprintf("2.2절 재현 대조: %d/%d 일치", res["ok"], res["total"]),
             file.path(OUT_DIR, "s02_axis3d_independence.txt"))
  res
}

if (!exists(".SOURCED_BY_VERIFY_ALL")) invisible(run_s02())
