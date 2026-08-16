package com.voca.englishwordapp.tts

import android.content.Context
import android.speech.tts.TextToSpeech
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import java.util.Locale

/**
 * 안드로이드 내장 [TextToSpeech]를 감싼 상태 홀더. 엔진/영어 데이터가 없는 기기에서도
 * 크래시 없이 "사용 불가" 상태로만 남도록, 초기화 결과를 [isReady]/[initializationFailed]로
 * 노출한다 — 실제 실패 여부를 확인하기 전([isReady]도 [initializationFailed]도 false인 상태)과
 * 확인 후 실패([initializationFailed] = true)를 구분해야 UI에서 "1회만" 안내할 수 있다.
 */
class WordSpeakerState(context: Context) {

    var isReady: Boolean by mutableStateOf(false)
        private set

    var initializationFailed: Boolean by mutableStateOf(false)
        private set

    private var tts: TextToSpeech? = TextToSpeech(context.applicationContext) { status ->
        val languageResult = if (status == TextToSpeech.SUCCESS) tts?.setLanguage(Locale.US) else null
        val supported = languageResult != null &&
            languageResult != TextToSpeech.LANG_MISSING_DATA &&
            languageResult != TextToSpeech.LANG_NOT_SUPPORTED
        if (supported) {
            isReady = true
        } else {
            initializationFailed = true
        }
    }

    fun speak(text: String) {
        if (!isReady) return
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        tts = null
    }
}

/** [WordSpeakerState]를 만들고, 화면이 사라질 때 자동으로 [WordSpeakerState.shutdown]한다. */
@Composable
fun rememberWordSpeaker(): WordSpeakerState {
    val context = LocalContext.current
    val speaker = remember { WordSpeakerState(context) }
    DisposableEffect(Unit) {
        onDispose { speaker.shutdown() }
    }
    return speaker
}
