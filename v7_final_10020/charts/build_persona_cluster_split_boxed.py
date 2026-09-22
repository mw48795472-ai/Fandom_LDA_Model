# 그림 4-2(Fan Persona 군집화 세부 구조)를 좌/우 패널로 분리해 각각 별도 PNG로 생성.
# 원본 build_persona_cluster_structure_v7.py(그림 4-2 통합판)의 계산 로직을 그대로 유지
# (데이터·통계 계산은 전혀 바꾸지 않음), 다음만 변경:
#   - 왼쪽(덴드로그램)·오른쪽(PCA biplot)을 완전히 별도의 figure/PNG로 분리
#   - 전체 제목(fig.suptitle)과 하단 각주(fig.text)를 각각 생략
#   - 패널 자체의 소제목(① ... / ② ...)도 생략 — "그래프만" 요청
#   - 글자 크기를 키워 단독 이미지로도 선명하게 보이도록 조정
#   - (최종본) 하이라이트 3개 팬덤 라벨을 여백으로 이동해 테두리 박스로 표시, 페르소나 범례를
#     아티팩트(persona.html) 공식 팔레트로 교체하고 좌상단 빈 공간에 테두리 박스로 배치
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
from sklearn.decomposition import PCA

import os
from pathlib import Path

# 저장소 상대 경로
BASE = Path(__file__).resolve().parents[2]
DATA_DIR = BASE / "data" / "v7_final"
OUT_DIR = BASE / "output" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _find_korean_font():
    """NotoSansCJKkr 폰트를 환경변수(KFONT_PATH) -> 저장소 fonts/ -> 시스템 경로 순으로 찾는다.
    없으면 matplotlib 기본 폰트로 진행(한글이 깨질 수 있음을 경고)."""
    candidates = [os.environ.get("KFONT_PATH", ""), str(BASE / "fonts" / "NotoSansCJKkr-Regular.otf"),
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    print("[warn] 한글 폰트를 찾지 못했습니다 — KFONT_PATH 환경변수로 NotoSansCJKkr-Regular.otf 경로를 지정하세요.")
    return None

_font = _find_korean_font()
if _font:
    KFONT = fm.FontProperties(fname=_font)
    fm.fontManager.addfont(_font)
    plt.rcParams["font.family"] = KFONT.get_name()
else:
    KFONT = fm.FontProperties()
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["axes.unicode_minus"] = False

# 입력 1: K→M 군집 구조(토픽 코사인거리 행렬 + 팬덤별 F1~F5 비중). 동결 스냅샷 v7-40(7,350건) 기준.
#   원본 factor_clustering_structure_v7.json은 아직 저장소에 없다. 같은 스냅샷의 K=10 토픽 명칭·F코드·
#   덴드로그램 병합 순서·PCA 좌표는 data/v7_final/persona_decision_space_v7.json(Persona_결정공간.html에서
#   추출)에 있으나 코사인거리 행렬 자체는 포함돼 있지 않아 이 스크립트가 바로 쓰지는 못한다.
with open(DATA_DIR / "factor_clustering_structure_v7.json", encoding="utf-8") as f:
    cs = json.load(f)
# 입력 2: 팬덤별 페르소나(동결 스냅샷 기준, 저장소에 있음)
with open(DATA_DIR / "fan_persona_v7.json", encoding="utf-8") as f:
    persona_data = json.load(f)

K, M = cs["K"], cs["M"]
HIGHLIGHT = {"BTS", "임영웅", "리센느(RESCENE)"}

F_COLORS = {"F1": "#2a78d6", "F2": "#27ae60", "F3": "#eb6834", "F4": "#9b59b6", "F5": "#c0392b"}
# persona 아티팩트(persona.html)의 공식 라이트 테마 팔레트(--p-tour/--p-onsite/--p-expedition/--p-mobilize)와
# 값을 맞춤. 기존 스크립트는 원정소비형=#c0392b로 F5(빨강) 화살표와 완전히 동일한 색을 써 구분이 안 됐던 문제가
# 있었는데, 아티팩트 팔레트로 교체하면 4개 페르소나 색이 서로 뚜렷이 구분되고 F1~F5 화살표 색과도 덜 겹친다.
PERSONA_COLORS = {
    "글로벌투어형": "#2a78d6",   # --p-tour
    "현장상업형": "#c85a1f",    # --p-onsite
    "원정소비형": "#1baf7a",    # --p-expedition
    "집단동원형": "#4a3aa7",    # --p-mobilize
}

# 데이터 무결성 검증 (분리 과정에서 값이 바뀌지 않았는지 확인)
print(f"[verify] K={K} M={M} silhouette={cs['silhouette']:.4f} n_fandoms={len(persona_data['fandoms'])}")

# ============================================================
# ① 왼쪽 패널 단독: K→M Meta-Factor 계층적 군집화 덴드로그램
# ============================================================
fig1, ax1 = plt.subplots(figsize=(11.5, 10), dpi=450)

dist = np.array(cs["topic_cosine_distance_matrix"])
np.fill_diagonal(dist, 0.0)
condensed = squareform(dist, checks=False)
Z = linkage(condensed, method="average")

merge_heights = np.sort(Z[:, 2])
cut_height = (merge_heights[K - M - 1] + merge_heights[K - M]) / 2 if M < K else merge_heights[-1] + 1

cluster_labels = fcluster(Z, t=cut_height, criterion="distance")
cluster_to_color = {}
for lab in set(cluster_labels):
    members = [i for i in range(K) if cluster_labels[i] == lab]
    fcs_in_cluster = {cs["topic_f_codes"][i] for i in members}
    color = F_COLORS[next(iter(fcs_in_cluster))] if len(fcs_in_cluster) == 1 else "#9a9a96"
    cluster_to_color[lab] = color

node_leaves = {i: {i} for i in range(K)}
for i, (a, b, _dist, _cnt) in enumerate(Z):
    node_leaves[K + i] = node_leaves[int(a)] | node_leaves[int(b)]

def link_color_func(node_id):
    labs = {cluster_labels[leaf] for leaf in node_leaves[node_id]}
    return cluster_to_color[labs.pop()] if len(labs) == 1 else "#9a9a96"

dendrogram(Z, labels=[""] * K, ax=ax1, link_color_func=link_color_func, color_threshold=0)
ax1.axhline(cut_height, color="#c0392b", linestyle="--", linewidth=1.6)
ax1.text(0.35, cut_height, f"M={M} 절단선 (silhouette={cs['silhouette']:.3f})",
          transform=ax1.get_yaxis_transform(), ha="left", va="bottom", fontsize=14.5, color="#c0392b",
          fontweight="bold")
ax1.set_ylim(-0.28, 1.05)

leaf_order = dendrogram(Z, no_plot=True)["leaves"]
short_names = [n.split("(")[0] for n in cs["topic_names"]]
for pos, leaf_idx in enumerate(leaf_order):
    fc = cs["topic_f_codes"][leaf_idx]
    xpos = ax1.get_xticks()[pos]
    ax1.scatter([xpos], [-0.07], marker="s", s=210,
                color=F_COLORS.get(fc, "#999999"), clip_on=False, zorder=6,
                transform=ax1.get_xaxis_transform())
    ax1.text(xpos, -0.10, f'{cs["topic_ids"][leaf_idx]} {short_names[leaf_idx]}',
              rotation=50, rotation_mode="anchor",
              ha="right", va="top", fontsize=13.5, transform=ax1.get_xaxis_transform())

handles = [plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=c, markersize=14, label=f"{fc}")
           for fc, c in F_COLORS.items()]
