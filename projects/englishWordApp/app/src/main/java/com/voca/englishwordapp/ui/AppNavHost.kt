package com.voca.englishwordapp.ui

import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.foundation.layout.windowInsetsTopHeight
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.voca.englishwordapp.data.StudyPrefs
import com.voca.englishwordapp.data.WordRepository
import com.voca.englishwordapp.ui.ads.AdBanner
import com.voca.englishwordapp.ui.ads.BOTTOM_AD_UNIT_ID
import com.voca.englishwordapp.ui.ads.TOP_AD_UNIT_ID
import com.voca.englishwordapp.ui.day.DayListScreen
import com.voca.englishwordapp.ui.home.ContinueInfo
import com.voca.englishwordapp.ui.home.HomeScreen
import com.voca.englishwordapp.ui.quiz.QuizScreen
import com.voca.englishwordapp.ui.quiz.QuizSetupScreen
import com.voca.englishwordapp.ui.review.FavoritesScreen
import com.voca.englishwordapp.ui.review.MistakesScreen
import com.voca.englishwordapp.ui.study.StudyScreen

private const val ROUTE_HOME = "home"
private const val ROUTE_DAYS = "days"
private const val ROUTE_STUDY = "study/{dayNumber}"
private const val ROUTE_FAVORITES = "favorites"
private const val ROUTE_MISTAKES = "mistakes"
private const val ROUTE_REVIEW_STUDY = "study/review/{type}"
private const val ROUTE_QUIZ_SETUP = "quiz"
private const val ROUTE_QUIZ_DAY = "quiz/day/{dayNumber}"
private const val ROUTE_QUIZ_REVIEW = "quiz/review/{type}"
private const val ARG_DAY_NUMBER = "dayNumber"
private const val ARG_REVIEW_TYPE = "type"
private const val REVIEW_TYPE_FAVORITES = "favorites"
private const val REVIEW_TYPE_UNKNOWN = "unknown"

/**
 * 화면 전환 그래프. 기존 `visibility` 토글 방식(홈/날짜선택/학습 3개 컨테이너) 대신
 * navigation-compose 백스택을 쓴다 — 뒤로가기(학습→날짜선택→홈→앱종료)는 NavController가
 * 자동으로 처리하므로 API 33+에서 deprecated된 `onBackPressed()` 오버라이드가 필요 없다.
 *
 * Phase 4: 홈의 "이어서 학습"/day 목록의 완료 배지/즐겨찾기·오답노트 복습은 모두 [StudyPrefs]를
 * 읽어서 구성한다. 이 값들은 일부러 `remember` 없이(또는 [resetTick]에만 의존해) 계산한다 —
 * Navigation-Compose는 목적지를 벗어났다가 되돌아오면 그 목적지의 컴포저블을 새로 구성하므로,
 * study 화면에서 돌아올 때마다 최신 값을 다시 읽게 된다.
 */
