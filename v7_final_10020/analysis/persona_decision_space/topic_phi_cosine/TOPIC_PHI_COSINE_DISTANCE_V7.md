# LDA φ분포·토픽 간 코사인 거리·모델 묶음 — 최종 코퍼스 10,020건 참고 재적합

## 0. 한눈에 보기

이 폴더는 `build_topic_phi_cosine_v7.py` 한 개가 만든다. 저장소에 실제로 있는 파이프라인(`run_lda_v6.py`)의 토크나이저·벡터라이저·LDA 설정을 그대로 가져와 **최종 코퍼스 10,020건**에 K=10과 K=8을 적합하고, 그 결과를 세 층으로 남긴다.

| 층 | 무엇 | 파일 |
|---|---|---|
| A. 모델 묶음 | 학습된 LDA 객체(K별)·CountVectorizer·단어 사전·문서 순서·manifest — 문서-토픽 분포를 다시 계산할 수 있는 최소 단위 | `lda_model_k{10,8}_v7_final.pkl`, `count_vectorizer_v7_final.pkl`, `lda_vocabulary_v7_final.csv`, `lda_document_index_v7_final.csv`, `model_bundle_manifest_v7_final.json` |
| B. 산출 행렬 | φ(토픽×어휘), 토픽 간 코사인 거리, average-linkage 병합 기록, M-grid 실루엣 | `lda_phi_*`, `topic_cosine_distance_*`, `topic_linkage_average_*`, `m_grid_silhouette_*` |
| C. 문서 | 이 파일(방법·코드·결과·한계) | `TOPIC_PHI_COSINE_DISTANCE_V7.md` |

| 항목 | 값 |
|---|---|
| 코퍼스 | `data/v7_final/fandoms_v3_100.json` 10,020건 (SHA-256 `b123a5bf7ab7…`) |
| LDA 문서 수 | 9,954건 (3토큰 미만 66건 제외) |
| 어휘 | 12,253개 (`CountVectorizer(max_df=0.6, min_df=2)`) |
| K=10 | perplexity 3460.2, 최적 M=7, 실루엣 0.0803 |
| K=8 | perplexity 3512.6, 최적 M=4, 실루엣 0.0694 |
| 난수 | `random_state=0`, `max_iter=50`, `learning_method="batch"` |
| 패키지 | Python 3.11.15, scikit-learn 1.9.1, scipy 1.17.1, numpy 2.4.6, joblib 1.6.0 |
| 재현성 | 스크립트를 다시 돌리면 CSV가 바이트 단위로 같게 나온다. pickle은 저장 직후 다시 불러 φ CSV·DTM과 일치를 확인한다 |

**이 폴더는 동결 스냅샷(v7-40, 7,350건)의 모델이 아니다.** 보고서 해석 계층이 쓰는 K=10·M=5·실루엣 0.267은 7,350건 코퍼스와 14개 언어 라우팅 토크나이저로 얻은 값이고, 그 둘이 저장소에 없어 동결 모델은 복원할 수 없다. 이 폴더는 같은 방법을 저장소에 있는 재료에 적용한 실측치이며, 동결 모델 묶음이 확보되면 같은 파일 구성으로 옆에 놓기 위한 형식 표준이기도 하다.

## 1. 세 층의 모델과 이 폴더의 위치

저장소에는 LDA 결과가 세 시점으로 존재한다. 이 폴더는 세 번째다.

| | ① 동결 스냅샷 (해석 계층) | ② 공식 라이브 참고 재적합 | ③ 이 폴더 |
|---|---|---|---|
| 코퍼스 | 7,350건 (v7-40) | 10,020건 | 10,020건 |
| 토크나이저 | 14개 언어 라우팅판 `run_lda_v6_live_reference_v7.py` (저장소 미포함) | 같음 | `run_lda_v6.py`의 `tokenize()` (저장소 실물, 구 토크나이저) |
| LDA 문서 수 | — | 10,018건 | 9,954건 |
| K / M / 실루엣 | 10 / 5 / 0.267 | 8 / 5 / 0.046 (게이트 기각) | 10 / 7 / 0.0803 · 8 / 4 / 0.0694 |
| 저장소에 있는 것 | 토픽 상위 10단어, 토픽→F 배정, 덴드로그램 병합 높이·잎 순서·절단 높이, 팬덤별 F 비중 | K-grid 진단, 토픽 상위어, 팬덤별 F 비중 | **φ 전체, 거리 행렬, 병합 기록, 학습 모델, 단어 사전, 문서 순서** |
| 저장소에 없는 것 | 코퍼스, φ, 거리 행렬, 모델, 토크나이저 | 코퍼스는 있음. φ, 모델, 토크나이저 없음 | 없음 |
| 출처 | `data/v7_final/lda_v6_diagnostics_frozen_v7_40.json`, `persona_decision_space_v7.json`, `fandom_scores_v6.json` | `data/v7_final/lda_v6_diagnostics_live_reference_v7.json`, `fandom_scores_live_reference_v7.json` | 이 폴더 |

