'use client'

import { FormEvent, useState } from 'react'
import { createClient } from '@/lib/supabase/client'

export function SignupForm({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setMessage('')
    if (password.length < 8) {
      setMessage('비밀번호는 8자 이상 입력해 주세요.')
      return
    }
    setLoading(true)
    const supabase = createClient()
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback?next=/auth/confirmed`,
      },
    })
    setLoading(false)
    if (error) {
      setMessage(error.message.includes('already registered')
        ? '이미 가입된 이메일입니다. 로그인 탭을 이용해 주세요.'
        : error.message)
      return
    }
    setMessage('인증 메일을 보냈어요. 이메일 링크를 클릭한 뒤 로그인해 주세요.')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold text-zinc-900">회원가입</h2>
      <input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="이메일" className="w-full rounded-xl border p-3 text-zinc-900 placeholder:text-zinc-400" />
      <input required type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호 8자 이상" className="w-full rounded-xl border p-3 text-zinc-900 placeholder:text-zinc-400" />
      {message && <p className="rounded-lg bg-brand-50 p-3 text-sm text-brand-700">{message}</p>}
      <button disabled={loading} className="btn btn-primary btn-lg w-full">
        {loading ? '가입 처리 중...' : '회원가입'}
      </button>
      <button type="button" onClick={onLogin} className="w-full text-sm text-zinc-700 underline hover:text-zinc-900">이미 계정이 있나요? 로그인</button>
    </form>
  )
}