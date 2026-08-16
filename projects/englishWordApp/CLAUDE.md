# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **AI 에이전트 협업 규칙:** 이 저장소는 Claude Code와 Codex가 번갈아 작업한다. 프로젝트 지침의
> 원본은 **이 파일 하나**이며, `AGENTS.md`는 이 파일을 가리키는 스텁이다 (지침을 복사하지 말 것 —
> 과거 복사본이 낡아 이미 삭제된 화면을 참조하는 사고가 있었다).
>
> - **작업 시작 전**: `AI_WORKLOG.md`(현재 미커밋 작업과 소유자) → `git status` →
>   `git log --oneline -10` 순으로 확인한다.
> - **다른 작업자의 미커밋 변경은 소유자를 확인하기 전에는 수정·삭제하지 않는다.**
> - **작업을 커밋하면** `AI_WORKLOG.md`의 해당 항목을 지우고, 검증 결과는 커밋 메시지 본문에
>   `검증: <명령> 성공` 형식으로, 작업자는 `Co-Authored-By:` 트레일러로 남긴다.
> - **남은 작업**은 항목을 지우기 전에 옮긴다 — 다음 작업자가 실제로 해야 할 일은 아래
>   "알려진 이슈 / 미구현"으로, 배경·장기 계획은 `docs/`로.
> - 세션 도중 이 파일이나 일지를 고쳐도 **이미 실행 중인 상대 세션에는 반영되지 않는다.**
>   규칙 변경은 다음 세션부터 효력이 생긴다는 전제로 작업할 것.

## 프로젝트 개요

토익 영단어 학습용 안드로이드 앱 (`englishWordApp`, 패키지 `com.voca.englishwordapp`).
`assets/words.csv`에 들어있는 로컬 단어 데이터를 day별로 나눠 보여주고, 학습 진행도·즐겨찾기·
오답노트를 기기에 저장하며, 발음 재생과 4지선다 퀴즈를 제공하는 단일 Activity 앱이다.
서버·DB 없이 전부 로컬(CSV + SharedPreferences)에서 동작한다.

> **v9(2026-07)에서 Java/XML 구조를 Kotlin + Jetpack Compose로 전면 재작성**했다. 과거
> Java 버전 문서는 `docs/CLAUDE_구버전.md`에 보존되어 있다 (지금 작업에는 참고할 필요 없음).
> 재작성 배경·단계별 결정·실기기에서 발견된 버그와 수정 내역은 `docs/PLAN_v9.md`와
> `docs/phase-reports/`(`PHASE_0.md` ~ `PHASE_7.md`, `PHASE_7_DEVICE_FIXES.md`)에 있다.
> "이 코드가 왜 이렇게 되어 있는지" 궁금하면 먼저 그 문서들을 찾아볼 것 — 특히 아래
> "⚠️ 자주 반복된 실수" 섹션은 꼭 읽고 시작할 것.

## ⚠️ 자주 반복된 실수 — Compose 상태 관리

이 프로젝트에서 **같은 버그가 두 번 발생했다**: ViewModel의 프로퍼티를 `mutableStateOf`로
감싸지 않고 일반 `var`로 선언하면, 값이 바뀌어도 Compose가 변경을 감지하지 못해 **화면이
갱신되지 않는다.** `StudyViewModel`은 처음부터 이 규칙을 지켰지만, `QuizViewModel`의
`questions` 필드는 일반 `var`로 뒤늦게 추가되어 "퀴즈를 만들 단어가 부족합니다" 화면에
영원히 멈춰 있는 버그로 실기기에서 발견됐다 (`docs/phase-reports/PHASE_7_DEVICE_FIXES.md`
참고). **새 ViewModel이나 상태 홀더를 추가할 때는 Compose에서 읽는 프로퍼티를 전부
`by mutableStateOf(...)` (또는 `mutableStateListOf`/`mutableStateMapOf`)로 선언했는지
반드시 확인할 것.**

