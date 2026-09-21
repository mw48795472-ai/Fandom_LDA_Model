# -*- coding: utf-8 -*-
"""
최종 제출본 수치(docs: KEY_FINDINGS.md / METHODOLOGY.md, 분석보고서 PDF) ↔ 저장소 데이터 파일 정합성 검증.

이 프로젝트의 다른 검증 스크립트와 같은 원칙("결과를 눈으로 믿지 않고 프로그램이 재대조")으로,
data/v7_final/ 에 있는 최종 파일들에서 보고서 수치를 실제로 재계산해 비교하고, 재현되는 것과
재현되지 않는 것을 항목별로 그대로 출력한다. 어떤 수치도 맞추기 위해 조정하지 않는다.

검증 대상 (전부 저장소 안의 파일만 사용):
  [A] 라이브 코퍼스 fandoms_v3_100.json(10,020건) 자체 규모 — 팬덤 100개, 불릿 10,020건
  [B] 언어·도메인 요약 language_domain_summary_v7.json — 14개 언어, 불릿 합 10,020, 도메인 수
  [C] 충성도·파급효과 점수 — METHODOLOGY.md 2-4절 EvidenceScore 산식을 10,020건 코퍼스에 그대로 적용해
      3D 포지셔닝맵 HTML 내장 payload(chart3d_payload_live_reference_v7.json)의 100개 팬덤 점수·표본
      평균(0.3710/0.2661)·4구획(24/17/10/49)이 재현되는지
  [D] 강건성 통계(KEY_FINDINGS.md "상관/회귀", "3D 매트릭스 축 독립성", "영향점/강건성") — 라이브 점수 기준
  [E] 동결 스냅샷(v7-40, 7,350건) 산출물 fandom_scores_v6.csv / fan_persona_v7.json — activity 합 7,350,
      페르소나 4유형 카운트(43/31/17/9)와 상위 2개 F코드 규칙, factor_specific_* = share × score
  [F] 라이브 참고 재적합 진단 lda_v6_diagnostics_live_reference_v7.json — K=8, M=5, 실루엣 0.046 (게이트 기각)
  [G] Persona_결정공간.html 내장 데이터 — K=10/M=5/0.267, 토픽→F코드 배정이 METHODOLOGY.md 표와 일치하는지

실행: python verify_v7_final_consistency.py   (scipy, statsmodels 필요)
"""
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
D = BASE / "data" / "v7_final"

PASS, FAIL, INFO = "[일치]", "[불일치]", "[참고]"
results = []


def check(label, ok, detail=""):
    tag = PASS if ok else FAIL
    results.append((label, ok))
    print(f"{tag} {label}" + (f" — {detail}" if detail else ""))


