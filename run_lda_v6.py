"""
LDA v6 — Topic Factoring + Fan Impact Model (Second Expanded-Corpus Round)
Same methodology as v5 (multi-K LDA selection, Topic->Meta Factor compression, Fan Factor
Matrix, Coverage Index, Factor Diversity, Member Mention Pilot). The ONLY change from v5 is
the input corpus: the user asked to roughly double the evidence base ("두배로 증가"). Two
rounds of parallel research agents (10 agents, then a follow-up 4 agents targeting the 31
fandoms the first round could not reach) expanded real, web-sourced evidence bullets from
2,403 to 2,674 (a disclosed ~1.11x increase — NOT the requested 2x), because the session's
shared WebSearch/WebFetch quota (200 calls, pooled across all concurrently running agents)
was exhausted well before 10 parallel agents each finished their ~10 assigned fandoms. This
mirrors the same constraint documented in v5's docstring for the original 10x->1.32x outcome.
Per that established precedent, the actual achieved multiplier is reported honestly here and
in the deliverables rather than silently treated as a full doubling or padded with fabricated
bullets. The key improvement over the prior shortfall: after round 2, all 100/100 fandoms
received at least some genuinely new, source-verified evidence (round 1 alone left 31 fandoms
at zero new bullets; round 2 closed that gap completely). See v6_merge_log.json for the full
per-fandom before/after breakdown.

  1. Multi-K model selection: perplexity + UMass coherence + topic diversity + seed stability
  2. Topic -> Meta Factor compression via cosine-similarity hierarchical clustering
  3. Fan Factor Matrix: per-fandom share of each Meta Factor (theta-weighted, not just bullet count)
  4. Coverage Index (Language Balance + Source-Type Diversity) computed from real source URLs,
     kept SEPARATE from the Loyalty/Spillover Impact score (never multiplied in) per the
     "Impact != Coverage" principle in the strategy docs.
  5. Factor Diversity (Shannon entropy of a fandom's Factor Share) as the 3D Z-axis candidate,
     replacing the old "raw evidence count" Z-axis, which was not independent of X/Y.
  6. Member Mention Pilot (text-mining only, NOT new research) for 11 Tier-S idol groups whose
     already-collected bullets are scanned for individual member name mentions.

No bullet text or URL used here is invented — everything is read from fandoms_v3_100.json,
which itself is 100% sourced to real URLs collected by prior research passes in this project.
"""
import json, re, math, csv, itertools, argparse, os
from collections import defaultdict, Counter
from urllib.parse import urlparse
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

# ------------------------------------------------------------------------------------------
# 입력/출력 경로 (저장소 상대경로;
# 저장소 상대경로 + CLI 인자로 교체. 파이프라인 로직은 변경하지 않았다.)
#
#   기본값: 최종 라이브 코퍼스(data/v7_final/fandoms_v3_100.json, 10,020건) -> 출력 output/lda_rerun/
#
# 주의: 이 파일은 최종 토크나이저 개편 이전 판의 파이프라인이다. 최종 제출본의 라이브 참고 재적합
# (data/v7_final/lda_v6_diagnostics_live_reference_v7.json, 10,020건, K=8/M=5/실루엣 0.046)은
# 이후 토크나이저 개편(v7 38~39라운드, 14개 언어 문자권별 라우팅)을 거친
# run_lda_v6_live_reference_v7.py(소스 유실)로 산출된 것이라, 이 스크립트를 10,020건 코퍼스에 그대로
# 돌리면 문서 수·어휘·K-grid 수치가 달라진다(README.md "재현성 범위" 참고).
# ------------------------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parent
_ap = argparse.ArgumentParser(description="LDA v6 pipeline (K-grid -> Meta Factor -> Fan Factor Matrix -> scores)")
_ap.add_argument("--data", default=str(_BASE / "data" / "v7_final" / "fandoms_v3_100.json"),
                 help="근거문장 코퍼스 JSON (fandoms_v3_100.json 스키마)")
_ap.add_argument("--out", default=str(_BASE / "output" / "lda_rerun"), help="산출물 저장 디렉터리")
_args = _ap.parse_args()
DATA = _args.data
OUT = _args.out
os.makedirs(OUT, exist_ok=True)
with open(DATA, encoding="utf-8") as f:
    fandoms = json.load(f)
print(f"[0] DATA={DATA}\n[0] OUT={OUT}")

# ============================================================
# 1. Corpus construction (v6.1 FIX: English function words were leaking through the v3
#    tokenizer uncaught — v5/v6's expanded corpus pulled in enough English-language
#    sources (global media, Wikipedia) that generic words like "the/and/of/in/on/first"
#    became frequent enough to form their own bogus "topics", which then surfaced as
#    meaningless Meta Factors (F1 "기타형·the형", F2 "기타형·copies형", F3 "기타형·out형" in
#    the pre-fix v6 run). Fix: filter English stopwords + pure-numeric tokens, and extend
#    LABEL_RULES with English keywords so genuine English-language topics (concert/tour/
#    album/chart vocabulary that IS meaningful) still map to a real label instead of the
#    "기타형" default.)
# ============================================================
PARTICLES = ["으로부터","까지","에서부터","이라는","라는","에서","으로","까지","부터","에게","한테","에는","에도",
             "이나","라도","이며","하며","되어","됐다","했다","한다","됨","임","은","는","이","가","을","를",
             "의","와","과","도","만","로","에","고","서","다","며"]
