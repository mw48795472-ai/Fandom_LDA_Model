# -*- coding: utf-8 -*-
"""L13 — 로스터 이력 파일. 동결(v7-40)과 라이브의 팬덤 집합이 다른 이유(교체 3건)와 그 이전 교체 3건을 한 파일로 고정한다.
모든 표가 이 파일을 참조해 '해당 없음'을 표기할 수 있도록, 팬덤마다 들어온 라운드·나간 라운드·교체 상대·동결/라이브 포함 여부를 적는다.

입력: data/v7_rounds/swap_log_r29.json, swap_log_r34.json, merge_log_r58.json, swap_log_r62.json, swap_log_r63.json,
      data/v7_final/fandoms_v3_100.json (라이브 로스터·카테고리), data/v7_final/fandom_scores_v6.json (동결 로스터)
출력: data/v7_final/roster_history_v7.csv (106행 = 라이브 100 + 제거 6)
실행: python v7_final_10020/data_export/build_roster_history_v7.py
"""
import csv, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
R = BASE / "data" / "v7_rounds"; D = BASE / "data" / "v7_final"
live = {f["fandom"]: f for f in json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))}
frozen = {r["fandom"] for r in json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))}

swaps = []  # (round, removed, removed_cat, removed_n, added, added_cat, added_n, added_l, added_s)
for fn in ("swap_log_r29.json", "swap_log_r34.json", "merge_log_r58.json", "swap_log_r62.json", "swap_log_r63.json"):
    d = json.load(open(R / fn, encoding="utf-8")); rnd = int(fn.split("_r")[1].split(".")[0])
    items = d["swaps"] if "swaps" in d else [d]
    for s in items:
        swaps.append((rnd, s["removed_fandom"], s.get("removed_fandom_category", ""), s.get("removed_fandom_bullet_count"),
                      s["added_fandom"], s.get("added_fandom_category", ""), s.get("added_fandom_bullet_count"), s.get("added_fandom_loyalty"), s.get("added_fandom_spillover")))
swaps.sort()
entered = {a: (rnd, rem, n, l, s) for rnd, rem, _, _, a, _, n, l, s in swaps}
removed = {rem: (rnd, a, rc, rn) for rnd, rem, rc, rn, a, _, _, _, _ in swaps}

rows = []
for name, f in live.items():
    e = entered.get(name)
    rows.append({"fandom": name, "category": f.get("category", ""), "status": "live", "entered_round": f"r{e[0]}" if e else "initial(v4∼v5)",
                 "replaces": e[1] if e else "", "removed_round": "", "replaced_by": "",
                 "in_frozen_v7_40": "Y" if name in frozen else "N", "in_live_10020": "Y",
                 "bullets_at_entry": e[2] if e else "", "loyalty_at_entry": e[3] if e else "", "spillover_at_entry": e[4] if e else "",
                 "bullets_live": len(f["loyalty"]) + len(f["spillover"]),
                 "note": ("동결 이후 교체로 들어옴 — 동결 순위표·페르소나에는 없음" if e and e[0] > 40 else "동결 이전 교체로 들어옴 — 동결·라이브 모두 포함" if e else "")})
for name, (rnd, by, cat, n) in removed.items():
    rows.append({"fandom": name, "category": cat, "status": "removed", "entered_round": "initial(v4∼v5)", "replaces": "",
                 "removed_round": f"r{rnd}", "replaced_by": by, "in_frozen_v7_40": "Y" if name in frozen else "N", "in_live_10020": "N",
                 "bullets_at_entry": "", "loyalty_at_entry": "", "spillover_at_entry": "", "bullets_live": "", "note": f"r{rnd}에서 제거, 불릿 {n}건 삭제" + (" — 동결 스냅샷에는 포함(r22 백업에 문장 일부 보존)" if name in frozen else " — 동결 이전 제거")})
rows.sort(key=lambda r: (r["status"] != "live", r["entered_round"], r["fandom"]))
out = D / "roster_history_v7.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
n_live = sum(r["status"] == "live" for r in rows); n_rm = len(rows) - n_live
assert n_live == 100 and set(r["fandom"] for r in rows if r["in_frozen_v7_40"] == "Y") == frozen
print(f"wrote {out}: live {n_live}, removed {n_rm}, frozen set {sum(r['in_frozen_v7_40']=='Y' for r in rows)}, swaps {len(swaps)}")
