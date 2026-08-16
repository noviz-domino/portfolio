import { NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'

function errorResponse(code: string, message: string, status: number) {
  return Response.json({ ok: false, error: { code, message } }, { status })
}

// 소유자 확인: 로그인한 사용자가 이 식단의 주인인지 검사한다.
// RLS가 1차 방어선이지만, 라우트에서도 명시적으로 확인해 404/403을 정확히 돌려준다.
async function requireOwner(planId: string) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { error: errorResponse('AUTH_REQUIRED', '로그인이 필요합니다.', 401) }

  const { data: plan } = await supabase
    .from('meal_plans')
    .select('id, user_id')
    .eq('id', planId)
    .single()

  if (!plan) return { error: errorResponse('NOT_FOUND', '식단을 찾을 수 없습니다.', 404) }
  if (plan.user_id !== user.id) {
    return { error: errorResponse('FORBIDDEN', '본인 식단만 수정할 수 있습니다.', 403) }
  }

  return { supabase, user }
}

// F-12 공개/비공개 토글, 제목 변경
export async function PATCH(request: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const owner = await requireOwner(id)
  if (owner.error) return owner.error

  const body = await request.json().catch(() => null)
  if (!body || typeof body !== 'object') {
    return errorResponse('INVALID_BODY', '요청 형식이 올바르지 않습니다.', 400)
  }

  const patch: { is_public?: boolean; title?: string } = {}

  if ('isPublic' in body) {
    if (typeof body.isPublic !== 'boolean') {
      return errorResponse('INVALID_IS_PUBLIC', '공개 여부 값이 올바르지 않습니다.', 400)
    }
    patch.is_public = body.isPublic
  }

  if ('title' in body) {
    const title = typeof body.title === 'string' ? body.title.trim() : ''
    if (title.length < 1 || title.length > 60) {
      return errorResponse('INVALID_TITLE', '제목은 1자 이상 60자 이하로 입력해 주세요.', 400)
    }
    patch.title = title
  }

  if (Object.keys(patch).length === 0) {
    return errorResponse('NOTHING_TO_UPDATE', '변경할 값이 없습니다.', 400)
  }

  const { data, error } = await owner.supabase
    .from('meal_plans')
    .update(patch)
    .eq('id', id)
    .select('id, title, is_public')
    .single()

  if (error || !data) {
    return errorResponse('UPDATE_FAILED', '식단을 수정하지 못했어요.', 500)
  }

  return Response.json({ ok: true, data })
}

// F-13 식단 삭제 (하위 테이블은 on delete cascade로 함께 삭제됨)
export async function DELETE(_request: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const owner = await requireOwner(id)
  if (owner.error) return owner.error

  const { error } = await owner.supabase.from('meal_plans').delete().eq('id', id)
  if (error) {
    return errorResponse('DELETE_FAILED', '식단을 삭제하지 못했어요.', 500)
  }

  return Response.json({ ok: true, data: { id } })
}
