# 토크나이저 불용어 목록 — 언어별 정리 (최종 코퍼스 10,020건 기준)

이 문서와 같은 폴더의 `tokenizer_stopwords_by_language_v7.csv`는 `export_tokenizer_stopwords_v7.py`가 **저장소 안의 코드에서 직접 읽어** 만든 것이다. 손으로 옮겨 적은 목록이 아니므로, 코드가 바뀌면 스크립트를 다시 돌려 갱신한다.

## 불용어가 정의된 곳 3군데

| 출처 | 파일 | 무엇에 쓰이나 | 목록 |
|---|---|---|---|
| A | `run_lda_v6.py` (저장소 루트) | 원 파이프라인의 `tokenize()` — LDA 입력 토큰화 (한국어·영어 일반 경로) | PARTICLES 39, STOPWORDS 30, ENGLISH_STOPWORDS 118 |
| B | `analysis/tokenizer/build_bullet_token_frequency_csv_v7.py` | 최종 코퍼스 10,020건 토큰 빈도 CSV(`csv/bullet_token_frequency_v7_final.csv`) — 일반 경로 + 일본어(fugashi)·중국어(jieba)·태국어(pythainlp) 추가 경로 | 한국어 74, 영어 75, 라틴 통합 53, 러시아어 21, 일본어 29, 중국어 32 |
| C | `pythainlp 5.3.7` `corpus.thai_stopwords()` | B의 태국어 경로가 그대로 쓰는 라이브러리 내장 목록 | 태국어 1030 |

**원 보고서의 14개 언어 라우팅 토크나이저(`run_lda_v6_live_reference_v7.py`)와의 관계.** 보고서 7.7절(`tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` 표 1)은 STOPWORDS 41종·ENGLISH_STOPWORDS 64종·7개 라틴어권 언어별 세트를 합친 ALL_LATIN_STOPWORDS·RUSSIAN_STOPWORDS·JAPANESE_STOPWORDS 28종·CHINESE_STOPWORDS 60여 종·pythainlp 내장 태국어 불용어를 쓴다고 서술한다. 그 소스는 저장소에 없다. 저장소에 실제로 있는 목록은 A(그 이전 판 파이프라인)와 B(같은 구조를 독자 구현한 병행 파일럿)이며, 태국어(C)만 원 보고서와 동일한 라이브러리 목록이다. 따라서 B의 한국어·영어·라틴·러시아어·일본어·중국어 목록은 원 보고서 목록과 **개수와 내용이 다르다**.

## 개수 요약

| 출처 | 목록명 | 언어 | 코드 | 개수 |
|---|---|---|---|---|
| A. 원 파이프라인 | `PARTICLES` | 한국어 | ko | 39 |
| A. 원 파이프라인 | `STOPWORDS` | 한국어 | ko | 30 |
| A. 원 파이프라인 | `ENGLISH_STOPWORDS` | 영어 | en | 118 |
| B. 최종 코퍼스 토큰 빈도 | `KOREAN_STOPWORDS` | 한국어 | ko | 74 |
| B. 최종 코퍼스 토큰 빈도 | `ENGLISH_STOPWORDS` | 영어 | en | 75 |
| B. 최종 코퍼스 토큰 빈도 | `LATIN_OTHER_STOPWORDS` | 스페인어 | es | 19 |
| B. 최종 코퍼스 토큰 빈도 | `LATIN_OTHER_STOPWORDS` | 프랑스어 | fr | 10 |
| B. 최종 코퍼스 토큰 빈도 | `LATIN_OTHER_STOPWORDS` | 인도네시아어 | id | 10 |
| B. 최종 코퍼스 토큰 빈도 | `LATIN_OTHER_STOPWORDS` | 베트남어 | vi | 9 |
| B. 최종 코퍼스 토큰 빈도 | `LATIN_OTHER_STOPWORDS` | 튀르키예어 | tr | 7 |
| B. 최종 코퍼스 토큰 빈도 | `RUSSIAN_STOPWORDS` | 러시아어 | ru | 21 |
| B. 최종 코퍼스 토큰 빈도 | `JAPANESE_STOPWORDS` | 일본어 | ja | 29 |
| B. 최종 코퍼스 토큰 빈도 | `CHINESE_STOPWORDS` | 중국어 | zh | 32 |
| C. pythainlp 내장 | `THAI_STOPWORDS` | 태국어 | th | 1030 |
| 합계 | | | | 1503 |

## A. `run_lda_v6.py` — 원 파이프라인 (한국어·영어)

토큰 정규식 `[가-힣A-Za-z0-9]{2,}` → 조사 접미사 제거(PARTICLES, 긴 것부터 1회) → 2자 미만·STOPWORDS 제외 → 소문자 ENGLISH_STOPWORDS 제외 → 순수 숫자 제외.

