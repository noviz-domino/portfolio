# CLAUDE.md (구버전 — Java/XML 시절, v9 Compose 재작성 이전)

> ⚠️ 이 파일은 **더 이상 실제 코드와 일치하지 않는 과거 기록**입니다.
> 2026-07 Kotlin + Jetpack Compose 재작성(v9) 이전, `MainActivity.java` + XML 레이아웃으로
> 되어 있던 시절의 `CLAUDE.md` 원본을 그대로 보존한 것입니다. 지금 작업할 때는 이 파일이 아니라
> 루트의 `CLAUDE.md`(현재 버전)를 참고하세요. 과거 구조가 왜 이렇게 바뀌었는지 배경이 궁금할 때만
> 이 파일과 `docs/PLAN_v9.md`, `docs/phase-reports/`를 보면 됩니다.

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

토익 영단어 학습용 안드로이드 앱 (`englishWordApp`, 패키지 `com.voca.englishwordapp`).
`assets/words.csv`에 들어있는 로컬 단어 데이터를 day별로 나눠 보여주는 단일 Activity 앱이며,
AdMob 배너 광고가 상/하단에 붙어 있다. 서버·DB 없이 전부 로컬에서 동작한다.

## 기술 스택

- **언어**: Java 전용 (Kotlin 코드 없음. `android.builtInKotlin=false`)
- **Java 호환 레벨**: 11 (`sourceCompatibility` / `targetCompatibility`)
- **빌드**: Gradle 9.5.0 (wrapper) + AGP 9.3.1, Kotlin DSL(`.kts`), 버전 카탈로그(`gradle/libs.versions.toml`)
- **SDK**: `compileSdk` 35 / `targetSdk` 35 / `minSdk` 21
- **UI**: AppCompat + Material3 + ConstraintLayout, XML 레이아웃 (Compose 미사용)
- **광고**: `com.google.android.gms:play-services-ads:23.0.0`
- **기타**: `androidx.core:core-splashscreen:1.0.1` (의존성만 추가됨, 실제 적용 안 됨 — 아래 "알려진 이슈" 참고)
- **테스트**: JUnit4 + Espresso (기본 템플릿 파일만 존재, 실제 테스트 없음)

> `readme.md`의 기술 스택 설명(Kotlin, minSdk 24, targetSdk 34, MVVM)은 실제 코드와 다르다.
> 실제 값은 항상 `app/build.gradle.kts`를 기준으로 판단할 것.

## 자주 쓰는 명령어

Windows 환경이므로 `gradlew.bat`(PowerShell) 또는 `./gradlew`(Git Bash)를 사용한다.

```powershell
.\gradlew.bat assembleDebug          # 디버그 APK 빌드
.\gradlew.bat assembleRelease        # 릴리즈 APK 빌드 (서명 미포함)
.\gradlew.bat bundleRelease          # Play Store 업로드용 AAB 빌드
.\gradlew.bat installDebug           # 연결된 기기/에뮬레이터에 설치
.\gradlew.bat lint                   # Android Lint (리포트: app/build/reports/lint-results-*.html)
.\gradlew.bat clean

.\gradlew.bat test                   # 로컬 단위 테스트 전체
.\gradlew.bat testDebugUnitTest      # 디버그 variant 단위 테스트
.\gradlew.bat connectedAndroidTest   # 계측 테스트 (기기 필요)

# 단일 테스트 클래스 / 메서드 실행
.\gradlew.bat testDebugUnitTest --tests "com.voca.englishwordapp.ExampleUnitTest"
.\gradlew.bat testDebugUnitTest --tests "com.voca.englishwordapp.ExampleUnitTest.addition_isCorrect"
```

릴리즈 서명은 Gradle에 `signingConfig`가 없다. Android Studio의
**Build → Generate Signed Bundle / APK**에서 루트의 `englishWordApp.jks`를 직접 지정해 빌드한다.

## 아키텍처

전체 로직이 `app/src/main/java/com/voca/englishwordapp/MainActivity.java` 한 파일에 들어있다.
Activity/Fragment 전환 없이, **하나의 레이아웃 안에 3개의 화면 컨테이너를 두고 `visibility`로 전환**하는 구조다.

```
activity_main.xml (ConstraintLayout)
├── adViewTop            (항상 표시)
├── layout_home          (LinearLayout)  — 시작 화면, "단어보기" 버튼
├── layout_day_selection (ScrollView)    — day 버튼 목록, 코드에서 동적 생성
├── layout_word_study    (ConstraintLayout) — 단어/뜻 + 이전/다음 버튼
└── adViewBottom         (항상 표시)
```

화면 흐름과 상태:

- `onCreate()` → 광고 초기화 → 뷰 바인딩(`findViewById`) → `loadWordsFromCSV()` → 리스너 등록
- `loadWordsFromCSV()`: `assets/words.csv`를 한 줄씩 읽어 `allWords`(`List<WordItem>`)에 적재. 헤더 1줄은 건너뜀
- `showDaySelection()`: `allWords`에서 `day` 값을 `LinkedHashSet`으로 중복 제거해 **Button을 런타임에 생성**하고 `day_button_container`에 추가
- day 버튼 클릭 → `filteredWords`에 해당 day만 복사, `currentIndex = 0` → 학습 화면 표시
- `updateUI()`: `filteredWords.get(currentIndex)`를 `wordText` / `meaningText`에 반영
- `onBackPressed()`: 학습 → 날짜 선택 → 홈 순서로 되돌아가고, 홈에서만 앱 종료

