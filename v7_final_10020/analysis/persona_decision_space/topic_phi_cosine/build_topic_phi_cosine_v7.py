# -*- coding: utf-8 -*-
"""LDA 토픽-단어 분포(φ)와 토픽 간 코사인 거리 행렬, average-linkage 병합 트리를 최종 코퍼스 10,020건에서 실제로 산출해 CSV·MD로 남긴다.

배경: Persona_결정공간.html 의 덴드로그램은 동결 스냅샷(v7-40, 7,350건, K=10)의 φ 로 만든 코사인 거리 행렬에서 나왔지만,
그 φ·거리 행렬·7,350건 코퍼스는 저장소에 없다(덴드로그램의 병합 높이만 HTML 데이터에 남아 있다). 이 스크립트는 저장소에 실제로
있는 파이프라인(run_lda_v6.py)의 토크나이저·CountVectorizer·LDA 설정을 그대로 가져와 최종 코퍼스에 K=10(동결 구조와 같은 K)과
K=8(최종 코퍼스 참고 재적합 승자)을 적합하고, 파이프라인 [3]절과 같은 방법으로 코사인 거리·M-grid 실루엣·병합 트리를 계산한다.

  - tokenize()·PARTICLES·STOPWORDS·ENGLISH_STOPWORDS 는 run_lda_v6.py 소스에서 ast 로 잘라 와 그대로 실행한다(재구현 아님).
  - CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\\b\\w+\\b"), 3토큰 미만 불릿 제외 — 파이프라인 [1]절과 동일.
  - LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method="batch") — [2]절과 동일.
  - φ_norm = components_ / ||row||, cos_dist = 1 − φ_norm·φ_normᵀ (대각 0, 음수 클립) — [3]절과 동일.
  - AgglomerativeClustering(metric="precomputed", linkage="average") 로 M=4∼8 실루엣, scipy linkage(average) 로 병합 트리.

출력 (같은 폴더, K별 접미사 _k10 / _k8):
  lda_phi_{k}_v7_final.csv                 φ (토픽 × 어휘, 행 합 = 1)          — 넓은 표
  lda_phi_top50_{k}_v7_final.csv           토픽별 상위 50단어(long)             — 읽기용
  topic_cosine_distance_{k}_v7_final.csv   토픽 간 코사인 거리 행렬 (K×K)
  topic_linkage_average_{k}_v7_final.csv   average-linkage 병합 기록 (id, left, right, height, size)
  m_grid_silhouette_{k}_v7_final.csv       M=4∼8 실루엣과 M별 토픽 배정
  TOPIC_PHI_COSINE_DISTANCE_V7.md          방법·코드·결과 정리(이 스크립트가 생성)

실행: python v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_phi_cosine_v7.py   (저장소 안 어느 폴더에서든, 1∼3분)
"""
import ast
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import silhouette_score

try:
    HERE = Path(__file__).resolve().parent
except NameError:
    HERE = Path.cwd()


def find_repo_root():
    for start in (HERE, Path.cwd()):
        for p in [start, *start.parents]:
            if (p / "run_lda_v6.py").exists() and (p / "data" / "v7_final" / "fandoms_v3_100.json").exists():
                return p
    raise SystemExit("저장소 루트를 찾지 못했습니다. GitHub 저장소(Fandom_LDA_Model)를 통째로 받은 폴더 안에서 실행하세요.")


REPO = find_repo_root()
DATA = REPO / "data" / "v7_final"
OUT_DIR = REPO / "v7_final_10020" / "analysis" / "persona_decision_space" / "topic_phi_cosine"
OUT_DIR.mkdir(parents=True, exist_ok=True)
K_LIST = [10, 8]

# --- 1. run_lda_v6.py 에서 토크나이저 소스를 그대로 가져온다 ---------------------------------
src = (REPO / "run_lda_v6.py").read_text(encoding="utf-8")
tree = ast.parse(src)
pieces = []
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("PARTICLES", "STOPWORDS", "ENGLISH_STOPWORDS"):
        pieces.append(ast.get_source_segment(src, node))
    if isinstance(node, ast.FunctionDef) and node.name == "tokenize":
        pieces.append(ast.get_source_segment(src, node))
assert len(pieces) == 4, "run_lda_v6.py 에서 PARTICLES/STOPWORDS/ENGLISH_STOPWORDS/tokenize 를 찾지 못함"
ns = {"re": __import__("re")}
exec("\n\n".join(pieces), ns)
tokenize = ns["tokenize"]