STOPWORDS = {"있다","없다","되다","됐다","한다","했다","이다","아니다","통해","위해","대해","대한","관련",
             "이후","당시","통한","밝혔다","전했다","나타났다","것으로","것이다","것을","것은","것이",
             "라고","이라고","하는","되는","있는","없는"}
# English function/stopwords (v6.1 fix): standard closed-class words that carry no topical
# signal but were previously passing straight through the [가-힣A-Za-z0-9]{2,} token filter.
ENGLISH_STOPWORDS = {
    "the","and","of","in","on","at","for","with","from","to","by","as","is","was","were",
    "be","been","being","this","that","these","those","it","its","his","her","their","our",
    "your","my","he","she","they","we","you","who","whom","which","what","when","where",
    "while","since","into","onto","out","off","up","down","over","under","across","per",
    "via","amid","among","between","during","after","before","than","such","very","so",
    "no","not","but","or","if","then","also","more","most","much","many","some","any",
    "all","each","other","another","both","few","new","first","second","third","one","two",
    "three","said","says","according","announced","reported","included","including","have",
    "has","had","will","would","can","could","should","may","might","did","does","do",
    "an","a","are","about","up","out","officially","recently","previously","currently",
}

def tokenize(text):
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    out = []
    for t in tokens:
        tt = t
        for p in sorted(PARTICLES, key=len, reverse=True):
            if len(tt) > len(p) + 1 and tt.endswith(p):
                tt = tt[: -len(p)]
                break
        if len(tt) < 2 or tt in STOPWORDS:
            continue
        low = tt.lower()
        if low in ENGLISH_STOPWORDS:
            continue
        if tt.isdigit():  # bare numbers ("000", "2025") carry no topical meaning on their own
            continue
        out.append(tt)
    return out

docs, raw_texts, meta = [], [], []
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for item in fd.get(tag, []):
            txt, url = item["t"], item.get("u", "")
            toks = tokenize(txt)
            if len(toks) < 3:
                continue
            docs.append(" ".join(toks))
            raw_texts.append(txt)
            meta.append({"fandom": fd["fandom"], "category": fd["category"], "tag": tag, "url": url})

print(f"[1] Corpus: {len(docs)} documents (bullets) from {len(fandoms)} fandoms")

vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
X = vectorizer.fit_transform(docs)
vocab = vectorizer.get_feature_names_out()
Xbin = (X > 0).astype(int)  # binary doc-term presence, for coherence
doc_freq = np.asarray(Xbin.sum(axis=0)).ravel()  # doc frequency per word
print(f"[1] Vocab: {len(vocab)}  DTM: {X.shape}")

# ============================================================
# 2. Multi-K model selection: perplexity, coherence, diversity, stability
# ============================================================
def umass_coherence(topic_word, top_n=10):
    """Average UMass coherence across topics. Uses real co-document-frequency from the corpus
    (no external corpus needed) — standard formulation:
    C = (2/(N*(N-1))) * sum_{i<j} log((D(wi,wj)+1)/D(wi))"""
    Xbin_csc = Xbin.tocsc()
    coh_scores = []
    for t in range(topic_word.shape[0]):
        top_idx = topic_word[t].argsort()[::-1][:top_n]
        pair_scores = []
        for i in range(1, len(top_idx)):
            for j in range(i):
                wi, wj = top_idx[i], top_idx[j]
                d_wi = doc_freq[wi]
                if d_wi == 0:
                    continue
                co = Xbin_csc[:, wi].multiply(Xbin_csc[:, wj]).sum()
                pair_scores.append(math.log((co + 1) / d_wi))
        if pair_scores:
            coh_scores.append(sum(pair_scores) / len(pair_scores))
    return float(np.mean(coh_scores)) if coh_scores else float("nan")

def topic_diversity(topic_word, top_n=10):
    K = topic_word.shape[0]
    words = set()
    for t in range(K):
        top_idx = topic_word[t].argsort()[::-1][:top_n]
        words.update(top_idx.tolist())
    return len(words) / (K * top_n)

def seed_stability(k, n_seeds=3, top_n=10):
    """Fit the same K with different random seeds; match topics by top-word Jaccard overlap,
    average best-match Jaccard as a reproducibility score (1.0 = perfectly stable)."""
    runs = []
    for seed in range(1, n_seeds + 1):
        m = LatentDirichletAllocation(n_components=k, random_state=seed, max_iter=50,
                                       learning_method="batch")
        m.fit(X)
        top_sets = [set(m.components_[t].argsort()[::-1][:top_n].tolist()) for t in range(k)]
        runs.append(top_sets)
    scores = []
    for a, b in itertools.combinations(range(len(runs)), 2):
        for sa in runs[a]:
            best = max((len(sa & sb) / len(sa | sb) for sb in runs[b]), default=0)
            scores.append(best)
    return float(np.mean(scores)) if scores else float("nan")

candidates = [8, 10, 12, 15, 20, 25, 30]  # per strategy doc: K=8 preserved as baseline, grid K=8~30
grid = []
fitted = {}
print("\n[2] K-grid evaluation (perplexity / coherence / diversity / stability):")
for k in candidates:
    lda = LatentDirichletAllocation(n_components=k, random_state=0, max_iter=50,
                                     learning_method="batch")
    lda.fit(X)
    perp = lda.perplexity(X)
    coh = umass_coherence(lda.components_)
    div = topic_diversity(lda.components_)
    stab = seed_stability(k)
    grid.append({"k": k, "perplexity": round(perp, 1), "coherence": round(coh, 3),
                 "diversity": round(div, 3), "stability": round(stab, 3)})
    fitted[k] = lda
    print(f"  k={k:>2}  perplexity={perp:8.1f}  coherence={coh:7.3f}  diversity={div:.3f}  stability={stab:.3f}")

