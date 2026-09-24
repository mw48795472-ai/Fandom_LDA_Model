# -*- coding: utf-8 -*-
# persona_decision_space_v7.ipynb 와 같은 내용의 Spyder 셀 스크립트. 저장소 안 어느 폴더에서 실행해도 된다.
# Spyder: F5(전체 실행) 또는 Ctrl+Enter(현재 셀). 그림은 Plots 창, 표는 IPython 콘솔에 나온다.
try:
    display
except NameError:
    display = print

# %% [markdown]
# # Persona 결정공간 — `Persona_결정공간.html`에 설정된 로직의 파이썬 재현
#
# 저장소 루트의 `Persona_결정공간.html`은 동결 스냅샷(v7-40, 7,350건, K=10 → M=5, silhouette 0.267)을 바탕으로 세 가지를 보여 주는
# 자기완결형 페이지다. 이 노트북은 그 페이지의 JS가 하는 계산을 파이썬으로 하나씩 다시 하고, 페이지에 내장된 데이터
# (`data/v7_final/persona_decision_space_v7.json`, HTML의 `const DATA`를 그대로 추출한 것)와 대조한다.
#
# | 절 | HTML 구획 | 로직 | 대조 대상 |
# |---|---|---|---|
# | 1 | 덴드로그램 범례 | K=10 토픽 → 메타팩터 → F1∼F5 경로 코드 배정 | `topic_f_codes` 10/10 |
# | 2 | ① 덴드로그램 | 토픽 간 코사인 거리 average-linkage 병합 트리, M=5 절단선, 가지 색 규칙(`colorForNode`) | `merges`·`leaf_order`·`cut_height` |
# | 3 | ② PCA 산점도의 점 색 | 팬덤별 F1∼F5 비중 → 상위 2개 F코드 → 10개 조합표 → 페르소나 4유형 | `persona` 100/100, 43/31/17/9 |
# | 4 | ② PCA 산점도 | 100×5 비중 행렬의 PCA(2성분), 설명분산, F1∼F5 loading 화살표 | `pc1`·`pc2`·`var_ratio`·`loadings` |
# | 5 | ③ 상세 레이더 패널 | 선택 팬덤의 F 비중 5각형 + 100개 팬덤 평균 5각형(`AVG_SHARES`), `RADAR_MAX` 스케일 | HTML 상수 |
# | 6 | 툴팁·필터 | Factor-specific Loyalty/Spillover = 비중 × 점수, 페르소나 필터·검색·고정 | `fan_persona_v7.json` 500/500 |
# | 7 | 저장 | 팬덤별 결과 CSV | — |
#
# 실행 위치는 저장소 안 어디든 된다(`data/v7_final/fandoms_v3_100.json`이 있는 상위 폴더를 루트로 잡는다).

# %%
import json, re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.cluster.hierarchy import dendrogram, fcluster
from sklearn.decomposition import PCA

pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 60)


def find_repo_root():
    starts = [Path.cwd()]
    if "__file__" in globals():
        starts.append(Path(__file__).resolve().parent)
    for start in starts:
        for p in [start, *start.parents]:
            if (p / "data" / "v7_final" / "fandoms_v3_100.json").exists():
                return p
    raise FileNotFoundError("저장소 루트(data/v7_final/fandoms_v3_100.json)를 찾지 못함 — 저장소 안에서 실행하세요")


REPO = find_repo_root()
DATA = REPO / "data" / "v7_final"
HTML = REPO / "Persona_결정공간.html"
OUT_DIR = Path.cwd() if (Path.cwd() / "build_persona_decision_space_notebook.py").exists() else REPO / "v7_final_10020" / "analysis" / "persona_decision_space"

# 한글 폰트(있으면) — 그림 라벨용. 없으면 F코드·K번호 같은 ASCII 라벨만 쓴다.
_font = None
for cand in [REPO / "fonts" / "NotoSansCJKkr-Regular.otf", Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
             Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"), Path("C:/Windows/Fonts/malgun.ttf"),
             Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"), Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")]:
    if cand.exists():
        fm.fontManager.addfont(str(cand)); [fm.fontManager.addfont(str(b)) for b in (REPO / "fonts").glob("NotoSansCJKkr-*.otf")]
        _font = fm.FontProperties(fname=str(cand)); plt.rcParams["font.family"] = _font.get_name(); break
