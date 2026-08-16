import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { generateJson } from '@/lib/gemini'
import {
  GOALS,
  MEAL_SYSTEM,
  PLAN_DAYS,
  buildContents,
  findAllergyViolations,
  mealPlanSchema,
  validateStructure,
  type GeneratedPlan,
  type Goal,
  type PlanDays,
} from '@/lib/mealPlan'

export const runtime = 'nodejs'
export const maxDuration = 60

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// F-09 내 식단 목록 (RLS의 plans_public_select만으로는 남의 공개 식단도 보이므로
// user_id를 명시적으로 걸어서 본인 것만 가져온다)
export async function GET() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401)
  }

  const { data, error } = await supabase
    .from('meal_plans')
    .select('id, title, goal, ingredients, summary, is_public, total_meals, done_meals, created_at')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })

  if (error) {
    return errorResponse('FETCH_FAILED', '식단 목록을 불러오지 못했어요.', 500)
  }

  return Response.json({ ok: true, data: data ?? [] })
}

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return errorResponse('AUTH_REQUIRED', '식단을 만들려면 먼저 로그인해 주세요.', 401)
  }

  const body = await request.json().catch(() => null)
  if (!body || typeof body !== 'object') {
    return errorResponse('INVALID_BODY', '요청 형식이 올바르지 않습니다.', 400)
  }

  const ingredients = Array.isArray(body.ingredients) ? body.ingredients.filter((v: unknown) => typeof v === 'string') : []
  const exclusions = Array.isArray(body.exclusions) ? body.exclusions.filter((v: unknown) => typeof v === 'string') : []
  const goal = body.goal
  const mealsPerDay = body.mealsPerDay
  const days = body.days

  if (ingredients.length < 3 || ingredients.length > 20 || ingredients.some((v: string) => v.length > 30)) {
    return errorResponse('INVALID_INGREDIENTS', '재료는 3개 이상 20개 이하로 입력해 주세요.', 400)
  }
  if (exclusions.length > 20 || exclusions.some((v: string) => v.length > 30)) {
    return errorResponse('INVALID_EXCLUSIONS', '제외 재료 입력이 올바르지 않습니다.', 400)
  }
  if (!GOALS.includes(goal)) {
    return errorResponse('INVALID_GOAL', '목표 값이 올바르지 않습니다.', 400)
  }
  if (mealsPerDay !== 2 && mealsPerDay !== 3) {
    return errorResponse('INVALID_MEALS_PER_DAY', '하루 끼니 수는 2 또는 3이어야 합니다.', 400)
  }
  if (!PLAN_DAYS.includes(days)) {
    return errorResponse('INVALID_DAYS', '식단 일수는 3일 또는 7일이어야 합니다.', 400)
  }

  const input = {
    ingredients,
    exclusions,
    goal: goal as Goal,
    mealsPerDay: mealsPerDay as 2 | 3,
    days: days as PlanDays,
  }
  const contents = buildContents(input)

  let plan: GeneratedPlan
  try {
    plan = await generateJson({
      systemInstruction: MEAL_SYSTEM,
      contents,
      responseSchema: mealPlanSchema,
    })
  } catch {
    return errorResponse('AI_GENERATION_FAILED', '식단 생성에 실패했어요. 잠시 후 다시 시도해 주세요.', 502)
  }

  const structureIssue = validateStructure(plan, input.mealsPerDay, input.days)
  const violations = findAllergyViolations(plan, input.exclusions)
  const issue = structureIssue ?? (violations.length > 0 ? `제외한 재료가 포함되었습니다: ${violations.join(', ')}` : null)

  if (issue) {
    try {
      plan = await generateJson({
        systemInstruction: MEAL_SYSTEM,
        contents: `${contents}\n\n이전 시도에서 문제가 있었습니다: ${issue}\n반드시 규칙을 지켜 다시 생성하세요.`,
        responseSchema: mealPlanSchema,
      })
    } catch {
      return errorResponse('AI_GENERATION_FAILED', '식단 생성에 실패했어요. 잠시 후 다시 시도해 주세요.', 502)
    }

    const structureIssue = validateStructure(plan, input.mealsPerDay, input.days)
    const violations = findAllergyViolations(plan, input.exclusions)
    if (structureIssue || violations.length > 0) {
      return errorResponse(
        'PLAN_VALIDATION_FAILED',
        '제외한 재료 없이 안전한 식단을 만들지 못했어요. 재료를 조정해서 다시 시도해 주세요.',
        422
      )
    }
  }

  const { data: savedPlan, error: planError } = await supabase
    .from('meal_plans')
    .insert({
      user_id: user.id,
      title: plan.title || `${input.days}일 식단`,
      ingredients: input.ingredients,
      exclusions: input.exclusions,
      goal: input.goal,
      meals_per_day: input.mealsPerDay,
      summary: plan.summary,
      tips: plan.tips ?? [],
      total_meals: input.days * input.mealsPerDay,
    })
    .select('id')
    .single()

  if (planError || !savedPlan) {
    return errorResponse('SAVE_FAILED', '식단을 저장하지 못했어요.', 500)
  }

  const planId = savedPlan.id

  const { data: savedDays, error: daysError } = await supabase
    .from('meal_days')
    .insert(plan.days.map(day => ({
      plan_id: planId,
      day_index: day.dayIndex,
      tip: day.tip ?? null,
    })))
    .select('id, day_index')

  if (daysError || !savedDays) {
    return errorResponse('SAVE_FAILED', '식단을 저장하지 못했어요.', 500)
  }

  const dayIdByIndex = new Map(savedDays.map(d => [d.day_index, d.id]))

  const mealsPayload = plan.days.flatMap(day =>
    day.meals.map(meal => ({
      plan_id: planId,
      day_id: dayIdByIndex.get(day.dayIndex),
      user_id: user.id,
      slot: meal.slot,
      name: meal.name,
      used_ingredients: meal.usedIngredients,
      needed_ingredients: meal.neededIngredients,
      reason: meal.reason ?? null,
      tags: meal.tags ?? [],
    }))
  )

  const { error: mealsError } = await supabase.from('meals').insert(mealsPayload)
  if (mealsError) {
    return errorResponse('SAVE_FAILED', '식단을 저장하지 못했어요.', 500)
  }

  const uniqueShoppingItems = new Map<string, (typeof plan.shoppingItems)[number]>()
  for (const item of plan.shoppingItems) {
    if (!uniqueShoppingItems.has(item.name)) uniqueShoppingItems.set(item.name, item)
  }

  if (uniqueShoppingItems.size > 0) {
    const { error: shoppingError } = await supabase.from('shopping_items').insert(
      [...uniqueShoppingItems.values()].map((item, index) => ({
        plan_id: planId,
        user_id: user.id,
        name: item.name,
        category: item.category || '기타',
        priority: item.priority,
        reason: item.reason ?? null,
        sort_order: index,
      }))
    )
    if (shoppingError) {
      return errorResponse('SAVE_FAILED', '식단을 저장하지 못했어요.', 500)
    }
  }

  return Response.json({ ok: true, data: { id: planId } })
}
