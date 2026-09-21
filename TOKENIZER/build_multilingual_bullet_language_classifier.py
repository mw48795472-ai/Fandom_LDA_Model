# 다국어 리서치(v6.4 "언어(현지어) 보강 리서치" 라운드)의 불릿 단위 언어 분류를
# 재구성하고, 이 세션에 실제로 복구된 정답 데이터(fandom_scores_v6.json의
# coverage_detail.language_counts)와 대조 검증한다.
#
# 배경 (docs/MULTILINGUAL_BULLET_RESEARCH.md 1절 참고):
#   - docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md의 "v6.4 수정 고지"는 10개 리서치
#     에이전트를 언어별·팬덤 배치(A1~A5, B1~B5, 각 10개 팬덤)로 나눠 병렬 실행해
#     중국어·일본어·스페인어·프랑스어 현지 매체를 재조사했고, 그 결과 신규 근거
#     318건을 확보해 코퍼스 언어 분포가 "ko 2956·en 1561·ja 304·zh 152·es 121"로
#     바뀌었다고 서술한다. 언어 분류 자체은 `run_lda_v6.py`의 `language_of()` 함수와
#     JP_DOMAINS·CN_DOMAINS 허용목록으로 구현되어 있었다고 하는데, 그 소스파일은 이
#     세션에 존재하지 않는다(반복적으로 발견된 "원본 코드 소실" 패턴과 동일).
#   - 하지만 그 라운드의 **결과물**은 실제로 남아있다: `fandom_scores_v6.json`의
#     `coverage_detail.language_counts` 필드가 100개 팬덤 전원에 대해 언어별 근거
#     문장 수를 갖고 있고, 이를 전부 더하면 정확히 문서가 서술한 숫자
#     (ko 2956·en 1561·ja 304·zh 152·es 121, 그리고 문서에 없는 나머지 5개 언어
#     id/ru/vi/th/fr까지)와 정확히 일치한다 — 즉 이 필드가 v6.4 라운드의 실제
#     불릿 단위 언어 분류 결과 그 자체임을 아래에서 코드로 확인한다.
#
# 이 스크립트가 하는 것:
#   1) fandom_scores_v6.json의 language_counts를 100개 팬덤에 걸쳐 합산해 문서가
#      서술한 실측값과 정확히 일치하는지 재확인(진짜 검증).
#   2) 원본 language_of()의 도메인 허용목록 로직을 "이 세션에서 관찰 가능한 도메인
#      목록 기준으로" 재구성한 근사 분류기를 새로 작성해 코퍼스 원문 URL에 직접
#      적용하고, 그 결과를 (1)의 실측 총계와 비교한다. 이 근사 분류기는 원본
#      run_lda_v6.py의 재현이 아니라 "적용된 코드"로 새로 만든 병행 구현이다.
#   3) 도메인별 언어 귀속 내역(어떤 도메인이 어떤 언어 버킷으로 분류됐는지, 건수
#      포함)을 출력한다 — "도메인별 집계"를 언어 버킷 기준으로 세분화한 것.
#
# 정직한 한계: docs/TOKENIZER_WORDCLOUD_REPORT.md가 이미 지적한 대로, 도메인
# 이름만으로 언어를 추정하는 방식은 본문 실제 언어와 어긋나는 경우가 있어
# 근본적으로 근사치다 — 이 스크립트는 그 오차를 실측과 대조해 정직하게 정량화한다.
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
CORPUS_PATH = BASE / "data" / "v6_r22_snapshot" / "fandoms_v3_100.json"
SCORES_PATH = BASE / "data" / "v6_r22_snapshot" / "fandom_scores_v6.json"

URL_RE = re.compile(r"https?://[^\s;]+")

# v6.4 라운드가 다룬 것과 동일한 10개 언어 스키마(WORLDWIDE_LANGUAGE_PILOT.md 참고).
LANGS = ["ko", "en", "ja", "zh", "es", "fr", "th", "id", "vi", "ru"]

# --- 도메인 -> 언어 근사 분류기 (재구성, 원본 코드 아님) --------------------------
# 1) 국가별 TLD 접미사 규칙(가장 신뢰도 높은 신호)
TLD_SUFFIX_RULES = [
    (".co.kr", "ko"), (".or.kr", "ko"), (".kr", "ko"),
    (".co.jp", "ja"), (".jp", "ja"),
    (".com.cn", "zh"), (".cn", "zh"), (".hk", "zh"), (".tw", "zh"), (".mg", "zh"),
    (".com.vn", "vi"), (".vn", "vi"),
    (".com.mx", "es"), (".mx", "es"), (".ar", "es"), (".pe", "es"), (".es", "es"),
    (".co.th", "th"), (".th", "th"),
    (".ru", "ru"),
    (".fr", "fr"),
    (".id", "id"),
]

