# 개발자가 자소서·이력서·포트폴리오에 어필할 것

2026-09-09 웹 리서치. 공고 인용 원문은 [`postings.md`](postings.md), 출처 목록은 [`sources.md`](sources.md) 에 있다. `[P#]` 는 공고 번호, `[S#]` 는 출처 번호다.

조사 방법: 웹 검색 + 원문 fetch. 국내 공고는 점핏 공개 API(`jumpit-api.saramin.co.kr`)와 원티드 공개 API에서 2026-08-29~09-09 게시분을 직접 뽑았다. 해외 공고는 Greenhouse·Lever·HN Who is hiring 에서 뽑았고, 원문 접근이 차단된 것(403/404)은 검색 스니펫 기준임을 표시했다.

## 1. 요약

1. 기본은 바뀌지 않았다. 국내 인사담당자 조사에서 신입 채용 1순위는 실무 경험(39.8%), 2026 인재상 1순위는 직무 전문 역량(64.7%)이고, AI 활용 역량은 4위(24.2%)·신입 기준 7.0%다 [S1][S2].
2. 이력서 문장은 "요구사항 → 기술 → 어떻게 해결 → 수치"가 합격 이력서의 공통 형식이다 [S3][S4].
3. AI 도구 사용 자체는 이제 신호가 아니라 기본값이다. 전문 개발자 90%가 주 1회 이상 에이전트를 쓰고 68%가 매일 쓴다 [S7]. "쓸 줄 안다"는 문장은 소음이다.
4. 신호가 되는 것은 **검증**이다. 국내 공고 원문에 "그 결과를 검증하는 자기기준"(바로팜), "AI 생성 코드 검증·운영 적용 역량"(대원씨티에스), "AI가 생성한 코드와 정보를 직접 검증"(디오에프)이 자격·우대로 적혀 있다 [P1][P5][P7].
5. 해외 공고도 같다. CoderPad는 "delegation, context scoping, and review of AI-generated code 에 대한 judgment"를, Elevance는 "review, test, and harden AI-generated code"를 요구한다 [P17][P20].
6. 에이전트용 인프라(MCP·eval·프롬프트 파이프라인·에이전트가 다루기 좋은 코드베이스)를 설계한 경험은 우대 항목으로 실제 등장한다 [P2][P4][P8][P10].
7. 면접은 AI 사용을 허용하는 쪽으로 이동 중이나 아직 62%가 금지한다 [S13]. 허용하는 곳은 코드가 아니라 "문제 분해·과정 수정·검증"을 본다 [S12][S14].
8. 감점은 AI 사용이 아니라 **설명 못 하는 산출물**과 **개인화 없는 AI 문장**에 붙는다 [S16][S17][S18].
9. 해커뉴스·Ghostty 류의 강경한 시각도 실재한다. "쓸 거면 잘 써라, 못 쓰면 밴"이다 [S16].
10. 리포지토리에서 자동으로 뽑을 수 있는 증거는 (A)의 절반, (B)의 대부분이다. 검증 습관은 테스트·CI·PR 설명·에이전트 설정 파일에 남는다 (#5).

## 2. (A) 기본 어필 요소

| 요소 | 맞는 문서 | 근거 | 리포에서 증거 |
|---|---|---|---|
| 실무 경험(실제 배포·운영한 것) | 이력서·포폴 | 신입 채용 1순위 39.8% [S1]; "실제 결과물로 증명해야" [S5] | 부분 — 배포 설정·릴리스 태그·운영 이슈는 보이나 실제 트래픽은 안 보임 |
| 직무 전문 역량(스택 깊이) | 이력서 | 2026 인재상 1위 64.7% [S2]; Google RRK [S6] | 가능 — 언어·프레임워크·의존성·코드 |
| 수치 있는 성과 | 이력서·자소서 | 합격 이력서 "수치 데이터 필수", 예 "react-query 도입(코드량 30% 감소)" [S3]; "results, impact and your contribution" [S4] | 부분 — 커밋·PR 본문에 적어 두었을 때만 |
| 문제→기술→해결 서술 | 자소서·포폴 | 합격 이력서 3요소 "어떤 요구사항을, 어떤 기술을 사용해서, 구체적으로 어떻게 해결했는지" [S3] | 가능 — PR 설명·ADR·이슈 스레드 |
| 협업·커뮤니케이션 | 자소서 | 인재상 2위 팀워크 37.9% [S2]; 신입 3위 커뮤니케이션 22.3% [S1]; 조직적합성 검증 67% [S8] | 부분 — 리뷰 코멘트·이슈 응답 톤, 1인 리포면 불가 |
| 주도성·오너십 | 자소서 | Google "leadership … stepped up, took ownership" [S6]; 조직 기여 의지 28.1% [S2] | 부분 — 이슈 직접 열고 닫은 이력, 유지보수 기간 |
| 배운 것·기술의 장단점 판단 | 자소서·포폴 | 주니어 팁 "배움을 통해 얻은 인사이트, 특정 기술의 장단점" [S3] | 가능 — ADR·README 의 결정 근거, 롤백 커밋 |
| 디버깅·시스템 설계·정확성 검증 | 포폴·면접 | Anthropic 면접 설계가 보는 것 "tough debugging, systems design, … verify the correctness" [S9] | 가능 — 버그 수정 커밋+회귀 테스트, 설계 문서 |
| 조직 적합성(인성·책임감) | 자소서 | 면접관 414명 중 67%가 1순위 [S8] | 불가 |

## 3. (B) AI 에이전트 활용 개발자의 추가 어필 요소

| 요소 | 맞는 문서 | 근거 | 리포에서 증거 |
|---|---|---|---|
| AI 산출물 검증 기준을 갖고 있음 | 이력서·포폴 | 공고 원문 [P1][P5][P7][P20]; "you'll be expected to use it well and verify its output rather than just accept it" [P15]; 30%가 AI 코드를 거의 신뢰 안 함 [S10]; 46% 불신 [S11] | 가능 — AI 생성 커밋 뒤의 테스트 추가·수정 커밋, PR 의 "검증 방법" 절 |
| 위임 범위 판단(무엇을 맡기고 무엇은 직접 하나) | 자소서·면접 | CoderPad "judgment on delegation, context scoping" [P17]; Anthropic 내부 조사 "fully delegate 0-20%" [S19]; Rootly "problem decomposition" [S12] | 부분 — 커밋 단위·PR 크기, 세션 로그를 남겼을 때만 |
| 컨텍스트·프롬프트 설계 | 포폴 | 전문가 판별 신호 "how precisely the user frames their directions, what they ask Claude to verify, whether the user corrects Claude" [S20]; 우대 "프롬프트 파이프라인" [P2] | 가능 — CLAUDE.md·AGENTS.md·.cursor/rules·스킬 파일 |
| 에이전트용 문서·코드베이스 정비 | 포폴 | "AI agent가 다루기 좋은 코드베이스·도구(MCP, eval, 프롬프트 파이프라인 등)를 설계" [P2]; Uncountable "context files … sit in the folder you are touching" [S21] | 가능 — 위 파일 + 디렉토리별 컨텍스트 파일, 린트·타입 강화 이력 |
| 평가(evals) 설계 | 이력서·포폴 | Honeycomb "Familiarity with eval frameworks" [P10]; Anthropic "shared tools and evals" [P11]; Uncountable "eval harnesses" [S21] | 가능 — evals 디렉토리, 골든 케이스, CI 에서 eval 실행 |
| 도구 제작(MCP 서버·에이전트 훅·스킬) | 포폴 | 공고 [P4][P8][P10]; "judgment about how to invest in tooling is part of the signal" [S9] | 가능 — MCP 서버 코드, 훅 스크립트, 스킬 디렉토리 |
| AI 산출물에 대한 책임(내가 설명한다) | 자소서·면접 | Ghostty "If you use AI, you are responsible for the quality of your contributions" [S16]; Rootly 나쁜 신호 "accepting output without verification" [S12] | 부분 — PR 본문에 AI 사용 범위와 직접 검토한 부분을 밝힌 이력 |
| 생산성 개선을 도입한 경험 | 이력서 | 씨어스 "생성형 AI 도구를 실무 개발·운영 프로세스에 도입하여 생산성을 개선한 경험" [P3]; Shopify "reflexive AI usage is now a baseline" [S22] | 부분 — 자동화 스크립트·CI 단계 추가 커밋, 효과 수치는 본문에만 |
| 에이전트 시스템 이해(LLM 호출·툴콜·RAG) | 이력서 | 연합인포맥스 "에이전트·LLM 시스템 감각 (MCP·Function Calling·RAG)" [P4]; 포밸류 [P8] | 가능 — 해당 코드 |

### 감점 시각

| 상황 | 근거 | 대응 |
|---|---|---|
| AI 로 만든 코드를 본인이 설명 못 함 | Ghostty 정책: 나쁜 AI 기여는 "immediately banned", "you better be good" [S16]; "if you can't answer technical questions about the AI-generated code … liability" [S18] | 포폴에는 설명할 수 있는 것만. 회고에 "왜 이 설계인지"를 직접 씀 |
| 개인화 없는 AI 문체 자소서 | HR 925명 조사에서 62%가 개인화 없는 AI 이력서를 거절 가능성 높다고 답함 [S17]; 49% 자동 탈락 주장은 2차 통계 사이트에서만 확인 [S17] | 구체 사건·수치·고유명사로 채움. 문체보다 내용 |
| 면접에서 금지된 AI 를 몰래 씀 | 400개 조직 중 62%가 기술 면접에서 AI 금지, 절반 넘는 후보가 지시 무시 추정 [S13] | 규칙 확인 후 씀. 허용되면 "왜 이 프롬프트를 썼는지"를 말로 설명 |
| 검토 없는 대량 PR·"바이브 코딩" 자랑 | 오픈소스 "AI slop": curl 버그바운티 중단, tldraw 외부 PR 자동 종료 [S23]; SO 66% "almost right but not quite" 가 최대 불만 [S11] | 규모가 아니라 검증 흔적을 보임. 한 PR 에 테스트·롤백 근거 |
| 신뢰가 낮은 조직에서 AI 사용을 앞세움 | 경력 많은 개발자가 가장 불신(highly distrust 20%) [S11]; 면접관 조사 1순위는 여전히 인성·책임감 67% [S8] | 도구 이름을 전면에 두지 않고 결과와 검증을 앞세움 |
| 주니어의 성장 정체 의심 | Anthropic 엔지니어 "skills atrophying as they delegate more", 주니어에게 "deliberate effort" 필요 [S19] | 직접 짠 부분과 위임한 부분을 구분해 적음 |

## 4. 리포지토리에서 뽑을 수 있는 증거

| 증거 | 어디서 | 뒷받침하는 요소 |
|---|---|---|
| 테스트 파일 수·커버리지 변화 | 테스트 디렉토리, 커버리지 리포트, CI 로그 | (A) 정확성 검증, (B) AI 산출물 검증 |
| AI 생성 커밋 직후의 수정·테스트 추가 커밋 | 커밋 히스토리(Co-Authored-By 트레일러, 커밋 간격) | (B) 검증 기준, 위임 범위 판단 |
| CI 설정(lint·type check·test·eval 단계) | `.github/workflows`, 기타 CI 파일 | (A) 실무 경험, (B) 검증 자동화·eval |
| 커밋 메시지의 범위·이유 서술 | `git log` | (A) 문제→기술→해결 서술 |
| PR 설명의 "검증 방법"·"AI 사용 범위" 절 | PR 본문 | (B) 책임, 검증 기준 |
| 이슈 트리아지(라벨, 재현 단계, 닫은 사유) | 이슈 트래커 | (A) 오너십·커뮤니케이션 |
| README 의 실행 방법·설계 결정 | README, docs | (A) 배운 것·기술 판단 |
| ADR 또는 결정 기록(이 리포는 `docs/rationale.md`) | docs | (A) 기술 장단점 판단, (B) 컨텍스트 설계 |
| 릴리스 노트·태그 | 릴리스, CHANGELOG | (A) 실무 경험(배포 이력) |
| 에이전트 설정 파일(CLAUDE.md, AGENTS.md, `.claude/`, `.cursor/rules`, 스킬) | 리포 루트·하위 디렉토리 | (B) 컨텍스트·프롬프트 설계, 에이전트용 문서 |
| MCP 설정·서버 코드, 훅 스크립트 | `.mcp.json`, `.claude/settings.json`, 스크립트 | (B) 도구 제작 |
| evals 디렉토리·골든 케이스 | 리포 내 | (B) 평가 설계 |
| 롤백·되돌림 커밋과 그 이유 | 커밋 히스토리 | (A) 기술 판단, (B) 검증 결과에 따른 수정 |
| 리뷰 코멘트의 톤·근거 | PR 리뷰 | (A) 협업 — 1인 리포면 불가 |

못 뽑는 것: 실제 사용자 수·매출 같은 운영 수치, 조직 적합성, 면접에서의 설명 능력. 이건 본문과 면접에서만 보인다.
