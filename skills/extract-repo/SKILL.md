---
name: extract-repo
description: 저장소 하나(로컬 디렉토리 또는 원격 주소)를 끝까지 읽어 자소서·이력서·포트폴리오의 소재가 될 수 있는 모든 것을 근거와 함께 재료로 적는다. career/repos/<slug>/ 에 쌓이고, 실행 중 묻지 않는다.
disable-model-invocation: true
---

# 저장소에서 재료 뽑기

리포를 끝까지 읽고 소재가 될 가능성이 있는 것을 **전부** 재료로 적는다. 고르는 일은 이 스킬 뒤의 일이라 애매한 것도 적는다. 리포로 못 밝힌 것은 `확인 필요` 칸에 적고 끝까지 간다.

리포 한 장의 모양은 [`references/repo.md`](references/repo.md), 재료의 축·사건·칸과 `candidates.md`의 모양은 [`references/candidates.md`](references/candidates.md)가 정한다. `<스킬>`은 이 `SKILL.md`가 있는 디렉토리의 절대 경로다.

## 0. 자리

입력은 리포 하나 — 로컬 디렉토리 경로 또는 원격 주소. 데이터 디렉토리에서 실행한다(`career-setup/references/layout.md` #0). `<slug>`는 원격이면 `<owner>-<repo>` 소문자, 로컬뿐이면 디렉토리 이름이다.

- **원격**이면 `gh repo clone <url> cache/repos/<slug>`로 받고, 이미 있으면 `git -C cache/repos/<slug> pull -q --ff-only`. `gh auth status`가 실패하면 공개 리포만 `git clone`으로 받고 PR·이슈 단계는 `확인 필요`로 남긴다.
- **로컬**이면 그 디렉토리가 리포다. `git remote get-url origin`이 GitHub 주소면 원격과 같이 `gh`를 쓴다.

`career/repos/<slug>/artifacts/{git,gh}/`를 만든다. `repo.md`가 이미 있으면 `identities`·`gh_login`·`last_commit`을 읽어 둔다 — 이번 실행은 그 커밋 뒤만 훑어 덧붙인다.

**완료 조건:** 리포 디렉토리에서 `git rev-parse HEAD`가 나오고, `artifacts/git/`·`artifacts/gh/`가 있다.

## 1. 본인 식별

`repo.md`에 `identities`가 있으면 그대로 쓴다. 없으면 리포의 `git config user.email`, 전역 `git config --global user.email`, `gh api user -q .login`(로그인돼 있을 때)을 모아 `git -C <리포> shortlog -sne HEAD`의 저자 목록과 맞춘다. 같은 사람의 이메일이 여럿이면(이름이 같거나 noreply 주소가 같은 로그인 이름을 담고 있으면) 전부 넣는다.

**완료 조건:** `identities`에 저자 목록과 맞은 이메일이 있거나, 맞는 것이 없어 비어 있고 그 사실을 `repo.md`의 `확인 필요`에 적었다.

## 2. 사실 뽑기

```
python3 <스킬>/scripts/repo_facts.py <리포> --out career/repos/<slug>/artifacts/git [--since <last_commit>] --author <이메일>...
```

`summary.json`(리포 한 장의 사실과 흔적 표지)과 `commits.json`(커밋마다 본문·트레일러·바뀐 파일·되돌림·본인 여부)이 생긴다.

`gh`가 되면 같은 자리의 `gh/`에 받는다. `<owner/repo>`는 `gh repo view --json nameWithOwner -q .nameWithOwner`다.

```
gh pr list -R <owner/repo> --state all --limit 500 --json number,title,body,author,createdAt,mergedAt,closedAt,state,commits,files,additions,deletions,labels,reviews,comments,url > career/repos/<slug>/artifacts/gh/prs.json
gh issue list -R <owner/repo> --state all --limit 500 --json number,title,body,author,createdAt,closedAt,state,labels,comments,url > career/repos/<slug>/artifacts/gh/issues.json
```

본인이 저자이거나 리뷰어인 PR 중 `reviews`나 `comments`가 있는 것은 인라인 리뷰도 받는다 — `gh api --paginate repos/<owner/repo>/pulls/<n>/comments > career/repos/<slug>/artifacts/gh/reviews/<n>.json`.

**완료 조건:** `artifacts/git/summary.json`·`commits.json`이 있고, `gh`가 되는 리포면 `gh/prs.json`·`gh/issues.json`이 있고 리뷰가 있는 본인 PR마다 `gh/reviews/<n>.json`이 있다.

## 3. 리포 한 장

`repo.md`를 `references/repo.md` 모양으로 쓴다. `summary.json`의 `readme_head`·매니페스트·파일 분포·저자·태그와, 리포의 README·`docs/`·도메인 코드를 직접 열어 채운다. 도메인 용어는 코드에서 이름으로 쓰인 것만 표에 올리고 경로를 단다.

**완료 조건:** 절 여섯이 다 있고, 절마다 근거(경로·번호)가 붙었거나 `없음`·`~`가 적혔고, frontmatter의 `identities`·`gh_login`·`scanned_at`이 채워졌다.

## 4. 재료

`commits.json`·`prs.json`·`issues.json`·`reviews/`를 읽고 `candidates.md` #2대로 **사건**으로 묶는다. 사건마다 리포의 실제 파일·diff(`git -C <리포> show <sha>`)를 열어 #3의 칸 일곱을 채우고 해당 축 절에 적는다. 축 일곱은 #1의 "어디에 남나"를 전부 대어 훑고, 누구의 것을 뽑는지는 #4다.

이전 실행이 있으면 번호는 `count + 1`부터 잇고 기존 건은 그대로 둔다.

**완료 조건:** 절 여덟(축 일곱 + 함께 한 것)이 다 있고, 재료마다 근거가 하나 이상 있고, 본인 커밋(`mine: true`)과 본인 PR·이슈 전부가 어느 재료의 근거에 들어갔거나 `그 밖`에 적혔고, `count`와 `C<n>`의 마지막 번호가 같다.

## 5. 마무리

`repo.md`의 `last_commit`을 `summary.json`의 `head`로, `candidates.md`의 `runs`에 이번 줄을 붙인다. 출력은 세 줄이다 — 두 파일의 경로, 축별 재료 수, `확인 필요`가 붙은 건수.

**완료 조건:** `last_commit`이 HEAD와 같고, 출력이 세 줄이다.
