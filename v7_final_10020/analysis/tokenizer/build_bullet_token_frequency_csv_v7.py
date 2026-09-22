# 입력 data/v7_final/fandoms_v3_100.json(10,020건), 출력 csv/bullet_token_frequency_v7_final.csv,
# 원본 토크나이저 실행 결과(wordcloud_by_language_v7.json)의 버킷별 상위 단어와 대조.
# 코퍼스 불릿(근거문장) 전체를 토큰화해 "토큰별 등장횟수·비중" CSV를 산출한다.
#
# 배경(정직한 위치 표시): `v7_final_10020/tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md`는 원본 토크나이저
# `tokenize(text, url)`가 (1) "일반 경로"(정규식, 공백 구분 언어 전부: 한국어·영어·
# 스페인어·프랑스어·포르투갈어·인도네시아어·베트남어·튀르키예어·러시아어)를 항상
# 먼저 실행하고, (2) 불릿 본문에 가나·한자·태국 문자가 실제로 등장하면 그 위에
# 일본어(fugashi)·중국어(jieba)·태국어(pythainlp) 형태소 분석 결과를 추가로
# 얹는다고 설명한다. 그러나 원본 코드(`run_lda_v6.py`)와 정확한 불용어 목록
# (STOPWORDS 41종·ENGLISH_STOPWORDS 64종·CHINESE_STOPWORDS 60여종·
# JAPANESE_STOPWORDS 28종 등)은 저장소에 포함되어 있지 않다(같은 폴더
# `tokenizer_script_routing_v7.ipynb`의 한계 항목 참고).
#
# 이 스크립트는 그 한계를 메우는 것이 아니라, "동일한 구조(일반 경로 + 문자권별
# 추가 경로)를 새로 구현한 병행 파일럿"이다 — 불용어 목록은 이 스크립트가 독자적으로
# 정의한 것이며 원본과 개수·내용이 다르다(태국어만 예외 — pythainlp가 실제로 내장하는
# 진짜 불용어 코퍼스를 그대로 사용했다, 아래 참고). 원본 결과와 절대값을 비교할
# 수 없으므로, 이 CSV는 "최종 코퍼스(10,020건)에 새로
# 적용한 병행 산출물"로 취급해야 한다.
#
# 산출: v7_final_10020/analysis/tokenizer/csv/bullet_token_frequency_v7_final.csv
#   컬럼: 순위, 토큰, 등장횟수, 비중(%), 누적비중(%), 문자권
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import fugashi
import jieba
from pythainlp.corpus import thai_stopwords
from pythainlp.tokenize import word_tokenize as thai_word_tokenize

BASE = Path(__file__).resolve().parents[3]  # 저장소 루트 (v7_final_10020/analysis/tokenizer/ 는 3단 깊이)
CORPUS_PATH = BASE / "data" / "v7_final" / "fandoms_v3_100.json"
OUT_PATH = Path(__file__).resolve().parent / "csv" / "bullet_token_frequency_v7_final.csv"

# --- 문자 범위(analysis/tokenizer_script_routing_pilot.ipynb와 동일 정의) -------
RE_KANA = re.compile(r"[぀-ゟ゠-ヿ]")
RE_HANZI = re.compile(r"[一-鿿]")
RE_THAI = re.compile(r"[฀-๿]")
RE_HANGUL = re.compile(r"[가-힣]")
RE_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

# --- 일반 경로: 정규식 토큰화 -----------------------------------------------
# 공백·구두점 경계로 분리. 순수 숫자 토큰은 보고서가 "무의미하므로 제외"한다고
# 밝힌 규칙을 그대로 따른다.
GENERIC_TOKEN_RE = re.compile(r"[^\s\.,;:!?\"'“”‘’()\[\]{}<>·•\-–—/\\|~`^*+=_@#$%&《》「」『』]+")
PURE_NUMERIC_RE = re.compile(r"^[\d,\.%]+$")


def is_pure_numeric(tok: str) -> bool:
    return bool(PURE_NUMERIC_RE.match(tok))


