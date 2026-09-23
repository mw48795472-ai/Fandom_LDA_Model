# -*- coding: utf-8 -*-
"""동결 스냅샷(v7-40) 모델의 근방 재현: 근사 복원 코퍼스(7,326건) + 재구성 라우팅 토크나이저로 K=10 을 적합해
라이브 쪽(topic_phi_cosine/)과 같은 파일 구성의 모델 묶음을 frozen_v7_40/ 에 저장하고, 저장소에 남은 동결 값과 대조한다.

  코퍼스     data/v7_final/frozen_snapshot_v7_40/fandoms_v7_40_frozen_reconstructed.json (97개 팬덤 문장 동일, 3개 팬덤 24건 유실)
  토크나이저 run_lda_v6_live_reference_v7.py 의 === TOKENIZER BEGIN/END === 절 (마커 exec, 재구성본)
  설정       CountVectorizer(max_df=0.6, min_df=2), LDA(n_components=10, random_state=0, max_iter=50, batch) — 파이프라인 [1][2]절과 동일
  대조       lda_v6_diagnostics_frozen_v7_40.json (토픽 상위 10단어·토픽→F), persona_decision_space_v7.json (병합 높이·절단 높이·실루엣 0.267),
             fandom_scores_v6.json (팬덤별 factor_share·factor_diversity)

출력 (frozen_v7_40/): lda_model_k10, count_vectorizer, lda_vocabulary, lda_document_index, lda_phi_k10, lda_phi_top50_k10,
      topic_cosine_distance_k10, topic_linkage_average_k10, m_grid_silhouette_k10, frozen_refit_comparison_v7_40.json, manifest
실행: python build_frozen_model_bundle_v7_40.py [--era r40]   (약 2분)
  --era r40 : 동결 시점(v7-40)은 v7 76·77 라운드의 토크나이저 변경(일본어 불용어, 가나+한자 불릿의 fugashi 단독 처리, 자기인용 슬러그
              제거) 이전이므로, 그 세 가지를 끈 "r40 시점 토크나이저"로 적합해 frozen_v7_40_r40tok/ 에 따로 저장한다.
"""
import csv, hashlib, json, platform, re, sys
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import silhouette_score

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
D = REPO / "data" / "v7_final"
ERA = "r40" if "--era" in sys.argv and sys.argv[sys.argv.index("--era") + 1] == "r40" else "final"
OUT = HERE / ("frozen_v7_40_r40tok" if ERA == "r40" else "frozen_v7_40"); OUT.mkdir(exist_ok=True)
CORPUS = D / "frozen_snapshot_v7_40" / "fandoms_v7_40_frozen_reconstructed.json"
K, M_TARGET = 10, 5

# --- 토크나이저: 재구성본의 마커 절
src = (REPO / "run_lda_v6_live_reference_v7.py").read_text(encoding="utf-8")
block = src[src.index("# === TOKENIZER BEGIN ===") + len("# === TOKENIZER BEGIN ==="):src.index("# === TOKENIZER END ===")]
ns = {"re": re, "__name__": "tok"}
exec("import re\nfrom urllib.parse import urlparse\n" + block, ns)
tokenize = ns["tokenize"]
if ERA == "r40":  # v7 76·77 이전 동작으로 되돌림
    ns["JAPANESE_STOPWORDS"].clear()                       # r76 신설 이전
    ns["self_citation_slugs"] = lambda url: set()          # r77 신설 이전
    _g, _ja, _zh, _th, _strip, _K, _H, _T = ns["tokenize_generic"], ns["tokenize_ja"], ns["tokenize_zh"], ns["tokenize_th"], ns["strip_domain_fragments"], ns["RE_KANA"], ns["RE_HANZI"], ns["RE_THAI"]
    def tokenize(text, url=""):                             # r76 이전: 가나와 한자가 모두 있으면 fugashi·jieba 둘 다 실행
        text = _strip(text); toks = _g(text, url)
        if _K.search(text): toks += _ja(text)
        if _H.search(text): toks += _zh(text)
        if _T.search(text): toks += _th(text)
        return toks

