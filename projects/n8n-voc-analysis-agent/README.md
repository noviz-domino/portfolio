# 고객 VOC 분석 Agent

종합 쇼핑몰 고객 문의(VOC)를 Google Form으로 접수해 n8n + Gemini로 자동 분류하고,
긴급건만 Discord로 알리는 무인 파이프라인. AIM 2주차 미니프로젝트 1.

```
Google Form → Google Sheet → n8n (Loop → 중복확인 → Gemini 분류 → 검증 → 저장 → 긴급분기) → Discord
```

## 폴더 구조

```
mini1/
├── README.md                          이 파일
├── 미니프로젝트1_김민석.md               구현 설명서 (제출용 요약)
├── docs/
│   ├── 00_개발요청서.md                 원본 요청서 (수정하지 않음)
│   ├── 01_기획서.md                    전체 기획 · 준비물 · 테스트 계획 · 검수표
│   ├── 02_워크플로우_상세설계.md          노드별 설정값 · 전체 코드 · 트러블슈팅
│   └── 03_개발일지.md                  개발 진행 기록 (질의응답 · 오류 · 해결 과정)
└── workflow/
    └── voc-agent-workflow.json        n8n 최종 워크플로우 (Ctrl+V로 붙여넣는 파일)
```

## 어디서부터 읽나

| 하려는 일 | 볼 문서 |
| --- | --- |
| 전체 구현 요약만 빠르게 | `미니프로젝트1_김민석.md` |
| 전체 그림 파악, Form/Sheet/Discord 준비 | `docs/01_기획서.md` 1~7장 |
| n8n 워크플로우 만들기 | `docs/02_워크플로우_상세설계.md` A장 → 바로 붙여넣기 |
| 특정 노드 설정값 확인 | `docs/02_워크플로우_상세설계.md` C장 |
| 안 돌아갈 때 | `docs/02_워크플로우_상세설계.md` F장 (트러블슈팅) |
| 제출 전 자체 점검 | `docs/01_기획서.md` 9~10장 (시나리오 · 검수표) |
| 실제로 겪은 오류와 해결 과정 | `docs/03_개발일지.md` |

## 기술 스택

| 항목 | 선택 |
| --- | --- |
| 자동화 | n8n Cloud |
| LLM | Google Gemini (`gemini-2.5-flash`, temperature 0) |
| 저장소 | Google Sheets (원본 응답 탭 / 분석결과 탭) |
| 알림 | Discord Webhook |

## 시작하기

1. `docs/01_기획서.md` 3장의 준비물 표(P1~P8)를 채운다
2. Google Form(4항목) + `분석결과` 시트 탭을 만든다 — 4·5장
3. Discord Webhook을 발급하고 `curl`로 단독 테스트한다 — 6장
4. `workflow/voc-agent-workflow.json` 을 n8n 캔버스에 붙여넣고 Credential·시트ID·Webhook URL을 지정한다 (플레이스홀더 `YOUR_...` 값들을 본인 값으로 교체)
5. **Active 토글을 켠다** (이걸 잊으면 폼 제출에 반응하지 않는다)
6. `docs/01_기획서.md` 9-2장 시나리오 S1~S6 실행 → 10장 검수표 체크

> ⚠️ Gemini API 키와 Discord Webhook URL은 비밀값입니다. 이 저장소의 어떤 파일에도 적지 말고 n8n Credential / 노드 설정에만 넣으세요.
