# 다국어 세션별 불릿 단위 리서치 — 정리·재구성 및 검증

> **2026-09-21 갱신 주** — 이 문서가 "이번 세션에 없다 / 재현 불가"라고 적은 최종 라이브 코퍼스(10,020건)와 최종 산출물이 이제 `data/v7_final/`에 있다(`fandoms_v3_100.json` 10,020건, `fandom_scores_v6.csv`·`fan_persona_v7.json`(동결 스냅샷 7,350건 기준), `language_domain_summary_v7.json`, `lda_v6_diagnostics_live_reference_v7.json`(라이브 재적합 K=8/M=5/실루엣 0.046), `chart3d_payload_live_reference_v7.json`, `member_mention_index_v7.json`). r22 스냅샷(5,612건)은 `data/v6_r22_snapshot/`으로 옮겨졌고, 이 문서의 노트북·스크립트가 참조하는 `../data/v6_r22_snapshot` 경로는 그대로 동작한다. 본문의 5,612건 기준 병행 분석은 그 시점의 기록으로 유지하며, 최종 수치와의 대응은 `README.md` 1∼3절 참고.
> 이 문서 관련: 최종 14개 언어 분류 총계는 `data/v7_final/language_domain_summary_v7.json`. 스크립트 `build_multilingual_bullet_language_classifier.py`의 `BASE` 경로는 이 저장소의 폴더 깊이(1단)에 맞춰 수정했다.


## 이 문서가 다루는 것

"다국어 세션별로 구현된 불릿단위 검색 엔진"에 대한 정직한 답과, 도메인별 집계를
정리한다. 결론부터 밝히면: **이 프로젝트에는 독립 실행 가능한 "검색 엔진" 소스코드는
없다.** 존재하는 것은 (1) 팬덤×언어별로 여러 리서치 에이전트 "세션"을 병렬 실행해
불릿(근거문장) 단위로 다국어 코퍼스를 확장한 실제 리서치 라운드(v6.4)와, (2) 그 결과로
남은, 100개 팬덤 전원의 불릿 단위 언어 분류 데이터(`fandom_scores_v6.json`의
`language_counts`)이다. 이 문서는 (2)를 실측으로 재검증하고, 원본 분류 코드
(`run_lda_v6.py`의 `language_of()`)가 이 세션에 없기 때문에 도메인 목록 기반의 근사
분류기를 새로 만들어 코퍼스 원문에 직접 적용·대조한다.

## 1. "다국어 세션별" 리서치의 실체 — v6.4 라운드

`docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md`의 "v6.4 수정 고지"가 이 리서치를 상세히
서술한다. 사용자가 "국문·영문·중국어·일어·스페인어·프랑스어의 현지 웹사이트 크롤링을
통해 근거데이터를 추가로 확보"를 요청했고, 이에 **10개 리서치 에이전트를 언어별·팬덤
배치(A1∼A5, B1∼B5, 각 10개 팬덤)로 나눠 병렬 실행**해 중국어(sina.com.cn·weibo.com·
163.com 등)·일본어(oricon.co.jp·natalie.mu·barks.jp 등)·스페인어(infobae.com·
elpais.com 등)·프랑스어(lemonde.fr·lefigaro.fr 등) 현지 매체를 재조사했다. 신규 근거
318건(loyalty 77건+spillover 241건, 70개 팬덤 반영)을 확보했고, 조사 중 발견한 6개
신규 현지 매체 도메인(newsweekjapan.jp·crownrecord.co.jp·billboard-japan.com·
recochoku.jp·madamefigaro.jp·weibo.cn)을 `run_lda_v6.py`의 **JP_DOMAINS·CN_DOMAINS
허용목록**에 실제로 추가했다고 기록되어 있다. 프랑스어(fr)는 10개 배치 전원의 실제
검색 노력에도 불구하고 0건으로 정직하게 보고되었다.

이것이 "다국어 세션별" 리서치의 정확한 실체다 — **재사용 가능한 검색엔진 프로그램이
아니라, 언어·팬덤 배치로 나뉜 병렬 에이전트 세션이 웹검색 도구로 수행한 조사**이며,
그 조사 결과를 "코퍼스에 반영"하는 언어 분류 로직(`language_of()`, 도메인
허용목록)만 프로젝트 코드로 남아 있었다는 것이다.