# --- 불용어 목록(이 스크립트 독자 정의 — 원본과 다름, 참고용) ---------------------
KOREAN_STOPWORDS = {
    "그리고", "그러나", "하지만", "또한", "그래서", "따라서", "이는", "이를", "이에",
    "등이", "등을", "등의", "등은", "등에", "등", "및", "이", "그", "저", "것",
    "것으로", "것이다", "것은", "것을", "수", "등장", "위해", "통해", "대해",
    "관련", "이번", "당시", "현재", "이후", "이전", "한편", "특히", "다시",
    "함께", "가장", "또", "더", "많이", "이라고", "라고", "라며", "이라며",
    "하며", "하고", "했다", "있다", "된다", "이다", "됐다", "있으며", "하는",
    "된", "한", "할", "하는데", "에서", "에게", "으로", "로써", "으로써",
    "까지", "부터", "에도", "에는", "에서는", "이나", "나", "도", "만",
}
ENGLISH_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "from", "has", "have", "had",
    "not", "will", "would", "can", "could", "about", "into", "than", "then",
    "so", "such", "also", "more", "most", "over", "after", "before", "during",
    "between", "up", "down", "out", "off", "only", "other", "some", "all",
    "each", "both", "few", "own", "same", "just", "he", "she", "they", "we",
    "you", "his", "her", "their", "our", "your",
}
LATIN_OTHER_STOPWORDS = {  # 스페인어·프랑스어·포르투갈어·인도네시아어·베트남어·튀르키예어 통합
    "el", "la", "los", "las", "de", "del", "en", "un", "una", "que", "por",
    "para", "con", "su", "sus", "es", "se", "lo", "al",
    "le", "les", "des", "et", "un", "une", "dans", "sur", "avec", "pour",
    "yang", "dan", "di", "ke", "dari", "untuk", "pada", "dengan", "ini", "itu",
    "và", "của", "là", "có", "cho", "trong", "được", "này", "với",
    "ve", "bir", "bu", "de", "da", "için", "ile",
}
RUSSIAN_STOPWORDS = {
    "и", "в", "не", "на", "что", "с", "по", "для", "как", "это", "к", "из",
    "за", "от", "но", "а", "же", "то", "его", "её", "их",
}
JAPANESE_STOPWORDS = {
    "の", "に", "は", "を", "が", "で", "と", "も", "から", "まで", "する",
    "いる", "ある", "こと", "もの", "ため", "よう", "これ", "それ", "あの",
    "この", "その", "です", "ます", "った", "て", "た", "な", "だ",
}
CHINESE_STOPWORDS = {
    "的", "了", "在", "是", "和", "与", "也", "都", "就", "而", "及", "或",
    "对", "但", "而且", "因为", "所以", "一个", "这个", "那个", "为", "被",
    "着", "地", "得", "很", "又", "并", "以", "之", "其", "此",
}
THAI_STOPWORDS = set(thai_stopwords())  # pythainlp 내장 실제 불용어(보고서 설명과 일치)

ALL_GENERIC_STOPWORDS = (
    KOREAN_STOPWORDS | ENGLISH_STOPWORDS | LATIN_OTHER_STOPWORDS | RUSSIAN_STOPWORDS
)

_fugashi_tagger = fugashi.Tagger()
_JA_KEEP_POS = {"名詞", "動詞", "形容詞"}  # 보고서: "명사·동사·형용사만 채택"


def tokenize_generic(text: str) -> list[str]:
    tokens = []
    for raw in GENERIC_TOKEN_RE.findall(text):
        tok = raw.strip()
        if len(tok) < 2:
            continue
        if is_pure_numeric(tok):
            continue
        if tok.lower() in ALL_GENERIC_STOPWORDS:
            continue
        tokens.append(tok)
    return tokens


def tokenize_ja_extra(text: str) -> list[str]:
    out = []
    for w in _fugashi_tagger(text):
        pos1 = w.feature.pos1
        surface = w.surface
        if pos1 in _JA_KEEP_POS and surface not in JAPANESE_STOPWORDS and len(surface) >= 1:
            if RE_KANA.search(surface) or RE_HANZI.search(surface):
                out.append(surface)
    return out


def tokenize_zh_extra(text: str) -> list[str]:
    out = []
    for w in jieba.cut(text):
        w = w.strip()
        if not w or w in CHINESE_STOPWORDS:
            continue
        if not RE_HANZI.search(w):
            continue
        out.append(w)
    return out


def tokenize_th_extra(text: str) -> list[str]:
    out = []
    for w in thai_word_tokenize(text, engine="newmm"):
        w = w.strip()
        if not w or w in THAI_STOPWORDS:
            continue
        if not RE_THAI.search(w):
            continue
        out.append(w)
    return out


def script_of(tok: str) -> str:
    """토큰 표면형의 문자권 사후 분류(어느 하위 토크나이저가 만들었는지가 아님). jieba_and_thai_engine_details_v7.py가 import하므로 모듈 수준에 둔다."""
    if RE_KANA.search(tok):
        return "일본어"
    if RE_HANZI.search(tok):
        return "중국어"
    if RE_THAI.search(tok):
        return "태국어"
    if RE_HANGUL.search(tok):
        return "한국어"
    if RE_CYRILLIC.search(tok):
        return "러시아어"
    return "라틴(영어 등)"


