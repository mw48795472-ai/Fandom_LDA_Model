# -*- coding: utf-8 -*-
"""L5 — 식(1) EvidenceScore의 문장 단위 중간 결과와 Time 하위지표 분모를 파일로 남긴다.
산식은 verify_v7_final_consistency.py(NUM_PATTERN·보너스 키워드·evidence_score)와 run_lda_v6.py(years_in)에서 ast로 그대로 가져온다.

출력: evidence_score_by_sentence_v7.csv — 10,020행: fandom, bullet_type, idx, n_numeric, n_bonus_kw, bonus_kw_hit, evidence_score, years_in_text
      index_intermediate_values_v7.json — 코퍼스 연도 범위(Time 분모), 팬덤별 loyalty/spillover 문장 점수 합(=loyalty_raw/spillover_raw) 대조 결과
검증: 팬덤별 합이 fandom_scores_live_reference_v7.json의 loyalty_raw/spillover_raw와 1e-6 안에서 100/100 일치, 연도 범위 수 = 12
실행: python v7_final_10020/index_methodology/export_evidence_score_sentences_v7.py
"""
import ast, csv, json, re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
D = BASE / "data" / "v7_final"

ns = {"re": re}
src = (BASE / "verify_v7_final_consistency.py").read_text(encoding="utf-8")
for n in ast.parse(src).body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("NUM_PATTERN", "LOYALTY_BONUS_KW", "SPILLOVER_BONUS_KW"):
        exec(ast.get_source_segment(src, n), ns)
src2 = (BASE / "run_lda_v6.py").read_text(encoding="utf-8")
for n in ast.parse(src2).body:
    if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_YEAR_RE") or (isinstance(n, ast.FunctionDef) and n.name == "years_in"):
        exec(ast.get_source_segment(src2, n), ns)
NUM, LB, SB, years_in = ns["NUM_PATTERN"], ns["LOYALTY_BONUS_KW"], ns["SPILLOVER_BONUS_KW"], ns["years_in"]

fandoms = json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))
scores = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8"))}
rows, sums, corpus_years = [], {}, set()
for fd in fandoms:
    sums[fd["fandom"]] = {"loyalty": 0.0, "spillover": 0.0}
    for tag, bonus in (("loyalty", LB), ("spillover", SB)):
        for idx, it in enumerate(fd[tag]):
            t = it["t"]; nn = len(NUM.findall(t)); hits = [kw for kw in bonus if kw in t]
            score = 1.0 + 0.5 * nn + 0.3 * len(hits); sums[fd["fandom"]][tag] += score
            ys = sorted(years_in(t)); corpus_years |= set(ys)
            rows.append({"fandom": fd["fandom"], "bullet_type": tag, "idx": idx, "n_numeric": nn, "n_bonus_kw": len(hits), "bonus_kw_hit": "|".join(hits),
                         "evidence_score": round(score, 2), "years_in_text": "|".join(ys)})
with open(HERE / "evidence_score_by_sentence_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
match = sum(1 for k, v in sums.items() if abs(v["loyalty"] - scores[k]["loyalty_raw"]) < 1e-6 and abs(v["spillover"] - scores[k]["spillover_raw"]) < 1e-6)
yrs = sorted(corpus_years)
tc_ok = sum(1 for k, r in scores.items() if abs(len(r["coverage_detail"]["years_mentioned"]) / len(yrs) - r["coverage_detail"]["time_coverage"]) < 0.0015)
out = {"formula": "EvidenceScore(t) = 1.0 + 0.5·n_numeric(t) + 0.3·n_bonus_kw(t); loyalty_raw = Σ loyalty 문장, spillover_raw = Σ spillover 문장",
       "numeric_pattern": NUM.pattern, "loyalty_bonus_keywords": LB, "spillover_bonus_keywords": SB,
       "time_denominator": {"rule": "코퍼스 전체 문장에서 정규식 (?<!\\d)(20[0-2][0-9])(?!\\d) 로 뽑은 2015∼2026 연도의 고유 개수", "corpus_years": yrs, "n_corpus_years": len(yrs),
                            "time_coverage = len(years_mentioned)/n_corpus_years 재현": f"{tc_ok}/100"},
       "check": {"per_fandom_sum_equals_raw_scores": f"{match}/100", "n_sentences": len(rows)}}
json.dump(out, open(HERE / "index_intermediate_values_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"sentences {len(rows):,} | 팬덤별 합 = raw 점수 {match}/100 | 코퍼스 연도 {len(yrs)}개 {yrs[0]}∼{yrs[-1]} | time_coverage 재현 {tc_ok}/100")