또 하나: **`Box` 안에서 화면 전체를 덮는 `clickable` 영역을 다른 클릭 가능한 요소보다
나중에 선언하면, 그 영역이 위에 그려져서 아래 요소의 터치를 다 가져가 버린다** (실기기에서
학습 카드의 스피커/즐겨찾기 아이콘이 안 눌리는 버그로 발견됨 — `StudyScreen.kt`의
`WordCard` 참고). `Box`의 자식은 **나중에 선언된 것이 위에 그려진다**는 걸 기억할 것.

## 기술 스택

- **언어**: Kotlin (AGP 9 **내장 Kotlin** 사용, `android.builtInKotlin=true`. 별도
  `org.jetbrains.kotlin.android` 플러그인은 적용하지 않음 — AGP 9에서는 두 개를 함께 쓰면 빌드 실패).
  Java 소스는 없다
- **Java 호환 레벨**: 11 (`sourceCompatibility` / `targetCompatibility`, Kotlin 코드에도 동일 타겟 적용)
- **빌드**: Gradle 9.5.0 (wrapper) + AGP 9.3.1, Kotlin DSL(`.kts`), 버전 카탈로그(`gradle/libs.versions.toml`)
- **SDK**: `compileSdk` 36 / `targetSdk` 36 / `minSdk` 24
  - Google Play 정책상 2026-08-31부터 최신 Android 출시 기준 1년 이내 targetSdk가 필수라
    35→36으로 상향했다
  - `compileSdk` 36은 로컬에 `android-36` SDK 플랫폼이 필요하다 (없으면 Android Studio
    SDK Manager에서 설치, 또는 Gradle이 처음 빌드할 때 자동으로 받아온 적도 있었다)
  - `compileSdk` 37은 아직 올리지 않았다 — Compose 1.12.0부터 37을 요구하는데, 지금 쓰는
    BOM은 그 이전 버전(`2026.04.01`)이라 문제없다
  - **targetSdk 36부터 edge-to-edge가 강제**된다 (앱이 상태바/내비게이션바 뒤까지 그려짐).
    아래 "edge-to-edge / 시스템 바" 섹션 참고 — 이거 놓치면 광고나 UI가 시스템 바 뒤에 깔린다
- **UI**: Jetpack Compose only (`androidx.compose` BOM `2026.04.01`). XML 레이아웃과
  AppCompat/Material Components(View)/ConstraintLayout 의존성은 없음.
  화면 전환은 `androidx.navigation:navigation-compose`의 `NavHost`가 담당 — 뒤로가기는
  NavController가 자동 처리하므로 `onBackPressed()` 오버라이드가 없다
- **Compose 컴파일러**: `org.jetbrains.kotlin.plugin.compose` (Kotlin 버전과 동일하게 `2.3.20`).
  ⚠️ `import androidx.compose.foundation.layout.weight`처럼 이름을 하나씩 지정해서 import하면
  Compose Foundation의 `internal` 프로퍼티와 충돌해 컴파일 에러가 날 수 있었다 (실제로 겪음 —
  `docs/phase-reports/PHASE_2.md`). `foundation.layout` 계열은 `import
  androidx.compose.foundation.layout.*` 와일드카드로 쓸 것
- **아이콘**: `androidx.compose.material:material-icons-extended` (별/스피커 아이콘에 필요.
  `material-icons-core`에는 `VolumeUp`/`VolumeOff`가 없다)
- **광고**: `com.google.android.gms:play-services-ads:25.4.0`, `ui/ads/AdBanner.kt`에서
  기존 View `AdView`를 `AndroidView`로 감싸서 재사용 (Compose용 배너 API가 따로 있는 게 아님)
- **스플래시**: `androidx.core:core-splashscreen:1.0.1`. `MainActivity.onCreate()`에서
  `super.onCreate()` **이전에** `installSplashScreen()` 호출, 매니페스트가
  `Theme.EnglishWordApp.Splash`를 적용
