# -*- coding: utf-8 -*-
"""
fandoms_v3_100.json(팬덤별 loyalty/spillover 중첩 배열) -> 단일 평면 CSV
컬럼: fandom, category, bullet_type, text, url

기본값은 최종 라이브 코퍼스(data/v7_final, 10,020건)이며, --src/--out으로
v6 r22 스냅샷(archive/v6_r22_era/data/v6_r22_snapshot, 5,612건)에도 그대로 쓸 수 있다.
행 수는 --expected(지정 시)와 대조 검증한다.
"""
import argparse
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(BASE / "data" / "v7_final" / "fandoms_v3_100.json"))
    ap.add_argument("--out", default=str(BASE / "data" / "v7_final" / "bullets_flat_v7_final.csv"))
    ap.add_argument("--expected", type=int, default=10020)
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as f:
        fandoms = json.load(f)

    rows = []
    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for it in fd.get(tag, []):
                rows.append({"fandom": fd["fandom"], "category": fd.get("category", ""),
                             "bullet_type": tag, "text": it["t"], "url": it.get("u", "")})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fandom", "category", "bullet_type", "text", "url"])
        w.writeheader()
        w.writerows(rows)

    print(f"fandoms={len(fandoms)} rows={len(rows)} -> {args.out}")
    if args.expected:
        status = "일치" if len(rows) == args.expected else "불일치"
        print(f"[검증] 행 수 {len(rows)} vs 기대값 {args.expected}: {status}")
        assert len(rows) == args.expected


if __name__ == "__main__":
    main()
