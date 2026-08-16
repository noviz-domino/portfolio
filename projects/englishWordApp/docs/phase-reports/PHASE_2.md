# Phase 2 — Compose UI 패리티 이식

**상태**: 완료 (빌드/테스트/lint 통과). **실기기 검증은 여전히 보류** (Phase 0 결정과 동일 — 나중에 에뮬레이터→실기기 순으로 일괄 확인)
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
`MainActivity.java`/`activity_main.xml`을 삭제하고, 같은 화면 흐름(홈 → 날짜 선택 → 단어 학습)을
Compose + Navigation-Compose로 다시 만들었다. 기능 추가는 없고 기존 동작 그대로 재현하는 것이 목표.
XML 레이아웃과 View 기반 `appcompat`/`material`/`constraintlayout` 의존성을 전부 제거했다.

## 계획과 달라진 점

### 1. 화면 전환 구조가 `visibility` 토글 → NavController 백스택으로 바뀜
기존에는 레이아웃 3개를 한 파일에 두고 `View.VISIBLE`/`GONE`으로 전환하고, `onBackPressed()`를
오버라이드해 뒤로가기 순서를 직접 관리했다. 지금은 `AppNavHost`가 `home → days → study/{dayNumber}`
경로를 가진 NavHost이고, 뒤로가기는 NavController가 자동으로 처리한다 — API 33+에서
deprecated된 `onBackPressed()` 오버라이드가 필요 없어졌다 (CLAUDE.md에 적혀 있던 이슈 하나 해소).

### 2. 예상보다 빌드 중 시행착오가 있었음 — Compose 컴파일 오류
`StudyScreen.kt`에서 `import androidx.compose.foundation.layout.weight`처럼 이름을 하나씩 지정해서
import했더니, Kotlin 컴파일러가 `Modifier.weight(1f)`를 Row/Column의 public `weight()` 함수가 아니라
Compose Foundation 내부에서만 쓰는 `internal` 프로�터티로 잘못 연결해 컴파일 오류가 났다
(`Cannot access 'val RowColumnParentData?.weight: Float': it is internal in file`).
Kotlin 2.4.0→2.3.20, Compose BOM 2025.09.00→2026.04.01로 각각 바꿔봐도 동일하게 실패했고,
`import androidx.compose.foundation.layout.*` (와일드카드)로 바꾸자 바로 해결됐다. 즉 버전 문제가
아니라 이름별 import 방식 자체의 문제였다. **결론적으로 Kotlin/BOM 버전은 Phase 0 값 그대로 유지**했다
(kotlin `2.3.20`으로 한 번 낮췄다가 최종적으로도 그대로 둠 — `2.4.0`보다 더 오래 검증된 안정판이라
오히려 이대로 두는 게 나아 보여 변경 유지. `composeBom`은 `2026.04.01`로 최종 확정).

| 항목 | Phase 0 값 | Phase 2 최종 값 |
|---|---|---|
| `kotlin` | `2.4.0` | **`2.3.20`** (시행착오 중 다운그레이드, 문제의 원인은 아니었지만 더 안정된 버전이라 유지) |
| `composeBom` | `2025.09.00` | **`2026.04.01`** (Kotlin 2.4.0 시기와 더 잘 맞는 버전으로 올려봤음. Compose 1.12.0부터 compileSdk 37을 요구한다는 것을 확인했고, 1.11.0(=이 BOM)까지는 compileSdk 36으로 안전) |

### 3. 테마 의존성 정리 방식
`Theme.EnglishWordApp`이 `Theme.Material3.DayNight.NoActionBar`(Material Components 라이브러리
리소스)를 참조하고 있어서, `material`(View) 의존성을 제거하면 테마 리소스가 깨진다. 그래서
`values/themes.xml`과 `values-night/themes.xml`의 부모를 플랫폼 전용 테마
(`android:Theme.Material.Light.NoActionBar` / `android:Theme.Material.NoActionBar`)로 바꿔
라이브러리 의존 없이 액션바 없는 창만 구성하도록 했다. 실제 색상/타이포는 이제 전부
`EnglishWordAppTheme`(Compose `MaterialTheme`)가 담당한다.

## 추가/삭제한 파일

**추가**
- `ui/theme/Theme.kt` — Material3 `lightColorScheme`/`darkColorScheme`, 시스템 다크모드 감지
- `ui/AppNavHost.kt` — `home`/`days`/`study/{dayNumber}` 3개 경로의 NavHost + 상하단 `Scaffold`
- `ui/ads/AdBanner.kt` — 기존 `AdView`(View)를 `AndroidView`로 감싼 배너 (테스트 광고 ID 그대로 유지)
- `ui/home/HomeScreen.kt`, `ui/day/DayListScreen.kt`, `ui/study/StudyScreen.kt`
- `MainActivity.kt` — `ComponentActivity` + `setContent`, 광고 초기화만 유지

**삭제**
- `MainActivity.java`, `app/src/main/res/layout/activity_main.xml`
- `com/voca/englishwordapp/compose/MainActivityCompose.kt` (Phase 0 빌드 검증용 임시 코드, 이제 불필요)

**변경**
- `app/build.gradle.kts` / `gradle/libs.versions.toml` — `appcompat`, `material`(View), `constraintlayout`,
  `activity`(plain) 의존성·버전 제거. `composeBom` 버전 갱신
- `values/themes.xml`, `values-night/themes.xml` — 테마 부모를 플랫폼 전용으로 변경

## day 목록 정렬 관련 참고
`DayListScreen`은 `WordRepository.getDays()`(Phase 1에서 만든, dayNumber 오름차순 정렬)를 그대로 쓴다.
기존 Java 버전은 `LinkedHashSet`으로 CSV 등장 순서를 따랐는데, 지금 CSV는 이미 day1→day30 순서로
등장하므로 화면상 순서는 동일하게 보인다 — 다만 이제는 데이터 순서가 바뀌어도 화면 순서가 깨지지
않는다는 게 차이점이다 (CLAUDE.md에 있던 "day 버튼 순서가 CSV 등장 순서에 의존" 이슈 해소).

## 빌드/테스트 결과
```
./gradlew.bat assembleDebug        BUILD SUCCESSFUL
./gradlew.bat testDebugUnitTest    BUILD SUCCESSFUL (13/13 통과, Phase 1과 동일)
./gradlew.bat lint                 BUILD SUCCESSFUL (치명 오류 없음, 리포트: app/build/reports/lint-results-debug.html)
```

## 다음 단계에서 다룰 것 (이번엔 의도적으로 안 한 것)
- 뜻이 여전히 항상 보임 (가리기 없음) — Phase 3
- 화면 회전 시 `currentIndex`가 초기화됨 (기존과 동일한 한계, `remember`만 사용) — Phase 3
- 진행도 표시, 셔플, 안다/모른다 버튼 없음 — Phase 3
- 스플래시 화면은 여전히 미작동 (Phase 7에서 다룰 기존 이슈, 이번에 건드리지 않음)

## 실기기 검증
Phase 0/1과 동일하게 보류 상태. 화면 흐름이 크게 바뀐 단계라 **가장 먼저 실기기(또는 에뮬레이터)
확인이 필요한 지점**이라는 점은 짚어드립니다 — 다음에 디바이스를 붙이면 이 단계부터 확인해 주시면
좋을 것 같습니다.
