package com.voca.englishwordapp.ui.day

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.voca.englishwordapp.R
import com.voca.englishwordapp.data.WordRepository

/**
 * 날짜 선택 화면. [WordRepository.getDays]가 dayNumber 오름차순으로 정렬해 반환하므로
 * 항상 day1→day30 순서다. [completedDays]에 있는 day는 "완료" 표시, 아직 안 끝났지만
 * 진행 중인 day는 [progressByDay]의 저장된 위치로 "N/전체" 표시를 붙인다.
 */
@Composable
fun DayListScreen(
    days: List<WordRepository.DaySummary>,
    completedDays: Set<Int>,
    progressByDay: Map<Int, Int>,
    onDaySelected: (Int) -> Unit,
    contentPadding: PaddingValues = PaddingValues()
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(
            start = 20.dp,
            end = 20.dp,
            top = contentPadding.calculateTopPadding() + 20.dp,
            bottom = contentPadding.calculateBottomPadding() + 20.dp
        ),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(days, key = { it.dayNumber }) { day ->
            val completedLabel = stringResource(R.string.day_completed)
            val progressLabel = stringResource(
                R.string.day_progress_format,
                (progressByDay[day.dayNumber] ?: 0) + 1,
                day.wordCount
            )
            val status = when {
                day.dayNumber in completedDays -> completedLabel
                (progressByDay[day.dayNumber] ?: 0) > 0 -> progressLabel
                else -> null
            }
            Button(
                onClick = { onDaySelected(day.dayNumber) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(day.day)
                    if (status != null) {
                        Text(status, style = MaterialTheme.typography.labelMedium)
                    }
                }
            }
        }
    }
}
