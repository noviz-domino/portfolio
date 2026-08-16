import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// F-10 끼니 완료 토글
// meal_plans.done_meals는 DB 트리거(sync_done_meals)가 자동으로 다시 계산하므로
// 여기서는 meals.is_done만 바꾸고, 갱신된 실천율을 다시 읽어서 돌려준다.
export async function PATCH(request: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401)

  const body = await request.json().catch(() => null)
  if (!body || typeof body !== 'object') {
    return errorResponse('INVALID_BODY', '요청 형식이 올바르지 않습니다.', 400)
  }

  const mealId = typeof body.mealId === 'string' ? body.mealId : null
  const isDone = body.isDone

  if (!mealId) return errorResponse('INVALID_MEAL_ID', '끼니 id가 필요합니다.', 400)
  if (typeof isDone !== 'boolean') {
    return errorResponse('INVALID_IS_DONE', '완료 값이 올바르지 않습니다.', 400)
  }

  const { data: meal, error } = await supabase
    .from('meals')
    .update({ is_done: isDone })
    .eq('id', mealId)
    .eq('plan_id', id)
    .eq('user_id', user.id)
    .select('id, is_done')
    .single()

  if (error || !meal) {
    return errorResponse('UPDATE_FAILED', '완료 상태를 저장하지 못했어요.', 500)
  }

  const { data: plan } = await supabase
    .from('meal_plans')
    .select('done_meals, total_meals')
    .eq('id', id)
    .single()

  return Response.json({
    ok: true,
    data: {
      meal,
      doneMeals: plan?.done_meals ?? 0,
      totalMeals: plan?.total_meals ?? 0,
    },
  })
}
