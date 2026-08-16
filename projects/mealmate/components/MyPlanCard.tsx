import Link from 'next/link'
import { goalBadgeClass, goalLabel } from '@/lib/goal'

export type MyPlan = {
  id: string
  title: string
  goal: string
  ingredients: string[]
  summary: string | null
  is_public: boolean
  total_meals: number
  done_meals: number
  created_at: string
}

// 내 식단 목록용 카드. 공개 홈의 PlanCard와 달리 공개 상태 badge와 실천율을 보여준다.
export function MyPlanCard({ plan }: { plan: MyPlan }) {
  const percent = plan.total_meals > 0 ? Math.round((plan.done_meals / plan.total_meals) * 100) : 0

  return (
    <Link
      href={`/plans/${plan.id}`}
      className="flex flex-col gap-3 rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:border-brand/40 hover:shadow-lg"
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="line-clamp-1 text-lg font-semibold text-zinc-900">{plan.title}</h3>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
            plan.is_public ? 'bg-brand-50 text-brand-700' : 'bg-zinc-200 text-zinc-700'
          }`}
        >
          {plan.is_public ? '공개' : '비공개'}
        </span>
      </div>

      <span className={`w-fit rounded-full px-3 py-1 text-xs font-medium ${goalBadgeClass(plan.goal)}`}>
        {goalLabel(plan.goal)}
      </span>

      {plan.summary && <p className="line-clamp-2 text-sm text-zinc-600">{plan.summary}</p>}

      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-zinc-500">
          <span>실천율</span>
          <span>
            {plan.done_meals} / {plan.total_meals}끼 · {percent}%
          </span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-zinc-100">
          <div className="h-full rounded-full bg-brand" style={{ width: `${percent}%` }} />
        </div>
      </div>

      <time className="mt-auto text-xs text-zinc-400">
        {new Date(plan.created_at).toLocaleDateString('ko-KR')}
      </time>
    </Link>
  )
}