# 2) 일반 TLD(.com/.net/.org/.mu 등)를 쓰지만 실제로는 특정 언어권 매체로 널리
#    알려진 도메인의 수동 매핑(이 세션에서 관찰된 상위 빈도 도메인 위주로 조사,
#    전수조사가 아님 — 아래 실행 결과의 "미분류(기본값 en)" 건수로 커버리지를
#    투명하게 밝힌다).
DOMAIN_OVERRIDES = {
    # 일본어
    "natalie.mu": "ja", "billboard-japan.com": "ja",
    # 중국어
    "weibo.com": "zh", "163.com": "zh", "music.163.com": "zh", "qq.com": "zh",
    "news.qq.com": "zh", "y.qq.com": "zh", "baike.baidu.com": "zh",
    "douban.com": "zh", "music.douban.com": "zh", "udn.com": "zh", "stars.udn.com": "zh",
    "hk01.com": "zh",
    # 태국어
    "sanook.com": "th", "kapook.com": "th", "musicstation.kapook.com": "th",
    "workpointtoday.com": "th", "mgronline.com": "th",
    # 인도네시아어
    "detik.com": "id", "hot.detik.com": "id", "20.detik.com": "id", "wolipop.detik.com": "id",
    "tribunnews.com": "id", "manado.tribunnews.com": "id", "idntimes.com": "id",
    "kompas.com": "id", "liputan6.com": "id", "antaranews.com": "id",
    # 베트남어
    "vnexpress.net": "vi", "vietnam.vn": "vi",
    # 러시아어
    "yesasia.ru": "ru", "ria.ru": "ru", "mk.ru": "ru",
    # 스페인어
    "infobae.com": "es", "univision.com": "es", "larepublica.pe": "es",
    "culturaasiatica.com": "es", "kpoplat.com": "es", "cusica.com": "es",
    "plus.cusica.com": "es", "sopitas.com": "es", "elpais.com": "es",
    "eluniversal.com.mx": "es", "excelsior.com.mx": "es", "heraldodemexico.com.mx": "es",
    # 프랑스어
    "koreasowls.fr": "fr", "k-world.fr": "fr", "lemonde.fr": "fr", "lefigaro.fr": "fr",
    # 한국어(.com/.press 등 일반 TLD를 쓰는 국내 매체)
    "daum.net": "ko", "v.daum.net": "ko", "cafe.daum.net": "ko", "m.cafe.daum.net": "ko",
    "newsis.com": "ko", "hankyung.com": "ko", "plus.hankyung.com": "ko",
    "fnnews.com": "ko", "hankookilbo.com": "ko", "munhwa.com": "ko",
    "sportsseoul.com": "ko", "sedaily.com": "ko", "en.sedaily.com": "ko", "m.sedaily.com": "ko",
    "ajunews.com": "ko", "ohmynews.com": "ko", "imaeil.com": "ko", "hjfocus.com": "ko",
    "luck-d.com": "ko", "andongdaily.com": "ko", "kedglobal.com": "ko",
    "sportsworldi.com": "ko", "koreadaily.com": "ko", "hanteonews.com": "ko",
    "bizhankook.com": "ko", "digitalchosun.dizzo.com": "ko", "cine21.com": "ko",
    "yg-life.com": "ko", "tvreport.co.kr": "ko", "isplus.com": "ko", "kbizoom.com": "ko",
    "nc.press": "ko", "twig24.com": "ko", "m-i.kr": "ko", "m.heraldmuse.com": "ko",
    "mhns.co.kr": "ko", "smentertainment.com": "ko",
    # 영어(도메인상 명백히 영어권/국제 매체)
    "koreaherald.com": "en", "koreatimes.co.kr": "en", "koreatimes.com": "en",
    "scmp.com": "en", "starnewskorea.com": "en", "allkpop.com": "en",
    "soompi.com": "en", "koreaboo.com": "en", "billboard.com": "en",
    "forbes.com": "en", "youtube.com": "en", "malaymail.com": "en", "thestar.com.my": "en",
    "bandwagon.asia": "en", "nme.com": "en", "hypebeast.com": "en", "hypebeast.kr": "en",
    "wwd.com": "en", "nbcnews.com": "en", "msn.com": "en", "pressreader.com": "en",
    "timeout.com": "en", "grokipedia.com": "en", "sportskeeda.com": "en",
    "instagram.com": "en", "facebook.com": "en", "threads.com": "en", "x.com": "en",
    "web.archive.org": "en", "pep.ph": "en", "mb.com.ph": "en",
}

