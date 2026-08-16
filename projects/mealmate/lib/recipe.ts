import { Type } from '@google/genai'

// F-16 조리법 상세.
// 식단 생성(mealPlan.ts)과 달리 "한 끼"만 다룬다. 카드를 펼칠 때 그 끼니 하나만 생성하므로
// 응답이 작고 빨라서, 21끼를 한꺼번에 만들 때 생기는 응답 잘림·타임아웃 위험이 없다.

export const RECIPE_SYSTEM = `너는 한국어로 답하는 요리 레시피 작성자다. 아래 규칙을 반드시 지켜라.
- 제외 식품 목록에 있는 재료와 그 파생어(가공품, 다른 이름, 같은 원재료로 만든 음식)는 절대 사용하지 않는다.
- 요리 초보자가 그대로 따라 할 수 있게 구체적으로 쓴다.
- 재료는 분량을 함께 적는다. 예: "감자 2개(중간 크기)", "간장 1큰술".
- 조리 순서는 3단계 이상 8단계 이하로 쓰고, 한 단계에 한 가지 행동만 담는다.
- 불 세기와 시간을 가능한 한 함께 적는다. 예: "중불에서 5분간 볶는다".
- 칼로리, 단백질 등 구체적인 영양 수치는 절대 생성하지 않는다.
- 의료적 조언이나 다이어트 효과를 보장하는 표현을 쓰지 않는다.
- 모든 텍스트는 한국어로 작성한다.`

export const recipeSchema = {
  type: Type.OBJECT,
  properties: {
    servings: { type: Type.STRING },
    minutes: { type: Type.INTEGER },
    ingredients: { type: Type.ARRAY, items: { type: Type.STRING } },
    steps: { type: Type.ARRAY, items: { type: Type.STRING } },
    tip: { type: Type.STRING },
  },
  required: ['servings', 'minutes', 'ingredients', 'steps'],
}

export type GeneratedRecipe = {
  servings: string
  minutes: number
  ingredients: string[]
  steps: string[]
  tip?: string
}

export function buildRecipeContents(input: {
  mealName: string
  slot: string
  usedIngredients: string[]
  neededIngredients: string[]
  exclusions: string[]
}) {
  const slotLabel: Record<string, string> = {
    breakfast: '아침',
    lunch: '점심',
    dinner: '저녁',
  }
  return [
    `요리 이름: ${input.mealName}`,
    `끼니: ${slotLabel[input.slot] ?? input.slot}`,
    `이 요리에 쓰기로 한 재료: ${[...input.usedIngredients, ...input.neededIngredients].join(', ') || '제시된 재료 없음'}`,
    `절대 쓰면 안 되는 재료: ${input.exclusions.length > 0 ? input.exclusions.join(', ') : '없음'}`,
    '위 요리의 재료(분량 포함)와 조리 순서를 작성하라.',
  ].join('\n')
}

export function validateRecipe(recipe: GeneratedRecipe): string | null {
  if (!Array.isArray(recipe.ingredients) || recipe.ingredients.length === 0) {
    return '재료 목록이 생성되지 않았습니다.'
  }
  if (!Array.isArray(recipe.steps) || recipe.steps.length < 3 || recipe.steps.length > 8) {
    return '조리 순서가 3~8단계로 생성되지 않았습니다.'
  }
  if (recipe.steps.some(step => typeof step !== 'string' || step.trim().length === 0)) {
    return '조리 순서에 빈 단계가 있습니다.'
  }
  return null
}

// 식단 생성 때와 같은 방식으로, 조리법 본문에도 제외 재료가 섞이지 않았는지 확인한다.
// 조리 순서에 슬쩍 들어가는 경우가 실제로 위험하므로 저장 전에 반드시 검사한다.
export function findRecipeAllergyViolations(recipe: GeneratedRecipe, exclusions: string[]): string[] {
  if (exclusions.length === 0) return []
  const fullText = [
    recipe.servings,
    recipe.tip ?? '',
    ...recipe.ingredients,
    ...recipe.steps,
  ]
    .join(' ')
    .toLowerCase()
  return exclusions.filter(word => fullText.includes(word.toLowerCase()))
}
