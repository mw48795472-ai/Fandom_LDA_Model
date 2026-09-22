# 다국어 불릿 단위 언어 분류 재구성 — 최종 코퍼스 10,020건 · 14개 언어 판
#
# archive/v6_r22_era/TOKENIZER/build_multilingual_bullet_language_classifier.py(r22, 10개 언어)의
# 10,020건 판이다. 원본 language_of()(도메인 허용목록 기반)는 최종 토크나이저 소스
# run_lda_v6_live_reference_v7.py 안에 있고 그 파일은 저장소에 없다. 대신 그 함수의 **결과물**은
# 두 곳에 남아 있다:
#   - data/v7_final/fandom_scores_live_reference_v7.json  coverage_detail.language_counts (팬덤별, 14개 언어)
#   - data/v7_final/language_domain_summary_v7.json         언어별 근거 건수·도메인 수(코퍼스 합계)
#
# 이 스크립트가 하는 것:
#   1) 팬덤별 language_counts를 합산해 language_domain_summary_v7.json의 언어별 total_bullets와
#      14개 언어 전부 정확히 일치하는지 확인한다(합 10,020).
#   2) 도메인 → 언어 근사 분류기(재구성, 원본 아님)를 코퍼스 원문 URL에 직접 적용해 (1)과 비교한다.
#      r22 판의 TLD 규칙·수동 매핑에 필리핀어(tl)·포르투갈어(pt)·튀르키예어(tr)·아랍어(ar) 규칙을 더했다.
#   3) 언어 버킷별 상위 기여 도메인과, '기본값(en)'으로 떨어진 도메인 상위 목록을 출력해 분류기의
#      커버리지 한계를 투명하게 보인다.
#
# 정직한 한계: 도메인 이름만으로 언어를 추정하는 방식은 본문 언어와 어긋날 수 있어 근본적으로 근사치다.
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]          # 저장소 루트 (v7_final_10020/analysis/tokenizer/ 는 3단 깊이)
DATA = BASE / "data" / "v7_final"
CORPUS_PATH = DATA / "fandoms_v3_100.json"
SCORES_PATH = DATA / "fandom_scores_live_reference_v7.json"
SUMMARY_PATH = DATA / "language_domain_summary_v7.json"

URL_RE = re.compile(r"https?://[^\s;]+")
LANGS = ["ko", "en", "ja", "zh", "es", "fr", "th", "id", "vi", "ru", "tl", "pt", "tr", "ar"]

TLD_SUFFIX_RULES = [
    (".co.kr", "ko"), (".or.kr", "ko"), (".go.kr", "ko"), (".kr", "ko"),
    (".co.jp", "ja"), (".jp", "ja"),
    (".com.cn", "zh"), (".cn", "zh"), (".hk", "zh"), (".tw", "zh"), (".mg", "zh"),
    (".com.vn", "vi"), (".vn", "vi"),
    (".com.mx", "es"), (".mx", "es"), (".ar", "es"), (".pe", "es"), (".es", "es"), (".cl", "es"), (".co", "es"),
    (".co.th", "th"), (".th", "th"),
    (".ru", "ru"),
    (".fr", "fr"),
    (".id", "id"),
    (".com.ph", "tl"), (".ph", "tl"),
    (".com.br", "pt"), (".br", "pt"), (".pt", "pt"),
    (".com.tr", "tr"), (".tr", "tr"),
    (".ae", "ar"), (".sa", "ar"), (".eg", "ar"), (".qa", "ar"), (".kw", "ar"), (".ma", "ar"),
]