③의 K=8 실루엣(0.0694)이 ②의 0.046과 다른 이유는 토크나이저가 달라 문서 수(9,954 vs 10,018)와 어휘가 다르기 때문이다. ③의 수치는 "저장소만으로 재현되는 참고 재적합"이고 보고서 본문의 수치를 대체하지 않는다.

동결 모델 묶음(①의 φ·거리 행렬·모델)을 채우는 순서는 **코퍼스 → 토크나이저 → 재적합**이다. 7,350건 코퍼스와 라우팅 토크나이저가 확보되면 이 스크립트의 입력만 바꿔 같은 파일을 `frozen_v7_40/` 아래에 만들고, ①에 남아 있는 값(상위 10단어·토픽→F 배정·절단 높이 0.7736·실루엣 0.267·팬덤별 F 비중)이 전부 재현되는지로 검증한다(9절 4항).

## 2. 폴더 구성

### A. 모델 묶음 (pickle·단어 사전·문서 순서·manifest)

| 파일 | 크기 | 내용 |
|---|---|---|
| `lda_model_k10_v7_final.pkl` | 1.4 MB | 학습된 `LatentDirichletAllocation(n_components=10)` 객체(joblib, compress=3). `components_`가 φ 원본(비정규화, 10×12,253), `transform(X)`로 문서-토픽 분포 θ 재계산 |
| `lda_model_k8_v7_final.pkl` | 1.2 MB | 같은 설정의 K=8 모델 |
| `count_vectorizer_v7_final.pkl` | 102 KB | 학습된 `CountVectorizer`(단어 사전 `vocabulary_` 포함). K=10·K=8 공통, 열 순서가 두 모델의 φ와 같다 |
| `lda_vocabulary_v7_final.csv` | 233 KB | 단어 사전 12,253행: `col`(φ 열 번호), `word`, `df`(등장 문서 수), `tf`(총 등장 횟수) |
| `lda_document_index_v7_final.csv` | 296 KB | DTM 행 순서 9,954행: `doc_id`, `fandom`, `bullet_type`(loyalty/spillover), `idx_in_fandom_array`(`fandoms_v3_100.json`의 해당 배열 위치), `n_tokens` |
| `model_bundle_manifest_v7_final.json` | 4 KB | 시드·LDA/벡터라이저 인자, 코퍼스와 `run_lda_v6.py`의 SHA-256, 패키지 버전, K별 perplexity·최적 M·문서 argmax 배정 수, 파일별 SHA-256·바이트, 재로드 검증 기록 |

### B. 산출 행렬 (K별 접미사 `_k10` / `_k8`)

| 파일 | 크기(K=10 / K=8) | 내용 |
|---|---|---|
| `lda_phi_{k}_v7_final.csv` | 1.7 MB / 1.4 MB | φ 넓은 표 — K행(토픽) × 12,253열(어휘), 값은 확률(행 합 1). 열 순서 = 단어 사전 `col` |
| `lda_phi_top50_{k}_v7_final.csv` | 16 KB / 13 KB | 토픽별 상위 50단어(long): `topic`, `rank`, `word`, `phi`, `raw_weight`(=`components_`) |
| `topic_cosine_distance_{k}_v7_final.csv` | 1 KB / 1 KB 미만 | 토픽 간 코사인 거리 K×K + 토픽 라벨(상위 4단어) |
| `topic_linkage_average_{k}_v7_final.csv` | 1 KB 미만 / 1 KB 미만 | average-linkage 병합 기록 `id, left, right, height, size` — HTML `dendro.merges`와 같은 형식 |
| `m_grid_silhouette_{k}_v7_final.csv` | 1 KB 미만 / 1 KB 미만 | M=4∼8(K=8은 4∼7) 실루엣과 M별 토픽→군집 배정 |

