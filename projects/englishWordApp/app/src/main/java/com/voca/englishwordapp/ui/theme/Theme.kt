package com.voca.englishwordapp.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColors = lightColorScheme(
    primary = Color(0xFF6B4FB3),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE9DFFF),
    onPrimaryContainer = Color(0xFF251046),
    secondary = Color(0xFF8A5B78),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF6E8F1),
    onSecondaryContainer = Color(0xFF3A2132),
    tertiary = Color(0xFF9A405A),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFFFD9E2),
    onTertiaryContainer = Color(0xFF3F0015),
    error = Color(0xFFB3261E),
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    background = Color(0xFFFFFBFF),
    onBackground = Color(0xFF1D1A20),
    surface = Color(0xFFFFFBFF),
    onSurface = Color(0xFF1D1A20),
    surfaceVariant = Color(0xFFE9E1EB),
    onSurfaceVariant = Color(0xFF4A454D),
    outline = Color(0xFF7B747E)
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFD2BBFF),
    onPrimary = Color(0xFF3B1D78),
    primaryContainer = Color(0xFF52388F),
    onPrimaryContainer = Color(0xFFEBDDFF),
    secondary = Color(0xFFE7BBD5),
    onSecondary = Color(0xFF43263A),
    secondaryContainer = Color(0xFF5C4055),
    onSecondaryContainer = Color(0xFFFFD8EE),
    tertiary = Color(0xFFFFB1C2),
    onTertiary = Color(0xFF5F1130),
    tertiaryContainer = Color(0xFF763248),
    onTertiaryContainer = Color(0xFFFFD9E2),
    error = Color(0xFFFFB4AB),
    errorContainer = Color(0xFF6F3F4D),
    onErrorContainer = Color(0xFFFFD9E2),
    background = Color(0xFF1F1D21),
    onBackground = Color(0xFFE8E0E8),
    surface = Color(0xFF1F1D21),
    onSurface = Color(0xFFE8E0E8),
    surfaceVariant = Color(0xFF4A454D),
    onSurfaceVariant = Color(0xFFCEC5CF),
    outline = Color(0xFF958E98)
)

/**
 * 앱 전체를 감싸는 Material3 테마. light/dark 시스템 설정을 따른다.
 *
 * targetSdk 36부터 edge-to-edge가 강제되어 상태바/네비게이션 바가 항상 투명하게 그려진다.
 * 그 위에 놓이는 시계/배터리/뒤로가기 같은 시스템 아이콘은 밝은 아이콘과 어두운 아이콘 중
 * 하나를 앱이 직접 골라줘야 하는데, 이전에는 아무 것도 지정하지 않아서 항상 밝은(흰색)
 * 아이콘으로 남아 있었다 — 다크 모드(어두운 배경)에서는 잘 보였지만 라이트 모드(밝은 배경)에서는
 * 흰 아이콘이 거의 안 보였다 (실기기에서 발견된 버그). 여기서 다크 모드 여부에 맞춰
 * `isAppearanceLightStatusBars`/`isAppearanceLightNavigationBars`를 매번 갱신해준다.
 */
@Composable
fun EnglishWordAppTheme(content: @Composable () -> Unit) {
    val darkTheme = isSystemInDarkTheme()
    val colorScheme = if (darkTheme) DarkColors else LightColors

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            val insetsController = WindowCompat.getInsetsController(window, view)
            // 라이트 테마 = 배경이 밝음 = 어두운 아이콘이 잘 보임 (true).
            insetsController.isAppearanceLightStatusBars = !darkTheme
            insetsController.isAppearanceLightNavigationBars = !darkTheme
        }
    }

    MaterialTheme(colorScheme = colorScheme, content = content)
}