DOMAIN_OVERRIDES = {
    # 일본어
    "natalie.mu": "ja", "billboard-japan.com": "ja", "barks.jp": "ja",
    # 중국어
    "weibo.com": "zh", "163.com": "zh", "music.163.com": "zh", "qq.com": "zh", "news.qq.com": "zh", "y.qq.com": "zh",
    "baike.baidu.com": "zh", "douban.com": "zh", "music.douban.com": "zh", "udn.com": "zh", "stars.udn.com": "zh",
    "hk01.com": "zh", "sina.com.cn": "zh", "finance.sina.com.cn": "zh", "ettoday.net": "zh", "star.ettoday.net": "zh",
    "nownews.com": "zh", "ltn.com.tw": "zh", "chinatimes.com": "zh", "storm.mg": "zh",
    # 태국어
    "sanook.com": "th", "kapook.com": "th", "musicstation.kapook.com": "th", "workpointtoday.com": "th", "mgronline.com": "th",
    "thairath.co.th": "th", "khaosod.co.th": "th", "matichon.co.th": "th",
    # 인도네시아어
    "detik.com": "id", "hot.detik.com": "id", "20.detik.com": "id", "wolipop.detik.com": "id", "tribunnews.com": "id",
    "manado.tribunnews.com": "id", "idntimes.com": "id", "kompas.com": "id", "liputan6.com": "id", "antaranews.com": "id",
    "cnnindonesia.com": "id", "kapanlagi.com": "id",
    # 베트남어
    "vnexpress.net": "vi", "vietnam.vn": "vi", "kenh14.vn": "vi", "tuoitre.vn": "vi", "thanhnien.vn": "vi",
    # 러시아어
    "yesasia.ru": "ru", "ria.ru": "ru", "mk.ru": "ru",
    # 스페인어
    "infobae.com": "es", "univision.com": "es", "larepublica.pe": "es", "culturaasiatica.com": "es", "kpoplat.com": "es",
    "cusica.com": "es", "plus.cusica.com": "es", "sopitas.com": "es", "elpais.com": "es", "eluniversal.com.mx": "es",
    "excelsior.com.mx": "es", "heraldodemexico.com.mx": "es", "milenio.com": "es", "clarin.com": "es", "lanacion.com.ar": "es",
    # 프랑스어
    "koreasowls.fr": "fr", "k-world.fr": "fr", "lemonde.fr": "fr", "lefigaro.fr": "fr", "leparisien.fr": "fr", "20minutes.fr": "fr",
    # 필리핀어(원본 스키마의 tl — 필리핀 매체는 영어 기사가 많아 원본 language_of()가 이를 tl로 묶었는지는 확인 불가)
    "pep.ph": "tl", "mb.com.ph": "tl", "abs-cbn.com": "tl", "gmanetwork.com": "tl", "inquirer.net": "tl", "philstar.com": "tl",
    "rappler.com": "tl", "manilatimes.net": "tl", "news.abs-cbn.com": "tl",
    # 포르투갈어
    "globo.com": "pt", "g1.globo.com": "pt", "uol.com.br": "pt", "folha.uol.com.br": "pt", "terra.com.br": "pt", "estadao.com.br": "pt",
    "cnnbrasil.com.br": "pt", "correiobraziliense.com.br": "pt",
    # 튀르키예어
    "hurriyet.com.tr": "tr", "sabah.com.tr": "tr", "milliyet.com.tr": "tr", "haberturk.com": "tr", "sozcu.com.tr": "tr", "ntv.com.tr": "tr",
    "bigpara.hurriyet.com.tr": "tr", "cnnturk.com": "tr",
    # 아랍어
    "aljazeera.net": "ar", "alarabiya.net": "ar", "ahram.org.eg": "ar", "youm7.com": "ar", "albayan.ae": "ar", "emaratalyoum.com": "ar",
    "okaz.com.sa": "ar", "alkhaleej.ae": "ar", "elwatannews.com": "ar", "alraimedia.com": "ar",
    # 한국어(.com/.press 등 일반 TLD를 쓰는 국내 매체)
    "daum.net": "ko", "v.daum.net": "ko", "cafe.daum.net": "ko", "m.cafe.daum.net": "ko", "newsis.com": "ko", "hankyung.com": "ko",
    "plus.hankyung.com": "ko", "fnnews.com": "ko", "hankookilbo.com": "ko", "munhwa.com": "ko", "sportsseoul.com": "ko",
    "sedaily.com": "ko", "en.sedaily.com": "ko", "m.sedaily.com": "ko", "ajunews.com": "ko", "ohmynews.com": "ko", "imaeil.com": "ko",
    "hjfocus.com": "ko", "luck-d.com": "ko", "andongdaily.com": "ko", "kedglobal.com": "ko", "sportsworldi.com": "ko",
    "koreadaily.com": "ko", "hanteonews.com": "ko", "bizhankook.com": "ko", "digitalchosun.dizzo.com": "ko", "cine21.com": "ko",
    "yg-life.com": "ko", "tvreport.co.kr": "ko", "isplus.com": "ko", "kbizoom.com": "ko", "nc.press": "ko", "twig24.com": "ko",
    "m-i.kr": "ko", "m.heraldmuse.com": "ko", "mhns.co.kr": "ko", "smentertainment.com": "ko", "namu.wiki": "ko",
    "news.nate.com": "ko", "mt.co.kr": "ko", "sports.khan.co.kr": "ko", "topstarnews.net": "ko", "mydaily.co.kr": "ko",
    "osen.mt.co.kr": "ko", "tenasia.hankyung.com": "ko", "news1.kr": "ko", "edaily.co.kr": "ko", "heraldcorp.com": "ko",
    "biz.heraldcorp.com": "ko", "xportsnews.com": "ko", "sportsdonga.com": "ko", "sports.donga.com": "ko", "chosun.com": "ko",
    "joongang.co.kr": "ko", "news.kbs.co.kr": "ko", "imnews.imbc.com": "ko", "news.sbs.co.kr": "ko", "ytn.co.kr": "ko",
    "yna.co.kr": "ko", "newsen.com": "ko", "kmib.co.kr": "ko", "segye.com": "ko", "hani.co.kr": "ko", "dt.co.kr": "ko",
    # 영어
    "koreaherald.com": "en", "koreatimes.co.kr": "en", "koreatimes.com": "en", "scmp.com": "en", "starnewskorea.com": "en",
    "allkpop.com": "en", "soompi.com": "en", "koreaboo.com": "en", "billboard.com": "en", "forbes.com": "en", "youtube.com": "en",
    "malaymail.com": "en", "thestar.com.my": "en", "bandwagon.asia": "en", "nme.com": "en", "hypebeast.com": "en", "hypebeast.kr": "en",
    "wwd.com": "en", "nbcnews.com": "en", "msn.com": "en", "pressreader.com": "en", "timeout.com": "en", "grokipedia.com": "en",
    "sportskeeda.com": "en", "instagram.com": "en", "facebook.com": "en", "threads.com": "en", "x.com": "en", "web.archive.org": "en",
    "en.yna.co.kr": "en", "koreajoongangdaily.joins.com": "en", "en.seoul.co.kr": "en", "english.hani.co.kr": "en",
}