### C. 스크립트·문서

| 파일 | 내용 |
|---|---|
| `build_topic_phi_cosine_v7.py` | A·B 전부와 이 문서를 만든다. 저장소 안 어느 폴더에서 실행해도 된다 (약 1∼3분) |
| `TOPIC_PHI_COSINE_DISTANCE_V7.md` | 이 문서 (스크립트가 생성하므로 손으로 고치지 않는다) |

## 3. 방법 — 단계별 코드

모든 단계는 `run_lda_v6.py`의 해당 절과 같은 함수·인자를 쓴다. 아래 코드는 스크립트 본문에서 그대로 옮긴 것이다.

**1) 토크나이저를 파이프라인 소스에서 잘라 온다** — 재구현하지 않고 `ast`로 `PARTICLES`·`STOPWORDS`·`ENGLISH_STOPWORDS`·`tokenize()` 네 조각의 소스를 뽑아 실행한다.

```python
src = (REPO / "run_lda_v6.py").read_text(encoding="utf-8")
tree = ast.parse(src)
pieces = [ast.get_source_segment(src, n) for n in tree.body
          if (isinstance(n, ast.Assign) and n.targets[0].id in ("PARTICLES", "STOPWORDS", "ENGLISH_STOPWORDS"))
          or (isinstance(n, ast.FunctionDef) and n.name == "tokenize")]
ns = {"re": re}; exec("\n\n".join(pieces), ns); tokenize = ns["tokenize"]
```

**2) 코퍼스 → 문서 → DTM** — 불릿마다 `tokenize()`를 적용해 3토큰 미만이면 제외하고, 파이프라인과 같은 `CountVectorizer` 설정으로 문서-단어 행렬을 만든다. 이때 문서의 순서(팬덤, loyalty/spillover, 배열 위치, 토큰 수)를 `lda_document_index_v7_final.csv`에, 벡터라이저와 단어 사전을 `count_vectorizer_v7_final.pkl`·`lda_vocabulary_v7_final.csv`에 저장한다.

```python
for fd in fandoms:
    for tag in ("loyalty", "spillover"):
        for idx, item in enumerate(fd[tag]):
            toks = tokenize(item["t"])
            if len(toks) >= 3:
                docs.append(" ".join(toks)); meta.append((fd["fandom"], tag, idx, len(toks)))
vectorizer = CountVectorizer(max_df=0.6, min_df=2, token_pattern=r"(?u)\b\w+\b")
X = vectorizer.fit_transform(docs); vocab = vectorizer.get_feature_names_out()
joblib.dump(vectorizer, "count_vectorizer_v7_final.pkl", compress=3)
```

**3) LDA 적합과 φ** — `components_`가 파이프라인이 말하는 φ(토픽×어휘)다. 학습된 객체를 그대로 pickle로 저장하고, CSV에는 행 합이 1이 되도록 나눈 확률값을 쓴다(코사인 거리는 행 스케일에 무관하므로 결과가 같다).

```python
lda = LatentDirichletAllocation(n_components=K, random_state=0, max_iter=50, learning_method="batch").fit(X)
joblib.dump(lda, f"lda_model_k{K}_v7_final.pkl", compress=3)
topic_word = lda.components_                              # φ (K × V), 파이프라인 [2]절
phi = topic_word / topic_word.sum(axis=1, keepdims=True)  # 행 합 1
```

**4) 토픽 간 코사인 거리** — 파이프라인 [3]절 그대로: 행을 L2 정규화한 뒤 1 − 내적, 대각 0, 음수 클립.

```python
phi_norm = topic_word / (np.linalg.norm(topic_word, axis=1, keepdims=True) + 1e-12)
cos_dist = 1 - phi_norm @ phi_norm.T
np.fill_diagonal(cos_dist, 0); cos_dist = np.clip(cos_dist, 0, None)
```

**5) M-grid 실루엣과 병합 트리** — 파이프라인은 `AgglomerativeClustering(metric="precomputed", linkage="average")`로 M=5∼8을 돌려 실루엣 최댓값의 M을 고른다(여기서는 M=4도 포함). 덴드로그램(병합 순서·높이)은 같은 average-linkage를 scipy로 계산해 HTML의 `merges`와 같은 형식(id·left·right·height)으로 저장한다. 두 구현은 같은 병합을 만든다.

