package com.voca.englishwordapp.ui.quiz

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.StudyPrefs
import com.voca.englishwordapp.data.Word

/**
 * 4지선다 퀴즈 화면. [scopeWords]가 출제 범위, [distractorPool]이 오답 후보(보통 전체 단어)다.
 * 방향은 영어 단어 → 한글 뜻으로 고정. 선택하면 즉시 정오 피드백을 보이고, "다음"으로 넘어간다.
 * 마지막 문제 다음에는 [QuizResultScreen]으로 전환되고, 그 시점에 틀린 단어를 오답노트
 * ([StudyPrefs])에 등록한다.
 */
@Composable
fun QuizScreen(
    scopeWords: List<Word>,
    distractorPool: List<Word>,
    onExit: () -> Unit,
    onRetryWrongOnly: () -> Unit,
    contentPadding: PaddingValues = PaddingValues(),
    viewModel: QuizViewModel = viewModel()
) {
    val context = LocalContext.current
    val prefs = remember { StudyPrefs.getInstance(context) }

    LaunchedEffect(scopeWords) {
        if (scopeWords.isNotEmpty()) {
            viewModel.start(QuizLogic.buildQuiz(scope = scopeWords, distractorPool = distractorPool))
        }
    }

    if (viewModel.questions.isEmpty() && !viewModel.isFinished) {
        Box(modifier = Modifier.fillMaxSize().padding(contentPadding), contentAlignment = Alignment.Center) {
            Text(stringResource(R.string.quiz_insufficient))
        }
        return
    }

    if (viewModel.isFinished) {
        LaunchedEffect(viewModel.isFinished) {
            viewModel.wrongWords.forEach { word -> prefs.setUnknown(word.dayNumber, word.word, unknown = true) }
        }
        QuizResultScreen(
            correctCount = viewModel.correctCount,
            total = viewModel.questions.size,
            wrongWords = viewModel.wrongWords,
            onRetryWrongOnly = onRetryWrongOnly,
            onExit = onExit,
            contentPadding = contentPadding
        )
        return
    }

    val question = viewModel.questions[viewModel.currentIndex]
    val selected = viewModel.selectedChoiceIndex

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .padding(16.dp)
    ) {
        Text(
            text = stringResource(R.string.quiz_progress_format, viewModel.currentIndex + 1, viewModel.questions.size),
            style = MaterialTheme.typography.labelLarge
        )
        LinearProgressIndicator(
            progress = { (viewModel.currentIndex + 1) / viewModel.questions.size.toFloat() },
            modifier = Modifier.fillMaxWidth().padding(top = 4.dp, bottom = 24.dp)
        )

        Text(
            text = question.word.word,
            style = MaterialTheme.typography.displaySmall,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        question.choices.forEachIndexed { index, choice ->
            val isCorrectChoice = index == question.correctChoiceIndex
            val colors = when {
                selected == null -> ButtonDefaults.outlinedButtonColors()
                isCorrectChoice -> ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                index == selected -> ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                else -> ButtonDefaults.outlinedButtonColors()
            }
            // 정답 후에도 색이 그대로 보이도록 enabled는 항상 true로 두고, 재선택은
            // viewModel.selectAnswer 쪽에서 이미 막는다 (disabled 상태의 회색 처리를 피하기 위함).
            Button(
                onClick = { viewModel.selectAnswer(index) },
                colors = colors,
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
            ) {
                Text(choice)
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        if (selected != null) {
            Button(
                onClick = { viewModel.nextQuestion() },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    if (viewModel.currentIndex == viewModel.questions.lastIndex) {
                        stringResource(R.string.quiz_show_result)
                    } else {
                        stringResource(R.string.quiz_next)
                    }
                )
            }
        }
    }
}
