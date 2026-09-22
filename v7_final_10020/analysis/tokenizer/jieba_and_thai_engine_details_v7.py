# jieba(중국어 형태소 분석 엔진)와 pythainlp의 newmm(태국어 형태소 분석 엔진)
# 상세 스펙을 실제 설치된 패키지에서 직접 읽어 정리하고, 이 프로젝트의 실제
# 코퍼스(최종 10,020건)에 적용한 결과를 재검증한다.
#
# 문서: JIEBA_AND_THAI_TOKENIZER_ENGINE_SPEC_V7.md 참고.
#
# 이 스크립트가 하는 것:
#   1) 설치된 jieba·pythainlp의 버전, 사전 크기, 불용어 코퍼스 크기를 "패키지
#      소스에서 직접" 읽어 출력한다(추측이 아니라 런타임 조회).
#   2) jieba의 DAG+동적계획법 경로와, 사전에 없는 문자열에 대해 HMM(finalseg)이
#      개입하는 사례를 실제로 실행해 보여준다.
#   3) pythainlp newmm의 사전 기반 최장일치(Thai Character Cluster 경계 제약)
#      분절을 실제 태국어 불릿 원문에 실행해 보여준다.
#   4) build_bullet_token_frequency_csv_v7.py가 이미 산출한
#      csv/bullet_token_frequency_v7_final.csv의 중국어·
#      태국어 버킷 집계를, 같은 토크나이저 함수로 독립 재계산해 0건 불일치로
#      재검증한다.
import csv
import sys
from collections import Counter
from pathlib import Path

import jieba
import pythainlp
from pythainlp.corpus import thai_stopwords, thai_words
from pythainlp.tokenize import word_tokenize as thai_word_tokenize

BASE = Path(__file__).resolve().parents[3]  # 저장소 루트 (v7_final_10020/analysis/tokenizer/ 는 3단 깊이)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bullet_token_frequency_csv_v7 import (  # noqa: E402
    RE_HANZI,
    RE_THAI,
    load_corpus,
    script_of,
    tokenize_bullet,
    tokenize_th_extra,
    tokenize_zh_extra,
)

FREQ_CSV = Path(__file__).resolve().parent / "csv" / "bullet_token_frequency_v7_final.csv"


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def report_jieba_spec():
    section("1. jieba 엔진 스펙 (설치된 패키지에서 직접 조회)")
    print(f"버전: jieba {jieba.__version__}")
    dict_path = Path(jieba.__file__).parent / "dict.txt"
    with open(dict_path, encoding="utf-8") as f:
        n_entries = sum(1 for _ in f)
    print(f"기본 사전(dict.txt) 표제어 수: {n_entries:,}개")
    print("알고리즘 (jieba/__init__.py 소스 확인):")
    print("  1) 입력 문장에 대해 사전(prefix dictionary, trie 구조)으로 가능한")
    print("     모든 절단 경로의 DAG(방향성 비순환 그래프)를 구성한다(get_DAG).")
    print("  2) 각 절단 후보 단어의 사전 빈도(FREQ)를 이용해 동적계획법으로")
    print("     문장 전체의 '최대 확률 경로'를 계산한다(calc, __cut_DAG).")
    print("  3) 그 경로에서 사전에 없는 연속 구간(buf)이 나오면, HMM(은닉마르코프")
    print("     모델) 기반 비터비 알고리즘을 쓰는 finalseg 모듈로 새 단어(신조어·")
    print("     고유명사 등)를 추정 분리한다 — 이것이 '사전에 없어도 어느 정도")
    print("     분리는 된다'는 jieba의 핵심 특징이다.")
    print("  4) 기본 cut()은 '정밀 모드'(cut_all=False)+HMM=True로 동작한다 —")
    print("     이 프로젝트의 tokenize_zh_extra()도 기본값 그대로 사용한다.")


def report_thai_spec():
    section("2. pythainlp newmm(태국어) 엔진 스펙 (설치된 패키지에서 직접 조회)")
    print(f"버전: pythainlp {pythainlp.__version__}")
    words = thai_words()
    stopwords = thai_stopwords()
    print(f"기본 태국어 사전(thai_words) 표제어 수: {len(words):,}개")
    print(f"내장 태국어 불용어(thai_stopwords) 수: {len(stopwords):,}개")
    print("알고리즘 (pythainlp/tokenize/newmm.py 소스 상단 docstring 확인):")
    print("  \"Dictionary-based maximal matching word segmentation, constrained")
    print("   by Thai Character Cluster (TCC) boundaries\" — 사전 기반 최장")
    print("   일치 분절이되, 태국 문자는 자음+모음+성조부호가 한 덩어리(TCC)로")
    print("   묶여야 하는 특성이 있어 그 경계를 벗어나는 절단은 애초에 후보에서")
    print("   제외한다(tcc_pos_array). 그래프 폭발을 막기 위한 그래프 크기")
    print("   상한(_MAX_GRAPH_SIZE=50)과, 긴 문장을 위한 '안전 모드' 슬라이딩")
    print("   윈도(_TEXT_SCAN_*)도 소스에 정의되어 있다.")
    print("  이 프로젝트의 tokenize_th_extra()는 기본 엔진 'newmm'과 위 내장")
    print("  불용어(thai_stopwords)를 그대로 사용한다.")