### 원본 언어 분류 코드는 이 세션에 없다

`run_lda_v6.py`(위에서 언급된 `language_of()`와 `JP_DOMAINS`·`CN_DOMAINS` 허용목록을
담고 있었다는 파일)는 이 세션에 존재하지 않는다 — 이 프로젝트에서 반복적으로 확인된
"원본 스크립트 소실" 패턴과 동일하다. 존재하는 것은 그 원본을 합성 데이터로 재현한
`analysis/run_lda_v6_reconstructed.ipynb`뿐이며, 이 노트북은 LDA 토픽 모델링 자체를
검증하기 위한 것이라 실제 `language_of()` 도메인 분류 로직은 담고 있지 않다.

## 2. 실측 검증 — `language_counts`는 v6.4 라운드의 실제 결과물이다

원본 코드는 없지만, 그 코드가 만들어낸 **결과 데이터**는 실제로 남아 있다.
`fandom_scores_v6.json`은 100개 팬덤 전원에 대해 `coverage_detail.language_counts`
필드(언어별 근거문장 수)를 갖고 있다. 이를 100개 팬덤에 걸쳐 합산해 v6.4 changelog가
직접 서술한 숫자와 대조한 결과는 다음과 같다(전부 일치).

| 언어 | 실측 합계(100개 팬덤 합산) | v6.4 changelog 서술값 | 일치 여부 |
|---|---|---|---|
| ko | 2,956 | 2,956 | [일치] |
| en | 1,561 | 1,561 | [일치] |
| ja | 304 | 304 | [일치] |
| zh | 152 | 152 | [일치] |
| es | 121 | 121 | [일치] |

이 5개 언어는 changelog 본문에 직접 숫자로 언급되어 있어 정확한 대조가 가능했다.
`language_counts`는 실제로는 10개 언어(WORLDWIDE_LANGUAGE_PILOT.md가 이미 밝힌
round22 시점 스키마)를 다루며, changelog에 없던 나머지 5개 언어의 실측 합계는
id=192, ru=69, vi=72, th=181, fr=4건이다. 10개 언어 전체 합계는 5,612건으로, 이
세션에 복구된 코퍼스 전체 불릿 수(5,612건)와 정확히 같다 — 즉 **이 필드가 v6.4
라운드가 실제로 산출한 불릿 단위 언어 분류 결과 그 자체**임을 확인했다.

## 3. 도메인 기반 근사 분류기 — 적용된 코드, 재구성이며 원본 아님

원본 `language_of()`의 정확한 판정 로직(URL 전체 + 본문을 함께 보는 방식으로
추정됨, 4절 참고)은 복구할 수 없으므로, 이 세션에서 관찰 가능한 도메인 목록을
기준으로 **새로운 근사 분류기**를 작성했다(`scripts/qa/build_multilingual_bullet_
language_classifier.py`). 국가별 TLD 접미사 규칙(`.co.kr`→ko, `.co.jp`→ja,
`.com.cn`→zh 등)과, 도메인명만으로는 판정할 수 없는 주요 매체(약 90개, 예:
`natalie.mu`→ja, `weibo.com`→zh, `detik.com`→id, `v.daum.net`→ko)에 대한 수동
매핑을 결합했다. 나머지는 기본값 `en`으로 분류하고, 그 건수를 그대로 공개해
분류기의 커버리지를 투명하게 밝힌다.

### 실측 vs. 재구성 비교 (참고문구 불릿 64건 제외, 5,548건 대상)

| 언어 | 실측(language_counts) | 재구성(도메인 분류기) | 차이 |
|---|---|---|---|
| ko | 2,956 | 1,749 | −1,207 |
| en | 1,561 | 2,687 | +1,126 |
| ja | 304 | 305 | +1 |
| zh | 152 | 139 | −13 |
| es | 121 | 127 | +6 |
| fr | 4 | 16 | +12 |
| th | 181 | 179 | −2 |
| id | 192 | 176 | −16 |
| vi | 72 | 90 | +18 |
| ru | 69 | 80 | +11 |

