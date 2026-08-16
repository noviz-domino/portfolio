import Link from 'next/link'
import Image from 'next/image'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { MyPlanCard, type MyPlan } from '@/components/MyPlanCard'
import { SearchInput } from '@/components/SearchInput'

const GOAL_FILTERS = [
  { value: '', label: '전체' },
  { value: 'loss', label: '감량' },
  { value: 'maintain', label: '유지' },
  { value: 'bulk', label: '벌크업' },
  { value: 'balanced', label: '균형식' },
]

// F-09 내 식단 목록. 로그인 필수이고, 검색어(q)와 목표(goal)는 URL 쿼리로 관리한다.
// 쿼리로 두면 새로고침·뒤로가기에도 필터가 유지되고 별도 상태 관리가 필요 없다.
export default async function MyPlansPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; goal?: string }>
}) {
  const { q = '', goal = '' } = await searchParams
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth?next=/plans')

  let query = supabase
    .from('meal_plans')
    .select('id, title, goal, ingredients, summary, is_public, total_meals, done_meals, created_at')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })

  if (GOAL_FILTERS.some(filter => filter.value === goal && filter.value !== '')) {
    query = query.eq('goal', goal)
  }
  if (q.trim()) {
    // 제목에 검색어가 들어간 식단만 (ilike = 대소문자 구분 없는 부분 일치)
    query = query.ilike('title', `%${q.trim()}%`)
  }

  const { data: plans, error } = await query

  const hasFilter = Boolean(q.trim() || goal)

  return (
    <div className="flex flex-1 flex-col page-bg">
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-12">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-900">내 식단</h1>
            <p className="mt-1 text-sm text-zinc-500">내가 만든 주간 식단을 관리하세요.</p>
          </div>
          <Link
            href="/plans/new"
            className="btn btn-primary btn-md"
          >
            식단 만들기
          </Link>
        </div>

        <div className="mb-8 flex flex-wrap items-center gap-2">
          {GOAL_FILTERS.map(filter => {
            const params = new URLSearchParams()
            if (q.trim()) params.set('q', q.trim())
            if (filter.value) params.set('goal', filter.value)
            const href = params.toString() ? `/plans?${params.toString()}` : '/plans'
            const active = goal === filter.value

            return (
              <Link
                key={filter.label}
                href={href}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  active
                    ? 'bg-brand text-white'
                    : 'border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-100'
                }`}
              >
                {filter.label}
              </Link>
            )
          })}

          <form action="/plans" className="ml-auto flex items-center gap-2">
            {goal && <input type="hidden" name="goal" value={goal} />}
            <SearchInput defaultValue={q} placeholder="제목 검색" />
            <button
              type="submit"
              className="btn btn-secondary px-4 py-2"
            >
              검색
            </button>
          </form>
        </div>

        {error && (
          <p className="rounded-2xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger">
            식단을 불러오지 못했어요: {error.message}
          </p>
        )}

        {!error && plans?.length === 0 && (
          <div className="rounded-3xl border border-dashed bg-white/60 p-10 text-center">
            <Image
              src="/empty-plan.svg"
              alt=""
              width={240}
              height={180}
              className="mx-auto mb-4 h-auto w-[200px] sm:w-[240px]"
            />
            <p className="text-sm text-zinc-500">
              {hasFilter
                ? '조건에 맞는 식단이 없어요.'
                : '아직 만든 식단이 없어요. 냉장고 재료로 첫 식단을 만들어 보세요.'}
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Link
                href="/plans/new"
                className="btn btn-primary btn-md"
              >
                첫 식단 만들기
              </Link>
              <Link
                href="/"
                className="btn btn-secondary btn-md"
              >
                공개 식단 둘러보기
              </Link>
            </div>
          </div>
        )}

        {!error && plans && plans.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {plans.map(plan => (
              <MyPlanCard key={plan.id} plan={plan as MyPlan} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