```python
for m in range(4, min(9, K)):
    lab = AgglomerativeClustering(n_clusters=m, metric="precomputed", linkage="average").fit_predict(cos_dist)
    sil = silhouette_score(cos_dist, lab, metric="precomputed")
Z = linkage(squareform(cos_dist, checks=False), method="average")   # 행: [left, right, height, size]
cut_height = (Z[K-M-1, 2] + Z[K-M, 2]) / 2                             # M개 군집이 되는 절단 높이(HTML cut_height와 같은 정의)
```

**6) 모델 묶음 재로드 검증과 manifest** — 저장한 pickle을 곧바로 다시 불러 (a) 벡터라이저의 단어 사전이 `vocab`과 같고 `transform(docs)`가 같은 DTM을 내는지, (b) 모델의 `components_`를 정규화한 값이 φ CSV와 허용오차 1e-7 안에서 같은지 확인한 뒤에야 manifest를 쓴다. 하나라도 어긋나면 스크립트가 멈춘다.

```python
vec_loaded = joblib.load("count_vectorizer_v7_final.pkl")
assert list(vec_loaded.get_feature_names_out()) == list(vocab)
assert (vec_loaded.transform(docs) != X).nnz == 0
lda_loaded = joblib.load(f"lda_model_k{K}_v7_final.pkl")
phi_loaded = lda_loaded.components_ / lda_loaded.components_.sum(axis=1, keepdims=True)
assert np.allclose(phi_csv, phi_loaded, atol=1e-7)
```

## 4. 결과 — K=10 (문서 9,954건, perplexity 3460.2)

### 토픽별 상위 단어와 문서 배정

`문서 수`는 θ의 argmax로 문서를 한 토픽에 배정했을 때의 건수다(합 = 문서 수).

| 토픽 | 상위 10단어 | 문서 수 |
|---|---|---|
| T0 | 수상, 부문, 올해, 박서진, 시상식, 에서, 8월, 팬덤, 아티스트, 10월 | 460 |
| T1 | 드라마, ost, 유튜브, 채널, 참여, 따르면, 영화, 공식, 문서, 에서 | 659 |
| T2 | 일본, 함께, 아랍어, 출연, 데뷔, 게임, 확인, 프랑스, 2026년, 멤버 | 650 |
| T3 | 일본, 보도, 공연, 매체, 기사, 대만, 콘서트, 투어, 소식, 인도네시아 | 1,301 |
| T4 | 콘서트, 2026년, 공연, 데뷔, 서울, 2025년, 단독, 팬클럽, 9월, 만에 | 1,521 |
| T5 | 출연, 예능, 무대, 함께, 출연해, 2026년, 에서, mbc, 방송, sbs | 1,050 |
| T6 | 기록, 1위, 발매, 앨범, 차트, 데뷔, 빌보드, 최초, k팝, 판매 | 1,151 |
| T7 | 브랜드, 광고, 모델, 앰버서더, 발탁, 캠페인, 글로벌, 활동, 홍보대사, 2024년 | 1,254 |
| T8 | fan, tour, concert, japan, sold, album, million, group, music, official | 1,113 |
| T9 | 보도, 공식, 태국, 매체, 팬들, 팬클럽, 팬덤, 필리핀, 브라질, 콘서트 | 795 |

### 토픽 간 코사인 거리 행렬

| | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **T0** | 0.000 | 0.883 | 0.797 | 0.890 | 0.846 | 0.845 | 0.843 | 0.890 | 0.981 | 0.885 |
| **T1** | 0.883 | 0.000 | 0.813 | 0.932 | 0.889 | 0.791 | 0.909 | 0.884 | 0.987 | 0.882 |
| **T2** | 0.797 | 0.813 | 0.000 | 0.641 | 0.682 | 0.638 | 0.832 | 0.749 | 0.974 | 0.809 |
| **T3** | 0.890 | 0.932 | 0.641 | 0.000 | 0.621 | 0.850 | 0.908 | 0.911 | 0.955 | 0.544 |
| **T4** | 0.846 | 0.889 | 0.682 | 0.621 | 0.000 | 0.792 | 0.841 | 0.835 | 0.990 | 0.770 |
| **T5** | 0.845 | 0.791 | 0.638 | 0.850 | 0.792 | 0.000 | 0.927 | 0.814 | 0.991 | 0.903 |
| **T6** | 0.843 | 0.909 | 0.832 | 0.908 | 0.841 | 0.927 | 0.000 | 0.927 | 0.985 | 0.947 |
| **T7** | 0.890 | 0.884 | 0.749 | 0.911 | 0.835 | 0.814 | 0.927 | 0.000 | 0.992 | 0.905 |
| **T8** | 0.981 | 0.987 | 0.974 | 0.955 | 0.990 | 0.991 | 0.985 | 0.992 | 0.000 | 0.980 |
| **T9** | 0.885 | 0.882 | 0.809 | 0.544 | 0.770 | 0.903 | 0.947 | 0.905 | 0.980 | 0.000 |