@Composable
fun AppNavHost() {
    val context = LocalContext.current
    val repository = remember { WordRepository.getInstance(context) }
    val prefs = remember { StudyPrefs.getInstance(context) }
    val navController = rememberNavController()

    // 홈 화면에 머무른 채로 "초기화"를 누르는 경우(네비게이션이 안 일어남)를 위한 갱신 신호.
    var resetTick by remember { mutableIntStateOf(0) }

    Scaffold(
        // targetSdk 36부터 edge-to-edge가 강제되어 상태바/내비게이션바가 항상 투명하게 그려진다.
        // 광고(외부 콘텐츠, 색이 매번 다름)와 상태바/내비게이션바 아이콘이 뒤섞여 보이지 않도록,
        // 상태바·내비게이션바 영역을 앱 테마 색으로 단색 처리해 광고와 분리한다
        // (실기기 확인으로 발견됨 - 라이트 모드에서 상태바 아이콘이 안 보이던 문제와 함께 수정).
        topBar = {
            Column(modifier = Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surface)) {
                Spacer(modifier = Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
                AdBanner(adUnitId = TOP_AD_UNIT_ID)
            }
        },
        bottomBar = {
            Column(modifier = Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surface)) {
                AdBanner(adUnitId = BOTTOM_AD_UNIT_ID)
                Spacer(modifier = Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
            }
        }
    ) { innerPadding ->
        // 네비게이션 기본 전환(슬라이드+페이드)이 광고 배너 재렌더링과 겹치면서 잔상처럼
        // 느껴지는 문제가 실기기에서 보고됐다. 슬라이드 없이 짧은 페이드만 쓰도록 단순화했다.
        NavHost(
            navController = navController,
            startDestination = ROUTE_HOME,
            enterTransition = { fadeIn(animationSpec = tween(120)) },
            exitTransition = { fadeOut(animationSpec = tween(120)) },
            popEnterTransition = { fadeIn(animationSpec = tween(120)) },
            popExitTransition = { fadeOut(animationSpec = tween(120)) }
        ) {
            composable(ROUTE_HOME) {
                @Suppress("UNUSED_EXPRESSION")
                resetTick // 이 스코프가 resetTick 변경을 구독하도록 읽어둔다.
                val continueInfo = remember(resetTick) { buildContinueInfo(prefs, repository) }
                HomeScreen(
                    onGoStudyList = { navController.navigate(ROUTE_DAYS) },
                    onOpenFavorites = { navController.navigate(ROUTE_FAVORITES) },
                    onOpenMistakes = { navController.navigate(ROUTE_MISTAKES) },
                    onOpenQuiz = { navController.navigate(ROUTE_QUIZ_SETUP) },
                    onResetProgress = {
                        prefs.clearAll()
                        resetTick++
                    },
                    continueInfo = continueInfo,
                    onContinue = { dayNumber -> navController.navigate("study/$dayNumber") },
                    contentPadding = innerPadding
                )
            }
            composable(ROUTE_DAYS) {
                val days = remember { repository.getDays() }
                val completedDays = prefs.getCompletedDays()
                val progressByDay = days.associate { it.dayNumber to prefs.getProgress(it.dayNumber) }
                DayListScreen(
                    days = days,
                    completedDays = completedDays,
                    progressByDay = progressByDay,
                    onDaySelected = { dayNumber -> navController.navigate("study/$dayNumber") },
                    contentPadding = innerPadding
                )
            }
            composable(
                route = ROUTE_STUDY,
                arguments = listOf(navArgument(ARG_DAY_NUMBER) { type = NavType.IntType })
            ) { backStackEntry ->
                val dayNumber = backStackEntry.arguments?.getInt(ARG_DAY_NUMBER) ?: 0
                StudyScreen(
                    words = remember(dayNumber) { repository.getWords(dayNumber) },
                    onBackToDayList = { navController.popBackStack() },
                    trackingDayNumber = dayNumber,
                    contentPadding = innerPadding
                )
            }
            composable(ROUTE_FAVORITES) {
                FavoritesScreen(
                    words = repository.getWordsByKeys(prefs.getFavoriteKeys()),
                    onStudy = { navController.navigate("study/review/$REVIEW_TYPE_FAVORITES") },
                    contentPadding = innerPadding
                )
            }
            composable(ROUTE_MISTAKES) {
                MistakesScreen(
                    words = repository.getWordsByKeys(prefs.getUnknownKeys()),
                    onStudy = { navController.navigate("study/review/$REVIEW_TYPE_UNKNOWN") },
                    contentPadding = innerPadding
                )
            }
            composable(
                route = ROUTE_REVIEW_STUDY,
                arguments = listOf(navArgument(ARG_REVIEW_TYPE) { type = NavType.StringType })
            ) { backStackEntry ->
                val reviewType = backStackEntry.arguments?.getString(ARG_REVIEW_TYPE)
                val words = when (reviewType) {
                    REVIEW_TYPE_FAVORITES -> repository.getWordsByKeys(prefs.getFavoriteKeys())
                    else -> repository.getWordsByKeys(prefs.getUnknownKeys())
                }
                StudyScreen(
                    words = words,
                    onBackToDayList = { navController.popBackStack() },
                    trackingDayNumber = null,
                    contentPadding = innerPadding
                )
            }
            composable(ROUTE_QUIZ_SETUP) {
                val days = remember { repository.getDays() }
                QuizSetupScreen(
                    days = days,
                    favoriteCount = prefs.getFavoriteKeys().size,
                    unknownCount = prefs.getUnknownKeys().size,
                    onQuizFavorites = { navController.navigate("quiz/review/$REVIEW_TYPE_FAVORITES") },
                    onQuizUnknown = { navController.navigate("quiz/review/$REVIEW_TYPE_UNKNOWN") },
                    onQuizDay = { dayNumber -> navController.navigate("quiz/day/$dayNumber") },
                    contentPadding = innerPadding
                )
            }
            composable(
                route = ROUTE_QUIZ_DAY,
                arguments = listOf(navArgument(ARG_DAY_NUMBER) { type = NavType.IntType })
            ) { backStackEntry ->
                val dayNumber = backStackEntry.arguments?.getInt(ARG_DAY_NUMBER) ?: 0
                QuizScreen(
                    scopeWords = remember(dayNumber) { repository.getWords(dayNumber) },
                    distractorPool = remember { repository.getAllWords() },
                    onExit = { navController.popBackStack() },
                    onRetryWrongOnly = { navController.navigate("study/review/$REVIEW_TYPE_UNKNOWN") },
                    contentPadding = innerPadding
                )
            }
            composable(
                route = ROUTE_QUIZ_REVIEW,
                arguments = listOf(navArgument(ARG_REVIEW_TYPE) { type = NavType.StringType })
            ) { backStackEntry ->
                val reviewType = backStackEntry.arguments?.getString(ARG_REVIEW_TYPE)
                val scopeWords = when (reviewType) {
                    REVIEW_TYPE_FAVORITES -> repository.getWordsByKeys(prefs.getFavoriteKeys())
                    else -> repository.getWordsByKeys(prefs.getUnknownKeys())
                }
                QuizScreen(
                    scopeWords = scopeWords,
                    distractorPool = remember { repository.getAllWords() },
                    onExit = { navController.popBackStack() },
                    onRetryWrongOnly = { navController.navigate("study/review/$REVIEW_TYPE_UNKNOWN") },
                    contentPadding = innerPadding
                )
            }
        }
    }
}

private fun buildContinueInfo(prefs: StudyPrefs, repository: WordRepository): ContinueInfo? {
    val lastDay = prefs.lastDay ?: return null
    val totalWords = repository.getWords(lastDay).size
    if (totalWords == 0) return null
    val progressIndex = prefs.getProgress(lastDay).coerceIn(0, totalWords - 1)
    return ContinueInfo(dayNumber = lastDay, progressIndex = progressIndex, totalWords = totalWords)
}