**상태는 전부 Activity 필드(`allWords`, `filteredWords`, `currentIndex`)에 있다.**
화면 회전 등 Activity 재생성 시 상태가 초기화되며, 별도 저장 로직은 없다.

## 데이터: `app/src/main/assets/words.csv`

- 형식: `Day,Word,Meaning` 헤더 + 약 1,222행, day1~day30
- 뜻에 쉼표가 들어가는 경우 큰따옴표로 감싸져 있음 — 예: `day1,resume,"재개하다. ,'(résumé)이력서'랑 다름"`
- 파서는 `line.split(",", 3)`이라 **따옴표를 해석하지 않는다.** 3번째 필드는 남은 전체를 가져오므로 쉼표는 살아남지만, 따옴표 문자가 화면에 그대로 노출된다.
- **한 줄 = 한 단어 규칙이 깨지면 안 된다.** 셀 안에 개행이 들어간 항목은 다음 줄이 별개 레코드로 읽혀 깨진다. 현재도 `(anticipation 예상)"` 등 3개 행이 이런 잔재로 남아 있다.
- 단어 추가/수정 시: 개행 없이 한 줄로 작성하고, `day` 값은 기존 표기(`day1`, `day2` … 소문자 + 숫자)를 그대로 따를 것. day 버튼 순서는 CSV 등장 순서를 따른다.

## 코딩 컨벤션

- **Java 관례를 그대로 사용**: 클래스 PascalCase, 메서드/필드 camelCase, 뷰 필드는 `private`
- **뷰 id는 snake_case**(`layout_day_selection`, `btn_go_study_list`) 또는 camelCase(`wordText`, `nextButton`)가 혼재. 새 id는 인접한 기존 id의 표기를 따를 것
- **클릭 리스너는 람다**로 작성 (`v -> ...`)
- **주석은 한국어**, 화면 단위로 번호를 매겨 구분 (`// 1. 광고 초기화`, `<!-- 2. 날짜 선택 화면 -->`)
- **UI 문자열은 대부분 레이아웃/코드에 하드코딩**되어 있고 `strings.xml`에는 `app_name`만 있다. 기존 방식을 유지하되 새로 만들 때 굳이 리소스화할 필요는 없음
- **커밋 메시지는 한국어**. 문서 변경은 `docs: ` 접두어 사용, 기능 변경은 접두어 없이 요약 + 버전 갱신 시 `버전8상승 260609`처럼 버전/날짜 표기

## 중요한 설정

### 버전 갱신 (`app/build.gradle.kts`)

```kotlin
versionCode = 8     // 정수. Play Store 업로드 시 이전 값보다 반드시 커야 함
versionName = "8.0" // 사용자에게 보이는 버전
```

이 두 줄만 수정한다 (파일 내 주석에도 명시되어 있음).

### AdMob

- **앱 ID (실제 운영용)**: `AndroidManifest.xml`의 `com.google.android.gms.ads.APPLICATION_ID` = `ca-app-pub-9599668530205647~2274065657`
- **광고 단위 ID (현재 테스트용)**: `activity_main.xml`의 `adViewTop` / `adViewBottom` 둘 다 `ca-app-pub-3940256099942544/6300978111` — 구글이 제공하는 **테스트 배너 ID**다. 실제 수익화하려면 본인 광고 단위 ID로 교체해야 하고, 반대로 개발 중에는 정책 위반을 피하기 위해 테스트 ID를 유지해야 한다.

### `gradle.properties`

AGP 9 대응 플래그가 다수 들어있다. 빌드가 깨질 때 우선 확인할 것:

- `android.newDsl=false`, `android.builtInKotlin=false` — 신규 DSL/내장 Kotlin 비활성화
- `android.enableAppCompileTimeRClass=false`, `android.nonTransitiveRClass=true`
- `android.sdk.defaultTargetSdkToCompileSdkIfUnset=false`
- `org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8` — **UTF-8 인코딩 필수** (한글 리소스/CSV)

### 저장소에 커밋되어 있는 산출물

- `englishWordApp.jks` (서명 키스토어)와 `app/release/app-release.{apk,aab}`가 git에 추적되고 있다. 릴리즈 빌드 후 이 파일들을 갱신·커밋하는 것이 현재 흐름이다.
- `local.properties`는 `.gitignore` 처리되어 있다 (`sdk.dir`만 포함).

## 알려진 이슈 / 미구현

- **스플래시 화면 미작동**: `themes.xml`의 `Theme.EnglishWordApp.Splash`가 `postSplashScreenTheme`로 `@style/Base.Theme.EnglishWordApp`을 참조하는데, 이 스타일은 light(`values/themes.xml`)에서 주석 처리되어 있고 `values-night`에만 정의되어 있다. 게다가 매니페스트는 `Theme.EnglishWordApp`을 적용하므로 Splash 테마 자체가 쓰이지 않는다.
- **테스트 없음**: `ExampleUnitTest` / `ExampleInstrumentedTest`는 안드로이드 스튜디오 기본 템플릿 그대로다.
- **미구현 기능** (readme 기준): 퀴즈 모드, 오답노트/통계, 단어 추가·수정·삭제 UI, Room DB / SharedPreferences 도입.
