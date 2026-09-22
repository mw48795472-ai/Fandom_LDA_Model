# Figure: 팬덤100 LDA 파이프라인 — 근거 코퍼스 규모 vs. Meta-Factor 실루엣 계수 타임라인
# (v4 종료 ~ v7 r66(2차), 이중축)
#
# 입력: data/silhouette_gate_timeline/corpus_silhouette_timeline_v7_66_2ch.csv
#   - 실측 타임라인 데이터. "실측" 행과 "[추정·선형보간]" 행(토크나이저가 일관되게 쓰인
#     구간에서만 양 끝 실측값을 선형보간한 것) 두 종류가 라운드 컬럼 문자열로 구분되어 있다.
#   - v7 38~39라운드 사이(토크나이저 개편) 등 방법론이 바뀐 지점은 보간 자체가 불가능하므로,
#     실측점만 점선으로 잇는다(중간값을 추정하지 않는다).
#
# 이 스크립트는 "실루엣 게이트" 거버넌스 정책(SILHOUETTE_GATE_POLICY.md 참고 — 새
# K→M 재군집화 결과가 동결 기준선(v7-40 스냅샷, silhouette=0.267)을 넘지 못하면 해석
# 계층에 반영하지 않고 자동 기각)을 시각적으로 보여주기 위해, 코퍼스가
# 1,781건→9,680건(+443%, 최종 10,020건)으로 계속 성장하는데도 게이트 정책 구간(v7 46~66 2차,
# 실측 20회 연속 기각)의 실루엣은 기준선에 전혀 접근하지 못하고 등락만 반복함(상관계수
# r≈+0.15, 코퍼스 크기와 사실상 무관)을 대비시킨다.
import json
import csv as csv_module
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# 저장소 상대 경로
BASE = Path(__file__).resolve().parents[2]
OUT_DIR = BASE / "output" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _find_korean_font():
    candidates = [os.environ.get("KFONT_PATH", ""), str(BASE / "fonts" / "NotoSansCJKkr-Regular.otf"),
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                  "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                  "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]
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
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["axes.unicode_minus"] = False

# 입력: 사용자가 업로드한 실측 타임라인 CSV. 저장소에는 r66(2차)까지 확장된 판이 있다.
CSV_PATH = BASE / "data" / "silhouette_gate_timeline" / "corpus_silhouette_timeline_v7_66_2ch.csv"
BASELINE_SILHOUETTE = 0.267
GATE_START = 46

df = pd.read_csv(CSV_PATH)
df["is_estimate"] = df["라운드"].astype(str).str.contains(r"\[추정")
df["라운드_clean"] = df["라운드"].astype(str).str.replace(r"\s*\[추정.*\]", "", regex=True)

real = df[~df["is_estimate"]].sort_values("순서").reset_index(drop=True)
interp = df[df["is_estimate"]].sort_values("순서").reset_index(drop=True)
# 게이트 구간 끝은 CSV의 마지막 실측 라운드(현재 r66(2차)=66.5)로 자동 결정
GATE_END = float(real.dropna(subset=["실루엣"])["순서"].max())
LAST_ROW = real.dropna(subset=["실루엣"]).sort_values("순서").iloc[-1]

# ---------------------------------------------------------------------------
# 무결성 재검증 — 이 스크립트가 그리는 값이 업로드된 CSV·이 프로젝트의 다른 실측 자료와
# 일치하는지 그리기 전에 먼저 확인하고, 결과를 콘솔에 출력한다(다른 지수 스크립트들과 동일한
# "결과를 눈으로 믿지 않고 프로그램이 재대조" 원칙).
gate_rows = real[(real["순서"] >= GATE_START) & (real["순서"] <= GATE_END)].dropna(subset=["실루엣"])
gate_corr = float(np.corrcoef(gate_rows["코퍼스(불릿수)"], gate_rows["실루엣"])[0, 1])
v4_end = real.loc[real["순서"] == -4, "코퍼스(불릿수)"].iloc[0]
r61_val = real.loc[real["라운드_clean"].str.contains("r61"), "코퍼스(불릿수)"].iloc[0]
last_val = LAST_ROW["코퍼스(불릿수)"]
growth_pct = (last_val / v4_end - 1) * 100
gate_61 = real[(real["순서"] >= GATE_START) & (real["순서"] <= 61)].dropna(subset=["실루엣"])
r39_40 = real[real["순서"].isin([39, 40])]