### A-1. PARTICLES — 한국어 조사·어미 접미사 (39개, 코드 순서)

`으로부터` · `까지` · `에서부터` · `이라는` · `라는` · `에서` · `으로` · `부터` · `에게` · `한테` · `에는` · `에도` · `이나` · `라도` · `이며` · `하며` · `되어` · `됐다`  
`했다` · `한다` · `됨` · `임` · `은` · `는` · `이` · `가` · `을` · `를` · `의` · `와` · `과` · `도` · `만` · `로` · `에` · `고`  
`서` · `다` · `며`

### A-2. STOPWORDS — 한국어 (30개)

`것으로` · `것은` · `것을` · `것이` · `것이다` · `관련` · `나타났다` · `당시` · `대한` · `대해` · `됐다` · `되는` · `되다` · `라고` · `밝혔다` · `아니다` · `없는` · `없다`  
`위해` · `이다` · `이라고` · `이후` · `있는` · `있다` · `전했다` · `통한` · `통해` · `하는` · `한다` · `했다`

### A-3. ENGLISH_STOPWORDS — 영어 (118개; 소스 리터럴 120개 중 `up`·`out` 중복)

`a` · `about` · `according` · `across` · `after` · `all` · `also` · `amid` · `among` · `an` · `and` · `announced` · `another` · `any` · `are` · `as` · `at` · `be`  
`been` · `before` · `being` · `between` · `both` · `but` · `by` · `can` · `could` · `currently` · `did` · `do` · `does` · `down` · `during` · `each` · `few` · `first`  
`for` · `from` · `had` · `has` · `have` · `he` · `her` · `his` · `if` · `in` · `included` · `including` · `into` · `is` · `it` · `its` · `many` · `may`  
`might` · `more` · `most` · `much` · `my` · `new` · `no` · `not` · `of` · `off` · `officially` · `on` · `one` · `onto` · `or` · `other` · `our` · `out`  
`over` · `per` · `previously` · `recently` · `reported` · `said` · `says` · `second` · `she` · `should` · `since` · `so` · `some` · `such` · `than` · `that` · `the` · `their`  
`then` · `these` · `they` · `third` · `this` · `those` · `three` · `to` · `two` · `under` · `up` · `very` · `via` · `was` · `we` · `were` · `what` · `when`  
`where` · `which` · `while` · `who` · `whom` · `will` · `with` · `would` · `you` · `your`

## B. `build_bullet_token_frequency_csv_v7.py` — 최종 코퍼스 토큰 빈도 (일반 경로 + 문자권별 추가 경로)

일반 경로: 구두점 경계 정규식 토큰화 → 2자 미만·순수 숫자 제외 → 소문자가 아래 한국어·영어·라틴·러시아어 통합 집합에 있으면 제외. 추가 경로: 본문에 가나가 있으면 fugashi(명사·동사·형용사만, 일본어 불용어 제외), 가나 없이 한자만 있으면 jieba(중국어 불용어 제외), 태국 문자가 있으면 pythainlp newmm(내장 불용어 제외).

### B-1. KOREAN_STOPWORDS — 한국어 (74개)

`가장` · `것` · `것으로` · `것은` · `것을` · `것이다` · `관련` · `그` · `그래서` · `그러나` · `그리고` · `까지` · `나` · `다시` · `당시` · `대해` · `더` · `도`  
`됐다` · `된` · `된다` · `등` · `등에` · `등은` · `등을` · `등의` · `등이` · `등장` · `따라서` · `또` · `또한` · `라고` · `라며` · `로써` · `만` · `많이`  
`및` · `부터` · `수` · `에게` · `에는` · `에도` · `에서` · `에서는` · `위해` · `으로` · `으로써` · `이` · `이나` · `이는` · `이다` · `이라고` · `이라며` · `이를`  
`이번` · `이에` · `이전` · `이후` · `있다` · `있으며` · `저` · `통해` · `특히` · `하고` · `하는` · `하는데` · `하며` · `하지만` · `한` · `한편` · `할` · `함께`  
`했다` · `현재`

### B-2. ENGLISH_STOPWORDS — 영어 (75개)

`a` · `about` · `after` · `all` · `also` · `an` · `and` · `are` · `as` · `at` · `be` · `been` · `before` · `being` · `between` · `both` · `but` · `by`  
`can` · `could` · `down` · `during` · `each` · `few` · `for` · `from` · `had` · `has` · `have` · `he` · `her` · `his` · `in` · `into` · `is` · `it`  
`its` · `just` · `more` · `most` · `not` · `of` · `off` · `on` · `only` · `or` · `other` · `our` · `out` · `over` · `own` · `same` · `she` · `so`  
`some` · `such` · `than` · `that` · `the` · `their` · `then` · `these` · `they` · `this` · `those` · `to` · `up` · `was` · `we` · `were` · `will` · `with`  
`would` · `you` · `your`

