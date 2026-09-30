# 김민석

**AI Agent Engineer (신입)**

LLM 응용 서비스를 만듭니다. 출력 검증과 사람 승인 단계를 설계해 **LLM을 실제 서비스에 안전하게 붙이는 일**에 집중하고 있습니다.

| | |
|:--|:--|
| **이메일** | [noviz2025@gmail.com](mailto:noviz2025@gmail.com) |
| **GitHub** | [noviz-domino](https://github.com/noviz-domino) |
| **LinkedIn** | [kim-min-seok-domino](https://www.linkedin.com/in/kim-min-seok-domino/) |
| **사이트** | [noviz-domino.github.io](https://noviz-domino.github.io/) |
| **생년월일** | 1998. 02. 01 |
| **병역** | 육군 만기 전역 |
| **현재** | 삼성 멀티캠퍼스 AI 에이전트 엔지니어 트랙 수강 중 (2026.07 ~ 2027.01) |

[라이브 데모](#라이브-데모) · [소개](#소개) · [핵심 성과](#핵심-성과) · [프로젝트](#프로젝트) · [그 외 프로젝트](#그-외-프로젝트) · [기술](#기술) · [학력 · 교육](#학력--교육) · [자격 · 수상](#자격--수상) · [English](README.en.md)

---

## 라이브 데모

| 프로젝트 | 무엇인지 | 링크 |
|:--|:--|:--|
| **금융 AI 에이전트** | 말로 하는 은행 업무, 승인 후에만 실행 | [웹 데모](https://noviz-bank.duckdns.org) |
| **englishWordApp** | 토익 단어 학습 Android 앱 | [Google Play](https://play.google.com/store/apps/details?id=com.voca.englishwordapp) |
| **mealmate** | AI 주간 식단 생성 | [웹 데모](https://mealmate-inky.vercel.app) |
| **가봐야 알지** | 시골 맛집 기록 · 데모 계정 `test1@goeat.test` / `test1234` | [웹 데모](https://go-eat-noviz.vercel.app) |
| **data-value-sandbox** | 데이터 가치 측정 시뮬레이션 | [웹 데모](https://noviz-domino.github.io/data-value-sandbox/) |
| **스쳐야 산다** | 브라우저 탄막 게임 | [바로 플레이](https://noviz-domino.github.io/cosmic-grazer/) |

모두 가상 데이터로 동작합니다. 무료 서버를 쓰는 데모는 첫 접속에 몇 초 걸릴 수 있습니다.

---

## 소개

컴퓨터정보보안을 전공했고, 지금은 삼성 멀티캠퍼스 AI 에이전트 엔지니어 트랙에서 **LLM · RAG · 멀티 에이전트**를 배우며 금융 도메인 과제를 중심으로 프로젝트를 진행하고 있습니다.

LLM은 그럴듯한 숫자를 지어낼 수 있습니다. 그래서 프로젝트마다 **LLM이 맡을 일과 코드·사람이 맡을 일을 나누고**, 그 경계가 지켜지는지 평가셋과 시나리오 테스트로 확인합니다. 실패한 시도와 설계를 바꾼 이유도 문서로 남깁니다.

AI 에이전트 외에도 Google Play에 출시한 Android 앱, 배포 중인 Next.js 웹 서비스 두 개를 혼자 만들어 운영해봤습니다. 필요한 영역이 있으면 직접 배워서 끝까지 완성하는 편입니다.

---

## 핵심 성과

| 성과 | 내용 | 프로젝트 |
|:--|:--|:--|
| **34% → 94%** | RAG 도입 후 AI 답변 초안의 1차 승인률. 답변 속 수치 정확률은 43.8% → 96.0% | replygate · 평가셋 50건 실측 |
| **47 / 47** | 잔액 부족·저장 실패·AI 서버 장애 등 실패 상황을 포함한 대화 시나리오에서 장부 무결성 유지 | langgraph-financial-agent |
| **188 → 4회** | 무료 API 한도 초과(429)를 해결하려고 필터·일일 상한·배치 요약으로 줄인 하루 LLM 호출 수 | n8n-finance-news-briefing |
| **Google Play 출시** | Kotlin·Compose로 전면 재작성한 토익 단어 앱. 퀴즈 로직을 JUnit 25건으로 고정 | englishWordApp |

---

## 프로젝트

*최신순. 모두 개인 프로젝트입니다.*

### langgraph-financial-agent · 대화형 은행 업무 AI 에이전트
`2026.09` · KDT 과제 · **완성 · 배포 중**

"생활비에서 저축으로 10만 원 보내줘" 같은 말을 이해해 계좌 조회·이체·카드 잠금을 처리합니다. 돈이나 카드 상태가 바뀌는 일은 사용자 승인을 받은 뒤에만 실행합니다.

- **설계** - LLM은 말을 해석하는 노드 한 곳에서만 사용하고, 잔액 계산·검사·저장·답변 문장은 모두 코드로 처리해 숫자가 LLM을 거치지 않게 했습니다.
- **안전장치** - LangGraph `interrupt`로 승인 전 실행을 멈추고, 저장은 무결성 규칙 10개를 통과해야만 한 번에 교체되도록(atomic write) 구현했습니다.
- **검증** - 실패 상황을 포함한 대화 시나리오 47개를 자동으로 돌려 전부 통과했고, 설계 변경 27건을 이유와 함께 기록했습니다.
- **문제 해결** - 프롬프트로 금지해도 LLM이 출금 계좌를 지어내는 것을 발견해, 규칙을 LLM 응답을 코드가 검증하는 방식으로 바꿨습니다.

`LangGraph` `LangChain` `Gemini` `FastAPI` `Python 3.13` `Oracle Cloud`

| 이체 요청 → 승인 카드 | 승인 후 잔액 변화 |
|:--:|:--:|
| <img src="projects/langgraph-financial-agent/docs/images/02-confirm.png" alt="이체 승인 카드" width="400" /> | <img src="projects/langgraph-financial-agent/docs/images/03-done.png" alt="승인 후 잔액 변화" width="400" /> |

[직접 써보기](https://noviz-bank.duckdns.org) · [원본 저장소](https://github.com/noviz-domino/langgraph-financial-agent) · [설계 변경 기록](projects/langgraph-financial-agent/docs/설계변경기록.md)

### legal_secretary · 노동법 조문 인용 RAG 비서
`2024.09 ~ 11` 캡스톤, `2026.09 ~` 재구축 · 졸업논문 주제 · **재구축 3 / 6단계**

법률 질문에 관련 조문을 찾아 근거와 함께 답합니다. 2024년 캡스톤 버전을 기획·개발·인프라까지 단독으로 만들었고, 2026년에 구조를 전면 재구축하고 있습니다.

- **재구축 이유** - "민감한 법률 문서라 로컬 LLM을 쓴다"는 설계와 달리 실제로는 질문이 외부 터널을 거쳐 나가고 있던 문제를 스스로 찾아냈습니다.
- **검색** - "근로기준법 제56조"처럼 정확히 일치해야 하는 표현을 놓치지 않도록 조문 단위로 나누고, 키워드(BM25)와 의미(벡터) 검색을 합쳤습니다.
- **응답** - 근거 조문을 답변보다 먼저 보내는 스트리밍(SSE)으로, 느린 무료 API(실측 8.8초)에서도 사용자가 기다리지 않게 했습니다.

`FastAPI` `LangChain` `Chroma` `BM25` `bge-m3` `SSE`

[코드](projects/legal_secretary/) · [재구축 계획](projects/legal_secretary/docs/리빌딩계획.md)

### mealmate · 냉장고 재료 기반 AI 주간 식단 생성
`2026.08 ~ 09` · **배포 · 라이브 데모**

재료를 입력하면 AI가 주간 식단과 장보기 목록을 만들고, 끼니별 조리법은 필요할 때 생성합니다.

- **출력 검증** - AI 출력 형식을 스키마로 강제한 뒤에도 구조를 다시 검사하고, 실패하면 한 번 재생성합니다.
- **알레르기** - 우유를 피하는 사람에게 연유·생크림이 나오지 않도록 파생 재료까지 차단했습니다.
- **보안** - Supabase RLS로 사용자별 데이터를 격리했습니다. TypeScript 약 3,200줄을 3일 동안 개발했습니다.

`Next.js 16` `React 19` `TypeScript` `Supabase` `Gemini` `Vercel`

| 공개 식단 | AI가 만든 식단 | 끼니별 조리법 |
|:--:|:--:|:--:|
| <img src="projects/mealmate/docs/screenshots/01-홈-공개식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/05-AI가만든식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/06-AI가만든조리법.png" width="240" /> |

[라이브 데모](https://mealmate-inky.vercel.app) · [코드](projects/mealmate/)

### replygate · AI 초안 + 사람 승인 고객 응대 자동화
`2026.08` · KDT 미니프로젝트 · **완성 · 실측 평가**

고객 문의가 오면 AI가 사내 정책 문서를 근거로 답변 초안을 쓰고, 담당자가 텔레그램에서 승인해야만 메일이 발송됩니다.

- **설계** - 틀리면 분쟁이 되는 수치(환불 수수료·배송 기한) 때문에 자동 발송 대신 사람 승인 단계를 두었습니다.
- **성과** - 평가셋 50건 기준 1차 승인률을 34% → 94%, 수치 정확률을 43.8% → 96.0%로 개선했습니다. 정책에 답이 없는 함정 질문 5건도 포함했습니다.
- **문제 해결** - 감정 분류에서 한 클래스가 전혀 선택되지 않는 원인이 두 기준을 하나로 섞은 데 있음을 찾아, 두 축으로 분리해 정확도 98% / 92%를 얻었습니다.

`n8n` `Gemini` `RAG` `FastAPI` `Telegram Bot`

<img src="projects/replygate/docs/screenshots/텔레그램-정책충돌-감지.png" alt="담당자의 수정 지시가 정책과 충돌하자 경고를 띄운 텔레그램 승인 카드" width="320" />

[코드](projects/replygate/) · [평가셋 설계](projects/replygate/eval/)

### englishWordApp · 토익 단어 학습 Android 앱
`2026.06 ~ 08` · **Google Play 출시**

뜻을 가리고 외우는 학습, 진행도 이어보기, TTS 발음, 오답노트, 4지선다 퀴즈를 제공합니다. 단어 1,222개.

- **재작성** - 직접 만든 Java 버전의 문제(뜻이 항상 보임, 1,225행 중 835행에 따옴표 노출, 화면 회전 시 진행도 초기화)를 Kotlin·Compose로 전면 재작성해 해결했습니다.
- **품질** - 퀴즈 출제 로직을 순수 함수로 분리해 JUnit 테스트 25건으로 고정하고, 앱이 종료됐다 다시 켜져도 학습 위치를 복원합니다.

`Kotlin` `Jetpack Compose` `JUnit` `Android`

| 홈 | 단어 학습 | 퀴즈 |
|:--:|:--:|:--:|
| <img src="projects/englishWordApp/docs/brand/play-store/capture/main.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/word.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/game.png" width="200" /> |

[Google Play](https://play.google.com/store/apps/details?id=com.voca.englishwordapp) · [코드](projects/englishWordApp/)

---

## 그 외 프로젝트

| 기간 | 프로젝트 | 기술 | 링크 |
|:--|:--|:--|:--|
| 2026.09 | **multi-agent-tax-prep** - 종합소득세 신고 준비 멀티 에이전트 (리서치·계획·검토). LLM 없이 도는 테스트 57개 | LangGraph · Gemini | [코드](projects/multi-agent-tax-prep/) |
| 2026.09 | **rag-experiment-script** - 설정 20개로 청킹·검색·리랭킹을 비교한 RAG 실험. 하이브리드 검색 Page Hit@1 0.943 (기준 0.886) | LangChain · Chroma · BM25 | [코드](projects/rag-experiment-script/) |
| 2026.08 ~ 09 | **personal-budget-ai-agent** - 자연어로 쓰는 가계부 에이전트 (도구 7개) | Gemini Function Calling | [코드](projects/personal-budget-ai-agent/) |
| 2026.08 ~ 09 | **가봐야 알지 (go-eat)** - 시골 맛집 기록 웹앱, 8시간 제약 개발 | Next.js · Supabase | [데모](https://go-eat-noviz.vercel.app) · [코드](projects/go-eat/) |
| 2026.08 | **n8n-finance-news-briefing** - 금융 뉴스 자동 요약 브리핑. 하루 API 호출 188회 → 4회 | n8n · Gemini · Discord | [코드](projects/n8n-finance-news-briefing/) |
| 2026.08 | **n8n-voc-analysis-agent** - 고객 VOC 자동 분류·긴급 알림 | n8n · Gemini · Sheets | [코드](projects/n8n-voc-analysis-agent/) |
| 2026.07 ~ 08 | **스쳐야 산다 (cosmic-grazer)** - 단일 HTML 파일 탄막 서바이버 게임 | Vanilla JS · Canvas2D | [플레이](https://noviz-domino.github.io/cosmic-grazer/) · [코드](projects/cosmic-grazer/) |
| 2026.07 | **대통령: 외교의 신 (god-of-diplomacy)** - Gemini 기반 정치·외교 텍스트 RPG | FastAPI · Gemini | [코드](projects/god-of-diplomacy/) |
| 2026.04 ~ 09 | **data-value-sandbox** - 합성 세계로 "어떤 데이터가 사건을 예측 가능하게 하는가" 측정. 표적 추론 top-1 51.5% (기준선의 3.81배) | deck.gl · Jupyter | [데모](https://noviz-domino.github.io/data-value-sandbox/) · [저장소](https://github.com/noviz-domino/data-value-sandbox) |
| 2021.12 | **GTD 테러예측모델** - 글로벌 테러 데이터 분석·예측 (2인 팀) | Python · Scikit-learn | [저장소](https://github.com/noviz-domino/gtd-terror-analysis-project) |

---

## 기술

| 분야 | 프로젝트에서 사용 |
|:--|:--|
| **AI · Agent** | LangGraph · LangChain · Gemini API · Function Calling · Structured Output · n8n |
| **RAG · 검색** | Chroma · BM25 · 하이브리드 검색(RRF) · Reranking · 평가셋 설계 |
| **Backend** | FastAPI · Flask · Supabase · PostgreSQL · MySQL |
| **Frontend · Mobile** | Next.js · React · Tailwind CSS · Jetpack Compose |
| **Language** | Python · C · TypeScript · JavaScript · Kotlin |
| **Infra · Tool** | Git · GitHub Actions · Vercel · Oracle Cloud · Ollama · Linux · Claude Code |
| *학습했지만 프로젝트 사용 경험은 없음* | *Java · PyTorch · TensorFlow · Alibaba Cloud* |

---

## 학력 · 교육

**삼성 멀티캠퍼스 · AI 에이전트 엔지니어 트랙 1회차** · `2026.07 ~ 2027.01` · *수강 중*
984시간 · 금융 AI 서비스 개발을 실습 축으로 하는 과정

| 단위기간 | 주제 | 관련 결과물 |
|:--|:--|:--|
| 1 | LLM · 프롬프트 · n8n | replygate · n8n-voc-analysis-agent · n8n-finance-news-briefing |
| 2 | Python AI 웹개발 · LangChain | personal-budget-ai-agent · rag-experiment-script |
| 3 | LangGraph · MCP · 멀티 에이전트 | langgraph-financial-agent · multi-agent-tax-prep |
| 4 ~ 6 | RAG 시스템 설계 · 프로덕션(Docker·AWS·CI/CD) · 종합 프로젝트 | *예정* |

**우송대학교** · 컴퓨터정보보안학과 · `2017.03 ~ 2026.03` · 수료

**베이징이공대학** · 공동학위과정 · `2019.03 ~ 2024.01` · 중퇴 · 다국적 팀 프로젝트 수행

매일의 학습 기록: [TIL 저장소](https://github.com/noviz-domino/TIL)

---

## 자격 · 수상

| 시기 | |
|:--|:--|
| 군 복무 중 | **C4I 체계 전산운용 1위** - 대한민국 육군 정보통신학교 준장 표창 |
| 2026.03 | TOEIC 545 |
| 보유 | 초경량비행장치 1급 (드론) |
| 준비 중 | 정보처리기사 · 정보보안기사 실기 |

---

이 저장소는 프로젝트별 소스 코드와 설계 문서를 `projects/` 아래에 모은 것입니다. 원본 저장소는 대부분 비공개라서, 여기 있는 사본은 민감정보를 뺀 것입니다. AI 코딩 도구를 운용한 방식은 [docs/agent-workflow.md](docs/agent-workflow.md)에 정리했습니다.

<sub>최종 수정 2026-09-30 · [정돈 기록](docs/CHANGELOG.md)</sub>
