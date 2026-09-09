---
name: career-setup
description: 개인 데이터 디렉토리를 만들고 키(.env)·로그인 상태(auth/)·브라우저·GitHub 로그인을 준비한다. 스킬을 처음 쓰기 전과, 새 키나 새 로그인이 필요해졌을 때 쓴다.
disable-model-invocation: true
---

# 준비하기

다른 스킬들이 읽는 자리를 한 번 만든다. 자리의 규약은 [`references/layout.md`](references/layout.md)가 소유하고 다른 스킬은 그 파일을 가리킨다. 키와 로그인 상태의 **내용은 읽지 않는다** — 파일이 있는지만 본다. `<스킬>`은 이 `SKILL.md`가 있는 디렉토리의 절대 경로다.

## 0. 디렉토리

현재 작업 디렉토리가 데이터 디렉토리가 된다. `plugin.json`이나 `skills/`가 있으면 툴킷 리포이니 멈추고, 개인 데이터를 둘 디렉토리로 옮겨 다시 실행하라고 한다. 없는 것만 만든다 — `career/`·`auth/`·`fixtures/dart/`, 그리고 `.env`·`auth/`·`cache/`를 담은 `.gitignore`. 그 다음 이 디렉토리의 절대 경로를 `~/.config/career-prep/data-dir`에 한 줄로 적는다(`layout.md` #0) — 이미 다른 경로가 적혀 있으면 바꿀지 사용자에게 묻는다.

**완료 조건:** 세 디렉토리가 있고, `.gitignore`에 `.env`·`auth/`·`cache/` 줄이 있고, `~/.config/career-prep/data-dir`이 이 디렉토리를 가리킨다.

## 1. 키

`layout.md` #2 표의 키마다 발급 URL과 `.env` 한 줄 모양을 보여주고, 사용자가 직접 적게 한다. `.env`가 생겼으면 `python3 <research-role 스킬>/scripts/dart_fetch.py "카카오" --check`로 키가 통하는지 본다 — 종료 5는 키 없음·무효. 키를 안 만들겠다고 하면 그대로 다음이다 — 키 없음은 `research-role` 뻗기의 DART 각도만 비운다.

**완료 조건:** 표의 키마다 "통함" 또는 "안 둠"이 정해졌다.

## 2. 브라우저

`uv run --quiet <스킬>/scripts/browser.py list`. 종료 3이면 크로미움이 없다 — 화면의 설치 명령을 사용자에게 보여주고 다시 돈다.

**완료 조건:** `list`가 종료 0이다(`auth/` 비어 있음도 된다).

## 3. 로그인

자기 계정으로 열게 할 사이트를 사용자에게 묻는다 — 로그인 뒤에 있는 페이지가 조사에 쓰이는 곳(링크드인·원티드 같은 채용·평판 사이트). 사이트마다 사용자가 자기 터미널에서 실행한다:

    ! uv run --quiet <스킬>/scripts/browser.py login <로그인 페이지 URL>

창이 뜨고, 로그인하고 창을 닫으면 `auth/<host>.json`이 남는다. 다시 `list`로 확인한다. 로그인이 곧 그 호스트를 자기 계정으로 한 페이지씩 열어도 된다는 허락이고, 계정 제한 위험은 사용자의 것이다 — `layout.md` #3을 한 번 보여준다.

**완료 조건:** 사용자가 든 호스트마다 `list`에 줄이 있다.

## 4. GitHub

`gh auth status`가 종료 0이면 끝이다. 아니면 사용자가 자기 터미널에서 실행한다:

    ! gh auth login

`gh`가 없으면 설치 안내(https://cli.github.com)를 보여주고 다시 돈다. 로그인 상태는 `gh`가 제 자리(`~/.config/gh/`)에 두고 데이터 디렉토리에는 아무것도 남지 않는다 — `layout.md` #5. 안 하겠다고 하면 그대로 끝이다 — `extract-repo`가 비공개 리포를 못 받고 PR·이슈를 못 읽을 뿐, 로컬 디렉토리는 그대로 된다.

**완료 조건:** `gh auth status`가 종료 0이거나, 사용자가 "안 둠"을 골랐다.
