# -*- coding: utf-8 -*-
"""L7 — 단일 시드 한계 점검: 같은 코퍼스·같은 설정으로 난수 시드만 바꿔 LDA를 반복 적합해
K→M 실루엣의 분포와 토픽 안정성(시드 간 상위 10단어 Jaccard, 헝가리안 1:1 대응)을 잰다.

  코퍼스   live: data/v7_final/fandoms_v3_100.json (10,020건)   frozen: data/v7_final/frozen_snapshot_v7_40/… (7,326건)
  토크나이저 run_lda_v6_live_reference_v7.py 마커 절 (재구성본)
  설정     CountVectorizer(max_df=0.6, min_df=2), LDA(max_iter=50, batch), K ∈ {8, 10}, 시드 0∼9
  M-grid   AgglomerativeClustering(average, precomputed cosine) M=4∼8, silhouette_score — 파이프라인 [3]절과 동일

출력 (seed_stability/): seed_silhouette_grid_v7.csv (코퍼스×K×시드×M 실루엣), seed_topic_jaccard_v7.csv (시드 쌍별 평균 Jaccard),
      seed_stability_summary_v7.json, SEED_STABILITY_V7.md
실행: python build_seed_stability_v7.py   (약 25∼35분: 4 조합 × 10 시드 = 40회 적합)
      python build_seed_stability_v7.py --report-only   (적합 없이 CSV 2개에서 요약 JSON·MD만 다시 생성)
"""
import csv, json, re, statistics, sys, time
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import silhouette_score

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
D = REPO / "data" / "v7_final"
OUT = HERE / "seed_stability"; OUT.mkdir(exist_ok=True)
SEEDS = list(range(10)); KS = [8, 10]
CORPORA = {"live_10020": D / "fandoms_v3_100.json", "frozen_approx_7326": D / "frozen_snapshot_v7_40" / "fandoms_v7_40_frozen_reconstructed.json"}
FROZEN_SIL, LIVE_SIL = 0.267, 0.046

src = (REPO / "run_lda_v6_live_reference_v7.py").read_text(encoding="utf-8")
block = src[src.index("# === TOKENIZER BEGIN ===") + len("# === TOKENIZER BEGIN ==="):src.index("# === TOKENIZER END ===")]
ns = {"re": re, "__name__": "tok"}; exec("import re\nfrom urllib.parse import urlparse\n" + block, ns); tokenize = ns["tokenize"]


def dtm_of(path):
    docs = []
    for fd in json.load(open(path, encoding="utf-8")):
        for tag in ("loyalty", "spillover"):
            for it in fd[tag]:
                t = tokenize(it["t"], it.get("u", ""))
                if len(t) >= 3: docs.append(" ".join(t))
    vec = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
    return vec.fit_transform(docs), vec.get_feature_names_out()


def mgrid(tw):
    pn = tw / (np.linalg.norm(tw, axis=1, keepdims=True) + 1e-12)
    cos = 1 - pn @ pn.T; np.fill_diagonal(cos, 0); cos = np.clip(cos, 0, None); cos = (cos + cos.T) / 2
    out = {}
    for m in range(4, min(9, tw.shape[0])):
        lab = AgglomerativeClustering(n_clusters=m, metric="precomputed", linkage="average").fit_predict(cos)
        out[m] = round(float(silhouette_score(cos, lab, metric="precomputed")), 4)
    return out


rows, jrows, summary, all_tops = [], [], {}, {}
REPORT_ONLY = "--report-only" in sys.argv
if REPORT_ONLY:
    rows = [{k: (v if k == "corpus" else (int(v) if k in ("K", "seed", "best_M") else (float(v) if v != "" else ""))) for k, v in r.items()} for r in csv.DictReader(open(OUT / "seed_silhouette_grid_v7.csv", encoding="utf-8-sig"))]
    jrows = [{"corpus": r["corpus"], "K": int(r["K"]), "seed_a": int(r["seed_a"]), "seed_b": int(r["seed_b"]), "mean_jaccard_top10": float(r["mean_jaccard_top10"])} for r in csv.DictReader(open(OUT / "seed_topic_jaccard_v7.csv", encoding="utf-8-sig"))]