plt.rcParams["axes.unicode_minus"] = False
import warnings; warnings.filterwarnings("ignore", message="Glyph")


def load_json(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


html_data = load_json("persona_decision_space_v7.json")      # HTML의 const DATA 그대로
fan_persona = load_json("fan_persona_v7.json")               # 페르소나 조합표·팬덤별 상위 2 F·factor-specific 값
frozen_scores = {r["fandom"]: r for r in load_json("fandom_scores_v6.json")}   # 동결 스냅샷 점수(팬덤별 factor_share)
frozen_diag = load_json("lda_v6_diagnostics_frozen_v7_40.json")               # K=10 토픽 상위어, topic_to_factor, factor_labels
pathway = load_json("factor_pathway_map_v7.json")["mapping"]                  # 메타팩터 이름 → F코드·경로명
html_src = HTML.read_text(encoding="utf-8") if HTML.exists() else ""

pca_d, dendro_d = html_data["pca"], html_data["dendro"]
print(f"HTML 내장 데이터: K={pca_d['K']}, M={pca_d['M']}, silhouette={pca_d['silhouette']}, 팬덤 {len(pca_d['fandoms'])}개, 병합 {len(dendro_d['merges'])}회")
print("F 경로 코드:", {k: (v["f_code"], v["f_name"], v["f_path"]) for k, v in pathway.items()})

# %% [markdown]
# ## 1. K=10 토픽 → 메타팩터 → F 경로 코드
#
# 동결 진단 파일의 `topic_to_factor`(토픽 번호 → 메타팩터 번호)와 `factor_labels`(메타팩터 이름), 그리고 `factor_pathway_map_v7.json`
# (메타팩터 이름 → F1∼F5 경로 코드)을 이으면 HTML 덴드로그램 잎에 붙은 F코드 배지가 나온다.

# %%
label_to_f = {name: v["f_code"] for name, v in pathway.items()}
rows = []
for t in range(dendro_d["K"]):
    m = frozen_diag["topic_to_factor"][str(t)]
    label = frozen_diag["factor_labels"][str(m)]
    rows.append({"topic": f"K{t}", "HTML 토픽명": dendro_d["topic_names"][t], "메타팩터": label, "F코드(재현)": label_to_f[label],
                 "F코드(HTML)": dendro_d["topic_f_codes"][t], "상위어": ", ".join(frozen_diag["topics_top_words"][str(t)][:6])})
kf = pd.DataFrame(rows)
display(kf)
print(f"[대조] K→F 배정 일치: {(kf['F코드(재현)'] == kf['F코드(HTML)']).sum()}/{len(kf)}")
print("F코드별 토픽 수:", dict(Counter(kf["F코드(재현)"])))

# %% [markdown]
# ## 2. 덴드로그램 — 병합 트리, M=5 절단선, 가지 색 규칙
#
# HTML의 `buildDendro()`는 `merges`(병합 id·좌·우·높이)로 U자 링크를 그리고, `cut_height`에 절단선을 긋고, 각 가지 아래 잎들의
# F코드가 **전부 같으면 그 F 색, 섞이면 중립색**으로 칠한다(`colorForNode`). 여기서는 같은 병합 기록을 scipy linkage 행렬로 옮겨
# 절단선에서 자르면 M=5 군집이 나오고 그 군집이 F코드와 정확히 일치하는지, 절단 높이가 5번째와 6번째 병합 높이의 중점인지,
# 잎 순서가 scipy의 덴드로그램 잎 순서와 같은지 확인한다.
#
# 토픽 간 코사인 거리 행렬 자체는 저장소에 없으므로(LDA φ분포 필요) 병합 높이는 HTML 기록값을 그대로 쓴다.

# %%
K = dendro_d["K"]
merges = sorted(dendro_d["merges"], key=lambda m: m["id"])
# scipy linkage 행렬: 각 행 [left, right, height, 잎 개수], 새 노드 id = K + 행 번호
size = {i: 1 for i in range(K)}
Z = []
for m in merges:
    assert m["id"] == K + len(Z)
    size[m["id"]] = size[m["left"]] + size[m["right"]]
    Z.append([m["left"], m["right"], m["height"], size[m["id"]]])
Z = np.array(Z, dtype=float)

heights = Z[:, 2]
cut_expected = (heights[K - dendro_d["M"] - 1] + heights[K - dendro_d["M"]]) / 2   # M=5 → 5번째·6번째 병합 높이의 중점
print(f"병합 높이(오름차순): {np.round(heights, 4).tolist()}")
print(f"절단선 재현 {cut_expected:.6f} vs HTML cut_height {dendro_d['cut_height']:.6f} → {'일치' if abs(cut_expected - dendro_d['cut_height']) < 1e-9 else '불일치'}")

clusters = fcluster(Z, t=dendro_d["cut_height"], criterion="distance")
cl = pd.DataFrame({"topic": [f"K{i}" for i in range(K)], "cluster": clusters, "F코드": dendro_d["topic_f_codes"]})
print("절단 결과 군집 수:", cl["cluster"].nunique())
display(cl.groupby("cluster").agg(topics=("topic", list), f_codes=("F코드", lambda s: sorted(set(s)))))
one_f = all(cl[cl.cluster == c]["F코드"].nunique() == 1 for c in cl.cluster.unique())
print(f"[대조] 각 군집이 F코드 하나와 대응: {one_f}")

leaf_order_scipy = dendrogram(Z, no_plot=True)["leaves"]
print(f"[대조] 잎 순서 scipy {leaf_order_scipy} vs HTML {dendro_d['leaf_order']} → {'일치' if leaf_order_scipy == dendro_d['leaf_order'] else '불일치(좌우 대칭 차이 가능)'}")

# colorForNode 규칙: 가지 아래 잎들의 F코드가 하나면 그 색, 아니면 중립
leaves_under = {i: {i} for i in range(K)}
for m in merges:
    leaves_under[m["id"]] = leaves_under[m["left"]] | leaves_under[m["right"]]
def color_for_node(node):
    fc = {dendro_d["topic_f_codes"][l] for l in leaves_under[node]}
    return next(iter(fc)) if len(fc) == 1 else "neutral"
branch_colors = {m["id"]: color_for_node(m["id"]) for m in merges}
print("병합 노드별 가지 색:", branch_colors)

# %%
F_HEX = {"F1": "#2a78d6", "F2": "#27ae60", "F3": "#eb6834", "F4": "#9b59b6", "F5": "#c0392b", "neutral": "#9a9a9a"}
fig, ax = plt.subplots(figsize=(11, 4.2))
dn = dendrogram(Z, labels=[f"K{i} {dendro_d['topic_f_codes'][i]}" for i in range(K)], ax=ax, color_threshold=0,
                link_color_func=lambda node: F_HEX[color_for_node(node)], leaf_rotation=40, leaf_font_size=9)
ax.axhline(dendro_d["cut_height"], ls="--", color="#333", lw=1)
ax.text(0.5, dendro_d["cut_height"] + 0.012, f"M={dendro_d['M']} cut (silhouette={dendro_d['silhouette']})", fontsize=9)
ax.set_ylabel("cosine distance"); ax.set_ylim(-0.02, 1.05)
ax.set_title("K=10 topics -> M=5 meta-factors (average linkage), branch color = F code when all leaves share it")
plt.tight_layout(); plt.savefig(OUT_DIR / "persona_dendrogram_py.png", dpi=150); plt.show()

# %% [markdown]
# ## 3. 팬덤별 F 비중 → 상위 2개 F코드 → 페르소나
#
# HTML 산점도의 점 모양·색은 `persona` 필드로 정해진다. 그 값은 동결 스냅샷 점수 파일의 `factor_share`(메타팩터 5개 비중)를 F코드로
# 바꾼 뒤 **비중 상위 2개 F코드 조합**을 10개 사전정의 조합표(`persona_table_definition`)에 대응시켜 얻는다.

# %%
F_ORDER = ["F1", "F2", "F3", "F4", "F5"]
table = fan_persona["persona_table_definition"]          # "F1|F2": "핵심소비형" 등 10개
print("페르소나 조합표:", table)


def shares_of(fandom):
    fs = frozen_scores[fandom]["factor_share"]
    return {label_to_f[label]: round(v, 4) for label, v in fs.items()}


def persona_of(shares):
    top2 = sorted(sorted(shares, key=lambda f: -shares[f])[:2])          # 비중 상위 2개, 코드 순 정렬(F3|F5)
    return table["|".join(top2)], top2


rows = []
for f in pca_d["fandoms"]:
    sh = shares_of(f["name"])
    persona, top2 = persona_of(sh)
    rows.append({"fandom": f["name"], **{k: sh[k] for k in F_ORDER}, "top2": "|".join(top2), "persona(재현)": persona,
                 "persona(HTML)": f["persona"], "shares_match": all(abs(sh[k] - f["shares"][k]) < 1e-9 for k in F_ORDER)})
pr = pd.DataFrame(rows).set_index("fandom")
display(pr.head(10))
print(f"[대조] F 비중 ↔ HTML shares 일치: {int(pr['shares_match'].sum())}/100")
print(f"[대조] 페르소나 ↔ HTML persona 일치: {int((pr['persona(재현)'] == pr['persona(HTML)']).sum())}/100")
fp_map = {r["fandom"]: r["persona"] for r in fan_persona["fandoms"]}
print(f"[대조] 페르소나 ↔ fan_persona_v7.json 일치: {sum(pr.loc[k, 'persona(재현)'] == fp_map[k] for k in pr.index)}/100")
counts = dict(Counter(pr["persona(재현)"]))
print("페르소나 분포:", counts, "| HTML:", pca_d["persona_counts"])
realized = sorted(set(pr["top2"]))
print(f"실현된 조합 {len(realized)}/10: {realized} — 전부 F3(현장경제 경로)를 포함")

# %% [markdown]
# ## 4. PCA 결정공간 — 100×5 비중 행렬의 2성분 주성분분석
#
# HTML은 팬덤별 F1∼F5 비중(합=1)을 중심화한 뒤 PCA 2성분으로 투영한 `pc1`·`pc2`, 성분별 설명분산 `var_ratio`, F코드별 `loadings`
# (화살표)를 내장한다. 같은 행렬로 `sklearn.decomposition.PCA(n_components=2)`를 돌리면 부호(방향)만 다를 수 있으므로,
# HTML 값과 상관 부호를 맞춘 뒤 좌표 차이를 본다.

# %%
X = pr[F_ORDER].to_numpy()
pca = PCA(n_components=2).fit(X)
scores = pca.transform(X)
html_pc = np.array([[f["pc1"], f["pc2"]] for f in pca_d["fandoms"]])
sign = np.sign([np.corrcoef(scores[:, i], html_pc[:, i])[0, 1] for i in range(2)])
scores_aligned = scores * sign
load_aligned = pca.components_.T * sign          # 5×2, 행 = F1..F5
print(f"설명분산 재현 {np.round(pca.explained_variance_ratio_, 4).tolist()} vs HTML {np.round(pca_d['var_ratio'], 4).tolist()}")
print(f"[대조] pc1/pc2 최대 |차이| (부호 정렬 후): {np.abs(scores_aligned - html_pc).max():.2e}")
html_load = np.array([pca_d["loadings"][f] for f in F_ORDER])
print(f"[대조] loadings 최대 |차이|: {np.abs(load_aligned - html_load).max():.2e}")
pr["pc1"], pr["pc2"] = np.round(scores_aligned[:, 0], 5), np.round(scores_aligned[:, 1], 5)
display(pd.DataFrame(load_aligned, index=F_ORDER, columns=["PC1 loading", "PC2 loading"]).round(4))

# %%
P_STYLE = {"글로벌투어형": ("#c0392b", "o"), "현장상업형": ("#eb6834", "^"), "원정소비형": ("#27ae60", "s"), "집단동원형": ("#2a78d6", "D")}
HIGHLIGHT = ["BTS", "임영웅", "리센느(RESCENE)"]
fig, ax = plt.subplots(figsize=(8.5, 6.5))
for persona, (c, mk) in P_STYLE.items():
    sub = pr[pr["persona(재현)"] == persona]
    ax.scatter(sub["pc1"], sub["pc2"], c=c, marker=mk, s=38, alpha=0.85, edgecolor="white", linewidth=0.5, label=f"{persona} (n={len(sub)})")
scale = 0.55 * max(np.abs(scores_aligned).max(axis=0))
for i, f in enumerate(F_ORDER):
    ax.annotate("", xy=(load_aligned[i, 0] * scale, load_aligned[i, 1] * scale), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=F_HEX[f], lw=1.6))
    ax.text(load_aligned[i, 0] * scale * 1.1, load_aligned[i, 1] * scale * 1.1, f, color=F_HEX[f], fontsize=10, fontweight="bold")
