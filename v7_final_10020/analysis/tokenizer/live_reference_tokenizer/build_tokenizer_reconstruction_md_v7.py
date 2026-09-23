# -*- coding: utf-8 -*-
"""TOKENIZER_RECONSTRUCTION_V7.md 를 검증 결과 JSON 두 개에서 생성한다 (수치를 손으로 옮기지 않기 위해).
  입력: tokenizer_reconstruction_check_v7.json (verify_tokenizer_reconstruction_v7.py)
        live_reference_refit_comparison_v7.json (compare_live_reference_refit_v7.py)
실행: python build_tokenizer_reconstruction_md_v7.py
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
C = json.load(open(HERE / "tokenizer_reconstruction_check_v7.json", encoding="utf-8"))
R = json.load(open(HERE / "live_reference_refit_comparison_v7.json", encoding="utf-8"))
src = (REPO / "run_lda_v6_live_reference_v7.py").read_text(encoding="utf-8")
block = src[src.index("# === TOKENIZER BEGIN ==="):src.index("# === TOKENIZER END ===")]
ns = {"re": re, "__name__": "x"}
try:
    exec("import re\nfrom urllib.parse import urlparse\n" + block.split("# === TOKENIZER BEGIN ===")[1], ns)
    counts = {k: len(ns[k]) for k in ("PARTICLES", "STOPWORDS", "STOPWORDS_R38_EXTRA", "ENGLISH_STOPWORDS", "ENGLISH_STOPWORDS_R38_EXTRA", "LATIN_STOPWORDS", "RUSSIAN_STOPWORDS", "JAPANESE_STOPWORDS", "CHINESE_STOPWORDS", "THAI_STOPWORDS")}
except Exception:
    counts = {}

md = []
md.append("# 14개 언어 라우팅 토크나이저 재구성 — `run_lda_v6_live_reference_v7.py`\n")
md.append("## 0. 한눈에 보기\n")
md.append("최종 참고 재적합(10,020건 → 10,018문서, K=8/M=5/실루엣 0.046)을 만든 `run_lda_v6_live_reference_v7.py`의 원본 소스는 유실됐다. "
          "이 폴더는 그 파일을 저장소 재료로 다시 만든 과정과 결과다. 저장소 루트의 `run_lda_v6_live_reference_v7.py`가 재구성본이다.\n")
md.append("| 항목 | 값 |\n|---|---|")
md.append(f"| LDA 문서 수 | {C['n_docs'][0]:,} / 원본 {C['n_docs'][1]:,} |")
md.append(f"| 3토큰 미만 제외 | 2건, 문장·토큰까지 원본(`lda_excluded_bullets_v7.json`)과 일치: {C['excluded_match']} |")
md.append(f"| 총 토큰 | {C['total_tokens'][0]:,} / 원본 {C['total_tokens'][1]:,} ({C['total_tokens'][0]/C['total_tokens'][1]:.4%}) |")
top_exact = sum(b["top30_exact"] for b in C["buckets"]); md.append(f"| 8개 버킷 상위 30단어 카운트 | {top_exact}/240 일치 |")
md.append(f"| 자기인용 제거 불릿 | {C['self_citation_bullets'][0]} / 보고서 기술 {C['self_citation_bullets'][1]} (4절) |")
if R:
    s = R["selection"]; md.append(f"| 재적합 선택 K / M / 실루엣 | {s['selected_k'][0]} / {s['selected_m'][0]} / {s['silhouette'][0]} — 원본 {s['selected_k'][1]} / {s['selected_m'][1]} / {s['silhouette'][1]} |")
md.append("")
md.append("**재구성본이지 원본이 아니다.** 아래 목표값 대조로 동작이 원본과 거의 같음을 보였지만, 불용어 목록의 글자 단위 동일성은 보장하지 못한다. "
          "특히 원본 top-30에 나타나지 않는 저빈도 불용어는 어느 쪽으로도 확인할 수 없다.\n")

md.append("## 1. 무엇을 근거로 다시 만들었나\n")
md.append("| 근거 | 내용 | 쓰임 |\n|---|---|---|")
md.append("| `run_lda_v6.py` (저장소) | 구 토크나이저 판 파이프라인. PARTICLES 40·STOPWORDS 30·ENGLISH_STOPWORDS 118, `tokenize()`, K-grid → K→M → 점수 | 파이프라인 전체와 (a) 목록을 그대로 씀 |")
md.append("| `tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` 1∼5절 | 라우팅 구조(일반 경로 + 가나/한자/태국 문자 분기), 언어별 불용어 종류, 순수 숫자 제외, 도메인 조각 제거, 자기인용 슬러그(nautiljon.com→nautiljon, detik.com→detik+detikcom), 811건 | 구조와 규칙의 사양 |")
md.append("| `data/v7_final/wordcloud_by_language_v7.json` | 원본 토크나이저를 실제 실행한 결과: 8개 버킷별 불릿 수·토큰 수·어휘 종수·상위 30단어 카운트, 총 170,725, 버킷 분류 규칙(methodology) | 목표값 ② |")
md.append("| `data/v7_final/lda_excluded_bullets_v7.json` | 제외 2건의 문장과 토큰(`['วาสนา','ได๋น้อ']`, `['맥도날드','조이']`) | 목표값 ① |")
md.append("| `data/v7_final/lda_v6_diagnostics_live_reference_v7.json`, `fandom_scores_live_reference_v7.json` | K-grid 7개 K 의 4개 지표, 선택 K·M·실루엣, 토픽 상위어, 팬덤별 factor_share | 목표값 ③ |")
md.append("| `analysis/tokenizer/build_bullet_token_frequency_csv_v7.py`, `JIEBA_AND_THAI_TOKENIZER_ENGINE_SPEC_V7.md` | fugashi(unidic-lite)·jieba(HMM)·pythainlp newmm 호출 방식 | 형태소 분석기 경로 |\n")

md.append("## 2. 재구성한 토크나이저의 구조\n")
md.append("```\ntokenize(text, url)\n  text = strip_domain_fragments(text)        # natalie.mu, oricon.co.jp 같은 도메인 표기 제거\n"
          "  toks = tokenize_generic(text, url)         # 정규식 [가-힣A-Za-z0-9À-ɏḀ-ỿЀ-ӿ]{2,} → 조사 접미사 제거 → 불용어 → 순수 숫자 제외 → 자기인용 슬러그 제외\n"
          "  if 가나 in text:   toks += tokenize_ja(text)   # fugashi: 名詞·動詞·形容詞, 2자 이상, JAPANESE_STOPWORDS\n"
          "  elif 한자 in text: toks += tokenize_zh(text)   # jieba: 한자 포함·2자 이상, CHINESE_STOPWORDS\n"
          "  if 태국문자 in text: toks += tokenize_th(text) # pythainlp newmm: 태국 문자 포함·2자 이상, 내장 불용어\n```\n")
if counts:
    md.append("| 목록 | 크기 | 출처 |\n|---|---|---|")
    md.append(f"| PARTICLES (조사 접미사) | {counts['PARTICLES']} | run_lda_v6.py 그대로 |")
    md.append(f"| STOPWORDS (한국어) | {counts['STOPWORDS']} + v7 38 추가 {counts['STOPWORDS_R38_EXTRA']} = {counts['STOPWORDS'] + counts['STOPWORDS_R38_EXTRA']} | 30은 run_lda_v6.py, 11은 재구성(보고서: 41종) |")
    md.append(f"| ENGLISH_STOPWORDS | {counts['ENGLISH_STOPWORDS']} + 확장 {counts['ENGLISH_STOPWORDS_R38_EXTRA']} | 118은 run_lda_v6.py, 확장분은 총계 대조로 재구성 |")
    md.append(f"| LATIN_STOPWORDS (es·fr·pt·id/ms·vi·tr·tl) | {counts['LATIN_STOPWORDS']} | 재구성 |")
    md.append(f"| RUSSIAN_STOPWORDS | {counts['RUSSIAN_STOPWORDS']} | 재구성 |")
    md.append(f"| JAPANESE_STOPWORDS | {counts['JAPANESE_STOPWORDS']} | 재구성(보고서: 28종) |")
    md.append(f"| CHINESE_STOPWORDS | {counts['CHINESE_STOPWORDS']} | 재구성(보고서: 60여 종) |")
    md.append(f"| THAI_STOPWORDS | {counts['THAI_STOPWORDS']:,} | pythainlp 내장 그대로 |\n")

md.append("## 3. 어떻게 맞췄나 — 대조로 확정된 규칙\n")
md.append("원본 실행 결과가 남긴 수치가 규칙을 하나씩 결정해 줬다. 아래는 그 순서다.\n")
md.append("1. **문자 클래스**: 비영어 버킷 원본 top-30에 `2×`(U+00D7 포함)·`pookïe`·`şarkıcı`·`İstanbul`이 있어 라틴 확장 범위 `À-ɏ`(U+00C0∼U+024F) 전체가 클래스에 포함됨을 확인. 베트남어 `Ḁ-ỿ`, 키릴 `Ѐ-ӿ` 포함.\n"
          "2. **한국어**: run_lda_v6.py의 PARTICLES·STOPWORDS(30)만으로 원본 top-30이 30/30 일치. 원본에 없는데 내 카운트가 380(30위) 이상인 토큰이 `만에`(472)·`에서`(435)뿐이라 보고서가 예시한 v7 38 bare 조사 추가를 확인. 총계 차이(+138)와 어휘 종수 차이로 나머지 추가분 9개(`따르면`·`에는`·`에도`·`까지`·`부터`·`에게`·`라며`·`이에`·`때문`)를 골랐다 — 합 41종.\n"
          "3. **영어**: 118종 목록으로 top-30 일치. `first`·`new`·`one`이 원본 top-30에 없어(있었다면 ≥93회) 118종이 원본과 같다고 판단(보고서의 '64종'은 계수 방식 차이로 봄). 총계·어휘 종수 대조로 기능어 확장분을 추가.\n"
          "4. **자기인용 슬러그**: `SBS`(원본 153, news.sbs.co.kr 인용 불릿에서 제거됨)와 `Music`(원본 110, music.163.com 인용 불릿에서 제거되지 않음)이 규칙을 결정 — 첫 라벨이 아니라 **등록 도메인 라벨**(co.kr·co.jp·com.br 같은 2단 접미 인식)이다. 이 규칙으로 영어 top-30이 30/30 일치.\n"
          "5. **일본어·중국어·태국어**: 원본 top-30에 한 글자 토큰이 없고 `會`·`來`·`し`·`ม` 같은 한 글자가 내 출력에서 상위에 올라 **2자 이상 필터**를 확인. 태국어는 이것으로 불릿·토큰·어휘 전부 일치, 중국어는 불릿·어휘 일치(토큰 −2), 일본어는 불릿 일치(토큰 +15).\n"
          "6. **제외 2건**: ATEEZ 태국어 `วาสนาผู้ได๋น้อ?` → `['วาสนา','ได๋น้อ']`(`ผู้`는 내장 불용어), 레드벨벳 `맥도날드 조이 (2026)` → `['맥도날드','조이']`(2026은 순수 숫자). 두 건 모두 원본과 토큰까지 같다.\n")

md.append("## 4. 검증 결과 ①② — 토크나이저 출력 대조\n")
md.append("| 버킷 | 불릿 (재구성/원본) | 토큰 | 어휘 종수 | top-30 카운트 일치 | 불일치 단어 |\n|---|---|---|---|---|---|")
for b in C["buckets"]:
    diff = ", ".join(f"{w} {v[0]}/{v[1]}" for w, v in b["top30_diff"].items()) or "—"
    md.append(f"| {b['bucket']} | {b['bullets'][0]:,}/{b['bullets'][1]:,} | {b['tokens'][0]:,}/{b['tokens'][1]:,} | {b['distinct'][0]:,}/{b['distinct'][1]:,} | {b['top30_exact']}/30 | {diff} |")
md.append(f"| **합계** | | **{C['total_tokens'][0]:,}/{C['total_tokens'][1]:,}** | | **{top_exact}/240** | |\n")
md.append(f"자기인용 슬러그 제거 불릿은 {C['self_citation_bullets'][0]}건으로 보고서의 811건과 다르다. 단어 단위 근거(`SBS`·`Music`·영어 top-30 전부)는 등록 도메인 규칙을 지지하므로 이 규칙을 택했고, 811이라는 집계가 어떤 세부 조건(예: 매체 유형 제한)으로 나왔는지는 알 수 없어 그대로 적어 둔다.\n")

if R:
    md.append("## 5. 검증 결과 ③ — 재적합 K-grid·K·M·실루엣 대조\n")
    md.append("재구성 스크립트를 최종 코퍼스 10,020건에 실제로 돌린 결과(`output/lda_live_reference_v7/`)와 원본 라이브 참고 재적합의 대조. 토큰이 완전히 같지 않고 LDA는 DTM의 작은 차이에도 민감하므로 마지막 자리까지 같을 수는 없다.\n")
    md.append("| K | perplexity 재구성/원본 | coherence | diversity | stability | rank_sum |\n|---|---|---|---|---|---|")
    for r in R["k_grid"]:
        md.append(f"| {r['k']} | {r['perplexity'][0]:.1f} / {r['perplexity'][1]:.1f} | {r['coherence'][0]:.3f} / {r['coherence'][1]:.3f} | {r['diversity'][0]:.3f} / {r['diversity'][1]:.3f} | {r['stability'][0]:.3f} / {r['stability'][1]:.3f} | {r['composite_rank_sum'][0]} / {r['composite_rank_sum'][1]} |")
    s = R["selection"]
    md.append(f"\n선택 K = **{s['selected_k'][0]}** (원본 {s['selected_k'][1]}), M = **{s['selected_m'][0]}** (원본 {s['selected_m'][1]}), 실루엣 = **{s['silhouette'][0]}** (원본 {s['silhouette'][1]}).\n")
    md.append("원본 토픽 → 가장 가까운 재구성 토픽 (상위 10단어 겹침):\n")
    md.append("| 원본 토픽 | 원본 상위어 | 재구성 토픽 | 겹침 | 재구성 상위어 |\n|---|---|---|---|---|")
    for a in R["topic_alignment"]:
        md.append(f"| T{a['orig_topic']} | {', '.join(a['orig_words'])} | T{a['best_recon_topic']} | {a['overlap10']}/10 | {', '.join(a['recon_words'])} |")
    sc = R["scores"]
    md.append(f"\n점수 계층: loyalty_raw/spillover_raw {sc['loyalty_spillover_raw_match'][0]}/{sc['loyalty_spillover_raw_match'][1]} 일치(토크나이저와 무관한 산식이므로 당연히 같아야 함), "
              f"factor_diversity 상관 r = {sc['factor_diversity_pearson']:.3f} (평균 {sc['factor_diversity_mean'][0]} / {sc['factor_diversity_mean'][1]}), dominant_factor 라벨 일치 {sc['dominant_factor_label_match'][0]}/{sc['dominant_factor_label_match'][1]}.\n")

md.append(f"## {6 if R else 5}. 파일\n")
md.append("| 파일 | 내용 |\n|---|---|")
md.append("| `../../../../run_lda_v6_live_reference_v7.py` (저장소 루트) | 재구성본. `# === TOKENIZER BEGIN/END ===` 마커 사이가 토크나이저 절이며, 원본이 다른 스크립트에서 하던 대로 마커 기반 exec()로 가져다 쓸 수 있다 |")
md.append("| `verify_tokenizer_reconstruction_v7.py` | 검증 ①②: 제외 2건, 8개 버킷 통계·top-30 카운트, 자기인용 건수 → `tokenizer_reconstruction_check_v7.json` |")
md.append("| `compare_live_reference_refit_v7.py` | 검증 ③: 재적합 산출물을 원본 진단·점수 파일과 대조 → `live_reference_refit_comparison_v7.json` |")
md.append("| `build_tokenizer_reconstruction_md_v7.py` | 이 문서 생성 |\n")

md.append(f"## {7 if R else 6}. 한계\n")
md.append("1. 원본 소스가 아니다. 목표값 ①②에 맞춘 재구성이며, 원본 top-30 바깥의 저빈도 불용어는 확인 수단이 없다. 일본어 +15 토큰, 자기인용 895 vs 811 같은 잔차는 그 흔적이다.\n"
          "2. `language_of()`(14개 언어 도메인 허용목록)는 이 재구성 범위 밖이다. 저장소의 run_lda_v6.py 판(6개 언어)을 그대로 두었으므로 이 스크립트의 coverage_index·language 관련 열은 원본 14개 언어 값과 다르다. 점수 파일의 언어 열은 `fandom_scores_live_reference_v7.json`을 그대로 쓴다.\n"
          "3. wordfreq 기반 영어/비영어 재분류는 워드클라우드 버킷 분류에만 쓰인 사후 규칙이라 토크나이저 자체에는 없다(검증 스크립트에서만 재현).\n"
          "4. 동결 모델(K=10·M=5·0.267) 재적합은 이 토크나이저와 `data/v7_final/frozen_snapshot_v7_40/`의 근사 코퍼스(7,326/7,350)를 함께 써야 하며, 3개 팬덤 24건 유실과 위 잔차 때문에 '근방 재현'이 목표다.\n")
(HERE / "TOKENIZER_RECONSTRUCTION_V7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("wrote", HERE / "TOKENIZER_RECONSTRUCTION_V7.md")