def demo_jieba_dag_and_hmm():
    section("3. jieba 실행 데모 — 사전 매칭 vs. HMM 신조어 추정")
    known = "北京天安门欢迎你"
    print(f"사전에 있는 일반 어휘: {known!r}")
    print(f"  -> {list(jieba.cut(known, HMM=True))}")

    # 사전에 없을 법한 고유명사(인명)가 섞인 문장을 HMM 유무로 비교 —
    # K-pop/한류 도메인에서 실제로 자주 등장하는 유형(사전에 없는 한국 인명의
    # 한자 음역)이라 이 프로젝트와 관련이 있다.
    novel = "朴敏英现象级效应"  # "박민영 현상급 효과" 식의 한자 음역 인명 + 신조어 조합(가상 예시)
    with_hmm = list(jieba.cut(novel, HMM=True))
    without_hmm = list(jieba.cut(novel, HMM=False))
    print(f"\n사전에 없을 가능성이 있는 인명 포함 문장: {novel!r}")
    print(f"  HMM=True  -> {with_hmm}")
    print(f"  HMM=False -> {without_hmm}")
    if with_hmm != without_hmm:
        print("  -> 실제로 차이가 남: HMM=True는 사전에 없는 인명(朴敏英)을 하나의")
        print("     단위로 묶어내지만, HMM=False는 개별 한자로 쪼갠다. 이 프로젝트")
        print("     코퍼스에 등장하는, 사전에 없을 한국·아이돌 고유명사의 한자")
        print("     표기에서 HMM이 실제로 이런 역할을 할 수 있음을 보여준다.")
    else:
        print("  -> 이 예시에서는 두 결과가 같았다(사전에 이미 등재된 조합일 수")
        print("     있음) — HMM 개입 여부는 입력 문자열에 따라 달라진다.")


def demo_thai_newmm():
    section("4. pythainlp newmm 실행 데모 — 실제 코퍼스 태국어 불릿")
    fandoms = load_corpus()
    sample_text = None
    sample_fandom = None
    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for bullet in fd.get(tag, []):
                t = bullet.get("t", "") or ""
                if RE_THAI.search(t):
                    sample_text, sample_fandom = t, fd.get("fandom")
                    break
            if sample_text:
                break
        if sample_text:
            break
    print(f"코퍼스에서 찾은 실제 태국어 포함 불릿 (팬덤: {sample_fandom}):")
    print(f"  원문: {sample_text}")
    print(f"  newmm 분절: {thai_word_tokenize(sample_text, engine='newmm')}")
    print(f"  본 프로젝트 필터(불용어·비태국문자 제거) 적용 후: {tokenize_th_extra(sample_text)}")


def reverify_against_frequency_csv():
    section("5. csv/bullet_token_frequency_v7_final.csv의 중국어·태국어 버킷 재검증")
    print("주의: CSV의 '문자권' 컬럼은 어느 하위 토크나이저가 그 토큰을 만들었는지가")
    print("아니라, 최종 토큰 표면형 자체에 어떤 문자가 있는지로 사후 분류한 것이다")
    print("(build_bullet_token_frequency_csv_v7.py의 script_of() 참고) — 그래서 '일반")
    print("경로'가 우연히 만들어낸 한자·태국문자 토큰(예: 한국어 문장에 인용부호로")
    print("섞인 외국어 고유명사)도 이 버킷에 함께 잡힌다. 아래 재검증은 그래서")
    print("tokenize_zh_extra()/tokenize_th_extra()만이 아니라 전체 파이프라인")
    print("(tokenize_bullet, 일반 경로+추가 경로)을 그대로 재실행해 CSV와 같은")
    print("기준으로 맞춘다.")

    fandoms = load_corpus()
    zh_counter, th_counter = Counter(), Counter()
    for fd in fandoms:
        for tag in ("loyalty", "spillover"):
            for bullet in fd.get(tag, []):
                text = bullet.get("t", "") or ""
                for tok in tokenize_bullet(text):
                    label = script_of(tok)
                    if label == "중국어":
                        zh_counter[tok] += 1
                    elif label == "태국어":
                        th_counter[tok] += 1

    with open(FREQ_CSV, encoding="utf-8-sig") as f:
        csv_rows = list(csv.DictReader(f))
    csv_zh = {r["토큰"]: int(r["등장횟수"]) for r in csv_rows if r["문자권"] == "중국어"}
    csv_th = {r["토큰"]: int(r["등장횟수"]) for r in csv_rows if r["문자권"] == "태국어"}

    zh_mismatch = sum(1 for tok, cnt in zh_counter.items() if csv_zh.get(tok) != cnt)
    th_mismatch = sum(1 for tok, cnt in th_counter.items() if csv_th.get(tok) != cnt)
    print(f"중국어 토큰 재계산: 고유 {len(zh_counter)}개 / CSV 기록 {len(csv_zh)}개, 불일치 {zh_mismatch}건")
    print(f"태국어 토큰 재계산: 고유 {len(th_counter)}개 / CSV 기록 {len(csv_th)}개, 불일치 {th_mismatch}건")
    assert len(zh_counter) == len(csv_zh) and zh_mismatch == 0, "중국어 버킷 불일치"
    assert len(th_counter) == len(csv_th) and th_mismatch == 0, "태국어 버킷 불일치"
    print("-> PASS: CSV의 중국어·태국어 버킷이 이 스크립트의 독립 재계산과 정확히 일치")

    print(f"\n중국어 상위 10개: {zh_counter.most_common(10)}")
    print(f"태국어 상위 10개: {th_counter.most_common(10)}")


if __name__ == "__main__":
    report_jieba_spec()
    report_thai_spec()
    demo_jieba_dag_and_hmm()
    demo_thai_newmm()
    reverify_against_frequency_csv()