print(f"[검증] 게이트 구간(v7 {GATE_START}~{GATE_END:g}) 실측 라운드 수: {len(gate_rows)}건, 전부 기준선 미달: {(gate_rows['실루엣'] < BASELINE_SILHOUETTE).all()}")
print(f"[검증] 부분 구간(v7 46~61) 실측 {len(gate_61)}건, 상관 r={np.corrcoef(gate_61['코퍼스(불릿수)'], gate_61['실루엣'])[0, 1]:.4f}")
print(f"[검증] 게이트 구간 전체({GATE_START}~{GATE_END:g}) 코퍼스-실루엣 상관계수 r={gate_corr:.4f}")
print(f"[검증] 코퍼스 성장: {int(v4_end)}건 -> r61 {int(r61_val)}건  -> 마지막 실측 {LAST_ROW['라운드_clean']} {int(last_val)}건 (+{growth_pct:.0f}%)")
print(f"[검증] v7 39~40라운드(동결 기준선) 실루엣={r39_40['실루엣'].unique().tolist()}, "
      f"K={r39_40['K'].unique().tolist()}, M={r39_40['M'].unique().tolist()} (기준: 0.267/K=10/M=5)")

# ---------------------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(16, 8))
ax2 = ax1.twinx()

# 배경 음영 — 세 구간을 구분한다.
ax1.axvspan(-4.5, 24.5, color="#e8b98a", alpha=0.18, hatch="//", zorder=0)   # 선형보간 가능(v5~r27 계열)
ax1.axvspan(24.5, 45.5, color="#9aa5b1", alpha=0.15, zorder=0)              # 토크나이저 개편 전후 혼재 구간
ax1.axvspan(45.5, GATE_END + 0.5, color="#6f9bd1", alpha=0.16, zorder=0)              # 실루엣 게이트 정책 적용 구간

# 코퍼스 규모(좌축, 실선) — 실측만 존재(코퍼스 크기는 추정치가 없다).
ax1.plot(real["순서"], real["코퍼스(불릿수)"], color="#1f5fa8", lw=2.2,
          marker="o", ms=3.2, label="근거 코퍼스 규모(불릿 수)", zorder=3)

# 실루엣(우축) — 실측치는 실선+다이아몬드, 구간 내에서만 서로 연결한다.
SEGMENT_BREAKS = {27, 41, 46}  # 이 순서 이전 실측점과는 잇지 않음(방법론 단절 지점)
meas = real.dropna(subset=["실루엣"]).sort_values("순서")
seg_start = 0
prev_order = None
for idx in range(len(meas)):
    order = meas["순서"].iloc[idx]
    if prev_order is not None and order in SEGMENT_BREAKS:
        seg = meas.iloc[seg_start:idx]
        ax2.plot(seg["순서"], seg["실루엣"], color="#c1440e", lw=2.0, marker="D", ms=6,
                  zorder=4, label="_nolegend_")
        seg_start = idx
    prev_order = order
seg = meas.iloc[seg_start:]
ax2.plot(seg["순서"], seg["실루엣"], color="#c1440e", lw=2.0, marker="D", ms=6,
          zorder=4, label="Meta-Factor 실루엣(실측)")

# 선형보간 추정치(우축, 옅은 점선 + 빈 원) — 구 토크나이저 일관 구간만.
for _, grp in interp.groupby((interp["순서"].diff() > 2).cumsum()):
    ax2.plot(grp["순서"], grp["실루엣"], color="#d99a5b", lw=1.3, ls="--",
              marker="o", ms=4, mfc="white", zorder=2, label="_nolegend_")
ax2.plot([], [], color="#d99a5b", lw=1.3, ls="--", marker="o", ms=4, mfc="white",
          label="선형보간 추정치(구 토크나이저 일관 구간만)")