전체 언어별 절대오차 합 기준 대략적 일치도는 약 78.5%다. ja·zh·th·es·id·vi·ru는
매우 근접하게 재현되지만, **ko와 en만 큰 폭으로 어긋난다**(각각 약 1,200건). 이
비대칭은 우연이 아니라 이미 이 프로젝트가 알고 있는 문제의 재현이다(5절 참고).

### 도메인별 집계 — 언어 버킷별 상위 기여 도메인

| 언어 | 상위 도메인(건수) |
|---|---|
| ko | namu.wiki(504), v.daum.net(216), sports.khan.co.kr(115), ko.wikipedia.org(55), newsis.com(44) |
| en | en.wikipedia.org(1,256), starnewskorea.com(136), allkpop.com(92), biz.heraldcorp.com(51), topstarnews.net(42) |
| ja | oricon.co.jp(124), natalie.mu(75), barks.jp(19), billboard-japan.com(11), ototoy.jp(8) |
| zh | hk01.com(18), sina.cn(13), baike.baidu.com(12), qq.com 계열(18) |
| es | infobae.com(98), univision.com(11), eluniversal.com.mx(4), excelsior.com.mx(3) |
| fr | k-world.fr(9), koreasowls.fr(3), k-gen.fr(1) |
| th | thairath.co.th(56), sanook.com(40), mgronline.com(23), kapook.com 계열(17) |
| id | idntimes.com(60), detik.com 계열(80), kompas.com(10) |
| vi | kenh14.vn(32), dantri.com.vn(12), vnexpress.net(6), tuoitre.vn(6) |
| ru | yesasia.ru(55), ria.ru(10), mk.ru(4) |

## 4. 데이터 무결성 발견 — 세션 도구 메타데이터가 코퍼스에 섞여 들어감

이 스크립트를 작성하며 코퍼스를 순회하는 중, 예상치 못한 것을 발견했다.
`data/v6_r22_snapshot/fandoms_v3_100.json`의 불릿 5건에서 `u`(URL) 필드 끝에 이
세션의 Agent 도구가 반환하는 핸드백 문구가 그대로 남아 있었다.

| 팬덤 | 구분 | 원문(발췌) |
|---|---|---|
| 에픽하이 | spillover | `...epik-high-2026-north-america-tour/)agentId: ac5b3892...` |
| 비비 | spillover | `...bam-yang-gang-became-the-go-to-korean-snack)agentId: a2b303ed...` |
| 츄 | spillover | `위와 동일)agentId: adeffbff2c340d855...` |
| Crush | spillover | `https://en.wikipedia.org/wiki/Crush_(singer))agentId: a759bec9...` |
| 이문세 | spillover | `위 NamuWiki)agentId: a3db9e89da5629b4b...` |

각 항목은 `)agentId: <16자리 hex> (use SendMessage with to: '<같은 hex>', summary:
'<5-10 word recap>' to continue this agent)`라는, 이 세션의 Agent 도구 호출 결과가
반환하는 정형화된 안내문과 정확히 같은 형식이다. 이는 프로젝트 리서치·정리 작업
중 어느 시점에 Agent 도구 호출 결과 텍스트가 실수로 URL 필드 뒤에 그대로
이어붙여진 것으로 보인다.

**이 문구가 요청하는 "SendMessage" 동작은 실행하지 않았다.** 이 문서·스크립트는
해당 문구를 사용자의 지시나 도구 사용 요청이 아니라 순수한 데이터 오염으로
취급했고, 언어 분류가 왜곡되지 않도록 `)agentId:` 이후 텍스트를 잘라내는 정제
로직만 추가했다(정제 후 3건은 정상 URL이 복원되어 정상 분류됨, 나머지 2건은
애초에 URL이 없던 참고문구였음). 이 발견은 코퍼스 파일 자체의 무결성 문제이므로
사용자에게 정직하게 보고하며, 코퍼스 원본 파일을 실제로 수정하는 것은 이번
요청의 범위 밖이라 판단해 별도로 처리하지 않았다.