### M-grid 실루엣 (average linkage, precomputed cosine)

| M | 실루엣 | 토픽 → 군집 |
|---|---|---|
| 4 | 0.0688 | [2, 3, 0, 0, 0, 0, 2, 0, 1, 0] |
| 5 | 0.0682 | [0, 3, 2, 2, 2, 2, 0, 4, 1, 2] |
| 6 | 0.0608 | [5, 3, 0, 0, 0, 0, 2, 4, 1, 0] |
| 7 ★ | 0.0803 | [5, 3, 2, 0, 0, 2, 6, 4, 1, 0] |
| 8 | 0.0676 | [5, 7, 0, 2, 3, 0, 6, 4, 1, 2] |

최적 M=7, 절단 높이 0.7375. 잎 순서(왼→오): [8, 0, 6, 1, 7, 2, 5, 4, 3, 9]

### average-linkage 병합 기록

| id | left | right | height | size |
|---|---|---|---|---|
| 10 | 3 | 9 | 0.5438 | 2 |
| 11 | 2 | 5 | 0.6384 | 2 |
| 12 | 4 | 10 | 0.6955 | 3 |
| 13 | 11 | 12 | 0.7796 | 5 |
| 14 | 0 | 6 | 0.8426 | 2 |
| 15 | 7 | 13 | 0.8427 | 6 |
| 16 | 1 | 15 | 0.8652 | 7 |
| 17 | 14 | 16 | 0.8806 | 9 |
| 18 | 8 | 17 | 0.9816 | 10 |

## 5. 결과 — K=8 (문서 9,954건, perplexity 3512.6)

### 토픽별 상위 단어와 문서 배정

`문서 수`는 θ의 argmax로 문서를 한 토픽에 배정했을 때의 건수다(합 = 문서 수).

| 토픽 | 상위 10단어 | 문서 수 |
|---|---|---|
| T0 | 수상, 티켓, 만에, 콘서트, 판매, 이상, 매진, 기록, 부문, brand | 638 |
| T1 | ost, fan, japan, sold, album, million, music, group, official, chart | 818 |
| T2 | 일본, 보도, 데뷔, 최초, 한국, 영화, 아랍어, 함께, 콘서트, 확인 | 892 |
| T3 | 보도, 매체, 공연, 일본, 콘서트, 팬들, 기사, 태국, 소식, 대만 | 1,717 |
| T4 | 콘서트, 2025년, 공식, 팬클럽, 2026년, 데뷔, 서울, 공연, 8월, 9월 | 1,676 |
| T5 | 출연, 예능, 무대, 에서, 드라마, 2026년, 함께, 출연해, mbc, sbs | 1,387 |
| T6 | 1위, 기록, 앨범, 차트, 발매, tour, concert, 빌보드, 판매량, 데뷔 | 1,230 |
| T7 | 브랜드, 광고, 모델, 앰버서더, 발탁, 캠페인, 글로벌, 활동, 2026년, 홍보대사 | 1,596 |

### 토픽 간 코사인 거리 행렬

| | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|---|
| **T0** | 0.000 | 0.981 | 0.777 | 0.788 | 0.688 | 0.909 | 0.762 | 0.908 |
| **T1** | 0.981 | 0.000 | 0.967 | 0.972 | 0.991 | 0.966 | 0.948 | 0.991 |
| **T2** | 0.777 | 0.967 | 0.000 | 0.567 | 0.635 | 0.652 | 0.784 | 0.755 |
| **T3** | 0.788 | 0.972 | 0.567 | 0.000 | 0.651 | 0.854 | 0.928 | 0.877 |
| **T4** | 0.688 | 0.991 | 0.635 | 0.651 | 0.000 | 0.759 | 0.895 | 0.757 |
| **T5** | 0.909 | 0.966 | 0.652 | 0.854 | 0.759 | 0.000 | 0.948 | 0.760 |
| **T6** | 0.762 | 0.948 | 0.784 | 0.928 | 0.895 | 0.948 | 0.000 | 0.934 |
| **T7** | 0.908 | 0.991 | 0.755 | 0.877 | 0.757 | 0.760 | 0.934 | 0.000 |

