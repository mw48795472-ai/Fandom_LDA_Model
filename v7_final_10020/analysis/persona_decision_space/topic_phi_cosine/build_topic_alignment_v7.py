# -*- coding: utf-8 -*-
"""L8 — 토픽 대응 자동화와 라벨 규칙 고정.
적합마다 토픽 번호가 임의로 매겨지므로, 모델 쌍마다 토픽을 자동으로 대응시킨다.
  · φ가 둘 다 있는 쌍: 공통 어휘 위 φ 벡터의 코사인 유사도 → 헝가리안 1:1 대응 (+ 상위 10단어 Jaccard 병기)
  · 한쪽에 상위 10단어만 남은 쌍(동결 스냅샷·라이브 원본 참고 재적합): 상위 10단어 Jaccard → 헝가리안 1:1 대응 + '가장 가까운 토픽'(최대 겹침, 1:1 아님)
라벨 규칙: 자동 라벨 = 상위 4단어를 '·'로 이은 뒤 '형' (예: 기록·1위·발매·차트형). 사람이 붙인 동결 라벨(topic_cards_v7.json)과 나란히 적는다.

모델:
  A frozen_snapshot_k10   data/v7_final/lda_v6_diagnostics_frozen_v7_40.json (상위 10단어만, 동결 7,350건)
  B live_k10              이 폴더 lda_phi_k10_v7_final.csv (φ, 10,020건·구 토크나이저 9,954문서)
  C frozen_refit_k10      frozen_v7_40/lda_phi_k10_v7_40.csv (φ, 동결 근사 7,326건·재구성 토크나이저)
  D live_reference_k8     data/v7_final/lda_v6_diagnostics_live_reference_v7.json (상위 10단어만, 라이브 원본 참고 재적합 10,018문서)
  E live_k8               이 폴더 lda_phi_k8_v7_final.csv (φ)
출력 (topic_alignment/): topic_alignment_v7.csv (쌍·방법·대응·점수 long form), topic_auto_labels_v7.csv, topic_alignment_summary_v7.json, TOPIC_ALIGNMENT_V7.md,
      그리고 ../TOPIC_PHI_COSINE_DISTANCE_V7.md 6절의 겹침 표를 마커(<!-- ALIGNMENT TABLE BEGIN/END -->) 사이에 다시 쓴다.
실행: python build_topic_alignment_v7.py
"""
import csv, json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
D = REPO / "data" / "v7_final"
OUT = HERE / "topic_alignment"; OUT.mkdir(exist_ok=True)

def phi_wide(path):
    df = pd.read_csv(path, index_col=0); df.index = [str(i) for i in df.index]
    return df

def top_words_from_phi(df, n=10):
    return {t: list(df.loc[t].sort_values(ascending=False).index[:n]) for t in df.index}

def norm_tid(t):  # 'T3'/'3' → '3'
    return str(t).lstrip("TK")

diag_A = json.load(open(D / "lda_v6_diagnostics_frozen_v7_40.json", encoding="utf-8"))
diag_D = json.load(open(D / "lda_v6_diagnostics_live_reference_v7.json", encoding="utf-8"))
cards = {c["topic_id"].lstrip("K"): c["topic_name"] for c in json.load(open(D / "topic_cards_v7.json", encoding="utf-8"))}
phi_B = phi_wide(HERE / "lda_phi_k10_v7_final.csv"); phi_C = phi_wide(HERE / "frozen_v7_40" / "lda_phi_k10_v7_40.csv"); phi_E = phi_wide(HERE / "lda_phi_k8_v7_final.csv")
for df in (phi_B, phi_C, phi_E): df.index = [norm_tid(i) for i in df.index]

MODELS = {
    "A_frozen_snapshot_k10": {"top": {k: v for k, v in diag_A["topics_top_words"].items()}, "phi": None, "f": diag_A["topic_to_factor"], "flabel": diag_A["factor_labels"], "human": cards,
                              "desc": "동결 스냅샷 K=10 (7,350건, 상위 10단어만 저장됨)"},
    "B_live_k10": {"top": top_words_from_phi(phi_B), "phi": phi_B, "desc": "이 폴더 K=10 (10,020건, 구 토크나이저 9,954문서, φ 있음)"},
    "C_frozen_refit_k10": {"top": top_words_from_phi(phi_C), "phi": phi_C, "desc": "frozen_v7_40/ K=10 (동결 근사 7,326건, 재구성 토크나이저, φ 있음)"},
    "D_live_reference_k8": {"top": {k: v for k, v in diag_D["topics_top_words"].items()}, "phi": None, "f": diag_D["topic_to_factor"], "flabel": diag_D["factor_labels"],
                            "desc": "라이브 원본 참고 재적합 K=8 (10,018문서, 상위 10단어만 저장됨)"},
    "E_live_k8": {"top": top_words_from_phi(phi_E), "phi": phi_E, "desc": "이 폴더 K=8 (10,020건, 구 토크나이저, φ 있음)"},
}
def auto_label(words): return "·".join(words[:4]) + "형"

