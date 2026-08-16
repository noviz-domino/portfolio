<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# 프로젝트 현황 — 가봐야 알지 (GoEat)

새 세션을 시작하면 아래 두 문서를 먼저 읽어라. 다른 건 안 읽어도 된다.

- `docs/기획서.md` — 무엇을 만드는지 (서비스 정의, 테이블, 화면, 안 만들 것)
- `docs/개발일지.md` — 지금까지 뭘 했는지, 왜 그렇게 결정했는지 (시간순, 이어서 추가하는 파일)

`docs/이게_다_뭐하는_건가요.md`, `docs/회고.md`, `docs/가장오래막혔던문제와해결과정.md`는
과제 제출·초보자 설명용이라 개발 작업에는 안 봐도 된다.

## 현재 상태 (2026-08-04 기준)

- 배포: https://go-eat-noviz.vercel.app (Vercel, main 브랜치 자동 배포)
- 저장소: https://github.com/noviz-domino/go-eat (main)
- 8시간 기획 분량(CRUD, 검색/필터, 로딩·에러 화면, 디자인) 전부 완료
- Gemini API로 맛집 메모 자동 요약 기능 추가 완료 (목록엔 요약, 상세엔 원문)
- 테스트 계정: `test1@goeat.test` / `test1234` (삭제하지 말 것)
- 미착수: (선택) Pinterest 참고 디자인 개선

## 작업 습관

- 코드 작성 전 `docs/개발일지.md`에서 관련 결정 이유를 먼저 확인한다.
- 큰 작업은 TaskCreate로 세부 목록을 쪼개서 진행 상황을 추적한다.
- 작업 끝나면 `docs/개발일지.md`에 새 항목을 이어서 추가하고, 커밋·푸시·배포 확인까지 마친다.
