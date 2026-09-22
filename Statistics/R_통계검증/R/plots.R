# -*- coding: utf-8 -*-
# =============================================================================
# 진단 플롯 생성 (R / ggplot2)
# =============================================================================
#   Rscript plots.R            # outputs/plots/ 에 png 7장
#
# ※ 이 파일은 터미널(Rscript) 전용이다. RStudio에서 Source 버튼으로 그림을
#    보려면 패키지 루트의 RUN_ALL.R 을 쓴다 — 같은 ggplot 코드가 들어 있고,
#    Plots 창 출력까지 함께 처리한다.
#
# 동봉된 Python 스크립트(src/plots.py)가 같은 7종을 같은 데이터로 그린다 —
# 두 언어의 결과를 나란히 비교할 수 있다.
#
# 그림 목록 (파일명 끝의 _R 로 Python 산출물과 구분한다)
#   fig1_positioning_scatter_R   2.1 포지셔닝 맵 — 산점도 + 회귀선 + 4분면
#   fig2_sign_reversal_R         2.1 활동량 통제 시 부호 반전 (부분회귀 plot)
#   fig3_qq_normality_R          2.1·2.2 Q-Q plot 3종
#   fig4_influence_R             2.1·2.2 영향점 진단 (leverage × 표준화잔차)
#   fig5_axis3d_pairs_R          2.2 3D 세 축 쌍별 산점도
#   fig6_k9_grid_R               3.8 K-그리드 합성순위 · M-그리드 실루엣
#   fig7_mci_R                   7.4 MCI 구조적 하한 · 설명력(R²) 비교

source(file.path(dirname(sub("^--file=", "",
       commandArgs(trailingOnly = FALSE)[grep("^--file=",
       commandArgs(trailingOnly = FALSE))])), "common.R"))

suppressPackageStartupMessages({
  library(ggplot2); library(ggrepel); library(patchwork)
})

PLOT_DIR <- file.path(OUT_DIR, "plots")
dir.create(PLOT_DIR, recursive = TRUE, showWarnings = FALSE)

HIGHLIGHT <- c("BTS", "임영웅", "리센느(RESCENE)")

# --- 한글 폰트 ---------------------------------------------------------------
KO_FONT <- ""
local({
  if (identical(.Platform$OS.type, "windows")) {
    tryCatch({
      wf <- get("windowsFonts", envir = asNamespace("grDevices"))
      wfont <- get("windowsFont", envir = asNamespace("grDevices"))
      do.call(wf, stats::setNames(list(wfont("Malgun Gothic")), "KO"))
    }, error = function(e) NULL)
    KO_FONT <<- "Malgun Gothic"
  } else if (identical(Sys.info()[["sysname"]], "Darwin")) {
    KO_FONT <<- "AppleGothic"
  } else {
    cand <- c("NanumGothic", "NanumBarunGothic", "Noto Sans CJK KR", "Noto Sans CJK JP")
    hit <- tryCatch({
      fams <- system("fc-list :lang=ko family", intern = TRUE, ignore.stderr = TRUE)
      fams <- trimws(unique(unlist(strsplit(paste(fams, collapse = ","), ","))))
      h <- cand[cand %in% fams]; if (length(h)) h[1] else ""
    }, error = function(e) "")
    KO_FONT <<- hit
  }
})
invisible(tryCatch(
  if (identical(.Platform$OS.type, "windows") && !isTRUE(l10n_info()$`UTF-8`)) Sys.setlocale("LC_CTYPE", "Korean")
  else if (!isTRUE(l10n_info()$`UTF-8`)) {
    for (lc in c("C.UTF-8", "en_US.UTF-8", "ko_KR.UTF-8"))
      if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", lc)))) break
  }, error = function(e) NULL))

DF_LIVE <- load_scores("live")

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

# --- 실행 -------------------------------------------------------------------
cat("진단 플롯 7종 생성 (ggplot2)\n")
render("fig1_positioning_scatter_R", 1480, 1180, build_fig1(DF_LIVE))
render("fig2_sign_reversal_R",       2100,  980, build_fig2(DF_LIVE))
render("fig3_qq_normality_R",        2200,  840, build_fig3(DF_LIVE))
render("fig4_influence_R",           2100, 1040, build_fig4(DF_LIVE))
render("fig5_axis3d_pairs_R",        2260,  860, build_fig5(DF_LIVE))
render("fig6_k9_grid_R",             2160, 1000, build_fig6())
render("fig7_mci_R",                 2160, 1020, build_fig7())
cat("완료 —", PLOT_DIR, "\n")
