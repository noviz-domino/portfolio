package com.voca.englishwordapp.data

import android.content.Context

/**
 * `assets/words.csv`를 1회 읽어 메모리에 캐싱하고, day별 조회를 제공한다.
 * `words.csv`는 읽기전용 원본으로 취급하며 이 클래스는 로드와 조회만 담당한다.
 */
class WordRepository private constructor(private val allWords: List<Word>) {

    /** day 선택 화면에 쓰는 요약 정보. */
    data class DaySummary(val day: String, val dayNumber: Int, val wordCount: Int)

    /** dayNumber 오름차순으로 정렬된 day 목록 (CSV 등장 순서에 의존하지 않음). */
    fun getDays(): List<DaySummary> =
        allWords
            .groupBy { it.dayNumber to it.day }
            .map { (key, words) -> DaySummary(day = key.second, dayNumber = key.first, wordCount = words.size) }
            .sortedBy { it.dayNumber }

    /** 특정 day에 속한 단어를 CSV 등장 순서 그대로 반환한다. */
    fun getWords(dayNumber: Int): List<Word> = allWords.filter { it.dayNumber == dayNumber }

    /**
     * [StudyPrefs]에 저장된 `dayNumber|word` 키 집합(즐겨찾기, 오답노트 등)에 해당하는 단어를
     * day 오름차순 → CSV 등장 순서로 반환한다. day를 가로지르는 복습 목록에 쓴다.
     */
    fun getWordsByKeys(keys: Set<String>): List<Word> {
        if (keys.isEmpty()) return emptyList()
        return allWords
            .filter { wordKey(it.dayNumber, it.word) in keys }
            .sortedBy { it.dayNumber }
    }

    fun getAllWords(): List<Word> = allWords

    companion object {
        @Volatile
        private var instance: WordRepository? = null

        fun getInstance(context: Context): WordRepository =
            instance ?: synchronized(this) {
                instance ?: WordRepository(loadFromAssets(context)).also { instance = it }
            }

        private fun loadFromAssets(context: Context): List<Word> {
            val lines = context.assets.open("words.csv").bufferedReader(Charsets.UTF_8).use { it.readLines() }
            return CsvWordParser.parse(lines)
        }
    }
}
