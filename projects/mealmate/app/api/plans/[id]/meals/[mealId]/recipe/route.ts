import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { generateJson } from '@/lib/gemini'
import {
  RECIPE_SYSTEM,
  buildRecipeContents,
  findRecipeAllergyViolations,
  recipeSchema,
  validateRecipe,
  type GeneratedRecipe,
} from '@/lib/recipe'

export const runtime = 'nodejs'
export const maxDuration = 60

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// F-16 조리법 생성.
// 카드를 처음 펼칠 때 호출된다. 이미 저장된 조리법이 있으면 그대로 돌려주므로
// 같은 끼니를 여러 번 펼쳐도 Gemini를 다시 부르지 않는다.
export async function POST(_request: NextRequest, ctx: { params: Promise<{ id: string; mealId: string }> }) {
  const { id, mealId } = await ctx.params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401)

  const { data: meal } = await supabase
    .from('meals')
    .select('id, user_id, slot, name, used_ingredients, needed_ingredients, recipe_ingredients, recipe_steps, recipe_servings, recipe_minutes, recipe_tip')
    .eq('id', mealId)
    .eq('plan_id', id)
    .single()

  if (!meal) return errorResponse('NOT_FOUND', '끼니를 찾을 수 없습니다.', 404)
  if (meal.user_id !== user.id) {
    return errorResponse('FORBIDDEN', '본인 식단의 조리법만 만들 수 있습니다.', 403)
  }

  // 이미 만들어 둔 조리법이 있으면 재생성하지 않는다
  if (meal.recipe_steps?.length > 0) {
    return Response.json({
      ok: true,
      data: {
        ingredients: meal.recipe_ingredients,
        steps: meal.recipe_steps,
        servings: meal.recipe_servings,
        minutes: meal.recipe_minutes,
        tip: meal.recipe_tip,
      },
    })
  }

  const { data: plan } = await supabase
    .from('meal_plans')
    .select('exclusions')
    .eq('id', id)
    .single()

  const exclusions: string[] = plan?.exclusions ?? []

  const contents = buildRecipeContents({
    mealName: meal.name,
    slot: meal.slot,
    usedIngredients: meal.used_ingredients ?? [],
    neededIngredients: meal.needed_ingredients ?? [],
    exclusions,
  })

  let recipe: GeneratedRecipe
  try {
    recipe = await generateJson({
      systemInstruction: RECIPE_SYSTEM,
      contents,
      responseSchema: recipeSchema,
    })
  } catch {
    return errorResponse('AI_GENERATION_FAILED', '조리법을 만들지 못했어요. 잠시 후 다시 시도해 주세요.', 502)
  }

  // 식단 생성과 같은 규칙: 구조·알레르기 검증에 실패하면 1회만 재생성한다
  const structureIssue = validateRecipe(recipe)
  const violations = findRecipeAllergyViolations(recipe, exclusions)
  const issue = structureIssue ?? (violations.length > 0 ? `제외한 재료가 포함되었습니다: ${violations.join(', ')}` : null)

  if (issue) {
    try {
      recipe = await generateJson({
        systemInstruction: RECIPE_SYSTEM,
        contents: `${contents}\n\n이전 시도에서 문제가 있었습니다: ${issue}\n반드시 규칙을 지켜 다시 작성하라.`,
        responseSchema: recipeSchema,
      })
    } catch {
      return errorResponse('AI_GENERATION_FAILED', '조리법을 만들지 못했어요. 잠시 후 다시 시도해 주세요.', 502)
    }

    if (validateRecipe(recipe) || findRecipeAllergyViolations(recipe, exclusions).length > 0) {
      // 검증에 실패한 조리법은 저장하지 않는다
      return errorResponse(
        'RECIPE_VALIDATION_FAILED',
        '제외한 재료 없이 안전한 조리법을 만들지 못했어요.',
        422
      )
    }
  }

  const { error: updateError } = await supabase
    .from('meals')
    .update({
      recipe_ingredients: recipe.ingredients,
      recipe_steps: recipe.steps,
      recipe_servings: recipe.servings,
      recipe_minutes: recipe.minutes,
      recipe_tip: recipe.tip ?? null,
      recipe_generated_at: new Date().toISOString(),
    })
    .eq('id', mealId)
    .eq('user_id', user.id)

  if (updateError) {
    return errorResponse('SAVE_FAILED', '조리법을 저장하지 못했어요.', 500)
  }

  return Response.json({
    ok: true,
    data: {
      ingredients: recipe.ingredients,
      steps: recipe.steps,
      servings: recipe.servings,
      minutes: recipe.minutes,
      tip: recipe.tip ?? null,
    },
  })
}
