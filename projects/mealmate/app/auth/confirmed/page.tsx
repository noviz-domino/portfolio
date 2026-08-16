export default function ConfirmedPage() {
  return (
    <main className="mx-auto max-w-lg px-6 py-20 text-center">
      <h1 className="text-2xl font-bold">이메일 인증이 완료됐어요</h1>
      <p className="mt-4 text-neutral-600">
        이제 MealMate 로그인 화면에서 로그인해 주세요.
      </p>
      <a className="btn btn-primary btn-lg mt-8" href="/auth">
        로그인하러 가기
      </a>
    </main>
  )
}