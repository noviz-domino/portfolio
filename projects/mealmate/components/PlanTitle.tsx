'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'

// 식단 제목. 소유자만 그 자리에서 고칠 수 있다.
// 기획서 9절의 PATCH /api/plans/[id] 가 이미 제목 변경을 받는다(1~60자 검증도 서버에 있음).
// 방문자에게는 편집 버튼을 아예 렌더링하지 않는다.
export function PlanTitle({
  planId,
  initialTitle,
  isOwner,
}: {
  planId: string
  initialTitle: string
  isOwner: boolean
}) {
  const router = useRouter()
  const [title, setTitle] = useState(initialTitle)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(initialTitle)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // 편집을 열면 바로 입력할 수 있게 커서를 넣고 기존 제목을 선택해 둔다
  useEffect(() => {
    if (editing) inputRef.current?.select()
  }, [editing])

  if (!isOwner) {
    return <h1 className="text-2xl font-semibold text-zinc-900">{title}</h1>
  }

  function startEdit() {
    setDraft(title)
    setError(null)
    setEditing(true)
  }

  function cancel() {
    setEditing(false)
    setError(null)
  }

  async function save() {
    const next = draft.trim()
    // 서버도 같은 규칙으로 검사하지만, 여기서 먼저 막아 헛된 요청을 줄인다
    if (next.length < 1 || next.length > 60) {
      setError('제목은 1자 이상 60자 이하로 입력해 주세요.')
      return
    }
    if (next === title) {
      setEditing(false)
      return
    }

    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`/api/plans/${planId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: next }),
      })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setError(result?.error?.message ?? '제목을 바꾸지 못했어요.')
        return
      }
      setTitle(result.data.title)
      setEditing(false)
      // 목록 등 다른 화면의 제목도 맞추기 위해 서버 데이터를 다시 받는다
      router.refresh()
    } catch {
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setSaving(false)
    }
  }

  if (!editing) {
    return (
      <span className="flex items-center gap-2">
        <h1 className="text-2xl font-semibold text-zinc-900">{title}</h1>
        <button
          type="button"
          onClick={startEdit}
          aria-label="식단 이름 바꾸기"
          title="식단 이름 바꾸기"
          className="rounded-full p-1.5 text-zinc-400 transition hover:bg-white hover:text-brand"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
          </svg>
        </button>
      </span>
    )
  }

  return (
    <span className="flex flex-wrap items-center gap-2">
      <input
        ref={inputRef}
        value={draft}
        maxLength={60}
        disabled={saving}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter') save()
          if (e.key === 'Escape') cancel()
        }}
        aria-label="식단 이름"
        className="w-full min-w-0 rounded-xl border border-zinc-300 bg-white px-3 py-1.5 text-xl font-semibold text-zinc-900 sm:w-80"
      />
      <button type="button" onClick={save} disabled={saving} className="btn btn-primary btn-sm">
        {saving ? '저장 중…' : '저장'}
      </button>
      <button type="button" onClick={cancel} disabled={saving} className="btn btn-secondary btn-sm">
        취소
      </button>
      {error && <p className="w-full text-sm text-danger">{error}</p>}
    </span>
  )
}
