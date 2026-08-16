# englishWordApp 개편 기획서 (v9 목표)

## Context — 왜 고치는가

현재 앱은 `assets/words.csv`(1,225행, day1~30)를 읽어 day별로 단어를 순서대로 보여주는 것까지만 동작한다.
`MainActivity.java` 128줄에 전 로직이 들어있고, 화면은 하나의 레이아웃 안에서 `visibility` 토글로 전환된다.

문제는 **"학습이 성립하지 않는다"**는 점이다.

| 구분 | 현상 | 근거 |
|---|---|---|
| 치명 | 단어와 뜻이 **항상 동시 노출** → 암기 여부를 스스로 검증할 수 없다 | `activity_main.xml:81-104` — `wordText`/`meaningText` 둘 다 상시 표시 |
| 치명 | CSV 파서가 따옴표를 해석하지 않아 **1,225행 중 835행에 `"` 문자가 화면에 그대로 노출** | `MainActivity.java:83` `line.split(",", 3)` |
| 치명 | 깨진 레코드 3건이 **day 선택 화면에 쓰레기 버튼으로 표시**됨 | `(anticipation 예상)"`, `(curtailment 단축)"`, `(substantial 상당한, 재력이 있는)"` |
| 높음 | 학습 이력이 전혀 저장되지 않음. 화면 회전만으로 처음으로 되돌아감 | 상태가 Activity 필드(`allWords`/`filteredWords`/`currentIndex`)에만 존재, `onSaveInstanceState` 없음 |
| 높음 | 진행도(12/40), 셔플, 발음, 즐겨찾기, 퀴즈, 오답노트 전부 없음 | readme "미구현" 항목과 일치 |
| 중간 | day 버튼 순서가 CSV 등장 순서에 의존 → 데이터 편집 시 순서 붕괴 | `LinkedHashSet` 사용, 숫자 정렬 없음 |
| 중간 | `onBackPressed()` 오버라이드는 API 33+ 예측형 뒤로가기에서 deprecated | `MainActivity.java:121` |
| 중간 | 스플래시 테마가 존재하지만 동작하지 않음 (`Base.Theme.EnglishWordApp`이 light에서 주석 처리, 매니페스트도 Splash 테마 미적용) | `values/themes.xml`, `AndroidManifest.xml:13` |
| 낮음 | 광고 단위가 구글 테스트 ID, AdMob SDK 23.0.0(구버전), UMP 동의 미적용 | 개발 중에는 정상 — 배포 시점 과제 |

**목표 결과물**: Kotlin + Jetpack Compose로 재작성된 v9. 뜻 가리기 기반 학습 카드, 진행도 저장,
TTS 발음, 즐겨찾기/이어서 학습, 4지선다 퀴즈 + 오답노트를 갖춘 앱.

---

## 확정된 방향 (사용자 결정)

| 항목 | 결정 |
|---|---|
| 1차 목표 | **학습 기능 강화** (데이터 정합성 수정은 선행 단계로 포함) |
| 데이터 저장 | **`words.csv` 읽기전용 유지 + SharedPreferences에 학습 기록만 저장** (Room 미도입) |
| 추가 기능 | 뜻 가리기/카드 뒤집기, 4지선다 퀴즈, TTS 발음, 즐겨찾기 + 이어서 학습 |
| 언어/아키텍처 | **Kotlin + Jetpack Compose 재작성** |

### 이 결정에 따른 파급 효과 (개발 전 인지 필요)

1. **`CLAUDE.md`의 "Java 전용 / `android.builtInKotlin=false`" 규칙이 무효화**된다. Phase 0에서 CLAUDE.md를 함께 갱신한다.
2. Compose 재작성은 **실질적으로 신규 개발 수준의 작업량**이다. 그래서 Phase 2(기능 추가 없는 순수 이식)를 독립시켜, 그 시점에 "지금과 똑같이 동작하는 Compose 앱"을 확보한 뒤 기능을 올린다.
3. APK 크기가 약 2~3MB 증가한다. Phase 7에서 R8(`isMinifyEnabled`) 활성화를 검토한다.
4. **`minSdk` 21 → 24 상향을 권장**한다. Compose는 21에서도 동작하지만 24부터 legacy multidex/desugar 이슈가 사라진다. (21 유지를 원하면 그대로 진행 가능 — 알려주시면 조정)
5. XML 레이아웃과 `appcompat`/`constraintlayout`/`material`(View) 의존성은 Phase 2 완료 시점에 제거된다.

---

## 목표 패키지 구조

