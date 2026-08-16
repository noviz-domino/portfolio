'use client'

import { FormEvent, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export function LoginForm({ onSignup, next = '/' }: { onSignup: () => void; next?: string }) {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setMessage('')
    setLoading(true)
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      setMessage(error.message.includes('Email not confirmed')
        ? '이메일 인증 링크를 먼저 클릭해 주세요.'
        : '이메일 또는 비밀번호를 확인해 주세요.')
      return
    }
    router.push(next)
    router.refresh()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold text-zinc-900">로그인</h2>
      <input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="이메일" className="w-full rounded-xl border p-3 text-zinc-900 placeholder:text-zinc-400" />
      <input required type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호" className="w-full rounded-xl border p-3 text-zinc-900 placeholder:text-zinc-400" />
      {message && <p className="rounded-lg bg-danger-50 p-3 text-sm text-danger">{message}</p>}
      <button disabled={loading} className="btn btn-primary btn-lg w-full">
        {loading ? '로그인 중...' : '로그인'}
      </button>
      <button type="button" onClick={onSignup} className="w-full text-sm text-zinc-700 underline hover:text-zinc-900">계정이 없나요? 회원가입</button>
    </form>
  )
}