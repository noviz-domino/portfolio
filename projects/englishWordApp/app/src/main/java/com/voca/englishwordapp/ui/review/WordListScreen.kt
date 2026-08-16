package com.voca.englishwordapp.ui.review

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.Word

/**
 * 즐겨찾기/오답노트 화면이 공유하는 목록 UI. 제목 + 개수, 목록, "학습하기" 버튼으로 구성된다.
 * [FavoritesScreen]과 [MistakesScreen]에서 각각 다른 데이터로 재사용한다.
 */
@Composable
internal fun WordListScreen(
    title: String,
    words: List<Word>,
    onStudy: () -> Unit,
    contentPadding: PaddingValues
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            Text(
                stringResource(R.string.review_count_format, words.size),
                style = MaterialTheme.typography.titleLarge
            )
        }

        if (words.isEmpty()) {
            Text(
                text = stringResource(R.string.review_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 16.dp)
            )
        } else {
            LazyColumn(modifier = Modifier.weight(1f).padding(vertical = 12.dp)) {
                items(words, key = { "${it.dayNumber}|${it.word}" }) { word ->
                    Text(
                        text = stringResource(R.string.review_item_format, word.day, word.word, word.meaning),
                        style = MaterialTheme.typography.bodyMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.padding(vertical = 6.dp)
                    )
                }
            }
            Button(onClick = onStudy, modifier = Modifier.fillMaxWidth().padding(top = 4.dp)) {
                Text(stringResource(R.string.review_study))
            }
        }
    }
}
