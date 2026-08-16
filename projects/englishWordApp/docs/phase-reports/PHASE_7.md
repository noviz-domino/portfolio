# Phase 7 — 마감 / 배포 품질 (마지막 단계)

**상태**: 완료. `./gradlew.bat clean lint testDebugUnitTest assembleRelease` 전부 통과.
**실기기 검증은 여전히 보류** — 이 개편 전체(Phase 0~7)를 통틀어 실기기/에뮬레이터 확인이
한 번도 되지 않았다. 아래 "다음에 꼭 해야 할 일" 참고.
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
스플래시 화면을 실제로 동작하게 연결하고, 다크 모드에서 흰 배경이 번쩍이지 않게 고치고,
모든 UI 문자열을 `strings.xml`로 옮겼다. AdMob을 최신 버전으로 올리고 `versionCode`/
`versionName`을 9로 갱신했다. R8은 시도했으나 막혀서 계획대로 비활성 상태를 유지했다.
문서(`readme.md`, `PROJECT_STRUCTURE.md`, `CLAUDE.md`)를 최종 상태로 동기화했다.

## 한 항목씩

### 1. 스플래시 정상화 ✅
- `AndroidManifest.xml`의 `android:theme`을 `Theme.EnglishWordApp`에서
  `Theme.EnglishWordApp.Splash`로 변경 (전에는 이 테마가 매니페스트에서 전혀 쓰이지 않았음)
- `MainActivity.onCreate()`에서 `super.onCreate()` **이전에** `installSplashScreen()` 호출
  (core-splashscreen 요구사항)
- 스플래시가 끝나면 `postSplashScreenTheme`에 지정된 `Base.Theme.EnglishWordApp`으로 자동 전환

### 2. 다크 모드 점검 ✅ (일부 수정)
- 스플래시 배경을 하드코딩된 `#FFFFFF`에서 `@color/splash_background`로 바꾸고,
  `values-night/colors.xml`에 어두운 값(`#FF121212`)을 따로 둬서, 다크 모드에서 스플래시가
  흰 배경으로 번쩍이던 문제를 없앴다
- 나머지 화면은 Phase 2에서 만든 `EnglishWordAppTheme`(Compose `MaterialTheme`)이 이미
  `isSystemInDarkTheme()`을 보고 있어서 별도 수정이 필요 없었다
- **실제 다크 모드 대비/가독성은 에뮬레이터/실기기에서 시각적으로 확인이 안 된 상태다** — 코드
  리뷰로는 "테마가 다크 모드를 인식한다"까지만 확인 가능했다

### 3. 문자열 리소스화 ✅
- 홈/day목록/학습/복습/퀴즈 화면의 UI 라벨을 전부 `strings.xml`로 옮겼다 (약 45개 문자열)
- 단어/뜻처럼 **데이터인 값**(`word.word`, `word.meaning`, `day.day`)은 리소스화하지 않았다 —
  이건 UI 문구가 아니라 콘텐츠이기 때문
- CLAUDE.md의 "UI 문자열은 하드코딩" 관례를 "strings.xml로 리소스화" 로 갱신 (이제부터 새
  문자열도 리소스로 추가할 것)

### 4. 광고 정책 검토
- `play-services-ads`를 `23.0.0` → **`25.4.0`**(최신 안정판)으로 상향. 빌드/실행 경로에 영향
  주는 API 변경은 없었다 (`MobileAds.initialize`, `AdView`, `AdRequest`, `AdSize` 그대로 사용)
- **UMP(사용자 동의) 도입은 검토만 하고 구현하지 않았다.** EU 등 일부 지역 배포 시 필요할 수
  있는데, 실제 배포 지역/타겟이 확정되지 않아 이번에는 범위 밖으로 남겨둔다 (CLAUDE.md에 근거 남김)
- 광고 단위 ID는 계획대로 테스트 ID 유지

### 5. 버전 갱신 ✅
```kotlin
versionCode = 9
versionName = "9.0"
```

### 6. R8 활성화 — 시도했으나 막힘, 계획대로 비활성 유지
`isMinifyEnabled = true`로 바꿔 `assembleRelease`를 시도했더니, AGP의
`produceReleaseComposeMapping` 태스크가 `org.jetbrains.kotlin:compose-group-mapping:2.2.10`
아티팩트를 Google/Maven Central 어디서도 찾지 못해 빌드가 실패했다:
```
Could not find org.jetbrains.kotlin:compose-group-mapping:2.2.10.
```
우리 프로젝트의 Kotlin은 `2.3.20`인데 왜 `2.2.10` 버전의 매핑 아티팩트를 요구하는지는 확실치
않다 — AGP 9.3.1과 Kotlin Compose 컴파일러 플러그인 조합에서 나오는 버전 불일치로 추정된다.
기획서에 적힌 대로("문제 시 보류") **`isMinifyEnabled = false`로 되돌렸다.** 릴리즈 APK는
축소·난독화되지 않은 채로 빌드된다 — 용량이 좀 더 크고 코드가 그대로 노출되지만, 기능에는
영향이 없다. CLAUDE.md에 재시도 방법(AGP/Kotlin 버전을 올린 뒤 다시 시도)을 남겨뒀다.