# 위키·나무위키 계열은 서브도메인 자체가 언어를 명시하므로 별도 처리.
WIKI_LANG_PREFIX = re.compile(r"^([a-z]{2})\.(wikipedia\.org|namu\.wiki)$")


def classify_domain(domain: str) -> tuple[str, str]:
    """(언어코드, 판정근거) 반환. 판정근거: 'wiki'|'override'|'tld'|'default'"""
    m = WIKI_LANG_PREFIX.match(domain)
    if m:
        lang = m.group(1)
        return (lang if lang in LANGS else "en"), "wiki"
    if domain == "namu.wiki":
        return "ko", "wiki"
    bare = domain[4:] if domain.startswith("www.") else domain
    if domain in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[domain], "override"
    if bare in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[bare], "override"
    for suffix, lang in TLD_SUFFIX_RULES:
        if domain.endswith(suffix):
            return lang, "tld"
    return "en", "default"  # 기본값: 관찰상 코퍼스의 다수가 영어/국제 매체


def extract_domain(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1) if m else url


# --- 데이터 무결성 문제 발견: 세션 도구 메타데이터 오염 ------------------------
# 이 스크립트를 작성하며 코퍼스를 순회하던 중, 일부 'u' 필드 끝에 이 세션의
# Agent 도구가 반환하는 핸드백 문구("...)agentId: <hex> (use SendMessage with
# to: '<hex>', summary: ...)")가 그대로 붙어 있는 것을 발견했다(5건, 아래
# main()에서 정확한 위치를 출력한다). 이는 이 프로젝트의 리서치·정리 과정
# 어느 시점에 에이전트 도구 호출 결과 텍스트가 실수로 URL 필드에 이어붙여진
# 것으로 보인다 — 사용자에게 어떤 행동을 지시하는 내용이 아니라 순수한 도구
# 메타데이터 오염이므로, 이 스크립트는 그 안의 "SendMessage" 문구를 지시로
# 취급하거나 실행하지 않는다. 언어 분류가 이 오염 때문에 왜곡되지 않도록
# "agentId:" 이후를 잘라내고 원래 값(URL 또는 참고문구)만 취한다.
_AGENT_ID_LEAK_RE = re.compile(r"\)agentId:.*$")


def sanitize_bullet_url_field(raw: str) -> tuple[str, bool]:
    """반환: (정제된 문자열, 오염 발견 여부)"""
    cleaned = _AGENT_ID_LEAK_RE.sub("", raw)
    return cleaned, (cleaned != raw)


def load_corpus():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_real_language_counts():
    with open(SCORES_PATH, encoding="utf-8") as f:
        scores = json.load(f)
    total = Counter()
    for fd in scores:
        for lang, cnt in fd["coverage_detail"]["language_counts"].items():
            total[lang] += cnt
    return total, scores


