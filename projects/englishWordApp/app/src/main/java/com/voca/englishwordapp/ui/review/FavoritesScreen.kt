package com.voca.englishwordapp.ui.review

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.Word
import com.voca.englishwordapp.ui.theme.EnglishWordAppTheme

/** 즐겨찾기 단어 목록 전용 화면. "학습하기"로 즐겨찾기만 모아 복습 세션에 들어간다. */
@Composable
fun FavoritesScreen(
    words: List<Word>,
    onStudy: () -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    WordListScreen(
        title = stringResource(R.string.review_favorites),
        words = words,
        onStudy = onStudy,
        contentPadding = contentPadding
    )
}

private val PREVIEW_WORDS = listOf(
    Word(day = "day1", dayNumber = 1, word = "resume", meaning = "재개하다, 이력서"),
    Word(day = "day3", dayNumber = 3, word = "eligible", meaning = "자격이 있는, 적격의"),
    Word(day = "day7", dayNumber = 7, word = "negotiate", meaning = "협상하다, 절충하다")
)

@Preview(showBackground = true, name = "즐겨찾기 - 항목 있음")
@Composable
private fun FavoritesScreenPreview() {
    EnglishWordAppTheme {
        FavoritesScreen(words = PREVIEW_WORDS, onStudy = {})
    }
}

@Preview(showBackground = true, name = "즐겨찾기 - 비어있음")
@Composable
private fun FavoritesScreenEmptyPreview() {
    EnglishWordAppTheme {
        FavoritesScreen(words = emptyList(), onStudy = {})
    }
}
