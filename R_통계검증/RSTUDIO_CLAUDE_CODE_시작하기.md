# RStudio + Claude Code 연동 — 시작하기

Windows(이 PC: `programming`) + RStudio 기준.

---

## 먼저 알아 둘 것: RStudio 전용 확장은 없다

Claude Code가 공식 지원하는 IDE는 **VS Code**와 **JetBrains** 두 가지다. 인라인 diff,
선택 영역 참조 같은 기능은 그 두 곳에서만 된다. **RStudio용 확장은 없다.**

그래서 방법이 세 가지로 갈린다. 이 프로젝트에는 **A안**을 권한다.

| | 방법 | 얻는 것 | 잃는 것 |
|---|---|---|---|
| **A** | RStudio **Terminal 탭**에서 `claude` 실행 | Plots 창·Environment·콘솔 전부 그대로. 설치 5분 | 인라인 diff 없음 (터미널 안에서 diff는 보임) |
| **B** | **Positron**(Posit의 VS Code 기반 IDE) + VS Code 확장 | 인라인 diff + R 콘솔·Plots 창 | Positron이 RStudio와 다른 IDE. 확장 동작은 공식 문서에 명시 없음 |
| **C** | VS Code + R 확장 | 완전한 Claude Code 연동 | RStudio를 떠나야 함 |

A안이 좋은 이유는 **Plots 창을 그대로 쓴다**는 점이다. `RUN_ALL.R` 은 그림을 Plots
창에 띄우도록 만들어 뒀으니, Terminal 탭의 Claude Code가 코드를 고치고 → 당신이
Source 눌러 Plots 창에서 확인하는 흐름이 끊기지 않는다.

---

## 0단계 — Claude Code 없이, raw 데이터만 있을 때

원본 아카이브 폴더(또는 zip)만 있고 R만 깔려 있으면 **`START.bat` 더블클릭**으로 끝난다.
원본을 자동으로 찾아 `data/` 를 채우고(JSON 7개) 검증 238개 + 플롯 7종을 돌린다.
못 찾으면 원본 폴더를 `START.bat` 위로 끌어다 놓는다. RStudio에서는 `SETUP_DATA.R`
Source → `RUN_ALL.R` Source. 아래 A안은 그 위에 Claude Code를 얹는 단계다.

---

## A안 설치 (5분)

### 1단계 — Claude Code 설치

**PowerShell**을 열고:

```powershell
irm https://claude.ai/install.ps1 | iex
```

설치 후 PowerShell을 **닫고 다시 열어야** `claude` 명령이 잡힌다. 확인:

```powershell
claude --version
```

> Node.js가 이미 있다면 `npm install -g @anthropic-ai/claude-code` 도 되지만,
> 위 네이티브 설치가 권장 방식이다.

### 2단계 — Git for Windows 설치 (권장)

Claude Code는 Windows에서 **Git Bash가 있으면 그것을, 없으면 PowerShell을** 셸로 쓴다.
Git Bash 쪽이 훨씬 안정적이다. https://git-scm.com/download/win

이미 설치했는데 못 찾는다면 `C:\Users\mw595\.claude\settings.json` 에:

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### 3단계 — RStudio에서 프로젝트 열기

이 폴더의 **`팬덤100_통계검증.Rproj`** 를 더블클릭한다. RStudio가 열리면서 작업
디렉터리가 이 폴더로 잡힌다 — `data/` 탐색이 항상 성공한다.

### 4단계 — Terminal 탭에서 Claude Code 켜기

RStudio 좌측 하단, **Console 옆의 `Terminal` 탭**을 누른다. (없으면
`Tools > Terminal > New Terminal`, 또는 `Alt`+`Shift`+`M`)

```bash
claude
```

작업 디렉터리가 이미 프로젝트 폴더이므로 `cd` 는 필요 없다. 첫 실행 시 로그인
안내가 나온다.

### 5단계 — 확인

Claude Code에 이렇게 입력해 본다:

```
RUN_ALL.R 을 실행해서 238개 대조가 전부 일치하는지 확인해줘
```

`합계 238 238 0` 이 나오면 연동 완료다.

---

## 실제 작업 흐름

```
 RStudio 한 화면
 ┌──────────────────────┬──────────────────────┐
 │ Source (RUN_ALL.R)   │ Environment / History│
 │ ← Claude Code가 고침  │                      │
 ├──────────────────────┼──────────────────────┤
 │ Console / Terminal   │ Plots  ← 그림 확인    │
 │ └ claude 실행 중      │ Files / Packages     │
 └──────────────────────┴──────────────────────┘
```

1. **Terminal 탭**에서 Claude Code에게 요청 — "fig4의 라벨이 겹쳐, 고쳐줘"
2. Claude Code가 `RUN_ALL.R` 을 수정
3. RStudio가 **바뀐 파일을 자동으로 다시 읽는다** (에디터에 반영됨)
4. **Source 버튼**(Ctrl+Shift+S)을 눌러 직접 실행 → **Plots 창**에서 확인
5. 마음에 안 들면 다시 1번

