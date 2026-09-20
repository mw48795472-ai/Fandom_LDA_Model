// '2026년 문화체육관광 통계 활용대회' 요약보고서(1~2페이지, 공식 hwp 양식 필드 구조 복제) 빌드 스크립트.
// 원본 hwp 양식은 pyhwp(hwp5html)로 파싱해 필드 구조(팀명/세부주제/분석데이터/신한카드 여부/
// 분석도구/기획내용(자료분석·결론))를 확인한 뒤, docx-js로 동일한 표 레이아웃을 재현하고
// 최종 분석보고서(20페이지) 내용을 근거로 각 항목을 채웠다. 기획내용(자료분석·결론)은 사용자
// 요청에 따라 2페이지 분량까지 상세하게 확장한 최종본이다.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, VerticalAlign,
} = require("docx");

const TABLE_W = 9026; // A4 기준 콘텐츠 폭(DXA) — docx-js 기본 페이지 크기(A4)를 그대로 사용
const LABEL_W = 1500;
const VAL_W = TABLE_W - LABEL_W;
const FONT = "Malgun Gothic";

function cell(children, { width, shaded = false, valign = VerticalAlign.CENTER, span } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shaded ? { type: ShadingType.CLEAR, color: "auto", fill: "E9EEF5" } : undefined,
    verticalAlign: valign,
    columnSpan: span,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children,
  });
}

function p(text, { bold = false, size = 18, color, alignment } = {}) {
  return new Paragraph({
    alignment,
    spacing: { after: 40 },
    children: [new TextRun({ text, bold, size, color, font: FONT })],
  });
}

function multiP(lines, { size = 17, spacingAfter = 30 } = {}) {
  return lines.map(
    (line) =>
      new Paragraph({
        spacing: { after: spacingAfter },
        children: [new TextRun({ text: line, size, font: FONT })],
      })
  );
}

// 소제목(굵게, 강조색) + 본문을 한 문단에 붙여 쓰는 헬퍼 — 자료분석 3개 항목을 구조화하는 데 사용
function headBody(head, body, { size = 16, spacingAfter = 45, headColor = "1F4E79" } = {}) {
  return new Paragraph({
    spacing: { after: spacingAfter },
    children: [
      new TextRun({ text: head, bold: true, size, color: headColor, font: FONT }),
      new TextRun({ text: body, size, font: FONT }),
    ],
  });
}

function bullet(text, { size = 15, spacingAfter = 25, indent = 200 } = {}) {
  return new Paragraph({
    indent: { left: indent },
    spacing: { after: spacingAfter },
    children: [new TextRun({ text: "· " + text, size, font: FONT })],
  });
}

const labelCellOpts = { width: LABEL_W, shaded: true, bold: true };

