# Figure: 팬덤결속 지수(Fandom Cohesion Index, 보조지표) — v7 45라운드(2차, 후속) 신설
# ad_commercial_index_v7.py(v7 39)의 차트 쌍(업종 순위 + 팬덤별 구성)과 동일한 패턴을 그대로
# 복제한다 — LDA 토픽/K→M→F 재군집화와 무관한 원문 키워드 매칭 보조지표이므로, 시각화 방식도
# 기존 "광고·상업성 지수" 차트 쌍(3.9절)과 나란히 비교할 수 있도록 일부러 동일하게 맞췄다.
# ① 좌: 5개 결속 활동 유형(A~E)별 근거문장 순위  ② 우: 상위 25개 팬덤별 유형 구성(누적 막대)
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

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

# 입력: 팬덤결속 지수 v7 JSON — 최종 라이브 코퍼스(10,020건) 기준 산출물. 아직 저장소에 없으면
# data/v7_final/ 에 넣어 실행한다.
with open(DATA_DIR / "fandom_cohesion_index_v7.json", encoding="utf-8") as f:
    data = json.load(f)

CAT_ORDER = ["A_공식팬클럽·회원제", "B_팬카페·온라인커뮤니티", "C_팬덤정체성·문화",
             "D_기부·후원캠페인(팬덤주도)", "E_오프라인결집·이벤트"]
CAT_SHORT = {
    "A_공식팬클럽·회원제": "A. 공식 팬클럽·회원제",
    "B_팬카페·온라인커뮤니티": "B. 팬카페·온라인 커뮤니티",
    "C_팬덤정체성·문화": "C. 팬덤 정체성·문화",
    "D_기부·후원캠페인(팬덤주도)": "D. 기부·후원 캠페인(팬덤 주도)",
    "E_오프라인결집·이벤트": "E. 오프라인 결집·이벤트",
}
CAT_COLOR = {
    "A_공식팬클럽·회원제": "#2a78d6",
    "B_팬카페·온라인커뮤니티": "#4fb3a9",
    "C_팬덤정체성·문화": "#8e6fc2",
    "D_기부·후원캠페인(팬덤주도)": "#e0863f",
    "E_오프라인결집·이벤트": "#c0392b",
}
HIGHLIGHT = {"BTS", "임영웅", "리센느(RESCENE)"}

# 우측 패널(25개 팬덤) 라벨을 2배로 키우면서 25줄이 겹치지 않도록 전체 높이를 함께 늘렸다
# (라벨 폰트만 키우고 세로 폭을 그대로 두면 줄 간격이 부족해 글자가 겹친다).
fig = plt.figure(figsize=(17, 16))
gs = fig.add_gridspec(1, 2, width_ratios=[0.85, 1.45], wspace=0.3)

# ① 좌: 카테고리별 순위 ------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
totals = data["category_totals"]
items = sorted(((c, totals.get(c, 0)) for c in CAT_ORDER), key=lambda kv: -kv[1])
labels = [CAT_SHORT[c] for c, _ in items]
vals = [v for _, v in items]
colors = [CAT_COLOR[c] for c, _ in items]
y = np.arange(len(labels))[::-1]
ax1.barh(y, vals, color=colors, edgecolor="white", linewidth=0.5)
ax1.set_yticks(y)
# 긴 전체 명칭 대신 알파벳 코드만 축에 딱 붙여 표시 — 전체 명칭은 ②패널 범례에 이미 있으므로
# 중복 없이 라벨 열 폭을 최소화하고, 그만큼 확보된 공간을 막대 영역에 돌려준다.
short_codes = [c.split("_")[0] for c, _ in items]
ax1.set_yticklabels(short_codes, fontsize=17, fontweight="bold")
for tick, color in zip(ax1.get_yticklabels(), colors):
    tick.set_color(color)
ax1.tick_params(axis="y", pad=4, length=0)
total_c = data["total_cohesion_bullets"]
for yi, v in zip(y, vals):
    share = v / total_c * 100 if total_c else 0
    ax1.text(v + max(vals) * 0.015, yi, f"{v}건 ({share:.1f}%)", va="center", fontsize=10.5, color="#333")
ax1.set_xlabel("팬덤결속 근거문장 수 (유형별, 멀티라벨 포함)", fontsize=11)
ax1.set_title("① 결속 활동 유형별 근거문장 순위", fontsize=14, fontweight="bold", pad=14)
ax1.tick_params(axis="x", labelsize=10.5)
ax1.grid(axis="x", alpha=0.25)
ax1.set_xlim(0, max(vals) * 1.25)

