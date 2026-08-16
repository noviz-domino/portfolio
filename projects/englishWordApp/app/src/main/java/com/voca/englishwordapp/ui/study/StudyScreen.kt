package com.voca.englishwordapp.ui.study

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.VolumeOff
import androidx.compose.material.icons.automirrored.filled.VolumeUp
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.StudyPrefs
import com.voca.englishwordapp.data.Word
import com.voca.englishwordapp.tts.WordSpeakerState
import com.voca.englishwordapp.tts.rememberWordSpeaker
import kotlinx.coroutines.launch
import kotlin.random.Random

/**
 * 단어 학습 화면.
 * - 뜻은 기본 숨김 → 카드를 탭하면 공개
 * - [HorizontalPager]로 좌우 스와이프 이동 (기존 이전/다음 버튼도 함께 유지)
 * - 상단에 진행도(`12 / 40`), 셔플 토글, 자동 발음 토글(기본 꺼짐)
 * - 뜻 공개 후 안다/모른다 버튼 → [StudyPrefs]에 오답(모르는 단어)으로 영속화
 * - 카드의 별 아이콘으로 즐겨찾기 토글, 스피커 아이콘으로 발음 재생 (역시 [StudyPrefs]에 영속화되는 건 즐겨찾기뿐)
 * - [StudyViewModel]이 NavBackStackEntry에 스코프되어, 회전/프로세스 재생성에도 위치가 유지된다
 *
 * [trackingDayNumber]가 있으면(day1~30을 순서대로 도는 일반 학습) 진행도/완료 여부를
 * [StudyPrefs]에 저장해 홈의 "이어서 학습"과 day 목록의 완료 배지에 반영한다. 즐겨찾기·오답노트
 * 복습처럼 여러 day를 섞어서 보는 세션에서는 null을 넘겨 day 단위 진행도 추적을 건너뛴다 —
 * 단어 자체의 즐겨찾기/오답 표시는 [Word.dayNumber]를 쓰므로 이 값과 무관하게 항상 동작한다.
 */
@Composable
fun StudyScreen(
    words: List<Word>,
    onBackToDayList: () -> Unit,
    trackingDayNumber: Int? = null,
    contentPadding: PaddingValues = PaddingValues(),
    viewModel: StudyViewModel = viewModel()
) {
    if (words.isEmpty()) return

    val context = LocalContext.current
    val prefs = remember { StudyPrefs.getInstance(context) }
    val speaker = rememberWordSpeaker()
    val snackbarHostState = remember { SnackbarHostState() }
    val coroutineScope = rememberCoroutineScope()
    val ttsUnavailableMessage = stringResource(R.string.study_tts_unavailable)

    val displayWords = remember(words, viewModel.isShuffled, viewModel.shuffleSeed) {
        if (viewModel.isShuffled) words.shuffled(Random(viewModel.shuffleSeed)) else words
    }

    val pagerState = rememberPagerState(initialPage = viewModel.currentIndex) { displayWords.size }
    var showCompletionDialog by remember { mutableStateOf(false) }

    // ViewModel -> Pager: 버튼/마킹으로 인덱스가 바뀌면 페이지를 따라 움직인다.
    LaunchedEffect(viewModel.currentIndex) {
        if (pagerState.currentPage != viewModel.currentIndex) {
            pagerState.animateScrollToPage(viewModel.currentIndex)
        }
    }
    // Pager -> ViewModel: 스와이프로 페이지가 바뀌면 인덱스/공개 상태를 갱신한다.
    LaunchedEffect(pagerState.currentPage) {
        if (pagerState.currentPage != viewModel.currentIndex) {
            viewModel.goTo(pagerState.currentPage, displayWords.size)
        }
    }
    // 진행 위치를 저장 (day 단위 학습일 때만 - 이어서 학습/완료 배지가 이 값을 읽는다).
    LaunchedEffect(trackingDayNumber, viewModel.currentIndex) {
        if (trackingDayNumber != null) {
            prefs.setProgress(trackingDayNumber, viewModel.currentIndex)
        }
    }
    // 자동 발음: 켜져 있으면 현재 단어가 바뀔 때마다 읽어준다.
    LaunchedEffect(viewModel.currentIndex, viewModel.isAutoSpeakEnabled, speaker.isReady) {
        if (viewModel.isAutoSpeakEnabled && speaker.isReady) {
            speaker.speak(displayWords[viewModel.currentIndex].word)
        }
    }
    // TTS를 이 기기에서 쓸 수 없는 경우, 딱 한 번만 안내한다.
    LaunchedEffect(speaker.initializationFailed) {
        if (speaker.initializationFailed) {
            snackbarHostState.showSnackbar(ttsUnavailableMessage)
        }
    }

    fun advanceOrComplete() {
        if (viewModel.currentIndex >= displayWords.lastIndex) {
            trackingDayNumber?.let { prefs.markDayCompleted(it) }
            showCompletionDialog = true
        } else {
            viewModel.next(displayWords.size)
        }
    }

    fun markAndAdvance(known: Boolean) {
        val current = displayWords[viewModel.currentIndex]
        viewModel.mark(known)
        prefs.setUnknown(current.dayNumber, current.word, unknown = !known)
        advanceOrComplete()
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.background
    ) { scaffoldPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(contentPadding)
                .padding(scaffoldPadding)
                .padding(horizontal = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            StudyProgressBar(
                currentIndex = viewModel.currentIndex,
                total = displayWords.size,
                isShuffled = viewModel.isShuffled,
                onToggleShuffle = { viewModel.toggleShuffle() },
                isAutoSpeakEnabled = viewModel.isAutoSpeakEnabled,
                onToggleAutoSpeak = { viewModel.toggleAutoSpeak() }
            )

            HorizontalPager(
                state = pagerState,
                modifier = Modifier.weight(1f)
            ) { page ->
                val pageWord = displayWords[page]
                val revealed = page == viewModel.currentIndex && viewModel.isMeaningRevealed
                var isFavorite by remember(pageWord) {
                    mutableStateOf(prefs.isFavorite(pageWord.dayNumber, pageWord.word))
                }
                WordCard(
                    word = pageWord,
                    revealed = revealed,
                    onReveal = { viewModel.revealMeaning() },
                    isFavorite = isFavorite,
                    onToggleFavorite = {
                        isFavorite = prefs.toggleFavorite(pageWord.dayNumber, pageWord.word)
                    },
                    speaker = speaker,
                    onSpeakerUnavailable = {
                        coroutineScope.launch {
                            snackbarHostState.showSnackbar(ttsUnavailableMessage)
                        }
                    }
                )
            }

            if (viewModel.isMeaningRevealed) {
                Row(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                    OutlinedButton(
                        onClick = { markAndAdvance(known = false) },
                        modifier = Modifier.weight(1f).padding(horizontal = 4.dp)
                    ) { Text(stringResource(R.string.study_dont_know)) }
                    Button(
                        onClick = { markAndAdvance(known = true) },
                        modifier = Modifier.weight(1f).padding(horizontal = 4.dp)
                    ) { Text(stringResource(R.string.study_know)) }
                }
            }

            Row(modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)) {
                Button(
                    onClick = { viewModel.previous(displayWords.size) },
                    enabled = viewModel.currentIndex > 0,
                    modifier = Modifier.weight(1f).padding(10.dp)
                ) { Text(stringResource(R.string.study_prev)) }
                Button(
                    onClick = { advanceOrComplete() },
                    modifier = Modifier.weight(1f).padding(10.dp)
                ) { Text(stringResource(R.string.study_next)) }
            }
        }
    }

    if (showCompletionDialog) {
        AlertDialog(
            onDismissRequest = { showCompletionDialog = false },
            title = { Text(stringResource(R.string.study_complete_title)) },
            text = { Text(stringResource(R.string.study_complete_text)) },
            confirmButton = {
                TextButton(onClick = {
                    showCompletionDialog = false
                    viewModel.goTo(0, displayWords.size)
                }) { Text(stringResource(R.string.study_restart)) }
            },
            dismissButton = {
                TextButton(onClick = {
                    showCompletionDialog = false
                    onBackToDayList()
                }) { Text(stringResource(R.string.study_back_to_days)) }
            }
        )
    }
}