- **음성**: 안드로이드 내장 `TextToSpeech` (`tts/WordSpeaker.kt`)
- **테스트**: JUnit4 (Kotlin으로 작성), 총 25건. `app/src/test/java/com/voca/englishwordapp/`
  - `data/CsvWordParserTest` — CSV 파서 단위 테스트
  - `data/WordsCsvIntegrityTest` — 실제 `words.csv` 데이터셋 회귀 테스트
  - `data/StudyPrefsKeyTest` — `wordKey()` 단위 테스트
  - `ui/quiz/QuizLogicTest` — 퀴즈 출제 로직 단위 테스트

  Espresso(`ExampleInstrumentedTest`)는 기본 템플릿 그대로이며 실질 테스트는 없다. UI/네비게이션
  동작은 실기기 확인으로 검증했다 (아래 "실기기 확인" 참고).

## 자주 쓰는 명령어

Windows 환경이므로 `gradlew.bat`(PowerShell) 또는 `./gradlew`(Git Bash)를 사용한다.

**`JAVA_HOME`을 따로 설정할 필요 없다.** `gradle/gradle-daemon-jvm.properties`가 데몬 JVM을
JetBrains JDK 21로 고정해두었고, `settings.gradle.kts`의 foojay 툴체인 리졸버가 없으면 받아온다.
시스템 기본 Java가 8이어도 빌드가 성공하는 것을 확인했다 (데몬 종료 후 `clean assembleDebug`).
이 두 파일을 지우면 다시 `$env:JAVA_HOME = "<Android Studio 설치 경로>\jbr"`처럼 수동 지정이
필요해진다 (Gradle 9는 JDK 17+ 요구).

```powershell
.\gradlew.bat assembleDebug          # 디버그 APK 빌드
.\gradlew.bat assembleRelease        # 릴리즈 APK 빌드 (서명 미포함, R8 비활성 - 아래 참고)
.\gradlew.bat bundleRelease          # Play Store 업로드용 AAB 빌드
.\gradlew.bat installDebug           # 연결된 기기/에뮬레이터에 설치
.\gradlew.bat lint                   # Android Lint (리포트: app/build/reports/lint-results-*.html)
.\gradlew.bat clean

.\gradlew.bat test                   # 로컬 단위 테스트 전체
.\gradlew.bat testDebugUnitTest      # 디버그 variant 단위 테스트
.\gradlew.bat connectedAndroidTest   # 계측 테스트 (기기 필요)

# 단일 테스트 클래스 / 메서드 실행
.\gradlew.bat testDebugUnitTest --tests "com.voca.englishwordapp.data.CsvWordParserTest"
.\gradlew.bat testDebugUnitTest --tests "com.voca.englishwordapp.ui.quiz.QuizLogicTest"
```

릴리즈 서명은 Gradle에 `signingConfig`가 없다. Android Studio의
**Build → Generate Signed Bundle / APK**에서 루트의 `englishWordApp.jks`를 직접 지정해 빌드한다.

### 실기기로 직접 확인하기 (adb)

에뮬레이터/실기기가 연결되어 있으면(`adb devices`로 확인), 화면을 직접 캡처해서 검증할 수 있다.
UI 관련 코드를 고칠 때는 빌드/테스트만 믿지 말고 아래처럼 실제로 확인하는 걸 권장한다
(이 프로젝트에서 실제로 여러 버그를 이 방법으로 잡았다 — `docs/phase-reports/PHASE_7_DEVICE_FIXES.md`).

```bash
adb devices                                    # 연결 확인
adb shell am start -n com.voca.englishwordapp/.MainActivity
adb exec-out screencap -p > screen.png         # 화면 캡처 (Read 도구로 열어서 확인)
adb shell input tap <x> <y>                    # 좌표 탭 (화면 해상도는 adb shell wm size)
adb logcat -c && adb logcat -d -t 50           # 특정 동작(TTS 등) 로그 확인
```

## 아키텍처

단일 Activity(`MainActivity.kt`, `ComponentActivity`) + Compose. 화면 전환은
`ui/AppNavHost.kt`의 `NavHost`가 담당한다.

