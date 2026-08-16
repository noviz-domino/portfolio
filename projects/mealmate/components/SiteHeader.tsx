import Link from 'next/link'
import Image from 'next/image'
import { createClient } from '@/lib/supabase/server'
import { LogoutButton } from './LogoutButton'

export async function SiteHeader() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* 좁은 화면에서는 마크만 남긴다. 가로형 로고를 그대로 두면 오른쪽 메뉴와 자리를 다툰다. */}
        <Link href="/" aria-label="MealMate 홈" className="shrink-0">
          <Image
            src="/brand/logo-lockup.png"
            alt="MealMate"
            width={560}
            height={137}
            priority
            className="hidden h-7 w-auto sm:block"
          />
          <Image
            src="/brand/logo-mark.png"
            alt="MealMate"
            width={512}
            height={543}
            priority
            className="h-8 w-auto sm:hidden"
          />
        </Link>
        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <Link href="/plans/new" className="text-sm font-medium text-zinc-600 hover:text-zinc-900">
                식단 만들기
              </Link>
              <Link href="/plans" className="text-sm font-medium text-zinc-600 hover:text-zinc-900">
                내 식단
              </Link>
              <span className="hidden text-sm text-zinc-500 lg:inline">{user.email}</span>
              <LogoutButton />
            </>
          ) : (
            <Link
              href="/auth"
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900"
            >
              로그인
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
