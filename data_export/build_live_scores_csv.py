# -*- coding: utf-8 -*-
"""
chart3d_payload_live_reference_v7.json(3D 포지셔닝맵 HTML에 내장된 라이브 코퍼스 10,020건
기준 payload)의 rows를 CSV로 푼다. (2026-09-22: 출력 파일명을 chart3d_positioning_rows_live_v7.csv로 변경 —
원본 산출물 fandom_scores_live_reference_v7.csv(라이브 재적합 F 비중 5개 컬럼 포함)가 저장소에 추가되어 이름 충돌 방지.
두 파일의 loyalty/spillover/diversity/coverage/activity/dominant는 100/100 동일하고, 이 파일에는 4구획(quadrant)이 추가로 있다.)

컬럼: fandom, category, loyalty_score, spillover_score, factor_diversity, coverage_index,
      dominant_factor, activity, n_loyalty_bullets, n_spillover_bullets, quadrant, is_target
정렬: payload 순서(loyalty+spillover 내림차순) 유지.

무결성 재검증: activity == n_loyalty_bullets + n_spillover_bullets, activity 합 == 10,020,
표본 평균 == payload의 lmean/smean, 4구획 카운트 == payload의 quadrant_counts.
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / "data" / "v7_final" / "chart3d_payload_live_reference_v7.json"
OUT = BASE / "data" / "v7_final" / "chart3d_positioning_rows_live_v7.csv"


def main():
    with open(SRC, encoding="utf-8") as f:
        payload = json.load(f)
    rows = payload["rows"]
    fields = ["fandom", "category", "loyalty_score", "spillover_score", "factor_diversity",
              "coverage_index", "dominant_factor", "activity", "n_loyalty_bullets",
              "n_spillover_bullets", "quadrant", "is_target"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({"fandom": r["fandom"], "category": r["category"],
                        "loyalty_score": r["loyalty"], "spillover_score": r["spillover"],
                        "factor_diversity": r["diversity"], "coverage_index": r["coverage"],
                        "dominant_factor": r["dominant"], "activity": r["activity"],
                        "n_loyalty_bullets": r["n_loyalty_bullets"],
                        "n_spillover_bullets": r["n_spillover_bullets"],
                        "quadrant": r["quadrant"], "is_target": r["is_target"]})

    n = len(rows)
    act_mismatch = sum(1 for r in rows if r["activity"] != r["n_loyalty_bullets"] + r["n_spillover_bullets"])
    total = sum(r["activity"] for r in rows)
    lmean = round(sum(r["loyalty"] for r in rows) / n, 5)
    smean = round(sum(r["spillover"] for r in rows) / n, 5)
    from collections import Counter
    q = Counter(r["quadrant"] for r in rows)
    print(f"rows={n} -> {OUT}")
    print(f"[검증] activity = loyalty+spillover 불릿 수 불일치: {act_mismatch}/{n}")
    print(f"[검증] activity 합계 {total} (payload corpus_total_evidence={payload['corpus_total_evidence']})")
    print(f"[검증] 평균 loyalty={lmean} (payload lmean={payload['lmean']}), spillover={smean} (payload smean={payload['smean']})")
    print(f"[검증] 4구획 {dict(q)} (payload {payload['quadrant_counts']})")
    assert act_mismatch == 0 and total == payload["corpus_total_evidence"]
    assert lmean == round(payload["lmean"], 5) and smean == round(payload["smean"], 5)
    assert dict(q) == payload["quadrant_counts"]


if __name__ == "__main__":
    main()
