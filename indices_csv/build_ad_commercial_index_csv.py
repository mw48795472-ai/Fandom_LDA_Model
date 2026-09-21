# -*- coding: utf-8 -*-
"""
ad_commercial_index_v7.json -> ad_commercial_index_v7.csv
광고·상업성 지수(Ad/Commercial Index) 100개 팬덤 전체 CSV 산출.
컬럼: 팬덤, 구분(category), 근거문장수, 광고성문장수, 광고비중, 대표업종 + 20개 업종별 매칭수
정렬: 광고성문장수(n_ad_bullets) 내림차순
"""
import json
import csv
from pathlib import Path

# 저장소 상대 경로 (원본은 이전 세션 작업 디렉터리 /home/claude/work/... 절대경로였음).
# 입력 JSON은 최종 라이브 코퍼스(10,020건) 기준 산출물이며, 아직 저장소에 없으면 data/v7_final/ 에 넣는다.
BASE = Path(__file__).resolve().parents[1]
OUT_DIR = BASE / "output" / "indices_csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SRC = BASE / "data" / "v7_final" / "ad_commercial_index_v7.json"
OUT = OUT_DIR / "ad_commercial_index_v7.csv"

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

INDUSTRIES = data["industries"]  # 20개 업종, 원본 순서 유지
fandoms = data["fandoms"]

rows = []
for d in fandoms:
    counts = d["industry_counts"]
    row = {
        "팬덤": d["fandom"],
        "구분": d.get("category", ""),
        "근거문장수": d["n_total_bullets"],
        "광고성문장수": d["n_ad_bullets"],
        "광고비중": d["ad_share"],
        "대표업종": d.get("top_industry", ""),
    }
    for ind in INDUSTRIES:
        row[ind] = counts.get(ind, 0)
    rows.append(row)

rows.sort(key=lambda r: (-r["광고성문장수"], r["팬덤"]))

fieldnames = ["팬덤", "구분", "근거문장수", "광고성문장수", "광고비중", "대표업종"] + INDUSTRIES

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

# 무결성 재검증
# 1) 전체 광고성문장수 합 == total_ad_bullets (원본 상단 집계와 대조)
sum_ad = sum(d["n_ad_bullets"] for d in fandoms)
# 2) 업종별 합계(전 팬덤) == industry_totals (원본 상단 집계와 대조)
industry_sum = {ind: 0 for ind in INDUSTRIES}
for d in fandoms:
    for ind, cnt in d["industry_counts"].items():
        industry_sum[ind] = industry_sum.get(ind, 0) + cnt

industry_mismatches = []
for ind, total in data.get("industry_totals", {}).items():
    if industry_sum.get(ind, 0) != total:
        industry_mismatches.append((ind, industry_sum.get(ind, 0), total))

print(f"rows_written={len(rows)}")
print(f"sum(n_ad_bullets)={sum_ad} vs total_ad_bullets(JSON)={data['total_ad_bullets']} -> {'일치' if sum_ad == data['total_ad_bullets'] else '불일치'}")
print(f"industry_totals 불일치 항목: {industry_mismatches if industry_mismatches else '없음(전부 일치)'}")
print(f"top5 by 광고성문장수: {[r['팬덤'] for r in rows[:5]]}")
