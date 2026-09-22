# -*- coding: utf-8 -*-
# =============================================================================
# 필요한 R 패키지 설치
# =============================================================================
#   Rscript install_packages.R
#
# 이 코드가 쓰는 패키지는 다섯 개다.
#   jsonlite  : 원본 JSON 로딩 (fromJSON)
#   car       : vif() — 분산팽창지수
#   ggplot2   : 진단 플롯 7종
#   ggrepel   : 겹치지 않는 점 라벨 (영향점·강조 팬덤 이름)
#   patchwork : 여러 패널을 한 장으로 합치기
#
# 나머지 통계량은 R 표준 stats 패키지 함수를 그대로 쓴다.
#   cor.test()        Pearson / Spearman 상관과 p-value
#   shapiro.test()    Shapiro-Wilk 정규성 검정
#   lm() / summary()  OLS 회귀 — 계수·표준오차·t·p·R²·adj R²·F
#   rstandard()       표준화(내부 스튜던트화) 잔차
#   cooks.distance()  Cook's distance
#   hatvalues()       leverage
#   chisq.test()      카이제곱 독립성 검정 (Yates 연속성 보정)
#   rank()            K-그리드 합성순위 (ties.method = "first")
#
# broom은 필수가 아니다. 설치돼 있으면 회귀 결과를 tidy 형식으로 볼 수 있다.
#
# ※ 패키지 루트의 RUN_ALL.R 은 이 다섯 개를 알아서 설치하므로, RStudio에서
#    RUN_ALL.R 을 Source 할 생각이라면 이 파일을 따로 돌릴 필요가 없다.

REQUIRED <- c("jsonlite", "car", "ggplot2", "ggrepel", "patchwork")
OPTIONAL <- c("broom")

install_if_missing <- function(pkgs, label) {
  missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (!length(missing)) {
    cat(sprintf("[%s] 모두 설치돼 있음: %s\n", label, paste(pkgs, collapse = ", ")))
    return(invisible(TRUE))
  }
  cat(sprintf("[%s] 설치 시도: %s\n", label, paste(missing, collapse = ", ")))
  install.packages(missing, repos = "https://cloud.r-project.org")
  still <- missing[!vapply(missing, requireNamespace, logical(1), quietly = TRUE)]
  if (length(still)) {
    cat(sprintf("[%s] 설치 실패: %s\n", label, paste(still, collapse = ", ")))
    cat("  · 사내망/오프라인 환경이라면 CRAN 미러 접근이 막혀 있을 수 있다.\n")
    cat("  · Debian/Ubuntu에서는 apt로도 설치된다:\n")
    cat(sprintf("      sudo apt-get install -y %s\n",
                paste0("r-cran-", tolower(still), collapse = " ")))
    return(invisible(FALSE))
  }
  cat(sprintf("[%s] 설치 완료\n", label))
  invisible(TRUE)
}

ok <- install_if_missing(REQUIRED, "필수")
install_if_missing(OPTIONAL, "선택")

cat("\nR 버전:", R.version.string, "\n")
for (p in c(REQUIRED, OPTIONAL)) {
  has <- requireNamespace(p, quietly = TRUE)
  cat(sprintf("  %-10s %s%s\n", p, if (has) "설치됨" else "없음",
              if (has) paste0(" (", as.character(packageVersion(p)), ")") else ""))
}

if (!ok) quit(status = 1)
cat("\n준비 완료. 다음으로 실행:\n  cd R && Rscript verify_all.R\n")