```
com.voca.englishwordapp/
├── MainActivity.kt              # ComponentActivity + setContent (유일한 Activity)
├── data/
│   ├── Word.kt                  # data class Word(day, dayNumber, word, meaning)
│   ├── CsvWordParser.kt         # RFC4180 준수 파서 (순수 함수 → 단위 테스트 대상)
│   ├── WordRepository.kt        # assets 1회 로드 + 캐싱, day 목록 자연 정렬
│   └── StudyPrefs.kt            # SharedPreferences 래퍼 (진행도/즐겨찾기/오답)
├── ui/
│   ├── theme/                   # Color.kt, Type.kt, Theme.kt (Material3 light/dark)
│   ├── AppNavHost.kt            # navigation-compose 그래프
│   ├── ads/AdBanner.kt          # AndroidView로 AdView 래핑
│   ├── home/HomeScreen.kt
│   ├── day/DayListScreen.kt     # LazyVerticalGrid + 학습 완료 배지
│   ├── study/StudyScreen.kt     # HorizontalPager 카드 + StudyViewModel
│   ├── quiz/QuizScreen.kt       # 4지선다 + QuizViewModel + 결과 화면
│   └── review/ReviewScreen.kt   # 즐겨찾기 / 오답노트
└── tts/WordSpeaker.kt           # TextToSpeech 래퍼 (lifecycle 연동)
```

---

## 개발 단계

각 Phase는 **독립적으로 빌드·설치·커밋이 가능한 단위**다. 한 Phase 완료 = 한 커밋.

### Phase 0 — Kotlin/Compose 빌드 전환 (기능 변경 0)

> 목적: 빌드 파이프라인만 바꾸고, 화면 하나 띄워 통과를 확인한다. 여기서 막히면 이후 전부 막히므로 반드시 분리한다.

**작업**
- `feature/compose-rewrite` 브랜치 생성 (main의 동작하는 Java 버전 보존)
- `gradle/libs.versions.toml`: `kotlin`, `composeBom`, `activityCompose`, `navigationCompose`, `lifecycleViewmodelCompose` 버전/라이브러리 추가.
  플러그인에 `kotlin-android`(`org.jetbrains.kotlin.android`), `kotlin-compose`(`org.jetbrains.kotlin.plugin.compose`) 추가
  → **버전은 구현 시점에 AGP 9.3.1과 호환되는 최신 안정판으로 확인 후 확정** (임의 지정 금지)
- `gradle.properties`: `android.builtInKotlin=false` 유지 여부 결정.
  1차 시도는 표준 경로(별도 Kotlin 플러그인 + Compose 컴파일러 플러그인). 실패 시 대안으로 `builtInKotlin=true` + AGP 내장 Kotlin DSL 사용
- `app/build.gradle.kts`: `buildFeatures { compose = true }`, `kotlin { jvmToolchain(11) }`(또는 `kotlinOptions.jvmTarget`), `minSdk = 24`, Compose BOM + `ui`/`material3`/`ui-tooling-preview` + `debugImplementation ui-tooling`, `ui-test-manifest`
- `MainActivityCompose.kt` 임시 생성 → "Hello" 하나만 렌더 (기존 `MainActivity.java`는 이 단계에서 건드리지 않음)
- `CLAUDE.md` 갱신: 언어(Kotlin), UI(Compose), 아키텍처 섹션, 자주 쓰는 명령어

**완료 기준**
```bash
./gradlew.bat clean assembleDebug
```
빌드 성공 + `installDebug`로 기존 Java 화면이 여전히 정상 동작.

**커밋**: `Kotlin/Compose 빌드 환경 전환`

---

### Phase 1 — 데이터 계층 + CSV 정합성 수정 (UI 변경 0)

> 목적: 따옴표 노출/깨진 레코드/day 정렬 문제를 근본에서 제거하고, **프로젝트 최초의 실질 단위 테스트**를 만든다.

**작업**
- `data/Word.kt` — `data class Word(val day: String, val dayNumber: Int, val word: String, val meaning: String)`.
  `dayNumber`는 `"day12"` → `12` 파싱 결과 (정렬 키)
- `data/CsvWordParser.kt` — RFC4180 준수 파서:
  - `"..."` 감싸인 필드 내부의 쉼표 보존, 감싸는 따옴표는 **제거**
  - `""` 이스케이프 → `"` 로 복원
  - 필드가 3개 미만이거나 `dayNumber` 파싱 실패 행은 **스킵**(깨진 3건이 자동 배제됨)
  - 헤더 1줄 스킵, 빈 줄 무시, BOM 제거
