# -*- coding: utf-8 -*-
"""보조지표 7종 — 100개 팬덤 전체(멤버 집중도는 45개 그룹 전체) 그래프.
README 6절의 그림은 상위 20·25개만 보여 주므로, 같은 지표를 전체 대상으로 다시 그려 assets/readme/100개_보조지표/ 에 저장한다.

  aux1_ad_commercial_100.png        광고·상업성 지수 — 20개 업종 전부(업종군별 색 계열) 누적 막대, 끝 라벨 = 광고 문장 수·비중
  aux2_media_exposure_100.png       미디어·콘텐츠 노출 지수 — 예능·유튜브·영화·드라마 누적 막대
  aux3_fandom_cohesion_100.png      팬덤결속 지수 — 결속 유형 A~E 누적 막대
  aux4_media_crossover_100.png      매체 크로스오버 지수 — 서로 다른 뉴스 매체 수
  aux5_domestic_regional_100.png    국내 지역 지수 — 17개 시/도 전부(권역별 색 계열) 누적 막대
  aux6_member_mci_45.png            멤버 집중도(MCI) — 45개 그룹, 구조적 하한 1/멤버수 표시
  aux7_worldwide_language_100.png   세계 언어 지수 — 해외언어 13개 전부 누적 막대

색: 범주형 7색(고정 순서, 명도·색각이상 검증 통과) + '그 외'는 중립 회색. 팬덤 100개는 1~50위 / 51~100위 두 패널로 나누고 x축 범위를 공유한다.
한글 폰트: KFONT_PATH(본문)·KFONT_BOLD_PATH(제목) 환경변수 → 없으면 시스템 후보(Noto Sans KR/CJK, 맑은 고딕, 나눔고딕 등).
실행: python v7_final_10020/charts/build_aux_indices_100_v7.py
"""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parents[2]
D = BASE / "data" / "v7_final"
OUT = BASE / "assets" / "readme" / "100개_보조지표"
OUT.mkdir(parents=True, exist_ok=True)

# ---- 폰트 --------------------------------------------------------------------
def _pick(env, cands):
    for c in [os.environ.get(env, "")] + cands:
        if c and os.path.exists(c):
            fm.fontManager.addfont(c)
            return fm.FontProperties(fname=c)
    return None

REG = _pick("KFONT_PATH", [str(BASE / "fonts" / "NotoSansCJKkr-Regular.otf"), str(BASE / "fonts" / "NotoSansKR-Regular.ttf"), "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                            "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"])
BOLD = _pick("KFONT_BOLD_PATH", [str(BASE / "fonts" / "NotoSansCJKkr-Bold.otf"), str(BASE / "fonts" / "NotoSansKR-Bold.ttf"), "C:/Windows/Fonts/malgunbd.ttf",
                                  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]) or REG
if REG is None:
    print("[warn] 한글 폰트를 찾지 못했습니다 — KFONT_PATH 로 지정하세요.")
else:
    plt.rcParams["font.family"] = REG.get_name()
plt.rcParams["axes.unicode_minus"] = False

# ---- 색·잉크 (reference palette, light) -------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]
SERIES8 = "#e34948"        # 범주형 8번째 슬롯(red)
OTHER = "#b4b2aa"          # '그 외' 묶음 — 의도적 중립 회색
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
DPI = 200
plt.rcParams["hatch.color"] = SURFACE
plt.rcParams["hatch.linewidth"] = 1.4


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def style_axis(ax, xmax):
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, xmax)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(axis="y", length=0, labelsize=10.5, colors=INK2, pad=6)
    ax.tick_params(axis="x", labelsize=9.5, colors=MUTED, length=0, pad=4)


def header(fig, title, subtitle, handles=None, ncol=8):
    fig.text(0.012, 0.992, title, fontsize=19, color=INK, fontproperties=BOLD, va="top")
    fig.text(0.012, 0.968, subtitle, fontsize=11.5, color=INK2, va="top")
    if handles:
        fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 0.952), ncol=ncol, frameon=False,
                   fontsize=11, handlelength=1.2, handleheight=1.0, columnspacing=1.6, labelcolor=INK)