# Composite ranking: perplexity (lower better) rank + coherence(higher better) rank
# + diversity(higher better) rank + stability(higher better) rank -> lowest sum wins.
def rank_asc(vals):   # lower value -> better rank (1 = best)
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0] * len(vals)
    for r, i in enumerate(order):
        ranks[i] = r + 1
    return ranks

def rank_desc(vals):  # higher value -> better rank
    return rank_asc([-v for v in vals])

perp_r = rank_asc([g["perplexity"] for g in grid])
coh_r = rank_desc([g["coherence"] for g in grid])
div_r = rank_desc([g["diversity"] for g in grid])
stab_r = rank_desc([g["stability"] for g in grid])
for i, g in enumerate(grid):
    g["composite_rank_sum"] = perp_r[i] + coh_r[i] + div_r[i] + stab_r[i]

best_idx = min(range(len(grid)), key=lambda i: grid[i]["composite_rank_sum"])
K = grid[best_idx]["k"]
lda_model = fitted[K]
print(f"\n[2] Selected K={K} by combined rank of perplexity+coherence+diversity+stability "
      f"(baseline-lowest-perplexity was K={candidates[np.argmin([g['perplexity'] for g in grid])]})")

doc_topic = lda_model.transform(X)     # theta: (n_docs, K)
topic_word = lda_model.components_      # phi:   (K, vocab)

def top_words(t, n=10):
    order = topic_word[t].argsort()[::-1][:n]
    return [vocab[i] for i in order]

topics_top_words = {t: top_words(t) for t in range(K)}
print("\n[2] Final topics:")
for t in range(K):
    print(f"  T{t}: {', '.join(topics_top_words[t][:8])}")

# ============================================================
# 3. Topic -> Meta Factor (hierarchical clustering on cosine similarity of Phi)
# ============================================================
phi_norm = topic_word / (np.linalg.norm(topic_word, axis=1, keepdims=True) + 1e-12)
cos_sim = phi_norm @ phi_norm.T
cos_dist = 1 - cos_sim
np.fill_diagonal(cos_dist, 0)
cos_dist = np.clip(cos_dist, 0, None)

M_CANDIDATES = [m for m in range(5, 9) if m < K]
best_m, best_sil, best_labels = None, -2, None
for m in M_CANDIDATES:
    if m < 2 or m >= K:
        continue
    cl = AgglomerativeClustering(n_clusters=m, metric="precomputed", linkage="average")
    labels = cl.fit_predict(cos_dist)
    if len(set(labels)) < 2:
        continue
    try:
        sil = silhouette_score(cos_dist, labels, metric="precomputed")
    except ValueError:
        continue
    print(f"[3] Meta-Factor M={m}  silhouette={sil:.3f}")
    if sil > best_sil:
        best_m, best_sil, best_labels = m, sil, labels

if best_labels is None:
    # fallback: fixed M=6 or K itself if K is already small; still compute a real
    # silhouette score for this fallback so diagnostics never report a sentinel value.
    best_m = min(6, max(2, K - 1))
    cl = AgglomerativeClustering(n_clusters=best_m, metric="precomputed", linkage="average")
    best_labels = cl.fit_predict(cos_dist)
    if len(set(best_labels)) >= 2:
        try:
            best_sil = silhouette_score(cos_dist, best_labels, metric="precomputed")
        except ValueError:
            best_sil = float("nan")
    else:
        best_sil = float("nan")

M = best_m
topic_to_factor = {t: int(best_labels[t]) for t in range(K)}
print(f"[3] Selected M={M} Meta Factors (silhouette={best_sil:.3f})")

# Label each Meta Factor from the pooled top words of its member topics
factor_words = defaultdict(Counter)
for t in range(K):
    for w in topics_top_words[t][:8]:
        factor_words[topic_to_factor[t]][w] += 1
factor_top_words = {m: [w for w, _ in factor_words[m].most_common(8)] for m in range(M)}

