# -*- coding: utf-8 -*-
"""시계열 패널 분석 노트북(시계열_패널분석_v7.ipynb)을 만들고 실행한다.

노트북은 timeseries_panel_v7.py의 함수를 그대로 불러 단계별(A 시점 태깅 → B 패널 → E 편향 → 통계 → C 경로 추이)로 표와 그림을 보여 준다.
실행: python 시계열분석/build_timeseries_notebook_v7.py   (jupyter nbconvert --execute, 약 1분)
"""
import subprocess, sys
from pathlib import Path

def _strip_exec_times(p):
    """실행 시각을 지우고 셀 id를 고정해, 다시 실행해도 노트북 파일이 바이트 단위로 같게 한다."""
    import nbformat as _nbf
    _nb = _nbf.read(str(p), as_version=4)
    for _i, _c in enumerate(_nb.cells):  # 실행 시각 제거 + 셀 id를 순서 번호로 고정(nbformat 기본값은 무작위)
        _c.metadata.pop("execution", None); _c["id"] = f"cell-{_i:03d}"
    _nbf.write(_nb, str(p))


import nbformat
from nbformat.v4 import new_code_cell as code, new_markdown_cell as md, new_notebook

HERE = Path(__file__).resolve().parent
PRE = '''import sys, json, csv
from pathlib import Path
HERE = Path.cwd() if (Path.cwd() / "timeseries_panel_v7.py").exists() else Path.cwd() / "시계열분석"
sys.path.insert(0, str(HERE))
import pandas as pd, numpy as np
import timeseries_panel_v7 as ts
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
D = ts.D; OUT = ts.OUT
'''
cells = [
    md("# 시계열 패널 분석 — 근거문장의 시점으로 본 연도별 추이\n\n본 분석(루트 README)과 별개의 탐색 분석이다. 해석 계층·점수 정의는 그대로 두고, 근거문장 10,020건에 사건 연도를 붙여 같은 EvidenceScore 산식을 연도별로 다시 센다. "
       "각 셀은 `timeseries_panel_v7.py`의 함수를 부른다. 규칙·산식은 `시계열_패널분석_상세명세서.docx`, 결과 문서는 `시계열_패널분석_V7.md`."),
    code(PRE + '''flat = ts.rows(D / "bullets_flat_v7_final.csv"); ev = ts.rows(ts.REPO / "v7_final_10020" / "index_methodology" / "evidence_score_by_sentence_v7.csv"); prov = ts.rows(D / "bullet_provenance_v7.csv")
print("문장", len(flat), "| 점수 CSV", len(ev), "| 시점 태그 CSV", len(prov))'''),
    md("## A. 문장 시점 태깅\n\n우선순위: 본문 연도(여럿이면 가장 늦은 연도) → URL 날짜 + 상대 표현(지난해·올해 …) → URL 날짜. 아무것도 없으면 `none`."),
    code('''tags = ts.tag_sentences(flat)
for t, r in zip(tags, flat): t["_text"] = r["text"]
tg = pd.DataFrame([{k: v for k, v in t.items() if k != "_text"} for t in tags])
print(tg["year_source"].value_counts().to_dict())
print("시점 태그 비율:", round((tg["year_source"] != "none").mean(), 4))
both = tg[(tg["text_url_gap"] != "")].copy(); both["gap"] = both["text_url_gap"].astype(int)
print("본문 연도·URL 연도 둘 다:", len(both), "| 같은 해:", (both["gap"] == 0).sum(), "| ±1년:", (both["gap"].abs() <= 1).sum())
tg[tg["event_year"] != ""]["event_year"].astype(int).value_counts().sort_index().loc[2015:2026]'''),
    md("## B·E. 팬덤×연도 패널\n\n칸 = (팬덤, 사건 연도). 규모 = EvidenceScore 합, 밀도 = 문장당 평균. 5문장 미만 칸은 결측(`valid_cell=0`), 축별 밀도는 3문장 이상일 때만. 연도 점유율과 후기 추가 비율(r41∼r72)도 함께 둔다."),
    code('''panel, year_total, round_dist, untagged, cell = ts.build_panel(tags, ev, prov)
pn = pd.DataFrame(panel); print("칸", len(pn), "| 유효 칸", int(pn["valid_cell"].sum()), "| 유효 연도 3개 이상 팬덤", (pn[pn.valid_cell == 1].groupby("fandom").size() >= 3).sum())
pn[pn["fandom"] == "BTS"]'''),
    code('''ys = pd.DataFrame(ts.year_stats(panel)); ys'''),
    md("### 검증 — 연도별 합 + 연도 미상 = 현재 raw 점수"),
    code('''scores = {r["fandom"]: r for r in ts.load(D / "fandom_scores_live_reference_v7.json")}; ok = 0
for f, s in scores.items():
    ls = sum(c["loyalty_sum"] for (ff, y), c in cell.items() if ff == f); ss = sum(c["spillover_sum"] for (ff, y), c in cell.items() if ff == f)
    un = [e for t, e in zip(tags, ev) if t["fandom"] == f and (not t["event_year"] or int(t["event_year"]) not in ts.YEARS)]
    ls += sum(float(e["evidence_score"]) for e in un if e["bullet_type"] == "loyalty"); ss += sum(float(e["evidence_score"]) for e in un if e["bullet_type"] == "spillover")
    ok += abs(ls - s["loyalty_raw"]) < 1e-6 and abs(ss - s["spillover_raw"]) < 1e-6
print("raw 점수 재현:", f"{ok}/100")'''),
    md("## 통계 — 팬덤별 추세, 고정효과 회귀, 부트스트랩"),
    code('''tr = pd.DataFrame(ts.fandom_trends(panel)); tr[tr["rho_loyalty_density"] != ""].head(15)'''),
    code('''reg = ts.panel_regressions(panel)
for k in ("loyalty_density", "spillover_density"): print(k, {kk: v for kk, v in reg[k].items() if kk != "year_effects_vs_2015"})
print("loyalty–spillover panel:", reg["loyalty_spillover_panel"])'''),
    code('''ranked = sorted(scores, key=lambda f: -(scores[f]["loyalty_score"] + scores[f]["spillover_score"])); pv = pn[pn.valid_cell == 1].groupby("fandom").size()
top8 = [f for f in ranked if pv.get(f, 0) >= 3][:8]; boots = ts.bootstrap_cells(cell, top8); pd.DataFrame(boots).head(12)'''),
    md("## C. 경로(F1∼F5) 비중의 연도 추이 — 근사\n\n저장된 재현 K=8 모델(옛 토크나이저)의 문서-토픽 분포 θ를 토픽 대응표(Hungarian)로 공식 토픽에 잇고 공식 토픽→F 배정으로 접는다. 대응 Jaccard가 낮은 토픽이 있어 방향 참고용이다."),
    code('''per_fy, per_f, n_docs, topic_map = ts.factor_shares_by_year(tags, None); print("θ 문서 수", n_docs); pd.DataFrame(topic_map).T'''),
    code('''fs = pd.read_csv(OUT / "fandom_year_factor_share_v7.csv"); tr2 = pd.read_csv(OUT / "persona_transition_v7.csv")
print("첫·마지막 유효 연도 페르소나가 다른 팬덤:", int(tr2["changed"].sum()), "/", len(tr2)); tr2.head(10)'''),
    md("## 그림\n\n`timeseries_panel_v7.py`가 만든 PNG 4장(`output/`)."),
    code('''from IPython.display import Image, display
for f in ["fig_ts01_year_profiles.png", "fig_ts02_yearwise_corr.png", "fig_ts03_persona_by_year.png", "fig_ts04_round_year_bias.png"]: display(Image(filename=str(OUT / f), width=900))'''),
    md("## 요약 JSON\n\n`output/summary_v7.json`의 핵심 값. 상세명세서·R 코드는 이 파일을 대조한다."),
    code('''S = json.load(open(OUT / "summary_v7.json", encoding="utf-8"))
print(json.dumps({k: S[k] for k in ("A_time_tags", "B_panel")}, ensure_ascii=False, indent=1)[:1500])'''),
]
nb = new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}, "language_info": {"name": "python"}})
out = HERE / "시계열_패널분석_v7.ipynb"; nbformat.write(nb, out)
print("wrote", out)
if "--no-exec" not in sys.argv:
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=600", str(out)], check=True, cwd=str(HERE)); _strip_exec_times(out)
    print("executed")
