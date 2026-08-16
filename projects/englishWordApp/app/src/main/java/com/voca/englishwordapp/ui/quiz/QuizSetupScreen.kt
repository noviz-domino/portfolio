package com.voca.englishwordapp.ui.quiz

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.WordRepository

/** 퀴즈 출제 범위 선택: 즐겨찾기 / 오답노트 / day별. */
@Composable
fun QuizSetupScreen(
    days: List<WordRepository.DaySummary>,
    favoriteCount: Int,
    unknownCount: Int,
    onQuizFavorites: () -> Unit,
    onQuizUnknown: () -> Unit,
    onQuizDay: (Int) -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .padding(16.dp)
    ) {
        Text(stringResource(R.string.quiz_setup_title), style = MaterialTheme.typography.titleLarge)

        Row(modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp)) {
            OutlinedButton(
                onClick = onQuizFavorites,
                enabled = favoriteCount > 0,
                modifier = Modifier.weight(1f).padding(end = 4.dp)
            ) { Text(stringResource(R.string.quiz_favorites_format, favoriteCount)) }
            OutlinedButton(
                onClick = onQuizUnknown,
                enabled = unknownCount > 0,
                modifier = Modifier.weight(1f).padding(start = 4.dp)
            ) { Text(stringResource(R.string.quiz_unknown_format, unknownCount)) }
        }

        HorizontalDivider()

        Text(
            text = stringResource(R.string.quiz_by_day_title),
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(top = 12.dp, bottom = 8.dp)
        )
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(days, key = { it.dayNumber }) { day ->
                Button(
                    onClick = { onQuizDay(day.dayNumber) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(stringResource(R.string.quiz_day_item_format, day.day, day.wordCount))
                }
            }
        }
    }
}