for name in HIGHLIGHT:
    if name in pr.index:
        ax.annotate(name if _font else name.split("(")[0], (pr.loc[name, "pc1"], pr.loc[name, "pc2"]), textcoords="offset points", xytext=(6, 6), fontsize=9, fontproperties=_font)
ax.axhline(0, color="#bbb", lw=0.8); ax.axvline(0, color="#bbb", lw=0.8)
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)"); ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
ax.set_title("Persona decision space — PCA of F1~F5 shares (frozen v7-40)")
ax.legend(loc="best", fontsize=9, prop=_font)
plt.tight_layout(); plt.savefig(OUT_DIR / "persona_pca_py.png", dpi=150); plt.show()

# %% [markdown]
# ## 5. 상세 레이더 패널 — 선택 팬덤 5각형 + 평균 5각형
#
# `showDetail(f)`는 F1∼F5 축을 정오각형으로 놓고, 반지름을 `min(1, 비중/RADAR_MAX)`로 스케일링한다. 점선 5각형은 100개 팬덤 평균
# `AVG_SHARES`, 실선 5각형은 선택 팬덤의 비중이다. 아래는 그 값들을 그대로 계산한 것이며, 하이라이트 3개 팬덤을 예시로 그린다.

# %%
m = re.search(r"const RADAR_MAX\s*=\s*([0-9.]+)", html_src)
RADAR_MAX = float(m.group(1)) if m else 0.6
avg_shares = pr[F_ORDER].mean().round(4)
print(f"RADAR_MAX = {RADAR_MAX} (HTML 상수), AVG_SHARES = {avg_shares.to_dict()}")


