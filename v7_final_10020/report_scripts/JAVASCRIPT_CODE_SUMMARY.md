# 이 프로젝트에 적용된 자바스크립트(Node.js + 브라우저 인라인 JS) 총정리

`v7_final_10020/docs/PYTHON_CODE_SUMMARY.md`(파이썬 총정리)의 짝이 되는 문서다. 이 프로젝트에서 JavaScript가
쓰인 곳은 딱 두 갈래뿐이다 — ① 워드 문서를 빌드하는 Node.js 스크립트 1개(이 폴더
`v7_final_10020/report_scripts/`), ② 결과를 브라우저에서 보여주는 시각화 산출물 3종에 들어있는 인라인
`<script>` 코드(자기완결형 정적 HTML — 이 중 2종은 저장소 루트에 있다). HTML 2종에 내장된 데이터
객체는 `v7_final_10020/data_export/extract_html_payloads.py`로 `data/v7_final/*.json`에 추출해 두었다
(3D 맵 payload: 최종 코퍼스 10,020건 점수·4구획; Persona: 동결 스냅샷 K=10 구조). 두 HTML을 가리키는
QR 코드는 `qr_codes/`에 있다.
**Java 언어는 이 프로젝트 어디에도 쓰이지 않았다** — 아래는 전부 JavaScript다.

## 한눈에 보기

| 구분 | 파일 | 실행 환경 | 무엇을 만드는가 |
|---|---|---|---|
| Node.js 스크립트(저장소 내) | `v7_final_10020/report_scripts/build_summary_report_2026_contest.js` | Node.js + `docx`(npm) | 「2026년 문화체육관광 통계 활용대회」 요약보고서 1∼2페이지를 `.docx`로 빌드 |
| 브라우저 인라인 JS | `팬덤루트랩_상세명세서.html` (서비스 상세명세서, 저장소 미포함) | — | **JS 없음** — 순수 정적 HTML/CSS (검증 결과, `<script>` 태그 0개) |
| 브라우저 인라인 JS | `Persona_결정공간.html` (페르소나 결정공간, 저장소 루트) | 브라우저(외부 라이브러리 없음) | 덴드로그램 + PCA 산점도 + 레이더 상세패널, 전부 순수 SVG DOM 조작으로 직접 구현 |
| 브라우저 인라인 JS + 번들 라이브러리 | `3D_포지셔닝맵_국내100팬덤.html` + `plotly-bundle.js` (둘 다 저장소 루트) | 브라우저 + Plotly.js v3.7.0(로컬 번들, 1.69MB) | 100개 팬덤 3D 산점도(충성도×파급효과×다양성), 구획색/하이라이트/버블크기 토글 + 카메라 프리셋 |

세 HTML 산출물은 파이썬 파이프라인의 산출 데이터를 리터럴로 내장해 발행한 정적 파일이며, 아래 정리는
그 안에 들어있는 JS를 읽고 구조를 분석한 결과다.

---

## A. Node.js 스크립트 — `build_summary_report_2026_contest.js`

파일 맨 위 주석이 밝히는 제작 과정: 원본 hwp 양식을 `pyhwp`(hwp5html)로 파싱해 필드 구조
(팀명/세부주제/분석데이터/신한카드 여부/분석도구/기획내용)를 확인한 뒤, `docx`(npm 패키지,
docx-js)로 같은 표 레이아웃을 재현하고 최종 분석보고서(20페이지) 내용을 근거로 각 항목을
채웠다. 재현 절차는 `npm install docx` → `node v7_final_10020/report_scripts/build_summary_report_2026_contest.js`
두 줄이다. 저장소에 `package.json`은 없고(전역 설치해 1회성 실행), 실행하면 저장소 루트의
`output/요약보고서_2026_문화체육관광통계활용대회.docx`를 쓴다.

구조(약 220줄):

1. **헬퍼 함수 5개** — `cell()`(표 셀, 배경색·정렬·columnSpan), `p()`(단락), `multiP()`
   (여러 줄 단락 배열), `headBody()`(굵은 소제목 + 본문을 한 문단에 이어 쓰는 헬퍼 — "자료분석"
   3개 항목을 구조화하는 데 사용), `bullet()`(글머리 기호 단락).
2. **`Document` 트리 1개** — A4 여백(top/bottom 700, left/right 850 DXA) 섹션 안에 제목 단락 +
   표 1개(`TABLE_W=9026` DXA, `LABEL_W=1500`/`VAL_W` 2열)를 중첩. 표 행은 팀명 → 세부주제 →
   분석데이터(필수/기타) → 신한카드 데이터 활용 여부 → 분석도구 → **기획내용(자료분석 3항목,
   `headBody`로 구조화 — ①LDA 토픽모델링 팬덤분석 ②리센느 DID ③BTS·임영웅 콘서트 DID 비교)**
   → **결론(정책방향·업종매칭·페르소나별 상품·기대효과 4개 불릿)** 순.