# Human-readable labels based on dominant vocabulary theme (heuristic keyword match, documented)
# v6.1 fix: each bucket now carries BOTH Korean and English keywords. Before the tokenizer
# fix, English-dominant topics never matched these Korean-only lists and fell through to the
# "기타형" default; after the fix, the English content words that remain (concert/tour/album/
# chart vocabulary — genuinely meaningful, not stopwords) need an English-side match too.
LABEL_RULES = [
    ("결속형(팬클럽·기부·커뮤니티)", {"공식","팬클럽","팬덤","팬카페","팬들","커뮤니티","기부",
        "fanclub","fandom","fans","community","donated","donation","charity","volunteer","relief"}),
    ("소비력형(초동·판매·앨범)", {"기록","앨범","판매","판매량","발매","음반","누적","세웠",
        "album","albums","sales","sold","copies","units","million","ep","selling"}),
    ("현장경제형(콘서트·투어·매진)", {"콘서트","공연","티켓","매진","단독","투어","전석","관객","동원",
        "concert","concerts","tour","tickets","sold-out","soldout","venue","shows","world"}),
    ("브랜드·상업형(광고·앰버서더)", {"브랜드","모델","광고","앰버서더","발탁","글로벌",
        "brand","ambassador","endorsement","campaign","model","global"}),
    ("차트·확산형(1위·빌보드·기록)", {"1위","차트","빌보드","기록","올랐","오르","연속","최초",
        "chart","charts","billboard","number","consecutive","record","records"}),
    ("미디어노출형(방송·조회수)", {"무대","방송","출연","조회수","음악방송","공개",
        "stage","broadcast","views","performance","music show","released"}),
    # v6.3 추가: 시장(Market) 보강 리서치 라운드에서 빌보드 진입·해외 시상식 관련 근거가 늘며
    # "수상/시상식/매출/흥행" 어휘가 하나의 실제 토픽으로 새로 뭉쳤으나 기존 6개 버킷 중 어디에도
    # 매칭되지 않아 "기타형"으로 잘못 라벨링되던 문제를 수정 — 새 버킷을 추가해 실제 어휘를 반영.
    ("성과·수상형(시상식·매출·흥행)", {"수상","시상식","대상","흥행","매출","실적","최우수","공로상","베스트",
        "award","awards","winner","won","ceremony","choice","grammy"}),
]
def label_for_factor(words):
    wordset = set(words)
    best_label, best_overlap = "기타형", 0
    for label, kws in LABEL_RULES:
        overlap = len(wordset & kws)
        if overlap > best_overlap:
            best_overlap, best_label = overlap, label
    return best_label

raw_factor_labels = {m: label_for_factor(factor_top_words[m]) for m in range(M)}

# Guarantee label uniqueness: two distinct Meta Factors can share the same nearest
# LABEL_RULES bucket (e.g. two different topic clusters both reading as "결속형"). Since
# factor_share / the CSV header / dominant_factor all key off the label STRING downstream,
# a duplicate label would silently collide (one factor's share overwriting another's) —
# so any bucket claimed by more than one m gets disambiguated with its own distinctive
# top word (a word not part of the generic LABEL_RULES vocabulary for that bucket).
_all_rule_kws = set()
for _, _kws in LABEL_RULES:
    _all_rule_kws |= _kws
_label_counts = Counter(raw_factor_labels.values())
factor_labels = {}
_used_labels = set()
for m in range(M):
    base = raw_factor_labels[m]
    if _label_counts[base] > 1:
        # prefer a meaningful (non-year, non-numeric) distinguishing word; fall back to any
        # remaining word only if every candidate is a bare year/number token.
        non_rule_words = [w for w in factor_top_words[m] if w not in _all_rule_kws]
        distinctive = next((w for w in non_rule_words if not re.match(r"^\d", w)), None)
        if distinctive is None:
            distinctive = non_rule_words[0] if non_rule_words else None
        candidate = f"{base}·{distinctive}형" if distinctive else base
        if candidate in _used_labels:
            n = 2
            while f"{candidate}({n})" in _used_labels:
                n += 1
            candidate = f"{candidate}({n})"
        factor_labels[m] = candidate
    else:
        factor_labels[m] = base
    _used_labels.add(factor_labels[m])
assert len(set(factor_labels.values())) == M, "Meta Factor labels must be unique (dict keys downstream depend on this)"

print("[3] Meta Factor labels:")
for m in range(M):
    print(f"  F{m} [{factor_labels[m]}]: {', '.join(factor_top_words[m])}")

# ============================================================
# 4. Fan Factor Matrix — theta-weighted share per fandom per Meta Factor
#    FactorShare(f,m) = sum_{d in f} sum_{t in m} theta(d,t)  /  sum_{d in f} sum_t theta(d,t)
# ============================================================
fandom_doc_idx = defaultdict(list)
for i, mrow in enumerate(meta):
    fandom_doc_idx[mrow["fandom"]].append(i)

topic_to_factor_arr = np.array([topic_to_factor[t] for t in range(K)])

fan_factor = {}
for fname, idxs in fandom_doc_idx.items():
    theta_sum = doc_topic[idxs].sum(axis=0)  # (K,)
    factor_sum = np.zeros(M)
    for t in range(K):
        factor_sum[topic_to_factor_arr[t]] += theta_sum[t]
    total = factor_sum.sum()
    share = (factor_sum / total) if total > 0 else np.zeros(M)
    fan_factor[fname] = share

# Factor Diversity (Shannon entropy, normalized 0-1 by log(M))
def entropy(p):
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    h = -np.sum(p * np.log(p))
    return float(h / math.log(M)) if M > 1 else 0.0

factor_diversity = {f: entropy(share) for f, share in fan_factor.items()}

