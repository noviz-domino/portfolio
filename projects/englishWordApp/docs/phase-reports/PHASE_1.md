# Phase 1 — 데이터 계층 + CSV 정합성 수정

**상태**: 완료 (단위 테스트 통과, `assembleDebug`도 정상)
**브랜치**: `feature/compose-rewrite`
**작업일**: 2026-07-29

## 한 줄 요약
`words.csv`를 RFC4180 규칙으로 파싱하는 Kotlin 데이터 계층(`Word`, `CsvWordParser`,
`WordRepository`)을 추가하고, 개행이 섞여 깨져 있던 레코드 3건을 원본 CSV에서 직접 병합했다.
UI(`MainActivity.java`, `activity_main.xml`)는 전혀 건드리지 않았다.

## 문제였던 것 → 고친 것

| 문제 | 원인 | 조치 |
|---|---|---|
| 뜻에 쉼표가 있는 항목(1,225행 중 835행)에서 `"` 문자가 화면에 그대로 노출 | `line.split(",", 3)`이 따옴표를 해석하지 않음 | `CsvWordParser.splitCsvLine`이 따옴표로 감싼 구간의 쉼표는 보존하고 감싸는 따옴표는 제거 |
| day19/day20에 깨진 레코드 3건 (`(anticipation 예상)"` 등) | 뜻 안의 개행이 다음 줄로 분리되어 읽힘 | `words.csv` 원본에서 3건을 각각 이전 줄과 한 줄로 병합 (아래 참고) |
| day 버튼 순서가 CSV 등장 순서에 의존 | `LinkedHashSet` | `WordRepository.getDays()`가 `dayNumber` 기준 오름차순 정렬 |

### 병합한 CSV 레코드 3건 (`app/src/main/assets/words.csv`)
```
day19,anticipate,"예상하다, 기대하다 (anticipation 예상)"
day20,curtail,"~을 줄이다, 삭감하다 (curtailment 단축)"
day20,substantially,"크게, 상당히 (substantial 상당한, 재력이 있는)"
```
(원래는 각각 2줄에 걸쳐 있었음. 개행을 공백으로 바꿔 한 줄로 합쳤고, 뜻 안에 쉼표가 있어 따옴표는 유지)

## 추가한 파일

- `app/src/main/java/com/voca/englishwordapp/data/Word.kt` — `data class Word(day, dayNumber, word, meaning)`
- `app/src/main/java/com/voca/englishwordapp/data/CsvWordParser.kt` — RFC4180 파서 (순수 함수, `internal` 공개로 테스트 가능)
- `app/src/main/java/com/voca/englishwordapp/data/WordRepository.kt` — assets 1회 로드 + 캐싱, `getDays()`/`getWords(dayNumber)`
- `app/src/test/java/com/voca/englishwordapp/data/CsvWordParserTest.kt` — 파서 단위 테스트 10건
  (일반 행, 쉼표 포함 뜻, 따옴표 제거, `""` 이스케이프, 필드 부족, day 파싱 실패, 헤더 스킵, 빈 줄, dayNumber 추출, 과거 깨진 레코드 형태가 이제 스킵되는지)
- `app/src/test/java/com/voca/englishwordapp/data/WordsCsvIntegrityTest.kt` — **실제 `words.csv` 데이터셋**으로
  돌려보는 회귀 테스트 3건 (따옴표 잔존 0건 / day1~day30 정확히 30개 / 깨진 레코드 잔재 없음).
  파서 로직 테스트와 별개로, 데이터 자체의 정합성을 앞으로도 계속 검증해준다
- `app/src/main/assets/words.csv` — 깨진 3행 병합 (1226행 → 1223행, 헤더 포함)
- `app/src/test/java/com/voca/englishwordapp/ExampleUnitTest.java` — 삭제 (Android Studio 기본 템플릿)

## 테스트 결과

```
./gradlew.bat testDebugUnitTest
BUILD SUCCESSFUL

CsvWordParserTest       : tests=10 failures=0 errors=0
WordsCsvIntegrityTest   : tests=3  failures=0 errors=0
```

```
./gradlew.bat assembleDebug
BUILD SUCCESSFUL
```

## 아직 연결 안 된 부분 (의도된 것)
`WordRepository`는 아직 `MainActivity.java`에서 쓰이지 않는다. 기존 화면은 여전히 자체
`loadWordsFromCSV()`(따옴표 미해석 버전)로 동작한다. 새 데이터 계층을 실제 화면에 연결하는 작업은
Phase 2(Compose UI 이식)에서 진행한다 — 그때 `MainActivity.java` 자체를 교체하기 때문이다.

## 실기기 검증
이번 단계는 데이터/로직 레이어만 다뤄서 UI 동작에 영향이 없다. Phase 0과 동일하게 실기기 확인은
사용자 계획(에뮬레이터 → 실기기)에 맞춰 나중에 일괄 진행.