```
com.voca.englishwordapp/
├── MainActivity.kt              — installSplashScreen() + 광고 초기화 + setContent
├── data/
│   ├── Word.kt                  — data class Word(day, dayNumber, word, meaning)
│   ├── CsvWordParser.kt         — RFC4180 준수 파서 (순수 함수)
│   ├── WordRepository.kt        — assets 1회 로드 + 캐싱. getDays()/getWords(dayNumber)/getWordsByKeys(keys)/getAllWords()
│   └── StudyPrefs.kt            — SharedPreferences 래퍼: 진행도/완료 day/즐겨찾기/오답노트
├── ui/
│   ├── theme/Theme.kt            — Material3 light/dark(보라·핑크 브랜드 색상표) +
│   │                                상태바/내비게이션바 아이콘 색 전환
│   ├── AppNavHost.kt             — 전체 네비게이션 그래프 + 상하단 AdBanner(단색 배경 + 시스템 바 여백)
│   ├── ads/AdBanner.kt           — AndroidView로 감싼 AdView
│   ├── home/HomeScreen.kt        — 브랜드 헤더(Word Buddy) + 2열x3행 메뉴 타일
│   │                                (단어보기/이어보기/퀴즈/오답노트/즐겨찾기/초기화)
│   ├── day/DayListScreen.kt      — day 목록 (dayNumber 오름차순, 완료/진행 배지)
│   ├── study/                    — StudyScreen + StudyViewModel (학습 화면 본체)
│   ├── review/                   — FavoritesScreen/MistakesScreen(각각 독립 화면) +
│   │                                WordListScreen(공유 목록 UI)
│   └── quiz/                     — QuizLogic(순수 함수) + QuizViewModel + QuizSetupScreen +
│                                    QuizScreen + QuizResultScreen
└── tts/WordSpeaker.kt            — TextToSpeech 래퍼 (WordSpeakerState, rememberWordSpeaker)
```

### 네비게이션 라우트 (`ui/AppNavHost.kt`)

| 라우트 | 화면 | 비고 |
|---|---|---|
| `home` | HomeScreen | 시작 화면 |
| `days` | DayListScreen | day1~30 목록 |
| `study/{dayNumber}` | StudyScreen | `trackingDayNumber`를 넘겨 진행도/완료를 `StudyPrefs`에 기록 |
| `favorites` | FavoritesScreen | 즐겨찾기 목록 (독립 화면) |
| `mistakes` | MistakesScreen | 오답노트 목록 (독립 화면) |
| `study/review/{type}` | StudyScreen | `type`=`favorites`/`unknown`. day 추적은 안 함(`trackingDayNumber=null`) |
| `quiz` | QuizSetupScreen | day별/즐겨찾기/오답노트 중 퀴즈 범위 선택 |
| `quiz/day/{dayNumber}` , `quiz/review/{type}` | QuizScreen | 퀴즈 진행, 마지막에 `QuizResultScreen`으로 내부 전환 |

뒤로가기는 NavController가 자동으로 처리한다 (deprecated `onBackPressed()` 오버라이드가 없다).

### 상태를 어디에 두는지

- **화면 로컬(`remember`)**: 다이얼로그 표시 여부처럼 화면을 나가면 사라져도 되는 것
- **ViewModel + `SavedStateHandle`** (`StudyViewModel`): 학습 화면의 현재 위치/뜻 공개/셔플/자동발음.
  NavBackStackEntry에 스코프되어 회전은 물론 **프로세스 재생성에도 복원**된다
- **ViewModel만(`QuizViewModel`)**: 퀴즈 진행 상태. 회전은 버티지만 프로세스 재생성까지는 복원 안 함
  (퀴즈는 세션이 짧아 다시 시작해도 손해가 적다고 판단해 `SavedStateHandle`을 쓰지 않음)
