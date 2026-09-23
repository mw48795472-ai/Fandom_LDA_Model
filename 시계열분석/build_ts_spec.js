const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, ShadingType, LevelFormat, PageNumber,
  Footer, Header, TabStopType, PageBreak,
} = require("docx");

const FONT = "Malgun Gothic";
const INK = "1F1F1F";
const MUTED = "5B5B5B";
const ACCENT = "1F4E79";
const HEAD_BG = "DCE6F1";
const ZEBRA = "F5F7FA";
const CONTENT_W = 9638; // A4 11906 - 2*1134

function run(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: opts.size || 20, bold: opts.bold, italics: opts.italics, color: opts.color || INK });
}
function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [run(text, opts)];
  return new Paragraph({ children: runs, spacing: { after: opts.after ?? 120, line: 300 }, alignment: opts.align, indent: opts.indent });
}
function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT, size: 30, bold: true, color: ACCENT })], spacing: { before: 360, after: 160 } }); }
function h2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT, size: 24, bold: true, color: ACCENT })], spacing: { before: 280, after: 120 } }); }
function h3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT, size: 21, bold: true, color: INK })], spacing: { before: 200, after: 80 } }); }
function bullet(text, level = 0) {
  const runs = Array.isArray(text) ? text : [run(text)];
  return new Paragraph({ children: runs, numbering: { reference: "bullets", level }, spacing: { after: 60, line: 300 } });
}
function numbered(text, ref = "nums") {
  const runs = Array.isArray(text) ? text : [run(text)];
  return new Paragraph({ children: runs, numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 300 } });
}
function label(k, v) { return p([run(k + "  ", { bold: true, color: ACCENT }), run(v)]); }

const thin = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: thin, bottom: thin, left: thin, right: thin, insideHorizontal: thin, insideVertical: thin };

function cell(text, width, opts = {}) {
  const lines = Array.isArray(text) ? text : [text];
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    verticalAlign: "center",
    children: lines.map((t) => new Paragraph({ children: [run(t, { size: opts.size || 18, bold: opts.bold, color: opts.color })], spacing: { after: 40, line: 260 }, alignment: opts.align })),
  });
}
function table(headers, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  if (total !== CONTENT_W) throw new Error("widths sum " + total);
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { fill: HEAD_BG, bold: true, size: opts.size })) });
  const body = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => cell(c, widths[i], { fill: ri % 2 ? ZEBRA : undefined, size: opts.size })) }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, borders, rows: [head, ...body] });
}
function spacer() { return new Paragraph({ children: [], spacing: { after: 80 } }); }
// 시계열 패널 분석 상세명세서 — output/summary_v7.json 에서 수치를 읽어 채운다. usage: node build_ts_spec.js <repo>/시계열분석 <out.docx>
const REPO_TS = process.argv[2]; const OUTP = process.argv[3];
const S = JSON.parse(fs.readFileSync(REPO_TS + "/output/summary_v7.json", "utf8"));
const A = S.A_time_tags, B = S.B_panel, C = S.C_factor_by_year, E = S.E_collection_bias, R = S.regressions, YS = S.year_summary, SET = S.settings;
const pct = (x) => (x * 100).toFixed(1) + "%"; const f4 = (x) => (typeof x === "number" ? x.toFixed(4) : String(x)); const n = (x) => Number(x).toLocaleString("en-US");
const children = [];
children.push(new Paragraph({ children: [new TextRun({ text: "시계열 패널 분석 상세명세서", font: FONT, size: 34, bold: true, color: ACCENT })], spacing: { after: 100 } }));
children.push(new Paragraph({ children: [run("근거문장의 시점 태그로 만든 팬덤×연도 패널 — 데이터·규칙·산식·검증·산출물 (2026-09-23, 폴더 시계열분석/)", { size: 20, color: MUTED })], spacing: { after: 360 } }));