@Composable
private fun StudyProgressBar(
    currentIndex: Int,
    total: Int,
    isShuffled: Boolean,
    onToggleShuffle: () -> Unit,
    isAutoSpeakEnabled: Boolean,
    onToggleAutoSpeak: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(top = 12.dp, bottom = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = stringResource(R.string.study_progress_format, currentIndex + 1, total),
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.weight(1f)
        )
        Text(stringResource(R.string.study_auto_speak), style = MaterialTheme.typography.labelMedium)
        Switch(checked = isAutoSpeakEnabled, onCheckedChange = { onToggleAutoSpeak() })
        Text(
            stringResource(R.string.study_shuffle),
            style = MaterialTheme.typography.labelMedium,
            modifier = Modifier.padding(start = 8.dp)
        )
        Switch(checked = isShuffled, onCheckedChange = { onToggleShuffle() })
    }
    LinearProgressIndicator(
        progress = { if (total == 0) 0f else (currentIndex + 1) / total.toFloat() },
        modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
    )
}

@Composable
private fun WordCard(
    word: Word,
    revealed: Boolean,
    onReveal: () -> Unit,
    isFavorite: Boolean,
    onToggleFavorite: () -> Unit,
    speaker: WordSpeakerState,
    onSpeakerUnavailable: () -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        // Box는 나중에 선언된 자식이 위에 그려진다. 뜻 공개용 탭 영역(전체 화면 크기)을
        // 아이콘 버튼보다 먼저 선언해야 아이콘이 위에 그려져서 클릭을 받을 수 있다 —
        // 순서가 반대였을 때는 투명한 탭 영역이 아이콘을 덮어 스피커/즐겨찾기가 먹통이었다.
        Column(
            modifier = Modifier
                .fillMaxSize()
                .clickable(enabled = !revealed, onClick = onReveal),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(text = word.word, style = MaterialTheme.typography.displaySmall)

            AnimatedContent(
                targetState = revealed,
                modifier = Modifier.padding(top = 20.dp),
                transitionSpec = { fadeIn() togetherWith fadeOut() }
            ) { isRevealed ->
                if (isRevealed) {
                    Text(text = word.meaning, style = MaterialTheme.typography.headlineSmall)
                } else {
                    Text(
                        text = stringResource(R.string.study_reveal_hint),
                        style = MaterialTheme.typography.headlineSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        IconButton(
            onClick = {
                if (speaker.isReady) speaker.speak(word.word) else onSpeakerUnavailable()
            },
            modifier = Modifier.align(Alignment.TopStart)
        ) {
            Icon(
                imageVector = if (speaker.isReady) Icons.AutoMirrored.Filled.VolumeUp else Icons.AutoMirrored.Filled.VolumeOff,
                contentDescription = stringResource(R.string.study_speak_desc),
                tint = if (speaker.isReady) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outlineVariant
                }
            )
        }

        IconButton(
            onClick = onToggleFavorite,
            modifier = Modifier.align(Alignment.TopEnd)
        ) {
            Icon(
                imageVector = Icons.Filled.Star,
                contentDescription = stringResource(R.string.study_favorite_desc),
                tint = if (isFavorite) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outlineVariant
                }
            )
        }
    }
}