WIKI_LANG_PREFIX = re.compile(r"^([a-z]{2})\.(wikipedia\.org|namu\.wiki)$")
_AGENT_ID_LEAK_RE = re.compile(r"\)agentId:.*$")


def classify_domain(domain: str):
    """(언어코드, 판정근거) 반환. 판정근거: 'wiki'|'override'|'tld'|'default'"""
    m = WIKI_LANG_PREFIX.match(domain)
    if m:
        lang = m.group(1)
        return (lang if lang in LANGS else "en"), "wiki"
    bare = domain[4:] if domain.startswith("www.") else domain
    if domain in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[domain], "override"
    if bare in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[bare], "override"
    # 서브도메인을 한 단계씩 벗겨 가며 수동 매핑 재시도 (예: star.ettoday.net -> ettoday.net)
    parts = bare.split(".")
    for i in range(1, len(parts) - 1):
        cand = ".".join(parts[i:])
        if cand in DOMAIN_OVERRIDES:
            return DOMAIN_OVERRIDES[cand], "override"
    for suffix, lang in TLD_SUFFIX_RULES:
        if domain.endswith(suffix):
            return lang, "tld"
    return "en", "default"


RE_HANGUL, RE_KANA, RE_HANZI, RE_THAI = (re.compile(r"[가-힣]"), re.compile(r"[぀-ゟ゠-ヿ]"), re.compile(r"[一-鿿]"), re.compile(r"[฀-๿]"))


def text_script_fallback(text: str) -> str:
    """원본 language_of()에는 없는 보조 규칙(일본어 가나 텍스트 보강만 원본에 있었다). 도메인 규칙이 전혀 없는 출처에 한해
    본문 문자권으로 언어를 추정한다 — 원본 재현이 아니라 '도메인 목록이 704개까지 있었던 원본'과의 격차를 줄이는 근사."""
    if RE_HANGUL.search(text):
        return "ko"
    if RE_KANA.search(text):
        return "ja"
    if RE_HANZI.search(text):
        return "zh"
    if RE_THAI.search(text):
        return "th"
    return "en"


def extract_domain(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1) if m else url


