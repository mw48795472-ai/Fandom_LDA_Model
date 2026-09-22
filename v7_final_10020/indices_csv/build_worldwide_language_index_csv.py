# -*- coding: utf-8 -*-
"""
worldwide_language_index_live_reference_v7.json -> worldwide_language_index_v7.csv
세계 언어 지수(Worldwide Language Index) 100개 팬덤 전체 CSV 산출.
컬럼: 팬덤, 근거문장수, 총언어언급, 검출언어수, 언어다양성, 해외근거문장수, 해외비중,
      검출해외언어수, 해외언어다양성, 대표해외언어, 대표해외언어비중 + 14개 언어별 언급수
정렬: 해외근거문장수(foreign_bullets) 내림차순 (보고서 표 16과 동일 기준)
"""
import json
import csv
from pathlib import Path

# 저장소 상대 경로
# 입력 JSON은 최종 라이브 코퍼스(10,020건) 기준 산출물이며, 아직 저장소에 없으면 data/v7_final/ 에 넣는다.
BASE = Path(__file__).resolve().parents[2]
OUT_DIR = BASE / "output" / "indices_csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 원본 데이터 묶음 README(data/v7_final/ARCHIVE_README_original.md)상의 원본 파일명은
# worldwide_language_pilot_live_reference_v7.json 이다. 두 이름 중 존재하는 쪽을 읽는다.
_CANDS = [BASE / "data" / "v7_final" / "worldwide_language_index_live_reference_v7.json",
          BASE / "data" / "v7_final" / "worldwide_language_pilot_live_reference_v7.json"]
SRC = next((c for c in _CANDS if c.exists()), _CANDS[0])
OUT = OUT_DIR / "worldwide_language_index_v7.csv"

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

LANGS = ["ko","en","ja","zh","es","fr","th","id","vi","ru","tl","pt","tr","ar"]
LANG_LABEL = {
    "ko":"한국어","en":"영어","ja":"일본어","zh":"중국어","es":"스페인어","fr":"프랑스어",
    "th":"태국어","id":"인도네시아어","vi":"베트남어","ru":"러시아어","tl":"필리핀어",
    "pt":"포르투갈어","tr":"튀르키예어","ar":"아랍어",
}

rows = []
for fandom, d in data.items():
    counts = d["language_mention_counts"]
    row = {
        "팬덤": fandom,
        "근거문장수": d["total_group_bullets"],
        "총언어언급": sum(counts.values()),
        "검출언어수": d["n_languages_hit"],
        "언어다양성": d["language_diversity"],
        "해외근거문장수": d["foreign_bullets"],
        "해외비중": d["foreign_ratio"],
        "검출해외언어수": d["n_foreign_languages_hit"],
        "해외언어다양성": d["foreign_diversity"],
        "대표해외언어": LANG_LABEL.get(d.get("primary_foreign_language"), d.get("primary_foreign_language") or ""),
        "대표해외언어비중": d.get("primary_foreign_share", 0),
    }
    for l in LANGS:
        row[LANG_LABEL[l]] = counts.get(l, 0)
    rows.append(row)

rows.sort(key=lambda r: (-r["해외근거문장수"], r["팬덤"]))

fieldnames = ["팬덤","근거문장수","총언어언급","검출언어수","언어다양성",
              "해외근거문장수","해외비중","검출해외언어수","해외언어다양성",
              "대표해외언어","대표해외언어비중"] + [LANG_LABEL[l] for l in LANGS]

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

# 무결성 재검증: 14개 언어 합이 total_group_bullets와 대략 일치하는지, foreign_bullets가
# 14개 언어 중 ko를 제외한 합과 일치하는지 원본 JSON과 재계산 대조
mismatches_total = 0
mismatches_foreign = 0
for fandom, d in data.items():
    counts = d["language_mention_counts"]
    s_all = sum(counts.values())
    s_foreign = sum(v for k, v in counts.items() if k != "ko")
    if s_all != d["total_group_bullets"]:
        mismatches_total += 1
    if s_foreign != d["foreign_bullets"]:
        mismatches_foreign += 1
        print(f"FOREIGN MISMATCH: {fandom} sum_foreign={s_foreign} vs foreign_bullets={d['foreign_bullets']}")

print(f"rows_written={len(rows)}")
print(f"mismatches_total(=total_group_bullets 불일치 건수, 참고용)={mismatches_total}")
print(f"mismatches_foreign(=foreign_bullets 불일치 건수)={mismatches_foreign}")
print(f"top5 by 해외근거문장수: {[r['팬덤'] for r in rows[:5]]}")