# 기준선
ax2.axhline(BASELINE_SILHOUETTE, color="#7a1f1f", lw=1.4, ls="--", zorder=1)
ax2.text(real["순서"].max() + 0.5, BASELINE_SILHOUETTE, f"기준선 {BASELINE_SILHOUETTE}",
          color="#7a1f1f", fontsize=10, va="center")

# 핵심 라운드 주석
def annotate(order, label, dy=0, axis="corpus"):
    row = real[real["순서"] == order].iloc[0]
    if axis == "corpus":
        ax1.annotate(label, (order, row["코퍼스(불릿수)"]), textcoords="offset points",
                      xytext=(0, 10 + dy), ha="center", fontsize=9, color="#1f5fa8")
    else:
        ax2.annotate(label, (order, row["실루엣"]), textcoords="offset points",
                      xytext=(0, 10 + dy), ha="center", fontsize=9, color="#c1440e")

annotate(-4, "v4 종료\n1,781건")
annotate(39, "7,350건", axis="corpus")
ax1.annotate(f"{int(last_val):,}건", (LAST_ROW["순서"], last_val), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9, color="#1f5fa8")
ax2.annotate("v7 40(기준선)", (40, 0.267), textcoords="offset points", xytext=(0, 12),
              ha="center", fontsize=9, color="#7a1f1f", fontweight="bold")
annotate(46, "r46", axis="silhouette")
ax2.annotate(LAST_ROW["라운드_clean"].split("(")[0], (LAST_ROW["순서"], LAST_ROW["실루엣"]), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=9, color="#c1440e")

ax1.set_xlabel(f"라운드 진행 순서 (v4 종료 -> v5 -> v6 -> v7 r1~{LAST_ROW['라운드_clean'].split('(')[0]})", fontsize=11)
ax1.set_ylabel("근거 코퍼스 규모 (불릿 수)", fontsize=11, color="#1f5fa8")
ax2.set_ylabel("Meta-Factor 실루엣 계수 (K/M 재작합 시점만)", fontsize=11, color="#c1440e")
ax1.set_ylim(0, 10000)
ax2.set_ylim(0, 0.30)
ax1.tick_params(axis="y", labelcolor="#1f5fa8")
ax2.tick_params(axis="y", labelcolor="#c1440e")
ax1.grid(alpha=0.2)

region_patches = [
    mpatches.Patch(facecolor="#e8b98a", alpha=0.35, hatch="//", label="선형보간 가능 구간(구 토크나이저 일관)"),
    mpatches.Patch(facecolor="#9aa5b1", alpha=0.3, label="보간 불가 구간(토크나이저 개편 전후)"),
    mpatches.Patch(facecolor="#6f9bd1", alpha=0.35, label=f'"실루엣 게이트" 정책 적용 구간(v7 {GATE_START}~{GATE_END:g}, 실측 {len(gate_rows)}회 연속 기각)'),
]
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2 + region_patches, l1 + l2 + [p.get_label() for p in region_patches],
            loc="upper left", fontsize=9.5, framealpha=0.92)

fig.suptitle(
    f"팬덤100 LDA 파이프라인 — 근거 코퍼스 규모 vs. Meta-Factor 실루엣 계수 (v4 종료~v7 {LAST_ROW['라운드_clean'].split('(')[0]}, 이중축)",
    fontsize=15, fontweight="bold", y=0.985,
)
ax1.set_title(
    f"코퍼스는 {int(v4_end):,}건→{int(last_val):,}건(+{growth_pct:.0f}%)으로 꾸준히 성장했지만, "
    f"실루엣은 게이트 정책 구간(r{GATE_START}~{GATE_END:g})에서\n"
    f"{gate_rows['실루엣'].min():.3f}~{gate_rows['실루엣'].max():.3f} 사이를 등락할 뿐 뚜렷한 추세 없이 "
    f"기준선({BASELINE_SILHOUETTE})에 못 미침 — 코퍼스 크기와 실루엣의 상관계수 r≈{gate_corr:.2f}",
    fontsize=10.5, color="#333", pad=10,
)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(OUT_DIR / "silhouette_gate_timeline_v7.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.savefig(OUT_DIR / "silhouette_gate_timeline_v7.svg", bbox_inches="tight", facecolor="white")
plt.close()
print("saved silhouette_gate_timeline_v7.png")