### B-3. LATIN_OTHER_STOPWORDS — 라틴 문자권 통합 (53개 고유; 세부 언어는 소스 줄 순서 기준, `un`·`de`는 두 언어에 중복)

- **스페인어(es) 19개**: `el` · `la` · `los` · `las` · `de` · `del` · `en` · `un` · `una` · `que` · `por` · `para` · `con` · `su` · `sus` · `es` · `se` · `lo` · `al`
- **프랑스어(fr) 10개**: `le` · `les` · `des` · `et` · `un` · `une` · `dans` · `sur` · `avec` · `pour`
- **인도네시아어(id) 10개**: `yang` · `dan` · `di` · `ke` · `dari` · `untuk` · `pada` · `dengan` · `ini` · `itu`
- **베트남어(vi) 9개**: `và` · `của` · `là` · `có` · `cho` · `trong` · `được` · `này` · `với`
- **튀르키예어(tr) 7개**: `ve` · `bir` · `bu` · `de` · `da` · `için` · `ile`

### B-4. RUSSIAN_STOPWORDS — 러시아어 (21개)

`а` · `в` · `для` · `его` · `её` · `же` · `за` · `и` · `из` · `их` · `к` · `как` · `на` · `не` · `но` · `от` · `по` · `с`  
`то` · `что` · `это`

### B-5. JAPANESE_STOPWORDS — 일본어 (29개)

`あの` · `ある` · `いる` · `から` · `が` · `こと` · `この` · `これ` · `する` · `その` · `それ` · `た` · `ため` · `だ` · `った` · `て` · `で` · `です`  
`と` · `な` · `に` · `の` · `は` · `ます` · `まで` · `も` · `もの` · `よう` · `を`

### B-6. CHINESE_STOPWORDS — 중국어 (32개)

`一个` · `与` · `为` · `之` · `也` · `了` · `以` · `但` · `其` · `又` · `及` · `和` · `因为` · `在` · `地` · `对` · `就` · `并`  
`很` · `得` · `或` · `所以` · `是` · `此` · `的` · `着` · `而` · `而且` · `被` · `这个` · `那个` · `都`

## C. pythainlp 내장 태국어 불용어 (1030개)

`pythainlp.corpus.thai_stopwords()` (pythainlp 5.3.7). 전체 목록은 CSV의 `THAI_STOPWORDS` 행에 있다. 앞 60개:

`กระทั่ง` · `กระทำ` · `กระนั้น` · `กระผม` · `กลับ` · `กลุ่ม` · `กลุ่มก้อน` · `กลุ่มๆ` · `กล่าว` · `กล่าวคือ` · `กว่า` · `กว้าง` · `กว้างขวาง` · `กว้างๆ` · `กัน`  
`กันดีกว่า` · `กันดีไหม` · `กันนะ` · `กันเถอะ` · `กันเอง` · `กันและกัน` · `กันไหม` · `กับ` · `การ` · `กำลัง` · `กำลังจะ` · `กำหนด` · `กู` · `ก็` · `ก็คือ`  
`ก็จะ` · `ก็ดี` · `ก็ตาม` · `ก็ตามที` · `ก็ตามแต่` · `ก็ต่อเมื่อ` · `ก็แค่` · `ก็แล้วแต่` · `ก็ได้` · `ก่อน` · `ก่อนหน้า` · `ก่อนหน้านี้` · `ก่อนๆ` · `ขณะ` · `ขณะที่`  
`ขณะนั้น` · `ขณะนี้` · `ขณะหนึ่ง` · `ขณะเดียวกัน` · `ขณะใด` · `ขณะใดๆ` · `ขวาง` · `ขวางๆ` · `ขอ` · `ของ` · `ขั้น` · `ขาด` · `ขึ้น` · `ข้า` · `ข้าง`

## 함께 보는 파일

- `../build_bullet_token_frequency_csv_v7.py` — B 목록을 정의하고 최종 코퍼스 10,020건에 적용해 토큰 빈도 CSV를 만드는 코드
- `../csv/bullet_token_frequency_v7_final.csv` — 그 결과(43,162 토큰, 176,944 발생)
- `../../../../run_lda_v6.py` — A 목록을 정의하는 원 파이프라인
- `../../../tokenizer_wordcloud_report/TOKENIZER_WORDCLOUD_REPORT.md` — 원 보고서의 토크나이저 구조·불용어 개수 서술과 재현 범위
- `export_tokenizer_stopwords_v7.py` — 이 문서와 CSV를 코드에서 다시 만드는 스크립트