ax1.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.34), fontsize=13.5,
           frameon=False, title="배정된 F코드", title_fontsize=14.5, ncol=5)

ax1.set_ylabel("코사인 거리 (topic-word 분포 phi 기준,\n0=완전동일·1=완전무관)", fontsize=14.5)
ax1.set_xlabel(f"K={K}개 LDA 토픽 (Latent Dirichlet Allocation, random_state=0) — 색상 사각형=배정된 F코드",
               fontsize=14, labelpad=180)
ax1.tick_params(axis="y", labelsize=13.5)
ax1.grid(axis="y", alpha=0.2)
# 제목(① K→M ...) 생략 — 요청에 따라 그래프만

fig1.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.40)
fig1.savefig(OUT_DIR / "persona_cluster_left_dendrogram_v7_sharp.png",
             dpi=450, facecolor="white")
plt.close(fig1)
print("saved persona_cluster_left_dendrogram_v7.png")

# ============================================================
# ② 오른쪽 패널 단독: 100개 팬덤 F1~F5 factor share → PCA biplot
# ============================================================
F_ORDER = ["F1", "F2", "F3", "F4", "F5"]
rows = persona_data["fandoms"]
names = [r["fandom"] for r in rows]
personas = {r["fandom"]: r["persona"] for r in rows}
X = np.array([[cs["fandom_factor_share_full"][n][fc] for fc in F_ORDER] for n in names])

