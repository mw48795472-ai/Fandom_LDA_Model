# -*- coding: utf-8 -*-
"""L14 — 본문 언어 병행 판정. 세계 언어 지수는 출처 도메인 기준(language_of)이라 본문 언어와 어긋날 수 있다.
불릿 10,020건마다 (a) 도메인 기준 언어(재구성 분류기, analysis/tokenizer/build_multilingual_bullet_language_classifier_v7.py)와
(b) 본문 기준 언어를 나란히 두고 언어별 불일치율을 잰다.

본문 언어 판정(외부 감지기 없이 결정적으로):
  1) 문자권: 한글/가나/한자/태국/키릴/아랍/라틴 글자 수로 지배 문자권을 정한다(가나가 있으면 한자도 일본어 쪽으로 센다).
  2) 라틴 문자권이면 wordfreq zipf 빈도로 8개 후보(en es fr id vi tl(fil) pt tr)의 평균 점수를 비교해 최대를 고른다.
     베트남어 고유 자모(ăâđêôơư+성조)·튀르키예어 고유 자모(ğşıİ)는 우선 규칙.
  3) '14개 외 언어' 탐지: 라틴 문자권 불릿을 wordfreq의 다른 라틴계 언어(de it nl pl ms ca ro sv da nb fi cs hu sk sl hr lt lv is)와도 비교해
     그 언어가 14개 최대값보다 zipf 0.5 이상 높고 토큰 5개 이상이면 '기타(코드)'로 적는다.

출력 (이 폴더): bullet_language_body_vs_domain_v7.csv (10,020행), body_language_summary_v7.json, BODY_LANGUAGE_V7.md
실행: python v7_final_10020/analysis/worldwide_language_index/build_body_language_classifier_v7.py
"""
import csv, importlib.util, json, math, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from wordfreq import zipf_frequency

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
D = REPO / "data" / "v7_final"
spec = importlib.util.spec_from_file_location("domcls", REPO / "v7_final_10020" / "analysis" / "tokenizer" / "build_multilingual_bullet_language_classifier_v7.py")
domcls = importlib.util.module_from_spec(spec); spec.loader.exec_module(domcls)
LANGS = domcls.LANGS
LATIN14 = ["en", "es", "fr", "id", "vi", "tl", "pt", "tr"]; WF = {"tl": "fil"}
OTHER_LATIN = ["de", "it", "nl", "pl", "ms", "ca", "ro", "sv", "da", "nb", "fi", "cs", "hu", "sk", "sl", "sh", "lt", "lv", "is"]
RE = {"ko": re.compile(r"[가-힣]"), "kana": re.compile(r"[぀-ヿ]"), "hanzi": re.compile(r"[一-鿿]"), "th": re.compile(r"[฀-๿]"),
      "ru": re.compile(r"[Ѐ-ӿ]"), "ar": re.compile(r"[؀-ۿ]"), "latin": re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]")}
VI_RE = re.compile(r"[ăâđêôơưĂÂĐÊÔƠỪ-ͯ]|[àảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]"); TR_RE = re.compile(r"[ğşıİĞŞ]")
TOK = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]{2,}")

def latin_scores(text, langs):
    toks = [t.lower() for t in TOK.findall(text)]
    if not toks: return {}, 0
    return {l: float(np.mean([zipf_frequency(t, WF.get(l, l)) for t in toks])) for l in langs}, len(toks)