- `data/WordRepository.kt` — `getAllWords(context)` 1회 로드 후 메모리 캐싱, `getDays(): List<DaySummary>`(dayNumber 오름차순 정렬, 단어 수 포함), `getWords(dayNumber)`
- `app/src/main/assets/words.csv` 정리 — 깨진 3행을 직전 레코드에 병합. **한 줄 = 한 단어 규칙 준수** (CLAUDE.md 데이터 규칙)
- `app/src/test/.../CsvWordParserTest.kt` — 케이스: 일반 행, 뜻에 쉼표, 따옴표 감싸기, `""` 이스케이프, 필드 부족, 헤더, 빈 줄
- `ExampleUnitTest` 템플릿 삭제

**완료 기준**
```bash
./gradlew.bat testDebugUnitTest
```
전 테스트 통과 + 파서 결과에 `"` 문자가 남은 항목 0건 + day 목록이 day1…day30 순서로 30개.

**커밋**: `CSV 파서 RFC4180 준수 및 데이터 정합성 수정`

---

### Phase 2 — Compose UI 패리티 이식 (기능 추가 0)

> 목적: **현재와 똑같이 동작하는** Compose 앱을 만든다. 여기서 XML/Java를 완전히 제거한다.

**작업**
- `ui/theme/` — Material3 `lightColorScheme`/`darkColorScheme`, Typography. 하드코딩 색 대신 테마 색 사용
- `ui/AppNavHost.kt` — navigation-compose, 루트: `home` → `days` → `study/{dayNumber}`.
  **뒤로가기는 NavController가 처리** → deprecated `onBackPressed` 문제 해소
- `ui/ads/AdBanner.kt` — `AndroidView { AdView(it).apply { setAdSize(AdSize.BANNER); adUnitId = ... ; loadAd(...) } }`.
  광고 단위는 **테스트 ID 유지**(`ca-app-pub-3940256099942544/6300978111`), `MobileAds.initialize`는 MainActivity에서 1회
- `HomeScreen` (제목 + "단어보기"), `DayListScreen` (LazyVerticalGrid, day 카드), `StudyScreen` (단어/뜻 + 이전/다음)
  — 이 단계에서는 **뜻을 그대로 노출**해 현행 동작과 동일하게 유지
- 상/하단 배너는 `Scaffold`의 topBar/bottomBar 위치에 고정
- `MainActivity.kt` 작성, **`MainActivity.java` / `activity_main.xml` 삭제**, `appcompat`·`constraintlayout`·`material`(View) 의존성 제거
- 테마 부모를 `Theme.Material3.DayNight.NoActionBar` → Compose용 최소 테마로 정리

**완료 기준**
- `installDebug` 후 실기기에서: 홈 → day 목록 30개 → 단어 이동 → 뒤로가기 3단계(학습→day→홈→종료)가 현행과 동일하게 동작
- 상/하단 배너 노출 확인
- **화면 회전 시 크래시 없음** (상태 초기화는 Phase 3에서 해결)

**커밋**: `Compose UI 이식 및 XML/Java 레이어 제거`

---

### Phase 3 — 학습 카드 UX (핵심 개편)

> 목적: "암기가 되는" 학습 화면. 이번 개편의 본체.

**작업**
- **뜻 가리기**: 뜻 영역 기본 숨김(`뜻 보기` 플레이스홀더) → 카드 탭 시 `AnimatedContent`로 공개.
  기본값은 **숨김**(가정 — 항상 공개를 원하면 설정 토글로 전환 가능하게 열어둠)
- **스와이프 이동**: `HorizontalPager`로 좌우 스와이프. 기존 `이전/다음` 버튼도 병존
- **진행도**: 상단에 `12 / 40` 텍스트 + `LinearProgressIndicator`
- **셔플 토글**: day 내 단어 순서 무작위화 (시드 고정으로 회전 시 순서 유지)
- **안다/모른다 버튼**: 뜻 공개 후 표시. 이 시점에는 화면 상태만 갱신(영속화는 Phase 4)
- **상태 보존**: `StudyViewModel` + `rememberSaveable`로 회전/프로세스 재생성 시 현재 인덱스·공개 여부 유지
- 마지막 단어에서 `다음` → "day 학습 완료" 시트(다시 학습 / day 목록으로)

**완료 기준**
- 뜻이 기본 숨김, 탭으로 공개
- 스와이프·버튼 양쪽으로 이동, 진행도 정확
- **회전해도 현재 단어 위치 유지** (기존 대비 명확한 개선점)

