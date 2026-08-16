import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// F-11 장보기 체크
export async function PATCH(
  request: NextRequest,
  ctx: { params: Promise<{ id: string; itemId: string }> }
) {
  const { id, itemId } = await ctx.params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401)

  const body = await request.json().catch(() => null)
  if (!body || typeof body.isBought !== 'boolean') {
    return errorResponse('INVALID_BODY', '요청 형식이 올바르지 않습니다.', 400)
  }

  const { data: item, error } = await supabase
    .from('shopping_items')
    .update({ is_bought: body.isBought })
    .eq('id', itemId)
    .eq('plan_id', id)
    .eq('user_id', user.id)
    .select('id, is_bought')
    .single()

  if (error || !item) {
    return errorResponse('UPDATE_FAILED', '장보기 상태를 저장하지 못했어요.', 500)
  }

  return Response.json({ ok: true, data: item })
}
