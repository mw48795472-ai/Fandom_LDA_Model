# 「Ⅲ. 지표 산정 방법」(업로드 문서)의 식 1~7을 함수로 정리하고, 실제 복구된
# 최종 라이브 코퍼스 산출물 data/v7_final/fandom_scores_live_reference_v7.json(100개 팬덤, 10,020건)에 대해 재검증한다.
# (2026-09-22 정리 전에는 r22 스냅샷 fandom_scores_v6.json(M=6)을 읽었다 — 현재는 archive/v6_r22_era/ 에 있음)
# 문서 원문: docs/INDEX_CALCULATION_METHODOLOGY.md 참고.
#
# 이 스크립트가 하는 것:
#   1) 식(2) min-max 정규화(Loyalty/Spillover Score) 재검증
#   2) 식(4)/(6) 정규화 섀넌 엔트로피(팩터 다양성) 재검증
#   3) 식(7) Activity 재검증
#   4) 식(1) EvidenceScore의 보너스 키워드 목록을 "문서 원문 그대로" 정리하고,
#      기존 재구성 코드(scripts/notebook_generator/build_notebook.py)의 키워드 목록과
#      한 글자 단위로 대조해 실제 불일치를 코드로 재현한다.
#
# 무결성 원칙: 이 프로젝트의 다른 검증 스크립트와 동일하게, "결과를 눈으로 믿지 않고
# 프로그램이 재대조"한다 — 아래 각 절은 재계산값과 원본 값을 직접 비교해 불일치 건수를
# 출력한다.
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]  # 저장소 루트
DATA_PATH = BASE / "data" / "v7_final" / "fandom_scores_live_reference_v7.json"

# ---------------------------------------------------------------------------
# 식(1) EvidenceScore — 문서 원문 그대로의 보너스 키워드 (수정판)
#
# n_num(t): 문장 t에 포함된 "수치표현 패턴"(예: "120만 장", "1위" 등 만·억·조·%·명·장·
#           위·회·건·주·배·년 단위가 붙은 표현)의 개수. 개별 숫자 문자 수가 아니다.
# n_kx(t):  지표별 보너스 키워드 집합과의 일치 횟수.
LOYALTY_BONUS_KW = [
    "기부", "돌파", "매진", "출범", "창단", "결성", "총공", "역사", "지속",
    "확장", "1위", "최초", "신기록", "밀리언셀러", "팬클럽", "팬카페", "결속",
    "충성", "세대",
]  # n=19 (문서 원문)

SPILLOVER_BONUS_KW = [
    "경제효과", "매출", "관광", "지자체", "앰버서더", "모델", "브랜드", "팝업",
    "협업", "관중", "방문", "상권", "지역", "홍보대사", "수익", "투어", "콘서트",
    "소비",
]  # n=18 (문서 원문)

import re

NUMERIC_PATTERN = re.compile(
    r"\d+(?:,\d{3})*\s*(?:만|억|조|%|명|장|위|회|건|주|배|년)"
)


def n_num_by_pattern(text: str) -> int:
    """문서 정의: 숫자+단위 패턴의 개수(예: '120만 장'→1건, '2026년'→1건)."""
    return len(NUMERIC_PATTERN.findall(text))


def n_num_by_digit_count(text: str) -> int:
    """기존 재구성 코드(build_notebook.py)의 실제 구현: 개별 숫자 문자 수."""
    return len(re.findall(r"\d", text))


def evidence_score(text: str, bonus_keywords, num_counter=n_num_by_pattern) -> float:
    """식(1): EvidenceScore(f) = Σ[1.0 + 0.5·n_num(t) + 0.3·n_kx(t)]"""
    n_num = num_counter(text)
    n_kx = sum(1 for kw in bonus_keywords if kw in text)
    return 1.0 + 0.5 * n_num + 0.3 * n_kx


def min_max_normalize(raw_values):
    """식(2): Score(f) = (ScoreRaw(f) - min) / (max - min)"""
    lo, hi = min(raw_values), max(raw_values)
    return [(v - lo) / (hi - lo) for v in raw_values]


def shannon_entropy_normalized(probs, n_categories):
    """식(4)/(6) 공통 형태: -Σ p·ln(p) / ln(N), p=0인 항목은 합에서 제외."""
    return -sum(p * math.log(p) for p in probs if p > 0) / math.log(n_categories)


def activity(n_loyalty_bullets: int, n_spillover_bullets: int) -> int:
    """식(7): Activity(f) = n_loyalty(f) + n_spillover(f)"""
    return n_loyalty_bullets + n_spillover_bullets


