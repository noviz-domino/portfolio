'use client'

import { useState } from 'react'
import { LoginForm } from './LoginForm'
import { SignupForm } from './SignupForm'

export function AuthPanel({ next = '/' }: { next?: string }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  return (
    <section className="mx-auto max-w-md rounded-3xl border bg-white p-6 shadow-sm">
      {mode === 'login'
        ? <LoginForm key="login" next={next} onSignup={() => setMode('signup')} />
        : <SignupForm key="signup" onLogin={() => setMode('login')} />}
    </section>
  )
}