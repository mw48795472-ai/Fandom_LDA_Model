# qr_codes — 인터랙티브 HTML 2종 QR 코드

보고서에 실린 QR 코드 원본 이미지. 각 QR은 claude.ai에 게시된 아티팩트를 가리키며, 그 아티팩트의 `index.html`은 저장소 루트의 HTML 파일과
**SHA-256이 동일**하다(2026-09-22 점검, 헤드리스 Chromium 렌더링으로 오류 없음 확인).

| QR 이미지 | 링크 | 저장소 파일 | 내용 |
|---|---|---|---|
| `QR_Persona_결정공간.png` | https://claude.ai/code/artifact/654cb2c0-3558-4856-b92a-8a3f35dc9876 | `Persona_결정공간.html` | 동결 스냅샷(7,350건) K=10→M=5 덴드로그램 · PCA 투영(100팬덤) · 레이더 |
| `QR_3D_포지셔닝맵.png` | https://claude.ai/code/artifact/f23c02c5-8586-4265-bcf7-8e333b117b26 | `3D_포지셔닝맵_국내100팬덤.html` + `plotly-bundle.js` | 라이브 10,020건 충성도×파급효과×요인다양성 3D 맵, 4구획 24/17/10/49 |

- 3D 맵 아티팩트에는 `plotly-bundle.js`(1,690,770바이트)가 함께 게시돼 있고 저장소의 파일과 해시가 같다.
- 두 HTML의 내장 데이터는 각각 `data/v7_final/persona_decision_space_v7.json`, `data/v7_final/chart3d_payload_live_reference_v7.json`과 동일하다(`verify_v7_final_consistency.py` [G]·[C]).
- 로컬에서 열 때는 3D 맵 HTML과 `plotly-bundle.js`를 같은 폴더에 두어야 한다. Persona HTML은 Google Fonts를 불러오며 오프라인이면 기본 글꼴로 표시된다.