children.push(h1("1. 범위와 위치"));
children.push(p("이 분석은 루트 README의 본 분석과 별개의 탐색 분석이다. 해석 계층(K→F→페르소나), 팬충성도·파급효과 점수 정의, 보조지표, 순위표는 손대지 않는다. 근거문장 10,020건 각각에 사건 연도를 붙이고, 같은 EvidenceScore 산식을 연도별로 다시 세어 팬덤×연도 패널을 만든 뒤 그 위에서 추세·횡단면 관계·고정효과·경로 비중 추이를 본다. 모든 코드와 산출물은 폴더 시계열분석/ 안에 있고, 저장소의 다른 파일을 쓰지 않는다."));
children.push(table(["구분", "내용"], [
  ["입력 (읽기만)", "data/v7_final/bullets_flat_v7_final.csv(문장·URL), bullet_provenance_v7.csv(수집 라운드), fandom_scores_live_reference_v7.json(raw 점수·factor_share), lda_v6_diagnostics_live_reference_v7.json(토픽→요인), fan_persona_v7.json(페르소나 정의), factor_pathway_map_v7.json(요인→F), v7_final_10020/index_methodology/evidence_score_by_sentence_v7.csv(문장 점수), topic_phi_cosine/{lda_model_k8_v7_final.pkl, count_vectorizer_v7_final.pkl, topic_alignment_v7.csv}, run_lda_v6.py(토크나이저)"],
  ["코드", "timeseries_panel_v7.py(전체 파이프라인), build_timeseries_notebook_v7.py → 시계열_패널분석_v7.ipynb(실행 결과 포함), R/(RUN_ALL.R + 01∼03, base R)"],
  ["산출물", "output/ CSV 8개 · summary_v7.json · PNG 4장, 시계열_패널분석_V7.md(결과 문서), 이 명세서"],
  ["실행", "python 시계열분석/timeseries_panel_v7.py (약 6초) → python 시계열분석/build_timeseries_notebook_v7.py (약 1분) → Rscript 시계열분석/R/RUN_ALL.R (선택; 이 환경에는 R이 없어 실행하지 않았다)"],
], [1800, 7838], { size: 17 }));

children.push(h1("2. A. 문장 시점 태깅"));
children.push(p("문장마다 사건 연도(event_year)와 근거(year_source)를 정한다. 코퍼스 JSON은 바꾸지 않고 사이드카 CSV(output/sentence_time_tags_v7.csv, 10,020행)로 둔다."));
children.push(table(["단계", "규칙", "비고"], [
  ["① 본문 연도", "정규식 (?<!\\d)(20[0-2]\\d)(?!\\d) 로 2000∼2026 연도를 모두 뽑고, 여럿이면 가장 늦은 연도를 event_year로 (year_source = text)", "회고 서술('2013년 데뷔 이래')은 이른 연도가 되므로 늦은 연도 채택이 사건 연도에 가깝다는 가정"],
  ["② URL 날짜", "URL 경로의 (20[12]\\d)[/-.]?(MM)[/-.]?(DD)? 패턴 → url_date, url_year", "매체마다 규칙이 달라 일부만 잡힘"],
  ["③ 상대 표현", "본문 연도가 없고 URL 연도가 있을 때: '올해·이달·최근·현재' → url_year, '지난해·작년·전년' → url_year−1, '내년' → +1, '재작년' → −2 (year_source = relative)", "URL 날짜가 없으면 해석 불가"],
  ["④ URL만", "본문 연도·상대 표현이 없고 URL 연도만 있으면 그 연도 (year_source = url)", "발행 연도 ≈ 사건 연도 가정"],
  ["⑤ 없음", "어느 것도 없으면 event_year 비움 (year_source = none)", "패널에서 제외, 검증에서는 '연도 미상'으로 합산"],
  ["범위", "패널은 2015∼2026년(12개 연도)만 사용. 2015년 이전 연도는 태그는 남기되 패널에서 제외", "Coverage Index의 연도 분모 12와 같은 범위"],
], [1500, 5300, 2838], { size: 17 }));
children.push(spacer());
children.push(table(["항목", "값"], [
  ["문장 수", n(A.n)], ["시점 태그", `${n(A.tagged)} (${pct(A.tagged_share)}) — text ${n(A.by_source.text || 0)} · url ${n(A.by_source.url || 0)} · relative ${n(A.by_source.relative || 0)} · none ${n(A.by_source.none || 0)}`],
  ["2015∼2026 범위 안", `${n(A.in_range_2015_2026)} (2015년 이전 ${n(A.before_2015)})`], ["복수 연도 문장", n(A.multi_year_sentences)],
  ["본문 연도 vs URL 연도 (둘 다 있는 문장)", `${n(A.text_url_both)}건 중 같은 해 ${n(A.text_url_same_year)} (${pct(A.text_url_same_year / A.text_url_both)}), ±1년 ${n(A.text_url_within_1y)} (${pct(A.text_url_within_1y / A.text_url_both)})`],
  ["연도별 문장 수", Object.entries(A.event_year_dist).map(([y, v]) => `${y} ${n(v)}`).join(" · ")],
], [3200, 6438], { size: 17 }));
children.push(p("검증: 본문 연도와 URL 연도가 모두 있는 문장에서 두 연도의 일치율이 태깅 규칙의 정확도 하한이다. 사람 판정 표본 검증(제안서의 ≥0.9 기준)은 아직 하지 않았다.", { size: 18, color: MUTED }));

