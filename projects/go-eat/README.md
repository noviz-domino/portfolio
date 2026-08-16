<div align="center">

<img src="public/logo-hero.png" alt="가봐야 알지" width="360" />

# 가봐야 알지 (go-eat)

**검색해도 안 나오는 시골 맛집을, 직접 가보고 직접 기록하는 앱**

[![라이브 데모](https://img.shields.io/badge/라이브_데모-go--eat--noviz.vercel.app-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://go-eat-noviz.vercel.app)

![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)

</div>

---

## 왜 만들었나

도시에는 맛집 데이터가 넘친다. 리뷰도, 사진도, 평점도 있다. **그런데 시골에는 아예 없다.** 검색해도 안 나오고, 나와도 몇 년 전 글 하나가 전부다.

그래서 시골에서는 검색으로 맛집을 찾는 게 불가능하다. 직접 가보고, 직접 기록하는 것 말고는 방법이 없다.

이 앱은 **남의 리뷰를 모으는 서비스가 아니라, 내가 가본 곳을 내가 기록하는 도구**다.

> 멀티캠퍼스 과정 실습으로 **8시간 제약** 안에서 개발했다. 기능을 어디까지 넣고 어디서 자를지가 이 프로젝트의 실질적인 과제였다.

## 데모 계정

로그인 없이도 둘러볼 수 있지만, 등록/수정을 해보려면 아래 계정을 쓰면 된다.

```
이메일   test1@goeat.test
비밀번호  test1234
```

## 기능

- **맛집 등록 · 조회 · 수정 · 삭제**
- **필터** — 방문 여부, 별점, 카테고리
- **검색** — 이름 검색, 디바운스 적용
- **진행률 바** — "가봐야지" 목록 중 몇 곳을 실제로 가봤는지. 필터와 무관하게 전체를 집계한다
- **AI 메모 요약** — 길게 쓴 메모를 Gemini가 한 줄로 줄여준다
- **사용자별 데이터 격리** — Supabase RLS

## 이 프로젝트에서 신경 쓴 것

### 클라이언트가 보낸 값을 믿지 않는다

맛집을 등록할 때 `user_id`를 클라이언트에서 받지 않는다. **서버 액션이 세션에서 직접 확정한다.**

클라이언트가 보낸 `user_id`를 그대로 저장하면, 요청을 조작해서 **남의 계정 이름으로 데이터를 심을 수 있다.** RLS를 켜두더라도 애초에 서버가 신뢰할 수 없는 값을 쓰면 안 된다.

→ [`src/app/actions/restaurants.ts`](src/app/actions/restaurants.ts)

### AI가 실패해도 저장은 성공해야 한다

메모 요약은 **부가 기능**이다. Gemini 호출이 실패했다고 맛집 등록 자체가 실패하면 안 된다.

그래서 요약 함수는 실패 시 예외를 던지지 않고 `null`을 반환한다. 요약이 없으면 없는 대로 저장이 진행된다.

→ [`src/app/actions/ai.ts`](src/app/actions/ai.ts)

**부가 기능이 핵심 기능을 망가뜨리지 않게 하는 것**은 기능을 추가할 때마다 확인해야 할 부분이라고 생각한다.

### 필터 상태를 URL에 둔다

검색어와 필터를 컴포넌트 상태가 아니라 **URL 쿼리 파라미터**로 관리한다. 그래야 새로고침해도 유지되고, 링크를 그대로 공유할 수 있다.

→ [`src/app/page.tsx`](src/app/page.tsx)

### 봐야 할 파일

| 파일 | 역할 |
|---|---|
| [`src/app/actions/restaurants.ts`](src/app/actions/restaurants.ts) | CRUD 서버 액션. 권한 처리의 핵심 |
| [`src/app/actions/ai.ts`](src/app/actions/ai.ts) | Gemini 메모 요약. 실패 허용 설계 |
| [`src/proxy.ts`](src/proxy.ts) | 로그인 유지와 비로그인 리다이렉트 |
| [`src/app/page.tsx`](src/app/page.tsx) | 목록 화면. URL 기반 필터 상태 |

## 막혔던 문제들

자세한 기록은 [`docs/가장오래막혔던문제와해결과정.md`](docs/가장오래막혔던문제와해결과정.md)에 있다.

**프로젝트 생성부터 실패했다.** 폴더 이름을 `맛집실습`으로 만들었는데, npm 패키지명은 URL에 쓸 수 있는 소문자 문자만 허용한다. 한글 폴더명 안에서는 `create-next-app`이 아예 돌지 않았다. **개발 도구가 파일 시스템에 거는 제약을 처음 체감한 사례였다.**

**등록해도 목록이 안 바뀌었다.** 페이지가 빌드 시점에 정적(`○`)으로 굳어서, 새 데이터를 등록해도 미리 만들어둔 HTML이 계속 나왔다. `export const dynamic = "force-dynamic"`으로 요청마다 렌더링하게 바꿔 해결했다. **Next.js가 언제 정적으로 만들고 언제 동적으로 두는지 알아야 한다는 걸 알게 됐다.**

**재시도 버튼이 안 눌렸다.** Next.js 16에서 에러 바운더리의 `reset()`이 `unstable_retry()`로 이름이 바뀌었다. 이름이 바뀐 걸 모르면 버튼은 렌더링되는데 아무 일도 안 일어난다.

## 기술 스택

| 구분 | 사용 |
|---|---|
| 프레임워크 | Next.js 16.2 (App Router), React 19.2, TypeScript |
| 스타일 | Tailwind CSS 4, Pretendard |
| 데이터 | Supabase (PostgreSQL + Auth + RLS) |
| AI | Google Gemini (`gemini-flash-lite-latest`) |
| 배포 | Vercel |

## 실행 방법

```bash
npm install
cp .env.example .env.local   # 아래 값들을 채운다
npm run dev
```

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
GEMINI_API_KEY=
```

## 문서

| 문서 | 내용 |
|---|---|
| [기획서](docs/기획서.md) | 요구사항과 화면 설계 |
| [개발일지](docs/개발일지.md) | 작업 기록 |
| [가장 오래 막혔던 문제](docs/가장오래막혔던문제와해결과정.md) | 트러블슈팅 |
| [회고](docs/회고.md) | 8시간 개발을 마치고 |
| [라이브 데모 유지](docs/라이브데모_유지.md) | Supabase 무료 플랜 자동 정지 방지 |

---

개인 프로젝트 · 8시간 제약 개발 · 커밋 33개
