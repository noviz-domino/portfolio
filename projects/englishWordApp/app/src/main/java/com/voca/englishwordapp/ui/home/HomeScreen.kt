package com.voca.englishwordapp.ui.home

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Assignment
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Quiz
import androidx.compose.material.icons.filled.RestartAlt
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.voca.englishwordapp.BuildConfig
import com.voca.englishwordapp.R
import com.voca.englishwordapp.ui.theme.EnglishWordAppTheme

/** 홈의 "이어보기" 타일에 필요한 정보. */
data class ContinueInfo(val dayNumber: Int, val progressIndex: Int, val totalWords: Int)

/** 시작 화면. 브랜드 헤더 아래에서 2열×3행 메뉴로 전체 기능에 바로 접근한다. */
@Composable
fun HomeScreen(
    onGoStudyList: () -> Unit,
    onOpenFavorites: () -> Unit,
    onOpenMistakes: () -> Unit,
    onOpenQuiz: () -> Unit,
    onResetProgress: () -> Unit,
    continueInfo: ContinueInfo?,
    onContinue: (Int) -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    var showResetDialog by remember { mutableStateOf(false) }

    val continueCaption = if (continueInfo != null) {
        stringResource(
            R.string.home_tile_continue_caption_format,
            continueInfo.dayNumber,
            continueInfo.progressIndex + 1,
            continueInfo.totalWords
        )
    } else {
        stringResource(R.string.home_tile_continue_empty)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        HomeBrandHeader()

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            HomeMenuTile(
                icon = Icons.AutoMirrored.Filled.MenuBook,
                label = stringResource(R.string.home_study_list),
                containerColor = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                onClick = onGoStudyList,
                modifier = Modifier.weight(1f)
            )
            HomeMenuTile(
                icon = Icons.Filled.PlayCircle,
                label = stringResource(R.string.home_tile_continue),
                caption = continueCaption,
                containerColor = MaterialTheme.colorScheme.secondaryContainer,
                contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
                enabled = continueInfo != null,
                onClick = { continueInfo?.let { onContinue(it.dayNumber) } },
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            HomeMenuTile(
                icon = Icons.Filled.Quiz,
                label = stringResource(R.string.home_quiz),
                containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                contentColor = MaterialTheme.colorScheme.onTertiaryContainer,
                onClick = onOpenQuiz,
                modifier = Modifier.weight(1f)
            )
            HomeMenuTile(
                icon = Icons.AutoMirrored.Filled.Assignment,
                label = stringResource(R.string.review_unknown),
                containerColor = MaterialTheme.colorScheme.errorContainer,
                contentColor = MaterialTheme.colorScheme.onErrorContainer,
                onClick = onOpenMistakes,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            HomeMenuTile(
                icon = Icons.Filled.Star,
                label = stringResource(R.string.review_favorites),
                containerColor = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                onClick = onOpenFavorites,
                modifier = Modifier.weight(1f)
            )
            HomeMenuTile(
                icon = Icons.Filled.RestartAlt,
                label = stringResource(R.string.home_reset),
                containerColor = MaterialTheme.colorScheme.surfaceVariant,
                contentColor = MaterialTheme.colorScheme.onSurfaceVariant,
                onClick = { showResetDialog = true },
                modifier = Modifier.weight(1f)
            )
        }

        HomeFooter()
    }

    if (showResetDialog) {
        AlertDialog(
            onDismissRequest = { showResetDialog = false },
            title = { Text(stringResource(R.string.home_reset_confirm_title)) },
            text = { Text(stringResource(R.string.home_reset_confirm_text)) },
            confirmButton = {
                TextButton(onClick = {
                    showResetDialog = false
                    onResetProgress()
                }) { Text(stringResource(R.string.action_confirm_reset)) }
            },
            dismissButton = {
                TextButton(onClick = { showResetDialog = false }) { Text(stringResource(R.string.action_cancel)) }
            }
        )
    }
}

/**
 * 홈 맨 아래 앱 정보. 바로 아래가 하단 광고이므로 **누를 수 있는 요소를 두지 않는다** —
 * 오조작 클릭은 AdMob에서 무효 트래픽으로 처리될 수 있다.
 * 나중에 "오늘의 단어"나 학습 현황 요약으로 교체하기 쉽도록 이 컴포저블만 갈아끼우면 된다.
 */
@Composable
private fun HomeFooter() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 28.dp, bottom = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Text(
            text = stringResource(R.string.home_footer_version_format, BuildConfig.VERSION_NAME),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.45f)
        )
        Text(
            text = stringResource(R.string.home_footer_credit),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.45f)
        )
        // 문의용 이메일. mailto 링크로 만들지 않는다 — 바로 아래가 광고라 탭 영역을 두면 안 된다.
        Text(
            text = stringResource(R.string.home_footer_contact),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.45f)
        )
    }
}

