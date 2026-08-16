import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { PlanOwnerControls } from '@/components/PlanOwnerControls'
import { PlanBody, type PlanDay, type ShoppingItem } from '@/components/PlanBody'
import { CopyPlanButton } from '@/components/CopyPlanButton'
import { PlanTitle } from '@/components/PlanTitle'
import { buildPlanMarkdown } from '@/lib/planMarkdown'
import { goalBadgeClass, goalLabel } from '@/lib/goal'

export default async function PlanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()

  // 비공개 식단은 RLS(plans_public_select)가 소유자에게만 내려준다.
  // 남의 비공개 식단이면 여기서 plan이 null이 되어 404로 표시된다.
  const { data: plan } = await supabase
    .from('meal_plans')
    .select('id, user_id, title, goal, meals_per_day, summary, tips, is_public, total_meals, created_at')
    .eq('id', id)
    .single()

  if (!plan) notFound()

  const isOwner = !!user && user.id === plan.user_id

  const { data: days } = await supabase
    .from('meal_days')
    .select(
      'id, day_index, tip, meals(id, slot, name, reason, tags, is_done, used_ingredients, needed_ingredients, recipe_ingredients, recipe_steps, recipe_servings, recipe_minutes, recipe_tip)'
    )
    .eq('plan_id', id)
    .order('day_index', { ascending: true })

  const { data: shoppingItems } = await supabase
    .from('shopping_items')
    .select('id, name, category, priority, reason, is_bought')
    .eq('plan_id', id)
    .order('sort_order', { ascending: true })

  const markdown = buildPlanMarkdown({
    title: plan.title,
    goal: plan.goal,
    mealsPerDay: plan.meals_per_day,
    summary: plan.summary,
    tips: plan.tips ?? [],
    days: (days ?? []) as PlanDay[],
    shoppingItems: (shoppingItems ?? []) as ShoppingItem[],
  })

  return (
    <div className="flex flex-1 flex-col page-bg">
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <PlanTitle planId={plan.id} initialTitle={plan.title} isOwner={isOwner} />
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${goalBadgeClass(plan.goal)}`}>
            {goalLabel(plan.goal)}
          </span>
          <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700">
            하루 {plan.meals_per_day}끼
          </span>
          {isOwner && (
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                plan.is_public ? 'bg-brand-50 text-brand-700' : 'bg-zinc-200 text-zinc-700'
              }`}
            >
              {plan.is_public ? '공개' : '비공개'}
            </span>
          )}
          <span className="ml-auto">
            <CopyPlanButton markdown={markdown} />
          </span>
        </div>

        {plan.summary && <p className="mb-6 text-sm text-zinc-600">{plan.summary}</p>}

        {isOwner && <PlanOwnerControls planId={plan.id} initialIsPublic={plan.is_public} />}

        {plan.tips?.length > 0 && (
          <ul className="mb-8 flex flex-col gap-1.5 rounded-2xl border bg-white p-4 text-sm text-zinc-600">
            {plan.tips.map((tip: string) => (
              <li key={tip}>· {tip}</li>
            ))}
          </ul>
        )}

        <PlanBody
          planId={plan.id}
          isOwner={isOwner}
          totalMeals={plan.total_meals}
          days={(days ?? []) as PlanDay[]}
          shoppingItems={(shoppingItems ?? []) as ShoppingItem[]}
        />
      </main>
    </div>
  )
}