# --- 2. 코퍼스 → 문서(3토큰 미만 제외) → DTM  (파이프라인 [1]절과 동일) ----------------------
with open(DATA / "fandoms_v3_100.json", encoding="utf-8") as f:
    fandoms = json.load(f)
docs, meta = [], []
n_bullets = 0
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for item in fd.get(tag, []):
            n_bullets += 1
            toks = tokenize(item["t"])
            if len(toks) < 3:
                continue
            docs.append(" ".join(toks))
            meta.append((fd["fandom"], tag))
vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
X = vectorizer.fit_transform(docs)
vocab = vectorizer.get_feature_names_out()
print(f"[1] 불릿 {n_bullets:,}건 → 3토큰 이상 문서 {len(docs):,}건, 어휘 {len(vocab):,}개, DTM {X.shape}")

# 동결 스냅샷의 덴드로그램(HTML 내장) — 비교용
with open(DATA / "persona_decision_space_v7.json", encoding="utf-8") as f:
    frozen_dendro = json.load(f)["dendro"]
with open(DATA / "lda_v6_diagnostics_frozen_v7_40.json", encoding="utf-8") as f:
    frozen_diag = json.load(f)
with open(DATA / "lda_v6_diagnostics_live_reference_v7.json", encoding="utf-8") as f:
    live_diag = json.load(f)

