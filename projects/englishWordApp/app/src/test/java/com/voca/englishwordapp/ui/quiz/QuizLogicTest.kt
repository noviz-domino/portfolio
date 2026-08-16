package com.voca.englishwordapp.ui.quiz

import com.voca.englishwordapp.data.Word
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

class QuizLogicTest {

    private fun word(day: Int, word: String, meaning: String) =
        Word(day = "day$day", dayNumber = day, word = word, meaning = meaning)

    /** day1 범위 20단어, day2~3에 오답 후보 40단어. */
    private val scope = (1..20).map { word(1, "word$it", "뜻$it") }
    private val distractorPool = (1..40).map { word(2 + it % 2, "other$it", "다른뜻$it") }

    @Test
    fun `문항 수는 기본 10개다`() {
        val questions = QuizLogic.buildQuiz(scope, distractorPool, random = Random(1))
        assertEquals(QuizLogic.DEFAULT_QUESTION_COUNT, questions.size)
    }

    @Test
    fun `범위가 문항 수보다 적으면 범위 전체를 쓴다`() {
        val smallScope = scope.take(3)
        val questions = QuizLogic.buildQuiz(smallScope, distractorPool, random = Random(1))
        assertEquals(3, questions.size)
    }

    @Test
    fun `빈 범위는 빈 퀴즈를 만든다`() {
        assertEquals(emptyList<QuizQuestion>(), QuizLogic.buildQuiz(emptyList(), distractorPool))
    }

    @Test
    fun `각 문항은 선택지 4개를 갖는다`() {
        val questions = QuizLogic.buildQuiz(scope, distractorPool, random = Random(42))
        questions.forEach { assertEquals(QuizLogic.CHOICE_COUNT, it.choices.size) }
    }

    @Test
    fun `선택지는 중복이 없다`() {
        val questions = QuizLogic.buildQuiz(scope, distractorPool, random = Random(7))
        questions.forEach { q -> assertEquals(q.choices.size, q.choices.distinct().size) }
    }

    @Test
    fun `정답 인덱스는 항상 정답 뜻을 가리킨다`() {
        val questions = QuizLogic.buildQuiz(scope, distractorPool, random = Random(99))
        questions.forEach { q -> assertEquals(q.word.meaning, q.choices[q.correctChoiceIndex]) }
    }

    @Test
    fun `오답은 정답과 뜻이 겹치지 않는다`() {
        val questions = QuizLogic.buildQuiz(scope, distractorPool, random = Random(5))
        questions.forEach { q ->
            val wrongChoices = q.choices.filterIndexed { index, _ -> index != q.correctChoiceIndex }
            assertTrue(wrongChoices.none { it == q.word.meaning })
        }
    }

    @Test
    fun `오답 후보가 부족해도 예외 없이 있는 만큼만 채운다`() {
        val tinyDistractorPool = listOf(word(9, "only", "유일한뜻"))
        val questions = QuizLogic.buildQuiz(scope.take(2), tinyDistractorPool, random = Random(3))
        assertEquals(2, questions.size)
        questions.forEach { q -> assertTrue(q.choices.size <= QuizLogic.CHOICE_COUNT) }
    }
}
