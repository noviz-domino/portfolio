// F-14 마크다운 복사.
// 상세 페이지가 이미 들고 있는 데이터를 문자열로 바꾸기만 한다. DB도 AI도 부르지 않는다.
// 조리법은 넣지 않는다. 21끼 분량이면 붙여넣기 어려울 만큼 길어져서, 식단과 장보기까지만 담는다.

const SLOT_LABEL: Record<string, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

const SLOT_ORDER = ['breakfast', 'lunch', 'dinner']

const PRIORITY_LABEL: Record<string, string> = {
  required: '필수',
  recommended: '추천',
  optional: '선택',
}

const GOAL_LABEL: Record<string, string> = {
  loss: '체중 감량',
  maintain: '체중 유지',
  bulk: '벌크업',
  balanced: '균형 식단',
}

type MarkdownMeal = {
  slot: string
  name: string
  reason: string | null
  used_ingredients: string[]
  needed_ingredients: string[]
}

type MarkdownDay = {
  day_index: number
  tip: string | null
  meals: MarkdownMeal[]
}

type MarkdownShoppingItem = {
  name: string
  priority: string
  reason: string | null
}

export function buildPlanMarkdown(input: {
  title: string
  goal: string
  mealsPerDay: number
  summary: string | null
  tips: string[]
  days: MarkdownDay[]
  shoppingItems: MarkdownShoppingItem[]
}): string {
  const lines: string[] = []

  lines.push(`# ${input.title}`, '')
  lines.push(`${GOAL_LABEL[input.goal] ?? input.goal} · 하루 ${input.mealsPerDay}끼`, '')

  if (input.summary) lines.push(input.summary, '')

  if (input.tips.length > 0) {
    lines.push('## 이번 주 팁', '')
    input.tips.forEach(tip => lines.push(`- ${tip}`))
    lines.push('')
  }

  for (const day of input.days) {
    lines.push(`## Day ${day.day_index}`, '')
    if (day.tip) lines.push(`> ${day.tip}`, '')

    const sorted = [...day.meals].sort(
      (a, b) => SLOT_ORDER.indexOf(a.slot) - SLOT_ORDER.indexOf(b.slot)
    )
    for (const meal of sorted) {
      lines.push(`### ${SLOT_LABEL[meal.slot] ?? meal.slot} · ${meal.name}`)
      if (meal.reason) lines.push(meal.reason)
      const athome = meal.used_ingredients ?? []
      const needed = meal.needed_ingredients ?? []
      if (athome.length > 0) lines.push(`- 집에 있는 재료: ${athome.join(', ')}`)
      if (needed.length > 0) lines.push(`- 사와야 하는 재료: ${needed.join(', ')}`)
      lines.push('')
    }
  }

  if (input.shoppingItems.length > 0) {
    lines.push('## 장보기 목록', '')
    for (const item of input.shoppingItems) {
      const priority = PRIORITY_LABEL[item.priority] ?? item.priority
      const reason = item.reason ? ` — ${item.reason}` : ''
      lines.push(`- [ ] ${item.name} (${priority})${reason}`)
    }
    lines.push('')
  }

  lines.push('---', 'AI가 만든 참고용 식단이에요. 실제 조리 시 재료 상태와 알레르기를 직접 확인해 주세요.')

  return lines.join('\n')
}
