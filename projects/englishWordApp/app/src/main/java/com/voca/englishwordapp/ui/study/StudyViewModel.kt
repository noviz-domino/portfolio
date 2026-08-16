package com.voca.englishwordapp.ui.study

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel

private const val KEY_INDEX = "study_current_index"
private const val KEY_REVEALED = "study_meaning_revealed"
private const val KEY_SHUFFLED = "study_is_shuffled"
private const val KEY_SHUFFLE_SEED = "study_shuffle_seed"
private const val KEY_AUTO_SPEAK = "study_auto_speak"

/**
 * day별 학습 화면 상태. Navigation-Compose가 `study/{dayNumber}` 목적지의 NavBackStackEntry에
 * 스코프해서 만들어주므로, 화면 회전은 물론 시스템이 백그라운드 프로세스를 죽였다가 되살리는
 * 경우에도 [SavedStateHandle]을 통해 현재 위치·뜻 공개 여부·셔플 상태가 복원된다.
 * (기존 Java 버전은 Activity 필드에만 상태가 있어 회전 시 항상 첫 단어로 되돌아갔다.)
 *
 * 프로퍼티는 전부 `mutableStateOf`로 감싼다 — Compose는 스냅샷 상태의 읽기만 recomposition의
 * 근거로 삼기 때문에, 일반 `var`로 두면 값이 바뀌어도 화면이 갱신되지 않는다.
 */
class StudyViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    var currentIndex: Int by mutableStateOf(savedStateHandle[KEY_INDEX] ?: 0)
        private set

    var isMeaningRevealed: Boolean by mutableStateOf(savedStateHandle[KEY_REVEALED] ?: false)
        private set

    var isShuffled: Boolean by mutableStateOf(savedStateHandle[KEY_SHUFFLED] ?: false)
        private set

    var shuffleSeed: Long by mutableStateOf(savedStateHandle[KEY_SHUFFLE_SEED] ?: 0L)
        private set

    var isAutoSpeakEnabled: Boolean by mutableStateOf(savedStateHandle[KEY_AUTO_SPEAK] ?: false)
        private set

    /**
     * index -> 안다(true)/모른다(false). 카드에 즉시 반영할 UI 상태일 뿐이고, 실제 오답노트
     * 저장은 [ui.study.StudyScreen]이 `StudyPrefs`에 직접 쓴다(단어의 day/word 키가 필요해서다).
     */
    val markedKnown = mutableStateMapOf<Int, Boolean>()

    fun revealMeaning() {
        isMeaningRevealed = true
        savedStateHandle[KEY_REVEALED] = true
    }

    fun goTo(index: Int, wordCount: Int) {
        if (wordCount <= 0 || index !in 0 until wordCount) return
        currentIndex = index
        isMeaningRevealed = false
        savedStateHandle[KEY_INDEX] = index
        savedStateHandle[KEY_REVEALED] = false
    }

    fun next(wordCount: Int) = goTo(currentIndex + 1, wordCount)

    fun previous(wordCount: Int) = goTo(currentIndex - 1, wordCount)

    fun mark(known: Boolean) {
        markedKnown[currentIndex] = known
    }

    fun toggleAutoSpeak() {
        isAutoSpeakEnabled = !isAutoSpeakEnabled
        savedStateHandle[KEY_AUTO_SPEAK] = isAutoSpeakEnabled
    }

    /** 셔플을 켜면 새 시드로 순서를 다시 섞고 처음 단어로 되돌아간다. 끄면 원래 순서로 복귀. */
    fun toggleShuffle() {
        isShuffled = !isShuffled
        if (isShuffled) {
            shuffleSeed = System.nanoTime()
            savedStateHandle[KEY_SHUFFLE_SEED] = shuffleSeed
        }
        savedStateHandle[KEY_SHUFFLED] = isShuffled
        currentIndex = 0
        savedStateHandle[KEY_INDEX] = 0
        isMeaningRevealed = false
        savedStateHandle[KEY_REVEALED] = false
    }
}
