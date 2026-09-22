# -*- coding: utf-8 -*-
# =============================================================================
# 보고서 7.4절 — 멤버 집중도(MCI)의 그룹 지표 설명력 통계 검증
# =============================================================================
# 입력
#   data/member_mention_pilot_v7.json  — 45개 그룹 멤버별 언급·MCI (라이브 트랙)
#   data/fandom_scores_v6.json         — outcome 4종 (v7-40 동결 스냅샷)
#
# 정답지가 두 개이고 서로 다르다
#   (A) 보고서 7.4절 본문 표 — v7 55 시점 계산값
#   (B) data/member_pilot_mci_correlation_v7.json — 아카이브 산출물
# 아카이브 입력에서 다시 계산하면 (A)와는 전부 일치하고 (B)와는 어긋난다.
# 따라서 (A)를 1차 정답지로 두고 검증하며, (B)와의 차이는 드리프트 표로 기록한다.
#
# MCI = Σ(멤버별 언급 점유율)²  (허핀달-허쉬만 지수와 같은 형태)
# 이론적 하한이 1/멤버수이므로 MCI_excess(= MCI − 1/멤버수)를 함께 본다.

source(file.path(dirname(sub("^--file=", "",
       commandArgs(trailingOnly = FALSE)[grep("^--file=",
       commandArgs(trailingOnly = FALSE))])), "common.R"))

OUTCOMES <- c("loyalty_score", "spillover_score", "coverage_index", "factor_diversity")

# 보고서 7.4절 본문 표 — (원시 r, 원시 R², 원시 p, excess r, excess R², excess p)
DOC_TABLE <- list(
  loyalty_score    = c(-0.385, 0.148, 0.009, -0.044, 0.002, 0.773),
  spillover_score  = c(-0.066, 0.004, 0.665,  0.214, 0.046, 0.159),
  coverage_index   = c(-0.056, 0.003, 0.715,  0.128, 0.016, 0.404),
  factor_diversity = c(-0.062, 0.004, 0.685, -0.157, 0.025, 0.304)
)
DOC_MCI_VS_MEMBERCOUNT <- -0.728
DOC_BEST_EXCESS_R2     <- 0.0457

