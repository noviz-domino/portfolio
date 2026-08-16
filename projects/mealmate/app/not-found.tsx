import Link from 'next/link'
import Image from 'next/image'

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-surface px-6 py-20 text-center">
      <Image
        src="/brand/logo-mark.png"
        alt=""
        width={512}
        height={543}
        className="mb-6 h-20 w-auto opacity-80"
      />
      <p className="text-sm font-medium text-zinc-400">404</p>
      <h1 className="mt-2 text-2xl font-semibold text-zinc-900">페이지를 찾을 수 없어요</h1>
      <p className="mt-3 text-sm text-zinc-600">
        주소가 잘못되었거나, 비공개로 바뀐 식단일 수 있어요.
      </p>
      <Link
        href="/"
        className="btn btn-primary btn-md mt-8"
      >
        공개 식단 보러 가기
      </Link>
    </div>
  )
}
