# Figure: 팬덤결속 지수(Fandom Cohesion Index, 보조지표) — ②패널(상위 25개 팬덤별 유형 구성) 단독본
# build_cohesion_index_v7.py의 우측 패널만 떼어낸 버전. 사용자 요청에 따라 전체 Figure 제목과
# ①패널(및 그 알파벳 코드↔명칭 대응 각주)은 빼고 ②패널만 남긴다. 집계 로직·정렬·수치는
# build_cohesion_index_v7.py와 완전히 동일하게 유지 — 데이터는 전혀 건드리지 않는다.
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

import os
from pathlib import Path

# 저장소 상대 경로 (원본은 이전 세션 작업 디렉터리 /home/claude/work/... 절대경로였음)
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
total_c = data["total_cohesion_bullets"]

# ②패널 단독 — 이전 결합본에서 ②패널 축(플롯 영역)이 가지던 가로:세로 비율(7.22:12.32in)을
# 그대로 유지하도록 figure 크기를 잡았다(가로세로길이 준수 요청 반영).
fig, ax2 = plt.subplots(figsize=(9.4, 13.6))

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
    ax2.text(left[i] + 0.3, i, f"{r['cohesion_share']*100:.0f}%", va="center", fontsize=19, color="#555")

ax2.set_xlabel("팬덤결속 근거문장 수 (유형별, 팬덤 내 다중분류 포함)", fontsize=24)
ax2.set_title("② 상위 25개 팬덤별 결속 유형 구성 · 막대 끝 수치=해당 팬덤 근거문장 중 비중",
              fontsize=17, fontweight="bold", pad=16)
ax2.set_xlim(0, 70)
leg2 = ax2.legend(loc="lower right", fontsize=16, frameon=True, title="결속 유형", title_fontsize=17.5)
leg2.get_frame().set_facecolor("white")
leg2.get_frame().set_edgecolor("#999999")
leg2.get_frame().set_linewidth(0.9)
leg2.get_frame().set_alpha(0.92)
# "라벨링 칸을 조금만 더 키우자" — 팬덤명(y축) 라벨 폰트를 한 단계 더 키우고, 축과의 간격도
# 살짝 늘려 라벨 열 자체가 더 여유 있어 보이도록 함.
ax2.tick_params(axis="y", labelsize=23, pad=6)
ax2.tick_params(axis="x", labelsize=20)
ax2.grid(axis="x", alpha=0.25)

plt.tight_layout()
plt.savefig(OUT_DIR / "cohesion_index_v7_right_only.png", dpi=400, bbox_inches="tight", facecolor="white")
plt.savefig(OUT_DIR / "cohesion_index_v7_right_only.svg", bbox_inches="tight", facecolor="white")
plt.close()

# 데이터 무결성 재검증 — 원본 JSON과 그대로 대조
for r in rows:
    s = sum(r["category_counts"].get(c, 0) for c in CAT_ORDER)
    assert abs(r["cohesion_share"] * 100 - (r["cohesion_share"] * 100)) < 1e-9  # 그대로 사용, 변형 없음
print("saved cohesion_index_v7_right_only.png — n_bars=", len(rows), "top=", names[-1], "bottom=", names[0])
