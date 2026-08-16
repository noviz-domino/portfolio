import Link from 'next/link'
import { goalBadgeClass, goalLabel } from '@/lib/goal'

export type Plan = {
  id: string
  title: string
  goal: string
  ingredients: string[]
  summary: string | null
  created_at: string
  user_id: string
}

export function PlanCard({ plan }: { plan: Plan }) {
  const visibleIngredients = plan.ingredients.slice(0, 4)
  const remaining = plan.ingredients.length - visibleIngredients.length

  return (
    <Link
      href={`/plans/${plan.id}`}
      className="flex flex-col gap-3 rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:border-brand/40 hover:shadow-lg"
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="line-clamp-1 text-lg font-semibold">{plan.title}</h3>
        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${goalBadgeClass(plan.goal)}`}>
          {goalLabel(plan.goal)}
        </span>
      </div>

      {plan.summary && (
        <p className="line-clamp-2 text-sm text-zinc-600">{plan.summary}</p>
      )}

      <div className="flex flex-wrap gap-1.5">
        {visibleIngredients.map(ingredient => (
          <span
            key={ingredient}
            className="rounded-full bg-zinc-50 px-2.5 py-1 text-xs text-zinc-600 ring-1 ring-zinc-200"
          >
            {ingredient}
          </span>
        ))}
        {remaining > 0 && (
          <span className="rounded-full bg-zinc-50 px-2.5 py-1 text-xs text-zinc-400 ring-1 ring-zinc-200">
            +{remaining}
          </span>
        )}
      </div>

      <time className="mt-auto text-xs text-zinc-400">
        {new Date(plan.created_at).toLocaleDateString('ko-KR')}
      </time>
    </Link>
  )
}
