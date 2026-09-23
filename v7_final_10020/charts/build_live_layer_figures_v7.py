# -*- coding: utf-8 -*-
"""README 5절 그림 4장을 라이브 해석 계층(게이트 v2 통과 모델, 라이브 K=8 참고 재적합)으로 그린다.
  fig05_persona_map.png            팬충성도 × 파급효과 평면, 페르소나 4유형(라이브) 색칠
  fig06_factor_specific_impact.png BTS·임영웅·리센느 + 합산 상위 17개 팬덤의 F1~F5 분해(비중 × 점수)
  fig07a_persona_k_to_f.png        라이브 K=8 토픽 → F 배정표(φ·병합 높이가 저장돼 있지 않아 덴드로그램 대신)
  fig07b_persona_pca.png           팬덤별 F1~F5 비중의 PCA 2성분(페르소나 색)
입력: analysis/persona_decision_space/live_interpretive_layer/{live_persona_v7.json, live_k_to_f_v7.csv}, chart3d payload(표본 평균)
한글 폰트: KFONT_PATH 환경변수 또는 저장소 fonts/ 의 Noto Sans KR. 실행: KFONT_PATH=... python v7_final_10020/charts/build_live_layer_figures_v7.py
"""
import csv, json, os
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.font_manager as fm, matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

