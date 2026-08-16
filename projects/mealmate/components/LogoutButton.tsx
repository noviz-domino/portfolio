'use client'

import { createClient } from '@/lib/supabase/client'

export function LogoutButton() {
  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    window.location.href = '/'
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="text-sm font-medium text-zinc-600 hover:text-zinc-900"
    >
      로그아웃
    </button>
  )
}
