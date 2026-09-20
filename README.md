# data/ — 재업로드 필요

이 폴더는 의도적으로 비어 있습니다. 원본 분석 데이터 JSON 파일들은 클라우드 샌드박스가 회수되며 함께
유실되었습니다. `scripts/` 아래 스크립트들을 실제로 실행하려면 아래 파일들을 이 폴더에 다시 넣어야 합니다.

| 파일명 | 사용하는 스크립트 |
|---|---|
| `fandom_cohesion_index_v7.json` | `scripts/charts/build_cohesion_index_v7.py`, `build_cohesion_index_v7_right_only.py` |
| `factor_clustering_structure_v7.json` | `scripts/charts/build_persona_cluster_split_boxed.py` |
| `fan_persona_v7.json` | `scripts/charts/build_persona_cluster_split_boxed.py` |
| `domestic_regional_index_live_reference_v7.json` | `scripts/indices_csv/build_domestic_regional_index_csv.py` |
| `worldwide_language_index_live_reference_v7.json` | `scripts/indices_csv/build_worldwide_language_index_csv.py` |
| `ad_commercial_index_v7.json` | `scripts/indices_csv/build_ad_commercial_index_csv.py` |
| `NotoSansCJKkr-Regular.otf` (폰트, `charts/` 폴더에 위치) | 모든 차트 스크립트 |

이 파일들이 원래 있던 팀 작업 환경(다른 팀원 PC, 클라우드 스토리지, 이전 세션에서 다운로드한 사본 등)에
남아있는지 확인해 주세요. 찾으면 이 폴더에 넣고 다시 커밋하면 스크립트가 그대로 동작합니다.