const doc = new Document({
  sections: [
    {
      properties: { page: { margin: { top: 700, bottom: 700, left: 850, right: 850 } } },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "「2026년 문화체육관광 통계 활용대회」 요약 보고서", bold: true, size: 30, font: FONT })],
        }),

        new Table({
          width: { size: TABLE_W, type: WidthType.DXA },
          columnWidths: [LABEL_W, VAL_W],
          rows: [
            new TableRow({
              children: [
                cell([p("팀 명", { bold: true, size: 18 })], labelCellOpts),
                cell([p("데이터오름 (서목원 · 고려대학교 학부생 외)", { size: 18 })], { width: VAL_W }),
              ],
            }),
            new TableRow({
              children: [
                cell([p("세부 주제\n(제목)", { bold: true, size: 18 })], labelCellOpts),
                cell(
                  [
                    p("K-팬덤의 지역관광 파급효과 분석:", { size: 19, bold: true }),
                    p("팬덤의 온라인 관심과 공연이 지역 방문·소비에 미치는 영향", { size: 19, bold: true }),
                  ],
                  { width: VAL_W }
                ),
              ],
            }),
            new TableRow({
              children: [
                cell([p("분석 데이터\n필수 데이터\n(최소 1종 이상)\n국가승인통계명\n(직접 기재)", { bold: true, size: 16 })], labelCellOpts),
                cell(
                  multiP([
                    "① 한국관광데이터랩(문화체육관광부·한국관광공사) 지역관광 빅데이터",
                    "   — 일별·지역별 검색건수, 관광지출액, 방문자 수(시군구 단위, Raw-data)",
                    "② 「2025년 외래관광객조사」(문화체육관광부·한국관광공사, 국가승인통계)",
                  ], { size: 17 }),
                  { width: VAL_W }
                ),
              ],
            }),
            new TableRow({
              children: [
                cell([p("기타 활용\n데이터명", { bold: true, size: 16 })], labelCellOpts),
                cell(
                  multiP([
                    "100대 팬덤 다국어 근거문장 코퍼스(14개 언어권 704개 도메인, 근거문장 10,020건, LDA 토픽모델링용) ·",
                    "KPOPIS 공연통계 · 기상청 일강수량·평균기온 · KBO 경기일정(더미변수) ·",
                    "리센느 연계 지역 콘텐츠 유튜브 댓글 크롤링 데이터(6개 지역, 14,254건, TF-IDF 텍스트마이닝)",
                  ], { size: 16 }),
                  { width: VAL_W }
                ),
              ],
            }),
            new TableRow({
              children: [
                cell([p("신한카드 데이터\n활용 여부\n(■ 표시)", { bold: true, size: 16 })], labelCellOpts),
                cell(
                  [
                    p("■ 예   □ 아니오", { size: 18 }),
                    p("(한국관광데이터랩 관광지출액 지표에 포함된 카드소비 기반 데이터 — 팀 최종확인 권장)", { size: 13, color: "888888" }),
                  ],
                  { width: VAL_W }
                ),
              ],
            }),
            new TableRow({
              children: [
                cell([p("분석 도구", { bold: true, size: 18 })], labelCellOpts),
                cell([p("□ SPSS   □ SAS   ■ PYTHON   □ R   □ STATA   □ EXCEL   □ 기타(　　　)", { size: 17 })], { width: VAL_W }),
              ],
            }),
            // 기획 내용 - 자료분석 (2페이지 확장판, 최종 반영본)
            new TableRow({
              children: [
                cell([p("기획 내용\n\n자료분석", { bold: true, size: 18 })], labelCellOpts),
                cell(
                  [
                    headBody(
                      "① 국내 100대 팬덤 충성도×파급효과 유형 분석(LDA 토픽모델링). ",
                      "14개 언어권 704개 도메인에서 수집한 근거문장 10,020건을 LDA(K=10)로 토픽화한 뒤, 코사인거리 기반 계층적 재군집화로 5개 메타요인(F1 팬덤결속·F2 직접소비·F3 현장경제·F4 산업전이·F5 대중글로벌확산, silhouette=0.267)을 도출했다. 각 팬덤의 상위 2개 메타요인 조합으로 4개 페르소나(글로벌투어형43·현장상업형31·원정소비형17·집단동원형9)를 부여하고, 팬충성도×파급효과 2축으로 4구획(핵심전략형24·내부결속형17·외부견인형10·주변부49)을 산출했다. Shapiro-Wilk로 비정규성을 확인해 Pearson·Spearman을 병행(r=0.493·ρ=0.380, 모두 p<.001)했고, 다중회귀+VIF(R²=0.243→0.847, VIF=1.93)로 활동량 통제 시 충성도-파급효과가 트레이드오프 관계로 반전됨을 확인했으며, 4분면 독립성 카이제곱(χ²=8.34, p=0.0039)과 Cook's D(BTS 최댓값 0.575) 점검으로 구조의 통계적 유의성과 강건성을 검증했다. 이를 근거로 파급경로가 상이한 BTS(글로벌 벤치마크, 해외언어비중 60%)·임영웅(팬덤결속 1위, 지역다양성 0.71 최고)·리센느(지역밀착형, 경남 비중 58%)를 심층 대조 사례로 선정했다."
                    ),
                    headBody(
                      "② 리센느 홍보대사 위촉 지역 파급효과 분석(DID). ",
                      "거제·경주·수원 3개 사례를 동일한 이중차분법 파이프라인(log(Y)=β₀+β₁treat+β₂post+β₃(treat×post)+통제변수, Newey-West HAC 표준오차)으로 비교하고, HAC회귀·무작위추론(in-time placebo 1,000회)·플라시보-연도 검정 3중으로 강건성을 검증했다. 거제만 검색건수(+23.3%)·관광소비(+20.1%)·방문자수(+5.6%) 3개 지표가 모두 양(+)의 방향으로 일관됐고 무작위추론에서도 이례적 수준(p=0.016)으로 확인된 반면, 경주(p=0.770, 우연 수준)·수원(검색건수 -11.7%, p=0.008로 오히려 유의한 감소)은 그렇지 않았다. 리센느 연계 지역 콘텐츠 유튜브 댓글 14,254건을 TF-IDF로 텍스트마이닝한 결과, 거제·경주에서만 지역명과 멤버 출신지 서사가 동시에 최상위 호명되며 좋아요 반응의 90% 이상이 두 출신지 사례에 집중됐다. LDA 토픽 담론유형 분석에서도 방문·소비 담론은 거제·대전에서만 형성되어, 다채널 노출이 단일 이벤트보다 뚜렷한 신호를 남기며 관심이 방문으로 전환되려면 지역 호명을 넘어 구체적 소비 대상이 함께 제시되어야 함을 실증했다."
                    ),
                    headBody(
                      "③ 콘서트가 지역관광에 미치는 효과: BTS·임영웅 비교(DID). ",
                      "사전평행추세를 충족하는 통제군을 공연별로 개별 검증해 선정한 뒤, BTS(서울 종로구·고양 일산서구·부산 연제구)와 임영웅(대전 유성구·서울 구로구·부산 해운대구) 각 3개 지자체를 DID+Event Study로 비교했다. BTS는 고양 일산서구 외국인방문자수 +18.3%(p=0.002)·관광총소비 +7.3%, 부산 연제구 외국인방문자수 +43.0%(p<0.0001)·소비 +11.3%로 나타나 해외관광객 동원력과 공연 익일까지 이어지는 지연반응형 패턴을 보였다. 임영웅은 대전 유성구 관광소비 3일평균 +17.5%·공연 첫날 단독 +39.1%(p=0.007), 서울 구로구 방문자수 +11.2%·검색건수 +47.8%(모두 p<0.0001, 통제군을 재선정해도 결과가 오히려 강화), 부산 해운대구 방문자수 +6.7%(p=0.002)로, 공연 당일에 소비·방문이 집중되고 이후 빠르게 소멸하는 즉시소비형 패턴을 세 지역에서 일관되게 보였다. 두 아티스트 모두 콘서트의 지역관광 유의성은 공통이나, 팬덤 특성(글로벌 vs 국내 중장년층)에 따라 지역 확산의 시간적·공간적 메커니즘이 뚜렷이 대조됨을 확인했다."
                    ),
                  ],
                  { width: VAL_W }
                ),
              ],
            }),
            // 기획 내용 - 결론 (2페이지 확장판, 최종 반영본)
            new TableRow({
              children: [
                cell([p("결론", { bold: true, size: 18 })], labelCellOpts),
                cell(
                  [
                    headBody(
                      "정책 방향(투트랙 통합 모델). ",
                      "K-POP·미디어 콘텐츠를 독립적 관광목적이 아닌 '관심을 지역 방문·체류로 전환하는 매개수단'으로 재정의하고, 미디어 노출로 관심을 형성하는 Track A(지속형 지역관광: 지역연고+다채널 콘텐츠)와 콘서트로 방문을 유도하는 Track B(이벤트형 지역관광: 대형행사+팬덤별 관광 프로그램)를 병행할 것을 제안한다. 두 트랙은 집객→체류→재방문의 공통 퍼널로 통합되며, 체류 연장형·당일 집중형 프로그램과 후속 콘텐츠·팬커뮤니티·지역축제 연계로 지속적 관광수요를 형성하는 것을 목표로 한다."
                    ),
                    headBody(
                      "지역별 특화업종 매칭(LQ·엔트로피극대화지수). ",
                      "고양·부산·거제·경주 4개 지역의 업종별 LQ지수와 엔트로피극대화지수 분석 결과를 바탕으로, 고양은 공연수요를 숙박·당일관광 전환으로, 거제는 지역연고 콘텐츠를 식당·체험시설과 결합해, 경주는 레저·숙박 수요를 지역상점·쇼핑 분야 확산으로 연결할 것을 제안한다. 특화 업종은 관광수요의 진입점으로, 상대적으로 소비가 취약한 업종은 확산 대상으로 삼아 관광소비가 특정 지점에 머물지 않고 주변 상권으로 퍼지도록 유도한다."
                    ),
                    headBody(
                      "페르소나 4유형별 맞춤 관광상품. ",
                      "LDA 기반 4개 페르소나 유형에 팬덤 100개 분석에서 도출한 소비 특성을 매칭해, 글로벌투어형에는 체류연장형 상품을, 현장상업형에는 특산품·굿즈 협업을, 원정소비형에는 직접소비 프로그램을, 집단동원형에는 단체이동·재방문 프로그램을 우선 검토하도록 제안한다."
                    ),
                    headBody("기대효과. ", ""),
                    bullet("지역관광 전환성과의 구체화 — 검색량·방문객수뿐 아니라 예약률·체류시간·숙박률까지 종합 활용해 콘텐츠 관심이 실제 방문·체류로 이어졌는지 평가."),
                    bullet("관광소비의 지역 내 확산 확인 — 엔트로피·LQ로 식별한 지역별 특화업종을 진입점으로 삼아 콘서트·관광지 소비가 주변 상권으로 확산되는지 추이 분석."),
                    bullet("우선순위 지원을 통한 정책 효율성 개선 — 이용 실적이 낮은 일회성 사업의 반복 지원을 축소."),
                    bullet("관광수요의 지속효과 기대 — 단발성 이벤트(올림픽 유치·엑스포 유치 등)를 넘어 재방문율을 높이고 파급효과의 지속가능성을 실증 데이터로 재검증."),
                  ],
                  { width: VAL_W }
                ),
              ],
            }),
          ],
        }),

        new Paragraph({
          spacing: { before: 150 },
          children: [
            new TextRun({
              text: "* 자료분석은 기존 통계보고서 현황자료 인용이 아닌, 필수자료(Raw-data) 1종을 포함한 총 2종 이상 자료를 분석 도구로 직접 분석한 과정·결과임.",
              size: 13, italics: true, color: "666666", font: FONT,
            }),
          ],
        }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/home/claude/work/output/요약보고서_2026_문화체육관광통계활용대회.docx", buf);
  console.log("done", buf.length);
});
