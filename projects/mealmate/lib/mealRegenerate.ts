import { Type } from '@google/genai'

// F-15 특정 끼니 재생성.
// 식단 생성(mealPlan.ts)은 7일 21끼를 한 번에 만들지만, 여기서는 딱 한 끼만 바꾼다.
// 나머지 날짜와 장보기 목록은 건드리지 않는다.

export const REGENERATE_SYSTEM = `너는 한국어로 답하는 식단 플래너다. 아래 규칙을 반드시 지켜라.
- 제외 식품 목록에 있는 재료와 그 파생어(가공품, 다른 이름, 같은 원재료로 만든 음식)는 절대 사용하지 않는다.
- 사용자가 가진 재료를 우선적으로 활용한다.
- 이미 이 식단에 들어 있는 메뉴와 겹치지 않는 새로운 메뉴를 제안한다.
- 요청받은 끼니(아침/점심/저녁)에 어울리는 메뉴여야 한다.
- 칼로리, 단백질 등 구체적인 영양 수치는 절대 생성하지 않는다.
- 의료적 조언이나 다이어트 효과를 보장하는 표현을 쓰지 않는다.
- 모든 텍스트는 한국어로 작성한다.`

export const regeneratedMealSchema = {
  type: Type.OBJECT,
  properties: {
    name: { type: Type.STRING },
    usedIngredients: { type: Type.ARRAY, items: { type: Type.STRING } },
    neededIngredients: { type: Type.ARRAY, items: { type: Type.STRING } },
    reason: { type: Type.STRING },
    tags: { type: Type.ARRAY, items: { type: Type.STRING } },
  },
  required: ['name', 'usedIngredients', 'neededIngredients', 'tags'],
}

export type RegeneratedMeal = {
  name: string
  usedIngredients: string[]
  neededIngredients: string[]
  reason?: string
  tags: string[]
}

const GOAL_LABEL: Record<string, string> = {
  loss: '체중 감량',
  maintain: '체중 유지',
  bulk: '벌크업',
  balanced: '균형 식단',
}

const SLOT_LABEL: Record<string, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

export function buildRegenerateContents(input: {
  slot: string
  dayIndex: number
  currentName: string
  goal: string
  ingredients: string[]
  exclusions: string[]
  existingNames: string[]
}) {
  return [
    `보유 재료: ${input.ingredients.length > 0 ? input.ingredients.join(', ') : '없음'}`,
    `제외할 재료: ${input.exclusions.length > 0 ? input.exclusions.join(', ') : '없음'}`,
    `목표: ${GOAL_LABEL[input.goal] ?? input.goal}`,
    `바꿀 끼니: ${input.dayIndex}일차 ${SLOT_LABEL[input.slot] ?? input.slot}`,
    `지금 메뉴: ${input.currentName} (이 메뉴는 제외하고 다른 것을 제안하라)`,
    `이 식단에 이미 있는 메뉴: ${input.existingNames.join(', ')}`,
    '위 끼니를 대체할 새로운 메뉴 한 가지를 제안하라.',
  ].join('\n')
}

export function validateRegeneratedMeal(
  meal: RegeneratedMeal,
  existingNames: string[]
): string | null {
  if (typeof meal.name !== 'string' || meal.name.trim().length === 0) {
    return '메뉴 이름이 생성되지 않았습니다.'
  }
  if (!Array.isArray(meal.usedIngredients) || !Array.isArray(meal.neededIngredients)) {
    return '재료 목록이 생성되지 않았습니다.'
  }
  if (meal.usedIngredients.length === 0 && meal.neededIngredients.length === 0) {
    return '재료가 하나도 없는 메뉴입니다.'
  }
  // 같은 메뉴가 또 나오면 재생성한 의미가 없다
  const normalized = meal.name.trim().toLowerCase()
  if (existingNames.some(name => name.trim().toLowerCase() === normalized)) {
    return '식단에 이미 있는 메뉴가 다시 생성되었습니다.'
  }
  return null
}

// 식단·조리법 생성과 같은 규칙으로, 저장 전에 제외 재료가 섞였는지 확인한다.
export function findMealAllergyViolations(meal: RegeneratedMeal, exclusions: string[]): string[] {
  if (exclusions.length === 0) return []
  const fullText = [
    meal.name,
    meal.reason ?? '',
    ...meal.usedIngredients,
    ...meal.neededIngredients,
    ...(meal.tags ?? []),
  ]
    .join(' ')
    .toLowerCase()
  return exclusions.filter(word => fullText.includes(word.toLowerCase()))
}