- **`SharedPreferences`(`StudyPrefs`)**: day별 진행도, 완료 day, 즐겨찾기, 오답노트 — 앱을
  껐다 켜도 유지되어야 하는 것. Compose 상태가 아니므로 값이 바뀌어도 자동으로 recomposition을
  유발하지 않는다. 홈/day 목록 화면은 이 값을 `remember`로 캐싱하지 않고 화면에 들어올 때마다
  새로 읽는다 (Navigation-Compose는 목적지를 벗어났다가 되돌아오면 그 컴포저블을 새로 구성함).
  단, **홈 화면에 머무른 채로 초기화를 누르는 경우**(네비게이션이 없음)는 예외라서 `resetTick`이라는
  별도 상태로 강제 재계산한다

**모든 새 ViewModel/상태 홀더는 위 "⚠️ 자주 반복된 실수" 섹션을 다시 확인할 것.**

### edge-to-edge / 시스템 바

`targetSdk` 36부터 edge-to-edge가 강제라 상태바/내비게이션바가 항상 투명하게 그려진다.
두 가지를 반드시 같이 처리해야 한다 (하나만 하면 다시 버그가 난다):

1. **아이콘 색상**: `ui/theme/Theme.kt`의 `EnglishWordAppTheme`이 다크/라이트 테마에 맞춰
   `WindowCompat.getInsetsController(...).isAppearanceLightStatusBars`/
   `isAppearanceLightNavigationBars`를 `SideEffect`로 갱신한다. 이걸 빼먹으면 라이트 모드에서
   상태바 아이콘(시계 등)이 거의 안 보인다 (실제로 겪은 버그).
2. **콘텐츠가 시스템 바 뒤에 깔리지 않게**: `AppNavHost`의 `Scaffold`에서 상/하단 `AdBanner`를
   감싼 `Column`에 `MaterialTheme.colorScheme.surface` 단색 배경 + `Spacer(Modifier
   .windowInsetsTopHeight(WindowInsets.statusBars))`(상단) /
   `windowInsetsBottomHeight(WindowInsets.navigationBars)`(하단)로 여백을 준다. 광고는
   외부 콘텐츠라 배경색이 매번 다르므로, 시스템 바로 깔리는 부분은 앱 테마색으로 통일해서
   광고와 분리해둔다.

## 데이터: `app/src/main/assets/words.csv`

- 형식: `Day,Word,Meaning` 헤더 + 약 1,222행, day1~day30
- 뜻에 쉼표가 들어가는 경우 큰따옴표로 감싸져 있음 — 예: `day1,resume,"재개하다. ,'(résumé)이력서'랑 다름"`
- `CsvWordParser`가 RFC4180 규칙(따옴표로 감싼 구간의 쉼표 보존, 감싸는 따옴표 제거, `""` 이스케이프
  복원)으로 파싱한다
- **한 줄 = 한 단어 규칙이 깨지면 안 된다.** 셀 안에 개행이 들어간 항목은 다음 줄이 별개 레코드로
  읽힌다. 단어 추가/수정 시 개행 없이 한 줄로 작성할 것
- `day` 값은 기존 표기(`day1`, `day2` … 소문자 + 숫자)를 그대로 따를 것. day 목록 화면 순서는
  `WordRepository.getDays()`가 dayNumber로 정렬하므로 CSV 등장 순서와 무관하게 항상 day1→day30 순서로 보인다
- **CSV는 앱에서 읽기전용이다.** 학습 진행도/즐겨찾기/오답노트는 CSV가 아니라
  `StudyPrefs`(SharedPreferences)에 저장된다. 단어 자체를 고치려면 이 파일을 직접 편집해야 한다
- 단어 식별은 `wordKey(dayNumber, word) = "$dayNumber|$word"`로 한다 (즐겨찾기/오답노트가 이 키로
  저장됨) — CSV 안에서 단어 순서가 바뀌어도 안전하다

## 코딩 컨벤션

- **Kotlin 관례**: 클래스 PascalCase, 함수/필드 camelCase. Composable 함수는 PascalCase
  (`HomeScreen`, `AdBanner`)로 View를 대신한다