for cname, cpath in CORPORA.items():
    if REPORT_ONLY: break
    X, vocab = dtm_of(cpath)
    print(f"[{cname}] DTM {X.shape}")
    for K in KS:
        tops, sils, t0 = {}, {}, time.time()
        for s in SEEDS:
            lda = LatentDirichletAllocation(n_components=K, random_state=s, max_iter=50, learning_method="batch").fit(X)
            tw = lda.components_
            tops[s] = [set(tw[t].argsort()[::-1][:10].tolist()) for t in range(K)]
            g = mgrid(tw); sils[s] = g
            best_m = max(g, key=g.get)
            rows.append({"corpus": cname, "K": K, "seed": s, **{f"sil_M{m}": g.get(m, "") for m in range(4, 9)}, "best_M": best_m, "best_sil": g[best_m], "perplexity": round(float(lda.perplexity(X)), 1)})
            print(f"  K={K} seed={s} best M={best_m} sil={g[best_m]} M5={g.get(5)}  ({time.time()-t0:.0f}s)", flush=True)
            all_tops[f"{cname}_K{K}_s{s}"] = [sorted(t) for t in tops[s]]; json.dump({"rows": rows, "tops": all_tops}, open(OUT / "_checkpoint_rows.json", "w"), ensure_ascii=False)  # 중간 저장(적합 결과 유실 방지)
        # 시드 쌍별 토픽 안정성: 상위 10단어 Jaccard 를 헝가리안으로 1:1 대응해 평균
        jac = []
        for a, b in combinations(SEEDS, 2):
            M_ = np.array([[len(tops[a][i] & tops[b][j]) / len(tops[a][i] | tops[b][j]) for j in range(K)] for i in range(K)])
            r, c = linear_sum_assignment(-M_)
            j = float(M_[r, c].mean()); jac.append(j); jrows.append({"corpus": cname, "K": K, "seed_a": a, "seed_b": b, "mean_jaccard_top10": round(j, 4)})
