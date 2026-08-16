# Phase 3 — 학습 카드 UX (뜻 가리기·스와이프·진행도)

**상태**: 완료 (빌드/테스트/lint 통과). **실기기 검증은 계속 보류** (이번 단계는 스와이프 제스처 등
실제 터치 동작이 들어가 있어 **디바이스에서 직접 확인이 특히 중요한 단계**입니다)
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
학습 화면(`StudyScreen`)에 뜻 가리기, 스와이프 이동, 진행도, 셔플, 안다/모른다 버튼을 추가하고,
`StudyViewModel`을 도입해 화면 회전/프로세스 재생성에도 현재 위치가 유지되도록 했다 — 이번
개편에서 "암기가 되는 화면"으로 바뀌는 핵심 단계다.

## 추가된 동작

| 기능 | 동작 |
|---|---|
| 뜻 가리기 | 기본 숨김("뜻 보기 (탭)") → 카드 탭 시 `AnimatedContent`로 페이드 전환하며 공개 |
| 스와이프 | `HorizontalPager`로 좌우 이동. 기존 이전/다음 버튼과 양방향으로 동기화됨 |
| 진행도 | 상단에 `3 / 40` 텍스트 + `LinearProgressIndicator` |
| 셔플 | 스위치 토글. 켜면 새 시드로 순서를 다시 섞고 첫 단어로, 꺼면 원래(CSV 등장) 순서로 복귀 |
| 안다/모른다 | 뜻 공개 후에만 표시. 누르면 현재 인덱스에 세션 한정으로 기록하고 다음 단어로 자동 이동 |
| day 완료 | 마지막 단어에서 "다음"(또는 안다/모른다) 클릭 시 다이얼로그로 "다시 학습"/"day 목록으로" 선택 |
| 회전/프로세스 재생성 시 위치 유지 | `StudyViewModel`이 `study/{dayNumber}` NavBackStackEntry에 스코프되고, 모든 상태를 `SavedStateHandle`에도 함께 써서 유지 |

## 구현 메모 (다음에 이 코드를 다시 볼 때 참고할 것)

- **`StudyViewModel`의 프로퍼티는 전부 `by mutableStateOf(...)`로 감쌌다.** 일반 `var`로 두면
  Compose가 변경을 감지하지 못해 화면이 갱신되지 않는다 — ViewModel + Compose 조합에서 흔히
  놓치는 부분이라 명시적으로 적어둔다.
- **Pager ↔ ViewModel 양방향 동기화**: 버튼/마킹으로 `viewModel.currentIndex`가 바뀌면
  `LaunchedEffect(viewModel.currentIndex)`가 페이지를 따라 움직이고, 반대로 스와이프로
  `pagerState.currentPage`가 바뀌면 `LaunchedEffect(pagerState.currentPage)`가 ViewModel을
  갱신한다. 한쪽만 두면 스와이프와 버튼 중 하나가 다른 하나를 반영하지 못한다.
- **셔플된 순서(`displayWords`)는 `remember(words, isShuffled, shuffleSeed)`로 계산**하고,
  `currentIndex`는 항상 "`displayWords` 안에서의 위치"로 취급한다. 셔플을 껐다 켰다 해도
  시드가 `SavedStateHandle`에 남아있어 회전 후에도 같은 순서가 유지된다.
- **안다/모른다 기록(`markedKnown`)은 아직 저장하지 않는다.** ViewModel 안의
  `mutableStateMapOf<Int, Boolean>()`일 뿐이라 화면을 나가면 사라진다 — Phase 4에서
  `StudyPrefs`(SharedPreferences)로 옮겨 영속화한다.

## 변경 파일
- `ui/study/StudyViewModel.kt` (신규)
- `ui/study/StudyScreen.kt` (전면 재작성)
- `ui/AppNavHost.kt` — `StudyScreen`에 `onBackToDayList` 콜백(day 완료 다이얼로그에서 사용) 전달

## 빌드/테스트 결과
```
./gradlew.bat assembleDebug        BUILD SUCCESSFUL (첫 시도에 통과)
./gradlew.bat testDebugUnitTest    BUILD SUCCESSFUL (13/13, Phase 1과 동일 — 이번 단계는 데이터 계층을 건드리지 않음)
./gradlew.bat lint                 BUILD SUCCESSFUL
```

## 실기기 검증 — 특히 이번엔 꼭 확인이 필요한 항목
스와이프 제스처, 다이얼로그, `Switch` 토글은 텍스트 로그로는 "진짜 그렇게 동작하는지"를
확신할 수 없는 부분입니다. 다음에 디바이스를 연결하시면 이 순서로 봐주시면 좋겠습니다:
1. 카드 탭 → 뜻 공개, 안다/모른다 버튼 등장
2. 좌우 스와이프로 이동 + 이전/다음 버튼과 섞어서 써도 꼬이지 않는지
3. 셔플 토글 on/off + **화면 회전** → 순서와 현재 위치가 유지되는지
4. 마지막 단어에서 "다음" → 완료 다이얼로그 → "day 목록으로"/"다시 학습" 각각 확인
