import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { generateJson } from '@/lib/gemini'
import {
  REGENERATE_SYSTEM,
  buildRegenerateContents,
  findMealAllergyViolations,
  regeneratedMealSchema,
  validateRegeneratedMeal,
  type RegeneratedMeal,
} from '@/lib/mealRegenerate'

export const runtime = 'nodejs'
export const maxDuration = 60

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// F-15 특정 끼니 재생성.
// 이 끼니 하나만 새 메뉴로 바꾼다. 장보기 목록은 건드리지 않는다(사용자가 체크해 둔 상태가 날아가므로).
// 메뉴가 바뀌면 저장돼 있던 조리법은 더 이상 맞지 않으므로 같이 비운다.
export async function POST(_request: NextRequest, ctx: { params: Promise<{ id: string; mealId: string }> }) {
  const { id, mealId } = await ctx.params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401)

  const { data: meal } = await supabase
    .from('meals')
    .select('id, user_id, slot, name, day_id')
    .eq('id', mealId)
    .eq('plan_id', id)
    .single()

  if (!meal) return errorResponse('NOT_FOUND', '끼니를 찾을 수 없습니다.', 404)
  if (meal.user_id !== user.id) {
    return errorResponse('FORBIDDEN', '본인 식단만 바꿀 수 있습니다.', 403)
  }

  const { data: plan } = await supabase
    .from('meal_plans')
    .select('goal, ingredients, exclusions')
    .eq('id', id)
    .single()

  if (!plan) return errorResponse('NOT_FOUND', '식단을 찾을 수 없습니다.', 404)

  const { data: day } = await supabase
    .from('meal_days')
    .select('day_index')
    .eq('id', meal.day_id)
    .single()

  // 같은 메뉴가 또 나오지 않도록 현재 식단의 메뉴 이름을 모두 넘긴다
  const { data: siblings } = await supabase
    .from('meals')
    .select('name')
    .eq('plan_id', id)

  const existingNames = (siblings ?? []).map(m => m.name)
  const exclusions: string[] = plan.exclusions ?? []

  const contents = buildRegenerateContents({
    slot: meal.slot,
    dayIndex: day?.day_index ?? 1,
    currentName: meal.name,
    goal: plan.goal,
    ingredients: plan.ingredients ?? [],
    exclusions,
    existingNames,
  })

  let generated: RegeneratedMeal
  try {
    generated = await generateJson({
      systemInstruction: REGENERATE_SYSTEM,
      contents,
      responseSchema: regeneratedMealSchema,
    })
  } catch {
    return errorResponse('AI_GENERATION_FAILED', '새 메뉴를 만들지 못했어요. 잠시 후 다시 시도해 주세요.', 502)
  }

  // 식단 생성과 같은 규칙: 구조·알레르기 검증에 실패하면 1회만 재생성한다
  const structureIssue = validateRegeneratedMeal(generated, existingNames)
  const violations = findMealAllergyViolations(generated, exclusions)
  const issue = structureIssue ?? (violations.length > 0 ? `제외한 재료가 포함되었습니다: ${violations.join(', ')}` : null)

  if (issue) {
    try {
      generated = await generateJson({
        systemInstruction: REGENERATE_SYSTEM,
        contents: `${contents}\n\n이전 시도에서 문제가 있었습니다: ${issue}\n반드시 규칙을 지켜 다시 작성하라.`,
        responseSchema: regeneratedMealSchema,
      })
    } catch {
      return errorResponse('AI_GENERATION_FAILED', '새 메뉴를 만들지 못했어요. 잠시 후 다시 시도해 주세요.', 502)
    }

    if (
      validateRegeneratedMeal(generated, existingNames) ||
      findMealAllergyViolations(generated, exclusions).length > 0
    ) {
      // 검증에 실패한 메뉴는 저장하지 않는다
      return errorResponse(
        'MEAL_VALIDATION_FAILED',
        '제외한 재료 없이 안전한 메뉴를 만들지 못했어요.',
        422
      )
    }
  }

  const { error: updateError } = await supabase
    .from('meals')
    .update({
      name: generated.name,
      reason: generated.reason ?? null,
      tags: generated.tags ?? [],
      used_ingredients: generated.usedIngredients,
      needed_ingredients: generated.neededIngredients,
      // 메뉴가 바뀌었으니 완료 체크와 예전 조리법은 무효다
      is_done: false,
      recipe_ingredients: [],
      recipe_steps: [],
      recipe_servings: null,
      recipe_minutes: null,
      recipe_tip: null,
      recipe_generated_at: null,
    })
    .eq('id', mealId)
    .eq('user_id', user.id)

  if (updateError) {
    return errorResponse('SAVE_FAILED', '새 메뉴를 저장하지 못했어요.', 500)
  }

  return Response.json({
    ok: true,
    data: {
      id: mealId,
      name: generated.name,
      reason: generated.reason ?? null,
      tags: generated.tags ?? [],
      usedIngredients: generated.usedIngredients,
      neededIngredients: generated.neededIngredients,
    },
  })
}
