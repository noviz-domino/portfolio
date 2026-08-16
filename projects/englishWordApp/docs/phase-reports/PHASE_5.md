# Phase 5 — TTS 발음 듣기

**상태**: 완료 (빌드/테스트/lint 통과, 경고 없음). **실기기 검증은 계속 보류** — TTS는 로그만으로는
"실제로 소리가 나는지"를 확인할 수 없는 대표적인 기능이라, 다음 실기기 확인 때 최우선으로
들어주시면 좋겠습니다.
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
안드로이드 내장 `TextToSpeech`를 감싼 `WordSpeakerState`를 추가하고, 학습 카드에 스피커 아이콘
(수동 재생)과 "자동 발음" 토글(카드 넘어갈 때마다 자동 재생, 기본 꺼짐)을 붙였다. TTS 엔진이나
영어 음성 데이터가 없는 기기에서도 크래시 없이 아이콘이 비활성화되고 스낵바로 한 번 안내한다.

## 추가된 동작

| 기능 | 동작 |
|---|---|
| 수동 발음 | 카드 좌상단 스피커 아이콘 탭 → 현재 단어 영어 발음 재생 (`Locale.US`) |
| 자동 발음 | 상단 "자동 발음" 스위치(기본 꺼짐) → 켜두면 카드가 바뀔 때마다 자동 재생 |
| 미지원 기기 대응 | TTS 초기화 실패 시 스피커 아이콘이 회색으로 비활성 표시되고, 스낵바로 "이 기기에서는 발음 재생을 사용할 수 없어요"를 **한 번만** 띄움 (크래시 없음) |

## 구현 메모

- **`WordSpeakerState`는 `isReady`/`initializationFailed`를 분리**했다. `TextToSpeech`의 초기화는
  비동기 콜백으로 오기 때문에, "아직 확인 중"(둘 다 false)과 "확인 결과 실패"(`initializationFailed
  = true`)를 구분해야 스낵바를 딱 한 번만 띄울 수 있다. 성공 여부는 `status == SUCCESS`뿐 아니라
  `setLanguage(Locale.US)` 결과도 함께 봐서, 엔진은 있는데 영어 데이터가 없는 경우도 잡아낸다.
- **`rememberWordSpeaker()`가 `DisposableEffect`로 `shutdown()`을 보장**한다 — 학습 화면을
  나갈 때 TTS 리소스를 정리하지 않으면 메모리/리소스가 누수된다.
- **스낵바는 화면 전역이 아니라 `StudyScreen` 안에서만 로컬로 띈다.** `AppNavHost`의 최상위
  `Scaffold`(광고 배너용)에는 `SnackbarHost`가 없어서, `StudyScreen` 안에 자체
  `Scaffold`+`SnackbarHostState`를 하나 더 두었다. 중첩 `Scaffold`가 살짝 어색하지만, 이번
  기능만을 위해 광고 배너까지 있는 최상위 네비게이션 구조를 뜯어고치는 것보다 낫다고 판단했다.
- **자동 발음 상태도 `StudyViewModel`의 `SavedStateHandle`에 저장**해서, 회전해도 토글이 풀리지
  않는다 (Phase 3에서 만든 패턴을 그대로 재사용).
- 아이콘은 `androidx.compose.material:material-icons-extended`로 확장했다 (Phase 3의 별 아이콘은
  `material-icons-core`에도 있었지만, `VolumeUp`/`VolumeOff`는 extended 세트에만 있다). 컴파일러가
  `Icons.Filled.VolumeUp`/`VolumeOff`를 deprecated로 표시해 `Icons.AutoMirrored.Filled.*`로 바꿨다
  (RTL 레이아웃에서 좌우가 자동으로 뒤집히는 최신 버전).

## 변경/추가 파일
- `tts/WordSpeaker.kt` (신규) — `WordSpeakerState` + `rememberWordSpeaker()`
- `ui/study/StudyViewModel.kt` — `isAutoSpeakEnabled` 상태 추가
- `ui/study/StudyScreen.kt` — 스피커 아이콘, 자동 발음 토글, 로컬 `Scaffold`+스낵바
- `app/build.gradle.kts` — `material-icons-core` → `material-icons-extended`로 교체

## 빌드/테스트 결과
```
./gradlew.bat assembleDebug        BUILD SUCCESSFUL (deprecation 경고까지 정리 후 재확인)
./gradlew.bat testDebugUnitTest    BUILD SUCCESSFUL (17/17, 이번 단계는 데이터 계층 변경 없음)
./gradlew.bat lint                 BUILD SUCCESSFUL
```

## 실기기 검증 시 확인해 주실 것
1. 스피커 아이콘 탭 → 영어 발음이 실제로 들리는지
2. "자동 발음" 켜고 스와이프/다음 버튼으로 이동 → 매번 자동으로 읽어주는지, 너무 빨리 겹쳐 재생되진 않는지
3. (가능하면) TTS 데이터가 없는 상태를 흉내내기 어렵겠지만, 최소한 정상 기기에서 스피커 아이콘이
   항상 활성 상태로 보이는지 확인 — 만약 회색으로 비활성 표시된다면 그 자체가 버그일 수 있습니다
4. 화면 회전 후에도 "자동 발음" 스위치 상태가 유지되는지
