# -*- coding: utf-8 -*-
"""
v6~v7 전체 병합·교체 로그 -> 코퍼스 성장 이력 CSV (v6 1차 ~ v7 r73, 최종 10,020건; r73은 투어스 재작성, 순증 0).

입력 (data/v7_rounds/ 는 사용자가 GitHub에 직접 업로드한 원본 로그 전량):
  data/v7_rounds/v6_merge_log.json, v6_3_market_merge_log.json, v6_4_language_merge_log.json (v6 단계 로그 3개)
  data/v7_rounds/merge_log_r*.json (r1~r72; r36~r59는 before_total_bullets/after_total_bullets 키 사용)
  data/v7_rounds/swap_log_r*.json (로스터 교체 r29·r34·r62·r63; r58 교체는 merge_log_r58에 round_type=roster_swap로 기록)
  data/v7_rounds/round_log_r70.json (재분류만, 순증 0), round_log_r73.json (투어스 86건 재작성, 순증 0)
출력: data/v7_final/corpus_growth_history_v6_v7_full.csv
  컬럼: stage, kind, before_total, after_total, net_new_bullets, n_touched_fandoms, roster_change, note
검증: 각 행 after_total == 다음 행 before_total (체인 연속성) — 로그 자체의 기록 오차(r21→r22 +1, r22→r23 -1,
  r28→r30 사이 swap r29, r32→r35 사이 swap r34 등)는 숨기지 않고 'chain_gap' 컬럼에 그대로 적는다.
  마지막 after_total 이 10,020(최종 라이브 코퍼스)인지, 타임라인 CSV의 같은 라운드 코퍼스 값과 일치하는지 대조한다.
"""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
R = BASE / "data" / "v7_rounds"
S = R  # v6 단계 병합 로그 3개도 data/v7_rounds/ 에 함께 둔다
OUT = BASE / "data" / "v7_final" / "corpus_growth_history_v6_v7_full.csv"


def rkey(name):
    m = re.search(r"r(\d+)(?:_(p2|2ch))?", name)
    return (int(m.group(1)), {"": 0, "p2": 1, "2ch": 2}[m.group(2) or ""])


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


rows = []
v6 = load(S / "v6_merge_log.json")
rows.append(dict(stage="v6_round1", kind="merge", before_total=v6["before_total"], after_total=v6["after_total"], net_new_bullets=v6["after_total"] - v6["before_total"], n_touched_fandoms=v6["fandoms_touched"], roster_change="", note="v6 1차 병합"))
rows.append(dict(stage="v6_round2", kind="merge", before_total=v6["after_total"], after_total=v6["final_total"], net_new_bullets=v6["round2_added"], n_touched_fandoms="", roster_change="", note="v6 2차 병합(같은 로그 파일)"))
for fn, st in [("v6_3_market_merge_log.json", "v6.3_market_research"), ("v6_4_language_merge_log.json", "v6.4_language_research")]:
    d = load(S / fn)
    rows.append(dict(stage=st, kind="merge", before_total=d["before_total"], after_total=d["after_total"], net_new_bullets=d["net_new_bullets"], n_touched_fandoms=d.get("n_touched_fandoms", ""), roster_change="", note=d.get("round", "")))

events = []
for p in R.glob("merge_log_r*.json"):
    d = load(p)
    k = rkey(p.name)
    before = d.get("before_total", d.get("before_total_bullets"))
    after = d.get("after_total", d.get("after_total_bullets"))
    swap = f"{d['removed_fandom']}→{d['added_fandom']}" if d.get("round_type") == "roster_swap" else ""
    events.append((k, dict(stage=p.stem.replace("merge_log_", "v7_"), kind=d.get("round_type", "merge"), before_total=before, after_total=after,
                            net_new_bullets=d.get("net_new_bullets"), n_touched_fandoms=d.get("n_touched_fandoms", ""), roster_change=swap,
                            note=(d.get("round") or d.get("round_name") or "")[:80])))
for p in R.glob("swap_log_r*.json"):
    d = load(p)
    k = rkey(p.name)
    swaps = d.get("swaps") or [d]
    label = ", ".join(f"{s['removed_fandom']}→{s['added_fandom']}" for s in swaps)
    events.append((k, dict(stage=p.stem.replace("swap_log_", "v7_") + "_swap", kind="roster_swap", before_total=d.get("before_total_bullets"), after_total=d.get("after_total_bullets"),
                            net_new_bullets=(d.get("after_total_bullets") or 0) - (d.get("before_total_bullets") or 0) if d.get("after_total_bullets") is not None else "",
                            n_touched_fandoms="", roster_change=label, note=d.get("round", ""))))
d = load(R / "round_log_r70.json")
events.append(((70, 0), dict(stage="v7_r70", kind="reclassify", before_total=d["before_total"], after_total=d["after_total"], net_new_bullets=d["net_new_bullets"], n_touched_fandoms="", roster_change="", note="언어별 도메인 표 갱신, 재분류 1건")))
d = load(R / "round_log_r73.json")
events.append(((73, 0), dict(stage="v7_r73", kind="rewrite", before_total=d["before_total"], after_total=d["after_total"], net_new_bullets=d["net_new_bullets"], n_touched_fandoms=1, roster_change="", note="투어스(TWS) 영문 근거 86건 한국어 재작성, 순증 0")))
events.sort(key=lambda e: e[0])
rows += [e[1] for e in events]

# 체인 연속성
for i, r in enumerate(rows):
    r["chain_gap"] = ""
    if i and r["before_total"] not in (None, "") and rows[i - 1]["after_total"] not in (None, "") and r["before_total"] != rows[i - 1]["after_total"]:
        r["chain_gap"] = f"prev after {rows[i - 1]['after_total']} != before {r['before_total']}"

fields = ["stage", "kind", "before_total", "after_total", "net_new_bullets", "n_touched_fandoms", "roster_change", "chain_gap", "note"]
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

gaps = [(r["stage"], r["chain_gap"]) for r in rows if r["chain_gap"]]
last = rows[-1]
print(f"rows={len(rows)} -> {OUT.relative_to(BASE)}")
print(f"[검증] 마지막 단계 {last['stage']} after_total={last['after_total']} (최종 라이브 코퍼스 10,020: {'일치' if last['after_total'] == 10020 else '불일치'})")
print(f"[검증] 체인 불연속 {len(gaps)}건 (로그 자체 기록 오차·교체 라운드 경계): {gaps}")
tl_path = BASE / "data" / "silhouette_gate_timeline" / "corpus_silhouette_timeline_v7_66_2ch.csv"
if tl_path.exists():
    with open(tl_path, encoding="utf-8-sig") as f:
        tl = {row["라운드"]: row["코퍼스(불릿수)"] for row in csv.DictReader(f) if "추정" not in row["라운드"]}
    ok = bad = 0
    for r in rows:
        m = re.match(r"v7_r(\d+)(_p2|_2ch)?$", r["stage"])
        if not m or r["after_total"] in (None, ""):
            continue
        key = "r" + m.group(1) + ("_p2" if m.group(2) == "_p2" else "")
        cands = [k for k in tl if (k == key or k.startswith(key + "(")) and (("2차" in k) == (m.group(2) == "_2ch"))]
        if cands:
            if int(tl[cands[0]]) == r["after_total"]:
                ok += 1
            else:
                bad += 1
                print(f"  [불일치] {r['stage']} after={r['after_total']} vs 타임라인 {cands[0]}={tl[cands[0]]}")
    print(f"[검증] 타임라인 CSV 대조: 일치 {ok}건, 불일치 {bad}건")
assert last["after_total"] == 10020