def radar_points(vals, R=1.0):
    pts = []
    for i, v in enumerate(vals):
        ang = -np.pi / 2 + i * 2 * np.pi / 5
        rr = max(0.0, min(1.0, v / RADAR_MAX)) * R
        pts.append((rr * np.cos(ang), rr * np.sin(ang)))
    return pts


fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), subplot_kw=dict(aspect="equal"))
for ax, name in zip(axes, HIGHLIGHT):
    for frac in (0.25, 0.5, 0.75, 1.0):
        ring = radar_points([frac * RADAR_MAX] * 5); ring.append(ring[0]); ax.plot(*zip(*ring), color="#ddd", lw=0.8)
    for i, f in enumerate(F_ORDER):
        x, y = radar_points([RADAR_MAX] * 5)[i]; ax.plot([0, x], [0, y], color="#ccc", lw=0.8); ax.text(x * 1.15, y * 1.15, f, ha="center", va="center", color=F_HEX[f], fontsize=9)
    avg = radar_points(avg_shares.tolist()); avg.append(avg[0]); ax.plot(*zip(*avg), ls="--", color="#777", lw=1.2, label="avg (100)")
    val = radar_points(pr.loc[name, F_ORDER].tolist()); val.append(val[0]); ax.fill(*zip(*val), color="#1f3864", alpha=0.18); ax.plot(*zip(*val), color="#1f3864", lw=1.6)
    ax.set_title(f"{name} — {pr.loc[name, 'persona(재현)']}", fontproperties=_font, fontsize=10); ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.3, 1.3); ax.axis("off")