@Composable
private fun HomeBrandHeader() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(132.dp)
            .clip(RoundedCornerShape(28.dp))
            .background(
                Brush.horizontalGradient(
                    colors = listOf(
                        MaterialTheme.colorScheme.primaryContainer,
                        MaterialTheme.colorScheme.secondaryContainer
                    )
                )
            )
    ) {
        Image(
            painter = painterResource(R.drawable.home_header),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Fit
        )

        Column(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .width(164.dp)
                .padding(start = 20.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text = stringResource(R.string.home_brand_title),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Text(
                text = stringResource(R.string.home_brand_subtitle),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.76f)
            )
        }
    }
}

@Composable
private fun HomeMenuTile(
    icon: ImageVector,
    label: String,
    containerColor: Color,
    contentColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    caption: String? = null,
    enabled: Boolean = true
) {
    val resolvedContainerColor = if (enabled) containerColor else MaterialTheme.colorScheme.surfaceVariant
    val resolvedContentColor = if (enabled) contentColor else MaterialTheme.colorScheme.onSurfaceVariant

    Surface(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(124.dp),
        shape = MaterialTheme.shapes.extraLarge,
        color = resolvedContainerColor,
        contentColor = resolvedContentColor
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(imageVector = icon, contentDescription = null, modifier = Modifier.size(36.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(top = 10.dp)
            )
            if (caption != null) {
                Text(
                    text = caption,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 2.dp)
                )
            }
        }
    }
}

// Android Studio에서 이 파일을 열면 우측 Split/Design 탭에서 앱을 실행하지 않고도
// 아래 3개 상태(이어보기 있음/없음/다크모드)를 바로 미리볼 수 있다.

@Preview(showBackground = true, name = "이어서 학습 있음")
@Composable
private fun HomeScreenWithContinuePreview() {
    EnglishWordAppTheme {
        HomeScreen(
            onGoStudyList = {},
            onOpenFavorites = {},
            onOpenMistakes = {},
            onOpenQuiz = {},
            onResetProgress = {},
            continueInfo = ContinueInfo(dayNumber = 1, progressIndex = 1, totalWords = 39),
            onContinue = {}
        )
    }
}

@Preview(showBackground = true, name = "이어서 학습 없음(첫 실행)")
@Composable
private fun HomeScreenEmptyPreview() {
    EnglishWordAppTheme {
        HomeScreen(
            onGoStudyList = {},
            onOpenFavorites = {},
            onOpenMistakes = {},
            onOpenQuiz = {},
            onResetProgress = {},
            continueInfo = null,
            onContinue = {}
        )
    }
}

@Preview(
    showBackground = true,
    name = "다크 모드",
    uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES
)
@Composable
private fun HomeScreenDarkPreview() {
    EnglishWordAppTheme {
        HomeScreen(
            onGoStudyList = {},
            onOpenFavorites = {},
            onOpenMistakes = {},
            onOpenQuiz = {},
            onResetProgress = {},
            continueInfo = ContinueInfo(dayNumber = 3, progressIndex = 10, totalWords = 40),
            onContinue = {}
        )
    }
}