# --- 자동 라벨 표
lab_rows = []
for m, spec in MODELS.items():
    for t, words in sorted(spec["top"].items(), key=lambda kv: int(kv[0])):
        human = spec.get("human", {}).get(t, "")
        f = spec.get("f", {}).get(t); flabel = spec["flabel"][str(f)] if f is not None and "flabel" in spec else ""
        lab_rows.append({"model": m, "topic": t, "auto_label": auto_label(words), "human_label": human, "F": f if f is not None else "", "F_label": flabel, "top10": " ".join(words)})
pd.DataFrame(lab_rows).to_csv(OUT / "topic_auto_labels_v7.csv", index=False, encoding="utf-8-sig")

# --- 대응
def jaccard_matrix(ta, tb):
    A = sorted(ta, key=int); B = sorted(tb, key=int)
    M = np.array([[len(set(ta[a]) & set(tb[b])) / len(set(ta[a]) | set(tb[b])) for b in B] for a in A]); O = np.array([[len(set(ta[a]) & set(tb[b])) for b in B] for a in A])
    return A, B, M, O
def cosine_matrix(pa, pb):
    shared = pa.columns.intersection(pb.columns)
    X = pa[shared].to_numpy(); Y = pb[shared].to_numpy()
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12); Y = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-12)
    return list(pa.index), list(pb.index), X @ Y.T, len(shared)

PAIRS = [("A_frozen_snapshot_k10", "B_live_k10"), ("A_frozen_snapshot_k10", "C_frozen_refit_k10"), ("A_frozen_snapshot_k10", "D_live_reference_k8"),
         ("B_live_k10", "C_frozen_refit_k10"), ("D_live_reference_k8", "E_live_k8"), ("B_live_k10", "E_live_k8")]
align_rows, summary = [], {}
for a, b in PAIRS:
    sa, sb = MODELS[a], MODELS[b]
    A, B, J, O = jaccard_matrix(sa["top"], sb["top"])
    methods = {"jaccard_top10": (J, O)}
    if sa["phi"] is not None and sb["phi"] is not None:
        Ai, Bi, Cm, n_shared = cosine_matrix(sa["phi"], sb["phi"])
        # 코사인 행렬을 Jaccard 행렬의 토픽 순서에 맞춘다
        Cm = pd.DataFrame(Cm, index=Ai, columns=Bi).loc[A, B].to_numpy(); methods["phi_cosine"] = (Cm, O)
    pair = f"{a}→{b}"; summary[pair] = {}
    for method, (S, Ov) in methods.items():
        r, c = linear_sum_assignment(-S)
        hung = {A[i]: B[j] for i, j in zip(r, c)}
        for i, ta in enumerate(A):
            j_near = int(np.argmax(S[i])); tb_near = B[j_near]
            tb_h = hung.get(ta)
            align_rows.append({"pair": pair, "method": method, "src_model": a, "src_topic": ta, "src_auto_label": auto_label(sa["top"][ta]), "src_human_label": sa.get("human", {}).get(ta, ""),
                               "nearest_topic": tb_near, "nearest_score": round(float(S[i, j_near]), 4), "nearest_overlap10": int(Ov[i, j_near]),
                               "hungarian_topic": tb_h if tb_h is not None else "", "hungarian_score": round(float(S[i, B.index(tb_h)]), 4) if tb_h is not None else "",
                               "hungarian_overlap10": int(Ov[i, B.index(tb_h)]) if tb_h is not None else "", "tgt_auto_label": auto_label(sb["top"][tb_h]) if tb_h is not None else "",
                               "same_as_nearest": (tb_h == tb_near) if tb_h is not None else ""})
        hs = [float(S[i, c[k]]) for k, i in enumerate(r)]
        summary[pair][method] = {"n_src": len(A), "n_tgt": len(B), "hungarian_mean": round(float(np.mean(hs)), 4), "hungarian_min": round(min(hs), 4), "hungarian_max": round(max(hs), 4),
                                 "hungarian_overlap10": [int(Ov[i, c[k]]) for k, i in enumerate(r)], "nearest_equals_hungarian": int(sum(1 for i, ta in enumerate(A) if hung.get(ta) == B[int(np.argmax(S[i]))])),
                                 **({"n_shared_vocab": n_shared} if method == "phi_cosine" else {})}
