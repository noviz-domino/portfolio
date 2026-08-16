# Phase 4 — 학습 기록 저장 (SharedPreferences)

**상태**: 완료 (빌드/테스트/lint 통과). **실기기 검증은 계속 보류**
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
`StudyPrefs`(SharedPreferences 래퍼)를 추가해 학습 진행도·즐겨찾기·오답(모르는 단어)을 저장하고,
홈의 "이어서 학습" 카드, day 목록의 완료/진행 배지, 즐겨찾기·오답노트 복습 화면(`ReviewScreen`)을
새로 연결했다. `words.csv`는 계속 읽기전용이고, 여기서는 "무엇을 어디까지 봤는지"만 기록한다.

## 추가된 동작

| 기능 | 동작 |
|---|---|
| 이어서 학습 | 홈에 `day{N}에서 이어보기 (18/40)` 버튼. `lastDay`가 없으면 숨김 |
| 즐겨찾기 | 학습 카드 우상단 별 아이콘 토글. `WordCard`마다 즉시 반영 |
| day 완료/진행 배지 | day 목록에서 완료한 day는 "완료", 진행 중인 day는 "N/전체" 표시 |
| 오답노트 | 뜻 공개 후 "모른다"를 누르면 저장, "안다"를 누르면 오답노트에서 제거 |
| 복습 화면 | 홈 → "즐겨찾기 / 오답노트" → 각 섹션 목록 + "학습하기"로 그 단어들만 모아 학습 |
| 초기화 | 홈의 "학습 기록 초기화" → 확인 다이얼로그 → 진행도/즐겨찾기/오답노트 전부 삭제 |

## 핵심 설계

- **단어 식별 키**: `wordKey(dayNumber, word) = "$dayNumber|$word"`. day 안에서 CSV 줄 순서가
  바뀌어도 흔들리지 않는다. (`StudyPrefsKeyTest`로 검증)
- **`words.csv`는 그대로, 기록은 별도 저장소**: `StudyPrefs`가 `study_prefs`라는 하나의
  SharedPreferences 파일에 `last_day`(Int), `progress_day_{n}`(Int), `completed_days`/
  `favorites`/`unknown_words`(StringSet)를 둔다.
- **day 단위 진행 추적과 복습 세션을 분리**: `StudyScreen`에 `trackingDayNumber: Int?`를 추가했다.
  일반 학습(`study/{dayNumber}`)에서는 실제 day 번호를 넘겨 진행도/완료를 기록하고, 즐겨찾기·오답노트
  복습(`study/review/{type}`)에서는 `null`을 넘겨 day 단위 추적을 건너뛴다 — 여러 day가 섞인
  목록이라 "이 day의 몇 번째"라는 개념이 없기 때문이다. 즐겨찾기/오답 표시 자체는
  `Word.dayNumber`를 직접 쓰므로 이 값과 무관하게 항상 동작한다.
- **SharedPreferences는 Compose 상태가 아니다**: 값이 바뀌어도 자동으로 recomposition을 유발하지
  않는다. 그래서 홈/day 목록 화면은 값을 `remember`로 캐싱하지 않고 목적지에 들어올 때마다
  새로 읽는다 (Navigation-Compose는 목적지를 벗어났다가 되돌아오면 그 컴포저블을 새로 구성하므로
  자연스럽게 최신값을 읽게 된다). 다만 **홈 화면에 머무른 채로 초기화를 누르는 경우**(네비게이션이
  없음)는 예외라서, `resetTick`이라는 별도 상태를 하나 두고 그 값이 바뀔 때만 다시 계산하게 했다.

## 변경/추가 파일

- `data/StudyPrefs.kt` (신규) — SharedPreferences 래퍼
- `data/WordRepository.kt` — `getWordsByKeys(keys)` 추가 (즐겨찾기/오답노트 목록 조회용)
- `ui/study/StudyScreen.kt` — `trackingDayNumber` 파라미터, 진행도/완료/오답 저장, 즐겨찾기 별 아이콘
- `ui/home/HomeScreen.kt` — `ContinueInfo`, 이어서 학습 카드, 복습 진입, 초기화 다이얼로그
- `ui/day/DayListScreen.kt` — `completedDays`/`progressByDay` 기반 배지
- `ui/review/ReviewScreen.kt` (신규) — 즐겨찾기/오답노트 섹션 + 학습하기
- `ui/AppNavHost.kt` — `review`, `study/review/{type}` 라우트 추가, prefs 연결
- `app/build.gradle.kts` — `androidx.compose.material:material-icons-core` 추가 (별 아이콘)
- `app/src/test/java/com/voca/englishwordapp/data/StudyPrefsKeyTest.kt` (신규) — `wordKey` 단위 테스트 4건

## 테스트한 것 / 못한 것
- `wordKey` 자체는 순수 함수라 단위 테스트로 검증했다 (4건, 전체 17/17 통과)
- `StudyPrefs`는 `Context.getSharedPreferences`에 의존해 순수 JVM 테스트로는 검증하기 어렵다
  (Robolectric 등 계측 테스트 도구가 필요 — 이번 개편 범위 밖으로 남겨둔다). **따라서 진행도 저장,
  이어서 학습, 즐겨찾기/오답노트 실제 동작은 아직 로직 리뷰로만 확인된 상태고, 실기기 확인이
  이번 단계의 핵심 검증 지점입니다.**

## 빌드/테스트 결과
```
./gradlew.bat assembleDebug        BUILD SUCCESSFUL
./gradlew.bat testDebugUnitTest    BUILD SUCCESSFUL (17/17)
./gradlew.bat lint                 BUILD SUCCESSFUL
```

## 실기기 검증 시 확인해 주실 것 (우선순위 순)
1. 단어 몇 개 즐겨찾기 표시 → 앱 완전히 종료 후 재실행 → 그대로 유지되는지
2. day 하나를 끝까지 봄 → day 목록에 "완료" 표시, 홈에 "이어서 학습"이 사라지는지
   (완료된 day는 이어서 학습 후보에서 빠지지 않고 그대로 남는데, 이 동작이 의도와 맞는지도 봐주세요 —
   지금 구현은 완료 여부와 무관하게 `lastDay`만 보고 이어서 학습을 띄웁니다)
3. "모른다"로 표시한 단어가 오답노트에 뜨는지, 나중에 "안다"로 다시 표시하면 빠지는지
4. 즐겨찾기/오답노트에서 "학습하기" → 여러 day가 섞인 목록이 잘 보이는지
5. "학습 기록 초기화" → 확인 후 전부 비워지는지
