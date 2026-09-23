# -*- coding: utf-8 -*-
"""후보 JSON이 동결 스냅샷(v7-40, 7,350건) 코퍼스인지 판정한다.

기준값은 전부 저장소 안의 동결 산출물(data/v7_final/fandom_scores_v6.json)에서 가져온다.
  1. 구조: 팬덤 100개, 각 팬덤 loyalty/spillover 배열, 원소 {t, u}
  2. 총 불릿 = 7,350
  3. 로스터 = 동결 로스터 100개 (BE'O·pH-1·한로로 포함, 빈지노·몬스타엑스·투어스 제외)
  4. 팬덤별 loyalty/spillover 건수 100쌍 일치
  5. 팬덤별 loyalty_raw/spillover_raw = EvidenceScore 산식 재계산값 (오차 1e-6)
     — 문장의 숫자 패턴·키워드에서 계산되므로 문장 내용까지 맞아야 통과하는 지문
  6. (참고) 97개 공통 팬덤 불릿이 라이브 10,020건에 있는 비율, 3개 동결 전용 팬덤과 r22 백업본의 포함 관계

이 폴더의 fandoms_v7_40_frozen_reconstructed.json(근사 복원본)에 대한 결과: 3/7 통과 —
97개 팬덤은 4·5번을 전부 통과(문장 집합이 동결과 동일)하고, BE'O·pH-1·한로로 3개만 r22 백업 수준(7,326/7,350).

실행: python verify_frozen_corpus_candidate.py [후보.json]   (인자 없으면 이 폴더의 근사 복원본을 검사)
"""
import ast, hashlib, json, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
D = REPO / "data" / "v7_final"
cand_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "fandoms_v7_40_frozen_reconstructed.json"

# --- 산식은 verify_v7_final_consistency.py 에서 ast 로 그대로 잘라 온다 (재구현 없음)
src = (REPO / "verify_v7_final_consistency.py").read_text(encoding="utf-8")
tree = ast.parse(src); ns = {"re": re}
for n in tree.body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("NUM_PATTERN", "LOYALTY_BONUS_KW", "SPILLOVER_BONUS_KW"):
        exec(ast.get_source_segment(src, n), ns)
    if isinstance(n, ast.FunctionDef) and n.name == "evidence_score":
        exec(ast.get_source_segment(src, n), ns)
evidence_score, LB, SB = ns["evidence_score"], ns["LOYALTY_BONUS_KW"], ns["SPILLOVER_BONUS_KW"]

frozen = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))}
live = {f["fandom"]: f for f in json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))}
z = zipfile.ZipFile(REPO / "archive" / "v6_r22_era_backup.zip")
r22 = {f["fandom"]: f for f in json.loads(z.read("v6_r22_era/data/v6_r22_snapshot/fandoms_v3_100.json"))}

results = []
def check(label, ok, detail=""):
    results.append(ok); print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

raw = cand_path.read_bytes()
print(f"후보: {cand_path}  ({len(raw):,} bytes, sha256 {hashlib.sha256(raw).hexdigest()[:16]}…)")
try:
    d = json.loads(raw.decode("utf-8-sig"))
except Exception as e:
    print("  [FAIL] JSON 파싱 실패:", e); sys.exit(1)
fl = d if isinstance(d, list) else d.get("fandoms") if isinstance(d, dict) else None
ok_struct = isinstance(fl, list) and all(isinstance(f, dict) and "fandom" in f and isinstance(f.get("loyalty"), list) and isinstance(f.get("spillover"), list) for f in fl)
check("1. 구조: 팬덤 리스트 + loyalty/spillover 배열", ok_struct, f"팬덤 {len(fl) if isinstance(fl, list) else '?'}개")
if not ok_struct:
    print("\n판정: 코퍼스 구조가 아님"); sys.exit(1)
bad_items = sum(1 for f in fl for k in ("loyalty", "spillover") for it in f[k] if not (isinstance(it, dict) and "t" in it))
check("   원소가 {t, u} 형식", bad_items == 0, f"형식 불일치 {bad_items}건")
cand = {f["fandom"]: f for f in fl}
n_total = sum(len(f["loyalty"]) + len(f["spillover"]) for f in fl)
check("2. 총 불릿 = 7,350", n_total == 7350, f"{n_total:,}")
extra, missing = sorted(set(cand) - set(frozen)), sorted(set(frozen) - set(cand))
check("3. 로스터 = 동결 로스터 100개", not extra and not missing, f"후보에만: {extra[:5]} / 동결에만: {missing[:5]}")
cnt_ok = [k for k in frozen if k in cand and (len(cand[k]["loyalty"]), len(cand[k]["spillover"])) == (frozen[k]["n_loyalty_bullets"], frozen[k]["n_spillover_bullets"])]
check("4. 팬덤별 loyalty/spillover 건수 100/100", len(cnt_ok) == 100, f"{len(cnt_ok)}/100 일치")
raw_ok = [k for k in frozen if k in cand and abs(evidence_score(cand[k]["loyalty"], LB) - frozen[k]["loyalty_raw"]) < 1e-6 and abs(evidence_score(cand[k]["spillover"], SB) - frozen[k]["spillover_raw"]) < 1e-6]
check("5. EvidenceScore 재계산 = loyalty_raw/spillover_raw 100/100 (문장 내용 지문)", len(raw_ok) == 100, f"{len(raw_ok)}/100 일치")
act_ok = sum(1 for k in frozen if k in cand and len(cand[k]["loyalty"]) + len(cand[k]["spillover"]) == frozen[k]["activity"])
check("   activity(불릿 수) 100/100", act_ok == 100, f"{act_ok}/100")

# 참고 정보 (판정에는 안 씀)
common = [k for k in cand if k in live]
sub = tot = 0
for k in common:
    lt = {it["t"] for it in live[k]["loyalty"]} | {it["t"] for it in live[k]["spillover"]}
    for it in cand[k]["loyalty"] + cand[k]["spillover"]:
        tot += 1; sub += it["t"] in lt
print(f"  [참고] 라이브 공통 팬덤 {len(common)}개: 후보 불릿 {tot:,}건 중 라이브에 같은 문장 {sub:,}건 ({sub/max(tot,1):.1%})")
for k in ("BE'O", "pH-1", "한로로"):
    if k in cand and k in r22:
        ct = {it["t"] for it in cand[k]["loyalty"] + cand[k]["spillover"]}
        rt = [it["t"] for it in r22[k]["loyalty"] + r22[k]["spillover"]]
        print(f"  [참고] {k}: r22 백업 {len(rt)}건 중 후보에 있음 {sum(t in ct for t in rt)}건, 후보 총 {len(ct)}건 (동결 기준 {frozen[k]['activity']}건)")

n_pass = sum(results)
verdict = ("**동결 7,350건 코퍼스 맞음**" if all(results)
           else f"근사 복원본 — {len(raw_ok)}개 팬덤은 문장 집합까지 동결과 동일, 나머지 {100-len(raw_ok)}개 부분" if len(raw_ok) >= 90
           else "동결 코퍼스 아님")
print(f"\n판정: {n_pass}/{len(results)} 통과 → {verdict}")
