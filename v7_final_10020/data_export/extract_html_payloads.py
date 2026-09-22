# -*- coding: utf-8 -*-
"""
HTML 아티팩트 2종에 리터럴로 내장된 데이터 객체를 JSON 파일로 추출한다.

  3D_포지셔닝맵_국내100팬덤.html  -> data/v7_final/chart3d_payload_live_reference_v7.json
      (라이브 코퍼스 10,020건 기준 100개 팬덤 loyalty/spillover/diversity/coverage/activity/
       quadrant + 표본 평균(lmean/smean) + 4구획 카운트 + 라이브 재적합 진단값
       selected_k=8 / selected_m=5 / meta_factor_silhouette=0.046)
  Persona_결정공간.html            -> data/v7_final/persona_decision_space_v7.json
      (동결 스냅샷 v7-40(7,350건) 기준 K=10 토픽 명칭·F코드 배정·덴드로그램 병합 순서·
       PCA loading/좌표·팬덤별 F1~F5 비중·페르소나)

두 HTML은 최종 제출본과 함께 발행된 시각화 산출물이며, 원본 산출 JSON(예:
factor_clustering_structure_v7.json, chart3d payload)의 실제 값이 그 안에 그대로 들어 있다.
이 스크립트는 그 값을 "복사"만 하며 어떤 수치도 재계산·수정하지 않는다.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT_DIR = BASE / "data" / "v7_final"


def extract_object(html: str, anchor: str) -> dict:
    """`anchor` 문자열 이후 처음 나오는 중괄호 블록을 균형 괄호 기준으로 잘라 JSON 파싱."""
    i = html.find(anchor)
    if i < 0:
        raise ValueError(f"anchor not found: {anchor}")
    start = html.find("{", i)
    depth = 0
    in_str = False
    esc = False
    for k in range(start, len(html)):
        ch = html[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : k + 1])
    raise ValueError("unbalanced braces")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    html3d = (BASE / "3D_포지셔닝맵_국내100팬덤.html").read_text(encoding="utf-8")
    payload = extract_object(html3d, "payload")
    assert payload["n"] == 100 and len(payload["rows"]) == 100
    assert payload["corpus_total_evidence"] == 10020
    out1 = OUT_DIR / "chart3d_payload_live_reference_v7.json"
    out1.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[3D map] rows={len(payload['rows'])} corpus={payload['corpus_total_evidence']} "
          f"lmean={payload['lmean']} smean={payload['smean']} quadrants={payload['quadrant_counts']} "
          f"K={payload['selected_k']} M={payload['selected_m']} sil={payload['meta_factor_silhouette']}")
    print(f"  -> {out1.relative_to(BASE)}")

    html_p = (BASE / "Persona_결정공간.html").read_text(encoding="utf-8")
    data = extract_object(html_p, "const DATA")
    assert data["pca"]["K"] == 10 and data["pca"]["M"] == 5
    assert len(data["pca"]["fandoms"]) == 100
    out2 = OUT_DIR / "persona_decision_space_v7.json"
    out2.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[persona] K={data['dendro']['K']} M={data['dendro']['M']} sil={data['dendro']['silhouette']} "
          f"persona_counts={data['pca']['persona_counts']}")
    print(f"  -> {out2.relative_to(BASE)}")


if __name__ == "__main__":
    main()
