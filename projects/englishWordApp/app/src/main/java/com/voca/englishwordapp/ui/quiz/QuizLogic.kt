package com.voca.englishwordapp.ui.quiz

import com.voca.englishwordapp.data.Word
import kotlin.random.Random

/** 문제 하나. [choices]는 이미 뒤섞여 있고, [correctChoiceIndex]가 정답 위치를 가리킨다. */
data class QuizQuestion(
    val word: Word,
    val choices: List<String>,
    val correctChoiceIndex: Int
)

/**
 * 4지선다 퀴즈 문제 생성. 순수 함수라 Android 의존성 없이 단위 테스트로 검증할 수 있다.
 *
 * 방향은 영어 단어 → 한글 뜻(고정)이다. 오답 선택지는 출제 범위([scope]) *밖*에서
 * 뽑는다([distractorPool]) — 같은 day 안에서만 오답을 뽑으면 학습 중이던 뜻과 헷갈리기 쉽고,
 * 뜻이 겹치는 단어가 우연히 섞여 정답이 여러 개처럼 보일 위험도 커진다.
 */
object QuizLogic {
    const val DEFAULT_QUESTION_COUNT = 10
    const val CHOICE_COUNT = 4

    fun buildQuiz(
        scope: List<Word>,
        distractorPool: List<Word>,
        questionCount: Int = DEFAULT_QUESTION_COUNT,
        random: Random = Random.Default
    ): List<QuizQuestion> {
        if (scope.isEmpty()) return emptyList()
        val questionWords = scope.shuffled(random).take(questionCount.coerceAtMost(scope.size))
        return questionWords.map { word -> buildQuestion(word, distractorPool, random) }
    }

    private fun buildQuestion(word: Word, distractorPool: List<Word>, random: Random): QuizQuestion {
        val distractorMeanings = distractorPool
            .asSequence()
            .map { it.meaning }
            .filter { it != word.meaning }
            .distinct()
            .shuffled(random)
            .take(CHOICE_COUNT - 1)
            .toList()

        val choices = (distractorMeanings + word.meaning).shuffled(random)
        val correctIndex = choices.indexOf(word.meaning)
        return QuizQuestion(word = word, choices = choices, correctChoiceIndex = correctIndex)
    }
}
