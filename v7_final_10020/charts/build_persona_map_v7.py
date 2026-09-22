# -*- coding: utf-8 -*-
"""Fan Persona Map — 팬충성도 × 파급효과 평면에 100개 팬덤을 페르소나 4유형(상위 2개 F 조합)으로 색칠한 산점도.
동결 스냅샷(v7-40) 점수(data/v7_final/fandom_scores_v6.json)와 페르소나(fan_persona_v7.json)를 읽어 두 판을 만든다.
  output/charts/persona_map_v7.png             BTS·임영웅·리센느 강조 표시 있음(보고서 그림 4와 같은 구성)
  output/charts/persona_map_v7_plain.png       강조 표시 없음
실행: python v7_final_10020/charts/build_persona_map_v7.py
"""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

BASE = Path(__file__).resolve().parents[2]
DATA_DIR = BASE / "data" / "v7_final"
OUT_DIR = BASE / "output" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _find_korean_font():
    candidates = [os.environ.get("KFONT_PATH", ""), str(BASE / "fonts" / "NotoSansCJKkr-Regular.otf"),
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                  "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]
    for c in candidates:
        if c and os.path.exists(c):
            fp = fm.FontProperties(fname=c); fm.fontManager.addfont(c); plt.rcParams["font.family"] = fp.get_name(); return fp
    print("[warn] 한글 폰트를 찾지 못했습니다 — KFONT_PATH 환경변수로 지정하세요."); return None


FONT = _find_korean_font()
plt.rcParams["axes.unicode_minus"] = False

with open(DATA_DIR / "fandom_scores_v6.json", encoding="utf-8") as f:
    scores = {r["fandom"]: r for r in json.load(f)}
with open(DATA_DIR / "fan_persona_v7.json", encoding="utf-8") as f:
    fp = json.load(f)
persona = {r["fandom"]: r["persona"] for r in fp["fandoms"]}
counts = fp["persona_counts"]

STYLE = {"글로벌투어형": ("#1f77b4", "o"), "현장상업형": ("#ff7f0e", "o"), "원정소비형": ("#2ca02c", "o"), "집단동원형": ("#9467bd", "o")}
HIGHLIGHT = ["BTS", "임영웅", "리센느(RESCENE)"]


def draw(highlight: bool, path: Path):
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    for p, (c, mk) in sorted(STYLE.items(), key=lambda kv: -counts.get(kv[0], 0)):
        names = [n for n in scores if persona.get(n) == p]
        ax.scatter([scores[n]["loyalty_score"] for n in names], [scores[n]["spillover_score"] for n in names],
                   s=34, c=c, marker=mk, alpha=0.85, edgecolors="white", linewidths=0.5, label=f"{p} (n={counts.get(p, len(names))})", zorder=3)
    if highlight:
        for n in HIGHLIGHT:
            x, y = scores[n]["loyalty_score"], scores[n]["spillover_score"]
            ax.scatter([x], [y], s=150, facecolors="none", edgecolors="black", linewidths=1.6, zorder=4)
            ax.annotate(n, (x, y), textcoords="offset points", xytext=(8, 6), fontsize=10, fontproperties=FONT, zorder=5)
    ax.set_xlim(-0.04, 1.06); ax.set_ylim(-0.04, 1.06)
    ax.set_xlabel("Loyalty Score (팬충성도)", fontsize=12, fontproperties=FONT)
    ax.set_ylabel("Spillover Score (파급효과)", fontsize=12, fontproperties=FONT)
    title = "Fan Persona Map — Top-2 Factor 조합 기반 팬덤 유형 분류"
    if highlight:
        title += "\n(원 표시: BTS·임영웅·리센느)"
    ax.set_title(title, fontsize=13, fontproperties=FONT)
    ax.grid(True, color="#e6e6e6", linewidth=0.8, zorder=0)
    ax.legend(loc="upper right", fontsize=10, prop=FONT, frameon=True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    plt.tight_layout(); plt.savefig(path, facecolor="white"); plt.close(fig)
    print("saved", path.relative_to(BASE))


print(f"[verify] 팬덤 {len(scores)}개, 페르소나 분포 {counts}")
draw(True, OUT_DIR / "persona_map_v7.png")
draw(False, OUT_DIR / "persona_map_v7_plain.png")
