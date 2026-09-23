# -*- coding: utf-8 -*-
"""
최종 제출본 수치(docs: v7_final_10020/docs/KEY_FINDINGS.md / v7_final_10020/docs/METHODOLOGY.md, 분석보고서 PDF) ↔ 저장소 데이터 파일 정합성 검증.

이 프로젝트의 다른 검증 스크립트와 같은 원칙("결과를 눈으로 믿지 않고 프로그램이 재대조")으로,
data/v7_final/ 에 있는 최종 파일들에서 보고서 수치를 실제로 재계산해 비교하고, 재현되는 것과
재현되지 않는 것을 항목별로 그대로 출력한다. 어떤 수치도 맞추기 위해 조정하지 않는다.

검증 대상 (전부 저장소 안의 파일만 사용):
  [A] 라이브 코퍼스 fandoms_v3_100.json(10,020건) 자체 규모 — 팬덤 100개, 불릿 10,020건
  [B] 언어·도메인 요약 language_domain_summary_v7.json — 14개 언어, 불릿 합 10,020, 도메인 수
  [C] 충성도·파급효과 점수 — v7_final_10020/docs/METHODOLOGY.md 2-4절 EvidenceScore 산식을 10,020건 코퍼스에 그대로 적용해
      3D 포지셔닝맵 HTML 내장 payload(chart3d_payload_live_reference_v7.json)의 100개 팬덤 점수·표본
      평균(0.3710/0.2661)·4구획(24/17/10/49)이 재현되는지
  [D] 강건성 통계(v7_final_10020/docs/KEY_FINDINGS.md "상관/회귀", "3D 매트릭스 축 독립성", "영향점/강건성") — 라이브 점수 기준
  [E] 동결 스냅샷(v7-40, 7,350건) 산출물 fandom_scores_v6.csv / fan_persona_v7.json — activity 합 7,350,
      페르소나 4유형 카운트(43/31/17/9)와 상위 2개 F코드 규칙, factor_specific_* = share × score
  [F] 라이브 참고 재적합 진단 lda_v6_diagnostics_live_reference_v7.json — K=8, M=5, 실루엣 0.046 (게이트 기각)
  [G] Persona_결정공간.html 내장 데이터 — K=10/M=5/0.267, 토픽→F코드 배정이 v7_final_10020/docs/METHODOLOGY.md 표와 일치하는지

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
# [C] 충성도·파급효과 점수 재현 (v7_final_10020/docs/METHODOLOGY.md 2-4절 산식 그대로)
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
print("\n[D] 강건성 통계 (v7_final_10020/docs/KEY_FINDINGS.md) — 라이브 점수 기준")
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
    # 4분면 독립성 χ²: 보고서 값은 표본 평균 기준 4구획(24/17/10/49)이 아니라 **점수 0.5 고정 임계값** 분할표에서
    # 계산된 것 (positioning_map_correlation_live_v7.json의 table=[[7,17],[4,72]] 로 확인)
    with open(D / "positioning_map_correlation_live_v7.json", encoding="utf-8") as f:
        pmc = json.load(f)
    hl, hs = L > 0.5, S > 0.5
    tab05 = np.array([[int((hl & hs).sum()), int((hl & ~hs).sum())], [int((~hl & hs).sum()), int((~hl & ~hs).sum())]])
    chi05 = stats.chi2_contingency(tab05, correction=True)
    check("4분면 독립성 χ²=8.34, p=0.0039 — loyalty/spillover 각각 0.5 초과 여부 2×2표 [[7,17],[4,72]] (Yates 보정)",
          tab05.tolist() == pmc["quadrant_chi_square"]["table"] and round(chi05[0], 4) == 8.3439 and round(chi05[1], 4) == 0.0039,
          f"표 {tab05.tolist()}, χ²={chi05[0]:.4f}, p={chi05[1]:.6f} (파일 값 χ²={pmc['quadrant_chi_square']['chi2']})")
    tabq = np.array([[q["핵심전략형"], q["내부결속형"]], [q["외부견인형"], q["주변부"]]])
    chiq = stats.chi2_contingency(tabq, correction=True)
    info("참고: 표본 평균 기준 4구획표(24/17/10/49)로 계산하면 다른 값", f"Yates χ²={chiq[0]:.2f} (p={chiq[1]:.1e}) — 보고서 χ²는 이 표가 아님")
    check("positioning_map_correlation_live_v7.json 의 회귀선·activity 상관 재현 (slope 0.3844, r_L·act 0.694, r_S·act 0.9019)",
          round(float(np.polyfit(L, S, 1)[0]), 4) == pmc["regression_spillover_on_loyalty"]["slope"]
          and round(stats.pearsonr(L, A)[0], 3) == round(pmc["each_score_vs_activity"]["loyalty_score_vs_activity"]["r"], 3)
          and round(stats.pearsonr(S, A)[0], 4) == pmc["each_score_vs_activity"]["spillover_score_vs_activity"]["r"],
          f"slope={np.polyfit(L, S, 1)[0]:.4f}, r_L·act={stats.pearsonr(L, A)[0]:.4f}, r_S·act={stats.pearsonr(S, A)[0]:.4f}")

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
fl = np.array([float(r["loyalty_score"]) for r in frozen]); fs = np.array([float(r["spillover_score"]) for r in frozen])
info("동결 스냅샷 점수 표본 평균(참고, 보고서 4구획 기준선은 라이브 점수 평균임)", f"loyalty {np.mean(fl):.4f}, spillover {np.mean(fs):.4f}")
if stats is not None:
    hl, hs = fl > 0.5, fs > 0.5
    tabf = np.array([[int((hl & hs).sum()), int((hl & ~hs).sum())], [int((~hl & hs).sum()), int((~hl & ~hs).sum())]])
    chif = stats.chi2_contingency(tabf, correction=True)
    check("프로즌 스냅샷 4분면 χ²=10.2273, p=0.0014 — 동결 CSV 점수 0.5 초과 2×2표 [[8,17],[4,71]]",
          round(chif[0], 4) == 10.2273 and round(chif[1], 4) == 0.0014, f"표 {tabf.tolist()}, χ²={chif[0]:.4f}, p={chif[1]:.6f}")
with open(D / "member_mention_pilot_v6.json", encoding="utf-8") as f:
    mpil = json.load(f)
fz_act = {r["fandom"]: int(r["activity"]) for r in frozen}
check("member_mention_pilot_v6.json(동결 스냅샷판) 23개 그룹 total_group_bullets = 동결 CSV activity",
      len(mpil) == 23 and all(fz_act.get(g) == v["total_group_bullets"] for g, v in mpil.items()),
      f"{len(mpil)}개 그룹, BTS {mpil['BTS']['total_group_bullets']}건")
mp_bad = [g for g, v in mpil.items() if sum(v["member_mention_counts"].values()) != v["total_member_mentions"]
          or abs(sum(x ** 2 for x in v["member_impact_share_pilot"].values()) - v["mci_pilot"]) > 0.002]
check("멤버 파일럿 내부 정합 (언급 합 = total, MCI = Σshare²)", not mp_bad, f"불일치 {mp_bad}")
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
check("토픽→F코드 배정 = v7_final_10020/docs/METHODOLOGY.md 2-1 표 (K0 F5, K1 F3, K2 F4, K3 F5, K4 F2, K5 F1, K6 F3, K7 F3, K8 F2, K9 F4)",
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
info("K=10 토픽 명칭은 v7_final_10020/docs/METHODOLOGY.md 표와 상위 4개 키워드가 일부 다름(같은 동결 스냅샷의 재적합 산출물, F코드 배정은 동일)",
     " / ".join(f"{i} {n}" for i, n in zip(pds["dendro"]["topic_ids"], pds["dendro"]["topic_names"])))

# ---------------------------------------------------------------------------
# [H] topic_cards_v7.json (동결 스냅샷 K=10 토픽 카드 — v7_final_10020/docs/METHODOLOGY.md 2-1 표의 출처)
# ---------------------------------------------------------------------------
print("\n[H] topic_cards_v7.json (동결 스냅샷 K=10 토픽 카드)")
with open(D / "topic_cards_v7.json", encoding="utf-8") as f:
    cards = json.load(f)
METHOD_NAMES = {"K0": "음원차트기록형(기록·1위·차트·최초)", "K1": "동남아현지보도형(보도·매체·인도네시아·기사)",
                "K2": "예능방송출연형(예능·출연·mbc·sbs)", "K3": "일본오리콘앨범형(일본·빌보드·오리콘·판매)",
                "K4": "글로벌음반판매형(million·album·copies·chart)", "K5": "팬클럽공식기부형(공식·팬클럽·기부·콘텐츠)",
                "K6": "단독콘서트월드투어형(콘서트·투어·단독·월드투어)", "K7": "브랜드앰버서더형(브랜드·광고·앰버서더·매진)",
                "K8": "월드투어매진형(tour·concert·sold·world)", "K9": "영화드라마출연형(드라마·ost·영화·출연)"}
check("토픽 10개, 명칭 = v7_final_10020/docs/METHODOLOGY.md 2-1 표와 완전 일치", len(cards) == 10 and all(c["topic_name"] == METHOD_NAMES[c["topic_id"]] for c in cards))
check("토픽→F 경로 = v7_final_10020/docs/METHODOLOGY.md 표", all(c["connected_f_pathway"].split()[0] == METHOD_TABLE[c["topic_id"]] for c in cards))
k5 = next(c for c in cards if c["topic_id"] == "K5")
fz_row = {r["fandom"]: r for r in frozen}
check("K5(=F1 단독 토픽) 대표 팬덤 avg_topic_weight = 동결 CSV 결속형 비중 (박서진 0.2653 · 임영웅 0.2017 …)",
      all(abs(x["avg_topic_weight"] - float(fz_row[x["fandom"]][F_COLS["F1"]])) < 1e-9 for x in k5["representative_fandoms_top5"]))
info("품질 메모: K2 대표 불릿 3번째는 태국어 aespa 콘서트 문장(topic_prob 0.9625)이 예능출연 토픽에 배정됨 — 비한국어 문장의 토픽 배정 한계 사례",
     "K1 '동남아현지보도형' 대표 불릿도 대학축제·VR 콘서트 등 국내 현장 문장이 섞여 있음")

# ---------------------------------------------------------------------------
# [I] member_pilot_mci_correlation_v7.json (MCI ↔ outcome 상관, 45개 그룹)
# ---------------------------------------------------------------------------
print("\n[I] member_pilot_mci_correlation_v7.json (MCI ↔ 동결 스냅샷 outcome 상관)")
with open(D / "member_pilot_mci_correlation_v7.json", encoding="utf-8") as f:
    mcc = json.load(f)
with open(D / "member_mention_index_v7.json", encoding="utf-8") as f:
    midx = json.load(f)
check("45개 그룹 = member_mention_index_v7.json 그룹 집합", mcc["n_groups"] == 45 and set(mcc["groups"]) == set(midx))
info("시점 주의(파일 caveat 원문)", mcc["caveat_temporal_mismatch"][:90] + "…")
if stats is not None:
    mv = np.array([midx[g]["mci_index"] for g in mcc["groups"]])
    ly = np.array([float(fz_row[g]["loyalty_score"]) for g in mcc["groups"]])
    r_idx = stats.pearsonr(mv, ly)[0]
    info("파일의 MCI는 v7-55 시점(8,981건)이라 저장소에 없음. 저장소의 10,020건 MCI(member_mention_index_v7.json)로 재계산하면 근사",
         f"raw MCI~loyalty r={r_idx:.4f} (파일 -0.3932), MCI 평균 {mv.mean():.4f} (파일 0.2662), max {mv.max()} (파일 0.649, FTISLAND)")
    check("MCI~loyalty 음의 상관 방향·크기 근사 재현 (|Δr| < 0.02)", abs(r_idx - mcc["correlations_mci_raw"]["loyalty_score"]["pearson_r"]) < 0.02, f"Δr={abs(r_idx + 0.3932):.4f}")

# ---------------------------------------------------------------------------
# [J] 보조지표 원본 JSON (라이브 10,020건) — 광고·상업성 / 팬덤결속
# ---------------------------------------------------------------------------
print("\n[J] ad_commercial_index_v7.json / fandom_cohesion_index_v7.json (라이브 10,020건 보조지표)")
corpus_cnt = {fd["fandom"]: len(fd.get("loyalty", [])) + len(fd.get("spillover", [])) for fd in fandoms}
with open(D / "ad_commercial_index_v7.json", encoding="utf-8") as f:
    ad = json.load(f)
check("광고·상업성: total_bullets 10,020, 광고성 불릿 1,302건(13.0%), 20개 업종", ad["total_bullets"] == 10020 and ad["total_ad_bullets"] == 1302
      and round(ad["corpus_ad_share"], 3) == 0.130 and len(ad["industries"]) == 20, f"{ad['total_ad_bullets']} ({ad['corpus_ad_share']:.1%})")
check("광고·상업성: 팬덤별 n_total_bullets = 코퍼스 불릿 수, Σn_ad_bullets = 1,302, Σ업종별 = industry_totals",
      all(corpus_cnt[x["fandom"]] == x["n_total_bullets"] for x in ad["fandoms"]) and sum(x["n_ad_bullets"] for x in ad["fandoms"]) == 1302
      and all(sum(x["industry_counts"].get(i, 0) for x in ad["fandoms"]) == ad["industry_totals"].get(i, 0) for i in ad["industries"]))
with open(D / "fandom_cohesion_index_v7.json", encoding="utf-8") as f:
    co = json.load(f)
check("팬덤결속: total_bullets 10,020, 결속 불릿 923건(9.2%), 유형 5개(A~E)", co["total_bullets"] == 10020 and co["total_cohesion_bullets"] == 923
      and round(co["corpus_cohesion_share"], 3) == 0.092 and len(co["categories"]) == 5, f"{co['total_cohesion_bullets']} ({co['corpus_cohesion_share']:.1%})")
check("팬덤결속: 팬덤별 n_total_bullets = 코퍼스 불릿 수, Σn_cohesion_bullets = 923, Σ유형별 = category_totals",
      all(corpus_cnt[x["fandom"]] == x["n_total_bullets"] for x in co["fandoms"]) and sum(x["n_cohesion_bullets"] for x in co["fandoms"]) == 923
      and all(sum(x["category_counts"].get(c, 0) for x in co["fandoms"]) == co["category_totals"][c] for c in co["categories"]))
coh = {x["fandom"]: x for x in co["fandoms"]}
check("팬덤결속 하이라이트 (KEY_FINDINGS 표): BTS 15건(6.6%) · 리센느 18건(21.2%) · 임영웅 30건(23%, 전체 1위)",
      coh["BTS"]["n_cohesion_bullets"] == 15 and coh["리센느(RESCENE)"]["n_cohesion_bullets"] == 18 and coh["임영웅"]["n_cohesion_bullets"] == 30
      and max(co["fandoms"], key=lambda x: x["n_cohesion_bullets"])["fandom"] == "임영웅",
      f"BTS {coh['BTS']['cohesion_share']:.1%}, 리센느 {coh['리센느(RESCENE)']['cohesion_share']:.1%}, 임영웅 {coh['임영웅']['cohesion_share']:.1%}")

# ---------------------------------------------------------------------------
# [K] chart3d_correlation_live_v7.json (3D 축 독립성 원본 파일)
# ---------------------------------------------------------------------------
print("\n[K] chart3d_correlation_live_v7.json (3D 매트릭스 축 독립성 검증 원본)")
with open(D / "chart3d_correlation_live_v7.json", encoding="utf-8") as f:
    c3 = json.load(f)
if stats is not None:
    m3c = sm.OLS(Dv, sm.add_constant(np.column_stack([L, S]))).fit()
    cd3 = m3c.get_influence().cooks_distance[0]
    top3 = [n for _, n in sorted(zip(cd3, names), reverse=True)[:5]]
    check("다양성 회귀 계수 (절편 0.7168, loyalty -0.073, spillover 0.3008) 및 Cook's D top5 (god·이효리·BTS·투어스·지드래곤) 재현",
          [round(v, 4) for v in m3c.params] == [0.7168, -0.073, 0.3008] and top3 == [x["fandom"] for x in c3["influence_top5"]],
          f"coef={m3c.params.round(4).tolist()}, top5={top3}")
    check("factor_diversity 정규성 Shapiro p=0.058 (정규성 유지), Spearman ρ(S,D)=0.4869",
          round(stats.shapiro(Dv).pvalue, 3) == 0.058 and round(stats.spearmanr(S, Dv)[0], 4) == 0.4869)

# ---------------------------------------------------------------------------
# [L] 실루엣 게이트 타임라인 CSV (v4 종료 ~ v7 r66(2차))
# ---------------------------------------------------------------------------
print("\n[L] data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv")
tl_path = BASE / "data" / "silhouette_gate_timeline" / "corpus_silhouette_timeline_v7_66_2ch.csv"
with open(tl_path, encoding="utf-8-sig") as f:
    tl = list(csv.DictReader(f))
real_rows = [r for r in tl if "[추정" not in r["라운드"]]
meas_rows = [r for r in real_rows if r["실루엣"]]
after40 = [r for r in meas_rows if float(r["순서"]) > 40]
check("v7-40 동결 기준선 행: 7,350건, 실루엣 0.267, K=10, M=5", any(r["순서"] == "40" and r["코퍼스(불릿수)"] == "7350" and r["실루엣"] == "0.267" and r["K"] == "10" and r["M"] == "5" for r in real_rows))
check("v7-40 이후 실측 지점 전부 0.267 미만 (게이트 기각)", len(after40) > 0 and all(float(r["실루엣"]) < 0.267 for r in after40),
      f"실측 {len(after40)}개 지점, 최대 {max(float(r['실루엣']) for r in after40)}, 마지막 {after40[-1]['라운드']} {after40[-1]['코퍼스(불릿수)']}건 {after40[-1]['실루엣']}")
check("KEY_FINDINGS '최신 v7-65 라운드 silhouette=0.141'", any(r["라운드"].startswith("r65") and r["실루엣"] == "0.141" for r in meas_rows))
info("'누적 26회 연속 기각'(보고서)은 라운드 횟수 기준으로 보이며, 이 CSV의 실측 지점 수로는 22개(r45 2개 변형 포함) — 재적합 없이 지나간 라운드까지 세면 26에 가깝지만 CSV만으로는 확정 불가")
info("타임라인 마지막 실측 코퍼스", f"{after40[-1]['코퍼스(불릿수)']}건 (r66 2차) — 최종 라이브 코퍼스 10,020건은 이 이후 라운드의 결과이며, 그 시점 재적합(K=8/M=5/0.046)은 lda_v6_diagnostics_live_reference_v7.json")
check("r22 행 5,613건 = merge_log_r22의 after_total (로그 산술 5606+7; 당시 평탄화 건수와 1건 차이)", any(r["라운드"] == "r22" and r["코퍼스(불릿수)"] == "5613" for r in real_rows))

# ---------------------------------------------------------------------------
# [M] 2026-09-22 3차 추가 파일: 라이브 점수 원본 CSV · 제외 불릿 · 동결 진단 · 매체 크로스오버 · K=9 검증
# ---------------------------------------------------------------------------
print("\n[M] fandom_scores_live_reference_v7.csv (라이브 10,020건 점수 + 라이브 재적합 F 비중 원본)")
with open(D / "fandom_scores_live_reference_v7.csv", encoding="utf-8-sig") as f:
    live_csv = list(csv.DictReader(f))
LIVE_COLS = ["현장경제형(콘서트·투어·매진)", "소비력형(초동·판매·앨범)", "결속형(팬클럽·기부·커뮤니티)", "브랜드·상업형(광고·앰버서더)", "차트·확산형(1위·빌보드·기록)"]
prow = {r["fandom"]: r for r in rows}
lc_bad = [r["fandom"] for r in live_csv if abs(float(r["loyalty_score"]) - prow[r["fandom"]]["loyalty"]) > 1e-9
          or abs(float(r["spillover_score"]) - prow[r["fandom"]]["spillover"]) > 1e-9 or abs(float(r["factor_diversity"]) - prow[r["fandom"]]["diversity"]) > 1e-9
          or abs(float(r["coverage_index"]) - prow[r["fandom"]]["coverage"]) > 1e-9 or int(r["activity"]) != prow[r["fandom"]]["activity"] or r["dominant_factor"] != prow[r["fandom"]]["dominant"]]
check("100개 팬덤 loyalty/spillover/diversity/coverage/activity/dominant = 3D 맵 payload (불일치 0)", not lc_bad, f"{lc_bad}")
check("F 비중 5개 컬럼 = 라이브 재적합 factor_labels, factor_diversity = 정규화 엔트로피(ln 5), dominant = argmax",
      sorted(LIVE_COLS) == sorted(diag["factor_labels"].values()) and all(
          abs(-sum(float(r[c]) * math.log(float(r[c])) for c in LIVE_COLS if float(r[c]) > 0) / math.log(5) - float(r["factor_diversity"])) < 0.0011
          and max(LIVE_COLS, key=lambda c: float(r[c])) == r["dominant_factor"] for r in live_csv))
live_set = {r["fandom"] for r in live_csv}; frozen_set = {r["fandom"] for r in frozen}
check("라이브 100개 팬덤 = 코퍼스 팬덤 집합", live_set == {fd["fandom"] for fd in fandoms})
info("로스터 차이: 동결 스냅샷(7,350건)에만 있는 팬덤 / 라이브(10,020건)에만 있는 팬덤",
     f"동결만 {sorted(frozen_set - live_set)} / 라이브만 {sorted(live_set - frozen_set)} — 타임라인 r62(한로로→몬스타엑스)·r63(pH-1→투어스) 교체 + BE'O→빈지노. "
     f"따라서 페르소나·F1~F5 비중(동결)은 라이브 3개 팬덤을 포함하지 않는다")

print("\n[N] lda_excluded_bullets_v7.json (10,020 → 10,018 재적합 문서 수의 근거)")
with open(D / "lda_excluded_bullets_v7.json", encoding="utf-8") as f:
    exb = json.load(f)
byf = {fd["fandom"]: fd for fd in fandoms}
check("10,020건 중 2건 제외(3토큰 미만) → LDA 문서 10,018건 (보고서 표 2-1 값)", exb["total_bullets"] == 10020 and exb["excluded_count"] == 2 and exb["lda_document_count"] == 10018)
check("제외된 2건이 코퍼스의 해당 위치에 실재 (ATEEZ spillover[30] 태국어 2토큰, 레드벨벳 spillover[56] '맥도날드 조이 (2026)')",
      all(byf[e["fandom"]][e["tag"]][e["idx"]]["t"] == e["t"] and byf[e["fandom"]][e["tag"]][e["idx"]]["u"] == e["u"] for e in exb["excluded"]))

print("\n[O] lda_v6_diagnostics_frozen_v7_40.json (동결 스냅샷 진단 — 업로드 원본 파일명 lda_v6_diagnostics.json)")
with open(D / "lda_v6_diagnostics_frozen_v7_40.json", encoding="utf-8") as f:
    fdg = json.load(f)
check("selected_k=10, M=5, silhouette=0.267, composite_rank_sum 최솟값 = K=10 (rank_sum 8 < K=8의 9)",
      fdg["selected_k"] == 10 and fdg["selected_m_meta_factors"] == 5 and fdg["meta_factor_silhouette"] == 0.267 and min(fdg["k_grid"], key=lambda g: g["composite_rank_sum"])["k"] == 10)
check("topics_top_words 10개 = topic_cards_v7.json top_keywords (10/10 동일)", all(fdg["topics_top_words"][str(i)] == cards[i]["top_keywords"] for i in range(10)))
LAB2F = {"결속형(팬클럽·기부·커뮤니티)": "F1", "소비력형(초동·판매·앨범)": "F2", "현장경제형(콘서트·투어·매진)": "F3", "미디어노출형(방송·조회수)": "F4", "차트·확산형(1위·빌보드·기록)": "F5"}
fmap = {f"K{k}": LAB2F[fdg["factor_labels"][str(v)]] for k, v in fdg["topic_to_factor"].items()}
check("topic_to_factor + factor_labels → v7_final_10020/docs/METHODOLOGY.md 2-1 표의 F코드 배정과 일치", fmap == METHOD_TABLE, f"{fmap}")

print("\n[P] media_crossover_index_v7.json (매체 크로스오버 지수, 라이브 10,020건)")
with open(D / "media_crossover_index_v7.json", encoding="utf-8") as f:
    mcx = json.load(f)
check("news_media 불릿 6,712건(67.0%) — 보고서 표 2-1 '매체 크로스오버 6,712건(67.0%)'", mcx["total_news_media_bullets"] == 6712 and round(mcx["corpus_news_media_share"], 3) == 0.670 and mcx["total_bullets"] == 10020)
check("팬덤별 n_total_bullets = 코퍼스, Σn_news_media_bullets = 6,712, outlet_diversity_ratio = n_distinct/n_news",
      all(corpus_cnt[x["fandom"]] == x["n_total_bullets"] for x in mcx["fandoms"]) and sum(x["n_news_media_bullets"] for x in mcx["fandoms"]) == 6712
      and all(abs(x["n_distinct_outlets"] / x["n_news_media_bullets"] - x["outlet_diversity_ratio"]) < 1e-3 for x in mcx["fandoms"] if x["n_news_media_bullets"]))
COMM = {"reddit.com", "x.com", "twitter.com", "facebook.com", "instagram.com", "threads.com"}; WIKI = {"en.wikipedia.org", "ko.wikipedia.org", "namu.wiki", "wikipedia.org"}
def _dom(u):
    m = re.match(r"https?://([^/\s]+)", u.strip()); d = (m.group(1) if m else "").lower(); return d[4:] if d.startswith("www.") else d
def _in(d, S): return any(d == x or d.endswith("." + x) for x in S)
n_news = Counter()
for fd in fandoms:
    for k in ("loyalty", "spillover"):
        for b in fd[k]:
            d = _dom(b.get("u", ""))
            if not (_in(d, COMM) or _in(d, WIKI)):
                n_news[d] += 1
info("run_lda_v6.py의 source_type_of() 도메인 목록(v6판)으로 재계산", f"news_media {sum(n_news.values()):,}건 / 고유 매체 {len(n_news):,}개 (원본 6,712 / 1,298 — 라이브판 목록이 약간 더 넓음), 상위 3개 {n_news.most_common(3)} = 원본 top_outlets와 동일")

print("\n[Q] k9_validation_v7.json (K=9 미검증 지적에 대한 추가 검증 실험)")
with open(D / "k9_validation_v7.json", encoding="utf-8") as f:
    k9 = json.load(f)
check("K=9를 추가한 K-grid에서도 합성순위 승자는 K=8 (rank_sum 9 vs K=9 13)", k9["k_grid_winner"]["k"] == 8 and min(k9["k_grid"], key=lambda g: g["composite_rank_sum"])["k"] == 8)
info("실험 코퍼스는 9,614 문서(중간 라운드, 10,018과 다름). K=9 phi에서 미디어 토픽은 M≥6에서만 단독 메타팩터로 분리(M=5 실루엣 0.099, M=6 0.081)",
     f"corpus_docs={k9['corpus_docs']}, vocab={k9['vocab_size']}")

# ---------------------------------------------------------------------------
# [R] 2026-09-22 4차 추가: 미디어·콘텐츠 노출 지수 · v7_progress(r48)
# ---------------------------------------------------------------------------
print("\n[R] media_exposure_v7.json (미디어·콘텐츠 노출 지수, 라이브 10,020건)")
with open(D / "media_exposure_v7.json", encoding="utf-8") as f:
    mex = json.load(f)
check("미디어 불릿 1,025건(10.2%) — 보고서 표 2-1 '미디어·콘텐츠 노출 1,025건(10.2%)', 서브태그 4종(예능/유튜브/영화/드라마)",
      mex["total_media_bullets"] == 1025 and round(mex["corpus_media_share"], 3) == 0.102 and mex["total_bullets"] == 10020 and len(mex["subtags"]) == 4)
check("팬덤별 n_total_bullets = 코퍼스, Σn_media_bullets = 1,025, Σ서브태그별 = subtag_totals (예능 309·유튜브 286·영화 179·드라마 313)",
      all(corpus_cnt[x["fandom"]] == x["n_total_bullets"] for x in mex["fandoms"]) and sum(x["n_media_bullets"] for x in mex["fandoms"]) == 1025
      and all(sum(x["subtag_counts"].get(t, 0) for x in mex["fandoms"]) == mex["subtag_totals"][t] for t in mex["subtags"]))
mex_hi = {x["fandom"]: x for x in mex["fandoms"]}
info("하이라이트 미디어 불릿", f"임영웅 {mex_hi['임영웅']['n_media_bullets']}건({mex_hi['임영웅']['media_share']:.1%}, 전체 1위) · 리센느 {mex_hi['리센느(RESCENE)']['n_media_bullets']}건 · BTS {mex_hi['BTS']['n_media_bullets']}건")

print("\n[T] v7_progress.json (data/v7_final 판 = v7 48라운드 시점)")
with open(D / "v7_progress.json", encoding="utf-8") as f:
    vp = json.load(f)
check("v7_progress current_total 8,311 = 타임라인 CSV r48 행", vp["current_total"] == 8311 and any(r["라운드"] == "r48" and r["코퍼스(불릿수)"] == "8311" for r in real_rows))
info("current_total_note 원문이 이원 구조를 명시", vp.get("current_total_note", "")[:120] + "…")

# ---------------------------------------------------------------------------
# [U] 2026-09-22 5차 추가: 세계 언어 지수 · 라이브 점수 JSON · 워드클라우드 · r45 탐색 · F 경로 맵
# ---------------------------------------------------------------------------
print("\n[U] worldwide_language_pilot_live_reference_v7.json (세계 언어 지수 원본, 라이브 10,020건)")
with open(D / "worldwide_language_pilot_live_reference_v7.json", encoding="utf-8") as f:
    wl = json.load(f)
wl_lang = Counter()
for _f, dd in wl.items():
    wl_lang.update(dd["language_mention_counts"])
check("100개 팬덤, total_group_bullets = 코퍼스, 14개 언어 언급 합 = language_domain_summary_v7.json (ko 5,551 … 합 10,020)",
      len(wl) == 100 and all(corpus_cnt[g] == dd["total_group_bullets"] for g, dd in wl.items()) and dict(wl_lang) == {x["lang_code"]: x["total_bullets"] for x in langs})
check("KEY_FINDINGS 하이라이트: BTS 해외 근거 135건(비중 60% — 원값 0.595의 반올림), 해외언어다양성 0.66",
      wl["BTS"]["foreign_bullets"] == 135 and abs(wl["BTS"]["foreign_ratio"] - 0.595) < 1e-9 and wl["BTS"]["foreign_diversity"] == 0.66, f"{wl['BTS']['foreign_bullets']}건, {wl['BTS']['foreign_ratio']:.1%}, {wl['BTS']['foreign_diversity']}")
check("foreign_bullets = 언어별 언급 중 ko 제외 합 (100/100)", all(dd["foreign_bullets"] == sum(v for k, v in dd["language_mention_counts"].items() if k != "ko") for dd in wl.values()))

print("\n[V] fandom_scores_live_reference_v7.json (라이브 점수 원본 JSON — raw 점수·coverage_detail 포함)")
with open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8") as f:
    sj = json.load(f)
check("loyalty_raw/spillover_raw = EvidenceScore 산식 재계산 (100/100, 오차 1e-6)",
      all(abs(evidence_score(byf[r["fandom"]]["loyalty"], LOYALTY_BONUS_KW) - r["loyalty_raw"]) < 1e-6 and abs(evidence_score(byf[r["fandom"]]["spillover"], SPILLOVER_BONUS_KW) - r["spillover_raw"]) < 1e-6 for r in sj))
Wc = {"language": 0.30, "market": 0.25, "source_type": 0.20, "time": 0.15, "entity": 0.10}
def _lang_ent(lc):
    tot = sum(lc.values()); return -sum(c / tot * math.log(c / tot) for c in lc.values() if c > 0) / math.log(14)
check("coverage_index = 0.30·언어 + 0.25·시장 + 0.20·출처유형 + 0.15·시간 + 0.10·개체, 언어 커버리지 = 14개 언어 정규화 엔트로피 ln(14)",
      all(abs(round(sum(Wc[k] * r["coverage_detail"][k + "_coverage"] for k in Wc), 3) - r["coverage_index"]) < 0.0015 and abs(_lang_ent(r["coverage_detail"]["language_counts"]) - r["coverage_detail"]["language_coverage"]) < 0.0015 for r in sj))
sj_lang = Counter()
for r in sj:
    sj_lang.update(r["coverage_detail"]["language_counts"])
check("coverage_detail.language_counts 합 = language_domain_summary (14개 언어, 10,020건) — 세계 언어 지수와 같은 분류", dict(sj_lang) == {x["lang_code"]: x["total_bullets"] for x in langs})
check("JSON 점수·coverage·activity = 같은 이름 CSV (100/100)", all(abs(r["loyalty_score"] - float(next(c for c in live_csv if c["fandom"] == r["fandom"])["loyalty_score"])) < 1e-9 and r["activity"] == int(next(c for c in live_csv if c["fandom"] == r["fandom"])["activity"]) for r in sj))

print("\n[W] wordcloud_by_language_v7.json (최종 토크나이저 실행 결과, TOKENIZER_WORDCLOUD_REPORT 표 2의 원본)")
with open(D / "wordcloud_by_language_v7.json", encoding="utf-8") as f:
    wcd = json.load(f)
wc_b = {b["bucket"].split("(")[0]: b for b in wcd["buckets"]}
check("총 토큰 170,725개(보고서 값), 버킷 8개 토큰 합 = 총계, 한국어 8,942불릿(89.2%)·중국어 398·일본어 155·태국어 56·러시아어 45·베트남어 30",
      wcd["total_tokens"] == 170725 and sum(b["n_total_tokens"] for b in wcd["buckets"]) == 170725 and wc_b["한국어"]["n_bullets_with_any_token"] == 8942
      and wc_b["중국어"]["n_bullets_with_any_token"] == 398 and wc_b["일본어"]["n_bullets_with_any_token"] == 155 and wc_b["태국어"]["n_bullets_with_any_token"] == 56)
info("보고서 표 2와의 차이", f"영어 {wc_b['영어']['n_bullets_with_any_token']}불릿·비영어 {wc_b['비영어']['n_bullets_with_any_token']}불릿 (문서 표 2: 6,438 / 158) — 이 파일은 wordfreq 재검증으로 순수 ASCII 토큰 219개를 비영어로 재분류한 후속판(methodology 필드 참고)")

print("\n[X] _explore_r45_meta_factor.json (v7 r45 1차 K=12 재적합의 M 그리드 탐색)")
with open(D / "_explore_r45_meta_factor.json", encoding="utf-8") as f:
    r45 = json.load(f)
check("K=12, M 2~11 전수 탐색 최댓값 M=2 실루엣 0.136 = 타임라인 'r45(1차)' 행 (K=12, M=2, 0.136)",
      r45["K"] == 12 and r45["best_m_full_grid"] == 2 and round(r45["best_silhouette_full_grid"], 3) == 0.136
      and any(r["라운드"].startswith("r45(1차") and r["실루엣"] == "0.136" and r["K"] == "12" and r["M"] == "2" for r in real_rows))
try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    dm = np.array(r45["topic_cosine_distance_matrix"])
    ok = True
    for g in r45["full_grid_2_to_11"]:
        lab = AgglomerativeClustering(n_clusters=g["m"], metric="precomputed", linkage="average").fit_predict(dm)
        ok &= abs(silhouette_score(dm, lab, metric="precomputed") - g["silhouette"]) < 1e-6
    check("코사인거리 행렬로 average-linkage 재군집화 → M 2~11 실루엣 10개 전부 재현", ok)
except ImportError:
    info("scikit-learn 미설치로 M 그리드 재계산 생략")

print("\n[Y] factor_pathway_map_v7.json (raw Factor 라벨 → F1~F5 경로 매핑)")
with open(D / "factor_pathway_map_v7.json", encoding="utf-8") as f:
    fpm = json.load(f)
check("5개 라벨 → F 코드 = 검증 스크립트의 LAB2F 표(결속 F1·소비력 F2·현장경제 F3·미디어노출 F4·차트확산 F5), 10개 토픽 전부 매핑",
      {k: v["f_code"] for k, v in fpm["mapping"].items()} == LAB2F and fpm["qa"]["n_mapped_topics"] == 10 and fpm["qa"]["unmapped_topic_ratio"] == 0.0)

# ---------------------------------------------------------------------------
# [Z] 2026-09-22 6차 추가: 동결 스냅샷 점수 JSON · 보조 CSV 2종
# ---------------------------------------------------------------------------
print("\n[Z] fandom_scores_v6.json (동결 스냅샷 v7-40 점수 원본 JSON — 같은 이름 CSV의 원본)")
with open(D / "fandom_scores_v6.json", encoding="utf-8") as f:
    fzj = json.load(f)
fz_row = {r["fandom"]: r for r in frozen}
check("100개 팬덤, activity 합 7,350, 점수·F 비중 5개·coverage·dominant = fandom_scores_v6.csv (100/100)",
      len(fzj) == 100 and sum(r["activity"] for r in fzj) == 7350 and all(
          abs(r["loyalty_score"] - float(fz_row[r["fandom"]]["loyalty_score"])) < 1e-9 and abs(r["coverage_index"] - float(fz_row[r["fandom"]]["coverage_index"])) < 1e-9
          and all(abs(r["factor_share"][c] - float(fz_row[r["fandom"]][c])) < 1e-9 for c in F_COLS.values()) and r["dominant_factor"] == fz_row[r["fandom"]]["dominant_factor"] for r in fzj))
Lr = [r["loyalty_raw"] for r in fzj]; Sr = [r["spillover_raw"] for r in fzj]
check("loyalty/spillover_score = raw 점수의 min-max 정규화 (식 2), factor_diversity = 정규화 엔트로피 ln(5), coverage = 5요소 가중합",
      all(abs(round((r["loyalty_raw"] - min(Lr)) / (max(Lr) - min(Lr)), 3) - r["loyalty_score"]) < 0.002 and abs(round((r["spillover_raw"] - min(Sr)) / (max(Sr) - min(Sr)), 3) - r["spillover_score"]) < 0.002
          and abs(-sum(p * math.log(p) for p in r["factor_share"].values() if p > 0) / math.log(5) - r["factor_diversity"]) < 0.0011
          and abs(round(sum(Wc[k] * r["coverage_detail"][k + "_coverage"] for k in Wc), 3) - r["coverage_index"]) < 0.0015 for r in fzj))
def _lang_ent_n(lc, n):
    tot = sum(lc.values()); return -sum(c / tot * math.log(c / tot) for c in lc.values() if c > 0) / math.log(n)
n13 = sum(1 for r in fzj if abs(_lang_ent_n(r["coverage_detail"]["language_counts"], 13) - r["coverage_detail"]["language_coverage"]) < 0.0015)
n14 = sum(1 for r in fzj if abs(_lang_ent_n(r["coverage_detail"]["language_counts"], 14) - r["coverage_detail"]["language_coverage"]) < 0.0015)
check("동결 스냅샷의 언어 커버리지 분모는 ln(13) (아랍어 추가 전 13개 언어; 라이브 10,020건은 ln(14))", n13 == 100, f"ln(13) 일치 {n13}/100, ln(14) 일치 {n14}/100")
fz_lang = Counter()
for r in fzj:
    fz_lang.update(r["coverage_detail"]["language_counts"])
info("동결 스냅샷 7,350건 언어 분포", f"{dict(fz_lang)} (합 {sum(fz_lang.values())}, 아랍어 없음)")

print("\n[AA] supplementary_csv/ (보조 CSV)")
with open(D / "supplementary_csv" / "fandom_bullet_share_v6.csv", encoding="utf-8-sig") as f:
    bsh = list(csv.DictReader(f))
bs_tot = sum(int(r["근거 문장 수"]) for r in bsh)
check("fandom_bullet_share_v6.csv: 100개 팬덤, 합 5,454건 = 타임라인 r17, 비중(%) = 건수/합", len(bsh) == 100 and bs_tot == 5454
      and any(r["라운드"] == "r17" and r["코퍼스(불릿수)"] == "5454" for r in real_rows) and all(abs(int(r["근거 문장 수"]) / bs_tot * 100 - float(r["비중(%)"])) < 0.006 for r in bsh),
      f"합 {bs_tot}, 로스터에 창모·사이먼도미닉·헤이즈 포함(초기 로스터)")
with open(D / "supplementary_csv" / "domestic_regional_pilot_v6_top3.csv", encoding="utf-8-sig") as f:
    top3 = list(csv.DictReader(f))
t3_sum = sum(int(r["근거 문장 수"]) for r in top3)
check("domestic_regional_pilot_v6_top3.csv: 100개 팬덤, 근거문장수 합 5,998 = 타임라인 r24 시점 보조 CSV", len(top3) == 100 and t3_sum == 5998, f"합 {t3_sum}")

# ---------------------------------------------------------------------------
# [AB] data/v7_rounds/ — 사용자가 GitHub에 직접 업로드한 v7 라운드별 병합·교체 로그 전량 (r1~r72) + v6 단계 로그 3개
# ---------------------------------------------------------------------------
print("\n[AB] data/v7_rounds/ (v7 병합·교체 로그 전량)")
RD = BASE / "data" / "v7_rounds"
def _rk(n):
    m = re.search(r"r(\d+)(?:_(p2|2ch))?", n); return (int(m.group(1)), {"": 0, "p2": 1, "2ch": 2}[m.group(2) or ""])
mlogs = sorted(RD.glob("merge_log_r*.json"), key=lambda p: _rk(p.name))
def _ba(d): return d.get("before_total", d.get("before_total_bullets")), d.get("after_total", d.get("after_total_bullets"))
r22_after = _ba(json.load(open(RD / "merge_log_r22.json", encoding="utf-8")))[1]
check("merge_log_r22 after_total 5,613 = 타임라인 CSV r22 행 (실제 평탄화는 5,612건 — 로그 기록상 +1)", r22_after == 5613 and any(r["라운드"] == "r22" and r["코퍼스(불릿수)"] == "5613" for r in real_rows), f"로그 {r22_after}")
last = json.load(open(mlogs[-1], encoding="utf-8"))
check("마지막 병합 로그 r72: 9,939 → 10,020 (최종 라이브 코퍼스 규모)", mlogs[-1].name == "merge_log_r72.json" and _ba(last) == (9939, 10020))
tl_map = {r["라운드"]: r["코퍼스(불릿수)"] for r in real_rows}
ok = bad = 0
for p in mlogs:
    d = json.load(open(p, encoding="utf-8")); b, a = _ba(d)
    if a is None: continue
    n, suf = _rk(p.name); key = f"r{n}" + ("_p2" if suf == 1 else "")
    c = [k for k in tl_map if (k == key or k.startswith(key + "(")) and (("2차" in k) == (suf == 2))]
    if c:
        ok += int(tl_map[c[0]]) == a; bad += int(tl_map[c[0]]) != a
check("병합 로그 after_total = 실루엣 타임라인 CSV의 같은 라운드 코퍼스 (불일치 0)", bad == 0, f"대조 {ok + bad}건 중 일치 {ok}")
swaps = {}
for p in RD.glob("swap_log_r*.json"):
    d = json.load(open(p, encoding="utf-8"))
    for sw in (d.get("swaps") or [d]):
        swaps[sw["removed_fandom"]] = sw["added_fandom"]
r58 = json.load(open(RD / "merge_log_r58.json", encoding="utf-8"))
if r58.get("round_type") == "roster_swap":
    swaps[r58["removed_fandom"]] = r58["added_fandom"]
check("로스터 교체 로그 6건 = 동결→라이브 로스터 차이 (한로로→몬스타엑스 r62, pH-1→투어스 r63, BE'O→빈지노 r58) + r22 이전 교체 (사이먼도미닉→GOT7 r29, 창모→김재중·헤이즈→박서진 r34)",
      swaps == {"사이먼도미닉": "GOT7", "창모": "김재중", "헤이즈": "박서진", "BE'O": "빈지노", "한로로": "몬스타엑스", "pH-1": "투어스(TWS)"}, f"{swaps}")
check("교체된 팬덤 6개는 최종 코퍼스에 없고, 추가된 6개는 있음", not (set(swaps) & set(corpus_cnt)) and set(swaps.values()) <= set(corpus_cnt))
sa = json.load(open(RD / "schema_audit_r74.json", encoding="utf-8"))
check("schema_audit_r74: 10,020건 스캔, 팬덤 100, LDA 3토큰 미만 제외 2건(= lda_excluded_bullets_v7.json)", sa["total_bullets_scanned"] == 10020 and sa["n_fandoms"] == 100 and sa["lda_sub_3_token_excluded_bullets"] == 2)
info("성장 이력 전체 CSV", "v7_final_10020/data_export/build_corpus_growth_history_csv.py -> data/v7_final/corpus_growth_history_v6_v7_full.csv (v6 1차 ~ v7 r72)")

# ---------------------------------------------------------------------------
# [AC] v7_final_10020/analysis/ — 국내 지역 지수 최종 산출본 (10,020건)
print("\n[AC] v7_final_10020/analysis/domestic_regional_index — 최종 10,020건 산출본")
_dr_path = BASE / "v7_final_10020" / "analysis" / "domestic_regional_index" / "domestic_regional_index_v7.json"
if _dr_path.exists():
    dr = json.load(open(_dr_path, encoding="utf-8"))
    _regions = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    _bad = sum(1 for v in dr.values() if sum(v["region_mention_counts"].get(r, 0) for r in _regions) != v["total_region_mentions"]
               or sum(1 for r in _regions if v["region_mention_counts"].get(r, 0) > 0) != v["n_regions_hit"]
               or abs(v["n_regions_hit"] / 17 - v["region_diversity"]) > 0.001)
    check("국내 지역 지수 산출본: 100개 팬덤, 17개 시도 합 = total_region_mentions, n_regions_hit/17 = region_diversity (불일치 0)", len(dr) == 100 and _bad == 0, f"불일치 {_bad}")
    check("근거문장 수 = 최종 코퍼스 실측 (100/100)", all(dr[f]["total_group_bullets"] == corpus_cnt.get(f) for f in dr))
    check("보고서 표 15·KEY_FINDINGS 강조 3팬덤 — 임영웅 28건·12지역·서울 21%·0.706(전체 1위), BTS 17건·5지역·서울 47%·0.294 (동결 시점과 최종이 같은 값)",
          dr["임영웅"]["total_region_mentions"] == 28 and dr["임영웅"]["n_regions_hit"] == 12 and dr["임영웅"]["primary_region"] == "서울" and abs(dr["임영웅"]["region_diversity"] - 0.706) < 0.001
          and dr["BTS"]["total_region_mentions"] == 17 and dr["BTS"]["n_regions_hit"] == 5 and dr["BTS"]["primary_region"] == "서울" and abs(dr["BTS"]["primary_region_share"] - 0.471) < 0.001
          and max(v["region_diversity"] for v in dr.values()) == dr["임영웅"]["region_diversity"])
    check("리센느(RESCENE): 최종 22건·5지역·경남 64% (표 15의 19건·58%는 동결 스냅샷 시점 — 노트북 3절에서 동결 근사로 재현)",
          dr["리센느(RESCENE)"]["total_region_mentions"] == 22 and dr["리센느(RESCENE)"]["primary_region"] == "경남" and abs(dr["리센느(RESCENE)"]["primary_region_share"] - 0.636) < 0.001)
    check("커버리지 99/100 (0건: 투어스(TWS)), 검출 지역 합 469, 지역 언급 총계 1,226",
          sum(1 for v in dr.values() if v["n_regions_hit"] == 0) == 1 and dr["투어스(TWS)"]["n_regions_hit"] == 0 and sum(v["n_regions_hit"] for v in dr.values()) == 469 and sum(v["total_region_mentions"] for v in dr.values()) == 1226)
else:
    info("v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json 없음", "python v7_final_10020/analysis/build_notebooks_v7.py domestic 으로 생성")

# ---------------------------------------------------------------------------
# [AD] 동결 스냅샷 코퍼스 근사 복원본 (data/v7_final/frozen_snapshot_v7_40/)
# ---------------------------------------------------------------------------
print("\n[AD] data/v7_final/frozen_snapshot_v7_40/fandoms_v7_40_frozen_reconstructed.json — 동결 7,350건 코퍼스 근사 복원본")
_fr_path = D / "frozen_snapshot_v7_40" / "fandoms_v7_40_frozen_reconstructed.json"
if _fr_path.exists():
    import zipfile as _zf
    _rec = {f["fandom"]: f for f in json.load(open(_fr_path, encoding="utf-8"))}
    _fz = {r["fandom"]: r for r in fzj}
    _r22 = {f["fandom"]: f for f in json.loads(_zf.ZipFile(BASE / "archive" / "v6_r22_era_backup.zip").read("v6_r22_era/data/v6_r22_snapshot/fandoms_v3_100.json"))}
    _partial = {"BE'O", "pH-1", "한로로"}
    _n = sum(len(f["loyalty"]) + len(f["spillover"]) for f in _rec.values())
    check("로스터 = 동결 로스터 100개 (BE'O·pH-1·한로로 포함), 총 7,326건 = 7,350 − 유실 24", set(_rec) == set(_fz) and _n == 7326, f"{len(_rec)}개, {_n:,}건")
    _fp = [k for k in _fz if k not in _partial and (len(_rec[k]["loyalty"]), len(_rec[k]["spillover"])) == (_fz[k]["n_loyalty_bullets"], _fz[k]["n_spillover_bullets"])
           and abs(evidence_score(_rec[k]["loyalty"], LOYALTY_BONUS_KW) - _fz[k]["loyalty_raw"]) < 1e-6 and abs(evidence_score(_rec[k]["spillover"], SPILLOVER_BONUS_KW) - _fz[k]["spillover_raw"]) < 1e-6]
    check("97개 공통 팬덤: 건수 + EvidenceScore 지문(loyalty_raw/spillover_raw, 1e-6) 97/97 일치 — 문장 집합이 동결과 동일", len(_fp) == 97, f"{len(_fp)}/97")
    _pref = sum(1 for k in _fz if k not in _partial for tag in ("loyalty", "spillover")
                if [it["t"] for it in byf[k][tag]][:len(_rec[k][tag])] == [it["t"] for it in _rec[k][tag]])
    check("97개 팬덤 불릿 = 라이브 목록의 접두어 (194개 목록 중 193 — 예외 1은 r56 수정 문장을 되돌린 여자친구 spillover)", _pref == 193, f"{_pref}/194")
    _r22ok = all([it["t"] for it in _rec[k][tag]] == [it["t"] for it in _r22[k][tag]] for k in _partial for tag in ("loyalty", "spillover"))
    _lost = sum(_fz[k]["activity"] - len(_rec[k]["loyalty"]) - len(_rec[k]["spillover"]) for k in _partial)
    check("BE'O·pH-1·한로로 = r22 백업 불릿 그대로(28·34·33건), 유실 24건(6·10·8)", _r22ok and _lost == 24, f"유실 {_lost}")
else:
    info("data/v7_final/frozen_snapshot_v7_40/ 없음")

# ---------------------------------------------------------------------------
# [AE] 로스터 이력 (data/v7_final/roster_history_v7.csv)
# ---------------------------------------------------------------------------
print("\n[AE] data/v7_final/roster_history_v7.csv — 로스터 이력")
_rh_path = D / "roster_history_v7.csv"
if _rh_path.exists():
    _rh = list(csv.DictReader(open(_rh_path, encoding="utf-8-sig")))
    _rh_live = {r["fandom"] for r in _rh if r["status"] == "live"}
    _rh_frozen = {r["fandom"] for r in _rh if r["in_frozen_v7_40"] == "Y"}
    check("라이브 100개 = 코퍼스 로스터, 동결 100개 = 동결 점수 로스터, 제거 6개", _rh_live == set(byf) and _rh_frozen == {r["fandom"] for r in fzj} and sum(r["status"] == "removed" for r in _rh) == 6,
          f"live {len(_rh_live)}, frozen {len(_rh_frozen)}, removed {sum(r['status']=='removed' for r in _rh)}")
    check("동결 이후 교체 3건: 빈지노(r58)·몬스타엑스(r62)·투어스(TWS)(r63) 진입, BE'O·한로로·pH-1 제거",
          {r["fandom"]: r["entered_round"] for r in _rh if r["status"] == "live" and r["in_frozen_v7_40"] == "N"} == {"빈지노": "r58", "몬스타엑스": "r62", "투어스(TWS)": "r63"}
          and {r["fandom"] for r in _rh if r["status"] == "removed" and r["in_frozen_v7_40"] == "Y"} == {"BE'O", "한로로", "pH-1"})
else:
    info("data/v7_final/roster_history_v7.csv 없음")

# ---------------------------------------------------------------------------
n_ok = sum(1 for _, ok in results if ok); n_all = len(results)
print(f"\n=== 결과: {n_ok}/{n_all} 항목 일치 ({n_all - n_ok}건 불일치) ===")
sys.exit(0 if n_ok == n_all else 1)