Claude Code가 `Rscript RUN_ALL.R` 로 직접 실행할 수도 있지만, 그러면 PNG만 나오고
Plots 창에는 안 뜬다. **그림을 눈으로 볼 때는 당신이 Source를 누르는 게 낫다.**

---

## 편의 설정

### 매번 실행 허락 묻지 않게 하기

이 폴더에 `.claude/settings.json` 을 미리 넣어 뒀다. `Rscript`/`R` 실행은 허용,
**`data/` 폴더 수정은 차단**해 뒀다(원본 아카이브이므로).

직접 조정하려면 세션 안에서 `/permissions` 를 입력하거나, 권한 질문이 뜰 때
**"Yes, and don't ask again"** 을 고르면 이 파일에 자동으로 기록된다.

### 수정 후 자동으로 검증 돌리기 (선택)

파일을 고칠 때마다 238개 대조를 자동으로 다시 돌리고 싶다면 `.claude/settings.json`
의 `permissions` 와 나란히 다음을 추가한다.

```json
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "Rscript RUN_ALL.R" }
        ]
      }
    ]
  }
```

전체 실행이 약 4초라 부담은 적다. 다만 플롯까지 매번 다시 그리므로, 검증만 돌리려면
`Rscript R/verify_all.R` 로 바꾸면 된다.

### 세션 다시 붙기

```bash
claude --continue      # 직전 대화 이어서
claude --resume        # 목록에서 골라서
```

RStudio를 닫았다 열어도 대화는 남는다.

---

## CLAUDE.md — 새 세션이 프로젝트를 알고 시작하게 하기

이 폴더의 **`CLAUDE.md`** 를 Claude Code가 **세션 시작할 때 자동으로 읽는다.**
그래서 새 세션을 열어도 처음부터 설명할 필요가 없다.

거기에 미리 적어 둔 것:

- 코퍼스 트랙이 둘이라는 것 (섞으면 값이 전부 달라짐)
- **대조 실패를 기댓값 고쳐서 통과시키지 말 것** — 불일치는 버그가 아니라 발견
- `data/` 는 읽기 전용
- 이미 발견해 기록한 문서-데이터 불일치 2건 (버그로 오인하지 않도록)
- ggplot 규칙과 `ggrepel` 이 회귀선을 모른다는 함정
- **한글을 변수명으로 쓰면 `source()` 에서 파싱 실패**한다는 것
- Windows 맑은 고딕 + cairo 장치 문제
- 3.8절 한계와 `run_lda_v6.py` 위치

무엇이 로드됐는지는 세션에서 `/context` 를 입력하면 **Memory files** 항목에서 확인할
수 있다.

메모리는 계층이다 — 가까운 것이 우선한다.

| 위치 | 범위 |
|---|---|
| `C:\Users\mw595\.claude\CLAUDE.md` | 모든 프로젝트 (개인 취향·말투 등) |
| `<이 폴더>\CLAUDE.md` | **이 프로젝트** ← 지금 이 파일 |
| `<이 폴더>\CLAUDE.local.md` | 개인용, git에 안 올라감 |

---

## B안 — Positron을 쓰고 싶다면

Positron은 Posit(RStudio 만든 회사)이 만든 **VS Code 기반** R·Python IDE다. R 콘솔과
Plots 창이 RStudio처럼 있으면서 VS Code 확장을 쓸 수 있다.

Claude Code VS Code 확장이 Positron에서 도는지는 **공식 문서에 명시돼 있지 않다.**
VS Code 기반이라 될 가능성이 높지만 보장은 없다. 시도 순서:

1. Positron 설치 → 확장 탭에서 `Claude Code` 검색
2. 없으면 Open VSX 또는 VSIX 직접 설치 시도
3. 그래도 안 되면 Positron의 Terminal에서 `claude` — **A안과 똑같이 동작한다**

즉 최악의 경우에도 A안으로 되돌아오면 되므로 위험은 없다.

---

## 막히면

| 증상 | 확인할 것 |
|---|---|
| `claude` 명령을 못 찾음 | 터미널을 닫고 다시 열기. RStudio도 재시작 |
| 터미널 화면이 깨짐 | `Tools > Global Options > Terminal` 에서 셸을 Git Bash로 |
| 한글 입력이 안 먹힘 | Claude Code를 Windows Terminal에서 따로 띄우고 RStudio는 편집·Plots 전용으로 |
| 그림 한글이 네모 | `[2/6]` 이 찍는 `폰트:` 줄 확인. 계산 238개에는 영향 없음 |
| `data/` 를 못 찾음 | `.Rproj` 로 열었는지 확인. 또는 `Session > Set Working Directory > To Source File Location` |
| `[3/6]` 직후 `unexpected symbol` 로 멈추거나 콘솔 한글이 깨짐 | R이 UTF-8 로케일인데 CP949로 강제 전환된 것. `RUN_ALL.R` [2/6] 의 `Sys.setlocale` 줄이 `!isTRUE(l10n_info()$"UTF-8")` 조건을 갖고 있는지 확인 (CLAUDE.md 5절 참고) |

공식 문서: https://code.claude.com/docs
