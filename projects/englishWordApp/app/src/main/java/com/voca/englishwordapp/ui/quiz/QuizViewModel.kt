package com.voca.englishwordapp.ui.quiz

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.voca.englishwordapp.data.Word

/**
 * 퀴즈 진행 상태. 문제 목록은 [QuizLogic.buildQuiz]로 화면에서 한 번 만들어 [start]로 넘겨준다
 * (문제 생성에는 `WordRepository`가 필요해 ViewModel 생성자에 넣기보다 화면에서 조립하는 편이
 * 간단하다). 회전은 ViewModel 보존만으로 버틴다 — 퀴즈는 세션이 짧아 프로세스 재생성까지
 * `SavedStateHandle`로 복원할 가치는 크지 않다고 보고 이번에는 생략했다.
 */
class QuizViewModel : ViewModel() {

    // mutableStateOf로 감싸지 않으면 start()가 값을 채워도 Compose가 변경을 감지하지 못해
    // "퀴즈를 만들 단어가 부족합니다" 화면에 멈춰 있는다 (실기기에서 발견된 버그).
    var questions: List<QuizQuestion> by mutableStateOf(emptyList())
        private set

    var currentIndex: Int by mutableStateOf(0)
        private set

    var selectedChoiceIndex: Int? by mutableStateOf(null)
        private set

    var correctCount: Int by mutableStateOf(0)
        private set

    var isFinished: Boolean by mutableStateOf(false)
        private set

    val wrongWords = mutableStateListOf<Word>()

    private var hasStarted = false

    /** 이미 시작된 세션이면 무시한다 — 화면이 재구성될 때마다 새 퀴즈로 덮어쓰지 않기 위해서다. */
    fun start(newQuestions: List<QuizQuestion>) {
        if (hasStarted) return
        hasStarted = true
        questions = newQuestions
        currentIndex = 0
        selectedChoiceIndex = null
        correctCount = 0
        wrongWords.clear()
        isFinished = newQuestions.isEmpty()
    }

    fun selectAnswer(index: Int) {
        if (selectedChoiceIndex != null || isFinished) return
        selectedChoiceIndex = index
        val question = questions[currentIndex]
        if (index == question.correctChoiceIndex) {
            correctCount++
        } else {
            wrongWords.add(question.word)
        }
    }

    fun nextQuestion() {
        if (currentIndex < questions.lastIndex) {
            currentIndex++
            selectedChoiceIndex = null
        } else {
            isFinished = true
        }
    }
}