# ============================================================
# 5. Coverage Index — FULL 5-component implementation (v6.2 EXPANSION):
#    Language(30%) + Market(25%) + Source-Type(20%) + Time(15%) + Entity(10%), from real
#    URLs + bullet text — matching the original strategy doc's proposed weights exactly.
#    (kept SEPARATE from Loyalty/Spillover Impact; never multiplied into the score)
#
#    v6.1 shipped only 2/5 components (Language, Source-Type) because Market/Time/Entity
#    were judged to need per-bullet metadata tags that were never collected. This version
#    implements all 5 using signal already present in the data (source URL + bullet text)
#    instead of new tags — each method and its honest limitations are documented inline.
# ============================================================
EN_GLOBAL_DOMAINS = {
    "en.wikipedia.org", "billboard.com", "forbes.com", "hollywoodreporter.com",
    "soompi.com", "allkpop.com", "complex.com", "nextshark.com", "gizmodo.com",
    "malaymail.com", "news24online.com", "nme.com", "gulfnews.com", "variety.com",
    "koreaherald.com", "koreatimes.co.kr", "pressreader.com", "vietnam.vn",
    "thejakartapost.com", "koreatimes.com",
}
# v6.2: language classification extended from binary EN/KR to 6 tracked languages
# (ko/en/ja/zh/es/fr), by user request. Domain lists below are real but, as documented in
# [5c] below, the actual v6 corpus turns out to contain almost no ja/zh/es/fr sources.
JP_DOMAINS = {
    "ygex.jp", "barks.jp", "natalie.mu", "oricon.co.jp", "nikkansports.com", "hochi.news",
    "sponichi.co.jp", "asahi.com", "yomiuri.co.jp", "mainichi.jp", "nikkei.com", "daily.co.jp",
}
CN_DOMAINS = {
    "sina.com.cn", "weibo.com", "163.com", "people.com.cn", "xinhuanet.com", "qq.com",
    "ifeng.com", "douban.com", "baidu.com", "zhihu.com",
}
ES_DOMAINS = {
    "elpais.com", "marca.com", "abc.es", "elmundo.es", "clarin.com", "infobae.com",
    "univision.com", "telemundo.com",
}
FR_DOMAINS = {
    "lemonde.fr", "lefigaro.fr", "liberation.fr", "francetvinfo.fr", "leparisien.fr",
}
COMMUNITY_SOCIAL_DOMAINS = {
    "reddit.com", "x.com", "twitter.com", "facebook.com", "instagram.com", "threads.com",
}
WIKI_DOMAINS = {"en.wikipedia.org", "ko.wikipedia.org", "namu.wiki", "wikipedia.org"}
LANGS = ["ko", "en", "ja", "zh", "es", "fr"]  # the 6 tracked languages (denominator for entropy)

def domain_of(url):
    try:
        d = urlparse(url).netloc.lower()
        return d[4:] if d.startswith("www.") else d
    except Exception:
        return ""

def _domain_in(d, domain_set):
    return any(d == dd or d.endswith("." + dd) for dd in domain_set)

def source_type_of(url):
    d = domain_of(url)
    if _domain_in(d, COMMUNITY_SOCIAL_DOMAINS):
        return "community_social"
    if _domain_in(d, WIKI_DOMAINS):
        return "reference_wiki"
    return "news_media"

# [5a] Language: domain rules first (ja/zh/es/fr/en_global), Korean-language site as default.
# For Japanese only, a text-based fallback (hiragana/katakana Unicode range) is ADDED because
# kana cannot appear by accident in Korean/English text — a zero-false-positive signal — so it
# can safely catch a JA-language article hosted on a non-JP-listed domain. The same fallback
# was tested for zh/es/fr and REJECTED: hanzi false-positive on decorative Korean hanja (e.g.
# "佳人의 선물"), and accented-Latin false-positived on brand names ("L'Oréal", "México",
# "pookïe") rather than real Spanish/French prose — see [5c] for the actual test results.
_JP_KANA_RE = re.compile(r"[\u3040-ヿ]")

def language_of(url, text=""):
    d = domain_of(url)
    if _domain_in(d, JP_DOMAINS):
        return "ja"
    if _domain_in(d, CN_DOMAINS):
        return "zh"
    if _domain_in(d, ES_DOMAINS):
        return "es"
    if _domain_in(d, FR_DOMAINS):
        return "fr"
    if _domain_in(d, EN_GLOBAL_DOMAINS) or d in ("reddit.com", "x.com", "twitter.com"):
        return "en"
    if _JP_KANA_RE.search(text):
        return "ja"
    return "ko"

def entropy_norm(counts, n_categories):
    """Shannon entropy of a category-count distribution, normalized by log(n_categories) —
    same construction as FactorDiversity in section 4, so both 'coverage breadth' metrics in
    this pipeline share one interpretable 0~1 scale. Returns 0 for n_categories<=1 or empty."""
    total = sum(counts.values())
    if total == 0 or n_categories <= 1:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p)
    return float(h / math.log(n_categories))

# [5b] Market: which international markets a fandom's press coverage actually TALKS ABOUT
# (not merely which language the source is written in — a Korean-language article about a
# Japan tour still counts as Japan-market coverage). Detected via keyword search on bullet
# text; a bullet may hit more than one region. Validated against the real corpus before
# adoption — see [5c].
MARKET_KEYWORDS = {
    "일본": ["일본", "도쿄", "오사카", "재팬", "japan", "tokyo", "osaka"],
    "중화권": ["중국", "대만", "홍콩", "상하이", "베이징", "china", "taiwan", "hong kong", "beijing", "shanghai"],
    "미국_북미": ["미국", "뉴욕", "북미", "america", "usa", "new york", "los angeles", "billboard", "grammy"],
    "유럽": ["유럽", "런던", "파리", "europe", "london", "paris"],
    "동남아": ["동남아", "태국", "베트남", "필리핀", "인도네시아", "싱가포르", "말레이시아",
              "southeast asia", "thailand", "vietnam", "philippines", "indonesia", "singapore", "malaysia"],
    "글로벌": ["글로벌", "전세계", "월드투어", "해외", "global", "worldwide", "world tour"],
}
MARKET_REGIONS = list(MARKET_KEYWORDS.keys())

