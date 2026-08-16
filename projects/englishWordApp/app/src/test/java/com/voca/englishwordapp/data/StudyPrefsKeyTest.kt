package com.voca.englishwordapp.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

/**
 * [StudyPrefs] 자체는 SharedPreferences(Android Context)가 필요해 순수 JVM 단위 테스트로
 * 다루기 어렵다 (Robolectric 등 계측 도구가 필요 — 이번 개편 범위 밖). 대신 순수 함수인
 * [wordKey]만 검증한다: 이 키가 잘못되면 즐겨찾기/오답노트 전체가 엉키므로 중요하다.
 */
class StudyPrefsKeyTest {

    @Test
    fun `같은 day와 단어는 같은 키를 만든다`() {
        assertEquals(wordKey(1, "resume"), wordKey(1, "resume"))
    }

    @Test
    fun `day가 다르면 키가 달라진다`() {
        assertNotEquals(wordKey(1, "resume"), wordKey(2, "resume"))
    }

    @Test
    fun `단어가 다르면 키가 달라진다`() {
        assertNotEquals(wordKey(1, "resume"), wordKey(1, "applicant"))
    }

    @Test
    fun `키 형식은 dayNumber와 word를 구분자로 잇는다`() {
        assertEquals("12|anticipate", wordKey(12, "anticipate"))
    }
}
