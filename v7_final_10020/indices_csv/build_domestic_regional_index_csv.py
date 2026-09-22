# -*- coding: utf-8 -*-
"""
domestic_regional_index_live_reference_v7.json -> domestic_regional_index_v7.csv
국내 지역 지수(Domestic Regional Index) 100개 팬덤 전체 CSV 산출.
컬럼: 팬덤, 근거문장수, 총지역언급, 검출지역수, 지역다양성, 대표지역, 대표지역비중 + 17개 시도별 언급수
정렬: 총지역언급 내림차순 (보고서 표 15와 동일 기준)
"""
import json
import csv
from pathlib import Path

# 저장소 상대 경로
# 입력 JSON은 최종 라이브 코퍼스(10,020건) 기준 산출물이며, 아직 저장소에 없으면 data/v7_final/ 에 넣는다.
BASE = Path(__file__).resolve().parents[2]
OUT_DIR = BASE / "output" / "indices_csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 원본 데이터 묶음 README(data/v7_final/ARCHIVE_README_original.md)에는 domestic_regional_pilot_v6.json(라이브판)으로
# 등재되어 있다. 두 이름 중 v7_final 에 존재하는 쪽을 읽는다
_CANDS = [BASE / "data" / "v7_final" / "domestic_regional_index_live_reference_v7.json",
          BASE / "data" / "v7_final" / "domestic_regional_pilot_v6.json",
          # 최종 코퍼스 10,020건 산출본(analysis/domestic_regional_index/)
          BASE / "v7_final_10020" / "analysis" / "domestic_regional_index" / "domestic_regional_index_v7.json"]
SRC = next((c for c in _CANDS if c.exists()), _CANDS[0])
OUT = OUT_DIR / "domestic_regional_index_v7.csv"

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

REGIONS = ["서울","부산","대구","인천","광주","대전","울산","세종","경기","강원",
           "충북","충남","전북","전남","경북","경남","제주"]

rows = []
for fandom, d in data.items():
    counts = d["region_mention_counts"]
    row = {
        "팬덤": fandom,
        "근거문장수": d["total_group_bullets"],
        "총지역언급": d["total_region_mentions"],
        "검출지역수": d["n_regions_hit"],
        "지역다양성": d["region_diversity"],
        "대표지역": d["primary_region"],
        "대표지역비중": d.get("primary_region_share", 0),
    }
    for r in REGIONS:
        row[r] = counts.get(r, 0)
    rows.append(row)

rows.sort(key=lambda r: (-r["총지역언급"], r["팬덤"]))

fieldnames = ["팬덤","근거문장수","총지역언급","검출지역수","지역다양성","대표지역","대표지역비중"] + REGIONS

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

# 무결성 재검증: 17개 지역 합 == total_region_mentions (원본 JSON과 재계산값 대조)
mismatches = 0
for fandom, d in data.items():
    s = sum(d["region_mention_counts"].get(r, 0) for r in REGIONS)
    if s != d["total_region_mentions"]:
        mismatches += 1
        print(f"MISMATCH: {fandom} sum={s} vs total_region_mentions={d['total_region_mentions']}")

print(f"rows_written={len(rows)}")
print(f"mismatches={mismatches}")
print(f"top5 by 총지역언급: {[r['팬덤'] for r in rows[:5]]}")