def markets_in(text):
    tl = text.lower()
    return {region for region, kws in MARKET_KEYWORDS.items() if any(kw.lower() in tl for kw in kws)}

# [5c] Time: distinct calendar years referenced in a fandom's evidence text, as a fraction of
# every year referenced anywhere in the v6 corpus — "how much of the corpus's own timeline does
# this fandom's evidence actually span."
# v6.3 FIX: the original \b...\b boundary regex silently failed to match a year immediately
# followed by a Korean suffix like "2025년" — Python's \w (and therefore \b) treats Hangul as a
# word character, so there is no boundary between "5" and "년". Since a large share of this
# corpus's dates are written exactly that way ("2025년 3월" etc.), this undercounted real year
# mentions by more than half (empirically: 24.2% of bullets detected under the old regex vs.
# 56.0% under this fix, on the same v6.3 corpus). Replaced with a digit-adjacency check that
# doesn't rely on \b at all, so it works the same regardless of what script follows the digits.
_YEAR_RE = re.compile(r"(?<!\d)(20[0-2][0-9])(?!\d)")

def years_in(text):
    return {y for y in _YEAR_RE.findall(text) if 2015 <= int(y) <= 2026}

# [5d] Entity: distinct THIRD-PARTY organizations/platforms named in a fandom's evidence,
# grouped into 6 categories (broadcaster / domestic chart / overseas chart-award / global
# digital platform / major venue / media-award outlet). This is a curated keyword list, not a
# general NER model — same "documented heuristic, not ground truth" caveat that already
# applies to the Meta Factor LABEL_RULES elsewhere in this pipeline.
ENTITY_CATEGORIES = {
    "방송사": ["KBS", "MBC", "SBS", "JTBC", "Mnet", "엠넷"],
    "음원차트_국내": ["멜론", "지니", "벅스", "플로", "가온"],
    "해외차트_시상식": ["빌보드", "Billboard", "오리콘", "Oricon", "AMA", "그래미", "Grammy", "골든디스크"],
    "글로벌플랫폼": ["유튜브", "YouTube", "스포티파이", "Spotify", "넷플릭스", "Netflix", "위버스", "Weverse",
                  "틱톡", "TikTok", "인스타그램", "Instagram"],
    "대형공연장": ["올림픽공원", "올림픽홀", "KSPO", "고척돔", "잠실체육관", "아레나", "코첼라", "Coachella"],
    "매체_어워드": ["포브스", "Forbes", "보그", "Vogue", "엘르", "Elle", "서울가요대상"],
}
ENTITY_TYPES = list(ENTITY_CATEGORIES.keys())

def _kw_hit(text, kw):
    if re.match(r"^[A-Za-z]+$", kw):
        return re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE) is not None
    return kw in text

def entities_in(text):
    return {cat for cat, kws in ENTITY_CATEGORIES.items() if any(_kw_hit(text, kw) for kw in kws)}

fan_urls = defaultdict(list)
fan_bullets = defaultdict(list)  # (url, text) pairs, for the text-dependent sub-metrics
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for item in fd.get(tag, []):
            u, t = item.get("u", ""), item.get("t", "")
            fan_urls[fd["fandom"]].append(u)
            fan_bullets[fd["fandom"]].append((u, t))

# Corpus-wide year range, used as the Time Coverage denominator (see [5c])
_corpus_years = set()
for _, bullets in fan_bullets.items():
    for _, t in bullets:
        _corpus_years |= years_in(t)
CORPUS_YEARS = sorted(_corpus_years)
N_CORPUS_YEARS = len(CORPUS_YEARS) or 1

W_LANG, W_MARKET, W_TYPE, W_TIME, W_ENTITY = 0.30, 0.25, 0.20, 0.15, 0.10  # strategy-doc weights

coverage_index = {}
coverage_detail = {}
for fname, bullets in fan_bullets.items():
    urls = [u for u, _ in bullets]
    texts = [t for _, t in bullets]
    n = len(bullets)

    langs = [language_of(u, t) for u, t in bullets]
    types = [source_type_of(u) for u in urls]
    lang_counts = Counter(langs)
    language_coverage = entropy_norm(lang_counts, len(LANGS))

    market_hits = set()
    for t in texts:
        market_hits |= markets_in(t)
    market_coverage = len(market_hits) / len(MARKET_REGIONS)

    n_types_present = len(set(types))
    source_type_coverage = n_types_present / 3.0  # 3 categories tracked (unchanged from v6.1)

    year_hits = set()
    for t in texts:
        year_hits |= years_in(t)
    time_coverage = len(year_hits) / N_CORPUS_YEARS

    entity_hits = set()
    for t in texts:
        entity_hits |= entities_in(t)
    entity_coverage = len(entity_hits) / len(ENTITY_TYPES)

    idx = round(
        W_LANG * language_coverage + W_MARKET * market_coverage + W_TYPE * source_type_coverage
        + W_TIME * time_coverage + W_ENTITY * entity_coverage, 3
    )
    coverage_index[fname] = idx
    coverage_detail[fname] = {
        "n_evidence": n,
        "language_coverage": round(language_coverage, 3),
        "language_counts": dict(lang_counts),
        "market_coverage": round(market_coverage, 3),
        "markets_mentioned": sorted(market_hits),
        "source_type_coverage": round(source_type_coverage, 3),
        "source_type_counts": dict(Counter(types)),
        "time_coverage": round(time_coverage, 3),
        "years_mentioned": sorted(year_hits),
        "entity_coverage": round(entity_coverage, 3),
        "entity_types_mentioned": sorted(entity_hits),
        "weights": {"language": W_LANG, "market": W_MARKET, "source_type": W_TYPE,
                    "time": W_TIME, "entity": W_ENTITY},
    }

