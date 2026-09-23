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
  lda_model_{k}_v7_final.pkl               학습된 LatentDirichletAllocation 객체 (joblib) — components_ 가 φ 원본
  count_vectorizer_v7_final.pkl            학습된 CountVectorizer (단어 사전 vocabulary_ 포함, K 공통)
  lda_vocabulary_v7_final.csv              단어 사전: 열 번호(col), 단어, 문서빈도(df), 총 빈도(tf)
  lda_document_index_v7_final.csv          DTM 행 순서: doc_id, 팬덤, loyalty/spillover, 코퍼스 내 idx, 토큰 수
  model_bundle_manifest_v7_final.json      시드·LDA/벡터라이저 인자·패키지 버전·파일별 SHA-256
  TOPIC_PHI_COSINE_DISTANCE_V7.md          방법·코드·결과 정리(이 스크립트가 생성)

실행: python v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_phi_cosine_v7.py   (저장소 안 어느 폴더에서든, 1∼3분)
"""
import ast
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn
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
        for idx, item in enumerate(fd.get(tag, [])):
            n_bullets += 1
            toks = tokenize(item["t"])
            if len(toks) < 3:
                continue
            docs.append(" ".join(toks))
            meta.append((fd["fandom"], tag, idx, len(toks)))
vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
X = vectorizer.fit_transform(docs)
vocab = vectorizer.get_feature_names_out()
print(f"[1] 불릿 {n_bullets:,}건 → 3토큰 이상 문서 {len(docs):,}건, 어휘 {len(vocab):,}개, DTM {X.shape}")

# --- 2-1. 벡터라이저·단어 사전·문서 순서를 저장한다 (모델 pickle 과 함께 있어야 doc-topic 을 다시 계산할 수 있다) --------
VEC_PARAMS = dict(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
joblib.dump(vectorizer, OUT_DIR / "count_vectorizer_v7_final.pkl", compress=3)
df_counts = np.asarray((X > 0).sum(axis=0)).ravel()
tf_counts = np.asarray(X.sum(axis=0)).ravel()
with open(OUT_DIR / "lda_vocabulary_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["col", "word", "df", "tf"])
    for i, word in enumerate(vocab):
        w.writerow([i, word, int(df_counts[i]), int(tf_counts[i])])
with open(OUT_DIR / "lda_document_index_v7_final.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["doc_id", "fandom", "bullet_type", "idx_in_fandom_array", "n_tokens"])
    for d, (fandom, tag, idx, ntok) in enumerate(meta):
        w.writerow([d, fandom, tag, idx, ntok])

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
    LDA_PARAMS = dict(n_components=K, random_state=0, max_iter=50, learning_method="batch")
    lda = LatentDirichletAllocation(**LDA_PARAMS).fit(X)
    joblib.dump(lda, OUT_DIR / f"lda_model_k{K}_v7_final.pkl", compress=3)
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

# --- 5-1. 모델 묶음 manifest: 다시 불러 φ CSV 와 같은지 확인한 뒤 시드·인자·버전·해시를 남긴다 -----------------------
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


vec_loaded = joblib.load(OUT_DIR / "count_vectorizer_v7_final.pkl")
assert list(vec_loaded.get_feature_names_out()) == list(vocab), "벡터라이저 pickle 의 단어 사전이 다름"
X_loaded = vec_loaded.transform(docs)
assert (X_loaded != X).nnz == 0, "벡터라이저 pickle 로 만든 DTM 이 다름"
bundle_files = ["count_vectorizer_v7_final.pkl", "lda_vocabulary_v7_final.csv", "lda_document_index_v7_final.csv"]
for K in K_LIST:
    lda_loaded = joblib.load(OUT_DIR / f"lda_model_k{K}_v7_final.pkl")
    phi_loaded = lda_loaded.components_ / lda_loaded.components_.sum(axis=1, keepdims=True)
    with open(OUT_DIR / f"lda_phi_k{K}_v7_final.csv", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    assert rows[0][1:] == list(vocab), f"K={K} φ CSV 의 어휘 열이 pickle 과 다름"
    phi_csv = np.array([[float(v) for v in r[1:]] for r in rows[1:]])
    assert np.allclose(phi_csv, phi_loaded, atol=1e-7), f"K={K} pickle 의 φ 가 CSV 와 다름"
    results[K]["doc_topic_argmax_share"] = np.bincount(lda_loaded.transform(X).argmax(axis=1), minlength=K).tolist()
    bundle_files += [f"lda_model_k{K}_v7_final.pkl", f"lda_phi_k{K}_v7_final.csv", f"lda_phi_top50_k{K}_v7_final.csv",
                     f"topic_cosine_distance_k{K}_v7_final.csv", f"topic_linkage_average_k{K}_v7_final.csv", f"m_grid_silhouette_k{K}_v7_final.csv"]
manifest = {
    "purpose": "최종 코퍼스 10,020건 참고 재적합의 모델 묶음. 동결 스냅샷(v7-40, 7,350건)의 모델이 아니다. 동결 모델 묶음은 7,350건 코퍼스와 라우팅 토크나이저가 확보되면 같은 형식으로 추가한다.",
    "corpus": {"file": "data/v7_final/fandoms_v3_100.json", "sha256": sha256(DATA / "fandoms_v3_100.json"), "n_bullets": n_bullets, "n_docs_after_min3_filter": len(docs)},
    "tokenizer": {"source": "run_lda_v6.py 의 PARTICLES/STOPWORDS/ENGLISH_STOPWORDS/tokenize() 를 ast 로 추출해 그대로 실행", "run_lda_v6_sha256": sha256(REPO / "run_lda_v6.py"),
                  "note": "보고서의 14개 언어 라우팅 토크나이저(run_lda_v6_live_reference_v7.py)가 아니므로 문서 수가 10,018건과 다르다"},
    "count_vectorizer": VEC_PARAMS | {"n_vocab": int(len(vocab))},
    "lda": {str(K): dict(n_components=K, random_state=0, max_iter=50, learning_method="batch", perplexity=results[K]["perplexity"],
                         best_m=results[K]["best"]["m"], best_silhouette=results[K]["best"]["silhouette"],
                         doc_topic_argmax_share=results[K]["doc_topic_argmax_share"]) for K in K_LIST},
    "reload_check": "pickle 을 다시 불러 φ CSV(atol 1e-7)·DTM 과 일치함을 확인한 뒤 이 manifest 를 썼다",
    "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__, "scipy": scipy.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
    "files": {name: {"sha256": sha256(OUT_DIR / name), "bytes": (OUT_DIR / name).stat().st_size} for name in bundle_files},
}
with open(OUT_DIR / "model_bundle_manifest_v7_final.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("[5-1] 모델 묶음 재로드 검증 통과, manifest 기록")

# --- 6. MD 생성 ------------------------------------------------------------------------------
def fmt_matrix(K, M, labels):
    head = "| | " + " | ".join(f"T{t}" for t in range(K)) + " |\n|---|" + "---|" * K
    rows = [f"| **T{t}** | " + " | ".join(f"{M[t, j]:.3f}" for j in range(K)) + " |" for t in range(K)]
    return head + "\n" + "\n".join(rows)


def kb(name):
    n = (OUT_DIR / name).stat().st_size
    if n < 1024:
        return "1 KB 미만"
    return f"{n/1024:,.0f} KB" if n < 1 << 20 else f"{n/1024/1024:.1f} MB"


R10, R8 = results[10], results[8]
frozen_heights = [round(m["height"], 4) for m in sorted(frozen_dendro["merges"], key=lambda m: m["id"])]
frozen_words = {int(k): v for k, v in frozen_diag["topics_top_words"].items()}
frozen_names = frozen_dendro["topic_names"]
frozen_t2f = {int(k): v for k, v in frozen_diag["topic_to_factor"].items()}
frozen_flabel = {int(k): v for k, v in frozen_diag["factor_labels"].items()}
V = manifest["versions"]
md = []
md.append("# LDA φ분포·토픽 간 코사인 거리·모델 묶음 — 최종 코퍼스 10,020건 참고 재적합\n")
md.append("## 0. 한눈에 보기\n")
md.append("이 폴더는 `build_topic_phi_cosine_v7.py` 한 개가 만든다. 저장소에 실제로 있는 파이프라인(`run_lda_v6.py`)의 토크나이저·벡터라이저·LDA 설정을 "
          "그대로 가져와 **최종 코퍼스 10,020건**에 K=10과 K=8을 적합하고, 그 결과를 세 층으로 남긴다.\n")
md.append("| 층 | 무엇 | 파일 |\n|---|---|---|")
md.append("| A. 모델 묶음 | 학습된 LDA 객체(K별)·CountVectorizer·단어 사전·문서 순서·manifest — 문서-토픽 분포를 다시 계산할 수 있는 최소 단위 | `lda_model_k{10,8}_v7_final.pkl`, `count_vectorizer_v7_final.pkl`, `lda_vocabulary_v7_final.csv`, `lda_document_index_v7_final.csv`, `model_bundle_manifest_v7_final.json` |")
md.append("| B. 산출 행렬 | φ(토픽×어휘), 토픽 간 코사인 거리, average-linkage 병합 기록, M-grid 실루엣 | `lda_phi_*`, `topic_cosine_distance_*`, `topic_linkage_average_*`, `m_grid_silhouette_*` |")
md.append("| C. 문서 | 이 파일(방법·코드·결과·한계) | `TOPIC_PHI_COSINE_DISTANCE_V7.md` |\n")
md.append("| 항목 | 값 |\n|---|---|")
md.append(f"| 코퍼스 | `data/v7_final/fandoms_v3_100.json` 10,020건 (SHA-256 `{manifest['corpus']['sha256'][:12]}…`) |")
md.append(f"| LDA 문서 수 | {R10['n_docs']:,}건 (3토큰 미만 {n_bullets - R10['n_docs']:,}건 제외) |")
md.append(f"| 어휘 | {R10['vocab']:,}개 (`CountVectorizer(max_df=0.6, min_df=2)`) |")
md.append(f"| K=10 | perplexity {R10['perplexity']}, 최적 M={R10['best']['m']}, 실루엣 {R10['best']['silhouette']} |")
md.append(f"| K=8 | perplexity {R8['perplexity']}, 최적 M={R8['best']['m']}, 실루엣 {R8['best']['silhouette']} |")
md.append("| 난수 | `random_state=0`, `max_iter=50`, `learning_method=\"batch\"` |")
md.append(f"| 패키지 | Python {V['python']}, scikit-learn {V['scikit-learn']}, scipy {V['scipy']}, numpy {V['numpy']}, joblib {V['joblib']} |")
md.append("| 재현성 | 스크립트를 다시 돌리면 CSV가 바이트 단위로 같게 나온다. pickle은 저장 직후 다시 불러 φ CSV·DTM과 일치를 확인한다 |\n")
md.append("**이 폴더는 동결 스냅샷(v7-40, 7,350건)의 모델이 아니다.** 보고서 해석 계층이 쓰는 K=10·M=5·실루엣 0.267은 7,350건 코퍼스와 14개 언어 라우팅 토크나이저로 얻은 값이고, "
          "그 둘이 저장소에 없어 동결 모델은 복원할 수 없다. 이 폴더는 같은 방법을 저장소에 있는 재료에 적용한 실측치이며, 동결 모델 묶음이 확보되면 같은 파일 구성으로 옆에 놓기 위한 형식 표준이기도 하다.\n")

md.append("## 1. 세 층의 모델과 이 폴더의 위치\n")
md.append("저장소에는 LDA 결과가 세 시점으로 존재한다. 이 폴더는 세 번째다.\n")
md.append("| | ① 동결 스냅샷 (해석 계층) | ② 공식 라이브 참고 재적합 | ③ 이 폴더 |\n|---|---|---|---|")
md.append("| 코퍼스 | 7,350건 (v7-40) | 10,020건 | 10,020건 |")
md.append(f"| 토크나이저 | 14개 언어 라우팅판 `run_lda_v6_live_reference_v7.py` (저장소 미포함) | 같음 | `run_lda_v6.py`의 `tokenize()` (저장소 실물, 구 토크나이저) |")
md.append(f"| LDA 문서 수 | — | 10,018건 | {R10['n_docs']:,}건 |")
md.append(f"| K / M / 실루엣 | 10 / 5 / {frozen_dendro['silhouette']} | {live_diag.get('selected_k')} / {live_diag.get('selected_m_meta_factors')} / {live_diag.get('meta_factor_silhouette')} (게이트 기각) | 10 / {R10['best']['m']} / {R10['best']['silhouette']} · 8 / {R8['best']['m']} / {R8['best']['silhouette']} |")
md.append("| 저장소에 있는 것 | 토픽 상위 10단어, 토픽→F 배정, 덴드로그램 병합 높이·잎 순서·절단 높이, 팬덤별 F 비중 | K-grid 진단, 토픽 상위어, 팬덤별 F 비중 | **φ 전체, 거리 행렬, 병합 기록, 학습 모델, 단어 사전, 문서 순서** |")
md.append("| 저장소에 없는 것 | 코퍼스, φ, 거리 행렬, 모델, 토크나이저 | 코퍼스는 있음. φ, 모델, 토크나이저 없음 | 없음 |")
md.append("| 출처 | `data/v7_final/lda_v6_diagnostics_frozen_v7_40.json`, `persona_decision_space_v7.json`, `fandom_scores_v6.json` | `data/v7_final/lda_v6_diagnostics_live_reference_v7.json`, `fandom_scores_live_reference_v7.json` | 이 폴더 |\n")
md.append(f"③의 K=8 실루엣({R8['best']['silhouette']})이 ②의 0.046과 다른 이유는 토크나이저가 달라 문서 수({R10['n_docs']:,} vs 10,018)와 어휘가 다르기 때문이다. "
          "③의 수치는 \"저장소만으로 재현되는 참고 재적합\"이고 보고서 본문의 수치를 대체하지 않는다.\n")
md.append("동결 모델 묶음(①의 φ·거리 행렬·모델)을 채우는 순서는 **코퍼스 → 토크나이저 → 재적합**이다. 7,350건 코퍼스와 라우팅 토크나이저가 확보되면 이 스크립트의 입력만 바꿔 같은 파일을 `frozen_v7_40/` 아래에 만들고, "
          "①에 남아 있는 값(상위 10단어·토픽→F 배정·절단 높이 "
          f"{frozen_dendro['cut_height']:.4f}·실루엣 {frozen_dendro['silhouette']}·팬덤별 F 비중)이 전부 재현되는지로 검증한다(9절 4항).\n")

md.append("## 2. 폴더 구성\n")
md.append("### A. 모델 묶음 (pickle·단어 사전·문서 순서·manifest)\n")
md.append("| 파일 | 크기 | 내용 |\n|---|---|---|")
md.append(f"| `lda_model_k10_v7_final.pkl` | {kb('lda_model_k10_v7_final.pkl')} | 학습된 `LatentDirichletAllocation(n_components=10)` 객체(joblib, compress=3). `components_`가 φ 원본(비정규화, 10×{R10['vocab']:,}), `transform(X)`로 문서-토픽 분포 θ 재계산 |")
md.append(f"| `lda_model_k8_v7_final.pkl` | {kb('lda_model_k8_v7_final.pkl')} | 같은 설정의 K=8 모델 |")
md.append(f"| `count_vectorizer_v7_final.pkl` | {kb('count_vectorizer_v7_final.pkl')} | 학습된 `CountVectorizer`(단어 사전 `vocabulary_` 포함). K=10·K=8 공통, 열 순서가 두 모델의 φ와 같다 |")
md.append(f"| `lda_vocabulary_v7_final.csv` | {kb('lda_vocabulary_v7_final.csv')} | 단어 사전 {R10['vocab']:,}행: `col`(φ 열 번호), `word`, `df`(등장 문서 수), `tf`(총 등장 횟수) |")
md.append(f"| `lda_document_index_v7_final.csv` | {kb('lda_document_index_v7_final.csv')} | DTM 행 순서 {R10['n_docs']:,}행: `doc_id`, `fandom`, `bullet_type`(loyalty/spillover), `idx_in_fandom_array`(`fandoms_v3_100.json`의 해당 배열 위치), `n_tokens` |")
md.append(f"| `model_bundle_manifest_v7_final.json` | {kb('model_bundle_manifest_v7_final.json')} | 시드·LDA/벡터라이저 인자, 코퍼스와 `run_lda_v6.py`의 SHA-256, 패키지 버전, K별 perplexity·최적 M·문서 argmax 배정 수, 파일별 SHA-256·바이트, 재로드 검증 기록 |\n")
md.append("### B. 산출 행렬 (K별 접미사 `_k10` / `_k8`)\n")
md.append("| 파일 | 크기(K=10 / K=8) | 내용 |\n|---|---|---|")
md.append(f"| `lda_phi_{{k}}_v7_final.csv` | {kb('lda_phi_k10_v7_final.csv')} / {kb('lda_phi_k8_v7_final.csv')} | φ 넓은 표 — K행(토픽) × {R10['vocab']:,}열(어휘), 값은 확률(행 합 1). 열 순서 = 단어 사전 `col` |")
md.append(f"| `lda_phi_top50_{{k}}_v7_final.csv` | {kb('lda_phi_top50_k10_v7_final.csv')} / {kb('lda_phi_top50_k8_v7_final.csv')} | 토픽별 상위 50단어(long): `topic`, `rank`, `word`, `phi`, `raw_weight`(=`components_`) |")
md.append(f"| `topic_cosine_distance_{{k}}_v7_final.csv` | {kb('topic_cosine_distance_k10_v7_final.csv')} / {kb('topic_cosine_distance_k8_v7_final.csv')} | 토픽 간 코사인 거리 K×K + 토픽 라벨(상위 4단어) |")
md.append(f"| `topic_linkage_average_{{k}}_v7_final.csv` | {kb('topic_linkage_average_k10_v7_final.csv')} / {kb('topic_linkage_average_k8_v7_final.csv')} | average-linkage 병합 기록 `id, left, right, height, size` — HTML `dendro.merges`와 같은 형식 |")
md.append(f"| `m_grid_silhouette_{{k}}_v7_final.csv` | {kb('m_grid_silhouette_k10_v7_final.csv')} / {kb('m_grid_silhouette_k8_v7_final.csv')} | M=4∼8(K=8은 4∼7) 실루엣과 M별 토픽→군집 배정 |\n")
md.append("### C. 스크립트·문서\n")
md.append("| 파일 | 내용 |\n|---|---|")
md.append("| `build_topic_phi_cosine_v7.py` | A·B 전부와 이 문서를 만든다. 저장소 안 어느 폴더에서 실행해도 된다 (약 1∼3분) |")
md.append("| `TOPIC_PHI_COSINE_DISTANCE_V7.md` | 이 문서 (스크립트가 생성하므로 손으로 고치지 않는다) |\n")

md.append("## 3. 방법 — 단계별 코드\n")
md.append("모든 단계는 `run_lda_v6.py`의 해당 절과 같은 함수·인자를 쓴다. 아래 코드는 스크립트 본문에서 그대로 옮긴 것이다.\n")
md.append("**1) 토크나이저를 파이프라인 소스에서 잘라 온다** — 재구현하지 않고 `ast`로 `PARTICLES`·`STOPWORDS`·`ENGLISH_STOPWORDS`·`tokenize()` 네 조각의 소스를 뽑아 실행한다.\n")
md.append("```python\nsrc = (REPO / \"run_lda_v6.py\").read_text(encoding=\"utf-8\")\ntree = ast.parse(src)\npieces = [ast.get_source_segment(src, n) for n in tree.body\n"
          "          if (isinstance(n, ast.Assign) and n.targets[0].id in (\"PARTICLES\", \"STOPWORDS\", \"ENGLISH_STOPWORDS\"))\n"
          "          or (isinstance(n, ast.FunctionDef) and n.name == \"tokenize\")]\nns = {\"re\": re}; exec(\"\\n\\n\".join(pieces), ns); tokenize = ns[\"tokenize\"]\n```\n")
md.append("**2) 코퍼스 → 문서 → DTM** — 불릿마다 `tokenize()`를 적용해 3토큰 미만이면 제외하고, 파이프라인과 같은 `CountVectorizer` 설정으로 문서-단어 행렬을 만든다. "
          "이때 문서의 순서(팬덤, loyalty/spillover, 배열 위치, 토큰 수)를 `lda_document_index_v7_final.csv`에, 벡터라이저와 단어 사전을 `count_vectorizer_v7_final.pkl`·`lda_vocabulary_v7_final.csv`에 저장한다.\n")
md.append("```python\nfor fd in fandoms:\n    for tag in (\"loyalty\", \"spillover\"):\n        for idx, item in enumerate(fd[tag]):\n            toks = tokenize(item[\"t\"])\n            if len(toks) >= 3:\n                docs.append(\" \".join(toks)); meta.append((fd[\"fandom\"], tag, idx, len(toks)))\n"
          "vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r\"(?u)\\b\\w+\\b\")\nX = vectorizer.fit_transform(docs); vocab = vectorizer.get_feature_names_out()\njoblib.dump(vectorizer, \"count_vectorizer_v7_final.pkl\", compress=3)\n```\n")
md.append("**3) LDA 적합과 φ** — `components_`가 파이프라인이 말하는 φ(토픽×어휘)다. 학습된 객체를 그대로 pickle로 저장하고, CSV에는 행 합이 1이 되도록 나눈 확률값을 쓴다(코사인 거리는 행 스케일에 무관하므로 결과가 같다).\n")
md.append("```python\nlda = LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method=\"batch\").fit(X)\njoblib.dump(lda, f\"lda_model_k{K}_v7_final.pkl\", compress=3)\n"
          "topic_word = lda.components_                              # φ (K × V), 파이프라인 [2]절\nphi = topic_word / topic_word.sum(axis=1, keepdims=True)  # 행 합 1\n```\n")
md.append("**4) 토픽 간 코사인 거리** — 파이프라인 [3]절 그대로: 행을 L2 정규화한 뒤 1 − 내적, 대각 0, 음수 클립.\n")
md.append("```python\nphi_norm = topic_word / (np.linalg.norm(topic_word, axis=1, keepdims=True) + 1e-12)\ncos_dist = 1 - phi_norm @ phi_norm.T\nnp.fill_diagonal(cos_dist, 0); cos_dist = np.clip(cos_dist, 0, None)\n```\n")
md.append("**5) M-grid 실루엣과 병합 트리** — 파이프라인은 `AgglomerativeClustering(metric=\"precomputed\", linkage=\"average\")`로 M=5∼8을 돌려 실루엣 최댓값의 M을 고른다(여기서는 M=4도 포함). "
          "덴드로그램(병합 순서·높이)은 같은 average-linkage를 scipy로 계산해 HTML의 `merges`와 같은 형식(id·left·right·height)으로 저장한다. 두 구현은 같은 병합을 만든다.\n")
md.append("```python\nfor m in range(4, min(9, K)):\n    lab = AgglomerativeClustering(n_clusters=m, metric=\"precomputed\", linkage=\"average\").fit_predict(cos_dist)\n"
          "    sil = silhouette_score(cos_dist, lab, metric=\"precomputed\")\nZ = linkage(squareform(cos_dist, checks=False), method=\"average\")   # 행: [left, right, height, size]\n"
          "cut_height = (Z[K-M-1, 2] + Z[K-M, 2]) / 2                             # M개 군집이 되는 절단 높이(HTML cut_height와 같은 정의)\n```\n")
md.append("**6) 모델 묶음 재로드 검증과 manifest** — 저장한 pickle을 곧바로 다시 불러 (a) 벡터라이저의 단어 사전이 `vocab`과 같고 `transform(docs)`가 같은 DTM을 내는지, "
          "(b) 모델의 `components_`를 정규화한 값이 φ CSV와 허용오차 1e-7 안에서 같은지 확인한 뒤에야 manifest를 쓴다. 하나라도 어긋나면 스크립트가 멈춘다.\n")
md.append("```python\nvec_loaded = joblib.load(\"count_vectorizer_v7_final.pkl\")\nassert list(vec_loaded.get_feature_names_out()) == list(vocab)\nassert (vec_loaded.transform(docs) != X).nnz == 0\n"
          "lda_loaded = joblib.load(f\"lda_model_k{K}_v7_final.pkl\")\nphi_loaded = lda_loaded.components_ / lda_loaded.components_.sum(axis=1, keepdims=True)\nassert np.allclose(phi_csv, phi_loaded, atol=1e-7)\n```\n")

for R in (R10, R8):
    K = R["K"]
    share = manifest["lda"][str(K)]["doc_topic_argmax_share"]
    md.append(f"## {4 if K == 10 else 5}. 결과 — K={K} (문서 {R['n_docs']:,}건, perplexity {R['perplexity']})\n")
    md.append("### 토픽별 상위 단어와 문서 배정\n")
    md.append("`문서 수`는 θ의 argmax로 문서를 한 토픽에 배정했을 때의 건수다(합 = 문서 수).\n")
    md.append("| 토픽 | 상위 10단어 | 문서 수 |\n|---|---|---|")
    for t in range(K):
        md.append(f"| T{t} | {', '.join(R['top_words'][t])} | {share[t]:,} |")
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

md.append("## 6. 동결 스냅샷(K=10)과의 대조\n")
md.append("토픽 번호는 적합마다 임의로 매겨지므로 번호로 대응시킬 수 없다. 여기서는 **상위 10단어의 겹침 수**로 동결 토픽 K0∼K9마다 이 폴더 K=10에서 가장 가까운 토픽을 찾았다. "
          "겹침 수는 기계적 지표이며 의미 대응을 보증하지 않는다.\n")
md.append("| 동결 토픽 | 동결 상위 10단어 | 동결 F | 가장 가까운 T (겹침) | 그 T의 상위 10단어 |\n|---|---|---|---|---|")
for k in range(10):
    fw = set(frozen_words[k])
    best_t, best_n = max(((t, len(fw & set(R10["top_words"][t]))) for t in range(10)), key=lambda x: (x[1], -x[0]))
    md.append(f"| K{k} {frozen_names[k]} | {', '.join(frozen_words[k])} | F{frozen_t2f[k]} {frozen_flabel[frozen_t2f[k]]} | T{best_t} ({best_n}/10) | {', '.join(R10['top_words'][best_t])} |")
md.append("")
md.append("| 구분 | 동결 스냅샷 | 이 폴더 K=10 |\n|---|---|---|")
md.append(f"| 코퍼스 / 문서 | 7,350건 / — | 10,020건 / {R10['n_docs']:,}건 |")
md.append(f"| 최적 M / 실루엣 | 5 / {frozen_dendro['silhouette']} | {R10['best']['m']} / {R10['best']['silhouette']} |")
md.append(f"| M=5 실루엣 | {frozen_dendro['silhouette']} | {next(r['silhouette'] for r in R10['mgrid'] if r['m'] == 5)} |")
md.append(f"| 절단 높이 | {frozen_dendro['cut_height']:.4f} | {R10['cut_height']:.4f} |")
md.append(f"| 병합 높이(오름차순) | {frozen_heights} | {[m['height'] for m in R10['merges']]} |")
md.append(f"| 잎 순서 | {frozen_dendro['leaf_order']} | {R10['leaf_order']} |\n")
md.append("동결 스냅샷은 첫 병합 높이가 0.41로 낮고 M=5에서 실루엣 0.267을 내는 반면, 이 폴더의 K=10은 첫 병합이 0.54에서 시작하고 M=5 실루엣이 0.07 수준이다. "
          "코퍼스가 2,670건 늘고 토크나이저가 다른 상태에서 같은 군집 구조가 나오지 않는다는 뜻이며, 이것이 보고서가 라이브 재적합을 실루엣 게이트로 기각하고 동결 스냅샷을 해석 계층으로 유지한 이유와 일치한다.\n")

md.append("## 7. 모델 묶음 사용법\n")
md.append("φ CSV만으로는 문서-토픽 분포 θ를 다시 만들 수 없으므로 학습 모델과 단어 사전을 같이 둔다. 문서는 `lda_document_index_v7_final.csv`의 순서대로 `run_lda_v6.py`의 `tokenize()`를 적용해 공백으로 이은 문자열이다.\n")
md.append("```python\nimport ast, csv, json, re, joblib, numpy as np\n\n# 1) 토크나이저 (3절 1단계와 같은 방법)\nsrc = open(\"run_lda_v6.py\", encoding=\"utf-8\").read(); tree = ast.parse(src); ns = {\"re\": re}\n"
          "exec(\"\\n\\n\".join(ast.get_source_segment(src, n) for n in tree.body\n     if (isinstance(n, ast.Assign) and getattr(n.targets[0], \"id\", \"\") in (\"PARTICLES\", \"STOPWORDS\", \"ENGLISH_STOPWORDS\"))\n"
          "     or (isinstance(n, ast.FunctionDef) and n.name == \"tokenize\")), ns)\ntokenize = ns[\"tokenize\"]\n\n"
          "# 2) 문서를 저장된 순서로 복원\nfandoms = {f[\"fandom\"]: f for f in json.load(open(\"data/v7_final/fandoms_v3_100.json\", encoding=\"utf-8\"))}\n"
          "rows = list(csv.DictReader(open(\"lda_document_index_v7_final.csv\", encoding=\"utf-8-sig\")))\n"
          "docs = [\" \".join(tokenize(fandoms[r[\"fandom\"]][r[\"bullet_type\"]][int(r[\"idx_in_fandom_array\"])][\"t\"])) for r in rows]\n\n"
          "# 3) 모델 묶음\nvec = joblib.load(\"count_vectorizer_v7_final.pkl\")\nlda = joblib.load(\"lda_model_k10_v7_final.pkl\")\nX = vec.transform(docs)\n"
          "theta = lda.transform(X)                                              # 문서 × 토픽, 행 합 1\nphi = lda.components_ / lda.components_.sum(axis=1, keepdims=True)  # = lda_phi_k10_v7_final.csv\n```\n")
md.append("이 절차를 별도 프로세스에서 실행해 확인한 결과: 문서 " f"{R10['n_docs']:,}건이 그대로 복원되고 각 문서의 토큰 수가 CSV의 `n_tokens`와 일치하며, θ는 {R10['n_docs']:,}×10·{R10['n_docs']:,}×8로 행 합이 1이고, "
          "각 토픽의 1위 단어가 `lda_phi_top50_*` CSV의 rank 1과 같다.\n")
md.append("팬덤별 F 비중 같은 파이프라인 후속 단계(토픽→F 합산, loyalty/spillover 가중)는 `run_lda_v6.py` [4]절 이후를 θ에 그대로 적용하면 된다. 다만 이 폴더의 K·M은 동결 스냅샷과 다르므로 보고서의 F1∼F5 라벨을 그대로 붙이면 안 된다.\n")

md.append("## 8. 재현 방법\n")
md.append("```bash\n# 저장소 루트(또는 안쪽 아무 폴더)에서\npython v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_phi_cosine_v7.py\n```\n")
md.append(f"- 소요 시간 약 1∼3분(LDA 적합 K=10·K=8 각 30∼40초). 필요한 패키지: scikit-learn, scipy, numpy, joblib. 기록된 버전은 scikit-learn {V['scikit-learn']}, scipy {V['scipy']}, numpy {V['numpy']}.\n"
          "- 같은 버전에서는 CSV가 바이트 단위로 같게 나온다(마지막 실행에서 기존 CSV 10개가 변경 없이 재생성됨을 `git status`로 확인). 버전이 크게 다르면 마지막 자리 값이 달라질 수 있다.\n"
          "- 스크립트는 `run_lda_v6.py`와 `data/v7_final/fandoms_v3_100.json`이 있는 폴더를 저장소 루트로 찾는다. 두 파일의 SHA-256은 manifest에 있어, 입력이 바뀌었는지 먼저 확인할 수 있다.\n"
          "- pickle은 scikit-learn 객체이므로 버전이 다른 환경에서 불러오면 경고가 날 수 있다. 그때는 CSV(φ·단어 사전·문서 순서)만으로도 3절 3단계부터 다시 적합해 같은 결과를 얻을 수 있다.\n")

md.append("## 9. 한계와 다음 단계\n")
md.append("1. **동결 스냅샷의 φ·모델이 아니다.** 7,350건 코퍼스와 14개 언어 라우팅 토크나이저가 저장소에 없으므로, HTML 덴드로그램의 병합 높이"
          f"({frozen_heights})를 이 폴더의 값으로 재현할 수는 없다. HTML 덴드로그램 자체의 절단·군집·잎 순서 재현은 `../persona_decision_space_v7.ipynb` 2절이 HTML 기록값으로 한다.\n"
          "2. 토픽 번호(T0∼T9)는 적합마다 임의로 매겨지므로 동결 스냅샷의 K0∼K9와 번호가 대응하지 않는다. 6절의 겹침 표는 참고용이다.\n"
          "3. 토크나이저가 구판이라 문서 수(9,954)와 어휘가 공식 라이브 참고 재적합(10,018)과 다르다. 라우팅 토크나이저가 재구성되면 이 스크립트의 1단계만 바꿔 다시 돌린다.\n"
          "4. **동결 모델 묶음을 추가할 때의 검증 기준** — 같은 파일 구성을 `frozen_v7_40/`에 만들고 다음이 전부 맞아야 한다: "
          "① 토픽별 상위 10단어가 `lda_v6_diagnostics_frozen_v7_40.json`의 `topics_top_words`와 일치, ② 토픽→F 배정이 `topic_to_factor`와 일치, "
          f"③ M=5 실루엣 {frozen_dendro['silhouette']}·절단 높이 {frozen_dendro['cut_height']:.4f}·병합 높이 {frozen_heights}가 재현, "
          "④ 팬덤별 F 비중이 `fandom_scores_v6.json`의 `factor_share`와 일치, ⑤ activity 합 7,350.\n")
(OUT_DIR / "TOPIC_PHI_COSINE_DISTANCE_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", OUT_DIR / "TOPIC_PHI_COSINE_DISTANCE_V7.md")
for p in sorted(OUT_DIR.glob("*.csv")):
    print(f"  {p.name}  {p.stat().st_size/1024:.0f} KB")
