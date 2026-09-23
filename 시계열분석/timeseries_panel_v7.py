# -*- coding: utf-8 -*-
"""시계열 패널 분석 — 근거문장의 시점 태그로 팬덤×연도 패널을 만들어 점수·경로 비중의 추이를 본다.

본 분석(README 0∼9절)과는 별개의 탐색 분석이다. 해석 계층(K→F→페르소나)과 점수 정의는 손대지 않고,
근거문장에 시점(연도)을 붙여 같은 산식을 연도별로 다시 셀 뿐이다.

단계 (시계열 고도화 방안 A·B·E·C):
  A. 문장 시점 태깅  — 본문 연도(가장 늦은 연도) > URL 날짜 > 상대 표현(URL 날짜 기준) 순으로 event_year 결정
  B. 팬덤×연도 패널 — 연도별 EvidenceScore 합(규모)과 문장당 평균(밀도); 5문장 미만 칸은 결측
  E. 수집 편향 보정 — 연도별 코퍼스 점유율, 수집 라운드(≤r39 / r41∼r72) 구성 통제
  C. 경로(F1∼F5) 연도 추이 — 저장된 재현 K=8 모델의 문서-토픽 분포 θ를 토픽 대응표로 공식 토픽→F에 접어 연도별 F 비중과 페르소나 전이
통계: 연도별 횡단면 상관(충성도 밀도 vs 파급효과 밀도), 팬덤·연도 이원 고정효과 회귀, 팬덤별 Spearman 추세, 문장 부트스트랩 CI.

입력(저장소): data/v7_final/fandoms_v3_100.json, bullets_flat_v7_final.csv, bullet_provenance_v7.csv, fandom_scores_live_reference_v7.json,
  lda_v6_diagnostics_live_reference_v7.json, fan_persona_v7.json, factor_pathway_map_v7.json,
  v7_final_10020/index_methodology/evidence_score_by_sentence_v7.csv,
  v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/{lda_model_k8_v7_final.pkl, count_vectorizer_v7_final.pkl, topic_alignment/topic_alignment_v7.csv}, run_lda_v6.py(토크나이저)
출력(이 폴더 output/): CSV 8개 + JSON 2개 + PNG 4장, 그리고 상위 폴더의 시계열_패널분석_V7.md
실행: python 시계열분석/timeseries_panel_v7.py   (약 40초; scipy·statsmodels·scikit-learn·matplotlib·joblib)
"""
import ast, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent; REPO = HERE.parent; D = REPO / "data" / "v7_final"; OUT = HERE / "output"; OUT.mkdir(exist_ok=True)
YEARS = list(range(2015, 2027)); MIN_CELL = 5; MIN_AXIS = 3; MIN_FANDOMS_YEAR = 20; MIN_CELLS_TREND = 4; SEED = 0
LATE_BINS = ("r41∼r72", "r58∼r72", "r62∼r72", "r63∼r72")
TWS = "투어스(TWS)"


