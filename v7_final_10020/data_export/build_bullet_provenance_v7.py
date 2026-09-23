# -*- coding: utf-8 -*-
"""L15 — 불릿 시점 태그(소급). 라이브 코퍼스 10,020건 각 불릿이 어느 라운드 구간에 추가됐는지를 저장소에 있는 스냅샷 4개로 역산해
사이드카 파일로 남긴다. 코퍼스 JSON 자체는 손대지 않는다(스키마·해시 유지).

근거: 병합 파이프라인은 새 근거를 각 팬덤 목록 끝에 붙인다(접두어 검증: r13·r22·동결 근사 스냅샷이 라이브 목록의 정확한 접두어, 예외는 r56에
수정된 여자친구 spillover 문장 1건). 따라서 스냅샷별 팬덤·유형 건수가 곧 구간 경계다.
  ≤r13   archive/v7_r13_corpus_5099.json (5,099건)          r14∼r22  archive/v6_r22_era_backup.zip 의 r22 코퍼스 (5,612건)
  r23∼r39 data/v7_final/frozen_snapshot_v7_40/…(7,326건, 동결 근사)   r41∼r72  나머지(라이브 10,020건)
교체로 들어온 팬덤(GOT7 r29, 김재중·박서진 r34, 빈지노 r58, 몬스타엑스 r62, 투어스 r63)은 진입 라운드를 하한으로 둔다.

출력: data/v7_final/bullet_provenance_v7.csv — fandom, bullet_type, idx, text_sha1, added_bin, bin_lower_round, bin_upper_round, bin_source
검증: 구간별 건수 합 = 스냅샷 건수(제거 팬덤 분 포함), 접두어 위반 0(여자친구 r56 수정 1건 제외)
실행: python v7_final_10020/data_export/build_bullet_provenance_v7.py
권장 스키마(다음 라운드부터): 불릿에 round, added_at, method, bullet_id(text_sha1)를 직접 기록하면 이 역산이 필요 없다.
"""
import csv, hashlib, json, zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
D = BASE / "data" / "v7_final"
live = {f["fandom"]: f for f in json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))}
r13 = {f["fandom"]: f for f in json.load(open(BASE / "archive" / "v7_r13_corpus_5099.json", encoding="utf-8"))}
r22 = {f["fandom"]: f for f in json.loads(zipfile.ZipFile(BASE / "archive" / "v6_r22_era_backup.zip").read("v6_r22_era/data/v6_r22_snapshot/fandoms_v3_100.json"))}
fr = {f["fandom"]: f for f in json.load(open(D / "frozen_snapshot_v7_40" / "fandoms_v7_40_frozen_reconstructed.json", encoding="utf-8"))}
roster = {r["fandom"]: r for r in csv.DictReader(open(D / "roster_history_v7.csv", encoding="utf-8-sig"))}
SNAPS = [("≤r13", 13, r13), ("r14∼r22", 22, r22), ("r23∼r39", 39, fr)]

def sha1(t): return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]

rows, violations = [], []
for name, f in live.items():
    entry = roster[name]["entered_round"]; entry_r = int(entry[1:]) if entry.startswith("r") else 0
    for tag in ("loyalty", "spillover"):
        lst = [it["t"] for it in f[tag]]
        bounds = []  # (label, upper_round, n_in_snapshot)
        for label, up, snap in SNAPS:
            if name in snap:
                s = [it["t"] for it in snap[name][tag]]
                mism = [i for i, (a, b) in enumerate(zip(s, lst[:len(s)])) if a != b]
                if len(s) > len(lst) or (mism and not (name == "여자친구" and tag == "spillover" and len(mism) == 1)):
                    violations.append((name, tag, label, mism[:3]))
                bounds.append((label, up, len(s)))
        for idx, t in enumerate(lst):
            b = next(((label, up, n) for label, up, n in bounds if idx < n), None)
            if b:
                label, up, _ = b
                lo = {"≤r13": 1, "r14∼r22": 14, "r23∼r39": 23}[label]
                src = {"≤r13": "r13 스냅샷", "r14∼r22": "r22 백업", "r23∼r39": "동결 근사 복원본"}[label]
                lo = max(lo, entry_r); label = label if entry_r <= lo else f"r{entry_r}∼r{up}"
            else:
                lo, up, src = max(41, entry_r), 72, "라이브 코퍼스(스냅샷 이후)"
                label = "r41∼r72" if entry_r <= 41 else f"r{entry_r}∼r72"
            rows.append({"fandom": name, "bullet_type": tag, "idx": idx, "text_sha1": sha1(t), "added_bin": label, "bin_lower_round": lo, "bin_upper_round": up, "bin_source": src})
out = D / "bullet_provenance_v7.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# --- 검증: 구간 누적 건수 + 제거 팬덤의 스냅샷 건수 = 스냅샷 총건수
from collections import Counter
cum = {}
for label, up, snap in SNAPS:
    n_live = sum(1 for r in rows if r["bin_upper_round"] <= up)
    n_removed = sum(len(snap[n]["loyalty"]) + len(snap[n]["spillover"]) for n in snap if n not in live)
    cum[label] = (n_live, n_removed, n_live + n_removed, sum(len(f["loyalty"]) + len(f["spillover"]) for f in snap.values()))
print("접두어 위반:", violations or "없음(여자친구 r56 수정 1건은 허용)")
for label, (a, b, c, tot) in cum.items():
    print(f"  {label}: 라이브 불릿 {a:,} + 제거 팬덤 분 {b:,} = {c:,} vs 스냅샷 {tot:,} → {'일치' if c == tot else '불일치'}")
print("구간별:", dict(Counter(r["added_bin"] for r in rows)))
assert not violations and all(c == tot for _, _, c, tot in cum.values())
print("wrote", out, len(rows))