def body_language(text):
    c = {k: len(r.findall(text)) for k, r in RE.items()}
    ja = c["kana"] + (c["hanzi"] if c["kana"] else 0); zh = 0 if c["kana"] else c["hanzi"]
    scripts = {"ko": c["ko"], "ja": ja, "zh": zh, "th": c["th"], "ru": c["ru"], "ar": c["ar"], "latin": c["latin"]}
    total = sum(scripts.values())
    if total == 0: return "ko", "none", 0.0, "", 0.0
    dom = max(scripts, key=scripts.get); latin_share = c["latin"] / total
    if dom != "latin": return dom, dom, round(scripts[dom] / total, 3), "", latin_share
    if VI_RE.search(text) and len(VI_RE.findall(text)) >= 2: return "vi", "latin", 1.0, "", latin_share
    if TR_RE.search(text) and len(TR_RE.findall(text)) >= 2: return "tr", "latin", 1.0, "", latin_share
    sc, n = latin_scores(text, LATIN14)
    if not sc: return "en", "latin", 0.0, "", latin_share
    best = max(sc, key=sc.get); ordered = sorted(sc.values(), reverse=True); margin = round(ordered[0] - (ordered[1] if len(ordered) > 1 else 0), 3)
    other = ""
    if n >= 5:
        so, _ = latin_scores(text, OTHER_LATIN); ob = max(so, key=so.get)
        if so[ob] - sc[best] >= 0.5: other = ob
    return best, "latin", margin, other, latin_share

corpus = json.load(open(D / "fandoms_v3_100.json", encoding="utf-8"))
scores = {r["fandom"]: r for r in json.load(open(D / "fandom_scores_live_reference_v7.json", encoding="utf-8"))}
rows = []; dom_tot = Counter(); body_tot = Counter(); other_tot = Counter(); cross = defaultdict(Counter); per_f_body = defaultdict(Counter); per_f_dom = defaultdict(Counter)
for fd in corpus:
    for tag in ("loyalty", "spillover"):
        for idx, it in enumerate(fd[tag]):
            u, _ = domcls.sanitize_bullet_url_field(it.get("u", "") or ""); urls = domcls.URL_RE.findall(u)
            domain = domcls.extract_domain(urls[0]) if urls else ""
            dl, basis = domcls.classify_domain(domain) if domain else ("ko", "no_url")
            bl, script, conf, other, lshare = body_language(it["t"])
            rows.append({"fandom": fd["fandom"], "bullet_type": tag, "idx": idx, "domain": domain, "domain_lang": dl, "domain_basis": basis, "body_script": script, "body_lang": bl,
                         "body_margin": conf, "other_lang_candidate": other, "latin_letter_share": round(lshare, 3), "agree": int(dl == bl)})
            dom_tot[dl] += 1; body_tot[bl] += 1; cross[dl][bl] += 1; per_f_body[fd["fandom"]][bl] += 1; per_f_dom[fd["fandom"]][dl] += 1
            if other: other_tot[other] += 1
