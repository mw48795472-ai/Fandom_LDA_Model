# -*- coding: utf-8 -*-
"""README 5절 그림 3장을 채택된 해석 계층(기본: r73, persona_decision_space/live_interpretive_layer/)으로 그린다.
  fig05_persona_map.png            팬충성도 × 파급효과 평면, 페르소나 4유형 색칠
  fig06_factor_specific_impact.png BTS·임영웅·리센느 + 합산 상위 17개 팬덤의 F1∼F5 분해(비중 × 점수)
  fig07b_persona_pca.png           팬덤별 F1∼F5 비중의 PCA 2성분(페르소나 색) + loading 인셋
옵션: --layer 폴더(기본 live_interpretive_layer) --suffix 접미사(예: _r72 → fig05_persona_map_r72.png)
글꼴: 저장소 fonts/NotoSansCJKkr-{Regular,Bold}.otf (없으면 KFONT_PATH). 팔레트 4색은 dataviz 검증 통과(색각·대비).
실행: python v7_final_10020/charts/build_live_layer_figures_v7.py
"""
import csv, json, os, sys
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager as fm, matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

BASE = Path(__file__).resolve().parents[2]
_a = sys.argv[1:]; _opt = {_a[i]: _a[i + 1] for i in range(0, len(_a) - 1, 2) if _a[i].startswith("--")}
L = BASE / _opt["--layer"] if "--layer" in _opt else BASE / "v7_final_10020" / "analysis" / "persona_decision_space" / "live_interpretive_layer"
SUF = _opt.get("--suffix", ""); OUT = BASE / "assets" / "readme"
for c in [str(BASE / "fonts" / "NotoSansCJKkr-Regular.otf"), str(BASE / "fonts" / "NotoSansCJKkr-Bold.otf"), os.environ.get("KFONT_PATH", "")]:
    if c and os.path.exists(c): fm.fontManager.addfont(c)
plt.rcParams["font.family"] = "Noto Sans CJK KR" if any("Noto Sans CJK KR" == f.name for f in fm.fontManager.ttflist) else plt.rcParams["font.family"]; plt.rcParams["axes.unicode_minus"] = False
P = json.load(open(L / "live_persona_v7.json", encoding="utf-8")); pay = json.load(open(BASE / "data" / "v7_final" / "chart3d_payload_live_reference_v7.json", encoding="utf-8"))
fs = P["fandoms"]; cnt = P["persona_counts"]; FC = ["F1", "F2", "F3", "F4", "F5"]
FN = {"F1": "F1 팬덤결속", "F2": "F2 직접소비", "F3": "F3 현장경제", "F4": "F4 산업전이", "F5": "F5 글로벌확산"}
PALETTE = ["#c1440e", "#2a62b8", "#b07a00", "#6f4fb8", "#3d8a3d"]  # 앞 4색 검증 통과; 5번째는 실현 페르소나가 5개일 때만
COL = {per: PALETTE[i] for i, per in enumerate(sorted(cnt, key=lambda k: -cnt[k]))}
SURF = "#fcfcfb"; TAG = P.get("model", "")[:30]

def label_points(ax, xs, ys, names_to_mark):
    idx = {f["fandom"]: i for i, f in enumerate(fs)}
    for nm, dx, dy, ha in names_to_mark:
        if nm not in idx: continue
        i = idx[nm]; ax.annotate(nm, (xs[i], ys[i]), xytext=(xs[i] + dx, ys[i] + dy), fontsize=9, color="#222", ha=ha, zorder=5, arrowprops=dict(arrowstyle="-", color="#999", lw=.6))

# fig05
fig, ax = plt.subplots(figsize=(10, 7.4), dpi=240); ax.set_facecolor(SURF)
for per, col in COL.items():
    idx = [i for i, f in enumerate(fs) if f["persona"] == per]
    ax.scatter([fs[i]["spillover_score"] for i in idx], [fs[i]["loyalty_score"] for i in idx], s=64, c=col, alpha=.92, edgecolors="white", linewidths=1.2, label=f"{per} ({len(idx)})", zorder=3)
ax.axvline(pay["smean"], color="#999", ls="--", lw=.8, zorder=1); ax.axhline(pay["lmean"], color="#999", ls="--", lw=.8, zorder=1)
label_points(ax, [f["spillover_score"] for f in fs], [f["loyalty_score"] for f in fs], [("BTS", -0.02, 0.01, "right"), ("임영웅", 0.015, 0.012, "left"), ("리센느(RESCENE)", 0.015, -0.03, "left"), ("TWICE", -0.02, 0.012, "right"), ("SEVENTEEN", 0.015, 0.01, "left"), ("god", 0.015, 0.0, "left"), ("투어스(TWS)", 0.015, -0.03, "left")])
ax.set_xlabel("파급효과 (spillover_score)"); ax.set_ylabel("팬충성도 (loyalty_score)"); ax.grid(alpha=.18, zorder=0)
ax.set_title("Fan Persona Map — 팬충성도 × 파급효과 평면의 페르소나 분포 (채택 해석 계층, 100개 팬덤)", fontsize=12, weight="bold")
ax.legend(loc="lower right", fontsize=9.5, title="페르소나 (상위 2 F 조합)", framealpha=.95); fig.tight_layout(); fig.savefig(OUT / f"fig05_persona_map{SUF}.png"); plt.close(fig)