pca = PCA(n_components=2, random_state=0)
scores2d = pca.fit_transform(X)
var_ratio = pca.explained_variance_ratio_

fig2, ax2 = plt.subplots(figsize=(12.5, 10), dpi=450)

personas_present = sorted({personas[n] for n in names}, key=lambda p: -persona_data["persona_counts"].get(p, 0))
for p in personas_present:
    idx = [i for i, n in enumerate(names) if personas[n] == p]
    n_cnt = persona_data["persona_counts"].get(p, 0)
    ax2.scatter(scores2d[idx, 0], scores2d[idx, 1], s=75, alpha=0.75,
                color=PERSONA_COLORS.get(p, "#999999"), label=f"{p} (n={n_cnt})",
                edgecolors="white", linewidths=0.6, zorder=3)

# 라벨을 데이터 밀집 영역 밖의 여백(마진)으로 이동시키고 각각 테두리 박스를 둘러 표시.
# 여백을 확보하기 위해 투명(alpha=0) 앵커 포인트를 미리 찍어 axes datalim을 확장한다.
ax2.scatter([0.34, -0.31], [0.24, -0.06], alpha=0, zorder=0)

HIGHLIGHT_BOX_POS = {
    "리센느(RESCENE)": (0.205, 0.205),
    "BTS": (0.255, 0.005),
    "임영웅": (-0.27, 0.07),
}
LABEL_BBOX = dict(boxstyle="round,pad=0.38", facecolor="white", edgecolor="#555555", linewidth=1.1)
for i, n in enumerate(names):
    if n in HIGHLIGHT:
        bx, by = HIGHLIGHT_BOX_POS[n]
        ax2.annotate(n, xy=(scores2d[i, 0], scores2d[i, 1]), xytext=(bx, by), textcoords="data",
                     fontsize=15.5, fontweight="bold", ha="center", va="center", zorder=5,
                     bbox=LABEL_BBOX,
                     arrowprops=dict(arrowstyle="-", color="#555555", lw=0.9, shrinkA=1, shrinkB=9))
        ax2.scatter([scores2d[i, 0]], [scores2d[i, 1]], s=230, facecolors="none",
                    edgecolors="black", linewidths=2.0, zorder=6)

loadings = pca.components_.T
scale = 0.9 * np.abs(scores2d).max() / np.abs(loadings).max()
for i, fc in enumerate(F_ORDER):
    ax2.annotate("", xy=(loadings[i, 0] * scale, loadings[i, 1] * scale), xytext=(0, 0),
                 arrowprops=dict(arrowstyle="-|>", color=F_COLORS[fc], lw=2.6), zorder=4)
    lx, ly = loadings[i, 0] * scale * 1.13, loadings[i, 1] * scale * 1.13
    ax2.text(lx, ly, fc, fontsize=16.5, fontweight="bold", color=F_COLORS[fc],
              ha="center", va="center", zorder=7)

ax2.axhline(0, color="#cccccc", linewidth=0.8, zorder=1)
ax2.axvline(0, color="#cccccc", linewidth=0.8, zorder=1)
ax2.set_xlabel(f"PC1 ({var_ratio[0]*100:.1f}% 분산 설명)", fontsize=15)
ax2.set_ylabel(f"PC2 ({var_ratio[1]*100:.1f}% 분산 설명)", fontsize=15)
# 페르소나 범례는 산점도 좌측 상단의 빈 공간(약 x<=-0.09, y>=0.13 구간에는 점이 없음)에
# 테두리 박스를 두른 채 플롯 내부로 배치 — 더 이상 축 바깥 별도 여백을 차지하지 않는다.
leg = ax2.legend(loc="upper left", bbox_to_anchor=(0.03, 0.97), fontsize=13.5,
                  frameon=True, borderpad=0.7, labelspacing=0.6, handletextpad=0.6)
leg.get_frame().set_facecolor("white")
leg.get_frame().set_edgecolor("#555555")
leg.get_frame().set_linewidth(1.1)
ax2.tick_params(axis="both", labelsize=13.5)
ax2.grid(alpha=0.2)
ax2.set_aspect("equal", adjustable="datalim")
# 제목(② Persona 결정 공간 ...) 생략 — 요청에 따라 그래프만

fig2.subplots_adjust(left=0.08, right=0.97, top=0.97, bottom=0.08)
fig2.savefig(OUT_DIR / "persona_cluster_right_pca_v7_boxed.png",
             dpi=450, facecolor="white", bbox_inches="tight")
plt.close(fig2)
print("saved persona_cluster_right_pca_v7_boxed.png")
