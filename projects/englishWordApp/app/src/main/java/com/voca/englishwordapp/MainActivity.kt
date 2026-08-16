package com.voca.englishwordapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.google.android.gms.ads.MobileAds
import com.voca.englishwordapp.ui.AppNavHost
import com.voca.englishwordapp.ui.theme.EnglishWordAppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // installSplashScreen()은 super.onCreate() 이전에 호출해야 한다 (core-splashscreen 요구사항).
        // 매니페스트의 Theme.EnglishWordApp.Splash가 postSplashScreenTheme로 지정한
        // Base.Theme.EnglishWordApp으로 자동 전환된다.
        installSplashScreen()
        super.onCreate(savedInstanceState)

        // targetSdk 36에서는 edge-to-edge가 어차피 강제되지만, 명시적으로 호출해두면
        // minSdk 24~34 기기에서도 같은 레이아웃으로 동작한다(시스템 바 뒤까지 그림).
        // Play Console이 "일부 사용자에게는 더 넓은 화면이 표시되지 않을 수 있습니다" 경고에서
        // 직접 권장하는 API다. 시스템 바 영역 여백은 AppNavHost의 Scaffold가 WindowInsets로
        // 처리하고, 바 아이콘 색은 EnglishWordAppTheme이 담당한다.
        enableEdgeToEdge()

        // 1. 광고 초기화
        MobileAds.initialize(this) {}

        // 2~4. 화면 구성/전환은 AppNavHost(Compose)가 담당한다.
        setContent {
            EnglishWordAppTheme {
                AppNavHost()
            }
        }
    }
}