axes[0].legend(loc="lower left", fontsize=8)
plt.tight_layout(); plt.savefig(OUT_DIR / "persona_radar_py.png", dpi=150); plt.show()
display(pd.DataFrame({name: pr.loc[name, F_ORDER] for name in HIGHLIGHT}).assign(평균=avg_shares).round(3))

# %% [markdown]
# ## 6. 툴팁·필터 로직 — Factor-specific Loyalty/Spillover와 상호작용
#
# `fan_persona_v7.json`의 `factor_specific_loyalty`/`factor_specific_spillover`는 **F 비중 × 팬덤 점수**(동결 loyalty/spillover)로,
# 페이지의 툴팁이 보여 주는 값이다. 상호작용은 데이터가 아니라 상태 변수로 처리된다.
#
# - `activePersonas`(Set): 범례 칩 클릭으로 페르소나를 넣고 빼며, `applyFilter()`가 빠진 페르소나의 점을 흐리게 한다.
# - `#search` 입력: 팬덤명 부분 일치가 아닌 점을 같은 방식으로 흐리게 한다.
# - `pinnedName`: 점 클릭 시 상세 패널을 고정하고, 다시 클릭하면 해제한다.

# %%
fp_rows = {r["fandom"]: r for r in fan_persona["fandoms"]}
mism = 0
for name in pr.index:
    sc = frozen_scores[name]; r = fp_rows[name]
    for f in F_ORDER:
        if abs(round(pr.loc[name, f] * sc["loyalty_score"], 4) - r["factor_specific_loyalty"][f]) > 1e-3: mism += 1
        if abs(round(pr.loc[name, f] * sc["spillover_score"], 4) - r["factor_specific_spillover"][f]) > 1e-3: mism += 1
