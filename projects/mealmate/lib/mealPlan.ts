import { Type } from '@google/genai'

export const GOALS = ['loss', 'maintain', 'bulk', 'balanced'] as const
export type Goal = (typeof GOALS)[number]

// 식단 일수. 기본은 3일이다.
// 장을 보통 2~3일에 한 번 보므로 3일이 실제 사용 주기에 맞고, 한 번에 만드는 끼니가
// 21끼에서 9끼로 줄어 응답이 잘리거나 타임아웃될 위험도 함께 줄어든다.
// 기획서 F-07은 7일 기준이라 7일도 그대로 고를 수 있게 남겨 둔다.
// DB의 meal_days.day_index 제약이 1~7이므로 3일도 그 안에 들어간다(마이그레이션 불필요).
export const PLAN_DAYS = [3, 7] as const
export type PlanDays = (typeof PLAN_DAYS)[number]
export const DEFAULT_PLAN_DAYS: PlanDays = 3

export const SLOTS_BY_MEALS_PER_DAY: Record<2 | 3, string[]> = {
  2: ['lunch', 'dinner'],
  3: ['breakfast', 'lunch', 'dinner'],
}

export type MealPlanInput = {
  ingredients: string[]
  exclusions: string[]
  goal: Goal
  mealsPerDay: 2 | 3
  days: PlanDays
}

export const MEAL_SYSTEM = `너는 한국어로 답하는 식단 플래너다. 아래 규칙을 반드시 지켜라.
- 제외 식품 목록에 있는 재료와 그 파생어(가공품, 다른 이름, 같은 원재료로 만든 음식)는 절대 사용하지 않는다.
- 사용자가 가진 재료를 우선적으로 활용한다.
- 요청받은 일수만큼만 식단을 생성한다. dayIndex는 1부터 요청 일수까지 하나도 빠뜨리지 않고 채운다.
- 하루 끼니 수가 2이면 lunch와 dinner만 생성하고, 3이면 breakfast, lunch, dinner를 모두 생성한다.
- 칼로리, 단백질 등 구체적인 영양 수치는 절대 생성하지 않는다.
- 의료적 조언이나 다이어트 효과를 보장하는 표현을 쓰지 않는다.
- 장보기 목록(shoppingItems)은 각 끼니의 neededIngredients를 집계한 결과여야 한다.
- 모든 텍스트는 한국어로 작성한다.`

export function buildContents(input: MealPlanInput) {
  const goalLabel: Record<Goal, string> = {
    loss: '체중 감량',
    maintain: '체중 유지',
    bulk: '벌크업',
    balanced: '균형 식단',
  }
  return [
    `보유 재료: ${input.ingredients.join(', ')}`,
    `제외할 재료: ${input.exclusions.length > 0 ? input.exclusions.join(', ') : '없음'}`,
    `목표: ${goalLabel[input.goal]}`,
    `식단 일수: ${input.days}일 (dayIndex 1~${input.days})`,
    `하루 끼니 수: ${input.mealsPerDay}`,
  ].join('\n')
}

const mealSchema = {
  type: Type.OBJECT,
  properties: {
    slot: { type: Type.STRING, enum: ['breakfast', 'lunch', 'dinner'] },
    name: { type: Type.STRING },
    usedIngredients: { type: Type.ARRAY, items: { type: Type.STRING } },
    neededIngredients: { type: Type.ARRAY, items: { type: Type.STRING } },
    reason: { type: Type.STRING },
    tags: { type: Type.ARRAY, items: { type: Type.STRING } },
  },
  required: ['slot', 'name', 'usedIngredients', 'neededIngredients', 'tags'],
}

export const mealPlanSchema = {
  type: Type.OBJECT,
  properties: {
    title: { type: Type.STRING },
    summary: { type: Type.STRING },
    tips: { type: Type.ARRAY, items: { type: Type.STRING } },
    days: {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          dayIndex: { type: Type.INTEGER },
          tip: { type: Type.STRING },
          meals: { type: Type.ARRAY, items: mealSchema },
        },
        required: ['dayIndex', 'meals'],
      },
    },
    shoppingItems: {
      type: Type.ARRAY,
      items: {
        type: Type.OBJECT,
        properties: {
          name: { type: Type.STRING },
          category: { type: Type.STRING },
          priority: { type: Type.STRING, enum: ['required', 'recommended', 'optional'] },
          reason: { type: Type.STRING },
        },
        required: ['name', 'category', 'priority'],
      },
    },
  },
  required: ['title', 'summary', 'days', 'shoppingItems'],
}

export type GeneratedMeal = {
  slot: string
  name: string
  usedIngredients: string[]
  neededIngredients: string[]
  reason?: string
  tags: string[]
}

export type GeneratedDay = {
  dayIndex: number
  tip?: string
  meals: GeneratedMeal[]
}

export type GeneratedPlan = {
  title: string
  summary: string
  tips?: string[]
  days: GeneratedDay[]
  shoppingItems: Array<{
    name: string
    category: string
    priority: 'required' | 'recommended' | 'optional'
    reason?: string
  }>
}

export function validateStructure(
  plan: GeneratedPlan,
  mealsPerDay: 2 | 3,
  days: PlanDays
): string | null {
  if (!Array.isArray(plan.days) || plan.days.length !== days) {
    return `${days}일치 식단이 생성되지 않았습니다.`
  }
  const expectedSlots = SLOTS_BY_MEALS_PER_DAY[mealsPerDay]
  const seenDays = new Set<number>()
  for (const day of plan.days) {
    if (day.dayIndex < 1 || day.dayIndex > days || seenDays.has(day.dayIndex)) {
      return '식단의 날짜 구성이 올바르지 않습니다.'
    }
    seenDays.add(day.dayIndex)
    if (!Array.isArray(day.meals) || day.meals.length !== expectedSlots.length) {
      return '하루 끼니 수가 요청과 다릅니다.'
    }
    const slots = day.meals.map(m => m.slot).sort()
    if (JSON.stringify(slots) !== JSON.stringify([...expectedSlots].sort())) {
      return '끼니 구성이 올바르지 않습니다.'
    }
  }
  if (!Array.isArray(plan.shoppingItems)) {
    return '장보기 목록이 생성되지 않았습니다.'
  }
  return null
}

export function findAllergyViolations(plan: GeneratedPlan, exclusions: string[]): string[] {
  if (exclusions.length === 0) return []
  const haystacks: string[] = []
  for (const day of plan.days) {
    for (const meal of day.meals) {
      haystacks.push(meal.name, meal.reason ?? '', ...meal.usedIngredients, ...meal.neededIngredients, ...meal.tags)
    }
  }
  for (const item of plan.shoppingItems) {
    haystacks.push(item.name, item.reason ?? '')
  }
  const fullText = haystacks.join(' ').toLowerCase()
  return exclusions.filter(word => fullText.includes(word.toLowerCase()))
}
