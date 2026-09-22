# -*- coding: utf-8 -*-
# =============================================================================
# 보고서 3.8절 — K9(미디어·콘텐츠 확장)/F6 제안 검증
# =============================================================================
# 정답지: data/k9_validation_v7.json
#
# 주의: 이 절의 원본 산출은 LDA 재학습(perplexity·coherence·stability)을 포함하며,
# 그 재학습은 원본 run_lda_v6.py와 동일 코퍼스·토크나이저·벡터라이저를 요구한다.
# 해당 파일이 아카이브에 없으므로 LDA 자체를 다시 돌리지는 않는다. 대신 원본이
# 기록한 4개 지표값에서 합성순위 규칙과 결론 도출 과정을 재현한다.

source(file.path(dirname(sub("^--file=", "",
       commandArgs(trailingOnly = FALSE)[grep("^--file=",
       commandArgs(trailingOnly = FALSE))])), "common.R"))

MEDIA_KEYWORDS <- c("예능", "유튜브", "영화", "드라마", "방송", "출연")

# 동점은 그리드 등장 순서로 가른다(ordinal). R의 rank(ties.method="first")와 같다.
rank_desc <- function(v) rank(-v, ties.method = "first")
rank_asc  <- function(v) rank( v, ties.method = "first")

run_s03 <- function() {
  truth <- load_json("k9_validation_v7.json")
  ck <- Checker("보고서 3.8절 — K9/F6 제안 검증")

  ck_check(ck, "코퍼스 문서 수", truth$corpus_docs, 9614,
           note = "v7 26라운드 시점 = v7 24라운드와 동일 코퍼스")
  ck_check(ck, "어휘 수", truth$vocab_size, 11924)
  ck_check(ck, "기존 K-그리드에 K=9 부재", truth$existing_k_grid_never_tested_k9, TRUE)

  # ---- 검증 ① 합성순위 규칙 재현 --------------------------------------------
  g     <- truth$k_grid
  ks    <- vapply(g, function(x) x$k, numeric(1))
  perp  <- vapply(g, function(x) x$perplexity, numeric(1))
  coh   <- vapply(g, function(x) x$coherence, numeric(1))
  divv  <- vapply(g, function(x) x$diversity, numeric(1))
  stab  <- vapply(g, function(x) x$stability, numeric(1))
  want  <- vapply(g, function(x) x$composite_rank_sum, numeric(1))

  r_perp <- rank_asc(perp)     # 낮을수록 좋음
  r_coh  <- rank_desc(coh)     # 높을수록(덜 음수일수록) 좋음
  r_div  <- rank_desc(divv)    # 높을수록 좋음
  r_stab <- rank_desc(stab)    # 높을수록 좋음
  comp   <- r_perp + r_coh + r_div + r_stab

  cat("K-그리드 합성순위 재현 (낮을수록 상위)\n")
  cat(sprintf("  %4s%10s%9s%8s%8s%16s%7s%7s\n",
              "K", "Perp", "Coher", "Div", "Stab", "순위(P/C/D/S)", "합계", "원본"))
  for (i in seq_along(ks)) {
    cat(sprintf("  %4d%10.1f%9.3f%8.3f%8.3f%16s%7d%7d\n",
                ks[i], perp[i], coh[i], divv[i], stab[i],
                sprintf("%d/%d/%d/%d", r_perp[i], r_coh[i], r_div[i], r_stab[i]),
                comp[i], want[i]))
  }
  cat("\n")

  for (i in seq_along(ks)) {
    ck_check(ck, sprintf("합성순위합 K=%d", ks[i]), comp[i], want[i])
  }
  ck_check(ck, "채택 K (합성순위합 최소)", ks[which.min(comp)], truth$k_grid_winner$k,
           note = "K=9를 후보에 넣어도 채택값은 바뀌지 않는다")
  i9 <- which(ks == 9); i8 <- which(ks == 8)
  ck_check(ck, "K=9 합성순위합", comp[i9], 13)
  ck_check(ck, "K=8 합성순위합", comp[i8], 9)
  ck_check(ck, "K=9가 K=8보다 상위인가", comp[i9] < comp[i8], FALSE,
           note = "K=9는 순위합 13으로 K=8(9)·K=12(10)에 밀린다")

  # ---- 검증 ② 미디어 키워드 매칭 재집계 --------------------------------------
  for (pair in list(c("K=9", "topics_k9", "2"), c("K=8", "topics_k8", "3"))) {
    tag <- pair[1]; key <- pair[2]; expected <- as.numeric(pair[3])
    topics <- truth[[key]]
    n_with <- 0
    for (t in topics) {
      hits <- intersect(unlist(t$top10), MEDIA_KEYWORDS)
      ck_check(ck, sprintf("%s T%d 미디어 키워드 수(top10)", tag, t$topic),
               length(hits), t$n_media_hits_top10)
      if (length(hits) > 0) n_with <- n_with + 1
    }
    ck_check(ck, sprintf("%s 미디어 키워드가 등장한 토픽 수", tag), n_with, expected)
  }

  t0_9 <- unlist(truth$topics_k9[[1]]$top10)
  t0_8 <- unlist(truth$topics_k8[[1]]$top10)
  ov <- intersect(t0_9, t0_8)
  ck_check(ck, "K=9 T0 ∩ K=8 T0 단어 수", length(ov), NULL,
           note = paste("겹치는 단어:", paste(sort(ov), collapse = ", ")))

  # ---- [불일치 기록] 보고서 본문 서술 대 원본 JSON ---------------------------
  # 보고서 3.8절 검증② 본문:
  #   "미디어 키워드가 등장한 토픽은 T0 한 곳(3개: 드라마·유튜브·영화)과
  #    T1 한 곳(0개: )뿐이었고, 나머지 7개 토픽은 0건이었다."
  #   "K=8에서도 미디어 키워드가 등장하는 토픽은 T0 한 곳(4개)뿐이었다."
  cat("[불일치 기록] 보고서 3.8절 검증② 본문 서술 대 원본 JSON\n")
  for (pair in list(c("K=9", "topics_k9"), c("K=8", "topics_k8"))) {
    tag <- pair[1]; topics <- truth[[pair[2]]]
    real <- Filter(function(t) t$n_media_hits_top10 > 0, topics)
    desc <- paste(vapply(real, function(t)
      sprintf("T%d(%d개: %s)", t$topic, t$n_media_hits_top10,
              paste(unlist(t$media_hits_top10), collapse = "·")), character(1)),
      collapse = ", ")
    cat(sprintf("  %s: 본문 서술 = T0 한 곳뿐 / 원본 JSON = %d개 토픽 %s\n",
                tag, length(real), desc))
  }
  cat(sprintf("  → K=9 T3 상위10단어: %s\n",
              paste(unlist(truth$topics_k9[[4]]$top10), collapse = ", ")))
  cat("     사실상 '방송출연' 성격의 토픽이며, 본문이 '나머지 7개 토픽은 0건'이라고\n")
  cat("     서술한 것과 원본 데이터가 어긋난다. 다만 K=8 유지라는 결론 자체는\n")
  cat("     검증①(합성순위합 13 vs 9)과 검증③(실루엣 0.099→0.081)이 독립적으로\n")
  cat("     뒷받침하므로 바뀌지 않는다.\n\n")
  ck_check(ck, "본문 '나머지 7개 토픽 0건' 서술이 원본과 일치",
           sum(vapply(truth$topics_k9, function(t) t$n_media_hits_top10 > 0, logical(1))) == 1,
           FALSE,
           note = "원본 JSON 기준 K=9에서 미디어 키워드 보유 토픽은 T0·T3 두 곳")

  # ---- 서브태그 출현 빈도 ----------------------------------------------------
  docs <- truth$corpus_docs
  for (tag in names(truth$subtag_doc_freq)) {
    v <- truth$subtag_doc_freq[[tag]]
    ck_check(ck, sprintf("서브태그 비중 — %s", tag),
             round(v$doc_freq / docs * 100, 2), v$pct_of_docs)
  }

  # ---- 검증 ③ M-그리드 트레이드오프 ------------------------------------------
  mg   <- truth$m_grid_on_k9_phi
  sil  <- vapply(mg, function(x) x$silhouette, numeric(1))
  ms   <- vapply(mg, function(x) x$m, numeric(1))
  iso  <- vapply(mg, function(x) isTRUE(x$media_topic_isolated), logical(1))
  bi   <- which.max(sil)
  ck_check(ck, "실루엣 최댓값 M", ms[bi], 5)
  ck_check(ck, "실루엣 최댓값", sil[bi], 0.099)
  fi   <- min(which(iso))
  ck_check(ck, "T0가 단독 분리되는 최소 M", ms[fi], 6)
  ck_check(ck, "그때의 실루엣", sil[fi], 0.081)
  ck_check(ck, "M=5 → M=6 실루엣 손실", round(sil[bi] - sil[fi], 3), 0.018,
           note = "F6을 얻는 대가로 군집 품질이 떨어지는 트레이드오프")
  ck_check(ck, "T0 분리가 실루엣 최댓값과 양립하는가", iso[bi], FALSE)

  res <- ck_report(ck)
  dir.create(OUT_DIR, showWarnings = FALSE)
  writeLines(sprintf("3.8절 재현 대조: %d/%d 일치", res["ok"], res["total"]),
             file.path(OUT_DIR, "s03_k9_validation.txt"))
  res
}

if (!exists(".SOURCED_BY_VERIFY_ALL")) invisible(run_s03())
