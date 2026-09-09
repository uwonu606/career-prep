# 데이터 디렉토리

스킬을 실행하는 **현재 작업 디렉토리**다. 툴킷 리포(`career-prep`)가 아니라 개인 데이터가 사는 곳이고, 모든 스킬은 여기서 `./career`·`./.env`·`./auth`를 상대 경로로 찾는다. `career-setup`이 만든다.

## 0. 경로

경로는 리포 밖 `~/.config/career-prep/data-dir` 한 줄(절대 경로)이 소유한다 — `career-setup`이 실행된 디렉토리를 거기 적는다. 스킬은 작업 디렉토리에 `career/`가 있으면 거기서 돌고, 없으면 그 파일의 경로로 옮겨 시작한다. 둘 다 없으면 `career-setup`을 안내한다.

## 1. 자리

| 자리 | 무엇 | 쓰는 것 | 읽는 것 |
|---|---|---|---|
| `career/` | 직무 조사·리포 재료 | `research-role`·`extract-repo` | 전부 |
| `cache/repos/<slug>/` | 원격 리포의 클론. 지워도 다시 받으면 된다 | `extract-repo` | `extract-repo` |
| `.env` | 키. 한 줄에 하나, `이름=값` | 사용자가 직접 편집 | 스크립트만 — `dart_fetch.py` |
| `auth/<host>.json` | 로그인 상태(쿠키·스토리지) | `browser.py login` | `browser.py open`만 |
| `fixtures/dart/` | 사업보고서 파서 회귀 픽스처. 파서를 고칠 때 만든다 | `research-role` 파서 수정 | `test_extract.py <이 경로>` |
| `.gitignore` | `.env`·`auth/`·`cache/`가 커밋되지 않게 | `career-setup` | git |
| `~/.config/gh/` (디렉토리 밖) | GitHub 로그인. 있는지는 `gh auth status` 종료 코드로 본다 | `gh auth login` | `extract-repo` — 비공개 리포 클론, PR·이슈·리뷰 |

`.env`와 `auth/`는 **있는지만** `ls`로 본다. 내용은 그 행의 스크립트만 읽는다.

## 2. 키

| 이름 | 여는 것 | 발급 | 확인 |
|---|---|---|---|
| `DART_API_KEY` | `research-role` 뻗기의 DART 절(`extend.md` #1) | https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do — 개인용 즉시 발급, 무료, 1인 1키 | `python3 <research-role 스킬>/scripts/dart_fetch.py "카카오" --check`가 종료 0 |

새 키가 필요해지면 이 표에 행을 붙인다. 읽는 스크립트는 `.env`의 그 줄만 읽는다.

## 3. 로그인 상태

`auth/<host>.json`은 `<career-setup 스킬>/scripts/browser.py login <url>`이 남기고 `open <url>`이 쓴다 — 명령과 옵션은 `--help`. 호스트는 `www.`를 뗀 이름이고, 상위 도메인 파일이 하위 도메인에도 맞는다 — `linkedin.com` 파일은 `kr.linkedin.com`에 쓰인다.

`open`이 로그인 페이지로 돌아오면 만료다 — 같은 URL로 `login`을 다시 하면 있던 상태를 물려받아 열린다.

로그인이 여는 것은 그 호스트를 사용자 계정으로 **페이지 하나씩** 여는 것까지다. 조사에서 언제 열고 출처에 무엇을 적는지는 `research-role/references/access.md` #2가 정한다.
