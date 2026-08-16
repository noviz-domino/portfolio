'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

// F-12 공개/비공개 토글 + F-13 삭제.
// 소유자에게만 렌더링되며, 상세 페이지(server component)에서 isOwner일 때만 넣는다.
export function PlanOwnerControls({
  planId,
  initialIsPublic,
}: {
  planId: string
  initialIsPublic: boolean
}) {
  const router = useRouter()
  const [isPublic, setIsPublic] = useState(initialIsPublic)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function togglePublic() {
    const next = !isPublic
    setSaving(true)
    setError(null)
    setIsPublic(next) // 먼저 UI를 바꾸고, 실패하면 되돌린다

    try {
      const response = await fetch(`/api/plans/${planId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isPublic: next }),
      })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setIsPublic(!next)
        setError(result?.error?.message ?? '공개 설정을 바꾸지 못했어요.')
        return
      }
      router.refresh()
    } catch {
      setIsPublic(!next)
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setSaving(false)
    }
  }

  async function deletePlan() {
    if (!window.confirm('이 식단을 삭제할까요? 되돌릴 수 없어요.')) return

    setDeleting(true)
    setError(null)

    try {
      const response = await fetch(`/api/plans/${planId}`, { method: 'DELETE' })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setError(result?.error?.message ?? '식단을 삭제하지 못했어요.')
        return
      }
      router.push('/plans')
      router.refresh()
    } catch {
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="mb-6 flex flex-wrap items-center gap-2 rounded-2xl border bg-white p-3">
      <span className="mr-auto text-sm text-zinc-600">
        {isPublic ? '이 식단은 공개 중이에요.' : '이 식단은 나만 볼 수 있어요.'}
      </span>

      <button
        type="button"
        onClick={togglePublic}
        disabled={saving || deleting}
        className="btn btn-secondary px-4 py-2"
      >
        {saving ? '변경 중…' : isPublic ? '비공개로 전환' : '공개로 전환'}
      </button>

      <button
        type="button"
        onClick={deletePlan}
        disabled={saving || deleting}
        className="btn btn-danger px-4 py-2"
      >
        {deleting ? '삭제 중…' : '삭제'}
      </button>

      {error && <p className="w-full text-sm text-danger">{error}</p>}
    </div>
  )
}