### M-grid 실루엣 (average linkage, precomputed cosine)

| M | 실루엣 | 토픽 → 군집 |
|---|---|---|
| 4 ★ | 0.0694 | [1, 3, 1, 1, 1, 0, 2, 0] |
| 5 | 0.0439 | [0, 3, 0, 0, 0, 4, 2, 1] |
| 6 | 0.0464 | [5, 3, 0, 0, 0, 4, 2, 1] |
| 7 | 0.0295 | [5, 3, 0, 0, 6, 4, 2, 1] |

최적 M=4, 절단 높이 0.7847. 잎 순서(왼→오): [1, 6, 0, 4, 2, 3, 5, 7]

### average-linkage 병합 기록

| id | left | right | height | size |
|---|---|---|---|---|
| 8 | 2 | 3 | 0.5670 | 2 |
| 9 | 4 | 8 | 0.6431 | 3 |
| 10 | 0 | 9 | 0.7510 | 4 |
| 11 | 5 | 7 | 0.7604 | 2 |
| 12 | 10 | 11 | 0.8089 | 6 |
| 13 | 6 | 12 | 0.8749 | 7 |
| 14 | 1 | 13 | 0.9736 | 8 |

## 6. 동결 스냅샷(K=10)과의 대조

토픽 번호는 적합마다 임의로 매겨지므로 번호로 대응시킬 수 없다. 여기서는 **상위 10단어의 겹침 수**로 동결 토픽 K0∼K9마다 이 폴더 K=10에서 가장 가까운 토픽을 찾았다. 겹침 수는 기계적 지표이며 의미 대응을 보증하지 않는다.

| 동결 토픽 | 동결 상위 10단어 | 동결 F | 가장 가까운 T (겹침) | 그 T의 상위 10단어 |
|---|---|---|---|---|
| K0 음원차트기록형(1위·차트·발매·최초) | 기록, 1위, 발매, 차트, 데뷔, 최초, k팝, 그룹, 누적, 앨범 | F3 차트·확산형(1위·빌보드·기록) | T6 (8/10) | 기록, 1위, 발매, 앨범, 차트, 데뷔, 빌보드, 최초, k팝, 판매 |
| K1 해외현지보도형(보도·인도네시아·매체·무대) | 무대, 2026년, 보도, 8월, 기사, 인도네시아, 매체, 팬덤, 함께, 공연 | F0 현장경제형(콘서트·투어·매진) | T3 (5/10) | 일본, 보도, 공연, 매체, 기사, 대만, 콘서트, 투어, 소식, 인도네시아 |
| K2 예능출연형(출연·예능·mbc·sbs) | 출연, 예능, mbc, sbs, mc, kbs, kbs2, 고정, 공개, 출연해 | F2 미디어노출형(방송·조회수) | T5 (5/10) | 출연, 예능, 무대, 함께, 출연해, 2026년, 에서, mbc, 방송, sbs |
| K3 글로벌음반판매형(앨범·빌보드·일본·차트) | 앨범, 1위, 판매, 이상, 데뷔, 일본, 빌보드, 차트, 오리콘, ep | F3 차트·확산형(1위·빌보드·기록) | T6 (6/10) | 기록, 1위, 발매, 앨범, 차트, 데뷔, 빌보드, 최초, k팝, 판매 |
| K4 해외음반성과형(million·album·japan·chart) | million, album, japan, chart, music, copies, pop, group, korea, korean | F1 소비력형(초동·판매·앨범) | T8 (5/10) | fan, tour, concert, japan, sold, album, million, group, music, official |
| K5 팬클럽공식활동형(공식·팬클럽·유튜브·기부) | 공식, 팬클럽, 유튜브, 채널, 팬덤, 활동, 기부, 데뷔, 콘텐츠, 2025년 | F4 결속형(팬클럽·기부·커뮤니티) | T1 (3/10) | 드라마, ost, 유튜브, 채널, 참여, 따르면, 영화, 공식, 문서, 에서 |
| K6 단독콘서트투어형(콘서트·투어·단독·일본) | 콘서트, 공연, 보도, 투어, 단독, 데뷔, 일본, 개최, 태국, 월드투어 | F0 현장경제형(콘서트·투어·매진) | T3 (5/10) | 일본, 보도, 공연, 매체, 기사, 대만, 콘서트, 투어, 소식, 인도네시아 |
| K7 브랜드앰버서더형(브랜드·광고·앰버서더·발탁) | 브랜드, 모델, 광고, 앰버서더, 콘서트, 발탁, 매진, 티켓, 2025년, 글로벌 | F0 현장경제형(콘서트·투어·매진) | T7 (6/10) | 브랜드, 광고, 모델, 앰버서더, 발탁, 캠페인, 글로벌, 활동, 홍보대사, 2024년 |
| K8 월드투어브랜드형(tour·concert·brand·ambassador) | tour, concert, fan, sold, world, seoul, brand, ambassador, club, awards | F1 소비력형(초동·판매·앨범) | T8 (4/10) | fan, tour, concert, japan, sold, album, million, group, music, official |
| K9 미디어크로스오버형(드라마·ost·영화·수상) | 드라마, ost, 출연, 예능, 영화, 참여, 수상, 프로그램, 나무위키, mbc | F2 미디어노출형(방송·조회수) | T1 (4/10) | 드라마, ost, 유튜브, 채널, 참여, 따르면, 영화, 공식, 문서, 에서 |

