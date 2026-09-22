# -*- coding: utf-8 -*-
"""토크나이저 불용어 목록을 코드에서 그대로 추출해 언어별 CSV·MD로 내보낸다.

출처 3곳 (전부 이 저장소 안의 실제 코드/라이브러리에서 읽는다 — 손으로 옮겨 적지 않는다):
  A. run_lda_v6.py (저장소 루트, 원 파이프라인)          — PARTICLES(한국어 조사 접미사), STOPWORDS(한국어), ENGLISH_STOPWORDS
       → 파일을 import 하면 LDA가 실행되므로 ast 로 리터럴만 읽는다.
  B. ../build_bullet_token_frequency_csv_v7.py (최종 코퍼스 10,020건 토큰 빈도 스크립트)
       — KOREAN/ENGLISH/LATIN_OTHER/RUSSIAN/JAPANESE/CHINESE_STOPWORDS (스크립트 독자 정의)
       → import 해서 실제 set 객체를 읽는다(fugashi·jieba·pythainlp 필요). LATIN_OTHER 는 소스 줄 순서로 세부 언어를 붙인다.
  C. pythainlp.corpus.thai_stopwords() — B 의 태국어 경로가 그대로 쓰는 내장 목록(1,030개)

출력 (같은 폴더):
  tokenizer_stopwords_by_language_v7.csv   컬럼: 출처, 스크립트, 목록명, 언어, 세부언어, 불용어, 비고
  TOKENIZER_STOPWORDS_BY_LANGUAGE.md       언어별 표 + 개수 요약 + 원 보고서(14개 언어 라우팅 토크나이저)와의 관계

실행: python v7_final_10020/analysis/tokenizer/stopwords/export_tokenizer_stopwords_v7.py
"""
import ast
import csv
import importlib.util
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOK_DIR = HERE.parent
REPO = HERE.parents[3]
RUN_LDA = REPO / "run_lda_v6.py"
TOK_SCRIPT = TOK_DIR / "build_bullet_token_frequency_csv_v7.py"
OUT_CSV = HERE / "tokenizer_stopwords_by_language_v7.csv"
OUT_MD = HERE / "TOKENIZER_STOPWORDS_BY_LANGUAGE.md"