fandoms = json.load(open(CORPUS, encoding="utf-8"))
docs, meta = [], []
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for idx, it in enumerate(fd[tag]):
            toks = tokenize(it["t"], it.get("u", ""))
            if len(toks) < 3:
                continue
            docs.append(" ".join(toks)); meta.append((fd["fandom"], tag, idx, len(toks)))
vec = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
X = vec.fit_transform(docs); vocab = vec.get_feature_names_out()
print(f"[1] 코퍼스 {sum(len(f['loyalty'])+len(f['spillover']) for f in fandoms):,}건 → 문서 {len(docs):,}, 어휘 {len(vocab):,}")

lda = LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method="batch").fit(X)
tw = lda.components_; phi = tw / tw.sum(axis=1, keepdims=True)
theta = lda.transform(X)
top10 = [[vocab[i] for i in tw[t].argsort()[::-1][:10]] for t in range(K)]
phi_norm = tw / (np.linalg.norm(tw, axis=1, keepdims=True) + 1e-12)
cos = 1 - phi_norm @ phi_norm.T; np.fill_diagonal(cos, 0); cos = np.clip(cos, 0, None); cos = (cos + cos.T) / 2
mgrid = []
for m in range(4, 9):
    lab = AgglomerativeClustering(n_clusters=m, metric="precomputed", linkage="average").fit_predict(cos)
    mgrid.append({"m": m, "silhouette": round(float(silhouette_score(cos, lab, metric="precomputed")), 4), "labels": lab.tolist()})
best = max(mgrid, key=lambda r: r["silhouette"])
Z = linkage(squareform(cos, checks=False), method="average")
heights = [round(float(h), 4) for h in Z[:, 2]]
leaf_order = dendrogram(Z, no_plot=True)["leaves"]
m5 = next(r for r in mgrid if r["m"] == M_TARGET)
cut5 = float((Z[K - M_TARGET - 1, 2] + Z[K - M_TARGET, 2]) / 2)
print(f"[2] K=10 perplexity {lda.perplexity(X):.1f} | M-grid " + ", ".join(f"M={r['m']}:{r['silhouette']}" for r in mgrid) + f" → 최적 M={best['m']} | M=5 실루엣 {m5['silhouette']}, 절단 높이 {cut5:.4f}")