pd.DataFrame(align_rows).to_csv(OUT / "topic_alignment_v7.csv", index=False, encoding="utf-8-sig")

# --- 사람 라벨 vs 자동 라벨 (동결): 괄호 안 키워드가 상위 10단어에 몇 개 들어 있나
human_check = []
for t, name in sorted(cards.items(), key=lambda kv: int(kv[0])):
    kws = name[name.find("(") + 1:name.rfind(")")].split("·") if "(" in name else []
    top = MODELS["A_frozen_snapshot_k10"]["top"][t]
    human_check.append({"topic": f"K{t}", "human_label": name, "auto_label": auto_label(top), "label_keywords_in_top10": f"{sum(k in top for k in kws)}/{len(kws)}", "label_keywords_in_top4": f"{sum(k in top[:4] for k in kws)}/{len(kws)}"})
json.dump({"rule": {"auto_label": "상위 4단어를 '·'로 이어 붙이고 '형'을 붙인다", "phi_cosine": "공통 어휘 위 φ 행 벡터의 코사인 유사도, 헝가리안 1:1", "jaccard_top10": "상위 10단어 집합 Jaccard, 헝가리안 1:1 + 최대 겹침(nearest)"},
           "models": {m: s["desc"] for m, s in MODELS.items()}, "pairs": summary, "frozen_human_label_check": human_check},
          open(OUT / "topic_alignment_summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# --- 6절 표 (A→B, jaccard nearest) — 문서 마커 사이에 다시 쓴다
def sec6_table():
    rows = [r for r in align_rows if r["pair"] == "A_frozen_snapshot_k10→B_live_k10" and r["method"] == "jaccard_top10"]
    fl = MODELS["A_frozen_snapshot_k10"]["flabel"]; f = MODELS["A_frozen_snapshot_k10"]["f"]
    md = ["| 동결 토픽 | 동결 상위 10단어 | 동결 F | 가장 가까운 T (겹침) | 헝가리안 1:1 T (겹침) | 그 T의 상위 10단어 |", "|---|---|---|---|---|---|"]
    for r in rows:
        t = r["src_topic"]; ft = f[t]
        md.append(f"| K{t} {cards[t]} | {', '.join(MODELS['A_frozen_snapshot_k10']['top'][t])} | F{ft} {fl[str(ft)]} | T{r['nearest_topic']} ({r['nearest_overlap10']}/10) | T{r['hungarian_topic']} ({r['hungarian_overlap10']}/10) | {', '.join(MODELS['B_live_k10']['top'][r['hungarian_topic']])} |")
    return "\n".join(md)
doc = HERE / "TOPIC_PHI_COSINE_DISTANCE_V7.md"; s = doc.read_text(encoding="utf-8")
B0, B1 = "<!-- ALIGNMENT TABLE BEGIN (build_topic_alignment_v7.py 가 생성) -->", "<!-- ALIGNMENT TABLE END -->"
if B0 in s:
    s = s[:s.index(B0) + len(B0)] + "\n" + sec6_table() + "\n" + s[s.index(B1):]
    doc.write_text(s, encoding="utf-8"); print("6절 표 갱신")
else:
    print("경고: 문서에 마커가 없어 6절 표를 갱신하지 않음")

# --- MD
md = ["# 토픽 대응 자동화 (L8) — 번호가 아니라 φ·상위어로 잇는다\n",
      "적합마다 토픽 번호가 임의로 매겨지므로 모델 쌍의 토픽은 번호로 대응하지 않는다. 이 폴더는 `build_topic_alignment_v7.py`가 다섯 모델의 토픽을 자동으로 대응시킨 결과다. "
      "φ가 둘 다 있는 쌍은 공통 어휘 위 φ 코사인 유사도로, 한쪽에 상위 10단어만 남은 쌍(동결 스냅샷·라이브 원본 참고 재적합)은 상위 10단어 Jaccard로 헝가리안 1:1 대응을 잡는다. "
      "'가장 가까운 토픽'(최대 겹침, 1:1 아님)도 같이 적어 6절 표와 이어지게 했다. 자동 라벨 규칙은 **상위 4단어를 '·'로 잇고 '형'** 이다.\n",
      "## 1. 모델\n", "| 코드 | 모델 | φ |\n|---|---|---|"]
for m, sp in MODELS.items(): md.append(f"| {m} | {sp['desc']} | {'있음' if sp['phi'] is not None else '상위 10단어만'} |")
md.append("\n## 2. 쌍별 요약\n")
md.append("| 쌍 | 방법 | 헝가리안 평균 / 최소 / 최대 | 대응별 상위 10단어 겹침 | nearest = 헝가리안 | 공통 어휘 |\n|---|---|---|---|---|---|")
for pair, ms in summary.items():
    for method, v in ms.items():
        md.append(f"| {pair} | {method} | {v['hungarian_mean']} / {v['hungarian_min']} / {v['hungarian_max']} | {v['hungarian_overlap10']} | {v['nearest_equals_hungarian']}/{v['n_src']} | {v.get('n_shared_vocab', '—')} |")
md.append("\n## 3. 동결 스냅샷 → 이 폴더 K=10 (6절 표의 자동 생성본)\n")
md.append(sec6_table())
md.append("\n## 4. φ 코사인 대응: 이 폴더 K=10 ↔ 동결 근사 재적합 K=10\n")
md.append("| B 토픽 (자동 라벨) | C 토픽 (자동 라벨) | φ 코사인 | 상위 10단어 겹침 | Jaccard 헝가리안과 같은 대응 |\n|---|---|---|---|---|")
jrows = {r["src_topic"]: r for r in align_rows if r["pair"] == "B_live_k10→C_frozen_refit_k10" and r["method"] == "jaccard_top10"}
for r in [r for r in align_rows if r["pair"] == "B_live_k10→C_frozen_refit_k10" and r["method"] == "phi_cosine"]:
    md.append(f"| T{r['src_topic']} {r['src_auto_label']} | T{r['hungarian_topic']} {r['tgt_auto_label']} | {r['hungarian_score']} | {r['hungarian_overlap10']}/10 | {'예' if jrows[r['src_topic']]['hungarian_topic'] == r['hungarian_topic'] else '아니오'} |")
md.append("\n## 5. 사람 라벨 vs 자동 라벨 (동결 K=10)\n")
md.append("| 토픽 | 사람 라벨 (topic_cards_v7.json) | 자동 라벨 (상위 4단어) | 라벨 키워드가 상위 10 / 상위 4 안에 |\n|---|---|---|---|")
for h in human_check: md.append(f"| {h['topic']} | {h['human_label']} | {h['auto_label']} | {h['label_keywords_in_top10']} / {h['label_keywords_in_top4']} |")
md.append("\n## 6. 읽는 법과 한계\n")
md.append("1. **동결 스냅샷과의 대응은 상위 10단어 Jaccard뿐이다.** 동결 φ가 없으므로(L3) 코사인 대응은 불가능하다. Jaccard는 열 단어 집합의 겹침이라 거칠고, 동결 토픽 둘이 라이브 토픽 하나로 몰리는 경우(nearest ≠ 헝가리안)가 그 신호다.")
md.append("2. **φ 코사인은 공통 어휘에서만 잰다.** B(구 토크나이저)와 C(재구성 토크나이저)는 어휘가 달라 공통 어휘 위에서 비교한다. 두 모델은 코퍼스도 다르므로(10,020 vs 7,326) 대응 점수는 '같은 토픽인가'가 아니라 '가장 닮은 토픽이 무엇인가'다.")
md.append("3. **자동 라벨은 규칙이지 해석이 아니다.** 상위 4단어 결합은 재현 가능하지만 사람 라벨(예: 팬클럽공식활동형)만큼 읽기 쉽지 않다. 5절 표가 둘의 거리를 보여준다: 사람 라벨의 괄호 키워드가 상위 4단어 안에 몇 개나 있는지.")
md.append("4. 시드가 바뀌면 토픽 자체가 바뀐다(`../seed_stability/`, 시드 간 Jaccard 중앙값 0.39∼0.40). 이 대응표는 각 모델의 seed 0 결과 사이의 대응이다.\n")
md.append("## 7. 파일\n")
md.append("| 파일 | 내용 |\n|---|---|\n| `topic_alignment_v7.csv` | 쌍 × 방법 × 원 토픽별: nearest 토픽·점수·겹침, 헝가리안 토픽·점수·겹침, 자동 라벨 |\n| `topic_auto_labels_v7.csv` | 다섯 모델 모든 토픽의 자동 라벨·사람 라벨·F·상위 10단어 |\n| `topic_alignment_summary_v7.json` | 규칙·모델·쌍별 요약·사람 라벨 점검 |\n| `../build_topic_alignment_v7.py` | 이 폴더와 `../TOPIC_PHI_COSINE_DISTANCE_V7.md` 6절 표를 만드는 스크립트 |\n")
(OUT / "TOPIC_ALIGNMENT_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT, len(align_rows), "alignment rows")
for pair, ms in summary.items():
    for method, v in ms.items(): print(f"  {pair} {method}: mean {v['hungarian_mean']} overlap {v['hungarian_overlap10']} nearest=hung {v['nearest_equals_hungarian']}/{v['n_src']}")
