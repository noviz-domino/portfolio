package com.voca.englishwordapp.data

/**
 * 단어 한 건.
 *
 * [dayNumber]는 [day]("day12" 형태)에서 숫자만 뽑아낸 값으로, day 목록을 등장 순서가 아니라
 * 숫자 순서로 정렬하기 위한 키로 쓴다.
 */
data class Word(
    val day: String,
    val dayNumber: Int,
    val word: String,
    val meaning: String
)