3. **`Packer.toBuffer(doc).then(...)`** — 빌드된 문서를 버퍼로 직렬화해 파일로 씀, 콘솔에
   `"done", buf.length` 출력.

docx-js의 일반적인 관례를 그대로 따른다: 표 너비를 DXA로 셀·테이블 양쪽에 명시, `\n` 대신 별도 `Paragraph`를 쓰지 않고 텍스트
내부 줄바꿈이 필요한 라벨(예: "세부 주제\n(제목)")은 `TextRun`의 `text`에 `\n`을 직접 넣는
방식(docx-js는 `TextRun.text` 안의 `\n`을 줄바꿈으로 렌더링하지 않으므로, 실제로는 `break: true`
런을 추가하지 않는 한 한 줄로 붙어 나올 수 있다 — 이 스크립트가 그 처리를 하지 않은 채 `\n`을
문자열에 포함시킨 부분은 렌더링 시 확인이 필요한 지점으로 남아있다).

## B. 브라우저 인라인 JS — 3개 시각화 산출물

세 파일 모두 **단일 HTML 파일**로 완결되며(CSS는 인라인, 데이터는 JS 안에 리터럴로 내장), 서버나
빌드 과정 없이 그냥 열면 동작한다(3D 맵만 같은 폴더의 `plotly-bundle.js`가 필요).

### B-1. `팬덤루트랩_상세명세서.html` — JS 전혀 없음

`<script`, `onclick`, `addEventListener` 문자열을 전부 검색해도 0건이다. 즉 이 파일은
**순수 정적 HTML + CSS 문서**(서비스/API 설계 상세명세서)이며, 표·다이어그램 등도 전부 HTML
태그와 CSS만으로 구성되어 있다. 세 산출물 중 유일하게 "인라인 JS"라 부를 코드가 아예 없는
경우라, 위 표에도 그 사실 자체를 명시해 두었다.

### B-2. `Persona_결정공간.html` — 순수 SVG 인라인 구현 (외부 라이브러리 없음)

`<script>` 블록 1개, 총 약 29,500자. 앞부분은 `const DATA = {...}`로 PCA 결과·덴드로그램
구조·팬덤별 좌표를 통째로 리터럴 JSON으로 내장하고, 그 뒤에 실제 렌더링 로직이 세 구획으로
나뉘어 있다(코드 주석 자체가 `/* 1) Dendrogram */`, `/* 2) PCA scatter */`, `/* 3) Detail panel
(radar) */`로 구획을 명시).

1. **덴드로그램** (`buildDendro()` IIFE) — `document.createElementNS`로 SVG `<line>`/`<path>`/
   `<text>`를 직접 생성하는 `el()` 헬퍼만으로 좌표 변환(`X()`/`Y()`)과 병합 트리 그리기를
   전부 손으로 구현. 가지 색은 `colorForNode()`가 그 가지 밑 리프들이 전부 같은 F코드를
   공유하는지 검사해 결정(공유하면 해당 F코드 색, 섞이면 중립색) — 이는 파이썬 차트 스크립트
   (`build_persona_cluster_split_boxed.py`)의 `link_color_func`와 같은 규칙을 브라우저용으로
   재구현한 것.
2. **PCA 산점도** (`buildLegend()` IIFE + 관련 함수들) — 페르소나 4종을 범례 칩으로 만들어
   클릭 시 `activePersonas` Set을 토글해 `applyFilter()`로 해당 페르소나 점들을 숨김/흐림
   처리. 축 격자·눈금·F1∼F5 loading 화살표(`drawScatterChrome()`)와 100개 팬덤 점(모양은
   페르소나별 원/삼각형/사각형/마름모, `shapePath()`)을 전부 SVG로 그리고, 각 점에
   `mouseenter`/`mousemove`/`mouseleave`/`focus`/`click` 5개 이벤트를 걸어 툴팁 표시
   (`showTooltip`/`positionTooltip`/`hideTooltip`)와 상세패널 갱신, 클릭 시 고정(pin) 토글을
   구현. 검색창(`#search`) 입력에도 `applyFilter()`가 연결되어 이름 검색 시 매칭 안 되는
   점을 흐리게 처리.
3. **상세 레이더 패널** (`showDetail(f)`) — 선택된 팬덤의 F1∼F5 `shares`를 5각 레이더 차트로
   그리고(격자 4겹 + 100개 팬덤 평균 다각형 + 선택 팬덤 값 다각형을 겹쳐 표시), 옆에 수치
   표(`#d-table`)도 함께 갱신.

다크모드 대응 헬퍼(`isDark()`, `cssVar()`)가 최상단에 있어 `document.documentElement`의
`data-theme` 속성이나 OS 설정(`prefers-color-scheme`)에 따라 배색을 CSS 변수(`var(--p-...)`)
로 읽어오는 구조다.

### B-3. `3D_포지셔닝맵_국내100팬덤.html` + `plotly-bundle.js` — Plotly.js 기반

