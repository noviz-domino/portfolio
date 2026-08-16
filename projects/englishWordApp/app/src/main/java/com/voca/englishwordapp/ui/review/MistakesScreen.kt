package com.voca.englishwordapp.ui.review

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.Word
import com.voca.englishwordapp.ui.theme.EnglishWordAppTheme

/** 오답노트(모르는 단어) 목록 전용 화면. "학습하기"로 오답노트만 모아 복습 세션에 들어간다. */
@Composable
fun MistakesScreen(
    words: List<Word>,
    onStudy: () -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    WordListScreen(
        title = stringResource(R.string.review_unknown),
        words = words,
        onStudy = onStudy,
        contentPadding = contentPadding
    )
}

private val PREVIEW_WORDS = listOf(
    Word(day = "day2", dayNumber = 2, word = "applicant", meaning = "지원자, 신청자"),
    Word(day = "day5", dayNumber = 5, word = "requirement", meaning = "필요조건, 요건")
)

@Preview(showBackground = true, name = "오답노트 - 항목 있음")
@Composable
private fun MistakesScreenPreview() {
    EnglishWordAppTheme {
        MistakesScreen(words = PREVIEW_WORDS, onStudy = {})
    }
}

@Preview(showBackground = true, name = "오답노트 - 비어있음")
@Composable
private fun MistakesScreenEmptyPreview() {
    EnglishWordAppTheme {
        MistakesScreen(words = emptyList(), onStudy = {})
    }
}