with open(HERE / "bullet_language_body_vs_domain_v7.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# 실측(저장된 language_counts) 합계
real_tot = Counter()
for r in scores.values():
    for l, c in r["coverage_detail"]["language_counts"].items(): real_tot[l] += c
def entropy_norm(cnt, n=14):
    tot = sum(cnt.values()); return 0.0 if tot == 0 else -sum(c / tot * math.log(c / tot) for c in cnt.values() if c > 0) / math.log(n)
cov_key = next((k for k in scores[next(iter(scores))]["coverage_detail"] if "language" in k and "coverage" in k), None)
fnames = [fd["fandom"] for fd in corpus]
stored_cov = np.array([scores[f]["coverage_detail"][cov_key] for f in fnames]) if cov_key else None
body_cov = np.array([entropy_norm(per_f_body[f]) for f in fnames]); dom_cov = np.array([entropy_norm(per_f_dom[f]) for f in fnames])
per_lang = {}
for l in LANGS:
    n_dom = dom_tot[l]; agree = cross[l][l]; per_lang[l] = {"stored_language_counts": real_tot[l], "domain_reconstructed": n_dom, "body": body_tot[l],
                                                            "domain_bullets_whose_body_agrees": agree, "mismatch_rate_given_domain": round(1 - agree / n_dom, 4) if n_dom else None,
                                                            "body_lang_of_domain_bullets": dict(cross[l].most_common(4))}
n = len(rows); agree_all = sum(r["agree"] for r in rows)
ko_media_en_body = sum(1 for r in rows if r["domain_lang"] == "ko" and r["body_lang"] == "en"); en_domain_ko_body = sum(1 for r in rows if r["domain_lang"] == "en" and r["body_lang"] == "ko")
summary = {"n_bullets": n, "agreement_rate": round(agree_all / n, 4), "per_language": per_lang, "other_language_candidates": dict(other_tot.most_common()),
           "notable": {"domain_ko_but_body_en": ko_media_en_body, "domain_en_but_body_ko": en_domain_ko_body, "domain_default_basis": sum(1 for r in rows if r["domain_basis"] == "default")},
           "language_coverage_by_fandom": {"stored_key": cov_key, "r(stored, domain_reconstructed)": round(float(np.corrcoef(stored_cov, dom_cov)[0, 1]), 4) if cov_key else None,
                                           "r(stored, body)": round(float(np.corrcoef(stored_cov, body_cov)[0, 1]), 4) if cov_key else None, "r(domain_reconstructed, body)": round(float(np.corrcoef(dom_cov, body_cov)[0, 1]), 4),
                                           "mean_stored": round(float(stored_cov.mean()), 4) if cov_key else None, "mean_body": round(float(body_cov.mean()), 4), "mean_domain_reconstructed": round(float(dom_cov.mean()), 4)},
           "method": {"script": "한글/가나/한자/태국/키릴/아랍/라틴 글자 수 최대 문자권", "latin": "wordfreq zipf 평균, 후보 en es fr id vi tl pt tr; vi·tr 고유 자모 우선", "other": "다른 라틴계 19개 언어가 14개 최대값보다 zipf 0.5 이상 높고 토큰 5개 이상"}}
json.dump(summary, open(HERE / "body_language_summary_v7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

md = ["# 본문 언어 병행 판정 (L14) — 도메인 언어와 본문 언어는 얼마나 어긋나는가\n",
      "세계 언어 지수의 언어는 출처 도메인 기준이다. 이 문서는 불릿 10,020건마다 본문 문자권·wordfreq 빈도로 언어를 따로 판정해 도메인 기준과 나란히 놓는다. 전부 `build_body_language_classifier_v7.py`가 만든다(외부 감지기 없음, 결정적).\n",
      "## 0. 결론\n",
      f"- 도메인 언어(재구성 분류기)와 본문 언어가 같은 불릿은 {agree_all:,}/{n:,} ({summary['agreement_rate']:.1%}).",
      f"- 어긋남의 두 축: 한국 도메인인데 본문이 영어인 불릿 {ko_media_en_body:,}건(한국 매체 영문판·영문 인용), 영어 도메인인데 본문이 한국어인 불릿 {en_domain_ko_body:,}건(해외 매체 한국어판·한국어 요약). 도메인 규칙이 없어 기본값으로 떨어진 불릿은 {summary['notable']['domain_default_basis']:,}건.",
      f"- 14개 외 언어 후보: {sum(other_tot.values())}건 ({', '.join(f'{k} {v}' for k, v in other_tot.most_common(6)) or '없음'}). 검출 언어 수는 하한이라는 한계 2의 크기가 이 정도다.",
      f"- **본문은 대부분 한국어다.** 본문 기준 한국어 불릿 {body_tot['ko']:,}건({body_tot['ko']/n:.1%}); 일본·중국·태국 등 외국 도메인 불릿도 본문은 한국어 요약이 대부분이라(도메인 ja 불릿 중 본문 일치 {per_lang['ja']['domain_bullets_whose_body_agrees']}/{per_lang['ja']['domain_reconstructed']}) 본문 기준으로 바꾸면 세계 언어 지수 평균이 {summary['language_coverage_by_fandom']['mean_stored']}에서 {summary['language_coverage_by_fandom']['mean_body']}로 무너진다. "
      "즉 이 지수는 '본문 언어의 다양성'이 아니라 **'출처(도메인) 언어권의 다양성'** 이며, 수집 방식(근거를 한국어로 요약)상 본문 언어 판정은 지수를 대체할 수 없고 도메인 기준을 보완하는 보조 신호로만 쓸 수 있다. 문서·표의 지수명은 그렇게 읽어야 한다.",
      (f"- 팬덤별 세계 언어 지수(엔트로피)의 상관: 저장값 ↔ 도메인 재구성 r = {summary['language_coverage_by_fandom']['r(stored, domain_reconstructed)']}, 저장값 ↔ 본문 기준 r = {summary['language_coverage_by_fandom']['r(stored, body)']}. 본문 기준으로 바꾸면 순위가 얼마나 흔들리는지의 척도다." if cov_key else "- 저장 JSON에 팬덤별 언어 커버리지 키가 없어 지수 상관은 생략."),
      "\n## 1. 언어별 — 저장 실측 / 도메인 재구성 / 본문 기준\n", "| 언어 | 저장 language_counts | 도메인 재구성 | 본문 기준 | 도메인 불릿 중 본문 일치 | 불일치율 | 도메인 불릿의 본문 언어 분포 |\n|---|---|---|---|---|---|---|"]
for l in LANGS:
    v = per_lang[l]; md.append(f"| {l} | {v['stored_language_counts']:,} | {v['domain_reconstructed']:,} | {v['body']:,} | {v['domain_bullets_whose_body_agrees']:,} | {v['mismatch_rate_given_domain'] if v['mismatch_rate_given_domain'] is not None else '—'} | {v['body_lang_of_domain_bullets']} |")
md.append("\n'저장 language_counts'는 원본 language_of()의 결과이고 '도메인 재구성'은 저장소의 근사 분류기 결과다(둘의 차이는 tokenizer 폴더 문서). '본문 기준'은 이 스크립트의 판정이다.\n")
md.append("## 2. 판정 방법\n")
md.append("| 단계 | 규칙 |\n|---|---|\n| 문자권 | 한글·가나·한자·태국·키릴·아랍·라틴 글자 수의 최대. 가나가 있으면 한자도 일본어로 센다 |\n| 라틴 | wordfreq zipf 평균으로 en/es/fr/id/vi/tl/pt/tr 비교, 최대 선택. 베트남어·튀르키예어 고유 자모 2개 이상이면 우선 |\n| 14개 외 | 다른 라틴계 19개 언어 중 최대가 14개 최대보다 zipf 0.5 이상 높고 토큰 5개 이상이면 후보로 기록(`other_lang_candidate`) |\n| 무 URL | 도메인 언어 ko(원본 규칙과 같음), 본문 판정은 그대로 |\n")
md.append("## 3. 한계\n1. 본문 판정은 문장 하나(짧으면 10여 단어)에 대한 빈도 비교라 라틴계 언어 간(특히 id/tl/pt/es)에는 오판이 있다. `body_margin`이 작은 행이 그 자리다.\n2. 한국어 기사 안의 영문 고유명사(앨범명·차트명)는 라틴 글자 비중을 높이지만 한글이 더 많으면 ko로 판정된다. 영문이 절반을 넘는 혼합 문장은 라틴으로 넘어간다(`latin_letter_share`).\n3. 지수 자체를 본문 기준으로 바꾸지는 않았다. 저장 JSON·README 표는 도메인 기준 그대로이고, 이 문서는 그 기준의 오차 크기를 보이는 병행 자료다.\n")
md.append("## 4. 파일\n| 파일 | 내용 |\n|---|---|\n| `bullet_language_body_vs_domain_v7.csv` | 10,020행: 도메인·도메인 언어·판정 근거·본문 문자권·본문 언어·여유·14개 외 후보·라틴 비중·일치 |\n| `body_language_summary_v7.json` | 언어별 집계·교차·팬덤별 지수 상관 |\n| `build_body_language_classifier_v7.py` | 이 문서를 만드는 스크립트 |\n")
(HERE / "BODY_LANGUAGE_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"agree {agree_all}/{n} = {summary['agreement_rate']:.3f}; ko-domain/en-body {ko_media_en_body}, en-domain/ko-body {en_domain_ko_body}; other {dict(other_tot.most_common(6))}")
print("coverage r:", summary["language_coverage_by_fandom"])
for l in LANGS: print(f"  {l}: stored {real_tot[l]} dom {dom_tot[l]} body {body_tot[l]} mismatch {per_lang[l]['mismatch_rate_given_domain']}")
