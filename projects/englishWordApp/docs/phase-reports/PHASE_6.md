# Phase 6 — 4지선다 퀴즈 및 오답노트

**상태**: 완료 (빌드/테스트/lint 통과). **실기기 검증은 계속 보류**
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
홈에 "퀴즈" 진입점을 추가하고, day별/즐겨찾기/오답노트 범위로 4지선다 퀴즈를 볼 수 있게 했다.
정답/오답을 즉시 피드백하고, 결과 화면에서 틀린 단어를 오답노트에 자동 등록한다. 출제 로직은
순수 함수로 분리해 단위 테스트로 검증했다 (Android 의존성 없이 돌아가는 로직).

## 추가된 동작

| 기능 | 동작 |
|---|---|
| 범위 선택 | 홈 → "퀴즈" → `QuizSetupScreen`에서 day별 / 즐겨찾기 / 오답노트 중 선택 (즐겨찾기·오답노트가 비어 있으면 버튼 비활성) |
| 문제 생성 | 영어 단어 → 한글 뜻 4지선다. 기본 10문항(범위가 더 적으면 전체). 오답 선택지는 **범위 밖** 전체 단어에서 뽑아 뜻 겹침을 피함 |
| 정오 피드백 | 선택 즉시 정답은 초록, 고른 오답은 빨강으로 표시. 재선택은 막고 "다음"으로만 진행 |
| 결과 | 점수/정답률, 틀린 단어 목록. **틀린 단어는 이 시점에 오답노트(`StudyPrefs.unknown_words`)에 자동 등록** |
| 틀린 단어만 다시 학습 | 결과 화면 → 오답노트 복습 세션(`study/review/unknown`)으로 이동 |

## 설계 메모

- **출제 로직(`QuizLogic.buildQuiz`)은 순수 함수**다. `Word` 목록과 `Random`만 받아 `QuizQuestion`
  목록을 반환하므로 Android 없이 JVM 단위 테스트로 검증했다 — 문항 수, 선택지 4개/중복 없음,
  정답 인덱스 일치, 오답 후보 부족 시 예외 없이 처리까지 8개 케이스 (`QuizLogicTest`).
- **"틀린 단어만 다시 학습"은 새 라우트를 만들지 않고 기존 오답노트 복습(`study/review/unknown`)을
  재사용**했다. 방금 틀린 단어는 결과 화면 진입 시 이미 오답노트에 등록해두므로, 그 경로로 보내면
  자연스럽게 방금 틀린 단어가 포함된다. 다만 **과거에 등록된 다른 오답 단어도 함께 보이는 차이가
  있다** — "이번 퀴즈에서 틀린 것만" 정확히 걸러내려면 화면 간에 임시 단어 목록을 넘기는 별도
  메커니즘이 필요한데, Navigation-Compose 인자로는 단어 리스트 같은 복합 타입을 바로 못 넘겨서
  이번엔 오답노트 재사용으로 단순화했다. (실사용에서 문제가 되면 별도 처리 필요 — 사용해보시고
  알려주세요)
- **버튼 색은 `enabled=true`를 유지한 채 `colors`만 바꿔서 표현**한다. `enabled=false`로 두면
  Material3가 비활성 색(회색)을 덧씌워 정답/오답 색이 흐려지는 문제가 있어, 재선택 방지는
  `QuizViewModel.selectAnswer`의 가드(`if (selectedChoiceIndex != null) return`)로만 처리했다.
- **퀴즈는 화면 회전까지만 버틴다.** `QuizViewModel`은 `SavedStateHandle`을 쓰지 않는
  일반 `ViewModel`이라, 회전(설정 변경)에는 살아남지만 프로세스가 완전히 죽었다 살아나면 처음부터
  다시 시작한다. 퀴즈 세션이 짧고 다시 시작해도 손해가 적다고 판단해 `StudyViewModel`만큼
  정교하게 만들지 않았다 — 필요해지면 나중에 확장 가능.

## 추가/변경 파일

- `ui/quiz/QuizLogic.kt` (신규) — `QuizQuestion`, `buildQuiz()` 순수 함수
- `ui/quiz/QuizViewModel.kt` (신규)
- `ui/quiz/QuizSetupScreen.kt` (신규) — 범위 선택
- `ui/quiz/QuizScreen.kt` (신규) — 문제/선택지/정오 피드백
- `ui/quiz/QuizResultScreen.kt` (신규) — 점수/오답 목록/다시 학습
- `ui/AppNavHost.kt` — `quiz`, `quiz/day/{dayNumber}`, `quiz/review/{type}` 라우트 추가
- `ui/home/HomeScreen.kt` — "퀴즈" 버튼 추가
- `app/src/test/java/com/voca/englishwordapp/ui/quiz/QuizLogicTest.kt` (신규) — 8건

## 빌드/테스트 결과
```
./gradlew.bat assembleDebug        BUILD SUCCESSFUL (첫 시도에 통과)
./gradlew.bat testDebugUnitTest    BUILD SUCCESSFUL (25/25 - 이번에 QuizLogicTest 8건 추가)
./gradlew.bat lint                 BUILD SUCCESSFUL
```

## 실기기 검증 시 확인해 주실 것
1. day 하나로 퀴즈 → 정답/오답 색 피드백이 잘 보이는지, "다음"으로 잘 넘어가는지
2. 마지막 문제 후 결과 화면 → 오답노트에 실제로 반영되는지 (ReviewScreen에서 확인 가능)
3. "틀린 단어만 다시 학습" → 방금 틀린 단어가 포함된 학습 화면으로 잘 이동하는지
4. 즐겨찾기/오답노트가 비어 있을 때 해당 버튼이 비활성으로 보이는지
5. 화면 회전 중에 퀴즈를 봐도 진행 중이던 문제가 유지되는지 (앱을 완전히 종료했다가 다시 열면
   처음부터 시작되는 게 의도된 동작입니다 — 위 설계 메모 참고)