def grouped_legend(fig, groups, top=0.944, row_h=0.0195, gap_in=0.45):
    """그룹 머리글이 열 위에 붙는 범례. groups = [(그룹명, [(색, 항목명), ...]), ...] — 그룹마다 한 열."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W = fig.get_figwidth() * fig.dpi
    x = 0.014
    sw_w, sw_h = 0.0085, row_h * 0.62                # 색 칸 크기(figure 비율)
    for gname, items in groups:
        head = fig.text(x, top, gname, fontsize=11.5, color=INK, fontproperties=BOLD, va="top", ha="left")
        widths = [head.get_window_extent(r).width]
        for j, (c, lab) in enumerate(items):
            y = top - row_h * (j + 1.0) - 0.004
            fig.patches.append(matplotlib.patches.Rectangle((x, y - sw_h * 0.5), sw_w, sw_h, transform=fig.transFigure,
                                                            facecolor=c, edgecolor="none", figure=fig))
            t = fig.text(x + sw_w + 0.005, y, lab, fontsize=11, color=INK, va="center", ha="left")
            widths.append(t.get_window_extent(r).width + (sw_w + 0.005) * W)
        x += max(widths) / W + gap_in / fig.get_figwidth()


def footer(fig, text):
    fig.text(0.012, 0.006, text, fontsize=9.5, color=MUTED, va="bottom")


def stacked_100(rows, keys, colors, labels, end_label, title, subtitle, xlabel, foot, fname, per_panel=50, hatches=None, ncol=None, top=0.905, legend_columns=None, legend_groups=None):
    """rows: [(name, {key: value}, total_for_sort)] 정렬 완료. 두 패널(1~50 / 51~100) 누적 가로 막대."""
    n = len(rows)
    panels = [rows[i:i + per_panel] for i in range(0, n, per_panel)]
    stack_max = max(sum(v.get(k, 0) for k in keys) for _, v, _ in rows)
    xmax = stack_max * 1.22 if stack_max else 1
    fig_h = 0.285 * per_panel + 2.6
    fig, axes = plt.subplots(1, len(panels), figsize=(9.2 * len(panels), fig_h), dpi=DPI, facecolor=SURFACE)
    axes = axes if len(panels) > 1 else [axes]
    for pi, (ax, part) in enumerate(zip(axes, panels)):
        names = [f"{pi * per_panel + i + 1:>3}. {r[0]}" for i, r in enumerate(part)]
        y = list(range(len(part)))[::-1]
        left = [0.0] * len(part)
        hs = hatches or [None] * len(keys)
        for k, c, h in zip(keys, colors, hs):
            vals = [r[1].get(k, 0) for r in part]
            ax.barh(y, vals, left=left, height=0.72, color=c, edgecolor=SURFACE, linewidth=0.7, zorder=2, hatch=h)
            left = [a + b for a, b in zip(left, vals)]
        for yi, r, l in zip(y, part, left):
            ax.text(l + xmax * 0.008, yi, end_label(r), va="center", ha="left", fontsize=9.5, color=INK2, zorder=3)
        ax.set_yticks(y)
        ax.set_yticklabels(names)
        ax.set_ylim(-0.7, per_panel - 0.3)
        style_axis(ax, xmax)
        ax.set_xlabel(xlabel, fontsize=10.5, color=INK2, labelpad=6)
        ax.set_title(f"{pi * per_panel + 1}~{pi * per_panel + len(part)}위", fontsize=12, color=INK2, loc="left", pad=6)
    handles = [Patch(facecolor=c, edgecolor=(SURFACE if h else "none"), hatch=h, label=l)
               for c, l, h in zip(colors, labels, hatches or [None] * len(colors))]
    if legend_columns:   # 열(column)마다 묶을 항목 인덱스 — matplotlib 범례는 열 우선으로 채워지므로 빈 칸으로 높이를 맞춘다
        depth = max(len(col) for col in legend_columns)
        blank = Patch(facecolor="none", edgecolor="none", label=" ")
        handles = [h for col in legend_columns for h in ([handles[i] for i in col] + [blank] * (depth - len(col)))]
        ncol = len(legend_columns)
    if legend_groups:    # [(그룹명, [키 인덱스...]), ...] — 그룹명을 열 머리글로
        header(fig, title, subtitle)
        grouped_legend(fig, [(g, [(colors[i], labels[i]) for i in idx]) for g, idx in legend_groups])
    else:
        header(fig, title, subtitle, handles, ncol=ncol or len(handles))
    footer(fig, foot)
    fig.subplots_adjust(left=0.105, right=0.985, top=top, bottom=0.05, wspace=0.42)
    fig.savefig(OUT / fname, facecolor=SURFACE)
    plt.close(fig)
    print("saved", (OUT / fname).relative_to(BASE))


def top_keys(totals, k=7):
    return [x for x, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:k]]


# ---- 1. 광고·상업성 ------------------------------------------------------------
# 20개 업종 전부를 업종군별 색 계열로 칠한다(같은 업종군 = 같은 색상의 명도 단계, 막대도 업종군 순서로 쌓음).
ad = load(D / "ad_commercial_index_v7.json")
AD_STYLE = [  # (업종군, 업종, 색)
    ("공공·미디어", "복지/행정", "#2a78d6"), ("공공·미디어", "교육", "#7fb2ee"), ("공공·미디어", "뉴스", "#17498a"), ("공공·미디어", "도서/참고자료", "#bcd6f5"),
    ("패션·뷰티", "패션/의류", "#eb6834"), ("패션·뷰티", "미용", "#e34948"),
    ("식품·생활·건강", "식음료", "#1baf7a"), ("식품·생활·건강", "건강/의료", "#008300"), ("식품·생활·건강", "가정/생활", "#8fd9b8"),
    ("IT·게임·엔터", "정보/통신", "#4a3aa7"), ("IT·게임·엔터", "게임", "#9387e0"), ("IT·게임·엔터", "엔터테인먼트", "#2a1f6e"),
    ("금융·산업", "금융", "#eda100"), ("금융·산업", "부동산", "#f6cf6a"), ("금융·산업", "비즈니스/산업", "#b37700"),
    ("여가·모빌리티", "여행", "#e87ba4"), ("여가·모빌리티", "스포츠/레저", "#f5b8cf"), ("여가·모빌리티", "자동차", "#b3406c"),
    ("유통", "쇼핑", "#8f6a3c"),
    ("기타", "기타", OTHER),
]
ad_keys = [k for _, k, _ in AD_STYLE]
assert set(ad_keys) == set(ad["industries"]), "업종 목록이 바뀌면 AD_STYLE을 갱신하세요"
rows = []
for f in ad["fandoms"]:
    ic = f["industry_counts"]
    rows.append((f["fandom"], {k: ic.get(k, 0) for k in ad_keys}, (f["n_ad_bullets"], f["ad_share"])))
rows.sort(key=lambda r: (-r[2][0], -r[2][1], r[0]))
groups = []
for i, (g, _, _) in enumerate(AD_STYLE):
    if not groups or groups[-1][0] != g:
        groups.append((g, []))
    groups[-1][1].append(i)
stacked_100(rows, ad_keys, [c for _, _, c in AD_STYLE],
            ad_keys,
            lambda r: f"{r[2][0]}건 · {r[2][1] * 100:.0f}%",
            "광고·상업성 지수 — 100개 팬덤 전체",
            f"광고신호 문장 {ad['total_ad_bullets']:,}건(전체 {ad['total_bullets']:,}건의 {ad['corpus_ad_share'] * 100:.1f}%) · 광고 문장 수 순 정렬 · 막대 = 업종별 문장 수(업종군 순으로 쌓음, 한 문장이 여러 업종에 걸리면 중복 집계) · 끝 라벨 = 광고 문장 수 · 팬덤 내 비중",
            "업종별 근거문장 수",
            "자료: data/v7_final/ad_commercial_index_v7.json · 20개 업종 전부 표시, 색 계열 = 업종군(공공·미디어 파랑 · 패션·뷰티 주황/빨강 · 식품·생활·건강 초록 · IT·게임·엔터 보라 · 금융·산업 노랑 · 여가·모빌리티 분홍 · 유통 갈색 · 기타 회색). 뉴스·도서/참고자료는 0건",
            "aux1_ad_commercial_100.png", top=0.83, legend_groups=groups)

# ---- 2. 미디어·콘텐츠 노출 ------------------------------------------------------
me = load(D / "media_exposure_v7.json")
subs = ["예능", "유튜브", "영화", "드라마"]
rows = sorted([(f["fandom"], dict(f["subtag_counts"]), (f["n_media_bullets"], f["media_share"])) for f in me["fandoms"]],
              key=lambda r: (-r[2][0], -r[2][1], r[0]))
stacked_100(rows, subs, SERIES[:4], subs, lambda r: f"{r[2][0]}건 · {r[2][1] * 100:.0f}%",
            "미디어·콘텐츠 노출 지수 — 100개 팬덤 전체",
            f"미디어 노출 문장 {me['total_media_bullets']:,}건(전체의 {me['corpus_media_share'] * 100:.1f}%) · 노출 문장 수 순 정렬 · 막대 = 서브태그별 문장 수(중복 집계) · 끝 라벨 = 노출 문장 수 · 팬덤 내 비중",
            "서브태그별 근거문장 수", "자료: data/v7_final/media_exposure_v7.json · 서브태그 키워드: 예능·유튜브·영화·드라마",
            "aux2_media_exposure_100.png")

# ---- 3. 팬덤결속 -----------------------------------------------------------------
co = load(D / "fandom_cohesion_index_v7.json")
cats = sorted(co["categories"]) if isinstance(co["categories"], list) else sorted(co["categories"].keys())
cat_labels = [c.replace("_", " ", 1) for c in cats]
rows = sorted([(f["fandom"], dict(f["category_counts"]), (f["n_cohesion_bullets"], f["cohesion_share"])) for f in co["fandoms"]],
              key=lambda r: (-r[2][0], -r[2][1], r[0]))
stacked_100(rows, cats, SERIES[:len(cats)], cat_labels, lambda r: f"{r[2][0]}건 · {r[2][1] * 100:.0f}%",
            "팬덤결속 지수 — 100개 팬덤 전체",
            f"결속 신호 문장 {co['total_cohesion_bullets']:,}건(전체의 {co['corpus_cohesion_share'] * 100:.1f}%) · 결속 문장 수 순 정렬 · 막대 = 유형별 문장 수(중복 집계) · 끝 라벨 = 결속 문장 수 · 팬덤 내 비중",
            "결속 유형별 근거문장 수", "자료: data/v7_final/fandom_cohesion_index_v7.json · D(기부·후원)는 팬덤 주도 캠페인만 집계(개인 선행 오탐 방지 게이트)",
            "aux3_fandom_cohesion_100.png")

# ---- 4. 매체 크로스오버 ----------------------------------------------------------
mc = load(D / "media_crossover_index_v7.json")
rows = sorted([(f["fandom"], {"outlets": f["n_distinct_outlets"]}, (f["n_distinct_outlets"], f["news_media_share"], f["n_news_media_bullets"])) for f in mc["fandoms"]],
              key=lambda r: (-r[2][0], -r[2][2], r[0]))
stacked_100(rows, ["outlets"], [SERIES[0]], ["서로 다른 뉴스 매체 수"], lambda r: f"{r[2][0]}개 · 뉴스 {r[2][2]}건({r[2][1] * 100:.0f}%)",
            "매체 크로스오버 지수 — 100개 팬덤 전체",
            f"뉴스 매체 출처 문장 {mc['total_news_media_bullets']:,}건 · 코퍼스 전체 서로 다른 매체 {mc['n_distinct_outlets_corpuswide']:,}개 · 매체 수 순 정렬 · 끝 라벨 = 매체 수 · 뉴스 출처 문장 수(팬덤 내 비중)",
            "서로 다른 뉴스 매체(도메인) 수", "자료: data/v7_final/media_crossover_index_v7.json · 실제 클릭·유입이 아니라 '보도한 매체의 폭'을 재는 대리 지표",
            "aux4_media_crossover_100.png")

# ---- 5. 국내 지역 ----------------------------------------------------------------
# 17개 시/도 전부를 권역별 색 계열로 칠한다: 같은 권역은 같은 색상(hue)의 명도 단계, 누적 막대도 권역 순서로 쌓는다.
#   수도권(서울·인천·경기)=파랑, 부울경(부산·경남·울산)=주황/빨강, 대구경북(대구·경북)=청록/초록,
#   호남(광주·전남·전북)=보라, 충청(대전·충남·충북·세종)=노랑/호박, 강원=분홍, 제주=갈색 — 17개 시/도 전부 표시
dr = load(BASE / "v7_final_10020" / "analysis" / "domestic_regional_index" / "domestic_regional_index_v7.json")
rtot = {}
for v in dr.values():
    for k, c in v["region_mention_counts"].items():
        rtot[k] = rtot.get(k, 0) + c
REGION_STYLE = [  # (시/도, 색) — 권역 순서
    ("서울", "#2a78d6"), ("인천", "#7fb2ee"), ("경기", "#17498a"),
    ("부산", "#eb6834"), ("경남", "#e34948"), ("울산", "#f6a57f"),
    ("대구", "#1baf7a"), ("경북", "#008300"),
    ("광주", "#4a3aa7"), ("전남", "#9387e0"), ("전북", "#2a1f6e"),
    ("대전", "#eda100"), ("충남", "#f6cf6a"), ("충북", "#b37700"), ("세종", "#fbe3a0"),
    ("강원", "#e87ba4"),
    ("제주", "#8f6a3c"),
]
reg15 = [k for k, _ in REGION_STYLE]   # 17개 전부
assert set(reg15) == set(rtot), "17개 시/도 전부가 REGION_STYLE에 있어야 합니다"
rows = []
for name, v in dr.items():
    rc = v["region_mention_counts"]
    d = {k: rc.get(k, 0) for k in reg15}
    rows.append((name, d, (v["total_region_mentions"], v["n_regions_hit"], v.get("region_diversity", 0))))
rows.sort(key=lambda r: (-r[2][0], -r[2][1], r[0]))
stacked_100(rows, reg15, [c for _, c in REGION_STYLE],
            reg15,
            lambda r: f"{r[2][0]}건 · {r[2][1]}개 지역",
            "국내 지역 지수 — 100개 팬덤 전체",
            f"지역 언급 {sum(rtot.values()):,}건 · 지역 언급 수 순 정렬 · 막대 = 시/도별 언급 문장 수(권역 순으로 쌓음) · 끝 라벨 = 언급 수 · 언급된 시/도 수",
            "시/도별 언급 근거문장 수",
            "자료: v7_final_10020/analysis/domestic_regional_index/domestic_regional_index_v7.json (최종 코퍼스 10,020건 산출본) · 색 계열 = 권역(수도권 파랑 · 부울경 주황/빨강 · 대구경북 청록/초록 · 호남 보라 · 충청 노랑/호박 · 강원 분홍 · 제주 갈색)",
            "aux5_domestic_regional_100.png", top=0.83,
            legend_groups=[("수도권", [0, 1, 2]), ("부울경", [3, 4, 5]), ("대구경북", [6, 7]), ("호남", [8, 9, 10]),
                           ("충청", [11, 12, 13, 14]), ("강원", [15]), ("제주", [16])])

# ---- 6. 멤버 집중도 MCI (45개 그룹) ------------------------------------------------
mi = load(D / "member_mention_index_v7.json")
rows = []
for g, v in mi.items():
    n_mem = len(v["member_mention_counts"])
    top = max(v["member_impact_share_index"].items(), key=lambda kv: kv[1])
    rows.append((g, v["mci_index"], n_mem, v["total_member_mentions"], top))
rows.sort(key=lambda r: (-r[1], r[0]))
n = len(rows)
fig, ax = plt.subplots(figsize=(13.5, 0.3 * n + 2.6), dpi=DPI, facecolor=SURFACE)
y = list(range(n))[::-1]
ax.barh(y, [r[1] for r in rows], height=0.7, color=SERIES[0], edgecolor=SURFACE, linewidth=0.7, zorder=2)
ax.scatter([1 / r[2] for r in rows], y, marker="|", s=260, linewidths=2.2, color=INK, zorder=4)
for yi, r in zip(y, rows):
    ax.text(r[1] + 0.008, yi, f"{r[1]:.3f} · {r[2]}명 · 언급 {r[3]}건 · 최다 {r[4][0]} {r[4][1]:.2f}", va="center", ha="left", fontsize=9.5, color=INK2)
ax.set_yticks(y)
ax.set_yticklabels([f"{i + 1:>2}. {r[0]}" for i, r in enumerate(rows)])
ax.set_ylim(-0.7, n - 0.3)
style_axis(ax, 0.9)
ax.set_xlabel("MCI = Σ(멤버별 언급 점유율)²", fontsize=10.5, color=INK2, labelpad=6)
header(fig, "멤버 집중도 지수(MCI) — 45개 그룹 전체",
       "MCI 높은 순 정렬 · 막대 = MCI · 검은 세로선 = 구조적 하한 1/멤버수(완전 균등 배분일 때의 MCI) · 끝 라벨 = MCI · 멤버 수 · 멤버 언급 수 · 최다 언급 멤버 점유율",
       [Patch(facecolor=SERIES[0], label="MCI"), Line2D([0], [0], marker="|", color=INK, linestyle="none", markersize=14, markeredgewidth=2.2, label="하한 1/멤버수")], ncol=2)
footer(fig, "자료: data/v7_final/member_mention_index_v7.json (최종 코퍼스 10,020건) · MCI와 멤버 수의 상관 r=−0.728 — 막대와 세로선의 간격(MCI_excess)이 실제 쏠림의 크기")
fig.subplots_adjust(left=0.16, right=0.985, top=0.915, bottom=0.05)
fig.savefig(OUT / "aux6_member_mci_45.png", facecolor=SURFACE)
plt.close(fig)
print("saved", (OUT / "aux6_member_mci_45.png").relative_to(BASE))

# ---- 7. 세계 언어 ----------------------------------------------------------------
ww = load(D / "worldwide_language_pilot_live_reference_v7.json")
LANG = {"en": "영어", "ja": "일본어", "zh": "중국어", "es": "스페인어", "fr": "프랑스어", "th": "태국어", "id": "인도네시아어",
        "vi": "베트남어", "ru": "러시아어", "tl": "필리핀어", "pt": "포르투갈어", "tr": "튀르키예어", "ar": "아랍어"}
ltot = {}
for v in ww.values():
    for k, c in v["language_mention_counts"].items():
        if k != "ko":
            ltot[k] = ltot.get(k, 0) + c
lang_all = top_keys(ltot, len(ltot))   # 해외언어 13개 전부, 전체 합계 순
# 범주형 8색(고정 순서) 뒤에 서로 구분되는 5색을 이어 붙인다 — 그룹화 없이 언어마다 고유 색
LANG_COLORS = SERIES + [SERIES8, "#7fb2ee", "#a0782f", "#b3406c", "#7a9a00", "#1f93a8"]   # 13색 인접쌍 검증 통과(validate_palette.js)
rows = []
for name, v in ww.items():
    lc = v["language_mention_counts"]
    rows.append((name, {k: lc.get(k, 0) for k in lang_all}, (v["foreign_bullets"], v["foreign_ratio"], v["n_foreign_languages_hit"])))
rows.sort(key=lambda r: (-r[2][0], -r[2][1], r[0]))
stacked_100(rows, lang_all, LANG_COLORS[:len(lang_all)], [f"{LANG[k]} {ltot[k]:,}" for k in lang_all],
            lambda r: f"{r[2][0]}건 · {r[2][1] * 100:.0f}% · {r[2][2]}개 언어",
            "세계 언어 지수 — 100개 팬덤 전체",
            f"해외언어 출처 문장 {sum(ltot.values()):,}건 · 해외언어 문장 수 순 정렬 · 막대 = 출처 매체 언어별 문장 수(한국어 제외, 13개 언어 전부) · 범례 숫자 = 코퍼스 전체 합계 · 끝 라벨 = 해외언어 문장 수 · 팬덤 내 비중 · 해외 언어 수",
            "해외언어별 근거문장 수", "자료: data/v7_final/worldwide_language_pilot_live_reference_v7.json · 언어는 문장 본문이 아니라 출처 매체 기준(Coverage Index의 language_counts 재사용)",
            "aux7_worldwide_language_100.png", ncol=len(lang_all))