**커밋**: `단어 카드 뜻 가리기·스와이프·진행도 추가`

---

### Phase 4 — 학습 기록 저장 (SharedPreferences)

> 목적: 앱을 껐다 켜도 이어지게 만든다. 이후 오답노트/퀴즈의 토대.

**작업**
- `data/StudyPrefs.kt` — 단일 `SharedPreferences`(`study_prefs`) 래퍼. 저장 키:
  | 키 | 형태 | 용도 |
  |---|---|---|
  | `last_day` | Int | 마지막 학습 day |
  | `progress_day_{n}` | Int | 해당 day의 마지막 인덱스 |
  | `completed_days` | StringSet | 끝까지 본 day |
  | `favorites` | StringSet (`"12\|resume"`) | 즐겨찾기 |
  | `unknown_words` | StringSet | "모른다" 표시 단어 |
  - 단어 식별 키는 `"$dayNumber|$word"` 규칙으로 통일 (CSV 편집 시 인덱스 이동에 안전)
- **이어서 학습**: 홈에 "day 12에서 이어보기 (18/40)" 카드. `last_day`/`progress_day_{n}` 없으면 숨김
- **즐겨찾기**: 카드에 별 아이콘 토글
- **day 목록에 완료 배지**: `DayListScreen`에서 완료 day에 체크 표시, 진행 중 day에 진행률 표시
- Phase 3의 "안다/모른다"를 `unknown_words`에 영속화
- `ui/review/ReviewScreen.kt` — 즐겨찾기 목록 / 모르는 단어 목록 탭. 목록 → 그 집합만으로 학습 카드 진입
- 홈에 "초기화" (진행도 전체 삭제, 확인 다이얼로그 필수)

**완료 기준**
- 앱 강제 종료 후 재실행 → 이어서 학습 카드가 정확한 위치 표시
- 즐겨찾기/모르는 단어가 재실행 후에도 유지
- 즐겨찾기 목록만으로 학습 카드 진입 가능

**커밋**: `학습 진행도·즐겨찾기·오답 단어 저장 기능 추가`

---

### Phase 5 — TTS 발음 듣기

**작업**
- `tts/WordSpeaker.kt` — `TextToSpeech(context)` 래퍼. `Locale.US`, `onInit` 성공 여부 보관, `shutdown()`을 `DisposableEffect`에서 호출
- 학습 카드에 스피커 아이콘 → 단어 발음. 카드 진입 시 자동 재생 여부는 **설정 토글**(기본 off)
- TTS 엔진/영어 데이터 미설치 기기 대응: 아이콘 비활성 + 1회 안내 스낵바 (크래시 금지)
- 퀴즈 화면에도 동일 컴포넌트 재사용

**완료 기준**
- 실기기에서 발음 재생 확인
- TTS 미지원 상황을 가정한 경로에서 크래시 없음

**커밋**: `TTS 단어 발음 재생 기능 추가`

---

### Phase 6 — 4지선다 퀴즈 + 오답노트

**작업**
- `ui/quiz/QuizViewModel.kt`
  - 출제 범위 선택: 특정 day / 여러 day / 즐겨찾기 / 모르는 단어
  - 문제 생성: 정답 단어 1 + **같은 범위 밖에서 뽑은 오답 뜻 3개**(중복·동일 뜻 배제)
  - 방향: 기본 **영어 단어 → 한글 뜻**. 한→영 토글은 선택 구현(가정 — 다른 기본값 원하면 조정)
  - 문항 수 기본 10 (범위가 10개 미만이면 전체)
- `QuizScreen` — 문항/선택지/즉시 정오 피드백/진행도
- `QuizResultScreen` — 점수, 정답률, 틀린 단어 목록. **틀린 단어는 `unknown_words`에 자동 등록**
- 결과 화면에서 "틀린 단어만 다시 학습" → Phase 4의 학습 카드로 진입
- `getQuestionCount` 등 출제 로직은 순수 함수로 분리해 **단위 테스트 작성** (오답 중복 없음, 정답 항상 포함)

**완료 기준**
- `testDebugUnitTest` 통과 (출제 로직)
- 실기기: day 선택 → 10문항 → 결과 → 틀린 단어가 오답노트에 반영

**커밋**: `4지선다 퀴즈 모드 및 오답노트 추가`

---

### Phase 7 — 마감 / 배포 품질

