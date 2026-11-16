# 김민석 | AI Engineer

금융 문서 RAG와 업무 에이전트를 설계·구현하는 신입 개발자입니다. 문서의 근거를 보존하고 AI의 판단을 권한·승인·검증 흐름에 연결합니다.

[포트폴리오 사이트](https://noviz-domino.github.io/) · [GitHub](https://github.com/noviz-domino) · [학습 기록](https://github.com/noviz-domino/TIL) · noviz2025@gmail.com

## 먼저 볼 프로젝트

| 프로젝트 | 집중한 문제 | 역할과 근거 |
|---|---|---|
| [캡아메리카뱅크](https://github.com/noviz-domino/avengers-bank-noviz) | AI 상담을 권한·PIN 승인·중복 방지와 연결 | 팀 기획 후 개인 구현·고도화. [사례](docs/case-studies/capamerica.md) |
| [금융 문서 RAG Agent](https://github.com/noviz-domino/financial-rag-agent) | 복잡한 PDF의 근거 보존과 과다 거절 개선 | 3인 팀. 전처리·Agent 구조·설정 비교 중심. [사례](docs/case-studies/rag.md) |
| [ReplyGate](projects/replygate/) | 정책 근거가 있는 초안과 사람 승인 후 발송 | 개인 프로젝트. [사례](docs/case-studies/reply.md) |

## 최근 작업

| 기간 | 작업 | 현재 범위 |
|---|---|---|
| 2026.11 | [Kick the Tires](https://ktt-w66x.axhub.app) | 삼일PwC AX 인재전쟁 W08. 가상 기업 인수 실사의 근거·조건·상신 흐름. 질의 발송·의결은 모의 처리 |
| 2026.10 - 11 | [Contest Radar](https://contest-radar-eta.vercel.app) | 수집·요약·중복 판정, 필터·캘린더·북마크. 11월 북마크 전용 보기·Paper 테마 반영. 코치는 로컬 MVP |
| 2026.10 - 현재 | KIC AI 에이전트 공모전 | 개인 참가. 대회 기간 코드·상세 자료 비공개 |
| 2026.11 | AWS 검색 배포 실습 | FastAPI·Docker Compose·EC2·RDS·pgvector 연결 실습 |
| 2026.11 | Agent Command | C# 코어와 규칙 기반 CLI. LLM 실행·게임 화면 미구현 |

## 기술과 경험

- **주로 사용하는 기술:** Python, FastAPI, LangGraph, LangChain, Gemini, MCP, PostgreSQL.
- **문서 검색:** PDF 전처리, BM25 + 벡터 검색, Chroma·pgvector, 청킹·RAG 평가. Parent-Child RAG 설정 비교, 관계 그래프 기반 조사 설계 경험.
- **제품 구현:** Next.js·TypeScript, Kotlin·Jetpack Compose, n8n.
- **실행과 검증:** Docker, GitHub Actions, Oracle Cloud, LangSmith·Langfuse. EC2·RDS는 배포 실습 경험.
- **교육:** 멀티캠퍼스 AI 에이전트 엔지니어 트랙, 2026.07 - 2027.01 수강 중.

## 이전 프로젝트와 소스 보관본

`projects/`는 공개 가능한 이전 프로젝트의 보관본입니다. 독립 저장소가 있는 작업은 위 링크의 최신 저장소를 우선 확인해 주세요. 모든 프로젝트를 같은 완성도나 운영 상태로 소개하지 않습니다.

| 분야 | 프로젝트 |
|---|---|
| Agent | [대화형 은행 업무](https://github.com/noviz-domino/langgraph-financial-agent), [종합소득세 신고 준비](projects/multi-agent-tax-prep/), [가계부](projects/personal-budget-ai-agent/) |
| RAG | [노동법 비서](projects/legal_secretary/), [검색 설정 비교 실험](projects/rag-experiment-script/) |
| 자동화 | [금융 뉴스 브리핑](projects/n8n-finance-news-briefing/), [VOC 분석](projects/n8n-voc-analysis-agent/) |
| 웹·앱 | [식단 생성](projects/mealmate/), [맛집 기록](projects/go-eat/), [토익 단어 앱](projects/englishWordApp/) |
| 기타 | [데이터 가치 실험](https://github.com/noviz-domino/data-value-sandbox), [Cosmic Grazer](projects/cosmic-grazer/), [외교 텍스트 RPG](projects/god-of-diplomacy/) |

## 수치 읽는 법

성과 수치는 각 프로젝트의 기록을 인용한 것으로, 이번 문서 갱신에서 모델 평가를 다시 실행한 결과가 아닙니다. 평가셋·비교 조건·미달 목표를 사례에 함께 적었습니다. 가상 금융 데이터와 공모전 사례를 실제 고객 성과로 해석하지 않습니다.

제출용 이력서·포트폴리오·자기소개서는 별도의 비공개 저장소에서 관리합니다. 공개 저장소에는 개인 전화번호와 제출 문서를 포함하지 않습니다.

마지막 내용 검토: 2026-11-16
