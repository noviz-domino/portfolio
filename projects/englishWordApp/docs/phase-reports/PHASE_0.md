# Phase 0 — Kotlin/Compose 빌드 환경 전환

**상태**: 빌드 성공, **커밋 완료**. 실기기/에뮬레이터 검증은 사용자 요청에 따라 보류 (아래 "남은 작업" 참고)
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29
**커밋**:
- `a7e715e` AGP 9.3.1 / Gradle 9.5.0 업그레이드 및 프로젝트 문서 정비 (Phase 0 이전부터 있던 미커밋 변경분)
- `ef90a49` Kotlin/Compose 빌드 환경 전환

## 한 줄 요약
`app/build.gradle.kts` / `gradle.properties` / `gradle/libs.versions.toml`에 Kotlin + Jetpack Compose
빌드 지원을 추가했고, `./gradlew.bat assembleDebug`가 성공한다. 기존 `MainActivity.java` /
`activity_main.xml`은 이번 단계에서 건드리지 않았다 — Compose는 아직 검증용 코드 한 파일뿐이고
실제 화면 전환에는 연결되지 않았다.

## 계획과 달라진 점 (중요)

원래 기획서(Phase 0)는 `compileSdk`/`targetSdk`를 35 그대로 두고 갈 계획이었으나, 실제로 빌드해보니
최신 Compose 관련 라이브러리(`activity-compose`, `lifecycle-viewmodel-compose`)가 **compileSdk 36~37**을
요구해서 빌드가 실패했다. 사용자에게 확인한 결과, 마침 **2026-08-31부터 Google Play가 targetSdk를
최신 Android 출시 기준 1년 이내로 강제**하는 정책 마감이 걸려 있어, 이번 기회에 함께 처리하기로 결정했다.

| 항목 | 기획서 원안 | 실제 적용 |
|---|---|---|
| `compileSdk` | 35 유지 | **36** |
| `targetSdk` | 35 유지 | **36** (Play 정책 2026-08-31 마감 대응) |
| `minSdk` | 21→24 권장(보류 가능) | **24로 상향** (기획서 권장안 그대로 적용) |
| `android.builtInKotlin` | 1차: `false` 유지 + 별도 `kotlin-android` 플러그인 | **`true`로 전환**, 별도 플러그인 미적용 |

### `android.builtInKotlin` 관련 조사 내용
AGP 9.0부터는 **내장 Kotlin이 기본값**이고, `android.builtInKotlin=false` + 별도
`org.jetbrains.kotlin.android` 플러그인 조합은 **AGP 10에서 제거될 임시 우회 경로**라는 것을
공식 마이그레이션 가이드에서 확인했다. 그래서 기획서의 "1차 시도" 경로 대신 곧바로 권장 경로
(`builtInKotlin=true`, 별도 Kotlin 플러그인 없이 Compose 컴파일러 플러그인만 적용)로 갔다.

### SDK Platform 36 자동 설치 (사전 승인 없이 발생함 — 고지)
`compileSdk = 36`으로 올린 뒤 첫 빌드 시, Gradle/AGP가 로컬에 없던 **Android SDK Platform 36을
자동으로 다운로드하고 라이선스에 자동 동의**한 뒤 설치했다. 사용자 승인 없이 진행된 시스템 변경이라
사후 고지한다. 되돌릴 필요가 있으면 `C:\Users\HOME\AppData\Local\Android\Sdk\platforms\android-36`
폴더를 삭제하면 된다.

## 확정한 버전 (구현 시점 기준 최신 안정판 조사 결과)

| 항목 | 버전 | 비고 |
|---|---|---|
| Kotlin | `2.4.0` | 2026-06 출시 최신 안정판. Compose 컴파일러 플러그인 버전도 동일하게 고정 |
| Compose BOM | `2025.09.00` | 최신(`2026.06.01`) 대신 다소 보수적인 버전 선택 — 최신 BOM 계열은 `compileSdk 37`을 요구하는 라이브러리가 섞여 있어, 이번 개편에서 쓰는 API(Scaffold/NavHost/HorizontalPager/Material3)는 오래전부터 안정 지원되므로 compileSdk 36에서 문제없는 버전으로 낮춤 |
| `androidx.activity:activity-compose` | `1.13.0` | 최신 안정판. `compileSdk 36` 요구 — 통과 |
| `androidx.navigation:navigation-compose` | `2.9.8` | 최신 안정판 |
| `androidx.lifecycle:lifecycle-viewmodel-compose` | `2.10.0` | 최신(`2.11.0`)은 `compileSdk 37` 요구라 한 단계 낮춘 버전 사용 |

## 변경 파일

- `gradle.properties` — `android.builtInKotlin=false` → `true`
- `gradle/libs.versions.toml` — `kotlin`, `composeBom`, `activityCompose`, `navigationCompose`,
  `lifecycleViewmodelCompose` 버전 및 관련 라이브러리/플러그인 alias 추가
- `app/build.gradle.kts` — `kotlin-compose` 플러그인 적용, `compileSdk`/`targetSdk` 36,
  `minSdk` 24, `buildFeatures { compose = true }`, Compose 관련 의존성 추가
- `app/src/main/java/com/voca/englishwordapp/compose/MainActivityCompose.kt` (신규) —
  빌드 검증용 임시 코드. `AndroidManifest.xml`에는 등록하지 않아 앱 동작에는 영향 없음
- `CLAUDE.md` — 기술 스택 섹션에 Kotlin/Compose 도입 현황과 SDK 변경 사항 반영
- `docs/PLAN_v9.md` (신규) — 전체 개편 기획서 사본 저장

## 빌드 결과

```
./gradlew.bat assembleDebug
...
BUILD SUCCESSFUL in 2m 18s
37 actionable tasks: 34 executed, 3 up-to-date
```

## 남은 작업 (완료 기준 미충족 — 사용자 확인 필요)

기획서의 Phase 0 완료 기준은 "`installDebug`로 기존 Java 화면이 여전히 정상 동작"이다.
**이 PC에 연결된 Android 기기/에뮬레이터가 없어(`adb devices` 결과 없음) 이 부분을 아직 검증하지
못했다.** 빌드 자체는 성공했고 `MainActivity.java`/`activity_main.xml`을 전혀 건드리지 않았으므로
동작이 바뀔 이유는 없지만, 실기기 확인 전에는 Phase 0을 완료로 표시하지 않는다.

**필요한 것**: USB로 연결된 Android 기기(USB 디버깅 활성화) 또는 Android Studio에서 만든 에뮬레이터.

**사용자 결정 (2026-07-29)**: 지금은 실기기 검증을 보류하고 커밋만 먼저 진행. 이후 기능이 어느 정도
완성되면 Android Studio 가상 디바이스로 먼저 확인하고, 문제가 없으면 실제 안드로이드폰을 연결해
테스트할 계획. → 위 커밋 2건은 이 결정에 따라 검증 없이 이미 커밋됨.