### 7. 문서 갱신 ✅
- `readme.md` — Kotlin/Compose/현재 기능 목록으로 전면 재작성
- `PROJECT_STRUCTURE.md` — 새 패키지 구조(`data/`, `ui/`, `tts/`)와 `docs/` 반영
- `CLAUDE.md` — 기술 스택/아키텍처/코딩 컨벤션/알려진 이슈를 v9 최종 상태로 재작성.
  특히 "상태를 어디에 두는지" 섹션을 새로 추가해, `remember` vs ViewModel+SavedStateHandle vs
  SharedPreferences를 언제 쓰는지 정리해뒀다 (다음에 기능을 추가할 때 참고용)

### 8. lint 정리
`./gradlew.bat lint` 결과, Phase 7 작업으로 새로 생긴/사라진 것:
- **고침**: `drawable-v24/`를 `drawable/`로 병합 (minSdk가 24라 v24 한정자가 불필요해졌다는
  `ObsoleteSdkInt` 경고 해소), 매니페스트에서 더 이상 안 쓰는 `Theme.EnglishWordApp` 스타일 삭제
  (`UnusedResources` 경고 해소)
- **남겨둔 것** (전부 기능에 영향 없는 advisory성 경고, 새 개편에서 만든 게 아니라 라이브러리/빌드
  스크립트 스타일에 대한 일반 권고):
  - `UseTomlInstead`(8) — `build.gradle.kts`의 문자열 리터럴 의존성을 버전 카탈로그로 옮기라는 권고
  - `UseKtx`(6), `GradleDependency`(6), `NewerVersionAvailable`(1) — 라이브러리를 더 최신/KTX
    버전으로 바꾸라는 권고
  - `AutoboxingStateCreation`(4) — `mutableStateOf<Int?>` 등 nullable 기본형을 boxing하는 경고
  - `MonochromeLauncherIcon`(2) — 앱 아이콘에 Android 13+ 테마 아이콘용 monochrome 태그가 없음
    (아이콘 리소스 자체는 이번 개편 범위 밖)
  - `OldTargetApi`(1) — compileSdk가 최신(37)보다 한 단계 낮다는 안내 (위 "SDK" 섹션 참고)

## 빌드/테스트 결과 (최종)
```
./gradlew.bat clean lint testDebugUnitTest assembleRelease
BUILD SUCCESSFUL in 57s
79 actionable tasks

- 단위 테스트: 25/25 통과
- lint: 치명 오류 없음 (위 advisory 경고만 남음)
- 릴리즈 APK: app/build/outputs/apk/release/app-release-unsigned.apk (약 17MB, 미서명)
```

## 다음에 꼭 해야 할 일 — 실기기 검증
**Phase 0부터 지금까지 실기기/에뮬레이터에서 앱을 실행해본 적이 한 번도 없다.** 사용자 요청에
따라 각 Phase마다 검증을 보류하고 코드 작성 → 빌드/단위테스트/lint 통과만 확인하며 진행했다.
이제 개발 자체는 끝났으니, 다음 순서로 꼭 확인이 필요하다:

1. Android Studio에서 가상 디바이스(에뮬레이터) 실행 → `installDebug`
2. 전체 플로우 1회 완주:
   - 스플래시 → 홈 → 단어보기 → day1 → 뜻 탭으로 공개 → 스와이프/버튼 이동 → 안다/모른다 →
     마지막 단어에서 완료 다이얼로그 → day 목록 (완료 배지 확인)
   - 홈에서 "이어서 학습" 카드 확인
   - 즐겨찾기 몇 개 표시 → 홈 → "즐겨찾기 / 오답노트" → 학습하기
   - 퀴즈: day 하나 선택 → 10문항 → 결과 → 오답노트 반영 확인
   - 스피커 아이콘/자동 발음 토글로 실제 소리 확인
   - 화면 회전 → 학습 위치 유지 확인
   - 다크 모드 전환 → 전 화면 가독성 확인
   - "학습 기록 초기화" 확인
3. 문제없으면 실제 안드로이드폰 연결해서 같은 흐름 재확인
4. 문제가 발견되면 이슈를 정리해서 알려주시면 됩니다 — Phase별 보고서(`docs/phase-reports/`)에
   각 기능이 어디 코드에 있는지 정리되어 있어서 원인 파악이 빠를 것입니다

## 기획서 진행 상황
`docs/PLAN_v9.md`의 Phase 0~7 **전체가 완료**되었습니다. main으로의 병합 시점은 위 실기기
검증이 끝난 뒤 다시 논의하면 좋겠습니다 (계획서의 "진행 방식 제안"에도 이렇게 적어뒀습니다).
