package com.voca.englishwordapp.ui.ads

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView

/**
 * 실제 운영용 배너 광고 단위 ID. 상단/하단을 각각 별도로 만들었다 (기존 것은 AdMob에서
 * 사용 불가 처리되어 새로 발급받음). 개발 중 실수로 클릭해도 문제없도록, 이 ID를 쓰는
 * 기기는 AdMob 콘솔의 "테스트 기기"에 등록해서 테스트 광고만 받게 해둘 것 — 등록되지 않은
 * 기기에서는 진짜 광고가 나오니 함부로 클릭하지 말 것.
 */
const val TOP_AD_UNIT_ID = "ca-app-pub-9599668530205647/4266447987"
const val BOTTOM_AD_UNIT_ID = "ca-app-pub-9599668530205647/3044177292"

/**
 * 상/하단에 고정으로 붙는 AdMob 배너. 기존 View 기반 `AdView`를 그대로 `AndroidView`로 감싼다 —
 * Compose용 배너 API가 따로 있는 게 아니라 View를 재사용하는 것이 정석이다.
 */
@Composable
fun AdBanner(adUnitId: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier.fillMaxWidth(),
        factory = { context ->
            AdView(context).apply {
                setAdSize(AdSize.BANNER)
                this.adUnitId = adUnitId
                loadAd(AdRequest.Builder().build())
            }
        }
    )
}
