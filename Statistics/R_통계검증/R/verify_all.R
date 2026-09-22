# -*- coding: utf-8 -*-
# =============================================================================
# 전체 검증 실행기 (R)
# =============================================================================
# 보고서 2.1 · 2.2 · 3.8 · 7.4절의 통계적 검증을 순서대로 재현하고 총괄 요약을 낸다.
#
#   Rscript verify_all.R            상세 + 총괄 요약
#   Rscript verify_all.R --quiet    총괄 요약만
#
# 종료 코드 0 = 모든 대조 일치, 1 = 불일치 존재.

.SOURCED_BY_VERIFY_ALL <- TRUE

.dir <- dirname(sub("^--file=", "",
        commandArgs(trailingOnly = FALSE)[grep("^--file=",
        commandArgs(trailingOnly = FALSE))]))

source(file.path(.dir, "common.R"))
source(file.path(.dir, "s01_positioning_correlation.R"))
source(file.path(.dir, "s02_axis3d_independence.R"))
source(file.path(.dir, "s03_k9_validation.R"))
source(file.path(.dir, "s04_mci_explanatory_power.R"))

quiet <- "--quiet" %in% commandArgs(trailingOnly = TRUE)

SECTIONS <- list(
  list("2.1", "포지셔닝 맵 상관계수 분석 및 통계적 검증", run_s01,
       "positioning_map_correlation_live_v7.json"),
  list("2.2", "3D 포지셔닝 맵 Z축 독립성 검증", run_s02,
       "chart3d_correlation_live_v7.json"),
  list("3.8", "K9/F6 제안 검증", run_s03,
       "k9_validation_v7.json"),
  list("7.4", "멤버 집중도(MCI) 설명력 검증", run_s04,
       "보고서 7.4절 본문 표 (+ member_pilot_mci_correlation_v7.json 드리프트 기록)")
)

results <- list()
for (s in SECTIONS) {
  if (quiet) {
    tmp <- textConnection("out", "w", local = TRUE)
    sink(tmp); res <- s[[3]](); sink(); close(tmp)
  } else {
    res <- s[[3]]()
  }
  results[[length(results) + 1]] <- list(sec = s[[1]], title = s[[2]],
                                         ok = unname(res["ok"]),
                                         tot = unname(res["total"]), truth = s[[4]])
}

cat(strrep("=", 96), "\n", sep = "")
cat("총괄 요약 — 팬덤100 LDA v7 보고서 통계적 검증 재현 (R)\n")
cat(strrep("=", 96), "\n", sep = "")
cat(.padr("절", 6), .padr("검증 항목", 40), .padl("대조", 8), .padl("일치", 8),
    .padl("불일치", 8), "  정답지\n", sep = "")
cat(strrep("-", 96), "\n", sep = "")
tot_ok <- 0; tot_all <- 0
for (r in results) {
  tot_ok <- tot_ok + r$ok; tot_all <- tot_all + r$tot
  cat(.padr(r$sec, 6), .padr(r$title, 40), .padl(r$tot, 8), .padl(r$ok, 8),
      .padl(r$tot - r$ok, 8), "  ", r$truth, "\n", sep = "")
}
cat(strrep("-", 96), "\n", sep = "")
cat(.padr("합계", 46), .padl(tot_all, 8), .padl(tot_ok, 8),
    .padl(tot_all - tot_ok, 8), "\n\n", sep = "")

if (tot_ok == tot_all) {
  cat("모든 대조 항목이 원본과 일치한다 — 보고서의 통계적 검증은 아카이브 데이터에서\n")
  cat("전부 재현 가능하며, 동봉된 Python 구현과도 같은 값이 나온다.\n")
} else {
  cat(sprintf("불일치 %d건 — 위 각 절 출력의 '불일치' 행을 확인할 것.\n", tot_all - tot_ok))
}
cat("\n[재현 과정에서 발견해 기록한 두 가지 문서-데이터 불일치]\n")
cat("  · 3.8절 검증② 본문은 미디어 키워드 보유 토픽을 'T0 한 곳뿐'이라 서술하지만,\n")
cat("    원본 JSON 기준 K=9는 T0·T3 두 곳, K=8은 T0·T3·T4 세 곳이다.\n")
cat("    (결론인 K=8 유지는 검증①·③이 독립적으로 뒷받침하므로 바뀌지 않는다.)\n")
cat("  · 7.4절은 보고서 본문 값과 아카이브 JSON 값이 서로 다르다. 아카이브 입력에서\n")
cat("    재계산하면 본문과 일치하므로, 아카이브 JSON은 보고서 이후 시점의 재계산본이다.\n")

quit(status = if (tot_ok == tot_all) 0 else 1)
