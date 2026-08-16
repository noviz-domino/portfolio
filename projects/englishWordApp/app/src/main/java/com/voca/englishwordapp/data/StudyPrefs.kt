package com.voca.englishwordapp.data

import android.content.Context

private const val PREFS_NAME = "study_prefs"
private const val KEY_LAST_DAY = "last_day"
private const val KEY_COMPLETED_DAYS = "completed_days"
private const val KEY_FAVORITES = "favorites"
private const val KEY_UNKNOWN_WORDS = "unknown_words"
private const val NO_LAST_DAY = -1

private fun progressKey(dayNumber: Int) = "progress_day_$dayNumber"

/** 단어 식별 키. `dayNumber|word` 형태로 만들어, CSV에서 단어 순서가 바뀌어도 안전하게 식별한다. */
fun wordKey(dayNumber: Int, word: String) = "$dayNumber|$word"

/**
 * 학습 진행도·즐겨찾기·오답(모르는 단어)을 저장하는 SharedPreferences 래퍼.
 * `words.csv`는 읽기전용으로 유지하고, 여기서는 "무엇을 어디까지 봤는지"만 기록한다.
 */
class StudyPrefs private constructor(context: Context) {

    private val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** 가장 최근에 학습한 day. 아직 아무것도 학습하지 않았으면 null. */
    var lastDay: Int?
        get() = prefs.getInt(KEY_LAST_DAY, NO_LAST_DAY).takeIf { it != NO_LAST_DAY }
        set(value) {
            prefs.edit().apply {
                if (value != null) putInt(KEY_LAST_DAY, value) else remove(KEY_LAST_DAY)
            }.apply()
        }

    fun getProgress(dayNumber: Int): Int = prefs.getInt(progressKey(dayNumber), 0)

    /** 학습 위치를 저장하고, [lastDay]도 함께 갱신한다 (홈의 "이어서 학습" 카드가 참조). */
    fun setProgress(dayNumber: Int, index: Int) {
        prefs.edit().putInt(progressKey(dayNumber), index).apply()
        lastDay = dayNumber
    }

    fun getCompletedDays(): Set<Int> =
        (prefs.getStringSet(KEY_COMPLETED_DAYS, emptySet()) ?: emptySet())
            .mapNotNull { it.toIntOrNull() }
            .toSet()

    fun markDayCompleted(dayNumber: Int) {
        val updated = getCompletedDays() + dayNumber
        prefs.edit().putStringSet(KEY_COMPLETED_DAYS, updated.map { it.toString() }.toSet()).apply()
    }

    fun getFavoriteKeys(): Set<String> = prefs.getStringSet(KEY_FAVORITES, emptySet()) ?: emptySet()

    fun isFavorite(dayNumber: Int, word: String): Boolean = wordKey(dayNumber, word) in getFavoriteKeys()

    /** 즐겨찾기를 토글하고, 토글 이후의 상태(true=즐겨찾기 됨)를 반환한다. */
    fun toggleFavorite(dayNumber: Int, word: String): Boolean {
        val key = wordKey(dayNumber, word)
        val current = getFavoriteKeys().toMutableSet()
        val isNowFavorite = if (!current.remove(key)) {
            current.add(key)
            true
        } else {
            false
        }
        prefs.edit().putStringSet(KEY_FAVORITES, current).apply()
        return isNowFavorite
    }

    fun getUnknownKeys(): Set<String> = prefs.getStringSet(KEY_UNKNOWN_WORDS, emptySet()) ?: emptySet()

    fun setUnknown(dayNumber: Int, word: String, unknown: Boolean) {
        val key = wordKey(dayNumber, word)
        val current = getUnknownKeys().toMutableSet()
        if (unknown) current.add(key) else current.remove(key)
        prefs.edit().putStringSet(KEY_UNKNOWN_WORDS, current).apply()
    }

    /** 진행도/즐겨찾기/오답 전부 삭제. 홈 화면의 "초기화"에서만 호출하며, 되돌릴 수 없다. */
    fun clearAll() {
        prefs.edit().clear().apply()
    }

    companion object {
        @Volatile
        private var instance: StudyPrefs? = null

        fun getInstance(context: Context): StudyPrefs =
            instance ?: synchronized(this) {
                instance ?: StudyPrefs(context).also { instance = it }
            }
    }
}
