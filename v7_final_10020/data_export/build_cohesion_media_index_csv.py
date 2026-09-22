# -*- coding: utf-8 -*-
"""
팬덤결속 지수·매체 크로스오버 지수 원본 JSON(라이브 10,020건) -> 팬덤별 CSV 2종.
  data/v7_final/fandom_cohesion_index_v7.json -> data/v7_final/fandom_cohesion_index_v7.csv
      컬럼: 팬덤, 구분, 근거문장수, 결속문장수, 결속비중, 대표유형 + 5개 유형(A~E)별 매칭수
      정렬: 결속문장수 내림차순 (차트 스크립트 build_cohesion_index_v7.py와 동일 기준)
  data/v7_final/media_crossover_index_v7.json -> data/v7_final/media_crossover_index_v7.csv
      컬럼: 팬덤, 구분, 근거문장수, 뉴스매체문장수, 뉴스매체비중, 고유매체수, 매체다양성비율, 상위매체1~3
      정렬: 고유매체수 내림차순
v7_final_10020/indices_csv/build_*_index_csv.py 와 같은 원칙으로, 세부 합계를 원본 JSON 집계 필드와 재대조해 출력한다.
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
D = BASE / "data" / "v7_final"


def cohesion():
    with open(D / "fandom_cohesion_index_v7.json", encoding="utf-8") as f:
        co = json.load(f)
    cats = co["categories"]
    rows = []
    for x in co["fandoms"]:
        r = {"팬덤": x["fandom"], "구분": x["category"], "근거문장수": x["n_total_bullets"],
             "결속문장수": x["n_cohesion_bullets"], "결속비중": x["cohesion_share"], "대표유형": x.get("top_category", "")}
        for c in cats:
            r[c] = x["category_counts"].get(c, 0)
        rows.append(r)
    rows.sort(key=lambda r: (-r["결속문장수"], r["팬덤"]))
    out = D / "fandom_cohesion_index_v7.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    tot = sum(r["결속문장수"] for r in rows)
    cat_ok = all(sum(r[c] for r in rows) == co["category_totals"][c] for c in cats)
    print(f"[cohesion] rows={len(rows)} -> {out.name}")
    print(f"  [검증] Σ결속문장수 {tot} vs total_cohesion_bullets {co['total_cohesion_bullets']}: {'일치' if tot == co['total_cohesion_bullets'] else '불일치'}")
    print(f"  [검증] 유형별 합 = category_totals: {'전부 일치' if cat_ok else '불일치'}")
    assert tot == co["total_cohesion_bullets"] and cat_ok


def media():
    with open(D / "media_crossover_index_v7.json", encoding="utf-8") as f:
        mc = json.load(f)
    rows = []
    for x in mc["fandoms"]:
        top = [t["domain"] for t in x.get("top_outlets", [])[:3]] + ["", "", ""]
        rows.append({"팬덤": x["fandom"], "구분": x["category"], "근거문장수": x["n_total_bullets"],
                     "뉴스매체문장수": x["n_news_media_bullets"], "뉴스매체비중": x["news_media_share"],
                     "고유매체수": x["n_distinct_outlets"], "매체다양성비율": x["outlet_diversity_ratio"],
                     "상위매체1": top[0], "상위매체2": top[1], "상위매체3": top[2]})
    rows.sort(key=lambda r: (-r["고유매체수"], r["팬덤"]))
    out = D / "media_crossover_index_v7.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    tot = sum(r["뉴스매체문장수"] for r in rows)
    ratio_ok = all(abs(r["고유매체수"] / r["뉴스매체문장수"] - r["매체다양성비율"]) < 1e-3 for r in rows if r["뉴스매체문장수"])
    print(f"[media] rows={len(rows)} -> {out.name}")
    print(f"  [검증] Σ뉴스매체문장수 {tot} vs total_news_media_bullets {mc['total_news_media_bullets']}: {'일치' if tot == mc['total_news_media_bullets'] else '불일치'}")
    print(f"  [검증] 매체다양성비율 = 고유매체수/뉴스매체문장수: {'전부 일치' if ratio_ok else '불일치'}")
    assert tot == mc["total_news_media_bullets"] and ratio_ok


if __name__ == "__main__":
    cohesion()
    media()
