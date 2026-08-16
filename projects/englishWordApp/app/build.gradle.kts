plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.voca.englishwordapp"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.voca.englishwordapp"
        minSdk = 24
        //noinspection EditedTargetSdkVersion
        targetSdk = 36
        //아래 두줄이 버전 갱신하는 부분. 두줄만 바꿔야함.
        versionCode = 11   //반드시 정수여야함. 구글플레이스토어의 시스템이 인식하려면 이전 숫자보다 부조건 커야함.
        versionName = "11.0"    //사용자에게 보이는 버전.

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // 우리 코드에는 네이티브(NDK) 코드가 없다 - play-services-ads(AdMob)가 담고 있는
            // .so 라이브러리의 디버그 심볼을 AAB에 함께 담아 Play Console 경고("네이티브 코드가
            // 있지만 디버그 기호가 업로드되지 않음")를 없앤다. SYMBOL_TABLE은 크래시 스택 트레이스
            // 해석에 필요한 최소 정보만 담아 FULL보다 용량이 훨씬 작다.
            ndk {
                debugSymbolLevel = "SYMBOL_TABLE"
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        // 홈 하단 정보에 versionName을 표시하려고 켰다. AGP 8부터 기본값이 false다.
        // 이걸 켜두면 버전 갱신 시 versionCode/versionName 두 줄만 고치면 화면에도 반영된다.
        buildConfig = true
    }
}

dependencies {

    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
    implementation("com.google.android.gms:play-services-ads:25.4.0")
    // 구글admob 챗gpt 코드 추가
    implementation(libs.core.splashscreen)
    // play-services-ads가 오래된 androidx.fragment:1.1.0을 끌어와서 명시적으로 최신 버전으로 강제
    implementation(libs.fragment)

    // Compose — Phase 2부터 유일한 UI 계층 (View 기반 appcompat/material/constraintlayout 제거됨)
    implementation(platform(libs.compose.bom))
    androidTestImplementation(platform(libs.compose.bom))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
    implementation(libs.activity.compose)
    implementation(libs.navigation.compose)
    implementation(libs.lifecycle.viewmodel.compose)
}