children.push(h1("3. B. 팬덤×연도 패널"));
children.push(p("칸 = (팬덤, event_year). 같은 순서의 문장 점수 CSV(evidence_score_by_sentence_v7.csv)에서 EvidenceScore를 가져와 칸별로 더한다."));
children.push(table(["변수", "정의"], [
  ["n_loyalty, n_spillover, n_total", "칸에 든 충성도·파급효과 문장 수와 합"],
  ["loyalty_sum, spillover_sum (규모)", "칸의 EvidenceScore 합 = Σ_t [1 + 0.5·n_num(t) + 0.3·n_kw(t)] — 본 분석의 raw 점수를 연도로 나눈 것"],
  ["loyalty_density, spillover_density (밀도)", "합 ÷ 문장 수. 축별 문장이 " + SET.min_axis + "개 미만이면 결측"],
  ["year_share", "n_total ÷ 그해 코퍼스 전체 시점 태그 문장 수 (수집 편향 보정용 점유율)"],
  ["late_round_share", "칸 문장 중 후기 추가분(r41∼r72 및 교체 진입) 비율"],
  ["valid_cell", "n_total ≥ " + SET.min_cell + " 이면 1. 통계는 유효 칸만 쓴다"],
], [3200, 6438], { size: 17 }));
children.push(spacer());
children.push(table(["항목", "값"], [
  ["칸 / 유효 칸", `${n(B.n_cells)} / ${n(B.n_valid_cells)}`], ["유효 연도 3개 이상 / 5개 이상 팬덤", `${B.fandoms_ge3_valid_years} / ${B.fandoms_ge5_valid_years}`],
  ["유효 연도 3개 미만(추세 제외) 팬덤", B.fandoms_excluded_lt3.join(", ") || "없음"],
  ["재현 검증", `연도별 합 + 연도 미상 문장 합 = 현재 loyalty_raw·spillover_raw: ${B.raw_score_reconciliation} (오차 1e-6)`],
  ["그림 1 대상(상위 8, 유효 연도 3개 이상)", B.top8.join(" · ")],
], [3200, 6438], { size: 17 }));

children.push(h1("4. 통계"));
children.push(h2("4-1. 연도별 횡단면 상관"));
children.push(p("그해 유효 칸이 있고 두 밀도가 모두 있는 팬덤이 " + SET.min_fandoms_year + "개 이상인 연도에서, 팬덤들 사이의 Pearson r·Spearman ρ(밀도)와 Pearson r(합)을 구한다. 본 분석의 판별타당도 검정(|r|<0.5)을 연도별로 다시 본 것이다."));
const yv = YS.filter((r) => r.r_density !== "");
children.push(table(["연도", "문장", "유효 팬덤", "평균 충성도 밀도", "평균 파급효과 밀도", "r(밀도)", "p", "ρ(밀도)", "r(합)"], yv.map((r) => [String(r.year), n(r.n_sentences), String(r.n_fandoms_valid), f4(r.mean_loyalty_density), f4(r.mean_spillover_density), f4(r.r_density), f4(r.p_density), f4(r.rho_density), f4(r.r_sum)]), [900, 1000, 1000, 1400, 1400, 1000, 900, 1000, 1038], { size: 16 }));
children.push(h2("4-2. 팬덤별 추세"));
children.push(p(`유효 연도 ${SET.min_cells_trend}개 이상인 팬덤에서 연도와 (규모 n_total, 충성도 밀도, 파급효과 밀도)의 Spearman ρ. 규모 ρ 중앙값 ${B.trend.volume_rho_median} (양수 ${B.trend.volume_rho_positive}/${B.trend.n_volume_tested}), 충성도 밀도 ρ 중앙값 ${B.trend.loyalty_density_rho_median}, 파급효과 밀도 ρ 중앙값 ${B.trend.spillover_density_rho_median}. p<0.05 상승/하락: 충성도 ${B.trend.loyalty_density_sig_up}/${B.trend.loyalty_density_sig_down}, 파급효과 ${B.trend.spillover_density_sig_up}/${B.trend.spillover_density_sig_down} (검정 가능 팬덤 ${B.trend.n_fandoms_tested}). 다중 비교 보정은 하지 않았으며 방향 참고용이다.`));
children.push(h2("4-3. 고정효과 회귀 (statsmodels OLS)"));
children.push(table(["모형", "종속변수", "칸", "R²(팬덤 FE)", "R²(팬덤+연도 FE)", "연도 효과 F (p)", "late_round_share 계수 (p)"], [
  ["density ~ C(fandom) [+ C(year)] [+ late_round_share]", "충성도 밀도", String(R.loyalty_density.n_cells), f4(R.loyalty_density.r2_fandom_fe), f4(R.loyalty_density.r2_two_way_fe), `${R.loyalty_density.year_fe_F} (${R.loyalty_density.year_fe_p.toPrecision(3)})`, `${R.loyalty_density.late_round_share_coef} (${R.loyalty_density.late_round_share_p.toPrecision(3)})`],
  ["같음", "파급효과 밀도", String(R.spillover_density.n_cells), f4(R.spillover_density.r2_fandom_fe), f4(R.spillover_density.r2_two_way_fe), `${R.spillover_density.year_fe_F} (${R.spillover_density.year_fe_p.toPrecision(3)})`, `${R.spillover_density.late_round_share_coef} (${R.spillover_density.late_round_share_p.toPrecision(3)})`],
], [2600, 1200, 800, 1200, 1400, 1400, 1038], { size: 16 }));
children.push(spacer());
children.push(p(`충성도–파급효과 패널 회귀 S ~ L: 통합 계수 ${R.loyalty_spillover_panel.pooled_coef} (p=${R.loyalty_spillover_panel.pooled_p.toPrecision(3)}), 팬덤·연도 고정효과 후 ${R.loyalty_spillover_panel.within_coef_two_way_fe} (p=${R.loyalty_spillover_panel.within_p.toPrecision(3)}), 칸 ${R.loyalty_spillover_panel.n_cells}. 로그 문장 수의 연도 효과(2015 대비, 팬덤 FE 통제): ` + Object.entries(R.log_volume.year_effects_vs_2015).map(([k, v]) => `${k.slice(-5, -1)} ${v >= 0 ? "+" : ""}${v.toFixed(2)}`).join(", ") + "."));
children.push(h2("4-4. 부트스트랩"));
children.push(p(`상위 8개 팬덤의 유효 칸마다 문장을 복원추출(B=${n(SET.bootstrap_B)}, seed ${SET.seed})해 밀도의 95% 백분위 CI를 구한다(output/bootstrap_year_cells_v7.csv, 그림 1의 음영). 칸 표본이 작아 CI가 넓은 것이 정상이며, 한 해 값이 아니라 방향을 읽는 근거로 쓴다.`));