def tokenize_bullet(text: str) -> list[str]:
    """보고서 1절 구조 재구현: 일반 경로 항상 실행 + 문자권별 추가 경로(additive)."""
    tokens = tokenize_generic(text)
    if RE_KANA.search(text):
        tokens += tokenize_ja_extra(text)
    elif RE_HANZI.search(text):
        # 보고서 7절 [정정]: 가나+한자 동시 존재 시 일본어 우선 처리(위 elif로 구현),
        # 가나 없이 한자만 있을 때만 중국어 형태소 분석기를 추가로 얹는다.
        tokens += tokenize_zh_extra(text)
    if RE_THAI.search(text):
        tokens += tokenize_th_extra(text)
    return tokens


def load_corpus():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    fandoms = load_corpus()
    all_tokens = []
    bullet_count = 0
    per_bullet_counts = []

    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for bullet in fd.get(tag, []):
                text = bullet.get("t", "") or ""
                bullet_count += 1
                toks = tokenize_bullet(text)
                all_tokens.extend(toks)
                per_bullet_counts.append(len(toks))

    print(f"[집계] 불릿 수: {bullet_count}건 (기대: 10,020)")
    assert bullet_count == 10020
    total_tokens = len(all_tokens)
    freq = Counter(all_tokens)
    print(f"[집계] 토큰 총 발생 수: {total_tokens}건, 고유 토큰(어휘) 수: {len(freq)}개")
    print(f"[집계] 불릿당 평균 토큰 수: {total_tokens / bullet_count:.2f}개")
    assert sum(freq.values()) == total_tokens

    rows = freq.most_common()
    cumulative = 0
    csv_rows = []
    for rank, (tok, cnt) in enumerate(rows, 1):
        cumulative += cnt
        csv_rows.append({
            "순위": rank,
            "토큰": tok,
            "등장횟수": cnt,
            "비중(%)": round(cnt / total_tokens * 100, 4),
            "누적비중(%)": round(cumulative / total_tokens * 100, 4),
            "문자권": script_of(tok),
        })

    # 자체 검증: 비중 합계가 100%에 근접(반올림 오차만 존재)해야 함
    share_sum = sum(r["비중(%)"] for r in csv_rows)
    share_sum_exact = sum(cnt / total_tokens * 100 for _, cnt in rows)
    print(f"[검증] 비중(%) 합계(정확값): {share_sum_exact:.6f}% | 소수 4자리 반올림 후 합계: {share_sum:.2f}% "
          f"(고유 토큰 {len(csv_rows):,}개 × 최대 0.00005 반올림 오차 → 고정 0.5%p 허용치보다 커질 수 있음)")
    assert abs(share_sum_exact - 100.0) < 1e-6
    assert abs(share_sum - 100.0) < 0.00005 * len(csv_rows) + 0.01
    print(f"[검증] 마지막 행 누적비중: {csv_rows[-1]['누적비중(%)']:.2f}% (기대: 100.00%)")
    assert abs(csv_rows[-1]["누적비중(%)"] - 100.0) < 0.01

    script_totals = Counter(r["문자권"] for r in csv_rows for _ in range(r["등장횟수"]))
    print("\n[집계] 문자권별 토큰 발생 수·비중")
    for script, cnt in script_totals.most_common():
        print(f"  {script}: {cnt}건 ({cnt/total_tokens*100:.2f}%)")

    print("\n[상위 20개 토큰]")
    for r in csv_rows[:20]:
        print(f"  {r['순위']:3d}. {r['토큰']:15s} {r['등장횟수']:5d}건  {r['비중(%)']:.3f}%")

    import csv as csv_module
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv_module.DictWriter(f, fieldnames=["순위", "토큰", "등장횟수", "비중(%)", "누적비중(%)", "문자권"])
        w.writeheader()
        w.writerows(csv_rows)
    print(f"\n=== 저장 완료: {OUT_PATH} ({len(csv_rows)}개 고유 토큰) ===")

    # 원본 토크나이저 실행 결과(data/v7_final/wordcloud_by_language_v7.json)와의 대조 — 원본 불용어 목록이 없으므로
    # 절대값 비교가 아니라 "버킷별 상위 30개 단어 중 이 병행 구현의 어휘에 같은 표면형으로 존재하는 비율"만 본다.
    wc_path = BASE / "data" / "v7_final" / "wordcloud_by_language_v7.json"
    with open(wc_path, encoding="utf-8") as f:
        wc = json.load(f)
    print(f"\n[대조] 원본 실행 결과 wordcloud_by_language_v7.json: 불릿 {wc['total_bullets']}건, 토큰 {wc['total_tokens']:,}개 "
          f"(이 병행 구현: 토큰 {total_tokens:,}개, 어휘 {len(freq):,}개)")
    for b in wc["buckets"]:
        words = [w["word"] for w in b["top_30"]]
        present = sum(1 for w in words if w in freq)
        print(f"  {b['bucket'][:12]:12s} 원본 상위30 중 병행 어휘에 존재: {present}/30  (원본 토큰 {b['n_total_tokens']:,}, 상위3 {words[:3]})")


if __name__ == "__main__":
    main()