_corpus_lang_counts = Counter(l for fname in fan_bullets for l in
                               [language_of(u, t) for u, t in fan_bullets[fname]])
print(f"\n[5] Coverage Index computed for {len(coverage_index)} fandoms "
      f"(FULL 5-component version: Language {W_LANG:.0%} + Market {W_MARKET:.0%} + "
      f"Source-Type {W_TYPE:.0%} + Time {W_TIME:.0%} + Entity {W_ENTITY:.0%}, matching the "
      f"strategy doc's proposed weights). Corpus-wide language distribution: "
      f"{dict(_corpus_lang_counts)} — ja/zh/es/fr sources are real but vanishingly rare in "
      f"this corpus (documented as a finding, not hidden). Corpus year range: "
      f"{CORPUS_YEARS[0]}-{CORPUS_YEARS[-1]} ({N_CORPUS_YEARS} distinct years).")

# ============================================================
# 6. Loyalty / Spillover raw+normalized scores — UNCHANGED formula (kept as explanatory axis,
#    per the strategy docs' explicit instruction not to discard it)
# ============================================================
NUM_PATTERN = re.compile(r"\d+[\.,]?\d*\s*(만|억|조|%|명|장|위|회|건|주|배|년)")
LOYALTY_BONUS_KW = ["기부","돌파","매진","출범","창단","결성","총공","역사","지속","확장","1위","최초","신기록",
                     "밀리언셀러","팬클럽","팬카페","결속","충성","세대"]
SPILLOVER_BONUS_KW = ["경제효과","매출","관광","지자체","앰버서더","모델","브랜드","팝업","협업","관중","방문",
                       "상권","지역","홍보대사","수익","투어","콘서트","소비"]

def evidence_score(items, bonus_kw):
    score = 0.0
    for it in items:
        txt = it["t"]
        score += 1.0
        score += 0.5 * len(NUM_PATTERN.findall(txt))
        score += 0.3 * sum(1 for kw in bonus_kw if kw in txt)
    return score

results = []
for fd in fandoms:
    fname = fd["fandom"]
    loy_raw = evidence_score(fd.get("loyalty", []), LOYALTY_BONUS_KW)
    spi_raw = evidence_score(fd.get("spillover", []), SPILLOVER_BONUS_KW)
    share = fan_factor.get(fname, np.zeros(M))
    results.append({
        "fandom": fname, "fanclub": fd["fanclub"], "category": fd["category"],
        "loyalty_raw": loy_raw, "spillover_raw": spi_raw,
        "n_loyalty_bullets": len(fd.get("loyalty", [])), "n_spillover_bullets": len(fd.get("spillover", [])),
        "factor_share": {factor_labels[m]: round(float(share[m]), 4) for m in range(M)},
        "factor_diversity": round(factor_diversity.get(fname, 0.0), 4),
        "coverage_index": coverage_index.get(fname, 0.0),
        "coverage_detail": coverage_detail.get(fname, {}),
    })

loy_vals = [r["loyalty_raw"] for r in results]
spi_vals = [r["spillover_raw"] for r in results]
loy_min, loy_max = min(loy_vals), max(loy_vals)
spi_min, spi_max = min(spi_vals), max(spi_vals)
for r in results:
    r["loyalty_score"] = round((r["loyalty_raw"] - loy_min) / (loy_max - loy_min), 3)
    r["spillover_score"] = round((r["spillover_raw"] - spi_min) / (spi_max - spi_min), 3)
    r["activity"] = r["n_loyalty_bullets"] + r["n_spillover_bullets"]
    # dominant factor = argmax of factor_share
    r["dominant_factor"] = max(r["factor_share"], key=r["factor_share"].get)

results.sort(key=lambda r: (-r["loyalty_score"] - r["spillover_score"]))