# fig06
top = sorted(fs, key=lambda f: -(f["loyalty_score"] + f["spillover_score"]))[:17]; names = ["BTS", "임영웅", "리센느(RESCENE)"] + [f["fandom"] for f in top if f["fandom"] not in ("BTS", "임영웅", "리센느(RESCENE)")]
byname = {f["fandom"]: f for f in fs}; names = [n for n in names if n in byname][:20]
fig, axes = plt.subplots(1, 2, figsize=(14, 7.4), dpi=240, sharey=True)
for ax, key, ttl in ((axes[0], "factor_specific_loyalty", "팬충성도 분해 (비중 × 점수)"), (axes[1], "factor_specific_spillover", "파급효과 분해 (비중 × 점수)")):
    ax.set_facecolor(SURF); left = np.zeros(len(names))
    for i, fc in enumerate(FC):
        vals = np.array([byname[n][key].get(fc, 0) for n in names]); ax.barh(range(len(names)), vals, left=left, color=PALETTE[i], edgecolor="white", linewidth=.8, label=FN[fc]); left += vals
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=9.5); ax.invert_yaxis(); ax.set_title(ttl, fontsize=11); ax.grid(axis="x", alpha=.2)
axes[0].legend(fontsize=8.5, loc="lower right"); fig.suptitle("경로별(F1~F5) 팬충성도·파급효과 분해 — BTS·임영웅·리센느 + 합산 상위 17", fontsize=12, weight="bold"); fig.tight_layout(); fig.savefig(OUT / f"fig06_factor_specific_impact{SUF}.png"); plt.close(fig)

# fig07b
sh = np.array([[f["factor_specific_loyalty"][c] / f["loyalty_score"] if f["loyalty_score"] else f["factor_specific_spillover"][c] / f["spillover_score"] for c in FC] for f in fs])
pca = PCA(n_components=2).fit(sh - sh.mean(0)); pc = pca.transform(sh - sh.mean(0)); vr = pca.explained_variance_ratio_
d = np.linalg.norm(pc - pc.mean(0), axis=1); far = [fs[i]["fandom"] for i in np.argsort(-d)[:4]]
fig = plt.figure(figsize=(13.2, 7.4), dpi=240); gs = fig.add_gridspec(1, 2, width_ratios=[3.1, 1], wspace=0.08); ax = fig.add_subplot(gs[0]); ins = fig.add_subplot(gs[1]); ax.set_facecolor(SURF)
for per, col in COL.items():
    idx = [i for i, f in enumerate(fs) if f["persona"] == per]; ax.scatter(pc[idx, 0], pc[idx, 1], s=64, c=col, alpha=.92, edgecolors="white", linewidths=1.2, label=f"{per} ({len(idx)})", zorder=3)
marks = [(n, 0.014, 0.012, "left") for n in far] + [("BTS", 0.014, -0.03, "left"), ("임영웅", -0.014, -0.03, "right"), ("투어스(TWS)", 0.012, 0.016, "left")]
label_points(ax, pc[:, 0], pc[:, 1], marks)
ax.axhline(0, color="#bbb", lw=.7, zorder=1); ax.axvline(0, color="#bbb", lw=.7, zorder=1); ax.grid(alpha=.18, zorder=0)
lead = lambda k: FN[FC[int(np.argmax(np.abs(pca.components_[k])))]]
ax.set_xlabel(f"PC1 ({vr[0]:.1%}) — 주 방향 {lead(0)}"); ax.set_ylabel(f"PC2 ({vr[1]:.1%}) — 주 방향 {lead(1)}")
ax.set_title("Persona decision space — 팬덤별 F1~F5 비중의 PCA (채택 해석 계층, 100개 팬덤)", fontsize=12, weight="bold"); ax.legend(fontsize=9.5, title="페르소나 (상위 2 F 조합)", loc="best", framealpha=.95)
ax.set_xlim(pc[:, 0].min() - 0.06, pc[:, 0].max() + 0.07); ax.set_ylim(pc[:, 1].min() - 0.05, pc[:, 1].max() + 0.06)
# 오른쪽 패널: F1∼F5 loading 화살표 (같은 PC1·PC2 축 방향)
ins.set_facecolor("white"); tips = [(pca.components_[0, i], pca.components_[1, i]) for i in range(5)]
for i, fc in enumerate(FC):
    x, y = tips[i]; ins.annotate("", xy=(x, y), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.4))
    # 라벨: 화살표 끝 바깥쪽, 서로 가까우면 위아래로 벌린다
    lx, ly = x * 1.18, y * 1.18
    for j in range(i):
        if abs(lx - tips[j][0] * 1.18) < 0.35 and abs(ly - tips[j][1] * 1.18) < 0.18: ly += 0.2 if ly >= 0 else -0.2
    ins.text(lx + (0.04 if x >= 0 else -0.04), ly, FN[fc], fontsize=9, color="#333", ha="left" if x >= 0 else "right", va="center", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=.9))
ins.set_xlim(-1.35, 1.6); ins.set_ylim(-1.3, 1.3); ins.axhline(0, color="#ccc", lw=.6); ins.axvline(0, color="#ccc", lw=.6); ins.set_xticks([]); ins.set_yticks([]); ins.set_aspect("equal")
ins.set_title("F 비중의 축 방향 (loading)", fontsize=10); ins.set_xlabel("PC1 →", fontsize=9); ins.set_ylabel("PC2 →", fontsize=9)
for sp in ins.spines.values(): sp.set_edgecolor("#bbb")
fig.tight_layout(); fig.savefig(OUT / f"fig07b_persona_pca{SUF}.png"); plt.close(fig)
json.dump({"pca_var_ratio": [round(float(v), 4) for v in vr], "loadings": {fc: [round(float(pca.components_[0, i]), 4), round(float(pca.components_[1, i]), 4)] for i, fc in enumerate(FC)}, "farthest_from_center": far, "palette": COL}, open(L / "live_pca_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("figs written", SUF or "(current)", "PCA var", [round(float(v), 3) for v in vr], "persona", cnt, "far", far)
