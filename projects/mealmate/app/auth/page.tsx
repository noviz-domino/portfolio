import Image from 'next/image'
import { AuthPanel } from '@/components/AuthPanel'

export default async function AuthPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const params = await searchParams
  return (
    <main className="auth-bg min-h-screen px-4 py-12">
      <div className="mx-auto mb-8 flex max-w-md flex-col items-center text-center">
        <h1 className="sr-only">MealMate</h1>
        {/* 로고 파일이 흰 배경을 갖고 있어, 크림색 배경 위에 그냥 두면 흰 사각형이 떠 보인다.
            흰 카드로 감싸서 그 사각형이 의도한 모양으로 읽히게 한다. */}
        <div className="rounded-2xl bg-white px-6 py-4 shadow-sm">
          <Image
            src="/brand/logo-lockup.png"
            alt="MealMate"
            width={560}
            height={137}
            priority
            className="h-11 w-auto"
          />
        </div>
        <p className="mt-3 text-zinc-600">로그인하면 내 냉장고 재료로 식단을 만들 수 있어요.</p>
      </div>
      <AuthPanel next={params.next || '/'} />
    </main>
  )
}