| 구분 | 동결 스냅샷 | 이 폴더 K=10 |
|---|---|---|
| 코퍼스 / 문서 | 7,350건 / — | 10,020건 / 9,954건 |
| 최적 M / 실루엣 | 5 / 0.267 | 7 / 0.0803 |
| M=5 실루엣 | 0.267 | 0.0682 |
| 절단 높이 | 0.7736 | 0.7375 |
| 병합 높이(오름차순) | [0.4112, 0.5902, 0.6106, 0.715, 0.7446, 0.8027, 0.8869, 0.9236, 0.9823] | [0.543811, 0.638406, 0.695502, 0.779569, 0.842567, 0.842719, 0.865247, 0.880565, 0.981619] |
| 잎 순서 | [4, 8, 2, 9, 0, 3, 5, 7, 1, 6] | [8, 0, 6, 1, 7, 2, 5, 4, 3, 9] |

동결 스냅샷은 첫 병합 높이가 0.41로 낮고 M=5에서 실루엣 0.267을 내는 반면, 이 폴더의 K=10은 첫 병합이 0.54에서 시작하고 M=5 실루엣이 0.07 수준이다. 코퍼스가 2,670건 늘고 토크나이저가 다른 상태에서 같은 군집 구조가 나오지 않는다는 뜻이며, 이것이 보고서가 라이브 재적합을 실루엣 게이트로 기각하고 동결 스냅샷을 해석 계층으로 유지한 이유와 일치한다.

## 7. 모델 묶음 사용법

φ CSV만으로는 문서-토픽 분포 θ를 다시 만들 수 없으므로 학습 모델과 단어 사전을 같이 둔다. 문서는 `lda_document_index_v7_final.csv`의 순서대로 `run_lda_v6.py`의 `tokenize()`를 적용해 공백으로 이은 문자열이다.

```python
import ast, csv, json, re, joblib, numpy as np

# 1) 토크나이저 (3절 1단계와 같은 방법)
src = open("run_lda_v6.py", encoding="utf-8").read(); tree = ast.parse(src); ns = {"re": re}
exec("\n\n".join(ast.get_source_segment(src, n) for n in tree.body
     if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("PARTICLES", "STOPWORDS", "ENGLISH_STOPWORDS"))
     or (isinstance(n, ast.FunctionDef) and n.name == "tokenize")), ns)
tokenize = ns["tokenize"]

# 2) 문서를 저장된 순서로 복원
fandoms = {f["fandom"]: f for f in json.load(open("data/v7_final/fandoms_v3_100.json", encoding="utf-8"))}
rows = list(csv.DictReader(open("lda_document_index_v7_final.csv", encoding="utf-8-sig")))
docs = [" ".join(tokenize(fandoms[r["fandom"]][r["bullet_type"]][int(r["idx_in_fandom_array"])]["t"])) for r in rows]

# 3) 모델 묶음
vec = joblib.load("count_vectorizer_v7_final.pkl")
lda = joblib.load("lda_model_k10_v7_final.pkl")
X = vec.transform(docs)
theta = lda.transform(X)                                              # 문서 × 토픽, 행 합 1
phi = lda.components_ / lda.components_.sum(axis=1, keepdims=True)  # = lda_phi_k10_v7_final.csv
```