- **클릭 리스너는 람다**로 작성 (`onClick = { ... }`) — Java 시절 관례를 그대로 이어받음
- **주석은 한국어**
- **UI 문자열은 `strings.xml`로 리소스화한다.** (v9 Phase 7에서 일괄 정리함 — 이전 Java 버전의
  "대부분 하드코딩" 관례는 더 이상 적용되지 않는다.) `stringResource(R.string.xxx, ...)`로 쓰고,
  포맷이 필요하면 `%1$s`/`%1$d` 같은 위치 지정자를 쓴다. 단, **단어/뜻처럼 데이터인 값**
  (`word.word`, `word.meaning`, `day.day` 등)은 리소스화 대상이 아니다
- **`androidx.compose.foundation.layout.*`은 와일드카드로 import**할 것 (위 "Compose 컴파일러" 참고)
- **커밋 메시지는 한국어**. 문서 변경은 `docs: ` 접두어 사용, 기능 변경은 접두어 없이 요약 + 버전 갱신 시
  `버전9상승 260729`처럼 버전/날짜 표기

## 중요한 설정

### 버전 갱신 (`app/build.gradle.kts`)

```kotlin
versionCode = 11     // 정수. Play Store 업로드 시 이전 값보다 반드시 커야 함
versionName = "11.0" // 사용자에게 보이는 버전
```

이 두 줄만 수정한다 (파일 내 주석에도 명시되어 있음).

### AdMob

- **앱 ID (실제 운영용)**: `AndroidManifest.xml`의 `com.google.android.gms.ads.APPLICATION_ID` = `ca-app-pub-9599668530205647~2274065657`
- **광고 단위 ID (실제 운영용)**: `ui/ads/AdBanner.kt`의 `TOP_AD_UNIT_ID`/`BOTTOM_AD_UNIT_ID`.
  기존 광고 단위가 AdMob에서 사용 불가 처리되어 상단/하단용으로 새로 만들었다. **디버그/릴리즈
  구분 없이 항상 이 실제 ID를 쓴다** — 대신 개발용 기기를 AdMob 콘솔의 "테스트 기기"에 등록해서
  실수로 클릭해도 안전한 테스트 광고만 받게 해뒀다 (기기 등록 안 하면 진짜 광고가 나오니
  실기기로 확인할 때 조심할 것). 새 기기로 테스트할 땐 `adb logcat`에서
  `Use RequestConfiguration.Builder().setTestDeviceIds(...)` 로그로 나오는 기기 ID를
  AdMob 콘솔 설정 → 테스트 기기에 추가하면 된다.
- **UMP(사용자 동의) 미적용**: EU 등 일부 지역은 광고 표시 전 동의 흐름(Google User Messaging
  Platform)이 필요할 수 있다. 검토만 했고 실제 도입은 안 했다 — 실제 배포 지역/수익화 계획이
  정해지면 `com.google.android.ump:user-messaging-platform` 도입을 검토할 것

### R8 / 코드 축소 — 현재 비활성 (`isMinifyEnabled = false`)

`isMinifyEnabled = true`로 릴리즈 빌드를 시도하면, AGP의 `produceReleaseComposeMapping`
태스크가 `org.jetbrains.kotlin:compose-group-mapping:2.2.10` 아티팩트를 해석하지 못해
빌드가 실패한다:
```
Could not find org.jetbrains.kotlin:compose-group-mapping:2.2.10.
```
Kotlin은 `2.3.20`인데 왜 `2.2.10` 버전의 매핑 아티팩트를 요구하는지는 불확실하다 — AGP 9.3.1과
Kotlin Compose 컴파일러 플러그인 조합의 버전 불일치로 추정된다. **다시 시도하려면**: AGP나
Kotlin 버전을 올린 뒤 `isMinifyEnabled = true`로 바꿔서 `assembleRelease`가 성공하는지 먼저
확인할 것. 실패하면 바로 되돌릴 것.

### `gradle.properties`

AGP 9 대응 플래그가 다수 들어있다. 빌드가 깨질 때 우선 확인할 것:

