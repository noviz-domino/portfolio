package com.voca.englishwordapp.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CsvWordParserTest {

    @Test
    fun `일반 행을 파싱한다`() {
        val word = CsvWordParser.parseLine("day1,resume,재개하다")
        assertEquals(Word(day = "day1", dayNumber = 1, word = "resume", meaning = "재개하다"), word)
    }

    @Test
    fun `뜻에 쉼표가 있으면 따옴표로 감싼 필드를 하나로 유지한다`() {
        val word = CsvWordParser.parseLine("day1,applicant,\"지원자, 신청자\"")
        assertEquals("지원자, 신청자", word?.meaning)
    }

    @Test
    fun `감싸는 따옴표는 결과에 남지 않는다`() {
        val word = CsvWordParser.parseLine("day1,resume,\"재개하다. ,'(résumé)이력서'랑 다름\"")
        assertEquals("재개하다. ,'(résumé)이력서'랑 다름", word?.meaning)
        assertTrue(word?.meaning?.contains('"') == false)
    }

    @Test
    fun `이스케이프된 이중 따옴표는 한 글자로 복원된다`() {
        val word = CsvWordParser.parseLine("day1,quote,\"그는 \"\"안녕\"\"이라고 말했다\"")
        assertEquals("그는 \"안녕\"이라고 말했다", word?.meaning)
    }

    @Test
    fun `필드가 3개 미만이면 건너뛴다`() {
        assertNull(CsvWordParser.parseLine("day1,resume"))
    }

    @Test
    fun `day 값에서 숫자를 뽑을 수 없으면 건너뛴다`() {
        assertNull(CsvWordParser.parseLine("(anticipation 예상)\""))
    }

    @Test
    fun `헤더 행은 parse에서 건너뛴다`() {
        val words = CsvWordParser.parse(listOf("Day,Word,Meaning", "day1,resume,재개하다"))
        assertEquals(1, words.size)
    }

    @Test
    fun `빈 줄은 무시한다`() {
        val words = CsvWordParser.parse(listOf("Day,Word,Meaning", "", "day1,resume,재개하다", "   "))
        assertEquals(1, words.size)
    }

    @Test
    fun `dayNumber는 day 뒤 숫자에서 추출된다`() {
        assertEquals(12, CsvWordParser.parseLine("day12,word,meaning")?.dayNumber)
        assertEquals(1, CsvWordParser.parseLine("day1,word,meaning")?.dayNumber)
    }

    @Test
    fun `실제 데이터의 과거 깨진 레코드는 더 이상 존재하지 않는다`() {
        // Phase 1에서 words.csv 원본의 개행 포함 레코드 3건을 병합했다.
        // 병합 후에는 각 조각이 독립된 줄로 남아있지 않아야 한다.
        assertNull(CsvWordParser.parseLine("(anticipation 예상)\""))
        assertNull(CsvWordParser.parseLine("(curtailment 단축)\""))
        assertNull(CsvWordParser.parseLine("(substantial 상당한, 재력이 있는)\""))
    }
}