`<script src="plotly-bundle.js">`로 **Plotly.js v3.7.0**(gl3d 빌드, 압축본 1.69MB, MIT
라이선스, 2026년판)을 로컬 파일로 함께 번들링해 오프라인에서도 동작하게 했고, 그 아래 두 번째
인라인 `<script>`(약 37,500자)가 실제 로직이다. 이쪽은 라이브러리(Plotly)에 그리기를 맡기고,
이 프로젝트가 직접 짠 코드는 **데이터 가공과 UI 상태 관리**에 집중된다.

- `const payload = {"rows": [...]}` — 100개 팬덤의 `loyalty`(팬충성도)·`spillover`(파급효과)·
  `diversity`(다양성 Z점수)·`coverage`(Coverage Index)·`quadrant`(4구획)·`activity`(근거문장
  수) 등을 리터럴로 내장.
- `interp()`/`hexToRgb()` — 팬덤특성분산성(diversity_t, 0∼1 정규화값)에 따라 구획별 5단계
  팔레트를 선형보간해 마커 색을 정하는 자체 색상 보간 함수(외부 색상 라이브러리 없이 hex를
  RGB로 쪼개 채널별로 보간).
- `bubbleSize()` — 근거자료 수(activity)를 반지름에 매핑할 때 **면적이 값에 비례**하도록
  `sqrt` 정규화(지각적으로 정확한 버블 크기 — 값을 반지름에 선형 매핑하면 면적 차이가
  과장되는 흔한 실수를 피함).
- `buildTraces()` — 현재 `state`(구획 표시 on/off, 하이라이트 on/off, 버블크기 on/off) 3개
  불리언에 따라 Plotly `scatter3d` trace 배열을 다시 구성. 구획 표시가 켜져 있으면 4구획별로
  trace를 나눠 범례에서 개별 토글 가능하게 하고, 꺼져 있으면 전체를 단일 trace로 합침.
- `redraw()` → `Plotly.react('plot', ...)` — DOM을 통째로 새로 만들지 않고 기존 plot을
  갱신(`newPlot`보다 가벼운 갱신 방식).
- `setCamera()` → `Plotly.relayout('plot', {'scene.camera': ...})` — 기본/위(top)/옆(side)
  3개 카메라 프리셋 버튼(`btn-default`/`btn-top`/`btn-side`)에 `eye`/`up` 좌표를 미리 정의해
  연결.
- `bindOption()` — 옵션 버튼 3개(4구획 색상/임영웅·BTS·리센느 강조/버블 크기)를 각각
  `state` 키에 연결해 클릭할 때마다 `redraw()` 호출, 버튼 라벨 앞에 체크마크(✓)를 붙였다 뗐다
  하는 것도 이 함수 하나로 통일 처리.
- `hoverTmpl()`/`customdataFor()` — Plotly의 `hovertemplate` 문법(`%{customdata[n]}`)으로
  구획·카테고리·팬충성도·파급효과·Coverage Index·근거자료 수까지 한 번에 보여주는 툴팁 구성.

## 공통적으로 쓰인 패턴

- **데이터-코드 분리 없음(의도적)**: 세 산출물 모두 별도 API 호출이나 외부 데이터 파일 로드
  없이, 산출 시점의 데이터를 `const DATA = {...}` / `const payload = {...}`로 스크립트 안에
  그대로 굳혀 넣었다 — 외부 호스트 없이 파일 하나로 열리는 자기완결형 HTML을 만들기 위한 선택이다. 즉 데이터를 갱신하려면 원본 파이썬 파이프라인을
  다시 돌려 이 리터럴 자체를 재생성해야 한다.
- **외부 라이브러리는 최소한만**: 4개 산출물(1 Node 스크립트 + 3 HTML) 중 외부 라이브러리를
  쓰는 것은 `3D_포지셔닝맵`(Plotly.js)과 Node 스크립트(`docx` npm 패키지) 둘뿐이고, 정적
  명세서는 라이브러리는커녕 JS 자체가 없으며, 페르소나 결정공간은 라이브러리 없이 SVG DOM
  API만으로 차트 3종을 직접 구현했다 — 표현 방식의 복잡도가 파일마다 다르게 선택된 것.
- **라이트/다크 테마 이중 대응**: `Persona_결정공간.html`의 `isDark()`/`cssVar()`처럼, CSS
  커스텀 프로퍼티(`var(--...)`)로 색을 참조하고 `data-theme` 속성 또는
  `prefers-color-scheme` 미디어쿼리로 두 테마 모두를 명시적으로 정의하는 패턴이 쓰였다.
- **Java 언어는 없음**: 위 A·B 전체를 통틀어 `.java` 파일이나 JVM 기반 코드는 전혀 없다 —
  Python(분석 파이프라인)·JavaScript(Node 리포트 빌더 + 브라우저 시각화)·HTML/CSS(문서·레이아웃)
  세 가지가 이 프로젝트의 전부다.
