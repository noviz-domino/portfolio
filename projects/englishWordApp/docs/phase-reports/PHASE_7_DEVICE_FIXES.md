# Phase 7 후속 — 실기기 확인에서 발견된 버그 수정

**상태**: 완료, **실기기에서 직접 확인함** (Galaxy S23+ 계열, `SM-S916N`)
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 배경
Phase 7 완료 후 사용자가 Android Studio로 실제 휴대폰에 앱을 설치해 처음으로 실기기 확인을
진행했다. 그 과정에서 이 개편 전체(Phase 0~7)에서 로그/빌드만으로는 잡을 수 없었던 버그
2건을 발견해 알려주셨고, adb로 화면을 캡처해 직접 원인을 진단하고 고쳤다.

## 버그 1 — 학습 카드의 스피커/즐겨찾기 아이콘이 클릭되지 않음

**증상**: 사용자가 "왼쪽 상단 소리 아이콘을 눌러도 반응이 없고, 별 모양도 클릭이 안 된다"고 보고.
직접 원인을 짚어주기도 했다 — "단어 뜻이 보이는 탭에 가려져있는거같아."

**원인**: `StudyScreen.kt`의 `WordCard`에서 `Box` 안에 아이콘 버튼 2개를 먼저 선언하고, 그 아래에
전체 화면 크기의 `Column`(뜻 공개용 탭 영역, `Modifier.fillMaxSize().clickable(...)`)을 나중에
선언했다. Compose의 `Box`는 **나중에 선언된 자식이 위에 그려지므로**, 화면 전체를 덮는 투명한
탭 영역이 실제로는 아이콘들보다 위에 있어서 터치를 전부 가져가고 있었다. 즉 아이콘 자체는
정상이었지만 그 위에 보이지 않는 레이어가 덮여 있던 것.

**수정**: 선언 순서를 바꿔서 탭 영역(`Column`)을 먼저, 아이콘 버튼들을 나중에(위에) 오도록 했다.

**실기기 검증**: 즐겨찾기 별 클릭 → 색이 채워짐(회색→보라) 확인. 스피커 클릭 →
`adb logcat`에서 `com.google.android.tts` 패키지가 `content type=SPEECH`로 오디오 재생을
시작한 로그를 확인 (스크린샷만으로는 소리 재생 자체를 확인할 수 없어 로그로 대체 검증).

## 버그 2 — 광고가 상태바/네비게이션 바 뒤에 깔림

**증상**: "화면 상단 네비게이션 바에서 시간도 봐야 하는데 광고가 그 뒤에 보여서 불편하다.
아래쪽도 뒤로가기 버튼 있는 곳에 광고가 배경으로 있어서 불편하다."

**원인**: 이 앱은 `targetSdk` 36(Android 15+ 기준)이라 **edge-to-edge가 강제**된다 —
앱 콘텐츠가 상태바/네비게이션 바 영역까지 그려지는 게 기본값이고, 앱이 직접 그 영역을
피해서 그려야 한다. `AppNavHost`의 `Scaffold`에 있는 상/하단 `AdBanner`에는 그런 처리가
전혀 없어서, 광고가 상태바(시계)와 네비게이션 바(뒤로가기 버튼 등) 영역까지 그려지고 있었다.

**수정**: 상단 `AdBanner`에 `Modifier.windowInsetsPadding(WindowInsets.statusBars)`,
하단 `AdBanner`에 `Modifier.windowInsetsPadding(WindowInsets.navigationBars)`를 추가해서
각각 상태바/네비게이션 바 높이만큼 스스로 여백을 두게 했다.

**실기기 검증**: 홈 화면 스크린샷에서 상단 광고가 시계 아래로, 하단 광고가 네비게이션 바
위로 내려가 겹치지 않는 것을 확인.

## 부수적으로 관찰한 것 (아직 안 고침)
day 목록을 스크롤하는 중간 스크린샷에서 마지막에 보이는 항목(day13/14 부근)이 하단 광고와
살짝 겹쳐 보이는 경우가 있었다. `DayListScreen`의 `LazyColumn`이 `contentPadding`으로 하단
여백을 주고 있는데(`Scaffold`의 `innerPadding` + 20dp), WindowInsets 값이 첫 프레임에는
0으로 보고되고 한 프레임 뒤에 실제 값으로 갱신되는 것으로 알려진 Compose의 타이밍 이슈일
가능성이 있다. 사용자가 명시적으로 보고한 문제는 아니라서 이번엔 손대지 않았고, 재현되는지
다음 실기기 확인 때 한 번 더 봐주시면 좋겠다.

## 변경 파일
- `ui/study/StudyScreen.kt` — `WordCard` 내부 `Box` 자식 순서 변경 (탭 영역 → 아이콘 순)
- `ui/AppNavHost.kt` — 상/하단 `AdBanner`에 `windowInsetsPadding` 추가

## 빌드/테스트
```
./gradlew.bat testDebugUnitTest lint
BUILD SUCCESSFUL (25/25 테스트, lint 신규 경고 없음)
```
`installDebug`로 실기기에 직접 설치해 확인함.