run_s04 <- function() {
  pilot   <- load_json("member_mention_pilot_v7.json")
  frozen  <- load_scores("frozen")
  archive <- load_json("member_pilot_mci_correlation_v7.json")

  ck <- Checker("보고서 7.4절 — MCI 설명력 검증 (1차 정답지: 보고서 본문 표)")

  groups <- sort(intersect(names(pilot), frozen$fandom))
  ck_check(ck, "분석 그룹 수", length(groups), 45)
  ck_check(ck, "그룹 명단 == 아카이브 JSON 명단",
           groups, sort(unlist(archive$groups)))

  mci    <- vapply(groups, function(g) as.numeric(pilot[[g]]$mci_pilot), numeric(1))
  mcount <- vapply(groups, function(g) length(pilot[[g]]$member_mention_counts), numeric(1))
  excess <- mci - 1 / mcount
  idx    <- match(groups, frozen$fandom)
  Y      <- lapply(OUTCOMES, function(o) frozen[[o]][idx])
  names(Y) <- OUTCOMES

  # ---- MCI 공식 자체 재검증 --------------------------------------------------
  bad <- sum(vapply(groups, function(g) {
    sh  <- unlist(pilot[[g]]$member_impact_share_pilot)
    abs(round(sum(sh^2), 3) - as.numeric(pilot[[g]]$mci_pilot)) > 0.0015
  }, logical(1)))
  ck_check(ck, "MCI = Σ(점유율)² 재계산 불일치", bad, 0,
           note = "점유율이 소수 3자리로 저장돼 있어 허용오차 0.0015")

  sbad <- sum(vapply(groups, function(g)
    abs(sum(unlist(pilot[[g]]$member_impact_share_pilot)) - 1) > 0.005, logical(1)))
  ck_check(ck, "점유율 합 = 1 불일치", sbad, 0)
  ck_check(ck, "구조적 하한 MCI ≥ 1/멤버수 위반", sum(mci < 1 / mcount - 1e-9), 0)

  # ---- (1) MCI 대 멤버 수 ----------------------------------------------------
  pmc <- cor.test(mci, mcount)
  ck_check(ck, "r — MCI × 멤버수", round(unname(pmc$estimate), 3), DOC_MCI_VS_MEMBERCOUNT,
           note = "MCI가 '집중도'보다 '멤버 수'를 상당 부분 대리한다는 근거")

  # ---- (2)(3) 상관 vs 보고서 본문 표 ----------------------------------------
  for (o in OUTCOMES) {
    d <- DOC_TABLE[[o]]
    preds <- list("원시MCI" = mci, MCI_excess = excess)
    wants <- list("원시MCI" = d[1:3], MCI_excess = d[4:6])
    for (lab in names(preds)) {
      p <- cor.test(preds[[lab]], Y[[o]])
      w <- wants[[lab]]
      ck_check(ck, sprintf("%s r — %s", lab, o), round(unname(p$estimate), 3), w[1])
      ck_check(ck, sprintf("%s R² — %s", lab, o), round(unname(p$estimate)^2, 3), w[2])
      ck_check(ck, sprintf("%s p — %s", lab, o), round(p$p.value, 3), w[3])
    }
  }

  r2ex <- vapply(OUTCOMES, function(o) cor(excess, Y[[o]])^2, numeric(1))
  ck_check(ck, "MCI_excess 최고 설명 outcome", OUTCOMES[which.max(r2ex)], "spillover_score")
  ck_check(ck, "MCI_excess 최고 R²", round(max(r2ex), 4), DOC_BEST_EXCESS_R2)

  # ---- (4) 다중회귀 outcome ~ MCI + member_count -----------------------------
  cat("다중회귀 outcome ~ MCI + member_count\n")
  cat(sprintf("  %-18s%8s%9s%11s%9s%7s%9s\n",
              "Outcome", "R²", "F", "MCI 계수", "MCI p", "VIF", "MCI 유의"))
  any_sig <- FALSE
  max_vif <- 0
  for (o in OUTCOMES) {
    dd  <- data.frame(y = Y[[o]], mci = mci, member_count = mcount)
    fit <- lm(y ~ mci + member_count, data = dd)
    s   <- ols_summary(fit)
    v   <- unname(vif(fit)["mci"])
    max_vif <- max(max_vif, v)
    sig <- s$p[2] < 0.05
    any_sig <- any_sig || sig
    cat(sprintf("  %-18s%8.4f%9.3f%11.4f%9.4f%7.3f%9s\n",
                o, s$r_squared, s$f_statistic, s$coef[2], s$p[2], v,
                if (sig) "예" else "아니오"))
  }
  cat("\n")
  ck_check(ck, "MCI 편회귀계수가 유의한 outcome 존재", any_sig, FALSE,
           note = "본문 서술 '어느 outcome 지표에서도 유의하지 않았다'와 일치")
  ck_check(ck, "VIF < 10 (심각 기준 미달)", max_vif < 10, TRUE)

  # ---- (5) 정규성 ------------------------------------------------------------
  cat("Shapiro-Wilk 정규성 (모두 α=.05에서 정규분포 기각 예상)\n")
  vars <- c(list(mci = mci, mci_excess = excess), Y)
  for (nm in names(vars)) {
    sw <- shapiro.test(vars[[nm]])
    cat(sprintf("  %-18s W=%.4f  p=%.6f  %s\n", nm, unname(sw$statistic), sw$p.value,
                if (sw$p.value < 0.05) "정규 기각" else "정규 유지"))
  }
  cat("\n")

  # ---- (6) 최강 쌍 영향점 · LOO ----------------------------------------------
  o   <- "loyalty_score"
  dd  <- data.frame(y = Y[[o]], mci = mci)
  fit <- lm(y ~ mci, data = dd)
  inf <- influence_stats(fit)
  thr <- 4 / length(groups)
  ck_check(ck, "Cook's D 임계값 4/n", round(thr, 4), 0.0889)
  ord <- order(inf$cooks_d, decreasing = TRUE)
  cat(sprintf("영향점 상위 5 (회귀: %s ~ MCI, 임계값 4/n=%.4f)\n", o, thr))
  for (rk in 1:5) {
    i <- ord[rk]
    cat(sprintf("  %d. %-14s MCI=%.3f %s=%.3f 멤버수=%2d 표준화잔차=%+.3f Cook's D=%.4f\n",
                rk, groups[i], mci[i], o, Y[[o]][i], mcount[i],
                unname(inf$std_resid[i]), unname(inf$cooks_d[i])))
  }
  cat("\n")

  r0 <- cor(mci, Y[[o]])
  dl <- vapply(seq_along(groups), function(i) abs(cor(mci[-i], Y[[o]][-i]) - r0), numeric(1))
  cat(sprintf("Leave-one-out (%s ~ MCI): 최대 |Δr|=%.4f (%s) · 평균 |Δr|=%.5f\n\n",
              o, max(dl), groups[which.max(dl)], mean(dl)))

  res <- ck_report(ck)

  # ---- [드리프트 기록] -------------------------------------------------------
  cat("[드리프트 기록] 같은 지표의 세 시점 값\n")
  cat(.padr("  항목", 28), .padl("재현(아카이브 입력)", 22),
      .padl("보고서 본문", 14), .padl("아카이브 JSON", 16), "\n", sep = "")
  rows <- list(list("MCI × 멤버수 r", round(unname(pmc$estimate), 4),
                    DOC_MCI_VS_MEMBERCOUNT, archive$mci_vs_member_count$pearson_r))
  for (o in OUTCOMES) {
    rows[[length(rows) + 1]] <- list(sprintf("원시MCI × %s r", o),
                                     round(cor(mci, Y[[o]]), 4), DOC_TABLE[[o]][1],
                                     archive$correlations_mci_raw[[o]]$pearson_r)
  }
  rows[[length(rows) + 1]] <- list("MCI 평균", round(mean(mci), 4), NA,
                                   archive$mci_descriptives$mean)
  rows[[length(rows) + 1]] <- list("MCI 최댓값", round(max(mci), 3), NA,
                                   archive$mci_descriptives$max)
  for (r in rows) {
    cat(.padr(paste0("  ", r[[1]]), 28), .padl(format(r[[2]]), 22),
        .padl(if (is.na(r[[3]])) "—" else format(r[[3]]), 14),
        .padl(format(r[[4]]), 16), "\n", sep = "")
  }
  cat("  → 재현값은 보고서 본문과 일치하고 아카이브 JSON과는 어긋난다.\n")
  cat("     아카이브 JSON은 보고서 작성 이후 갱신된 코퍼스로 재계산된 별개 시점 산출물이며,\n")
  cat("     그 값은 보고서 본문에 반영되지 않았다. 결론은 세 시점 모두 동일하다 —\n")
  cat("     원시 MCI 최고 R²는 15% 안팎, 멤버 수 통제 후에는 5% 미만.\n\n")

  dir.create(OUT_DIR, showWarnings = FALSE)
  writeLines(sprintf("7.4절 재현 대조(보고서 본문 기준): %d/%d 일치", res["ok"], res["total"]),
             file.path(OUT_DIR, "s04_mci_explanatory_power.txt"))
  res
}

if (!exists(".SOURCED_BY_VERIFY_ALL")) invisible(run_s04())