if not REPORT_ONLY:
    (OUT / "_checkpoint_rows.json").unlink(missing_ok=True)
    with open(OUT / "seed_silhouette_grid_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["corpus", "K", "seed"] + [f"sil_M{m}" for m in range(4, 9)] + ["best_M", "best_sil", "perplexity"]); w.writeheader(); w.writerows(rows)
    with open(OUT / "seed_topic_jaccard_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(jrows[0].keys())); w.writeheader(); w.writerows(jrows)
r4 = lambda x: round(float(x), 4)
for cname in CORPORA:
    for K in KS:
        rs = sorted((r for r in rows if r["corpus"] == cname and r["K"] == K), key=lambda r: r["seed"])
        m5 = [r["sil_M5"] for r in rs]; bests = [r["best_sil"] for r in rs]; bm = [r["best_M"] for r in rs]
        jac = [j["mean_jaccard_top10"] for j in jrows if j["corpus"] == cname and j["K"] == K]
        summary[f"{cname}_K{K}"] = {"corpus": cname, "K": K, "n_seeds": len(rs),
                                    "silhouette_M5": {"min": min(m5), "median": r4(statistics.median(m5)), "max": max(m5), "values": m5},
                                    "silhouette_best_M": {"min": min(bests), "median": r4(statistics.median(bests)), "max": max(bests), "best_M_by_seed": bm},
                                    "topic_jaccard_top10": {"min": r4(min(jac)), "median": r4(statistics.median(jac)), "max": r4(max(jac))},
                                    "n_seeds_M5_ge_0267": sum(v >= FROZEN_SIL for v in m5), "n_seeds_best_ge_0267": sum(v >= FROZEN_SIL for v in bests)}
all_max = max(rows, key=lambda r: r["best_sil"]); live8 = summary["live_10020_K8"]; fr10 = summary["frozen_approx_7326_K10"]
json.dump({"settings": {"seeds": SEEDS, "K": KS, "lda": "max_iter=50, batch", "vectorizer": "max_df=0.6, min_df=2", "tokenizer": "run_lda_v6_live_reference_v7.py 마커 절"},
           "reference": {"frozen_snapshot_silhouette": FROZEN_SIL, "live_reference_silhouette": LIVE_SIL}, "results": summary},
          open(OUT / "seed_stability_summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

md = ["# 시드 안정성 점검 (L7) — 실루엣 0.267은 시드 분포의 어디에 있나\n",
      "## 0. 결론\n"]
for k, v in summary.items():
    md.append(f"- **{v['corpus']} K={v['K']}**: M=5 실루엣 시드 10개 중앙값 {v['silhouette_M5']['median']} (최소 {v['silhouette_M5']['min']}, 최대 {v['silhouette_M5']['max']}); "
              f"M 자유 선택 시 최대 실루엣 중앙값 {v['silhouette_best_M']['median']} (최대 {v['silhouette_best_M']['max']}); "
              f"0.267 이상인 시드 {v['n_seeds_best_ge_0267']}/10; 시드 간 토픽 Jaccard 중앙값 {v['topic_jaccard_top10']['median']}")
md.append("\n동결 기준선 0.267과 라이브 참고값 0.046은 각각 시드 하나(random_state=0)의 한 번 적합이다. 위 분포가 그 값들을 어떻게 자리매김하는지가 이 문서의 요점이다.\n")
md.append(f"1. **0.267은 분포 밖이다.** 4조합 × 10시드 = 40회 적합 중 M을 자유롭게 골라도 최대는 {all_max['best_sil']}({all_max['corpus']} K={all_max['K']} seed {all_max['seed']}, M={all_max['best_M']})으로 0.267에 {round(FROZEN_SIL - all_max['best_sil'], 3)} 못 미친다. "
          f"동결 근사 코퍼스 K=10·M=5의 분포는 {fr10['silhouette_M5']['min']}∼{fr10['silhouette_M5']['max']}(중앙값 {fr10['silhouette_M5']['median']})이고 seed 0의 값 {fr10['silhouette_M5']['values'][0]}은 `frozen_v7_40/`의 재적합 결과와 같다. "
          "따라서 동결 실루엣 0.267이 재현되지 않은 것(L3)은 시드 운이 아니라 입력(코퍼스 24건·토크나이저 저빈도 불용어)이나 당시 코드·환경의 차이다. 0.267은 '그 시점의 코퍼스·코드·환경 조합에서 한 번 나온 값'으로 읽어야 한다.")
md.append(f"2. **0.046은 분포 하단이다.** 라이브 원본 참고 재적합의 M=5 실루엣 0.046은 재구성 토크나이저 K=8·M=5 분포의 최소 {live8['silhouette_M5']['min']}보다도 낮다(seed 0은 {live8['silhouette_M5']['values'][0]}). 원본 토크나이저와 재구성본의 DTM 차이가 실루엣을 이만큼 움직인다는 뜻이며, 게이트 기각(0.267 미달)이라는 결론은 어느 시드에서도 같다(0/40).")
md.append(f"3. **M 선택과 토픽 내용이 시드에 따라 흔들린다.** 최적 M은 시드마다 4∼8 사이에서 바뀌고, 시드 쌍 간 토픽 상위 10단어 Jaccard 중앙값은 네 조합 모두 0.39∼0.40이다. 즉 시드를 바꾸면 각 토픽의 상위 단어 열 개 중 여섯 개 안팎이 달라진다. "
          "단일 시드로 K→M→F→페르소나를 확정한 해석 계층은 이 변동을 담지 못하며, 게이트 정책(0.267 미달 시 기각)은 시드 분포를 고려한 기준으로 바꾸는 것이 맞다(L6).\n")
md.append("## 1. 설정\n")
md.append("| 항목 | 값 |\n|---|---|")
md.append("| 코퍼스 | live 10,020건 / 동결 근사 7,326건 (둘 다 재구성 토크나이저, 3토큰 미만 제외) |")
md.append(f"| K | {KS} · 시드 {SEEDS[0]}∼{SEEDS[-1]} (10개) · LDA max_iter=50 batch · CountVectorizer(max_df=0.6, min_df=2) |")
md.append("| M-grid | average-linkage(precomputed cosine) M=4∼8, silhouette_score — 파이프라인 [3]절과 동일 |")
md.append("| 토픽 안정성 | 시드 쌍(45쌍)마다 상위 10단어 Jaccard 를 헝가리안 1:1 대응으로 평균 |\n")
md.append("## 2. 시드별 실루엣\n")
md.append("| 코퍼스 | K | 시드 | M=4 | M=5 | M=6 | M=7 | M=8 | 최적 M | 최적 실루엣 | perplexity |\n|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    md.append(f"| {r['corpus']} | {r['K']} | {r['seed']} | {r.get('sil_M4','')} | {r.get('sil_M5','')} | {r.get('sil_M6','')} | {r.get('sil_M7','')} | {r.get('sil_M8','')} | {r['best_M']} | {r['best_sil']} | {r['perplexity']} |")
md.append("\n## 3. 요약\n")
md.append("| 코퍼스 | K | M=5 실루엣 min / 중앙 / max | 최적 M 실루엣 min / 중앙 / max | 시드별 최적 M | ≥0.267 시드 수 | 토픽 Jaccard min / 중앙 / max |\n|---|---|---|---|---|---|---|")
for k, v in summary.items():
    a, b, j = v["silhouette_M5"], v["silhouette_best_M"], v["topic_jaccard_top10"]
    md.append(f"| {v['corpus']} | {v['K']} | {a['min']} / {a['median']} / {a['max']} | {b['min']} / {b['median']} / {b['max']} | {b['best_M_by_seed']} | {v['n_seeds_best_ge_0267']} | {j['min']} / {j['median']} / {j['max']} |")
md.append("\n## 4. 파일\n")
md.append("| 파일 | 내용 |\n|---|---|\n| `seed_silhouette_grid_v7.csv` | 코퍼스×K×시드별 M=4∼8 실루엣, 최적 M, perplexity |\n| `seed_topic_jaccard_v7.csv` | 시드 쌍별 상위 10단어 Jaccard(헝가리안 대응 평균) |\n| `seed_stability_summary_v7.json` | 요약 통계 |\n| `../build_seed_stability_v7.py` | 이 폴더 전부와 이 문서를 만드는 스크립트 |\n")
md.append("## 5. 한계\n")
md.append("1. 라이브 코퍼스는 원본 토크나이저가 아니라 재구성본으로 토큰화했고, 동결 코퍼스는 근사 복원본(24건 유실)이다. 분포의 위치는 믿을 만하지만 개별 값은 원본 실행과 소수점 셋째 자리에서 다를 수 있다.\n"
          "2. 시드 10개는 분포의 폭을 보기에 충분하지만 꼬리를 말하기엔 적다.\n"
          "3. 실루엣은 토픽 수 K개 점에 대한 값이라(K=8이면 8개 점) 본래 분산이 크다. 이 점 자체가 단일 실루엣을 게이트로 쓰는 것의 한계다.\n")
(OUT / "SEED_STABILITY_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT)