BASE = Path(__file__).resolve().parents[2]; L = BASE / "v7_final_10020" / "analysis" / "persona_decision_space" / "live_interpretive_layer"; OUT = BASE / "assets" / "readme"
for c in [os.environ.get("KFONT_PATH", ""), str(BASE / "fonts" / "NotoSansKR.ttf"), "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "C:/Windows/Fonts/malgun.ttf"]:
    if c and os.path.exists(c): fm.fontManager.addfont(c); plt.rcParams["font.family"] = fm.FontProperties(fname=c).get_name(); break
else: print("[warn] 한글 폰트 없음 — KFONT_PATH 지정")
plt.rcParams["axes.unicode_minus"] = False
P = json.load(open(L / "live_persona_v7.json", encoding="utf-8")); pay = json.load(open(BASE / "data" / "v7_final" / "chart3d_payload_live_reference_v7.json", encoding="utf-8"))
k2f = list(csv.DictReader(open(L / "live_k_to_f_v7.csv", encoding="utf-8-sig")))
COL = {"글로벌투어형": "#c1440e", "현장상업형": "#1f6f8b", "원정소비형": "#e0a100", "집단동원형": "#4e8a3e"}; FC = ["F1", "F2", "F3", "F4", "F5"]
FN = {"F1": "F1 팬덤결속", "F2": "F2 직접소비", "F3": "F3 현장경제", "F4": "F4 산업전이", "F5": "F5 글로벌확산"}
fs = P["fandoms"]; cnt = P["persona_counts"]

# fig05
fig, ax = plt.subplots(figsize=(9.6, 7.2), dpi=250)
for per, col in COL.items():
    xs = [f["spillover_score"] for f in fs if f["persona"] == per]; ys = [f["loyalty_score"] for f in fs if f["persona"] == per]
    ax.scatter(xs, ys, s=46, c=col, alpha=.85, edgecolors="white", linewidths=.5, label=f"{per} ({cnt.get(per, 0)})")
ax.axvline(pay["smean"], color="#888", ls="--", lw=.8); ax.axhline(pay["lmean"], color="#888", ls="--", lw=.8)
for f in fs:
    if f["fandom"] in ("BTS", "임영웅", "리센느(RESCENE)", "TWICE", "SEVENTEEN", "god"): ax.annotate(f["fandom"], (f["spillover_score"], f["loyalty_score"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
ax.set_xlabel("파급효과 (spillover_score)"); ax.set_ylabel("팬충성도 (loyalty_score)"); ax.set_title("Fan Persona Map — 라이브 코퍼스 10,020건, K=8→M=5 (게이트 v2 통과 모델)", fontsize=11)
ax.legend(loc="lower right", fontsize=9, title="페르소나 (상위 2 F 조합)"); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(OUT / "fig05_persona_map.png"); plt.close(fig)

# fig06
top = sorted(fs, key=lambda f: -(f["loyalty_score"] + f["spillover_score"]))[:17]; names = ["BTS", "임영웅", "리센느(RESCENE)"] + [f["fandom"] for f in top if f["fandom"] not in ("BTS", "임영웅", "리센느(RESCENE)")]
byname = {f["fandom"]: f for f in fs}; names = [n for n in names if n in byname][:20]
fig, axes = plt.subplots(1, 2, figsize=(14, 7.2), dpi=250, sharey=True)
colors = ["#4e8a3e", "#e0a100", "#c1440e", "#1f6f8b", "#7b5ea7"]
for ax, key, ttl in ((axes[0], "factor_specific_loyalty", "팬충성도 분해 (비중 × 점수)"), (axes[1], "factor_specific_spillover", "파급효과 분해 (비중 × 점수)")):
    left = np.zeros(len(names))
    for i, fc in enumerate(FC):
        vals = np.array([byname[n][key].get(fc, 0) for n in names]); ax.barh(range(len(names)), vals, left=left, color=colors[i], label=FN[fc]); left += vals
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=9); ax.invert_yaxis(); ax.set_title(ttl, fontsize=11); ax.grid(axis="x", alpha=.25)
axes[0].legend(fontsize=8, loc="lower right"); fig.suptitle("경로별(F1~F5) 팬충성도·파급효과 분해 — 라이브 해석 계층 (BTS·임영웅·리센느 + 합산 상위 17)", fontsize=12); fig.tight_layout(); fig.savefig(OUT / "fig06_factor_specific_impact.png"); plt.close(fig)

# fig07a: K→F 배정표
fig, ax = plt.subplots(figsize=(12, 5.4), dpi=250); ax.axis("off")
rows = [[k["topic"], k["topic_name"], k["top10"].replace(" ", ", "), k["F"] + " " + k["F_name"]] for k in k2f]
tb = ax.table(cellText=rows, colLabels=["토픽", "이름", "상위 10단어", "F (파급경로)"], loc="center", cellLoc="left", colWidths=[.06, .27, .47, .2]); tb.auto_set_font_size(False); tb.set_fontsize(8.5); tb.scale(1, 1.7)
for (r, c), cell in tb.get_celld().items():
    if r == 0: cell.set_facecolor("#e8eef3"); cell.set_text_props(weight="bold")
    elif c == 3: cell.set_facecolor({"F1": "#e6f0e3", "F2": "#fbf1d6", "F3": "#f5ded3", "F4": "#dbe8ee", "F5": "#e8e1f1"}[rows[r - 1][3][:2]])
ax.set_title("라이브 K=8 토픽 → F 배정 (M=5, 실루엣 0.046; 시드 10개 중앙값 0.102, 최빈 M=5)", fontsize=11); fig.tight_layout(); fig.savefig(OUT / "fig07a_persona_k_to_f.png"); plt.close(fig)

# fig07b: PCA
X = np.array([[sum(t["share"] for t in f["top2_factors"] if t["f_code"] == fc) or 0 for fc in FC] for f in fs])  # placeholder; replace by full share below
shares = np.array([[f["factor_specific_loyalty"][fc] / f["loyalty_score"] if f["loyalty_score"] else 0 for fc in FC] for f in fs])
# loyalty_score가 0인 팬덤은 spillover 분해에서 복원
for i, f in enumerate(fs):
    if not f["loyalty_score"]: shares[i] = [f["factor_specific_spillover"][fc] / f["spillover_score"] for fc in FC]
pca = PCA(n_components=2).fit(shares - shares.mean(0)); pc = pca.transform(shares - shares.mean(0)); vr = pca.explained_variance_ratio_
fig, ax = plt.subplots(figsize=(9.6, 7.2), dpi=250)
for per, col in COL.items():
    idx = [i for i, f in enumerate(fs) if f["persona"] == per]; ax.scatter(pc[idx, 0], pc[idx, 1], s=46, c=col, alpha=.85, edgecolors="white", linewidths=.5, label=f"{per} ({len(idx)})")
for i, fc in enumerate(FC):
    ax.annotate("", xy=(pca.components_[0, i] * .6, pca.components_[1, i] * .6), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="#333", lw=1.2)); ax.text(pca.components_[0, i] * .66, pca.components_[1, i] * .66, FN[fc], fontsize=9, color="#333")
ax.set_xlabel(f"PC1 ({vr[0]:.1%})"); ax.set_ylabel(f"PC2 ({vr[1]:.1%})"); ax.set_title("Persona decision space — 팬덤별 F1~F5 비중의 PCA (라이브 해석 계층)", fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(OUT / "fig07b_persona_pca.png"); plt.close(fig)
json.dump({"pca_var_ratio": [round(float(v), 4) for v in vr], "loadings": {fc: [round(float(pca.components_[0, i]), 4), round(float(pca.components_[1, i]), 4)] for i, fc in enumerate(FC)}}, open(L / "live_pca_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("figs written; PCA var", [round(float(v), 3) for v in vr], "persona", cnt)
