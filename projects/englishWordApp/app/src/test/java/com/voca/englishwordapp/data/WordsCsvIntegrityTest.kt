package com.voca.englishwordapp.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * `assets/words.csv` 원본 데이터가 실제로 정합성 문제 없이 파싱되는지 확인한다.
 * (CsvWordParserTest는 파서 로직 자체를, 이 테스트는 실제 데이터셋 결과를 검증한다.)
 */
class WordsCsvIntegrityTest {

    private fun loadCsvLines(): List<String> {
        // 단위 테스트 실행 시 작업 디렉터리는 app 모듈 루트(app/)이다.
        val file = File("src/main/assets/words.csv")
        assertTrue("words.csv를 찾을 수 없다: ${file.absolutePath}", file.exists())
        return file.readLines(Charsets.UTF_8)
    }

    @Test
    fun `파싱 결과에 따옴표 문자가 남은 항목이 없다`() {
        val words = CsvWordParser.parse(loadCsvLines())
        val leaked = words.filter { it.word.contains('"') || it.meaning.contains('"') }
        assertTrue("따옴표가 남은 단어: $leaked", leaked.isEmpty())
    }

    @Test
    fun `day 목록은 day1부터 day30까지 30개다`() {
        val words = CsvWordParser.parse(loadCsvLines())
        val dayNumbers = words.map { it.dayNumber }.distinct().sorted()
        assertEquals((1..30).toList(), dayNumbers)
    }

    @Test
    fun `과거에 깨져 있던 3개 레코드 잔재가 더 이상 없다`() {
        val words = CsvWordParser.parse(loadCsvLines())
        val brokenLeftovers = words.filter {
            it.word.startsWith("(") || it.meaning.trim().endsWith("\"")
        }
        assertFalse("깨진 레코드 잔재가 남아있다: $brokenLeftovers", brokenLeftovers.isNotEmpty())
    }
}