- `android.newDsl=false` — 신규 DSL 비활성화
- `android.builtInKotlin=true` — AGP 9 내장 Kotlin 사용. `false` + 별도 `kotlin-android`
  플러그인 조합은 AGP 10에서 제거될 임시 우회 경로라 권장 경로인 `true`로 전환함
- `android.enableAppCompileTimeRClass=false`, `android.nonTransitiveRClass=true`
- `android.sdk.defaultTargetSdkToCompileSdkIfUnset=false`
- `org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8` — **UTF-8 인코딩 필수** (한글 리소스/CSV)

### 저장소에 커밋되어 있는 산출물

- `englishWordApp.jks` (서명 키스토어)와 `app/release/app-release.{apk,aab}`가 git에 추적되고 있다. 릴리즈 빌드 후 이 파일들을 갱신·커밋하는 것이 현재 흐름이다.
- `local.properties`는 `.gitignore` 처리되어 있다 (`sdk.dir`만 포함).

## 알려진 이슈 / 미구현

- **R8 비활성**: 위 "R8 / 코드 축소" 참고. 릴리즈 APK가 축소·난독화되지 않은 상태로 빌드된다.
- **UMP(광고 동의) 미적용**: 위 "AdMob" 참고.
- **계측 테스트 없음**: `ExampleInstrumentedTest`(Espresso)는 기본 템플릿 그대로다. UI 동작은
  실기기 확인(스크린샷 + `adb input tap` + `logcat`)으로 검증하고 있다
- **"틀린 단어만 다시 학습"의 근사치**: 퀴즈 결과에서 "틀린 단어만 다시 학습"을 누르면 방금 틀린
  단어만이 아니라 오답노트 전체가 보인다 (내비게이션으로 임의 단어 목록을 넘기기 어려워서 택한
  단순화 — `docs/phase-reports/PHASE_6.md` 참고)
- **day 목록 하단이 광고와 살짝 겹쳐 보일 수 있음**: 화면 전환 첫 프레임에 `WindowInsets` 값이
  아직 0으로 보고되다가 한 프레임 뒤에 갱신되는 Compose의 알려진 타이밍 이슈로 추정된다.
  재현되면 원인을 더 파봐야 함 (`docs/phase-reports/PHASE_7_DEVICE_FIXES.md`에 첫 관찰 기록)
- **미구현 기능**: 앱 내 단어 추가/수정/삭제 UI, Room DB 도입, 실제 광고 단위 ID 교체,
  학습 통계 대시보드, 위젯/알림 — `docs/PLAN_v9.md`의 "이번 범위에서 제외" 참고

### 브랜드/아이콘 후속 작업 (2026-08-14 적용분)

Word Buddy 마스코트와 홈 헤더, 새 런처 아이콘을 적용했다 (색상·파일 용도·캐릭터 재현
프롬프트는 `docs/brand/README.md`, `docs/brand/PROMPTS.md` 참고). 남은 확인 사항:

- **실기기 확인 미완료**: 작은 화면과 다크 모드에서 홈 헤더가 상하단 광고 사이에 제대로
  들어오는지, 런처 아이콘이 원형/스퀴클 마스킹에서 잘리지 않는지 확인 필요
- **Play 스토어 스크린샷 미촬영**: 홈 → 단어 학습 → 퀴즈 → 오답노트/즐겨찾기 순으로 재촬영 권장
- **앱 이름 미확정**: 아이콘·피처 그래픽에 일부러 글자를 넣지 않았다. 이름이 정해지면
  앱 이름·Play 스토어 제목·피처 그래픽 문구를 함께 정리할 것
  (문구 없는 원본: `docs/brand/play-store/feature-graphic-no-text-1024x500.png`)
- **레거시 round 아이콘이 사각형과 동일 파일**: `mipmap-*/ic_launcher_round.png`가
  `ic_launcher.png`와 바이트 단위로 같다. API 26+는 `mipmap-anydpi-v26`의 adaptive icon이
  처리하므로 무관하지만, `minSdk 24`라 API 24~25 기기에서는 둥근 마스킹 없이 보인다 (우선순위 낮음)