# ============================================================
# 7. Member Mention Pilot (TEXT-MINING ONLY on already-collected bullets — no new research)
# ============================================================
MEMBER_ALIASES = {
    "BTS": {"RM":["RM","김남준"], "진":["진","Jin","석진"], "슈가":["슈가","SUGA","민윤기"],
            "제이홉":["제이홉","j-hope","정호석"], "지민":["지민","Jimin","박지민"],
            "뷔":["뷔","V ","김태형"], "정국":["정국","Jungkook","전정국"]},
    "빅뱅": {"지드래곤":["지드래곤","G-DRAGON","GD","권지용"], "태양":["태양","TAEYANG","동영배"],
             "대성":["대성","DAESUNG","강대성"], "탑":["T.O.P","최승현"]},
    "BLACKPINK": {"지수":["지수","JISOO"], "제니":["제니","JENNIE"], "로제":["로제","ROSÉ","ROSE"],
                  "리사":["리사","LISA"]},
    "EXO": {"디오":["디오","D.O.","도경수"], "백현":["백현","Baekhyun"], "카이":["카이","Kai","김종인"],
            "수호":["수호","Suho"], "찬열":["찬열","Chanyeol"], "세훈":["세훈","Sehun"],
            "시우민":["시우민","Xiumin"], "첸":["첸","Chen"], "레이":["레이","Lay"]},
    "슈퍼주니어": {"규현":["규현","Kyuhyun"], "희철":["희철","Heechul"], "이특":["이특","Leeteuk"],
                 "신동":["신동","Shindong"], "은혁":["은혁","Eunhyuk"], "동해":["동해","Donghae"],
                 "시원":["시원","Siwon"], "예성":["예성","Yesung"]},
    "샤이니": {"태민":["태민","TAEMIN"], "키":["키 ","KEY"], "민호":["민호","MINHO"], "온유":["온유","ONEW"]},
    "소녀시대": {"태연":["태연","TAEYEON"], "윤아":["윤아","YOONA"], "수영":["수영","SOOYOUNG"],
               "유리":["유리","YURI"], "서현":["서현","SEOHYUN"], "티파니":["티파니","TIFFANY"],
               "효연":["효연","HYOYEON"], "써니":["써니","Sunny"], "제시카":["제시카","Jessica"]},
    "(여자)아이들": {"전소연":["전소연","소연"], "미연":["미연"], "민니":["민니"], "우기":["우기"], "슈화":["슈화"]},
    "마마무": {"화사":["화사"], "솔라":["솔라"], "문별":["문별"], "휘인":["휘인"]},
    "IVE": {"장원영":["장원영","원영"], "안유진":["안유진","유진"], "레이":["아이브 레이","Rei"],
            "리즈":["리즈"], "가을":["가을"], "이서":["이서"]},
}

member_pilot = {}
for group, members in MEMBER_ALIASES.items():
    fd = next((f for f in fandoms if f["fandom"] == group), None)
    if fd is None:
        continue
    all_texts = [it["t"] for tag in ("loyalty", "spillover") for it in fd.get(tag, [])]
    mention_counts = {}
    for mname, aliases in members.items():
        cnt = sum(1 for txt in all_texts if any(a.strip() in txt for a in aliases))
        mention_counts[mname] = cnt
    total = sum(mention_counts.values())
    if total == 0:
        member_pilot[group] = {"total_group_bullets": len(all_texts), "total_member_mentions": 0,
                                "member_impact_share_pilot": {}, "mci_pilot": None,
                                "note": "기존 수집 문장에서 멤버명 개별 언급이 확인되지 않음 — 그룹 단위 리서치만 수행된 상태로, "
                                        "전용 멤버 리서치가 필요함을 시사."}
        continue
    shares = {m: round(c / total, 3) for m, c in mention_counts.items()}
    mci = round(sum(s ** 2 for s in shares.values()), 3)
    member_pilot[group] = {
        "total_group_bullets": len(all_texts),
        "member_mention_counts": mention_counts,
        "total_member_mentions": total,
        "member_impact_share_pilot": shares,
        "mci_pilot": mci,
        "note": "TEXT-MINING PILOT: 그룹 단위로 이미 수집된 실제 근거문장 내 멤버명 언급 횟수 기반. "
                "멤버별 독립 리서치(광고·연기·해외활동 등)를 수행한 결과가 아니므로 참고용 1차 지표로만 해석.",
    }

n_pilot_with_data = sum(1 for v in member_pilot.values() if v["total_member_mentions"] > 0)
print(f"\n[7] Member Mention Pilot: {n_pilot_with_data}/{len(MEMBER_ALIASES)} Tier-S groups "
      f"had at least one member-name mention in already-collected bullets.")

# ============================================================
# 8. Save all outputs
# ============================================================
with open(f"{OUT}/lda_v6_diagnostics.json", "w", encoding="utf-8") as f:
    json.dump({"k_grid": grid, "selected_k": K, "selected_m_meta_factors": M,
               "meta_factor_silhouette": round(float(best_sil), 3),
               "topics_top_words": {str(k): v for k, v in topics_top_words.items()},
               "topic_to_factor": {str(k): v for k, v in topic_to_factor.items()},
               "factor_labels": {str(k): v for k, v in factor_labels.items()},
               "factor_top_words": {str(k): v for k, v in factor_top_words.items()}},
              f, ensure_ascii=False, indent=2)

with open(f"{OUT}/fandom_scores_v6.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open(f"{OUT}/member_mention_pilot_v6.json", "w", encoding="utf-8") as f:
    json.dump(member_pilot, f, ensure_ascii=False, indent=2)

with open(f"{OUT}/fandom_scores_v6.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    header = ["fandom", "category", "loyalty_score", "spillover_score", "coverage_index",
              "factor_diversity", "dominant_factor", "activity"] + [factor_labels[m] for m in range(M)]
    w.writerow(header)
    for r in results:
        row = [r["fandom"], r["category"], r["loyalty_score"], r["spillover_score"],
               r["coverage_index"], r["factor_diversity"], r["dominant_factor"], r["activity"]]
        row += [r["factor_share"].get(factor_labels[m], 0) for m in range(M)]
        w.writerow(row)

print(f"\n[8] Saved: lda_v6_diagnostics.json, fandom_scores_v6.json, member_mention_pilot_v6.json, fandom_scores_v6.csv")
print("\n=== Top 15 by Loyalty+Spillover (v6, same formula as v3/v4/v5, further-expanded corpus) ===")
for r in results[:15]:
    print(f"{r['fandom']:16s} loy={r['loyalty_score']:.2f} spi={r['spillover_score']:.2f} "
          f"cov={r['coverage_index']:.2f} div={r['factor_diversity']:.2f} dom={r['dominant_factor']}")