def load(p): return json.load(open(p, encoding="utf-8"))
def rows(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def write_csv(p, fieldnames, data):
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(data)


# ---------------------------------------------------------------------------------------------
# A. 문장 시점 태깅
# ---------------------------------------------------------------------------------------------
YEAR_RE = re.compile(r"(?<!\d)(20[0-2]\d)(?!\d)")
URL_DATE_RE = re.compile(r"(?<!\d)(20[12]\d)[/\-\.]?(0[1-9]|1[0-2])(?:[/\-\.]?(0[1-9]|[12]\d|3[01]))?(?!\d)")
REL = [(re.compile(r"올해|이달|이번\s*달|최근|현재|지난주|이번\s*주"), 0), (re.compile(r"지난해|작년|전년"), -1), (re.compile(r"내년|이듬해"), 1), (re.compile(r"재작년"), -2)]


def tag_sentences(flat):
    out = []
    for r in flat:
        text, url = r["text"], r["url"]
        ys = sorted({int(y) for y in YEAR_RE.findall(text) if 2000 <= int(y) <= 2026})
        m = URL_DATE_RE.search(url); url_year = int(m.group(1)) if m else None
        url_date = f"{m.group(1)}-{m.group(2)}" + (f"-{m.group(3)}" if m.group(3) else "") if m else ""
        rel = next((off for rx, off in REL if rx.search(text)), None)
        if ys: ev, src = ys[-1], "text"
        elif url_year and rel is not None: ev, src = url_year + rel, "relative"
        elif url_year: ev, src = url_year, "url"
        else: ev, src = None, "none"
        out.append({"fandom": r["fandom"], "category": r["category"], "bullet_type": r["bullet_type"], "text_years": "|".join(map(str, ys)), "n_text_years": len(ys),
                    "url_date": url_date, "url_year": url_year or "", "relative_expr": "" if rel is None else str(rel), "event_year": ev or "", "year_source": src,
                    "text_url_gap": (ys[-1] - url_year) if (ys and url_year) else ""})
    return out


# ---------------------------------------------------------------------------------------------
# B·E. 팬덤×연도 패널
# ---------------------------------------------------------------------------------------------
def build_panel(tags, ev, prov):
    """tags·ev(evidence 문장 CSV)·prov(시점 태그 CSV)는 같은 순서(팬덤 → loyalty → spillover, idx)."""
    cell = defaultdict(lambda: {"n_loyalty": 0, "n_spillover": 0, "loyalty_sum": 0.0, "spillover_sum": 0.0, "n_late": 0, "scores": {"loyalty": [], "spillover": []}})
    year_total = Counter(); year_total_by_round = defaultdict(Counter); untagged = Counter()
    for t, e, p in zip(tags, ev, prov):
        assert t["fandom"] == e["fandom"] == p["fandom"] and t["bullet_type"] == e["bullet_type"] == p["bullet_type"]
        if not t["event_year"]: untagged[t["fandom"]] += 1; continue
        y = int(t["event_year"])
        if y not in YEARS: untagged[t["fandom"]] += 1; continue
        c = cell[(t["fandom"], y)]; bt = t["bullet_type"]; s = float(e["evidence_score"])
        c["n_" + bt] += 1; c[bt + "_sum"] += s; c["scores"][bt].append(s); c["n_late"] += p["added_bin"] in LATE_BINS
        year_total[y] += 1; year_total_by_round[y]["late" if p["added_bin"] in LATE_BINS else "early"] += 1
    panel = []
    for (f, y), c in sorted(cell.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        n = c["n_loyalty"] + c["n_spillover"]
        panel.append({"fandom": f, "year": y, "n_loyalty": c["n_loyalty"], "n_spillover": c["n_spillover"], "n_total": n,
                      "loyalty_sum": round(c["loyalty_sum"], 2), "spillover_sum": round(c["spillover_sum"], 2),
                      "loyalty_density": round(c["loyalty_sum"] / c["n_loyalty"], 4) if c["n_loyalty"] >= MIN_AXIS else "",
                      "spillover_density": round(c["spillover_sum"] / c["n_spillover"], 4) if c["n_spillover"] >= MIN_AXIS else "",
                      "year_share": round(n / year_total[y], 5), "late_round_share": round(c["n_late"] / n, 4), "valid_cell": int(n >= MIN_CELL)})
    return panel, year_total, year_total_by_round, untagged, cell


def year_stats(panel):
    from scipy import stats
    out = []
    for y in YEARS:
        pv = [r for r in panel if r["year"] == y and r["valid_cell"] and r["loyalty_density"] != "" and r["spillover_density"] != ""]
        row = {"year": y, "n_sentences": sum(r["n_total"] for r in panel if r["year"] == y), "n_fandoms_any": sum(1 for r in panel if r["year"] == y), "n_fandoms_valid": len(pv),
               "r_density": "", "p_density": "", "rho_density": "", "r_sum": "", "mean_loyalty_density": "", "mean_spillover_density": ""}
        if len(pv) >= MIN_FANDOMS_YEAR:
            L = np.array([float(r["loyalty_density"]) for r in pv]); S = np.array([float(r["spillover_density"]) for r in pv])
            r_, p_ = stats.pearsonr(L, S); rho, _ = stats.spearmanr(L, S); rs, _ = stats.pearsonr([r["loyalty_sum"] for r in pv], [r["spillover_sum"] for r in pv])
            row.update({"r_density": round(float(r_), 4), "p_density": round(float(p_), 4), "rho_density": round(float(rho), 4), "r_sum": round(float(rs), 4),
                        "mean_loyalty_density": round(float(L.mean()), 4), "mean_spillover_density": round(float(S.mean()), 4)})
        out.append(row)
    return out


def fandom_trends(panel):
    from scipy import stats
    by = defaultdict(list)
    for r in panel:
        if r["valid_cell"]: by[r["fandom"]].append(r)
    out = []
    for f, cells in by.items():
        cells.sort(key=lambda r: r["year"]); yrs = [r["year"] for r in cells]
        row = {"fandom": f, "n_valid_years": len(cells), "first_year": yrs[0], "last_year": yrs[-1], "peak_year_volume": max(cells, key=lambda r: r["n_total"])["year"],
               "rho_volume": "", "rho_loyalty_density": "", "p_loyalty_density": "", "rho_spillover_density": "", "p_spillover_density": ""}
        if len(cells) >= MIN_CELLS_TREND:
            row["rho_volume"] = round(float(stats.spearmanr(yrs, [r["n_total"] for r in cells])[0]), 4)
            for ax in ("loyalty", "spillover"):
                pts = [(r["year"], float(r[ax + "_density"])) for r in cells if r[ax + "_density"] != ""]
                if len(pts) >= MIN_CELLS_TREND:
                    rho, p = stats.spearmanr([a for a, _ in pts], [b for _, b in pts]); row[f"rho_{ax}_density"] = round(float(rho), 4); row[f"p_{ax}_density"] = round(float(p), 4)
        out.append(row)
    return sorted(out, key=lambda r: -r["n_valid_years"])


def panel_regressions(panel):
    import pandas as pd, statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    df = pd.DataFrame([r for r in panel if r["valid_cell"]]); res = {}
    for ax in ("loyalty_density", "spillover_density"):
        d = df[df[ax] != ""].copy(); d[ax] = d[ax].astype(float); d["year_c"] = d["year"].astype(str)
        m0 = smf.ols(f"{ax} ~ C(fandom)", d).fit(); m1 = smf.ols(f"{ax} ~ C(fandom) + C(year_c)", d).fit(); m2 = smf.ols(f"{ax} ~ C(fandom) + C(year_c) + late_round_share", d).fit()
        a = anova_lm(m0, m1); ye = {y: round(float(v), 4) for y, v in m1.params.items() if y.startswith("C(year_c)")}
        res[ax] = {"n_cells": int(len(d)), "n_fandoms": int(d["fandom"].nunique()), "r2_fandom_fe": round(float(m0.rsquared), 4), "r2_two_way_fe": round(float(m1.rsquared), 4),
                   "year_fe_F": round(float(a["F"][1]), 3), "year_fe_p": float(a["Pr(>F)"][1]), "year_effects_vs_2015": ye,
                   "late_round_share_coef": round(float(m2.params["late_round_share"]), 4), "late_round_share_p": float(m2.pvalues["late_round_share"])}
    d = df.copy(); d["log_n"] = np.log(d["n_total"].astype(float)); d["year_c"] = d["year"].astype(str)
    m = smf.ols("log_n ~ C(fandom) + C(year_c)", d).fit()
    res["log_volume"] = {"r2_two_way_fe": round(float(m.rsquared), 4), "year_effects_vs_2015": {y: round(float(v), 4) for y, v in m.params.items() if y.startswith("C(year_c)")}}
    # 통합 패널: 팬덤 내 편차(within)로 본 충성도–파급효과 관계
    d2 = df[(df["loyalty_density"] != "") & (df["spillover_density"] != "")].copy(); d2["L"] = d2["loyalty_density"].astype(float); d2["S"] = d2["spillover_density"].astype(float)
    mw = smf.ols("S ~ L + C(fandom) + C(year)", d2).fit(); mb = smf.ols("S ~ L", d2).fit()
    res["loyalty_spillover_panel"] = {"pooled_coef": round(float(mb.params["L"]), 4), "pooled_p": float(mb.pvalues["L"]), "within_coef_two_way_fe": round(float(mw.params["L"]), 4), "within_p": float(mw.pvalues["L"]), "n_cells": int(len(d2))}
    return res


def bootstrap_cells(cell, fandoms, B=1000):
    rng = np.random.default_rng(SEED); out = []
    for f in fandoms:
        for y in YEARS:
            c = cell.get((f, y))
            if not c or c["n_loyalty"] + c["n_spillover"] < MIN_CELL: continue
            row = {"fandom": f, "year": y}
            for ax in ("loyalty", "spillover"):
                s = np.array(c["scores"][ax])
                if len(s) >= MIN_AXIS:
                    draws = rng.choice(s, (B, len(s))).mean(1); row[ax + "_density"] = round(float(s.mean()), 4); row[ax + "_lo"] = round(float(np.percentile(draws, 2.5)), 4); row[ax + "_hi"] = round(float(np.percentile(draws, 97.5)), 4)
                else: row[ax + "_density"] = row[ax + "_lo"] = row[ax + "_hi"] = ""
            out.append(row)
    return out


# ---------------------------------------------------------------------------------------------
# C. 경로 비중의 연도 추이 (재현 K=8 모델 θ → 공식 토픽 → F)
# ---------------------------------------------------------------------------------------------
def factor_shares_by_year(tags, corpus_by):
    import joblib
    T = REPO / "v7_final_10020" / "analysis" / "persona_decision_space" / "topic_phi_cosine"
    src = (REPO / "run_lda_v6.py").read_text(encoding="utf-8"); tree = ast.parse(src); pieces = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("PARTICLES", "STOPWORDS", "ENGLISH_STOPWORDS"): pieces.append(ast.get_source_segment(src, node))
        if isinstance(node, ast.FunctionDef) and node.name == "tokenize": pieces.append(ast.get_source_segment(src, node))
    ns = {"re": re}; exec("\n\n".join(pieces), ns); tokenize = ns["tokenize"]
    lda = joblib.load(T / "lda_model_k8_v7_final.pkl"); vec = joblib.load(T / "count_vectorizer_v7_final.pkl")
    diag = load(D / "lda_v6_diagnostics_live_reference_v7.json"); pm = load(D / "factor_pathway_map_v7.json")["mapping"]
    FCODE = {lab: v["f_code"] for lab, v in pm.items()}; FCODE["브랜드·상업형(광고·앰버서더)"] = "F4"
    d_topic_to_F = {int(t): FCODE[diag["factor_labels"][str(fi)]] for t, fi in diag["topic_to_factor"].items()}
    align = [r for r in rows(T / "topic_alignment" / "topic_alignment_v7.csv") if r["pair"].lstrip("﻿") == "D_live_reference_k8→E_live_k8"]
    e_to_d = {int(r["hungarian_topic"]): int(r["src_topic"]) for r in align if r["hungarian_topic"] != ""}; e_jac = {int(r["hungarian_topic"]): float(r["hungarian_score"]) for r in align if r["hungarian_topic"] != ""}
    assert len(e_to_d) == 8, e_to_d
    FC = ["F1", "F2", "F3", "F4", "F5"]; e_to_F = {e: d_topic_to_F[d] for e, d in e_to_d.items()}
    docs, meta = [], []
    for t in tags:
        it = corpus_by[t["fandom"]][t["bullet_type"]][int(t["idx"])] if "idx" in t else None
    # 문서 만들기(파이프라인과 같은 3토큰 필터)
    per_fy = defaultdict(lambda: np.zeros(5)); per_f = defaultdict(lambda: np.zeros(5)); n_docs = 0
    texts, keys = [], []
    for t in tags:
        toks = tokenize(t["_text"])
        if len(toks) < 3: continue
        texts.append(" ".join(toks)); keys.append((t["fandom"], int(t["event_year"]) if t["event_year"] else None))
    theta = lda.transform(vec.transform(texts)); n_docs = len(texts)
    M = np.zeros((8, 5))
    for e, F in e_to_F.items(): M[e, FC.index(F)] = 1.0
    fshare = theta @ M
    for (f, y), v in zip(keys, fshare):
        per_f[f] += v
        if y in YEARS: per_fy[(f, y)] += v
    return per_fy, per_f, n_docs, {str(e): {"official_topic": d, "F": e_to_F[e], "jaccard_top10": e_jac[e]} for e, d in sorted(e_to_d.items())}


# ---------------------------------------------------------------------------------------------
# 그림
# ---------------------------------------------------------------------------------------------
def figures(panel, ys, boots, pers_by_year, round_dist, top8):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.font_manager as fm, os
    for c in [str(REPO / "fonts" / "NotoSansCJKkr-Regular.otf"), str(REPO / "fonts" / "NotoSansCJKkr-Bold.otf"), os.environ.get("KFONT_PATH", "")]:
        if c and os.path.exists(c): fm.fontManager.addfont(c)
    if any(f.name == "Noto Sans CJK KR" for f in fm.fontManager.ttflist): plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False; SURF = "#fcfcfb"; INK = "#222"
    PCOL = {"글로벌투어형": "#c62828", "원정소비형": "#1e5cb3", "현장상업형": "#d9a300", "집단동원형": "#2e7d32"}  # README 그림 5와 같은 팔레트
    # 1. 상위 8개 팬덤 연도 프로파일 (small multiples, 밀도 + CI)
    fig, axes = plt.subplots(2, 4, figsize=(14, 6.4), dpi=220, sharex=True, sharey=True)
    for ax, f in zip(axes.flat, top8):
        ax.set_facecolor(SURF); b = [r for r in boots if r["fandom"] == f]
        for key, col, lab in (("loyalty", "#2a62b8", "팬충성도 밀도"), ("spillover", "#c1440e", "파급효과 밀도")):
            pts = [(r["year"], r[key + "_density"], r[key + "_lo"], r[key + "_hi"]) for r in b if r[key + "_density"] != ""]
            if not pts: continue
            x = [p[0] for p in pts]; ax.plot(x, [p[1] for p in pts], "-o", color=col, lw=1.8, ms=4, label=lab); ax.fill_between(x, [p[2] for p in pts], [p[3] for p in pts], color=col, alpha=.15, lw=0)
        ax.set_title(f, fontsize=10.5, color=INK); ax.grid(alpha=.18); ax.set_xticks([2016, 2020, 2024]); ax.tick_params(labelsize=8.5)
    axes[0, 0].legend(fontsize=8, loc="upper left"); fig.supxlabel("사건 연도 (event_year)", fontsize=10); fig.supylabel("문장당 평균 EvidenceScore (밀도)", fontsize=10)
    fig.suptitle("상위 팬덤의 연도별 점수 밀도 — 5문장 이상 칸만, 음영은 문장 부트스트랩 95% CI", fontsize=12, weight="bold"); fig.tight_layout(); fig.savefig(OUT / "fig_ts01_year_profiles.png"); plt.close(fig)
    # 2. 연도별 횡단면 상관
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=220); ax.set_facecolor(SURF)
    pts = [(r["year"], r["r_density"], r["n_fandoms_valid"]) for r in ys if r["r_density"] != ""]
    ax.axhline(0, color="#bbb", lw=.8); ax.axhline(0.5, color="#999", lw=.8, ls="--"); ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color="#2a62b8", lw=2, ms=6, label="Pearson r (팬충성도 밀도, 파급효과 밀도)")
    for x, r_, n in pts: ax.annotate(f"n={n}", (x, r_), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color="#555")
    ax.set_ylim(-0.6, 1.0); ax.set_xticks([p[0] for p in pts]); ax.set_xlabel("사건 연도"); ax.set_ylabel("횡단면 상관 r"); ax.grid(alpha=.18); ax.legend(fontsize=9, loc="lower left")
    ax.set_title("연도별 횡단면 판별타당도 — 그해 5문장 이상인 팬덤들 사이의 r (점선 = 설계 기준 0.5)", fontsize=11, weight="bold"); fig.tight_layout(); fig.savefig(OUT / "fig_ts02_yearwise_corr.png"); plt.close(fig)
    # 3. 연도별 페르소나 분포 (θ 기반)
    fig, ax = plt.subplots(figsize=(11.5, 4.8), dpi=220); ax.set_facecolor(SURF)
    order = ["글로벌투어형", "원정소비형", "현장상업형", "집단동원형"]; others = sorted({p for y in pers_by_year for p in pers_by_year[y] if p not in order})
    yrs = [y for y in YEARS if pers_by_year.get(y)]; bottom = np.zeros(len(yrs)); extra_cols = ["#6f4fb8", "#7a7a7a", "#8c6d3f", "#3f8c8c"]
    for i, per in enumerate(order + others):
        vals = np.array([pers_by_year[y].get(per, 0) / sum(pers_by_year[y].values()) for y in yrs]); col = PCOL.get(per, extra_cols[(i - 4) % 4])
        ax.bar(yrs, vals, bottom=bottom, color=col, edgecolor="white", linewidth=1, label=per); bottom += vals
    for x, y in zip(yrs, [sum(pers_by_year[y].values()) for y in yrs]): ax.annotate(f"{y}", (x, 1.01), ha="center", fontsize=8, color="#555")
    ax.set_ylim(0, 1.08); ax.set_xlabel("사건 연도 (위 숫자 = 그해 페르소나를 매길 수 있는 팬덤 수)"); ax.set_ylabel("팬덤 비율"); ax.legend(fontsize=8.5, loc="upper left", bbox_to_anchor=(1.01, 1.0), framealpha=.95)
    ax.set_title("연도별 페르소나 분포 — 재현 K=8 모델의 문서-토픽 분포를 공식 토픽→F로 접은 연도별 상위 2 F", fontsize=11, weight="bold"); fig.tight_layout(); fig.savefig(OUT / "fig_ts03_persona_by_year.png"); plt.close(fig)
    # 4. 수집 라운드별 연도 분포
    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=220); ax.set_facecolor(SURF); w = 0.4
    e = [round_dist[y].get("early", 0) for y in YEARS]; l = [round_dist[y].get("late", 0) for y in YEARS]; te, tl = sum(e), sum(l)
    ax.bar([y - w / 2 for y in YEARS], [v / te for v in e], w, color="#2a62b8", label=f"초기 수집(r39 이전, {te:,}건)"); ax.bar([y + w / 2 for y in YEARS], [v / tl for v in l], w, color="#b07a00", label=f"후기 추가(r41-r72, {tl:,}건)")
    ax.set_xlabel("사건 연도"); ax.set_ylabel("해당 수집 구간 문장 중 비율"); ax.grid(axis="y", alpha=.18); ax.legend(fontsize=9)
    ax.set_title("수집 시점별 사건 연도 분포 — 후기 추가분일수록 최근 연도에 몰린다", fontsize=11, weight="bold"); fig.tight_layout(); fig.savefig(OUT / "fig_ts04_round_year_bias.png"); plt.close(fig)