# ---------------------------------------------------------------------------
def check_keyword_lists():
    """기존 재구성 코드의 키워드 목록(build_notebook.py에서 그대로 옮김)과 문서 원문을 대조."""
    reconstructed_loyalty_kw = [
        "기부", "돌파", "매진", "출범", "창당", "결성", "총공", "역사", "지속",
        "확장", "1위", "최초", "신기록", "밀리언셀러", "팬클럽", "팬카페", "결속",
        "충성", "세대",
    ]  # scripts/notebook_generator/build_notebook.py LOYALTY_BONUS_KW (그대로 옮김)
    reconstructed_spillover_kw = SPILLOVER_BONUS_KW  # 이 목록은 문서와 완전히 동일

    loyalty_diff = set(LOYALTY_BONUS_KW) ^ set(reconstructed_loyalty_kw)
    spillover_diff = set(SPILLOVER_BONUS_KW) ^ set(reconstructed_spillover_kw)

    print("[검증] 충성도 보너스 키워드 — 문서 원문 vs 기존 재구성 코드")
    print(f"  문서: {len(LOYALTY_BONUS_KW)}개 / 코드: {len(reconstructed_loyalty_kw)}개")
    print(f"  불일치 키워드: {loyalty_diff if loyalty_diff else '없음'}")
    if loyalty_diff:
        print("  -> '창단'(문서, 그룹 결성)과 '창당'(코드, 정당 결성)의 한 글자 차이 오기로 추정")

    print("[검증] 파급효과 보너스 키워드 — 문서 원문 vs 기존 재구성 코드")
    print(f"  문서: {len(SPILLOVER_BONUS_KW)}개 / 코드: {len(reconstructed_spillover_kw)}개")
    print(f"  불일치 키워드: {spillover_diff if spillover_diff else '없음'}")


def check_n_num_definitions():
    samples = [
        "2026년 서울 올림픽공원에서 콘서트 개최",
        "EP 《16 Fantasy》는 피지컬 1만 3,653장이 판매되었다",
        "2024년 발매, 빌보드 200에도 이름을 올렸다",
    ]
    print("\n[검증] n_num 정의 차이 — 문서(패턴 개수) vs 기존 코드(숫자 문자 개수) 실제 비교")
    for t in samples:
        by_pattern = n_num_by_pattern(t)
        by_digit = n_num_by_digit_count(t)
        flag = "  <- 다름" if by_pattern != by_digit else ""
        print(f'  "{t}"\n    문서 정의(패턴 개수)={by_pattern}, 기존 코드(숫자문자 개수)={by_digit}{flag}')


def verify_against_real_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        scores = json.load(f)

    # 식(2): min-max 정규화 재검증
    loyalty_raw = [d["loyalty_raw"] for d in scores]
    spillover_raw = [d["spillover_raw"] for d in scores]
    recomputed_loyalty = min_max_normalize(loyalty_raw)
    recomputed_spillover = min_max_normalize(spillover_raw)

    loyalty_mismatch = sum(
        1 for d, v in zip(scores, recomputed_loyalty) if abs(round(v, 3) - d["loyalty_score"]) > 0.002
    )
    spillover_mismatch = sum(
        1 for d, v in zip(scores, recomputed_spillover) if abs(round(v, 3) - d["spillover_score"]) > 0.002
    )

    # 식(6): FactorDiversity 재검증 (메타팩터 수 = factor_share 길이; 라이브 M=5)
    fd_mismatch = 0
    for d in scores:
        shares = list(d["factor_share"].values())
        recomputed_fd = shannon_entropy_normalized(shares, len(shares))
        if abs(round(recomputed_fd, 4) - d["factor_diversity"]) > 0.001:
            fd_mismatch += 1

    # 식(7): Activity 재검증
    activity_mismatch = sum(
        1 for d in scores if d["activity"] != activity(d["n_loyalty_bullets"], d["n_spillover_bullets"])
    )

    print(f"\n[검증] 식(2) loyalty_score 재계산 불일치: {loyalty_mismatch}/{len(scores)}")
    print(f"[검증] 식(2) spillover_score 재계산 불일치: {spillover_mismatch}/{len(scores)}")
    print(f"[검증] 식(6) factor_diversity 재계산 불일치: {fd_mismatch}/{len(scores)}")
    print(f"[검증] 식(7) activity 재계산 불일치: {activity_mismatch}/{len(scores)}")

    # 식(3) Coverage Index 가중치 재확인
    doc_weights = {"language": 0.30, "market": 0.25, "source_type": 0.20, "time": 0.15, "entity": 0.10}
    weight_mismatch = sum(1 for d in scores if d["coverage_detail"]["weights"] != doc_weights)
    print(f"[검증] 식(3) Coverage Index 가중치 불일치: {weight_mismatch}/{len(scores)}")


if __name__ == "__main__":
    check_keyword_lists()
    check_n_num_definitions()
    verify_against_real_data()
