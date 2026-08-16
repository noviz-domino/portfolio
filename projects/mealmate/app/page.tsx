import Link from 'next/link'
import Image from 'next/image'
import { createClient } from '@/lib/supabase/server'
import { PlanCard, type Plan } from '@/components/PlanCard'
import { SearchInput } from '@/components/SearchInput'

const GOAL_FILTERS = [
  { value: '', label: '전체' },
  { value: 'loss', label: '감량' },
  { value: 'maintain', label: '유지' },
  { value: 'bulk', label: '벌크업' },
  { value: 'balanced', label: '균형식' },
]

// Supabase의 or() 필터는 쉼표·괄호로 조건을 구분한다.
// 검색어에 그 문자가 들어가면 필터 문법이 깨지므로 미리 제거한다.
function sanitize(term: string) {
  return term.replace(/[,()\\%]/g, '').trim().slice(0, 30)
}

// 필터 chip 링크를 만들 때 지금 켜져 있는 다른 필터를 유지한다.
function buildHref(current: { q: string; goal: string; tag: string }, patch: Partial<{ q: string; goal: string; tag: string }>) {
  const next = { ...current, ...patch }
  const params = new URLSearchParams()
  if (next.q) params.set('q', next.q)
  if (next.goal) params.set('goal', next.goal)
  if (next.tag) params.set('tag', next.tag)
  return params.toString() ? `/?${params.toString()}` : '/'
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; goal?: string; tag?: string }>
}) {
  const raw = await searchParams
  const q = sanitize(raw.q ?? '')
  const goal = GOAL_FILTERS.some(f => f.value === raw.goal && f.value) ? raw.goal! : ''
  const tag = sanitize(raw.tag ?? '')
  const current = { q, goal, tag }

  const supabase = await createClient()

  // 태그 chip 목록: 공개 식단에 실제로 등장한 태그를 세어 상위 6개만 노출한다.
  // (meals의 RLS가 공개 식단만 내려주므로 비공개 식단의 태그는 섞이지 않는다)
  const { data: tagRows } = await supabase.from('meals').select('tags').limit(500)
  const tagCount = new Map<string, number>()
  for (const row of tagRows ?? []) {
    for (const t of (row.tags ?? []) as string[]) {
      tagCount.set(t, (tagCount.get(t) ?? 0) + 1)
    }
  }
  const topTags = [...tagCount.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name]) => name)

  // 태그 필터는 meals 테이블에 있으므로, 해당 태그를 가진 끼니의 plan_id를 먼저 모은다.
  let planIdsForTag: string[] | null = null
  if (tag) {
    const { data: tagged } = await supabase.from('meals').select('plan_id').contains('tags', [tag])
    planIdsForTag = [...new Set((tagged ?? []).map(row => row.plan_id as string))]
  }

  let query = supabase
    .from('meal_plans')
    .select('id, title, goal, ingredients, summary, created_at, user_id', { count: 'exact' })
    .eq('is_public', true)
    .order('created_at', { ascending: false })
    .limit(24)

  if (goal) query = query.eq('goal', goal)
  if (q) query = query.or(`title.ilike.%${q}%,summary.ilike.%${q}%,ingredients.cs.{${q}}`)
  if (planIdsForTag) {
    // 태그에 맞는 식단이 하나도 없으면 빈 결과가 되도록 존재할 수 없는 값을 넣는다
    query = query.in('id', planIdsForTag.length > 0 ? planIdsForTag : ['00000000-0000-0000-0000-000000000000'])
  }

  const { data: plans, error, count } = await query

  const hasFilter = Boolean(q || goal || tag)

  return (
    <div className="flex flex-1 flex-col page-bg">
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-12">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-900">공개 식단</h1>
            {/* 처음 온 사람이 이 서비스가 뭘 하는지 알 수 있어야 해서, 핵심인 "냉장고 재료"를 먼저 적는다. */}
            <p className="mt-1 max-w-xl text-sm text-zinc-500">
              냉장고에 남은 재료를 적으면 AI가 식단과 장보기 목록을 만들어 줘요.
              먼저 다른 사람들의 식단을 둘러보세요.
            </p>
          </div>
          <Link
            href="/plans/new"
            className="btn btn-primary btn-md"
          >
            식단 만들기
          </Link>
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          {GOAL_FILTERS.map(filter => {
            const active = goal === filter.value
            return (
              <Link
                key={filter.label}
                href={buildHref(current, { goal: filter.value })}
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

          <form action="/" className="ml-auto flex items-center gap-2">
            {goal && <input type="hidden" name="goal" value={goal} />}
            {tag && <input type="hidden" name="tag" value={tag} />}
            <SearchInput defaultValue={q} placeholder="재료·제목 검색" />
            <button
              type="submit"
              className="btn btn-secondary px-4 py-2"
            >
              검색
            </button>
          </form>
        </div>

        {topTags.length > 0 && (
          <div className="mb-8 flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs text-zinc-400">태그</span>
            {topTags.map(name => {
              const active = tag === name
              return (
                <Link
                  key={name}
                  href={buildHref(current, { tag: active ? '' : name })}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                    active
                      ? 'bg-brand text-white'
                      : 'bg-white text-zinc-600 ring-1 ring-zinc-200 hover:bg-zinc-100'
                  }`}
                >
                  #{name}
                </Link>
              )
            })}
          </div>
        )}

        {!error && (
          <p className="mb-4 text-sm text-zinc-500">
            공개 식단 <span className="font-medium text-zinc-900">{count ?? 0}</span>개
            {hasFilter && (
              <>
                {' · '}
                <Link href="/" className="text-zinc-500 underline hover:text-zinc-900">
                  필터 초기화
                </Link>
              </>
            )}
          </p>
        )}

        {error && (
          <p className="rounded-2xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger">
            식단을 불러오지 못했어요: {error.message}
          </p>
        )}

        {!error && plans?.length === 0 && (
          <div className="rounded-2xl border border-dashed bg-white/60 p-10 text-center">
            <Image
              src="/empty-plan.svg"
              alt=""
              width={240}
              height={180}
              className="mx-auto mb-4 h-auto w-[200px] sm:w-[240px]"
            />
            <p className="text-sm text-zinc-500">
              {hasFilter
                ? '조건에 맞는 공개 식단이 없어요. 필터를 바꿔 보세요.'
                : '아직 공개된 식단이 없어요. 첫 번째 식단을 만들어 보세요.'}
            </p>
          </div>
        )}

        {!error && plans && plans.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {plans.map(plan => (
              <PlanCard key={plan.id} plan={plan as Plan} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
