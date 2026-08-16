package com.voca.englishwordapp.data

private val DAY_NUMBER_REGEX = Regex("day(\\d+)", RegexOption.IGNORE_CASE)

/**
 * `assets/words.csv` (Day,Word,Meaning 헤더)를 RFC4180 규칙에 맞게 파싱한다.
 *
 * 기존 `MainActivity.java`의 `line.split(",", 3)`은 따옴표를 해석하지 않아, 뜻에 쉼표가 있어
 * `"..."`로 감싼 행에서 따옴표 문자가 화면에 그대로 노출되는 문제가 있었다. 이 파서는:
 * - `"..."`로 감싼 필드 내부의 쉼표는 보존하고, 감싸는 따옴표 자체는 제거한다.
 * - `""` 이스케이프는 `"` 한 글자로 복원한다.
 * - 필드가 3개 미만이거나 day 값에서 숫자를 뽑을 수 없는 행(깨진 레코드)은 건너뛴다.
 */
object CsvWordParser {

    /** [lines]의 첫 줄을 헤더로 보고 건너뛴 뒤, 남은 줄을 [Word] 목록으로 변환한다. */
    fun parse(lines: List<String>): List<Word> {
        if (lines.isEmpty()) return emptyList()
        return lines.asSequence()
            .drop(1)
            .mapNotNull { parseLine(it) }
            .toList()
    }

    internal fun parseLine(rawLine: String): Word? {
        val line = rawLine.removeSuffix("\r")
        if (line.isBlank()) return null

        val fields = splitCsvLine(line)
        if (fields.size < 3) return null

        val day = fields[0].trim()
        val word = fields[1].trim()
        // 뜻 필드 뒤에 해석되지 않은 여분의 쉼표가 남아 있어도(따옴표 없는 데이터 오류 대비)
        // 기존 동작처럼 나머지를 전부 뜻으로 합쳐 유실을 막는다.
        val meaning = fields.drop(2).joinToString(",").trim()
        val dayNumber = DAY_NUMBER_REGEX.find(day)?.groupValues?.get(1)?.toIntOrNull() ?: return null

        if (word.isEmpty() || meaning.isEmpty()) return null

        return Word(day = day, dayNumber = dayNumber, word = word, meaning = meaning)
    }

    /** RFC4180 규칙(따옴표로 감싼 구간의 쉼표 보존, `""` 이스케이프)으로 한 줄을 필드로 나눈다. */
    internal fun splitCsvLine(line: String): List<String> {
        val fields = mutableListOf<String>()
        val current = StringBuilder()
        var inQuotes = false
        var i = 0
        while (i < line.length) {
            val c = line[i]
            when {
                inQuotes && c == '"' && i + 1 < line.length && line[i + 1] == '"' -> {
                    current.append('"')
                    i++ // "" -> " 로 축약
                }
                c == '"' -> inQuotes = !inQuotes
                c == ',' && !inQuotes -> {
                    fields.add(current.toString())
                    current.clear()
                }
                else -> current.append(c)
            }
            i++
        }
        fields.add(current.toString())
        return fields
    }
}