results = {}
for K in K_LIST:
    t0 = time.time()
    lda = LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method="batch").fit(X)
    topic_word = lda.components_                                    # (K, V) — 파이프라인의 phi (비정규화)
    phi = topic_word / topic_word.sum(axis=1, keepdims=True)         # 행 합 1 인 확률 분포
    top_words = [[vocab[i] for i in topic_word[t].argsort()[::-1][:10]] for t in range(K)]
    labels = [f"T{t}({'·'.join(top_words[t][:4])})" for t in range(K)]

    # --- 3. 코사인 거리 (파이프라인 [3]절과 동일) ---
    phi_norm = topic_word / (np.linalg.norm(topic_word, axis=1, keepdims=True) + 1e-12)
    cos_dist = 1 - phi_norm @ phi_norm.T
    np.fill_diagonal(cos_dist, 0)
    cos_dist = np.clip(cos_dist, 0, None)
    cos_dist = (cos_dist + cos_dist.T) / 2                           # 부동소수 비대칭 제거(scipy squareform 요구)

    # --- 4. M-grid 실루엣 (AgglomerativeClustering average, precomputed) ---
    mgrid = []
    for m in range(4, min(9, K)):
        lab = AgglomerativeClustering(n_clusters=m, metric="precomputed", linkage="average").fit_predict(cos_dist)
        sil = silhouette_score(cos_dist, lab, metric="precomputed") if len(set(lab)) > 1 else float("nan")
        mgrid.append({"m": m, "silhouette": round(float(sil), 4), "labels": lab.tolist()})
    best = max(mgrid, key=lambda r: r["silhouette"])

    # --- 5. average-linkage 병합 트리 (scipy) ---
    Z = linkage(squareform(cos_dist, checks=False), method="average")
    merges = [{"id": K + i, "left": int(a), "right": int(b), "height": round(float(h), 6), "size": int(n)} for i, (a, b, h, n) in enumerate(Z)]
    leaf_order = dendrogram(Z, no_plot=True)["leaves"]
    heights = Z[:, 2]
    cut_height = float((heights[K - best["m"] - 1] + heights[K - best["m"]]) / 2)
    scipy_labels = fcluster(Z, t=best["m"], criterion="maxclust")
    print(f"[K={K}] 적합 {time.time()-t0:.0f}s | perplexity {lda.perplexity(X):.1f} | M-grid " +
          ", ".join(f"M={r['m']}:{r['silhouette']}" for r in mgrid) + f" → 최적 M={best['m']} (실루엣 {best['silhouette']})")
    for t in range(K):
        print(f"   T{t}: {', '.join(top_words[t][:8])}")

    sfx = f"k{K}"
    # φ 넓은 표
    with open(OUT_DIR / f"lda_phi_{sfx}_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["topic"] + list(vocab))
        for t in range(K):
            w.writerow([f"T{t}"] + [f"{v:.8g}" for v in phi[t]])
    # 상위 50단어 long
    with open(OUT_DIR / f"lda_phi_top50_{sfx}_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["topic", "rank", "word", "phi", "raw_weight"])
        for t in range(K):
            for r, i in enumerate(topic_word[t].argsort()[::-1][:50], 1):
                w.writerow([f"T{t}", r, vocab[i], f"{phi[t, i]:.6g}", f"{topic_word[t, i]:.4f}"])
    # 코사인 거리
    with open(OUT_DIR / f"topic_cosine_distance_{sfx}_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["topic"] + [f"T{t}" for t in range(K)] + ["label"])
        for t in range(K):
            w.writerow([f"T{t}"] + [f"{v:.6f}" for v in cos_dist[t]] + [labels[t]])
    # 병합 트리
    with open(OUT_DIR / f"topic_linkage_average_{sfx}_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "left", "right", "height", "size"]); w.writeheader(); w.writerows(merges)
    # M-grid
    with open(OUT_DIR / f"m_grid_silhouette_{sfx}_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["m", "silhouette"] + [f"T{t}_cluster" for t in range(K)])
        for r in mgrid:
            w.writerow([r["m"], r["silhouette"]] + r["labels"])
    results[K] = dict(K=K, n_docs=len(docs), vocab=len(vocab), perplexity=round(float(lda.perplexity(X)), 1), top_words=top_words, labels=labels,
                      cos_dist=cos_dist, mgrid=mgrid, best=best, merges=merges, leaf_order=leaf_order, cut_height=cut_height,
                      scipy_labels=scipy_labels.tolist())

# --- 6. MD 생성 ------------------------------------------------------------------------------
def fmt_matrix(K, M, labels):
    head = "| | " + " | ".join(f"T{t}" for t in range(K)) + " |\n|---|" + "---|" * K
    rows = [f"| **T{t}** | " + " | ".join(f"{M[t, j]:.3f}" for j in range(K)) + " |" for t in range(K)]
    return head + "\n" + "\n".join(rows)


R10, R8 = results[10], results[8]
frozen_heights = [round(m["height"], 4) for m in sorted(frozen_dendro["merges"], key=lambda m: m["id"])]
md = []
md.append("# LDA φ분포·토픽 간 코사인 거리 행렬 — 최종 코퍼스 10,020건 재적합 산출\n")
md.append("이 폴더의 CSV는 `build_topic_phi_cosine_v7.py`가 **저장소의 파이프라인(`run_lda_v6.py`)과 같은 토크나이저·벡터라이저·LDA 설정으로 "
          "최종 코퍼스 10,020건에 K=10과 K=8을 적합**해 만든 것이다. 손으로 옮긴 값이 없고, 스크립트를 다시 돌리면 같은 파일이 다시 나온다"
          "(`random_state=0`).\n")
md.append("## 왜 이 파일을 따로 만들었나\n")
md.append(f"`Persona_결정공간.html`의 덴드로그램은 동결 스냅샷(v7-40, 7,350건, K=10 → M=5, 실루엣 {frozen_dendro['silhouette']})의 토픽-단어 분포 φ로 "
          "계산한 코사인 거리 행렬에서 나왔다. 그런데 저장소에는 그 φ, 거리 행렬, 7,350건 코퍼스가 없고 병합 높이만 HTML 데이터에 남아 있다"
          "(`data/v7_final/persona_decision_space_v7.json`의 `dendro.merges`). 동결 φ는 그 코퍼스가 없으면 복원할 수 없으므로, 이 폴더는 "
          "**같은 방법을 저장소에 있는 최종 코퍼스에 적용한 실측 산출물**을 제공한다. 동결 스냅샷의 값이 아니라는 점을 분명히 한다.\n")
md.append("| 구분 | 동결 스냅샷(HTML 덴드로그램) | 이 폴더(K=10) | 이 폴더(K=8) |\n|---|---|---|---|")
md.append(f"| 코퍼스 | 7,350건 (v7-40) | 10,020건 → 3토큰 이상 {R10['n_docs']:,}건 | 같음 |")
md.append(f"| 토크나이저 | 14개 언어 라우팅판(저장소 미포함) | `run_lda_v6.py`의 `tokenize()` (저장소 실물) | 같음 |")
md.append(f"| 어휘 | — | {R10['vocab']:,} | 같음 |")
md.append(f"| K / 최적 M / 실루엣 | 10 / 5 / {frozen_dendro['silhouette']} | 10 / {R10['best']['m']} / {R10['best']['silhouette']} | 8 / {R8['best']['m']} / {R8['best']['silhouette']} |")
md.append(f"| 병합 높이(오름차순) | {frozen_heights} | {[m['height'] for m in R10['merges']]} | {[m['height'] for m in R8['merges']]} |")
md.append(f"| 참고: 최종 코퍼스 공식 참고 재적합(`lda_v6_diagnostics_live_reference_v7.json`) | — | — | K={live_diag.get('selected_k')} / M={live_diag.get('selected_m_meta_factors')} / 실루엣 {live_diag.get('meta_factor_silhouette')} (라우팅 토크나이저, 10,018문서) |\n")
md.append("K=8 실루엣이 공식 참고 재적합(0.046)과 다른 이유는 토크나이저가 다르기 때문이다(저장소 판은 구 토크나이저라 문서 수도 "
          f"{R10['n_docs']:,}건으로 10,018건과 다르다). 그래서 이 폴더의 수치는 \"저장소만으로 재현되는 참고 재적합\"이며, 보고서 본문 수치를 대체하지 않는다.\n")

md.append("## 코드 — 단계별로 무엇을 하는가\n")
md.append("모든 단계는 `run_lda_v6.py`의 해당 절과 같은 함수·인자를 쓴다. 아래 코드는 스크립트 본문에서 그대로 옮긴 것이다.\n")
md.append("**1) 토크나이저를 파이프라인 소스에서 잘라 온다** — 재구현하지 않고 `ast`로 `PARTICLES`·`STOPWORDS`·`ENGLISH_STOPWORDS`·`tokenize()` 네 조각의 소스를 뽑아 실행한다.\n")
md.append("```python\nsrc = (REPO / \"run_lda_v6.py\").read_text(encoding=\"utf-8\")\ntree = ast.parse(src)\npieces = [ast.get_source_segment(src, n) for n in tree.body\n"
          "          if (isinstance(n, ast.Assign) and n.targets[0].id in (\"PARTICLES\", \"STOPWORDS\", \"ENGLISH_STOPWORDS\"))\n"
          "          or (isinstance(n, ast.FunctionDef) and n.name == \"tokenize\")]\nns = {\"re\": re}; exec(\"\\n\\n\".join(pieces), ns); tokenize = ns[\"tokenize\"]\n```\n")
md.append("**2) 코퍼스 → 문서 → DTM** — 불릿마다 `tokenize()`를 적용해 3토큰 미만이면 제외하고, 파이프라인과 같은 `CountVectorizer` 설정으로 문서-단어 행렬을 만든다.\n")
md.append("```python\nfor fd in fandoms:\n    for tag in (\"loyalty\", \"spillover\"):\n        for item in fd[tag]:\n            toks = tokenize(item[\"t\"])\n            if len(toks) >= 3:\n                docs.append(\" \".join(toks))\n"
          "vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r\"(?u)\\b\\w+\\b\")\nX = vectorizer.fit_transform(docs); vocab = vectorizer.get_feature_names_out()\n```\n")
md.append("**3) LDA 적합과 φ** — `components_`가 파이프라인이 말하는 φ(토픽×어휘)다. CSV에는 행 합이 1이 되도록 나눈 확률값을 쓴다(코사인 거리는 행 스케일에 무관하므로 결과가 같다).\n")
md.append("```python\nlda = LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method=\"batch\").fit(X)\n"
          "topic_word = lda.components_                              # φ (K × V), 파이프라인 [2]절\nphi = topic_word / topic_word.sum(axis=1, keepdims=True)  # 행 합 1\n```\n")
md.append("**4) 토픽 간 코사인 거리** — 파이프라인 [3]절 그대로: 행을 L2 정규화한 뒤 1 − 내적, 대각 0, 음수 클립.\n")
md.append("```python\nphi_norm = topic_word / (np.linalg.norm(topic_word, axis=1, keepdims=True) + 1e-12)\ncos_dist = 1 - phi_norm @ phi_norm.T\nnp.fill_diagonal(cos_dist, 0); cos_dist = np.clip(cos_dist, 0, None)\n```\n")
md.append("**5) M-grid 실루엣과 병합 트리** — 파이프라인은 `AgglomerativeClustering(metric=\"precomputed\", linkage=\"average\")`로 M=5∼8을 돌려 실루엣 최댓값의 M을 고른다(여기서는 M=4도 포함). "
          "덴드로그램(병합 순서·높이)은 같은 average-linkage를 scipy로 계산해 HTML의 `merges`와 같은 형식(id·left·right·height)으로 저장한다. 두 구현은 같은 병합을 만든다.\n")
md.append("```python\nfor m in range(4, min(9, K)):\n    lab = AgglomerativeClustering(n_clusters=m, metric=\"precomputed\", linkage=\"average\").fit_predict(cos_dist)\n"
          "    sil = silhouette_score(cos_dist, lab, metric=\"precomputed\")\nZ = linkage(squareform(cos_dist, checks=False), method=\"average\")   # 행: [left, right, height, size]\n"
          "cut_height = (Z[K-M-1, 2] + Z[K-M, 2]) / 2                             # M개 군집이 되는 절단 높이(HTML cut_height와 같은 정의)\n```\n")

for R in (R10, R8):
    K = R["K"]
    md.append(f"## 결과 — K={K} (최종 코퍼스 {R['n_docs']:,}문서, perplexity {R['perplexity']})\n")
    md.append("### 토픽별 상위 단어\n")
    md.append("| 토픽 | 상위 10단어 |\n|---|---|")
    for t in range(K):
        md.append(f"| T{t} | {', '.join(R['top_words'][t])} |")
    md.append("\n### 토픽 간 코사인 거리 행렬\n")
    md.append(fmt_matrix(K, R["cos_dist"], R["labels"]))
    md.append("\n### M-grid 실루엣 (average linkage, precomputed cosine)\n")
    md.append("| M | 실루엣 | 토픽 → 군집 |\n|---|---|---|")
    for r in R["mgrid"]:
        mark = " ★" if r["m"] == R["best"]["m"] else ""
        md.append(f"| {r['m']}{mark} | {r['silhouette']} | {r['labels']} |")
    md.append(f"\n최적 M={R['best']['m']}, 절단 높이 {R['cut_height']:.4f}. 잎 순서(왼→오): {R['leaf_order']}\n")
    md.append("### average-linkage 병합 기록\n")
    md.append("| id | left | right | height | size |\n|---|---|---|---|---|")
    for m in R["merges"]:
        md.append(f"| {m['id']} | {m['left']} | {m['right']} | {m['height']:.4f} | {m['size']} |")
    md.append("")

md.append("## 파일\n")
md.append("| 파일 | 내용 |\n|---|---|")
for K in K_LIST:
    s = f"k{K}"
    md.append(f"| `lda_phi_{s}_v7_final.csv` | φ 넓은 표 — {K}행(토픽) × {R10['vocab']:,}열(어휘), 값은 확률(행 합 1) |")
    md.append(f"| `lda_phi_top50_{s}_v7_final.csv` | 토픽별 상위 50단어(long): topic, rank, word, phi, raw_weight |")
    md.append(f"| `topic_cosine_distance_{s}_v7_final.csv` | 토픽 간 코사인 거리 {K}×{K} + 토픽 라벨 |")
    md.append(f"| `topic_linkage_average_{s}_v7_final.csv` | average-linkage 병합 기록 (HTML `dendro.merges`와 같은 형식) |")
    md.append(f"| `m_grid_silhouette_{s}_v7_final.csv` | M=4∼{min(8, K-1)} 실루엣과 M별 토픽 배정 |")
md.append("| `build_topic_phi_cosine_v7.py` | 위 파일 전부와 이 문서를 만드는 스크립트 |\n")
md.append("## 한계\n")
md.append("1. **동결 스냅샷의 φ가 아니다.** 7,350건 코퍼스와 14개 언어 라우팅 토크나이저가 저장소에 없으므로, HTML 덴드로그램의 병합 높이"
          f"({frozen_heights})를 이 폴더의 값으로 재현할 수는 없다. HTML 덴드로그램 자체의 절단·군집·잎 순서 재현은 `../persona_decision_space_v7.ipynb` 2절이 HTML 기록값으로 한다.\n"
          "2. 토픽 번호(T0∼T9)는 적합마다 임의로 매겨지므로 동결 스냅샷의 K0∼K9와 번호가 대응하지 않는다. 상위 단어로 내용을 대조해야 한다.\n"
          "3. LDA는 `random_state=0`으로 고정했지만, scikit-learn 버전이 크게 다르면 마지막 자리 값이 달라질 수 있다.\n")
(OUT_DIR / "TOPIC_PHI_COSINE_DISTANCE_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT_DIR / "TOPIC_PHI_COSINE_DISTANCE_V7.md")
for p in sorted(OUT_DIR.glob("*.csv")):
    print(f"  {p.name}  {p.stat().st_size/1024:.0f} KB")