# 알파벳 코드 ↔ 전체 명칭 대응표를 막대 아래 여백에 작은 범례로 추가 — 축 라벨을 줄인 만큼
# 정보 손실 없이 전체 명칭을 함께 제공한다.
legend_lines = "   ".join(f"{c.split('_')[0]}={CAT_SHORT[c].split('. ',1)[1]}" for c, _ in items)
ax1.text(0.0, -0.145, legend_lines, transform=ax1.transAxes, fontsize=8.3, color="#444",
          ha="left", va="top")

# ② 우: 상위 25개 팬덤별 유형 구성 --------------------------------------------
ax2 = fig.add_subplot(gs[0, 1])
rows = [r for r in data["fandoms"] if r["n_cohesion_bullets"] > 0]
rows = sorted(rows, key=lambda r: -r["n_cohesion_bullets"])[:25]
rows = rows[::-1]
names = [r["fandom"] for r in rows]

left = np.zeros(len(rows))
for c in CAT_ORDER:
    vals2 = np.array([r["category_counts"].get(c, 0) for r in rows])
    ax2.barh(names, vals2, left=left, color=CAT_COLOR[c], label=CAT_SHORT[c], edgecolor="white", linewidth=0.4)
    left += vals2

for i, n in enumerate(names):
    if n in HIGHLIGHT:
        ax2.get_yticklabels()[i].set_fontweight("bold")
        ax2.get_yticklabels()[i].set_color("#1a1a1a")

for i, r in enumerate(rows):
    ax2.text(left[i] + 0.3, i, f"{r['cohesion_share']*100:.0f}%", va="center", fontsize=17, color="#555")

ax2.set_xlabel("팬덤결속 근거문장 수 (유형별, 팬덤 내 다중분류 포함)", fontsize=22)
# 패널 제목은 축 라벨이 아니라 캡션이라 2배까지 키우면 ①패널 제목과 겹친다 — 적당히만 키움.
ax2.set_title("② 상위 25개 팬덤별 결속 유형 구성 · 막대 끝 수치=해당 팬덤 근거문장 중 비중",
              fontsize=16, fontweight="bold", pad=16)
# 범례 글자도 키우되, 2배 그대로 적용하면 박스가 커져 아래쪽 막대(볼빨간사춘기·최예나·QWER 등)의
# 수치 라벨을 가려 데이터가 안 보이게 된다 — 오른쪽 여백(xlim)을 넉넉히 넓혀 겹치지 않게 확보.
ax2.set_xlim(0, 60)
leg2 = ax2.legend(loc="lower right", fontsize=14.5, frameon=True, title="결속 유형", title_fontsize=15.5)
leg2.get_frame().set_facecolor("white")
leg2.get_frame().set_edgecolor("#999999")
leg2.get_frame().set_linewidth(0.9)
leg2.get_frame().set_alpha(0.92)
ax2.tick_params(axis="both", labelsize=20)
ax2.grid(axis="x", alpha=0.25)

fig.suptitle(
    "Figure. 팬덤결속 지수(Fandom Cohesion Index, 보조지표)\n"
    f"(전체 {data['total_bullets']:,}문장 중 {total_c}건={data['corpus_cohesion_share']*100:.1f}%가 팬덤결속 신호 포함, "
    f"{data['n_fandoms_with_any_cohesion_bullet']}/100개 팬덤에서 1건 이상 등장)",
    fontsize=15.5, fontweight="bold", y=0.995,
)

# v7 78라운드: 사용자 요청으로 각주(방법론 설명 각주 텍스트)를 이미지에서 제거하고(설명은 보고서
# 본문 문단·노트박스에서 이미 다루므로 중복), 제목에서도 라운드 번호 표기를 뺐다 — 이 지수는
# 코퍼스 상태를 그대로 가리키는 상시-라이브 지표라 "v7 45라운드 신설"이라는 문구가 시간이 지나도
# 계속 붙어 있는 것이 부적절하다는 지적을 반영했다.
plt.tight_layout(rect=[0, 0, 1, 0.965])
plt.savefig(OUT_DIR / "cohesion_index_v7_sharp.png", dpi=400, bbox_inches="tight", facecolor="white")
plt.savefig(OUT_DIR / "cohesion_index_v7.svg", bbox_inches="tight", facecolor="white")
plt.close()
print("saved cohesion_index_v7_sharp.png")
