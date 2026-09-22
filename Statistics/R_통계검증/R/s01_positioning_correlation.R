# -*- coding: utf-8 -*-
# =============================================================================
# 보고서 2.1절 — 포지셔닝 맵 두 축(팬충성도 × 파급효과) 상관계수 분석 및 통계적 검증
# =============================================================================
# 정답지: data/positioning_map_correlation_live_v7.json
#
# R 표준 함수(cor.test, shapiro.test, lm, chisq.test, cooks.distance, rstandard)와
# car::vif를 써서, 동봉된 Python 구현과 같은 값이 나오는지까지 확인한다.

source(file.path(dirname(sub("^--file=", "",
       commandArgs(trailingOnly = FALSE)[grep("^--file=",
       commandArgs(trailingOnly = FALSE))])), "common.R"))

run_s01 <- function() {
  df    <- load_scores("live")
  truth <- load_json("positioning_map_correlation_live_v7.json")
  n     <- nrow(df)

  ck <- Checker(sprintf("보고서 2.1절 — 포지셔닝 맵 상관계수 분석 및 통계적 검증 (n=%d)", n))
  ck_check(ck, "n", n, truth$n)

  # ---- (1) Pearson ----------------------------------------------------------
  pt <- cor.test(df$loyalty_score, df$spillover_score, method = "pearson")
  ci <- pearson_ci95(unname(pt$estimate), n)
  ck_check(ck, "Pearson r", round(unname(pt$estimate), 4), truth$pearson$r)
  ck_check(ck, "Pearson p", pt$p.value, truth$pearson$p_value, tol = 1e-12)
  ck_check(ck, "Pearson 95%CI 하한", round(ci[1], 4), truth$pearson$ci95[[1]])
  ck_check(ck, "Pearson 95%CI 상한", round(ci[2], 4), truth$pearson$ci95[[2]])
  ck_check(ck, "결정계수 R²", round(unname(pt$estimate)^2, 4), truth$pearson$r_squared)

  # ---- (2) Spearman ---------------------------------------------------------
  st <- suppressWarnings(cor.test(df$loyalty_score, df$spillover_score, method = "spearman"))
  ck_check(ck, "Spearman ρ", round(unname(st$estimate), 4), truth$spearman$rho)
  ck_check(ck, "Spearman p", st$p.value, truth$spearman$p_value, tol = 1e-6,
           note = "R은 타이 보정 시 근사 p를 쓰므로 Python(scipy)과 미세 차이 가능")

  # ---- (3) Shapiro-Wilk -----------------------------------------------------
  for (key in c("loyalty_score", "spillover_score")) {
    sw <- shapiro.test(df[[key]])
    tt <- truth$normality[[key]]
    ck_check(ck, sprintf("Shapiro-Wilk W — %s", key),
             round(unname(sw$statistic), 4), tt$W)
    ck_check(ck, sprintf("Shapiro-Wilk p — %s", key), sw$p.value, tt$p_value, tol = 1e-6)
    ck_check(ck, sprintf("정규성 α=.05 기각 안함 — %s", key),
             sw$p.value > 0.05, tt$normal_at_0.05)
  }

  # ---- (4) 각 점수 대 활동량 ------------------------------------------------
  for (pair in list(c("loyalty_score", "loyalty_score_vs_activity"),
                    c("spillover_score", "spillover_score_vs_activity"))) {
    p <- cor.test(df[[pair[1]]], df$activity)
    tt <- truth$each_score_vs_activity[[pair[2]]]
    ck_check(ck, sprintf("r — %s", pair[2]), round(unname(p$estimate), 4), tt$r)
    ck_check(ck, sprintf("p — %s", pair[2]), p$p.value, tt$p_value, tol = 1e-12)
  }

  # ---- (5) 다중회귀 ---------------------------------------------------------
  fit <- lm(spillover_score ~ loyalty_score + activity, data = df)
  s   <- ols_summary(fit)
  mr  <- truth$multiple_regression_spillover_on_loyalty_activity
  ck_check(ck, "다중회귀 R²", round(s$r_squared, 4), mr$r_squared)
  ck_check(ck, "다중회귀 adj R²", round(s$adj_r_squared, 4), mr$adj_r_squared)
  ck_check(ck, "다중회귀 F", round(s$f_statistic, 3), mr$f_statistic)
  ck_check(ck, "다중회귀 F p", s$f_pvalue, mr$f_pvalue, tol = 1e-12)

  json_names <- c("intercept", "loyalty_score", "activity")
  for (i in seq_along(json_names)) {
    cc  <- mr$coefficients[[json_names[i]]]
    dec <- if (json_names[i] == "activity") 6 else 4
    ck_check(ck, sprintf("계수 — %s", json_names[i]), round(s$coef[i], dec), cc$coef)
    ck_check(ck, sprintf("SE — %s", json_names[i]), round(s$se[i], dec), cc$se)
    ck_check(ck, sprintf("t — %s", json_names[i]), round(s$t[i], 3), cc$t)
    ck_check(ck, sprintf("p — %s", json_names[i]), s$p[i], cc$p, tol = 1e-12)
  }

  # ---- (6) VIF (car) --------------------------------------------------------
  v <- vif(fit)
  for (nm in names(v)) {
    ck_check(ck, sprintf("VIF — %s (car::vif)", nm), round(unname(v[nm]), 3), mr$vif[[nm]])
  }

  # ---- (7) 영향점 — 단순회귀 spillover ~ loyalty -----------------------------
  fit1 <- lm(spillover_score ~ loyalty_score, data = df)
  ck_check(ck, "단순회귀 기울기", round(unname(coef(fit1)[2]), 4),
           truth$regression_spillover_on_loyalty$slope)
  ck_check(ck, "단순회귀 절편", round(unname(coef(fit1)[1]), 4),
           truth$regression_spillover_on_loyalty$intercept)

  inf <- influence_stats(fit1)
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

  # ---- (8) 민감도 -----------------------------------------------------------
  for (f in names(truth$sensitivity_remove_highlighted)) {
    tt <- truth$sensitivity_remove_highlighted[[f]]
    sub <- df[df$fandom != f, ]
    p <- cor.test(sub$loyalty_score, sub$spillover_score)
    ck_check(ck, sprintf("민감도 r (제외: %s)", f), round(unname(p$estimate), 4), tt$r_without)
    ck_check(ck, sprintf("민감도 p (제외: %s)", f), p$p.value, tt$p_without, tol = 1e-12)
  }

  # ---- (9) Leave-one-out ----------------------------------------------------
  r0 <- unname(pt$estimate)
  d  <- vapply(seq_len(n), function(i)
    abs(cor(df$loyalty_score[-i], df$spillover_score[-i]) - r0), numeric(1))
  loo <- truth$leave_one_out
  ck_check(ck, "LOO 최대 |Δr|", round(max(d), 4), loo$max_abs_delta_r)
  ck_check(ck, "LOO 최대 변화 팬덤", df$fandom[which.max(d)], loo$max_delta_fandom)
  ck_check(ck, "LOO 평균 |Δr|", round(mean(d), 5), loo$mean_abs_delta_r)

  # ---- (10) 4분면 카이제곱 --------------------------------------------------
  hi_l <- df$loyalty_score >= 0.5
  hi_s <- df$spillover_score >= 0.5
  tab <- matrix(c(sum(hi_l & hi_s), sum(hi_l & !hi_s),
                  sum(!hi_l & hi_s), sum(!hi_l & !hi_s)), nrow = 2, byrow = TRUE)
  cs <- chisq.test(tab, correct = TRUE)   # Yates 연속성 보정
  q  <- truth$quadrant_chi_square
  ck_check(ck, "4분면 [1,1] 핵심전략", tab[1, 1], q$table[[1]][[1]])
  ck_check(ck, "4분면 [1,2] 내부결속", tab[1, 2], q$table[[1]][[2]])
  ck_check(ck, "4분면 [2,1] 외부견인", tab[2, 1], q$table[[2]][[1]])
  ck_check(ck, "4분면 [2,2] 주변부",   tab[2, 2], q$table[[2]][[2]])
  ck_check(ck, "χ²", round(unname(cs$statistic), 4), q$chi2)
  ck_check(ck, "자유도", unname(cs$parameter), q$dof)
  ck_check(ck, "χ² p", cs$p.value, q$p_value, tol = 1e-12)
  ck_check(ck, "기댓값 [1,1]", round(cs$expected[1, 1], 2), q$expected[[1]][[1]])

  # ---- 판별타당도 -----------------------------------------------------------
  dc <- truth$design_criterion
  ck_check(ck, "판별타당도 |r| < 0.5 충족",
           abs(r0) < dc$target_abs_r_below, dc$meets_criterion,
           note = sprintf("|r|=%.4f vs 기준 %.1f", abs(r0), dc$target_abs_r_below))

  res <- ck_report(ck)
  dir.create(OUT_DIR, showWarnings = FALSE)
  writeLines(sprintf("2.1절 재현 대조: %d/%d 일치", res["ok"], res["total"]),
             file.path(OUT_DIR, "s01_positioning_correlation.txt"))
  res
}

if (sys.nframe() == 0L || identical(environment(), globalenv())) {
  if (!exists(".SOURCED_BY_VERIFY_ALL")) invisible(run_s01())
}