# --- 저장 (라이브 묶음과 같은 구성)
joblib.dump(vec, OUT / "count_vectorizer_v7_40.pkl", compress=3)
joblib.dump(lda, OUT / "lda_model_k10_v7_40.pkl", compress=3)
dfc = np.asarray((X > 0).sum(axis=0)).ravel(); tfc = np.asarray(X.sum(axis=0)).ravel()
with open(OUT / "lda_vocabulary_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["col", "word", "df", "tf"]); [w.writerow([i, wd, int(dfc[i]), int(tfc[i])]) for i, wd in enumerate(vocab)]
with open(OUT / "lda_document_index_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["doc_id", "fandom", "bullet_type", "idx_in_fandom_array", "n_tokens"]); [w.writerow([d, *m]) for d, m in enumerate(meta)]
with open(OUT / "lda_phi_k10_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["topic"] + list(vocab)); [w.writerow([f"T{t}"] + [f"{v:.8g}" for v in phi[t]]) for t in range(K)]
with open(OUT / "lda_phi_top50_k10_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["topic", "rank", "word", "phi", "raw_weight"])
    for t in range(K):
        for r, i in enumerate(tw[t].argsort()[::-1][:50], 1): w.writerow([f"T{t}", r, vocab[i], f"{phi[t, i]:.6g}", f"{tw[t, i]:.4f}"])
with open(OUT / "topic_cosine_distance_k10_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["topic"] + [f"T{t}" for t in range(K)] + ["label"]); [w.writerow([f"T{t}"] + [f"{v:.6f}" for v in cos[t]] + ["·".join(top10[t][:4])]) for t in range(K)]
with open(OUT / "topic_linkage_average_k10_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "left", "right", "height", "size"]); [w.writerow([K + i, int(a), int(b), round(float(h), 6), int(n)]) for i, (a, b, h, n) in enumerate(Z)]
with open(OUT / "m_grid_silhouette_k10_v7_40.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["m", "silhouette"] + [f"T{t}_cluster" for t in range(K)]); [w.writerow([r["m"], r["silhouette"]] + r["labels"]) for r in mgrid]

# --- 동결 값과 대조
fdiag = json.load(open(D / "lda_v6_diagnostics_frozen_v7_40.json", encoding="utf-8"))
fden = json.load(open(D / "persona_decision_space_v7.json", encoding="utf-8"))["dendro"]
fsc = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_v6.json", encoding="utf-8"))}
fwords = {int(k): v for k, v in fdiag["topics_top_words"].items()}
ft2f = {int(k): v for k, v in fdiag["topic_to_factor"].items()}
flabels = {int(k): v for k, v in fdiag["factor_labels"].items()}
# 토픽 대응: 상위 10단어 겹침 최대 (1:1 탐욕)
align, used = [], set()
for fk in sorted(fwords, key=lambda k: -max(len(set(fwords[k]) & set(top10[t])) for t in range(K))):
    cand = sorted(((len(set(fwords[fk]) & set(top10[t])), t) for t in range(K) if t not in used), reverse=True)
    ov, t = cand[0]; used.add(t)
    align.append({"frozen_topic": fk, "frozen_name": fden["topic_names"][fk], "frozen_words": fwords[fk], "recon_topic": t, "overlap10": ov, "recon_words": top10[t], "frozen_factor": ft2f[fk]})
align.sort(key=lambda a: a["frozen_topic"])
# M=5 군집 구조 대조: 동결에서 같은 F인 토픽 쌍이 재구성 M=5 에서도 같은 군집인지 (대응 기준)
r_of = {a["frozen_topic"]: a["recon_topic"] for a in align}
lab5 = m5["labels"]
pairs_same = pairs_total = 0
for i in range(K):
    for j in range(i + 1, K):
        if ft2f[i] == ft2f[j]:
            pairs_total += 1; pairs_same += lab5[r_of[i]] == lab5[r_of[j]]
# 팬덤별 factor_share (M=5, 재구성 군집) vs 동결 factor_share — 군집↔F 대응은 대응 토픽 다수결
fandom_docs = {}
for d, (fname, tag, idx, n) in enumerate(meta): fandom_docs.setdefault(fname, []).append(d)
cluster_to_F = {}
for c in range(M_TARGET):
    votes = [ft2f[fk] for fk, t in r_of.items() if lab5[t] == c]
    cluster_to_F[c] = max(set(votes), key=votes.count) if votes else None
share_r, share_f, div_r, div_f = [], [], [], []
for fname, idxs in fandom_docs.items():
    ts = theta[idxs].sum(axis=0); fs = np.zeros(M_TARGET)
    for t in range(K): fs[lab5[t]] += ts[t]
    fs = fs / fs.sum()
    p = fs[fs > 0]; div_r.append(float(-(p * np.log(p)).sum() / np.log(M_TARGET)))
    if fname in fsc:
        div_f.append(fsc[fname]["factor_diversity"])
        byF = {}
        for c in range(M_TARGET): byF[cluster_to_F[c]] = byF.get(cluster_to_F[c], 0) + fs[c]
        share_r.append([byF.get(F, 0.0) for F in range(M_TARGET)]); share_f.append([fsc[fname]["factor_share"].get(flabels[F], 0.0) for F in range(M_TARGET)])
    else:
        div_f.append(None)
share_r, share_f = np.array(share_r), np.array(share_f)
share_corr = [round(float(np.corrcoef(share_r[:, F], share_f[:, F])[0, 1]), 3) if share_r[:, F].std() > 0 and share_f[:, F].std() > 0 else None for F in range(M_TARGET)]
dv = [(a, b) for a, b in zip(div_r, div_f) if b is not None]
div_corr = round(float(np.corrcoef([a for a, _ in dv], [b for _, b in dv])[0, 1]), 3)
comp = {
    "corpus": {"file": str(CORPUS.relative_to(REPO)), "n_bullets": 7326, "n_docs": len(docs), "n_vocab": int(len(vocab))},
    "frozen_reference": {"K": 10, "M": 5, "silhouette": fden["silhouette"], "cut_height": fden["cut_height"], "merge_heights": [round(m["height"], 4) for m in sorted(fden["merges"], key=lambda m: m["id"])], "leaf_order": fden["leaf_order"]},
    "reconstruction": {"K": 10, "perplexity": round(float(lda.perplexity(X)), 1), "m_grid": mgrid, "best_m": best["m"], "best_silhouette": best["silhouette"], "m5_silhouette": m5["silhouette"], "m5_cut_height": round(cut5, 4), "merge_heights": heights, "leaf_order": leaf_order},
    "topic_alignment": align,
    "topic_alignment_summary": {"overlap_ge8": sum(a["overlap10"] >= 8 for a in align), "overlap_ge5": sum(a["overlap10"] >= 5 for a in align), "mean_overlap": round(sum(a["overlap10"] for a in align) / K, 2)},
    "m5_cluster_structure": {"frozen_same_factor_pairs": pairs_total, "also_same_cluster_in_recon": pairs_same, "cluster_to_factor_by_vote": cluster_to_F},
    "fandom_factor_share": {"pearson_by_factor": dict(zip([flabels[F] for F in range(M_TARGET)], share_corr)), "n_fandoms": int(len(share_r))},
    "factor_diversity": {"pearson": div_corr, "mean_recon": round(float(np.mean(div_r)), 4), "mean_frozen": round(float(np.mean([b for _, b in dv])), 4)},
    "tokenizer_era": ERA,
    "verdict_note": "근사 코퍼스(3개 팬덤 24건 유실)와 재구성 토크나이저로 얻은 근방 재현이다. 동결 스냅샷 값 자체가 아니다.",
}
json.dump(comp, open(OUT / "frozen_refit_comparison_v7_40.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def sha(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()


files = sorted(p.name for p in OUT.iterdir() if p.suffix in (".pkl", ".csv", ".json") and p.name != "frozen_model_bundle_manifest_v7_40.json")
manifest = {"purpose": f"동결 스냅샷 v7-40 모델의 근방 재현 묶음 (근사 코퍼스 7,326건 + 재구성 토크나이저[{ERA} 시점 설정], K=10). 동결 원본 모델이 아니다.",
            "inputs": {"corpus_sha256": sha(CORPUS), "tokenizer_script_sha256": sha(REPO / "run_lda_v6_live_reference_v7.py")},
            "settings": {"count_vectorizer": {"max_df": 0.6, "min_df": 2}, "lda": {"n_components": 10, "random_state": 0, "max_iter": 50, "learning_method": "batch"}},
            "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__, "scipy": scipy.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
            "files": {n: {"sha256": sha(OUT / n), "bytes": (OUT / n).stat().st_size} for n in files}}
json.dump(manifest, open(OUT / "frozen_model_bundle_manifest_v7_40.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("[3] 대조:", json.dumps({k: comp[k] for k in ("topic_alignment_summary", "m5_cluster_structure", "fandom_factor_share", "factor_diversity")}, ensure_ascii=False))
print("    동결 병합 높이", comp["frozen_reference"]["merge_heights"], "\n    재구성 병합 높이", heights)
for a in align:
    print(f"    K{a['frozen_topic']} {a['frozen_name'][:14]:14s} → T{a['recon_topic']} ({a['overlap10']}/10) {a['recon_words'][:6]}")
print("wrote", OUT)