children.push(h1("5. E. 수집 시점 편향"));
children.push(p(`사건 연도의 ${pct(E.share_2025_2026)}가 2025∼2026년이다. 수집 구간별로 보면 후기 추가분(r41∼r72)의 연도 분포가 초기 수집보다 최근으로 치우친다(output/round_year_distribution_v7.csv, 그림 4). 보정은 (1) 연도 점유율 year_share, (2) 고정효과 회귀에 late_round_share를 넣는 것으로 했다: 계수는 충성도 밀도 ${E.late_round_share_coef.loyalty_density[0]} (p=${E.late_round_share_coef.loyalty_density[1].toPrecision(3)}), 파급효과 밀도 ${E.late_round_share_coef.spillover_density[0]} (p=${E.late_round_share_coef.spillover_density[1].toPrecision(3)})로, 밀도는 수집 시점에 크게 좌우되지 않는다. 규모(문장 수)는 수집 시점과 분리되지 않으므로 성장으로 해석하지 않는다.`));
children.push(table(["연도", "문장", "후기 추가 비율"], Object.entries(E.year_totals).map(([y, v]) => [y, n(v), pct(E.late_share_by_year[y])]), [2000, 3000, 4638], { size: 16 }));

children.push(h1("6. C. 경로(F1∼F5) 비중의 연도 추이 — 근사"));
children.push(p(`공식 라이브 K=8 모델의 문서-토픽 분포는 저장돼 있지 않다. 대신 저장된 재현 K=8 모델(topic_phi_cosine/lda_model_k8_v7_final.pkl, run_lda_v6.py 토크나이저, ${n(C.n_docs_theta)}문서)로 문장별 θ를 구하고, 토픽 대응표(D_live_reference_k8→E_live_k8, Hungarian)로 재현 토픽을 공식 토픽에 이은 뒤 공식 토픽→요인→F 배정으로 접어 팬덤×연도 F 비중(θ 평균)을 만든다. 연도별 상위 2 F 조합이 그해 페르소나다(유효 칸만).`));
children.push(table(["재현 토픽", "공식 토픽", "F", "Jaccard(top10)"], Object.entries(C.replica_topic_map).map(([e, v]) => ["E" + e, "T" + v.official_topic, v.F, String(v.jaccard_top10)]), [2400, 2400, 2400, 2438], { size: 17 }));
children.push(spacer());
children.push(p(`검증: 전 연도 합산 θ-F 비중과 공식 factor_share의 팬덤 간 상관은 ` + Object.entries(C.aggregate_vs_official_factor_share_r).map(([k, v]) => `${k} ${v}`).join(" · ") + `, 평균 절대 차이 ${C.aggregate_vs_official_mean_abs_diff}, 이 θ로 매긴 전 기간 페르소나가 공식과 같은 팬덤 ${C.theta_persona_same_as_official}. 대응이 약한 토픽(Jaccard ≤ 0.25)이 있어 F1·F5 쪽 상관이 낮다. 따라서 6절의 결과(첫·마지막 유효 연도 페르소나가 다른 팬덤 ${C.changed_first_to_last}/${C.fandoms_with_persona_years}, 한 번이라도 바뀐 팬덤 ${C.any_switch})는 방향 참고용이며, 공식 해석 계층의 시간 분해로 쓰려면 공식 모델의 θ 저장(파이프라인 옵션 추가)이 먼저다.`));

