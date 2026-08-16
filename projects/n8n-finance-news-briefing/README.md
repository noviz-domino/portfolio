# 금융 뉴스 브리핑 Agent

멀티캠퍼스 AIM 2주차 미니프로젝트2 제출 리포지토리입니다.

매일 아침 8시 30분, 여러 뉴스 매체의 기사 중 금융 관련 기사만 골라 요약하고 중요도를 매겨 디스코드로 자동 발송하는 n8n 워크플로우입니다.

## 문서

| 파일 | 내용 |
| --- | --- |
| [미니프로젝트2_김민석.md](./미니프로젝트2_김민석.md) | **제출 문서** — 요구사항 체크, 판단 근거, 테스트 결과 |
| [docs/00_개발요청서.md](./docs/00_개발요청서.md) | 원본 개발 요청서 |
| [docs/01_개발기획서.md](./docs/01_개발기획서.md) | 상세 개발 기획서 (노드 설계, 프롬프트, 근거) |
| [docs/02_구축가이드.md](./docs/02_구축가이드.md) | 처음부터 끝까지 구축 절차 |
| [workflow/finance_news_briefing.json](./workflow/finance_news_briefing.json) | n8n 워크플로우 (import 가능) |

## import 후 필수 설정

워크플로우 JSON에는 자격증명·웹훅 URL·스프레드시트 ID가 플레이스홀더로 되어 있습니다. n8n에 import한 뒤 아래를 채워야 동작합니다.

1. `이력 조회` / `이력 기록` — Google Sheets 자격증명 + 스프레드시트 ID
2. `Gemini Chat Model` — Google Gemini API 자격증명
3. `Discord 발송` — 실제 Discord 웹훅 URL
4. Workflow Settings → Timezone = `Asia/Seoul`

자세한 절차는 [구축 가이드](./docs/02_구축가이드.md)를 참고하세요.

## 요구사항 요약

| 항목 | 처리 |
| --- | --- |
| RSS 수집 | 연합뉴스·한국경제·매일경제 3개 |
| 중복 발송 방지 | 정리한 URL의 SHA-256 해시로 대조, LLM 호출 이전 차단 |
| 금융 키워드 필터 | LLM 앞에 배치 (비용 절감) |
| LLM 요약/중요도 | Gemini + Structured Output, 중요도 4 이상만 발송 |
| 발송 | 여러 기사를 메시지 1개로 묶어 Discord 발송, 0건인 날도 구분 가능 |
| 이력 기록 | Google Sheets에 자동 누적 |