**작업**
- **스플래시 정상화**: `values/themes.xml`에 `Base.Theme.EnglishWordApp` 정의(현재 주석 처리 상태), 매니페스트 테마를 `Theme.EnglishWordApp.Splash`로 교체, `installSplashScreen()` 호출. 이미 의존성(`core-splashscreen`)은 있음
- **다크 모드 점검**: 전 화면 light/dark 대비 확인 (Compose Preview 2종)
- **문자열 리소스화**: 신규 UI 문자열을 `strings.xml`로 이동 (Compose에서는 `stringResource` 사용이 자연스러움 — 기존 하드코딩 관례에서 이 단계만 예외 적용)
- **광고 정책 검토**: `play-services-ads` 최신 버전 상향 + UMP(동의) 필요성 검토. **광고 단위 ID는 테스트 ID 유지** (실 ID 교체는 별건으로 사용자가 결정)
- **버전 갱신**: `versionCode = 9`, `versionName = "9.0"` (그 두 줄만 수정)
- R8 활성화(`isMinifyEnabled = true`) 후 릴리즈 빌드 정상 동작 확인 — 문제 시 보류
- **문서 갱신**: `readme.md`의 잘못된 기술 스택 기술(Kotlin/minSdk 24/MVVM 등 실제와 불일치했던 부분)을 새 실제 값으로 정정, 기능 목록의 "미구현" 항목 갱신, `PROJECT_STRUCTURE.md` 트리 갱신, `CLAUDE.md` 최종 동기화
- `lint` 실행 후 신규 경고 정리

**완료 기준**
```bash
./gradlew.bat clean lint testDebugUnitTest assembleRelease
```
전부 통과 + 실기기에서 전체 플로우 1회 완주.

**커밋**: `스플래시·다크모드·문서 정비, 버전9상승 <날짜>`

---

## 이번 범위에서 제외 (추후 별건)

| 항목 | 제외 이유 |
|---|---|
| Room DB 도입 | SharedPreferences로 이번 기능 전부 충족. 앱 내 단어 편집이 필요해지는 시점에 재검토 |
| 앱 내 단어 추가/수정/삭제 UI | CSV 읽기전용 방침의 직접 결과. Room 도입과 함께 묶어야 함 |
| 실제 AdMob 광고 단위 ID 교체 | 수익화 판단이 필요한 별도 의사결정 |
| 상세 학습 통계 대시보드(일별 그래프 등) | 오답노트/진행도가 안정된 뒤 데이터가 쌓여야 의미 있음 |
| 위젯 / 학습 알림 푸시 | 별도 기획 필요 |
| targetSdk 36 상향 | Play 정책 마감일 기준으로 별도 처리 (현재 35는 유효) |
| `englishWordApp.jks` / `app/release/*` 의 git 추적 정리 | 저장소 정책 변경이라 사용자 판단 필요 (키스토어가 커밋되어 있는 상태는 별도로 논의 권장) |

---

## 전체 검증 방법

**단위 테스트** (Phase 1, 6에서 추가)
```bash
./gradlew.bat testDebugUnitTest
```

**실기기 확인** (각 Phase 완료 시)
```bash
./gradlew.bat installDebug
```

**최종 회귀 시나리오** (Phase 7)
1. 앱 실행 → 스플래시 → 홈
2. 단어보기 → day 목록 30개, 순서 day1→day30, 쓰레기 항목 없음
3. day1 진입 → 뜻 숨김 상태 → 탭하면 공개, **따옴표 문자 노출 없음**
4. 스와이프/버튼 이동, 진행도 정확, 발음 재생
5. 몇 개를 "모른다"·즐겨찾기 표시 → **앱 강제 종료 후 재실행 → 이어서 학습 카드가 정확한 위치 표시**
6. 퀴즈 10문항 → 결과 → 틀린 단어가 오답노트에 등록 → "틀린 단어만 다시 학습" 동작
7. **화면 회전** → 현재 위치 유지, 크래시 없음
8. 다크 모드 전환 → 전 화면 가독성 확인

---

## 진행 방식 제안

- Phase 0부터 순서대로, **한 Phase 끝날 때마다 실기기 확인 후 커밋**하고 다음으로 넘어간다
- Phase 0에서 Kotlin/Compose 빌드가 막히면 즉시 보고하고 플러그인 조합(표준 Kotlin 플러그인 ↔ AGP 내장 Kotlin)을 조정한다
- 커밋 메시지는 한국어, 기존 관례 유지 (문서 변경은 `docs: `, 기능 변경은 접두어 없이 요약)
- 작업은 `feature/compose-rewrite` 브랜치에서 진행하고, Phase 2(패리티 확보) 이후에 main 병합 시점을 논의한다
