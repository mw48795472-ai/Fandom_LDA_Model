# -*- coding: utf-8 -*-
"""재구성 라우팅 토크나이저(run_lda_v6_live_reference_v7.py 의 === TOKENIZER BEGIN/END === 절)를 저장소에 남아 있는
원본 실행 결과와 대조한다. 원본 소스가 없으므로 이 대조가 재구성의 유일한 근거다.

목표값 (전부 저장소 파일):
  ① data/v7_final/lda_excluded_bullets_v7.json — 3토큰 미만 제외 2건과 그 토큰, 문서 수 10,018
  ② data/v7_final/wordcloud_by_language_v7.json — 8개 버킷별 불릿 수·토큰 수·어휘 종수·상위 30단어 카운트, 총 토큰 170,725
  ③ TOKENIZER_WORDCLOUD_REPORT.md 4절 — 자기인용 슬러그가 제거된 불릿 811건
버킷 분류 규칙은 wordcloud_by_language_v7.json 의 methodology 필드를 그대로 구현했다(한글/키릴/베트남 성조/악센트+문맥/ASCII,
ASCII 토큰은 wordfreq 로 영어 zipf<1.5 이면서 es·fr·pt·id·ms·tl·tr 중 zipf≥3.5 인 것만 비영어).

실행: python verify_tokenizer_reconstruction_v7.py   (fugashi unidic-lite jieba pythainlp wordfreq 필요, 약 20초)
출력: 같은 폴더 tokenizer_reconstruction_check_v7.json + 콘솔 표
"""
import json, re, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

# --- 토크나이저 절을 마커로 잘라 실행 (원본 파이프라인이 다른 스크립트에서 쓰던 방식과 같음)
src = (REPO / "run_lda_v6_live_reference_v7.py").read_text(encoding="utf-8")
block = src[src.index("# === TOKENIZER BEGIN ===") + len("# === TOKENIZER BEGIN ==="):src.index("# === TOKENIZER END ===")]
ns = {"re": re, "__name__": "tok_block"}
exec("import re\nfrom urllib.parse import urlparse\n" + block, ns)
tokenize_parts, strip_domain_fragments, tokenize_generic = ns["tokenize_parts"], ns["strip_domain_fragments"], ns["tokenize_generic"]

fandoms = json.load(open(REPO / "data/v7_final/fandoms_v3_100.json", encoding="utf-8"))
W = json.load(open(REPO / "data/v7_final/wordcloud_by_language_v7.json", encoding="utf-8"))
target = {b["bucket"].split("(")[0]: b for b in W["buckets"]}
EXCL = json.load(open(REPO / "data/v7_final/lda_excluded_bullets_v7.json", encoding="utf-8"))

RE_HANGUL = re.compile(r"[가-힣]"); RE_CYR = re.compile(r"[Ѐ-ӿ]")
RE_VI = re.compile(r"[đĐơƠưƯḀ-ỿ]"); RE_ACC = re.compile(r"[À-ɏ]")
try:
    from wordfreq import zipf_frequency
except ImportError:
    sys.exit("wordfreq 가 필요합니다: pip install wordfreq")


def classify(tokens):
    vi_signal = any(RE_VI.search(t) for t in tokens)
    for t in tokens:
        if RE_HANGUL.search(t): yield "한국어", t
        elif RE_CYR.search(t): yield "러시아어", t
        elif RE_VI.search(t): yield "베트남어", t
        elif RE_ACC.search(t): yield ("베트남어" if vi_signal else "비영어"), t
        else:
            b = "영어"
            if t.isascii() and t.isalpha() and zipf_frequency(t, "en") < 1.5 and max(zipf_frequency(t, l) for l in ("es", "fr", "pt", "id", "ms", "tl", "tr")) >= 3.5:
                b = "비영어"
            yield b, t


B = {k: {"bullets": 0, "tokens": Counter()} for k in ("한국어", "영어", "비영어", "러시아어", "베트남어", "일본어", "중국어", "태국어")}
n_docs = 0; excluded = []; selfcit = 0
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for idx, it in enumerate(fd[tag]):
            u = it.get("u", "")
            g, ja, zh, th = tokenize_parts(it["t"], u)
            if len(tokenize_generic(strip_domain_fragments(it["t"]), "")) > len(g): selfcit += 1
            allt = g + ja + zh + th
            if len(allt) < 3: excluded.append({"fandom": fd["fandom"], "tag": tag, "idx": idx, "t": it["t"], "tokens": allt})
            else: n_docs += 1
            seen = set()
            for b, t in classify(g): B[b]["tokens"][t] += 1; seen.add(b)
            for b, L in (("일본어", ja), ("중국어", zh), ("태국어", th)):
                for t in L: B[b]["tokens"][t] += 1
                if L: seen.add(b)
            for b in seen: B[b]["bullets"] += 1

rows = []
for k, v in B.items():
    T = target[k]; nt = sum(v["tokens"].values())
    top = {d["word"]: d["n"] for d in T["top_30"]}
    top_match = sum(1 for w, n in top.items() if v["tokens"].get(w, 0) == n)
    rows.append({"bucket": k, "bullets": [v["bullets"], T["n_bullets_with_any_token"]], "tokens": [nt, T["n_total_tokens"]],
                 "distinct": [len(v["tokens"]), T["n_distinct_words"]], "top30_exact": top_match,
                 "top30_diff": {w: [v["tokens"].get(w, 0), n] for w, n in top.items() if v["tokens"].get(w, 0) != n}})
tot = sum(r["tokens"][0] for r in rows)
excl_ok = (len(excluded) == 2 and {(e["fandom"], e["idx"]) for e in excluded} == {(e["fandom"], e["idx"]) for e in EXCL["excluded"]}
           and all(sorted(e["tokens"]) == sorted(next(x["tokens"] for x in EXCL["excluded"] if x["fandom"] == e["fandom"])) for e in excluded))
res = {"n_docs": [n_docs, EXCL["lda_document_count"]], "excluded_match": excl_ok, "excluded": excluded,
       "total_tokens": [tot, W["total_tokens"]], "self_citation_bullets": [selfcit, 811], "buckets": rows}
json.dump(res, open(HERE / "tokenizer_reconstruction_check_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"문서 {n_docs:,}/{EXCL['lda_document_count']:,} | 제외 2건·토큰 일치: {excl_ok} | 총 토큰 {tot:,}/{W['total_tokens']:,} ({tot/W['total_tokens']:.4%}) | 자기인용 제거 불릿 {selfcit}/811")
print(f"{'버킷':6s} {'불릿(재구성/원본)':>18s} {'토큰':>18s} {'어휘':>16s} {'top30 일치':>10s}")
for r in rows:
    print(f"{r['bucket']:6s} {r['bullets'][0]:>8,}/{r['bullets'][1]:<8,} {r['tokens'][0]:>8,}/{r['tokens'][1]:<8,} {r['distinct'][0]:>7,}/{r['distinct'][1]:<7,} {r['top30_exact']:>6}/30  {r['top30_diff'] or ''}")