# ---------------------------------------------------------------------------------------------
def main():
    flat = rows(D / "bullets_flat_v7_final.csv"); ev = rows(REPO / "v7_final_10020" / "index_methodology" / "evidence_score_by_sentence_v7.csv"); prov = rows(D / "bullet_provenance_v7.csv")
    assert len(flat) == len(ev) == len(prov) == 10020
    scores = {r["fandom"]: r for r in load(D / "fandom_scores_live_reference_v7.json")}; fp = load(D / "fan_persona_v7.json"); PERSONA = fp["persona_table_definition"]
    live_persona = {p["fandom"]: p["persona"] for p in load(REPO / "v7_final_10020" / "analysis" / "persona_decision_space" / "live_interpretive_layer" / "live_persona_v7.json")["fandoms"]}

    # A
    tags = tag_sentences(flat)
    for t, r in zip(tags, flat): t["_text"] = r["text"]
    write_csv(OUT / "sentence_time_tags_v7.csv", [k for k in tags[0] if k != "_text"], [{k: v for k, v in t.items() if k != "_text"} for t in tags])
    src_cnt = Counter(t["year_source"] for t in tags); yr_cnt = Counter(int(t["event_year"]) for t in tags if t["event_year"])
    gap = [int(t["text_url_gap"]) for t in tags if t["text_url_gap"] != ""]
    A = {"n": len(tags), "by_source": dict(src_cnt), "tagged": sum(v for k, v in src_cnt.items() if k != "none"), "tagged_share": round(sum(v for k, v in src_cnt.items() if k != "none") / len(tags), 4),
         "in_range_2015_2026": sum(v for y, v in yr_cnt.items() if y in YEARS), "event_year_dist": {str(y): yr_cnt.get(y, 0) for y in YEARS}, "before_2015": sum(v for y, v in yr_cnt.items() if y < 2015),
         "text_url_both": len(gap), "text_url_same_year": sum(1 for g in gap if g == 0), "text_url_within_1y": sum(1 for g in gap if abs(g) <= 1), "multi_year_sentences": sum(1 for t in tags if t["n_text_years"] > 1)}

    # B·E
    panel, year_total, round_dist, untagged, cell = build_panel(tags, ev, prov)
    write_csv(OUT / "fandom_year_panel_v7.csv", list(panel[0].keys()), panel)
    ys = year_stats(panel); write_csv(OUT / "year_summary_v7.csv", list(ys[0].keys()), ys)
    tr = fandom_trends(panel); write_csv(OUT / "fandom_trend_v7.csv", list(tr[0].keys()), tr)
    reg = panel_regressions(panel)
    rd = [{"year": y, "early_le_r39": round_dist[y].get("early", 0), "late_r41_r72": round_dist[y].get("late", 0), "late_share": round(round_dist[y].get("late", 0) / max(1, year_total[y]), 4)} for y in YEARS]
    write_csv(OUT / "round_year_distribution_v7.csv", list(rd[0].keys()), rd)
    # 검증: 연도 합 + 미상 = 현재 raw 점수
    chk = 0
    for f, s in scores.items():
        ls = sum(c["loyalty_sum"] for (ff, y), c in cell.items() if ff == f); ss = sum(c["spillover_sum"] for (ff, y), c in cell.items() if ff == f)
        un = [e for t, e in zip(tags, ev) if t["fandom"] == f and (not t["event_year"] or int(t["event_year"]) not in YEARS)]
        ls += sum(float(e["evidence_score"]) for e in un if e["bullet_type"] == "loyalty"); ss += sum(float(e["evidence_score"]) for e in un if e["bullet_type"] == "spillover")
        chk += abs(ls - s["loyalty_raw"]) < 1e-6 and abs(ss - s["spillover_raw"]) < 1e-6
    valid = [r for r in panel if r["valid_cell"]]; per_f_valid = Counter(r["fandom"] for r in valid)
    ranked = sorted(scores, key=lambda f: -(scores[f]["loyalty_score"] + scores[f]["spillover_score"]))
    top8 = [f for f in ranked if per_f_valid.get(f, 0) >= 3][:8]
    boots = bootstrap_cells(cell, top8); write_csv(OUT / "bootstrap_year_cells_v7.csv", list(boots[0].keys()), boots)
    B = {"n_cells": len(panel), "n_valid_cells": len(valid), "fandoms_ge3_valid_years": sum(1 for v in per_f_valid.values() if v >= 3), "fandoms_ge5_valid_years": sum(1 for v in per_f_valid.values() if v >= 5),
         "fandoms_excluded_lt3": [f for f in scores if per_f_valid.get(f, 0) < 3], "raw_score_reconciliation": f"{chk}/100", "top8": top8,
         "trend": {"n_fandoms_tested": sum(1 for r in tr if r["rho_loyalty_density"] != ""), "n_volume_tested": sum(1 for r in tr if r["rho_volume"] != ""),
                   "volume_rho_positive": sum(1 for r in tr if r["rho_volume"] != "" and r["rho_volume"] > 0), "volume_rho_median": round(float(np.median([r["rho_volume"] for r in tr if r["rho_volume"] != ""])), 3),
                   "loyalty_density_sig_up": sum(1 for r in tr if r["rho_loyalty_density"] != "" and r["rho_loyalty_density"] > 0 and r["p_loyalty_density"] < 0.05), "loyalty_density_sig_down": sum(1 for r in tr if r["rho_loyalty_density"] != "" and r["rho_loyalty_density"] < 0 and r["p_loyalty_density"] < 0.05),
                   "spillover_density_sig_up": sum(1 for r in tr if r["rho_spillover_density"] != "" and r["rho_spillover_density"] > 0 and r["p_spillover_density"] < 0.05), "spillover_density_sig_down": sum(1 for r in tr if r["rho_spillover_density"] != "" and r["rho_spillover_density"] < 0 and r["p_spillover_density"] < 0.05),
                   "loyalty_density_rho_median": round(float(np.median([r["rho_loyalty_density"] for r in tr if r["rho_loyalty_density"] != ""])), 3), "spillover_density_rho_median": round(float(np.median([r["rho_spillover_density"] for r in tr if r["rho_spillover_density"] != ""])), 3)}}

    # C
    per_fy, per_f, n_docs, topic_map = factor_shares_by_year(tags, None)
    FC = ["F1", "F2", "F3", "F4", "F5"]; fs_rows = []; pers_by_year = defaultdict(Counter); pers_fy = {}
    valid_keys = {(r["fandom"], r["year"]) for r in valid}
    for (f, y), v in sorted(per_fy.items()):
        sh = v / v.sum(); top2 = sorted(range(5), key=lambda i: -sh[i])[:2]; per = PERSONA["|".join(sorted(FC[i] for i in top2))]
        row = {"fandom": f, "year": y, "n_docs": "", **{FC[i]: round(float(sh[i]), 4) for i in range(5)}, "top2": "+".join(sorted(FC[i] for i in top2)), "persona": per, "valid_cell": int((f, y) in valid_keys)}
        fs_rows.append(row)
        if (f, y) in valid_keys: pers_by_year[y][per] += 1; pers_fy[(f, y)] = per
    write_csv(OUT / "fandom_year_factor_share_v7.csv", list(fs_rows[0].keys()), fs_rows)
    # 검증: 전 연도 합산 θ-F 비중 vs 공식 factor_share
    from scipy import stats
    FCODE_OFF = {"현장경제형(콘서트·투어·매진)": "F3", "소비력형(초동·판매·앨범)": "F2", "결속형(팬클럽·기부·커뮤니티)": "F1", "브랜드·상업형(광고·앰버서더)": "F4", "차트·확산형(1위·빌보드·기록)": "F5"}
    off = {f: {FCODE_OFF[k]: v for k, v in scores[f]["factor_share"].items()} for f in scores}
    corr = {}; absdiff = []
    for i, F in enumerate(FC):
        a = [per_f[f][i] / per_f[f].sum() for f in scores]; b = [off[f][F] for f in scores]; corr[F] = round(float(stats.pearsonr(a, b)[0]), 3); absdiff += [abs(x - y) for x, y in zip(a, b)]
    theta_persona = {}
    for f in scores:
        sh = per_f[f] / per_f[f].sum(); top2 = sorted(range(5), key=lambda i: -sh[i])[:2]; theta_persona[f] = PERSONA["|".join(sorted(FC[i] for i in top2))]
    same = sum(1 for f in scores if theta_persona[f] == live_persona[f])
    # 전이: 첫 유효 연도 vs 마지막 유효 연도
    trans = []; by_f = defaultdict(list)
    for (f, y), per in pers_fy.items(): by_f[f].append((y, per))
    for f, lst in by_f.items():
        lst.sort(); n_ch = sum(1 for (y1, p1), (y2, p2) in zip(lst, lst[1:]) if p1 != p2)
        trans.append({"fandom": f, "n_years": len(lst), "first_year": lst[0][0], "first_persona": lst[0][1], "last_year": lst[-1][0], "last_persona": lst[-1][1], "changed": int(lst[0][1] != lst[-1][1]), "n_switches": n_ch, "path": " → ".join(f"{y}:{p}" for y, p in lst), "official_persona_all_years": live_persona[f]})
    trans.sort(key=lambda r: (-r["changed"], -r["n_years"])); write_csv(OUT / "persona_transition_v7.csv", list(trans[0].keys()), trans)
    C = {"n_docs_theta": n_docs, "replica_topic_map": topic_map, "aggregate_vs_official_factor_share_r": corr, "aggregate_vs_official_mean_abs_diff": round(float(np.mean(absdiff)), 4),
         "theta_persona_same_as_official": f"{same}/100", "fandoms_with_persona_years": len(trans), "changed_first_to_last": sum(r["changed"] for r in trans), "any_switch": sum(1 for r in trans if r["n_switches"]),
         "persona_by_year": {str(y): dict(pers_by_year[y]) for y in YEARS if pers_by_year.get(y)}}

    figures(panel, ys, boots, pers_by_year, round_dist, top8)
    E = {"year_totals": {str(y): year_total[y] for y in YEARS}, "late_share_by_year": {str(y): rd[i]["late_share"] for i, y in enumerate(YEARS)},
         "share_2025_2026": round(sum(year_total[y] for y in (2025, 2026)) / sum(year_total.values()), 4),
         "late_round_share_coef": {ax: [reg[ax]["late_round_share_coef"], reg[ax]["late_round_share_p"]] for ax in ("loyalty_density", "spillover_density")}}
    summary = {"A_time_tags": A, "B_panel": B, "E_collection_bias": E, "C_factor_by_year": C, "regressions": reg, "year_summary": ys, "settings": {"years": [YEARS[0], YEARS[-1]], "min_cell": MIN_CELL, "min_axis": MIN_AXIS, "min_fandoms_year": MIN_FANDOMS_YEAR, "min_cells_trend": MIN_CELLS_TREND, "bootstrap_B": 1000, "seed": SEED}}
    json.dump(summary, open(OUT / "summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_md(summary, ys, tr, trans, rd)
    print(json.dumps({"tagged": A["tagged_share"], "valid_cells": B["n_valid_cells"], "fandoms_ge3": B["fandoms_ge3_valid_years"], "reconcile": B["raw_score_reconciliation"], "theta_same": C["theta_persona_same_as_official"], "corr": corr}, ensure_ascii=False))


def write_md(S, ys, tr, trans, rd):
    A, B, C, E, R = S["A_time_tags"], S["B_panel"], S["C_factor_by_year"], S["E_collection_bias"], S["regressions"]
    yv = [r for r in ys if r["r_density"] != ""]
    md = ["# 시계열 패널 분석 — 근거문장의 시점으로 본 팬충성도·파급효과·경로 비중의 연도별 추이\n",
          "본 분석(루트 README)과 **별개의 탐색 분석**이다. 해석 계층과 점수 정의는 그대로 두고, 근거문장 10,020건에 사건 연도를 붙여 같은 EvidenceScore 산식을 연도별로 다시 센 팬덤×연도 패널을 만든다. "
          "방법·규칙은 `시계열_패널분석_상세명세서.docx`, 재현은 `timeseries_panel_v7.py`(파이썬)·`시계열_패널분석_v7.ipynb`(노트북)·`R/`(R 대응 코드)이다.\n",
          "## 0. 결론\n",
          f"1. **시점을 붙일 수 있는 문장은 {A['tagged']:,}건({A['tagged_share']:.1%})** 이다(본문 연도 {A['by_source'].get('text', 0):,} · URL 날짜 {A['by_source'].get('url', 0):,} · 상대 표현 {A['by_source'].get('relative', 0):,}). 본문 연도와 URL 연도가 둘 다 있는 {A['text_url_both']:,}건 중 같은 해가 {A['text_url_same_year']:,}건, ±1년 안이 {A['text_url_within_1y']:,}건이다.",
          f"2. **팬덤×연도 칸 {B['n_cells']:,}개 중 5문장 이상인 유효 칸은 {B['n_valid_cells']:,}개**, 유효 연도가 3개 이상인 팬덤은 {B['fandoms_ge3_valid_years']}개(5개 이상 {B['fandoms_ge5_valid_years']}개)다. 연도별 합에 연도 미상 문장을 더하면 현재 raw 점수가 {B['raw_score_reconciliation']} 재현된다.",
          f"3. **코퍼스는 최근에 몰려 있다.** 사건 연도의 {E['share_2025_2026']:.1%}가 2025∼2026년이고, 후기 추가분(r41∼r72)일수록 최근 연도 비중이 높다. 문장 수(규모)는 팬덤 대부분에서 연도와 함께 늘지만(팬덤별 Spearman ρ 중앙값 {B['trend']['volume_rho_median']}, 양수 {B['trend']['volume_rho_positive']}/{B['trend']['n_volume_tested']}; 유효 연도 4개 이상인 팬덤 기준), 이는 수집 시점의 효과가 섞인 값이라 성장으로 읽지 않는다.",
          f"4. **밀도(문장당 평균 EvidenceScore)는 뚜렷한 추세가 없다.** 팬덤별 ρ 중앙값은 충성도 {B['trend']['loyalty_density_rho_median']}, 파급효과 {B['trend']['spillover_density_rho_median']}이고, 유의(p<0.05)한 상승/하락은 충성도 {B['trend']['loyalty_density_sig_up']}/{B['trend']['loyalty_density_sig_down']}개, 파급효과 {B['trend']['spillover_density_sig_up']}/{B['trend']['spillover_density_sig_down']}개다(밀도 추세를 잴 수 있는 팬덤 {B['trend']['n_fandoms_tested']}개). 이원 고정효과 회귀에서 연도 효과는 충성도 F={R['loyalty_density']['year_fe_F']} (p={R['loyalty_density']['year_fe_p']:.3g}), 파급효과 F={R['spillover_density']['year_fe_F']} (p={R['spillover_density']['year_fe_p']:.3g})다.",
          f"5. **연도별 횡단면의 충성도–파급효과 관계는 해마다 다르다.** 밀도 기준 r은 {min(r['r_density'] for r in yv)}∼{max(r['r_density'] for r in yv)}({yv[0]['year']}∼{yv[-1]['year']}, 그해 20개 이상 팬덤이 있는 연도만)이며, 팬덤·연도 고정효과를 넣은 패널 내부 계수는 {R['loyalty_spillover_panel']['within_coef_two_way_fe']}(p={R['loyalty_spillover_panel']['within_p']:.3g}; 통합 {R['loyalty_spillover_panel']['pooled_coef']}).",
          f"6. **경로 비중의 연도 추이(재현 모델 θ 기반)** 에서는 유효 칸이 있는 팬덤 {C['fandoms_with_persona_years']}개 중 첫 유효 연도와 마지막 유효 연도의 페르소나가 다른 팬덤이 {C['changed_first_to_last']}개, 한 번이라도 바뀐 팬덤이 {C['any_switch']}개다. 다만 이 θ는 저장된 재현 K=8 모델(옛 토크나이저)에서 나온 근사값으로, 전 연도 합산 F 비중과 공식 factor_share의 상관은 " + " · ".join(f"{k} {v}" for k, v in C['aggregate_vs_official_factor_share_r'].items()) + f", 페르소나 일치 {C['theta_persona_same_as_official']}에 그친다. 연도 칸이 작아 페르소나가 자주 바뀌는 것은 상당 부분 표본 잡음이며, 이 절은 방향 참고용이지 공식 해석 계층이 아니다.\n",
          "## 1. 문장 시점 태깅 (A)\n", "| 항목 | 값 |\n|---|---|",
          f"| 문장 수 | {A['n']:,} |", f"| 시점 태그 | {A['tagged']:,} ({A['tagged_share']:.1%}) — text {A['by_source'].get('text', 0):,} · url {A['by_source'].get('url', 0):,} · relative {A['by_source'].get('relative', 0):,} · none {A['by_source'].get('none', 0):,} |",
          f"| 2015∼2026 범위 안 | {A['in_range_2015_2026']:,} (2015년 이전 {A['before_2015']}) |", f"| 복수 연도 문장(가장 늦은 연도 채택) | {A['multi_year_sentences']:,} |",
          f"| 본문 연도 vs URL 연도 | 둘 다 있는 {A['text_url_both']:,}건 중 같은 해 {A['text_url_same_year']:,}, ±1년 {A['text_url_within_1y']:,} |",
          "\n연도별 문장 수: " + " · ".join(f"{y} {n:,}" for y, n in A["event_year_dist"].items()) + "\n",
          "## 2. 팬덤×연도 패널 (B) — 연도별 요약\n", "| 연도 | 문장 | 팬덤(유효) | 평균 충성도 밀도 | 평균 파급효과 밀도 | r(밀도) | ρ(밀도) | r(합) | 후기 추가 비율 |\n|---|---|---|---|---|---|---|---|---|"]
    ls = {r["year"]: r["late_share"] for r in rd}
    for r in ys: md.append(f"| {r['year']} | {r['n_sentences']:,} | {r['n_fandoms_valid']} | {r['mean_loyalty_density']} | {r['mean_spillover_density']} | {r['r_density']} | {r['rho_density']} | {r['r_sum']} | {ls[r['year']]:.0%} |")
    md += ["\n밀도 = 그해 문장의 평균 EvidenceScore, 합 = 그해 문장 점수 합(규모). r·ρ는 그해 5문장 이상 팬덤 사이의 횡단면 상관이며 20개 미만이면 비운다.\n",
           "![연도 프로파일](output/fig_ts01_year_profiles.png)\n", "![연도별 횡단면 상관](output/fig_ts02_yearwise_corr.png)\n",
           "## 3. 팬덤별 추세 (유효 연도 4개 이상)\n", "| 팬덤 | 유효 연도 | 구간 | 규모 ρ | 충성도 밀도 ρ (p) | 파급효과 밀도 ρ (p) |\n|---|---|---|---|---|---|"]
    for r in [x for x in tr if x["rho_loyalty_density"] != ""][:20]: md.append(f"| {r['fandom']} | {r['n_valid_years']} | {r['first_year']}∼{r['last_year']} | {r['rho_volume']} | {r['rho_loyalty_density']} ({r['p_loyalty_density']}) | {r['rho_spillover_density']} ({r['p_spillover_density']}) |")
    md += [f"\n전체는 `output/fandom_trend_v7.csv`(상위 20개만 표시). 유효 연도 3개 미만이라 제외한 팬덤: {', '.join(B['fandoms_excluded_lt3']) or '없음'}.\n",
           "## 4. 고정효과 회귀와 수집 편향 (E)\n", "| 종속변수 | 칸 | R²(팬덤 FE) | R²(팬덤+연도 FE) | 연도 효과 F (p) | 후기 추가 비율 계수 (p) |\n|---|---|---|---|---|---|"]
    for ax, nm in (("loyalty_density", "충성도 밀도"), ("spillover_density", "파급효과 밀도")):
        r = R[ax]; md.append(f"| {nm} | {r['n_cells']} | {r['r2_fandom_fe']} | {r['r2_two_way_fe']} | {r['year_fe_F']} ({r['year_fe_p']:.3g}) | {r['late_round_share_coef']} ({r['late_round_share_p']:.3g}) |")
    md += [f"\n충성도–파급효과 패널 회귀(S ~ L): 통합 계수 {R['loyalty_spillover_panel']['pooled_coef']} (p={R['loyalty_spillover_panel']['pooled_p']:.3g}), 팬덤·연도 고정효과 후 {R['loyalty_spillover_panel']['within_coef_two_way_fe']} (p={R['loyalty_spillover_panel']['within_p']:.3g}), 칸 {R['loyalty_spillover_panel']['n_cells']}. 로그 문장 수의 연도 효과(2015 대비): " + ", ".join(f"{k[-5:-1]} {v:+.2f}" for k, v in R["log_volume"]["year_effects_vs_2015"].items()) + ".\n",
           "![수집 편향](output/fig_ts04_round_year_bias.png)\n",
           "## 5. 경로 비중의 연도 추이와 페르소나 전이 (C, 근사)\n",
           f"재현 K=8 모델(`topic_phi_cosine/lda_model_k8_v7_final.pkl`, 옛 토크나이저·{C['n_docs_theta']:,}문서)의 θ를 토픽 대응표(D_live_reference_k8→E_live_k8, Hungarian)로 공식 토픽에 잇고 공식 토픽→F 배정으로 접었다. 대응 Jaccard가 낮은 토픽이 있어 근사다.\n",
           "| 재현 토픽 | 공식 토픽 | F | Jaccard(top10) |\n|---|---|---|---|"]
    for e, v in C["replica_topic_map"].items(): md.append(f"| E{e} | T{v['official_topic']} | {v['F']} | {v['jaccard_top10']} |")
    md += [f"\n검증: 전 연도 합산 θ-F 비중 vs 공식 factor_share 상관 " + " · ".join(f"{k} {v}" for k, v in C['aggregate_vs_official_factor_share_r'].items()) + f", 평균 절대 차이 {C['aggregate_vs_official_mean_abs_diff']}, 페르소나 일치 {C['theta_persona_same_as_official']}.\n",
           "![연도별 페르소나](output/fig_ts03_persona_by_year.png)\n", "| 팬덤 | 유효 연도 | 첫 연도 페르소나 | 마지막 연도 페르소나 | 전환 횟수 | 경로 |\n|---|---|---|---|---|---|"]
    for r in trans[:15]: md.append(f"| {r['fandom']} | {r['n_years']} | {r['first_year']} {r['first_persona']} | {r['last_year']} {r['last_persona']} | {r['n_switches']} | {r['path']} |")
    md += ["\n전체는 `output/persona_transition_v7.csv`.\n",
           "## 6. 한계\n",
           "1. 사건 연도는 언론이 언급한 연도의 근사다. 회고 서술이 과거 연도를 만들고, 최근 사건은 연도를 생략하기도 한다. 복수 연도 문장은 가장 늦은 연도를 쓴다.\n"
           "2. 코퍼스는 최근 편중이며 팬덤마다 편중이 다르다. 신생 그룹의 과거 칸은 비어 있고, 규모 추세는 수집 시점과 섞여 있다. 밀도·점유율·고정효과로 보정했지만 완전하지 않다.\n"
           "3. 연도 칸의 표본은 작다(중앙값 수 문장). 한 해 값보다 방향과 CI를 읽는다.\n"
           "4. 5절의 θ는 공식 모델이 아니라 저장된 재현 모델에서 나온 것이며, 토픽 대응이 약한 곳이 있다. 페르소나 전이는 방향 참고용이다.\n"
           "5. 해석 계층·순위표·README 수치는 이 분석으로 바뀌지 않는다.\n",
           "## 7. 파일\n", "| 파일 | 내용 |\n|---|---|",
           "| `output/sentence_time_tags_v7.csv` | 문장 10,020건의 시점 태그(본문 연도·URL 날짜·상대 표현·event_year·year_source) |",
           "| `output/fandom_year_panel_v7.csv` | 팬덤×연도 칸: 문장 수·점수 합·밀도·연도 점유율·후기 추가 비율·유효 여부 |",
           "| `output/year_summary_v7.csv` · `fandom_trend_v7.csv` · `bootstrap_year_cells_v7.csv` · `round_year_distribution_v7.csv` | 연도 요약, 팬덤별 추세, 상위 8개 팬덤 연도 칸 CI, 수집 구간별 연도 분포 |",
           "| `output/fandom_year_factor_share_v7.csv` · `persona_transition_v7.csv` | 연도별 F 비중과 페르소나, 첫·마지막 연도 전이 |",
           "| `output/summary_v7.json` | 위 표들의 요약 수치(명세서·노트북·R 대조용) |",
           "| `output/fig_ts01∼04*.png` | 그림 4장 |",
           "| `timeseries_panel_v7.py` · `build_timeseries_notebook_v7.py` · `시계열_패널분석_v7.ipynb` · `R/` | 재현 코드 |"]
    (HERE / "시계열_패널분석_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