def info(label, detail=""):
    print(f"{INFO} {label}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# [A] 라이브 코퍼스 규모
# ---------------------------------------------------------------------------
print("\n[A] 라이브 코퍼스 fandoms_v3_100.json")
with open(D / "fandoms_v3_100.json", encoding="utf-8") as f:
    fandoms = json.load(f)
n_bullets = sum(len(fd.get("loyalty", [])) + len(fd.get("spillover", [])) for fd in fandoms)
check("팬덤 수 = 100", len(fandoms) == 100, f"{len(fandoms)}")
check("근거문장(불릿) 수 = 10,020 (데이터 파일 저장 건수)", n_bullets == 10020, f"{n_bullets}")
empty_url = sum(1 for fd in fandoms for k in ("loyalty", "spillover") for b in fd[k] if not b.get("u"))
check("URL 누락 불릿 0건", empty_url == 0, f"{empty_url}")

# ---------------------------------------------------------------------------
# [B] 언어·도메인 요약
# ---------------------------------------------------------------------------
print("\n[B] language_domain_summary_v7.json (보고서 표 '자료 선정 및 사용한 데이터')")
with open(D / "language_domain_summary_v7.json", encoding="utf-8") as f:
    langs = json.load(f)
lang_total = sum(x["total_bullets"] for x in langs)
check("언어권 수 = 14", len(langs) == 14, f"{len(langs)}")
check("14개 언어 불릿 합 = 10,020", lang_total == 10020, f"{lang_total}")
by = {x["lang_code"]: x for x in langs}
check("한국어 5,551건(55.4%)", by["ko"]["total_bullets"] == 5551, f"{by['ko']['total_bullets']} ({by['ko']['total_bullets']/lang_total:.1%})")
check("영어 2,195건(21.9%)", by["en"]["total_bullets"] == 2195, f"{by['en']['total_bullets']} ({by['en']['total_bullets']/lang_total:.1%})")
check("일본어 520건(5.2%) — 보고서 표 값", by["ja"]["total_bullets"] == 520, f"{by['ja']['total_bullets']} ({by['ja']['total_bullets']/lang_total:.1%})")
check("중국어 458건(4.6%)", by["zh"]["total_bullets"] == 458, f"{by['zh']['total_bullets']} ({by['zh']['total_bullets']/lang_total:.1%})")
check("한국어 도메인 수 = 704 (보고서/KEY_FINDINGS의 '704개 도메인'은 한국어권 도메인 수)", by["ko"]["total_domains"] == 704, f"{by['ko']['total_domains']}")
dom_sum = sum(x["total_domains"] for x in langs)
hosts = set()
for fd in fandoms:
    for k in ("loyalty", "spillover"):
        for b in fd[k]:
            m = re.match(r"https?://([^/\s]+)", b.get("u", "").strip())
            if m:
                h = m.group(1).lower()
                hosts.add(h[4:] if h.startswith("www.") else h)
info("14개 언어권 도메인 수 단순 합", f"{dom_sum:,}개 (언어권 간 중복 도메인 포함, 예: 위키피디아)")
info("코퍼스 URL 호스트(www. 제거) 고유 개수", f"{len(hosts):,}개")

# ---------------------------------------------------------------------------
# [C] 충성도·파급효과 점수 재현 (METHODOLOGY.md 2-4절 산식 그대로)
# ---------------------------------------------------------------------------
print("\n[C] EvidenceScore 산식으로 라이브 점수 재현 (chart3d payload 대조)")
NUM_PATTERN = re.compile(r"\d+[\.,]?\d*\s*(만|억|조|%|명|장|위|회|건|주|배|년)")
LOYALTY_BONUS_KW = ["기부", "돌파", "매진", "출범", "창단", "결성", "총공", "역사", "지속", "확장", "1위", "최초",
                    "신기록", "밀리언셀러", "팬클럽", "팬카페", "결속", "충성", "세대"]
SPILLOVER_BONUS_KW = ["경제효과", "매출", "관광", "지자체", "앰버서더", "모델", "브랜드", "팝업", "협업", "관중",
                      "방문", "상권", "지역", "홍보대사", "수익", "투어", "콘서트", "소비"]


def evidence_score(items, bonus):
    s = 0.0
    for it in items:
        t = it["t"]
        s += 1.0 + 0.5 * len(NUM_PATTERN.findall(t)) + 0.3 * sum(1 for kw in bonus if kw in t)
    return s


raw = {fd["fandom"]: (evidence_score(fd.get("loyalty", []), LOYALTY_BONUS_KW),
                      evidence_score(fd.get("spillover", []), SPILLOVER_BONUS_KW)) for fd in fandoms}
lv = [v[0] for v in raw.values()]
sv = [v[1] for v in raw.values()]
lmin, lmax, smin, smax = min(lv), max(lv), min(sv), max(sv)
recomputed = {k: (round((v[0] - lmin) / (lmax - lmin), 3), round((v[1] - smin) / (smax - smin), 3)) for k, v in raw.items()}

with open(D / "chart3d_payload_live_reference_v7.json", encoding="utf-8") as f:
    payload = json.load(f)
rows = payload["rows"]
mism = [r["fandom"] for r in rows if abs(r["loyalty"] - recomputed[r["fandom"]][0]) > 1e-9
        or abs(r["spillover"] - recomputed[r["fandom"]][1]) > 1e-9]
check("100개 팬덤 loyalty/spillover 점수 재현 (불일치 0)", len(mism) == 0, f"불일치 {len(mism)}건 {mism[:5]}")
check("payload corpus_total_evidence = 10,020", payload["corpus_total_evidence"] == 10020)
L = np.array([r["loyalty"] for r in rows]); S = np.array([r["spillover"] for r in rows])
Dv = np.array([r["diversity"] for r in rows]); A = np.array([r["activity"] for r in rows])
names = [r["fandom"] for r in rows]
check("Loyalty 평균 = 0.3710", round(float(L.mean()), 4) == 0.3710, f"{L.mean():.5f}")
check("Spillover 평균 = 0.2661", round(float(S.mean()), 4) == 0.2661, f"{S.mean():.5f}")
mL, mS = L.mean(), S.mean()
q = {"핵심전략형": int(((L >= mL) & (S >= mS)).sum()), "내부결속형": int(((L >= mL) & (S < mS)).sum()),
     "외부견인형": int(((L < mL) & (S >= mS)).sum()), "주변부": int(((L < mL) & (S < mS)).sum())}
check("4구획 = 핵심전략형24·내부결속형17·외부견인형10·주변부49",
      q == {"핵심전략형": 24, "내부결속형": 17, "외부견인형": 10, "주변부": 49}, f"{q}")
hi = {r["fandom"]: r for r in rows}
check("하이라이트 3사례 라이브 점수: BTS 0.972/1.000, 임영웅 0.950/0.517, 리센느 0.359/0.262 (동결 CSV 값과 다름 — [E] 참고)",
      (hi["BTS"]["loyalty"], hi["BTS"]["spillover"]) == (0.972, 1.0) and (hi["임영웅"]["loyalty"], hi["임영웅"]["spillover"]) == (0.95, 0.517)
      and (hi["리센느(RESCENE)"]["loyalty"], hi["리센느(RESCENE)"]["spillover"]) == (0.359, 0.262),
      f"BTS {hi['BTS']['loyalty']}/{hi['BTS']['spillover']}, 임영웅 {hi['임영웅']['loyalty']}/{hi['임영웅']['spillover']}, 리센느 {hi['리센느(RESCENE)']['loyalty']}/{hi['리센느(RESCENE)']['spillover']}")

# ---------------------------------------------------------------------------
# [D] 강건성 통계
# ---------------------------------------------------------------------------
print("\n[D] 강건성 통계 (KEY_FINDINGS.md) — 라이브 점수 기준")
try:
    from scipy import stats
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError as e:
    print(f"  scipy/statsmodels 미설치로 [D] 생략: {e}")
    stats = None
if stats is not None:
    sh_l, sh_s = stats.shapiro(L).pvalue, stats.shapiro(S).pvalue
    check("Shapiro-Wilk 둘 다 p<.05 (정규성 기각)", sh_l < 0.05 and sh_s < 0.05, f"p={sh_l:.2e}, {sh_s:.2e}")
    pr = stats.pearsonr(L, S); spr = stats.spearmanr(L, S)
    check("Pearson r = 0.493 (p<.001)", round(pr[0], 3) == 0.493 and pr[1] < 0.001, f"r={pr[0]:.4f}, p={pr[1]:.2e}, R²={pr[0]**2:.3f}")
    check("Spearman ρ = 0.380 (p<.001)", round(spr[0], 3) == 0.380 and spr[1] < 0.001, f"ρ={spr[0]:.4f}, p={spr[1]:.2e}")
    m1 = sm.OLS(S, sm.add_constant(L)).fit()
    cd = m1.get_influence().cooks_distance[0]
    top = sorted(zip(cd, names), reverse=True)[:5]
    check("Cook's D 상위: BTS 0.5749 > god 0.284 > 이효리 0.2538 > TWICE 0.2315 > BLACKPINK 0.094",
          [n for _, n in top] == ["BTS", "god", "이효리", "TWICE", "BLACKPINK"] and round(top[0][0], 4) == 0.5749,
          ", ".join(f"{n} {c:.4f}" for c, n in top))
    X2 = sm.add_constant(np.column_stack([L, A])); m2 = sm.OLS(S, X2).fit()
    vif2 = variance_inflation_factor(X2, 1)
    check("다중회귀 R²(+activity) = 0.847, 충성도 계수 -0.200 (p<.001), VIF 1.93",
          round(m2.rsquared, 3) == 0.847 and round(m2.params[1], 3) == -0.200 and m2.pvalues[1] < 0.001 and round(vif2, 2) == 1.93,
          f"R²={m2.rsquared:.3f}, coef={m2.params[1]:.3f} (p={m2.pvalues[1]:.2e}), VIF={vif2:.3f}")
    r0 = pr[0]
    drops = {}
    for h in ["BTS", "임영웅", "리센느(RESCENE)"]:
        i = names.index(h); drops[h] = stats.pearsonr(np.delete(L, i), np.delete(S, i))[0]
    check("민감도: BTS 제외 r=0.4314 / 임영웅 제외 0.4761 / 리센느 제외 0.4932",
          round(drops["BTS"], 4) == 0.4314 and round(drops["임영웅"], 4) == 0.4761 and round(drops["리센느(RESCENE)"], 4) == 0.4932,
          ", ".join(f"{k} {v:.4f}" for k, v in drops.items()))
    dl = [abs(stats.pearsonr(np.delete(L, i), np.delete(S, i))[0] - r0) for i in range(len(L))]
    check("Leave-one-out: max|Δr|=0.0618(BTS), mean|Δr|=0.00516",
          round(max(dl), 4) == 0.0618 and names[int(np.argmax(dl))] == "BTS" and round(float(np.mean(dl)), 5) == 0.00516,
          f"max={max(dl):.4f} ({names[int(np.argmax(dl))]}), mean={np.mean(dl):.5f}")
    ld = stats.pearsonr(L, Dv); sd = stats.pearsonr(S, Dv)
    check("3D축: Loyalty-Diversity r=0.099 (p=0.327) / Spillover-Diversity r=0.461 (p<.001)",
          round(ld[0], 3) == 0.099 and round(ld[1], 3) == 0.327 and round(sd[0], 3) == 0.461 and sd[1] < 0.001,
          f"r_LD={ld[0]:.3f} (p={ld[1]:.3f}), r_SD={sd[0]:.3f} (p={sd[1]:.2e})")
    X3 = sm.add_constant(np.column_stack([L, S])); m3 = sm.OLS(Dv, X3).fit()
    vif3 = variance_inflation_factor(X3, 1)
    check("3D축 다중회귀 R²=0.234 (F=14.83, p<.001), VIF(3축)=1.321",
          round(m3.rsquared, 3) == 0.234 and round(m3.fvalue, 2) == 14.83 and m3.f_pvalue < 0.001 and round(vif3, 3) == 1.321,
          f"R²={m3.rsquared:.3f}, F={m3.fvalue:.2f}, p={m3.f_pvalue:.2e}, VIF={vif3:.3f}")
    tab = np.array([[q["핵심전략형"], q["내부결속형"]], [q["외부견인형"], q["주변부"]]])
    chi_y = stats.chi2_contingency(tab, correction=True)
    chi_n = stats.chi2_contingency(tab, correction=False)
    info("4분면 독립성 χ² — 보고서 값 χ²=8.34, p=0.0039 는 저장소 파일로 재현되지 않음",
         f"라이브 4구획표 {tab.tolist()} 기준 재계산: Yates χ²={chi_y[0]:.2f} (p={chi_y[1]:.1e}), 보정없음 χ²={chi_n[0]:.2f} (p={chi_n[1]:.1e}). "
         f"보고서 값이 어느 시점·어느 분할표에서 나왔는지는 복구되지 않음 (KEY_FINDINGS.md 참고)")

# ---------------------------------------------------------------------------
# [E] 동결 스냅샷 산출물
# ---------------------------------------------------------------------------
print("\n[E] 동결 스냅샷(v7-40, 7,350건) 산출물 fandom_scores_v6.csv / fan_persona_v7.json")
with open(D / "fandom_scores_v6.csv", encoding="utf-8-sig") as f:
    frozen = list(csv.DictReader(f))
act_sum = sum(int(r["activity"]) for r in frozen)
check("fandom_scores_v6.csv activity 합 = 7,350 (동결 스냅샷 코퍼스 규모)", act_sum == 7350, f"{act_sum}")
F_COLS = {"F1": "결속형(팬클럽·기부·커뮤니티)", "F2": "소비력형(초동·판매·앨범)", "F3": "현장경제형(콘서트·투어·매진)",
          "F4": "미디어노출형(방송·조회수)", "F5": "차트·확산형(1위·빌보드·기록)"}
check("CSV 메타요인 컬럼 5개 = F1 결속형 / F2 소비력형 / F3 현장경제형 / F4 미디어노출형 / F5 차트·확산형",
      all(c in frozen[0] for c in F_COLS.values()), ", ".join(frozen[0].keys()))
with open(D / "fan_persona_v7.json", encoding="utf-8") as f:
    persona = json.load(f)
pc = Counter(x["persona"] for x in persona["fandoms"])
check("페르소나 카운트 = 글로벌투어형43·현장상업형31·원정소비형17·집단동원형9",
      pc == Counter({"글로벌투어형": 43, "현장상업형": 31, "원정소비형": 17, "집단동원형": 9}) and persona["persona_counts"] == dict(pc), f"{dict(pc)}")
pmap = {x["fandom"]: x for x in persona["fandoms"]}
bad_rule = bad_score = bad_spec = 0
for r in frozen:
    x = pmap[r["fandom"]]
    top2 = sorted(F_COLS, key=lambda fc: -float(r[F_COLS[fc]]))[:2]
    if persona["persona_table_definition"]["|".join(sorted(top2))] != x["persona"]:
        bad_rule += 1
    if abs(float(r["loyalty_score"]) - x["loyalty_score"]) > 1e-9 or abs(float(r["spillover_score"]) - x["spillover_score"]) > 1e-9:
        bad_score += 1
    for fc, col in F_COLS.items():
        if abs(round(float(r[col]) * float(r["loyalty_score"]), 4) - x["factor_specific_loyalty"][fc]) > 0.0002 or \
           abs(round(float(r[col]) * float(r["spillover_score"]), 4) - x["factor_specific_spillover"][fc]) > 0.0002:
            bad_spec += 1
check("페르소나 = 상위 2개 F코드 조합표 매핑 (불일치 0)", bad_rule == 0, f"{bad_rule}")
check("persona JSON loyalty/spillover_score = CSV 값 (불일치 0)", bad_score == 0, f"{bad_score}")
check("factor_specific_loyalty/spillover = factor_share × score (불일치 0)", bad_spec == 0, f"{bad_spec}")
fl = [float(r["loyalty_score"]) for r in frozen]; fs = [float(r["spillover_score"]) for r in frozen]
info("동결 스냅샷 점수 표본 평균(참고, 보고서 4구획 기준선은 라이브 점수 평균임)", f"loyalty {np.mean(fl):.4f}, spillover {np.mean(fs):.4f}")
check("동결 CSV 하이라이트: BTS 0.931/1.000, 임영웅 0.899/0.702, 리센느 0.444/0.304 (KEY_FINDINGS 표)",
      (pmap["BTS"]["loyalty_score"], pmap["BTS"]["spillover_score"]) == (0.931, 1.0) and
      (pmap["임영웅"]["loyalty_score"], pmap["임영웅"]["spillover_score"]) == (0.899, 0.702) and
      (pmap["리센느(RESCENE)"]["loyalty_score"], pmap["리센느(RESCENE)"]["spillover_score"]) == (0.444, 0.304))

# ---------------------------------------------------------------------------
# [F] 라이브 참고 재적합 진단
# ---------------------------------------------------------------------------
print("\n[F] lda_v6_diagnostics_live_reference_v7.json (라이브 10,020건 재적합 — 실루엣 게이트 기각분)")
with open(D / "lda_v6_diagnostics_live_reference_v7.json", encoding="utf-8") as f:
    diag = json.load(f)
check("selected_k=8, M=5, silhouette=0.046 (< 동결 기준선 0.267 → 해석 계층 미반영)",
      diag["selected_k"] == 8 and diag["selected_m_meta_factors"] == 5 and diag["meta_factor_silhouette"] == 0.046,
      f"K={diag['selected_k']}, M={diag['selected_m_meta_factors']}, sil={diag['meta_factor_silhouette']}")
check("3D 맵 payload의 selected_k/m/silhouette 와 동일", payload["selected_k"] == diag["selected_k"] and
      payload["selected_m"] == diag["selected_m_meta_factors"] and payload["meta_factor_silhouette"] == diag["meta_factor_silhouette"])
best = min(diag["k_grid"], key=lambda g: g["composite_rank_sum"])
check("k_grid composite_rank_sum 최솟값 = selected_k", best["k"] == diag["selected_k"], f"k={best['k']} (rank_sum {best['composite_rank_sum']})")

# ---------------------------------------------------------------------------
# [G] Persona_결정공간.html 내장 데이터 (동결 스냅샷 K=10 구조)
# ---------------------------------------------------------------------------
print("\n[G] persona_decision_space_v7.json (Persona_결정공간.html 내장, 동결 스냅샷 K=10 → M=5)")
with open(D / "persona_decision_space_v7.json", encoding="utf-8") as f:
    pds = json.load(f)
check("K=10, M=5, silhouette=0.267", pds["dendro"]["K"] == 10 and pds["dendro"]["M"] == 5 and pds["dendro"]["silhouette"] == 0.267)
METHOD_TABLE = {"K0": "F5", "K1": "F3", "K2": "F4", "K3": "F5", "K4": "F2", "K5": "F1", "K6": "F3", "K7": "F3", "K8": "F2", "K9": "F4"}
html_map = dict(zip(pds["dendro"]["topic_ids"], pds["dendro"]["topic_f_codes"]))
check("토픽→F코드 배정 = METHODOLOGY.md 2-1 표 (K0 F5, K1 F3, K2 F4, K3 F5, K4 F2, K5 F1, K6 F3, K7 F3, K8 F2, K9 F4)",
      html_map == METHOD_TABLE, f"{html_map}")
check("PCA 팬덤 100개 · 페르소나 카운트 43/31/17/9", len(pds["pca"]["fandoms"]) == 100 and pds["pca"]["persona_counts"] == dict(pc))
share_mism = 0
fmap = {x["name"]: x for x in pds["pca"]["fandoms"]}
for r in frozen:
    x = fmap[r["fandom"]]
    for fc, col in F_COLS.items():
        if abs(x["shares"][fc] - float(r[col])) > 1e-9:
            share_mism += 1
check("HTML 내장 F1~F5 비중 = fandom_scores_v6.csv 비중 (불일치 0)", share_mism == 0, f"{share_mism}")
info("K=10 토픽 명칭은 METHODOLOGY.md 표와 상위 4개 키워드가 일부 다름(같은 동결 스냅샷의 재적합 산출물, F코드 배정은 동일)",
     " / ".join(f"{i} {n}" for i, n in zip(pds["dendro"]["topic_ids"], pds["dendro"]["topic_names"])))

# ---------------------------------------------------------------------------
n_ok = sum(1 for _, ok in results if ok); n_all = len(results)
print(f"\n=== 결과: {n_ok}/{n_all} 항목 일치 ({n_all - n_ok}건 불일치) ===")
sys.exit(0 if n_ok == n_all else 1)