children.push(h1("7. 산출물"));
children.push(table(["파일", "내용", "행/규모"], [
  ["output/sentence_time_tags_v7.csv", "문장별 시점 태그(text_years, url_date, relative_expr, event_year, year_source, text_url_gap)", "10,020"],
  ["output/fandom_year_panel_v7.csv", "팬덤×연도 칸(문장 수·합·밀도·점유율·후기 비율·유효)", n(B.n_cells)],
  ["output/year_summary_v7.csv", "연도별 문장 수·유효 팬덤·평균 밀도·횡단면 상관", "12"],
  ["output/fandom_trend_v7.csv", "팬덤별 유효 연도·구간·규모/밀도 Spearman ρ·p", "유효 칸 있는 팬덤"],
  ["output/bootstrap_year_cells_v7.csv", "상위 8개 팬덤 칸별 밀도와 95% CI", "칸 수"],
  ["output/round_year_distribution_v7.csv", "연도별 초기/후기 수집 문장 수와 후기 비율", "12"],
  ["output/fandom_year_factor_share_v7.csv", "팬덤×연도 F1∼F5 비중·상위 2·페르소나(근사)", "칸 수"],
  ["output/persona_transition_v7.csv", "팬덤별 첫·마지막 유효 연도 페르소나·전환 횟수·경로(근사)", "100"],
  ["output/summary_v7.json", "위 전부의 요약 수치(이 명세서·노트북·R이 대조)", "—"],
  ["output/fig_ts01∼04*.png", "연도 프로파일 / 연도별 횡단면 상관 / 연도별 페르소나 분포 / 수집 시점별 연도 분포", "4장"],
  ["시계열_패널분석_V7.md", "결과 문서(스크립트가 생성)", "—"],
  ["시계열_패널분석_v7.ipynb", "실행 결과가 든 노트북", "—"],
  ["R/ (+ 시계열분석_R코드.zip)", "01 연도별 상관 · 02 고정효과 회귀 · 03 추세·부트스트랩, RUN_ALL.R이 output/r_verify_summary.txt에 파이썬 값과의 대조를 기록", "base R"],
], [3200, 5000, 1438], { size: 16 }));

children.push(h1("8. 한계와 다음 단계"));
children.push(bullet("사건 연도는 언론이 언급한 연도의 근사이며 사람 표본 검증을 아직 하지 않았다. 다음 단계: 200문장 표본 판정으로 year_source별 정확도를 재고 규칙을 고친다."));
children.push(bullet("코퍼스의 최근 편중과 팬덤별 편중 차이 때문에 규모 추세는 성장으로 읽을 수 없다. 밀도·점유율·고정효과가 보정이지만 완전하지 않다."));
children.push(bullet("연도 칸 표본이 작아 밀도의 연도 효과는 약하다(충성도 p≈0.04, 파급효과 p≈0.06). 유의 판정보다 CI와 방향으로 읽는다."));
children.push(bullet("6절 θ는 공식 모델이 아니다. 파이프라인에 문서-토픽 분포 저장 옵션을 넣어 공식 θ로 다시 계산하는 것이 다음 단계다."));
children.push(bullet("R 코드는 이 환경에 R이 없어 실행하지 않았다. 문법·경로는 파이썬 산출물에 맞춰 작성했으며, 실행하면 output/r_verify_summary.txt에 파이썬 값과의 대조가 남는다."));

const doc = new Document({
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] },
    { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 300 } } } }] },
  ] },
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: MUTED })], alignment: AlignmentType.CENTER })] }) }, children }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUTP, buf); console.log("wrote", OUTP, buf.length); });