print(f"[대조] Factor-specific Loyalty/Spillover = 비중 × 점수: 불일치 {mism}/1000 셀")
top2_match = sum(1 for name in pr.index if [t["f_code"] for t in fp_rows[name]["top2_factors"]] == sorted(pr.loc[name, "top2"].split("|"), key=lambda f: -pr.loc[name, f]))
print(f"[대조] 상위 2 F코드(비중 내림차순) ↔ fan_persona top2_factors: {top2_match}/100")


def apply_filter(active_personas, query=""):
    """HTML applyFilter()의 파이썬 판: 보이는(강조되는) 팬덤 목록을 돌려준다."""
    vis = pr[pr["persona(재현)"].isin(active_personas)]
    if query:
        vis = vis[vis.index.str.contains(query, case=False, regex=False)]
    return vis.index.tolist()


print("예: 글로벌투어형만 켜고 'BTS' 검색 →", apply_filter({"글로벌투어형"}, "BTS"))
print("예: 집단동원형만 켬 →", apply_filter({"집단동원형"}))

# %% [markdown]
# ## 7. 결과 저장

# %%
out = pr[F_ORDER + ["top2", "persona(재현)", "pc1", "pc2"]].rename(columns={"persona(재현)": "persona"})
out["persona_html"] = pr["persona(HTML)"]
out_csv = OUT_DIR / "persona_decision_space_v7_result.csv"
out.to_csv(out_csv, encoding="utf-8-sig")
print(f"저장: {out_csv.relative_to(REPO)} ({len(out)}행)")
summary = pd.DataFrame([
    {"항목": "K→F 배정", "결과": f"{(kf['F코드(재현)'] == kf['F코드(HTML)']).sum()}/10 일치"},
    {"항목": "덴드로그램 절단선·군집(M=5)", "결과": f"절단 {'일치' if abs(cut_expected - dendro_d['cut_height']) < 1e-9 else '불일치'}, 군집↔F코드 {'일치' if one_f else '불일치'}"},
    {"항목": "F 비중·페르소나", "결과": f"{int(pr['shares_match'].sum())}/100, {int((pr['persona(재현)'] == pr['persona(HTML)']).sum())}/100 일치 ({counts})"},
    {"항목": "PCA 좌표·loading", "결과": f"최대 차이 {np.abs(scores_aligned - html_pc).max():.1e} / {np.abs(load_aligned - html_load).max():.1e}"},
    {"항목": "Factor-specific 값", "결과": f"불일치 {mism}/1000"},
])
display(summary)

# %% [markdown]
# ## 한계
#
# 1. 동결 스냅샷의 **코사인 거리 행렬과 LDA φ분포는 저장소에 없다.** 그래서 2절의 병합 높이는 HTML 기록값을 그대로 쓰며, average-linkage
#    계산 자체를 다시 하지는 않는다. 절단선 위치·군집 구성·잎 순서·가지 색 규칙은 그 기록값에서 완전히 재현된다.
#    같은 방법(같은 토크나이저·벡터라이저·LDA 설정)을 최종 코퍼스 10,020건에 적용해 실제로 산출한 φ·코사인 거리 행렬·병합 트리·M-grid 실루엣은
#    `topic_phi_cosine/`(CSV + `TOPIC_PHI_COSINE_DISTANCE_V7.md`, `build_topic_phi_cosine_v7.py`)에 있다.
# 2. PCA는 부호(축 방향)가 구현마다 달라질 수 있어 HTML 좌표와 상관 부호를 맞춘 뒤 비교했다. 맞춘 뒤 좌표·loading은 수치 오차 범위에서 같다.
# 3. HTML의 `RADAR_MAX`는 페이지 소스에서 읽는다. 저장소 루트에 HTML이 없으면 0.6을 쓴다.

