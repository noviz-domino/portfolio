package com.voca.englishwordapp.ui.quiz

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.Word

/** 퀴즈 결과: 점수, 정답률, 틀린 단어 목록. 틀린 단어는 호출하는 쪽(QuizScreen)이 이미 오답노트에 등록해둔다. */
@Composable
fun QuizResultScreen(
    correctCount: Int,
    total: Int,
    wrongWords: List<Word>,
    onRetryWrongOnly: () -> Unit,
    onExit: () -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    val accuracy = if (total == 0) 0 else (correctCount * 100 / total)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(stringResource(R.string.quiz_result_title), style = MaterialTheme.typography.headlineSmall)
        Text(
            text = stringResource(R.string.quiz_result_score_format, correctCount, total, accuracy),
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(top = 8.dp, bottom = 16.dp)
        )

        if (wrongWords.isEmpty()) {
            Text(stringResource(R.string.quiz_result_all_correct), style = MaterialTheme.typography.bodyLarge)
        } else {
            Text(
                stringResource(R.string.quiz_result_wrong_count_format, wrongWords.size),
                style = MaterialTheme.typography.titleMedium
            )
            LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth().padding(vertical = 8.dp)) {
                items(wrongWords, key = { "${it.dayNumber}|${it.word}" }) { word ->
                    Text(
                        text = stringResource(R.string.review_item_format, word.day, word.word, word.meaning),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(vertical = 4.dp)
                    )
                }
            }
        }

        Row(modifier = Modifier.fillMaxWidth().padding(top = 16.dp)) {
            OutlinedButton(onClick = onExit, modifier = Modifier.weight(1f).padding(end = 4.dp)) {
                Text(stringResource(R.string.quiz_exit))
            }
            if (wrongWords.isNotEmpty()) {
                Button(onClick = onRetryWrongOnly, modifier = Modifier.weight(1f).padding(start = 4.dp)) {
                    Text(stringResource(R.string.quiz_retry_wrong))
                }
            }
        }
    }
}