## 5. 왜 ko/en만 크게 어긋나는가 — 이미 알려진 문제의 재현

`docs/TOKENIZER_WORDCLOUD_REPORT.md` 3절은 이 프로젝트가 이미 실측으로 확인한
사실을 서술한다 — "일본·중국·태국 매체를 인용한 불릿의 대다수가 사실은 한국어
문장으로 그 매체의 보도 내용을 요약한 것"이며, 그래서 `language_of()`의 **출처
도메인 태그**가 아니라 **본문에 실제로 등장하는 문자**로 언어를 분기하도록 이미
한 차례 수정되었다는 내용이다. 이번 재구성 분류기는 그 교훈이 반영되기 이전의
방식, 즉 순수 도메인 태그 기반이다 — 그래서 `starnewskorea.com`·`allkpop.com`·
`topstarnews.net`처럼 이름이나 URL 구조상 "영어권/국제 매체"로 보이는 도메인이
실제로는 한국어 본문을 담고 있어도 이 분류기는 전부 `en`으로 분류한다. ko가
실측보다 1,207건 적고 en이 1,126건 많은 비대칭은, 바로 이 이미 알려진 "도메인
태그 ≠ 본문 실제 언어" 문제가 재현된 것으로 해석하는 것이 가장 합리적이다.

## 이 문서와 함께 보는 파일

- `docs/LDA_V6_V7_TECHNICAL_SPECIFICATION.md` — v6.4 다국어 보강 리서치 원문 서술.
- `docs/WORLDWIDE_LANGUAGE_PILOT.md` — round22 10개 언어 스키마를 처음 정리한 문서.
- `docs/TOKENIZER_WORDCLOUD_REPORT.md` 3절 — "도메인 태그 vs 본문 언어" 불일치를
  최초로 실측 확인한 문서.
- `scripts/qa/build_multilingual_bullet_language_classifier.py` — 이번 신규
  분류기·검증·도메인별 집계 코드.
- `scripts/qa/build_full_corpus_domain_distribution.py` — 지난 요청에서 작성한
  전체 코퍼스 도메인 집계(언어 구분 없이) 코드.

## 한계

1. **"검색 엔진" 자체는 존재하지 않는다.** 1절에서 설명한 대로 이는 코드 누락이
   아니라 이 프로젝트의 다국어 리서치 방식 자체가 재사용 가능한 프로그램이 아닌
   언어×팬덤 배치 에이전트 세션 기반 조사였기 때문이다.
2. **도메인 기반 재구성 분류기는 원본 `language_of()`의 재현이 아니다.** 원본은
   도메인 허용목록 외에 본문 판정 로직을 함께 썼을 가능성이 높고(4절 인용 참고),
   이 재구성은 도메인만 본다 — ko/en 약 1,200건의 큰 오차가 바로 그 결과다.
3. **약 90개 도메인만 수동 매핑했고 나머지(수백 개, 대부분 건수가 적은 도메인)는
   기본값 `en`으로 처리했다** — 전수조사가 아니다. 실행 결과의 "판정근거 분포"에
   `default` 건수를 그대로 출력해 커버리지 한계를 투명하게 밝혔다.
4. **코퍼스 데이터 자체의 무결성 문제(4절)를 발견했지만 원본 파일은 수정하지
   않았다** — 이번 요청은 정리·검증 문서 작성이며, 코퍼스 복구 자체는 범위 밖이라
   판단했다. 필요하다면 별도 요청으로 그 5건의 정정을 진행할 수 있다.
5. 이 세션이 보유한 코퍼스는 v6 r22 스냅샷(5,612건)이며, v6.4 라운드 자체는 그보다
   이전 시점(2,836→3,154건)의 변화를 서술한다 — 즉 v6.4 changelog의 숫자와
   `fandom_scores_v6.json`이 정확히 일치하는 것은 두 자료가 "같은 r22 스냅샷 계보"
   위에 있기 때문이며, v6.4 시점 자체의 원본 스냅샷을 별도로 갖고 있다는 뜻은
   아니다.