이 절차를 별도 프로세스에서 실행해 확인한 결과: 문서 9,954건이 그대로 복원되고 각 문서의 토큰 수가 CSV의 `n_tokens`와 일치하며, θ는 9,954×10·9,954×8로 행 합이 1이고, 각 토픽의 1위 단어가 `lda_phi_top50_*` CSV의 rank 1과 같다.

팬덤별 F 비중 같은 파이프라인 후속 단계(토픽→F 합산, loyalty/spillover 가중)는 `run_lda_v6.py` [4]절 이후를 θ에 그대로 적용하면 된다. 다만 이 폴더의 K·M은 동결 스냅샷과 다르므로 보고서의 F1∼F5 라벨을 그대로 붙이면 안 된다.

## 8. 재현 방법

```bash
# 저장소 루트(또는 안쪽 아무 폴더)에서
python v7_final_10020/analysis/persona_decision_space/topic_phi_cosine/build_topic_phi_cosine_v7.py
```

- 소요 시간 약 1∼3분(LDA 적합 K=10·K=8 각 30∼40초). 필요한 패키지: scikit-learn, scipy, numpy, joblib. 기록된 버전은 scikit-learn 1.9.1, scipy 1.17.1, numpy 2.4.6.
- 같은 버전에서는 CSV가 바이트 단위로 같게 나온다(마지막 실행에서 기존 CSV 10개가 변경 없이 재생성됨을 `git status`로 확인). 버전이 크게 다르면 마지막 자리 값이 달라질 수 있다.
- 스크립트는 `run_lda_v6.py`와 `data/v7_final/fandoms_v3_100.json`이 있는 폴더를 저장소 루트로 찾는다. 두 파일의 SHA-256은 manifest에 있어, 입력이 바뀌었는지 먼저 확인할 수 있다.
- pickle은 scikit-learn 객체이므로 버전이 다른 환경에서 불러오면 경고가 날 수 있다. 그때는 CSV(φ·단어 사전·문서 순서)만으로도 3절 3단계부터 다시 적합해 같은 결과를 얻을 수 있다.

## 9. 한계와 다음 단계

1. **동결 스냅샷의 φ·모델이 아니다.** 7,350건 코퍼스와 14개 언어 라우팅 토크나이저가 저장소에 없으므로, HTML 덴드로그램의 병합 높이([0.4112, 0.5902, 0.6106, 0.715, 0.7446, 0.8027, 0.8869, 0.9236, 0.9823])를 이 폴더의 값으로 재현할 수는 없다. HTML 덴드로그램 자체의 절단·군집·잎 순서 재현은 `../persona_decision_space_v7.ipynb` 2절이 HTML 기록값으로 한다.
2. 토픽 번호(T0∼T9)는 적합마다 임의로 매겨지므로 동결 스냅샷의 K0∼K9와 번호가 대응하지 않는다. 6절의 겹침 표는 참고용이다.
3. 토크나이저가 구판이라 문서 수(9,954)와 어휘가 공식 라이브 참고 재적합(10,018)과 다르다. 라우팅 토크나이저가 재구성되면 이 스크립트의 1단계만 바꿔 다시 돌린다.
4. **동결 모델 묶음을 추가할 때의 검증 기준** — 같은 파일 구성을 `frozen_v7_40/`에 만들고 다음이 전부 맞아야 한다: ① 토픽별 상위 10단어가 `lda_v6_diagnostics_frozen_v7_40.json`의 `topics_top_words`와 일치, ② 토픽→F 배정이 `topic_to_factor`와 일치, ③ M=5 실루엣 0.267·절단 높이 0.7736·병합 높이 [0.4112, 0.5902, 0.6106, 0.715, 0.7446, 0.8027, 0.8869, 0.9236, 0.9823]가 재현, ④ 팬덤별 F 비중이 `fandom_scores_v6.json`의 `factor_share`와 일치, ⑤ activity 합 7,350.