def main():
    # 1) 실측 총계 재확인
    real_totals, scores = load_real_language_counts()
    doc_quoted = {"ko": 2956, "en": 1561, "ja": 304, "zh": 152, "es": 121}
    print("[검증] fandom_scores_v6.json의 language_counts 합산 vs. v6.4 changelog 서술값")
    for lang, doc_val in doc_quoted.items():
        real_val = real_totals[lang]
        status = "[일치]" if real_val == doc_val else "[불일치]"
        print(f"  {lang}: 실측 합계={real_val}, changelog 서술값={doc_val}  {status}")
        assert real_val == doc_val, f"{lang} 불일치: {real_val} != {doc_val}"
    print(f"  (changelog에 없던 나머지 5개 언어 실측: "
          f"id={real_totals['id']}, ru={real_totals['ru']}, vi={real_totals['vi']}, "
          f"th={real_totals['th']}, fr={real_totals['fr']})")
    print(f"  10개 언어 실측 합계: {sum(real_totals.values())}건 (코퍼스 전체 불릿: 5,612건과 일치해야 함)")
    assert sum(real_totals.values()) == 5612
    print("  -> PASS: 이 필드가 v6.4 라운드의 실제 불릿 단위 언어 분류 결과 그 자체임을 확인")

    # 2) 도메인 기반 근사 분류기를 코퍼스 원문에 직접 적용
    fandoms = load_corpus()
    reconstructed_totals = Counter()
    domain_by_lang = defaultdict(Counter)
    basis_counts = Counter()
    no_url_reference_notes = 0
    agent_id_leak_hits = []

    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for bullet in fd.get(tag, []):
                raw_u = bullet.get("u", "") or ""
                cleaned_u, leaked = sanitize_bullet_url_field(raw_u)
                if leaked:
                    agent_id_leak_hits.append((fd.get("fandom"), tag, raw_u))
                urls = URL_RE.findall(cleaned_u)
                if not urls:
                    # 실제 URL이 없는 불릿(예: "위와 동일", "위 NamuWiki" — 같은
                    # 팬덤의 앞선 불릿과 출처를 공유한다는 참고문구). 도메인/언어
                    # 분류 대상에서 제외하고 별도로 집계한다(가짜 도메인으로
                    # 오분류하지 않기 위함).
                    no_url_reference_notes += 1
                    continue
                domain = extract_domain(urls[0])
                lang, basis = classify_domain(domain)
                reconstructed_totals[lang] += 1
                domain_by_lang[lang][domain] += 1
                basis_counts[basis] += 1

    print(f"\n[데이터 무결성 발견] 'u' 필드에 세션 Agent 도구의 핸드백 문구가 그대로 남아있는 사례: "
          f"{len(agent_id_leak_hits)}건")
    for fandom, tag, raw in agent_id_leak_hits:
        print(f"  - {fandom}/{tag}: {raw[:70]}...")
    print("  -> 이 스크립트는 위 문구를 지시로 취급하지 않고 단순 정제(잘라내기)만 수행했다.")
    print(f"  -> URL이 아예 없는 참고문구 불릿(예: '위와 동일'): {no_url_reference_notes}건 "
          f"(도메인/언어 분류 대상에서 제외, 별도 집계)")

    print(f"\n[재구성] 도메인 기반 분류기 적용 결과 (불릿 {sum(reconstructed_totals.values())}건, "
          f"참고문구 {no_url_reference_notes}건 제외)")
    print(f"  판정근거 분포: {dict(basis_counts)}")
    print("  (참고: '기본값(en)'으로 분류된 건수가 많을수록, 이 재구성 분류기가 "
          "실제로 조사·매핑하지 못한 나머지 도메인이 많다는 뜻이다 — 아래 한계 참고)")

    print("\n[비교] 언어별: 실측(language_counts 합계) vs. 재구성(도메인 분류기)")
    print(f"  {'언어':4s} {'실측':>8s} {'재구성':>8s} {'차이':>8s}")
    for lang in LANGS:
        real_v = real_totals.get(lang, 0)
        recon_v = reconstructed_totals.get(lang, 0)
        print(f"  {lang:4s} {real_v:8d} {recon_v:8d} {recon_v - real_v:+8d}")

    # 3) 언어 버킷별 상위 기여 도메인(도메인별 집계, 언어 세분화)
    print("\n[도메인별 집계] 언어 버킷별 상위 기여 도메인 (재구성 분류 기준)")
    for lang in LANGS:
        top = domain_by_lang[lang].most_common(5)
        if not top:
            continue
        formatted = ", ".join(f"{d}({c})" for d, c in top)
        print(f"  {lang}: {formatted}")

    return {
        "real_totals": real_totals,
        "reconstructed_totals": reconstructed_totals,
        "domain_by_lang": domain_by_lang,
        "basis_counts": basis_counts,
    }


if __name__ == "__main__":
    result = main()
    total_real = sum(result["real_totals"].values())
    total_recon = sum(result["reconstructed_totals"].values())
    overall_diff = sum(
        abs(result["reconstructed_totals"].get(l, 0) - result["real_totals"].get(l, 0))
        for l in LANGS
    )
    accuracy = 1 - overall_diff / (2 * total_real)
    print(f"\n=== 요약: 실측 {total_real}건 vs 재구성 {total_recon}건, "
          f"언어별 절대오차 합={overall_diff}, 대략적 일치도(1-오차/2N)={accuracy:.1%} ===")