# --- A. run_lda_v6.py — ast 로 리터럴만 추출 -----------------------------------
def literal_assignments(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            nm = node.targets[0].id
            if nm in names:
                found[nm] = [c.value for c in ast.walk(node.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    missing = set(names) - set(found)
    if missing:
        raise SystemExit(f"{path.name}에서 찾지 못함: {missing}")
    return found


run_lda = literal_assignments(RUN_LDA, ["PARTICLES", "STOPWORDS", "ENGLISH_STOPWORDS"])


# --- B. build_bullet_token_frequency_csv_v7.py — import 로 실제 set 읽기 ------------
spec = importlib.util.spec_from_file_location("bbtf", TOK_SCRIPT)
bbtf = importlib.util.module_from_spec(spec)
sys.modules["bbtf"] = bbtf
spec.loader.exec_module(bbtf)

# LATIN_OTHER: 소스의 줄 순서(스페인어 2줄 → 프랑스어 → 인도네시아어 → 베트남어 → 튀르키예어)로 세부 언어를 붙인다
LATIN_LINE_LANGS = ["es", "es", "fr", "id", "vi", "tr"]
LANG_NAME = {"es": "스페인어", "fr": "프랑스어", "id": "인도네시아어", "vi": "베트남어", "tr": "튀르키예어"}
tree = ast.parse(TOK_SCRIPT.read_text(encoding="utf-8"))
latin_node = next(n for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "LATIN_OTHER_STOPWORDS")
latin_lines = sorted({c.lineno for c in ast.walk(latin_node.value) if isinstance(c, ast.Constant)})
latin_by_lang = OrderedDict((k, []) for k in ["es", "fr", "id", "vi", "tr"])
for c in ast.walk(latin_node.value):
    if isinstance(c, ast.Constant) and isinstance(c.value, str):
        lang = LATIN_LINE_LANGS[latin_lines.index(c.lineno)]
        latin_by_lang[lang].append(c.value)
assert set(w for ws in latin_by_lang.values() for w in ws) == bbtf.LATIN_OTHER_STOPWORDS

# --- C. pythainlp 내장 태국어 불용어 ---------------------------------------------
from pythainlp.corpus import thai_stopwords  # noqa: E402
import pythainlp  # noqa: E402

thai = sorted(thai_stopwords())
assert set(thai) == bbtf.THAI_STOPWORDS


# --- CSV ---------------------------------------------------------------------
def dedup_keep_order(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


rows = []
def add(source, script, listname, lang, sublang, words, note=""):
    for w in words:
        rows.append({"출처": source, "스크립트": script, "목록명": listname, "언어": lang, "세부언어": sublang, "불용어": w, "비고": note})


A = "A. 원 파이프라인"; A_s = "run_lda_v6.py"
add(A, A_s, "PARTICLES", "한국어", "ko", dedup_keep_order(run_lda["PARTICLES"]), "접미사 제거 규칙")
add(A, A_s, "STOPWORDS", "한국어", "ko", sorted(set(run_lda["STOPWORDS"])), "접미사 제거 후 제외")
add(A, A_s, "ENGLISH_STOPWORDS", "영어", "en", sorted(set(run_lda["ENGLISH_STOPWORDS"])), "소문자 비교")
B = "B. 최종 코퍼스 토큰 빈도"; B_s = "build_bullet_token_frequency_csv_v7.py"
add(B, B_s, "KOREAN_STOPWORDS", "한국어", "ko", sorted(bbtf.KOREAN_STOPWORDS), "독자 정의")
add(B, B_s, "ENGLISH_STOPWORDS", "영어", "en", sorted(bbtf.ENGLISH_STOPWORDS), "독자 정의")
for lang, ws in latin_by_lang.items():
    add(B, B_s, "LATIN_OTHER_STOPWORDS", LANG_NAME[lang], lang, ws, "라틴 통합 목록, 세부언어는 소스 줄 순서")
add(B, B_s, "RUSSIAN_STOPWORDS", "러시아어", "ru", sorted(bbtf.RUSSIAN_STOPWORDS), "키릴 문자")
add(B, B_s, "JAPANESE_STOPWORDS", "일본어", "ja", sorted(bbtf.JAPANESE_STOPWORDS), "fugashi 명사·동사·형용사 채택 후 제외")
add(B, B_s, "CHINESE_STOPWORDS", "중국어", "zh", sorted(bbtf.CHINESE_STOPWORDS), "jieba 분리 후 제외")
add("C. pythainlp 내장", f"pythainlp {pythainlp.__version__} corpus.thai_stopwords()", "THAI_STOPWORDS", "태국어", "th", thai, "pythainlp 내장, newmm 경로에서 제외")

with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["출처", "스크립트", "목록명", "언어", "세부언어", "불용어", "비고"])
    w.writeheader(); w.writerows(rows)
print(f"CSV: {OUT_CSV.relative_to(REPO)} ({len(rows)}행)")


# --- MD ----------------------------------------------------------------------
def words_md(ws, per_line=18):
    ws = list(ws)
    lines = []
    for i in range(0, len(ws), per_line):
        lines.append(" · ".join(f"`{x}`" for x in ws[i:i + per_line]))
    return "  \n".join(lines)


counts = OrderedDict()
for r in rows:
    key = (r["출처"], r["목록명"], r["언어"], r["세부언어"])
    counts[key] = counts.get(key, 0) + 1

md = []
md.append("# 토크나이저 불용어 목록 — 언어별 정리 (최종 코퍼스 10,020건 기준)\n")
md.append("이 문서와 같은 폴더의 `tokenizer_stopwords_by_language_v7.csv`는 `export_tokenizer_stopwords_v7.py`가 **저장소 안의 코드에서 직접 읽어** 만든 것이다. "
          "손으로 옮겨 적은 목록이 아니므로, 코드가 바뀌면 스크립트를 다시 돌려 갱신한다.\n")
md.append("## 불용어가 정의된 곳 3군데\n")
md.append("| 출처 | 파일 | 무엇에 쓰이나 | 목록 |\n|---|---|---|---|")
md.append(f"| A | `run_lda_v6.py` (저장소 루트) | 원 파이프라인의 `tokenize()` — LDA 입력 토큰화 (한국어·영어 일반 경로) | PARTICLES {len(dedup_keep_order(run_lda['PARTICLES']))}, STOPWORDS {len(set(run_lda['STOPWORDS']))}, ENGLISH_STOPWORDS {len(set(run_lda['ENGLISH_STOPWORDS']))} |")
md.append(f"| B | `analysis/tokenizer/build_bullet_token_frequency_csv_v7.py` | 최종 코퍼스 10,020건 토큰 빈도 CSV(`csv/bullet_token_frequency_v7_final.csv`) — 일반 경로 + 일본어(fugashi)·중국어(jieba)·태국어(pythainlp) 추가 경로 | 한국어 {len(bbtf.KOREAN_STOPWORDS)}, 영어 {len(bbtf.ENGLISH_STOPWORDS)}, 라틴 통합 {len(bbtf.LATIN_OTHER_STOPWORDS)}, 러시아어 {len(bbtf.RUSSIAN_STOPWORDS)}, 일본어 {len(bbtf.JAPANESE_STOPWORDS)}, 중국어 {len(bbtf.CHINESE_STOPWORDS)} |")
md.append(f"| C | `pythainlp {pythainlp.__version__}` `corpus.thai_stopwords()` | B의 태국어 경로가 그대로 쓰는 라이브러리 내장 목록 | 태국어 {len(thai)} |\n")
md.append("**원 보고서의 14개 언어 라우팅 토크나이저(`run_lda_v6_live_reference_v7.py`)와의 관계.** 보고서 7.7절(`tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` 표 1)은 "
          "STOPWORDS 41종·ENGLISH_STOPWORDS 64종·7개 라틴어권 언어별 세트를 합친 ALL_LATIN_STOPWORDS·RUSSIAN_STOPWORDS·JAPANESE_STOPWORDS 28종·CHINESE_STOPWORDS 60여 종·pythainlp 내장 태국어 불용어를 쓴다고 서술한다. "
          "그 소스는 저장소에 없다. 저장소에 실제로 있는 목록은 A(그 이전 판 파이프라인)와 B(같은 구조를 독자 구현한 병행 파일럿)이며, "
          "태국어(C)만 원 보고서와 동일한 라이브러리 목록이다. 따라서 B의 한국어·영어·라틴·러시아어·일본어·중국어 목록은 원 보고서 목록과 **개수와 내용이 다르다**.\n")
md.append("## 개수 요약\n")
md.append("| 출처 | 목록명 | 언어 | 코드 | 개수 |\n|---|---|---|---|---|")
for (src, ln, lang, sub), n in counts.items():
    md.append(f"| {src} | `{ln}` | {lang} | {sub} | {n} |")
md.append(f"| 합계 | | | | {len(rows)} |\n")

md.append("## A. `run_lda_v6.py` — 원 파이프라인 (한국어·영어)\n")
md.append("토큰 정규식 `[가-힣A-Za-z0-9]{2,}` → 조사 접미사 제거(PARTICLES, 긴 것부터 1회) → 2자 미만·STOPWORDS 제외 → 소문자 ENGLISH_STOPWORDS 제외 → 순수 숫자 제외.\n")
md.append(f"### A-1. PARTICLES — 한국어 조사·어미 접미사 ({len(dedup_keep_order(run_lda['PARTICLES']))}개, 코드 순서)\n")
md.append(words_md(dedup_keep_order(run_lda["PARTICLES"])) + "\n")
md.append(f"### A-2. STOPWORDS — 한국어 ({len(set(run_lda['STOPWORDS']))}개)\n")
md.append(words_md(sorted(set(run_lda["STOPWORDS"]))) + "\n")
md.append(f"### A-3. ENGLISH_STOPWORDS — 영어 ({len(set(run_lda['ENGLISH_STOPWORDS']))}개; 소스 리터럴 {len(run_lda['ENGLISH_STOPWORDS'])}개 중 `up`·`out` 중복)\n")
md.append(words_md(sorted(set(run_lda["ENGLISH_STOPWORDS"]))) + "\n")

md.append("## B. `build_bullet_token_frequency_csv_v7.py` — 최종 코퍼스 토큰 빈도 (일반 경로 + 문자권별 추가 경로)\n")
md.append("일반 경로: 구두점 경계 정규식 토큰화 → 2자 미만·순수 숫자 제외 → 소문자가 아래 한국어·영어·라틴·러시아어 통합 집합에 있으면 제외. "
          "추가 경로: 본문에 가나가 있으면 fugashi(명사·동사·형용사만, 일본어 불용어 제외), 가나 없이 한자만 있으면 jieba(중국어 불용어 제외), 태국 문자가 있으면 pythainlp newmm(내장 불용어 제외).\n")
md.append(f"### B-1. KOREAN_STOPWORDS — 한국어 ({len(bbtf.KOREAN_STOPWORDS)}개)\n")
md.append(words_md(sorted(bbtf.KOREAN_STOPWORDS)) + "\n")
md.append(f"### B-2. ENGLISH_STOPWORDS — 영어 ({len(bbtf.ENGLISH_STOPWORDS)}개)\n")
md.append(words_md(sorted(bbtf.ENGLISH_STOPWORDS)) + "\n")
md.append(f"### B-3. LATIN_OTHER_STOPWORDS — 라틴 문자권 통합 ({len(bbtf.LATIN_OTHER_STOPWORDS)}개 고유; 세부 언어는 소스 줄 순서 기준, `un`·`de`는 두 언어에 중복)\n")
for lang, ws in latin_by_lang.items():
    md.append(f"- **{LANG_NAME[lang]}({lang}) {len(ws)}개**: " + " · ".join(f"`{x}`" for x in ws))
md.append("")
md.append(f"### B-4. RUSSIAN_STOPWORDS — 러시아어 ({len(bbtf.RUSSIAN_STOPWORDS)}개)\n")
md.append(words_md(sorted(bbtf.RUSSIAN_STOPWORDS)) + "\n")
md.append(f"### B-5. JAPANESE_STOPWORDS — 일본어 ({len(bbtf.JAPANESE_STOPWORDS)}개)\n")
md.append(words_md(sorted(bbtf.JAPANESE_STOPWORDS)) + "\n")
md.append(f"### B-6. CHINESE_STOPWORDS — 중국어 ({len(bbtf.CHINESE_STOPWORDS)}개)\n")
md.append(words_md(sorted(bbtf.CHINESE_STOPWORDS)) + "\n")
md.append(f"## C. pythainlp 내장 태국어 불용어 ({len(thai)}개)\n")
md.append(f"`pythainlp.corpus.thai_stopwords()` (pythainlp {pythainlp.__version__}). 전체 목록은 CSV의 `THAI_STOPWORDS` 행에 있다. 앞 60개:\n")
md.append(words_md(thai[:60], per_line=15) + "\n")
md.append("## 함께 보는 파일\n")
md.append("- `../build_bullet_token_frequency_csv_v7.py` — B 목록을 정의하고 최종 코퍼스 10,020건에 적용해 토큰 빈도 CSV를 만드는 코드\n"
          "- `../csv/bullet_token_frequency_v7_final.csv` — 그 결과(43,162 토큰, 176,944 발생)\n"
          "- `../../../../run_lda_v6.py` — A 목록을 정의하는 원 파이프라인\n"
          "- `../../../tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` — 원 보고서의 토크나이저 구조·불용어 개수 서술과 재현 범위\n"
          "- `export_tokenizer_stopwords_v7.py` — 이 문서와 CSV를 코드에서 다시 만드는 스크립트")
OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"MD : {OUT_MD.relative_to(REPO)}")
for (src, ln, lang, sub), n in counts.items():
    print(f"  {src:14s} {ln:24s} {lang:8s} {sub:3s} {n}")