def sanitize_bullet_url_field(raw: str):
    cleaned = _AGENT_ID_LEAK_RE.sub("", raw)
    return cleaned, (cleaned != raw)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    scores = load_json(SCORES_PATH)
    summary = {r["lang_code"]: r for r in load_json(SUMMARY_PATH)}
    real_totals = Counter()
    for fd in scores:
        for lang, cnt in fd["coverage_detail"]["language_counts"].items():
            real_totals[lang] += cnt

    print("[검증] fandom_scores_live_reference_v7.json language_counts 합산 vs. language_domain_summary_v7.json total_bullets")
    for lang in LANGS:
        real_v, doc_v = real_totals[lang], summary[lang]["total_bullets"]
        print(f"  {lang}: 팬덤별 합계={real_v:5d}  summary={doc_v:5d}  도메인 수={summary[lang]['total_domains']:4d}  {'[일치]' if real_v == doc_v else '[불일치]'}")
        assert real_v == doc_v, f"{lang} 불일치"
    print(f"  14개 언어 합계: {sum(real_totals.values())}건 (코퍼스 10,020건과 일치해야 함)")
    assert sum(real_totals.values()) == 10020
    print("  -> PASS: 두 파일이 같은 language_of() 실행 결과를 담고 있다")

    fandoms = load_json(CORPUS_PATH)
    reconstructed_totals = Counter()
    stage2_totals = Counter()          # 2단계: 규칙이 없는 도메인(default)만 불릿 본문 문자권으로 보정한 근사
    domain_by_lang = defaultdict(Counter)
    default_domains = Counter()
    basis_counts = Counter()
    no_url_reference_notes = 0
    agent_id_leak_hits = []
    n_bullets = 0
    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for bullet in fd.get(tag, []):
                n_bullets += 1
                raw_u = bullet.get("u", "") or ""
                cleaned_u, leaked = sanitize_bullet_url_field(raw_u)
                if leaked:
                    agent_id_leak_hits.append((fd.get("fandom"), tag, raw_u))
                urls = URL_RE.findall(cleaned_u)
                if not urls:
                    no_url_reference_notes += 1
                    continue
                domain = extract_domain(urls[0])
                lang, basis = classify_domain(domain)
                reconstructed_totals[lang] += 1
                domain_by_lang[lang][domain] += 1
                basis_counts[basis] += 1
                if basis == "default":
                    default_domains[domain] += 1
                    lang = text_script_fallback(bullet.get("t", "") or "")
                stage2_totals[lang] += 1

    print(f"\n[코퍼스] 불릿 {n_bullets}건")
    print(f"[데이터 무결성] 'u' 필드에 세션 Agent 도구의 핸드백 문구가 남아있는 사례: {len(agent_id_leak_hits)}건 (r22 판에서는 5건)")
    for fandom, tag, raw in agent_id_leak_hits[:5]:
        print(f"  - {fandom}/{tag}: {raw[:70]}...")
    print(f"  -> URL이 없는 참고문구 불릿(예: '위와 동일'): {no_url_reference_notes}건 (분류 대상에서 제외)")

    print(f"\n[재구성] 도메인 기반 분류기 적용 결과 (불릿 {sum(reconstructed_totals.values())}건)")
    print(f"  판정근거 분포: {dict(basis_counts)}")

    print("\n[비교] 언어별: 실측(language_counts 합계) vs. 재구성(도메인 분류기)")
    print(f"  {'언어':4s} {'실측':>8s} {'재구성':>8s} {'차이':>8s}")
    overall_diff = 0
    for lang in LANGS:
        real_v, recon_v = real_totals.get(lang, 0), reconstructed_totals.get(lang, 0)
        overall_diff += abs(recon_v - real_v)
        print(f"  {lang:4s} {real_v:8d} {recon_v:8d} {recon_v - real_v:+8d}")
    accuracy = 1 - overall_diff / (2 * sum(real_totals.values()))
    print(f"  언어별 절대오차 합={overall_diff}, 대략적 일치도(1-오차/2N)={accuracy:.1%}")

    print("\n[비교 2단계] default 도메인만 본문 문자권으로 보정(원본에 없는 보조 규칙, 근사 목적)")
    print(f"  {'언어':4s} {'실측':>8s} {'2단계':>8s} {'차이':>8s}")
    diff2 = 0
    for lang in LANGS:
        real_v, s2 = real_totals.get(lang, 0), stage2_totals.get(lang, 0)
        diff2 += abs(s2 - real_v)
        print(f"  {lang:4s} {real_v:8d} {s2:8d} {s2 - real_v:+8d}")
    print(f"  언어별 절대오차 합={diff2}, 대략적 일치도={1 - diff2 / (2 * sum(real_totals.values())):.1%}")

    print("\n[도메인별 집계] 언어 버킷별 상위 기여 도메인 (재구성 분류 기준)")
    for lang in LANGS:
        top = domain_by_lang[lang].most_common(5)
        if top:
            print(f"  {lang}: {', '.join(f'{d}({c})' for d, c in top)}")
    print("\n[커버리지 한계] 규칙이 없어 기본값(en)으로 떨어진 도메인 상위 15")
    for d, c in default_domains.most_common(15):
        print(f"  {d}({c})")
    return real_totals, reconstructed_totals


if __name__ == "__main__":
    main()
