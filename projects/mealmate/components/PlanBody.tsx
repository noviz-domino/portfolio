'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const SLOT_LABEL: Record<string, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

const PRIORITY_LABEL: Record<string, string> = {
  required: '필수',
  recommended: '추천',
  optional: '선택',
}

const SLOT_ORDER = ['breakfast', 'lunch', 'dinner']

// 끼니별 색. 7일 21칸이 전부 같은 회색이라 훑어볼 때 아침·점심·저녁이 구분되지 않았다.
// 글자색과 점만 바꾸고 카드 배경은 그대로 둔다. 배경까지 칠하면 완료 표시와 헷갈린다.
const SLOT_TEXT: Record<string, string> = {
  breakfast: 'text-slot-breakfast',
  lunch: 'text-slot-lunch',
  dinner: 'text-slot-dinner',
}

const SLOT_DOT: Record<string, string> = {
  breakfast: 'bg-slot-breakfast-dot',
  lunch: 'bg-slot-lunch-dot',
  dinner: 'bg-slot-dinner-dot',
}

export type Recipe = {
  ingredients: string[]
  steps: string[]
  servings: string | null
  minutes: number | null
  tip: string | null
}

export type PlanMeal = {
  id: string
  slot: string
  name: string
  reason: string | null
  tags: string[]
  is_done: boolean
  used_ingredients: string[]
  needed_ingredients: string[]
  recipe_ingredients: string[]
  recipe_steps: string[]
  recipe_servings: string | null
  recipe_minutes: number | null
  recipe_tip: string | null
}

export type PlanDay = {
  id: string
  day_index: number
  tip: string | null
  meals: PlanMeal[]
}

export type ShoppingItem = {
  id: string
  name: string
  category: string
  priority: string
  reason: string | null
  is_bought: boolean
}

// 식단 본문(7일 끼니 + 장보기 목록).
// isOwner일 때만 체크박스(F-10, F-11)와 실천율을 보여준다. 방문자에게는 읽기 전용.
// 끼니 카드를 누르면 그 아래에 전체 폭 패널이 펼쳐지고 조리법(F-16)을 보여준다.
export function PlanBody({
  planId,
  isOwner,
  totalMeals,
  days,
  shoppingItems,
}: {
  planId: string
  isOwner: boolean
  totalMeals: number
  days: PlanDay[]
  shoppingItems: ShoppingItem[]
}) {
  const allMeals = days.flatMap(day => day.meals)

  const [mealDone, setMealDone] = useState<Record<string, boolean>>(
    () => Object.fromEntries(allMeals.map(meal => [meal.id, meal.is_done]))
  )
  const [bought, setBought] = useState<Record<string, boolean>>(
    () => Object.fromEntries(shoppingItems.map(item => [item.id, item.is_bought]))
  )
  // 이미 저장된 조리법은 처음부터 들고 시작한다. 없는 끼니만 펼칠 때 생성한다.
  const [recipes, setRecipes] = useState<Record<string, Recipe>>(() =>
    Object.fromEntries(
      allMeals
        .filter(meal => meal.recipe_steps?.length > 0)
        .map(meal => [
          meal.id,
          {
            ingredients: meal.recipe_ingredients,
            steps: meal.recipe_steps,
            servings: meal.recipe_servings,
            minutes: meal.recipe_minutes,
            tip: meal.recipe_tip,
          },
        ])
    )
  )
  const [expandedId, setExpandedId] = useState<string | null>(null)
  // 생성 중인 끼니는 여러 개일 수 있다. 하나만 기억하면 A가 만들어지는 동안 B를 누를 때
  // A의 진행 상태가 지워져서, A를 다시 누르면 중복으로 생성 요청이 나간다.
  const [generating, setGenerating] = useState<Record<string, boolean>>({})
  const [recipeError, setRecipeError] = useState<Record<string, string>>({})
  const [pending, setPending] = useState<Record<string, boolean>>({})
  const [error, setError] = useState<string | null>(null)
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const router = useRouter()

  const doneCount = Object.values(mealDone).filter(Boolean).length
  const total = totalMeals || allMeals.length
  const percent = total > 0 ? Math.round((doneCount / total) * 100) : 0

  // 펼치기와 생성을 나눠 둔다. 붙여 두면 "다시 시도"가 재생성 대신 접기로 빠진다.
  // (setExpandedId는 즉시 반영되지 않아서, 이어서 부른 toggleExpand가 아직 펼쳐진
  //  상태를 보고 접기 분기로 들어갔다.)
  async function generateRecipe(meal: PlanMeal) {
    // 저장된 조리법이 있거나, 이미 만들고 있는 중이면 새로 부르지 않는다
    if (recipes[meal.id] || generating[meal.id]) return
    // 방문자는 생성할 수 없다. 소유자가 만들어 둔 것만 볼 수 있다.
    if (!isOwner) return

    setGenerating(prev => ({ ...prev, [meal.id]: true }))
    setRecipeError(prev => ({ ...prev, [meal.id]: '' }))

    try {
      const response = await fetch(`/api/plans/${planId}/meals/${meal.id}/recipe`, { method: 'POST' })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setRecipeError(prev => ({
          ...prev,
          [meal.id]: result?.error?.message ?? '조리법을 만들지 못했어요.',
        }))
        return
      }
      setRecipes(prev => ({ ...prev, [meal.id]: result.data }))
    } catch {
      setRecipeError(prev => ({ ...prev, [meal.id]: '네트워크 오류가 발생했어요.' }))
    } finally {
      // 끝난 끼니만 내린다. null로 통째로 비우면 아직 만들고 있는 다른 끼니의
      // 로딩 표시까지 같이 꺼져서 빈 패널이 보인다.
      setGenerating(prev => ({ ...prev, [meal.id]: false }))
    }
  }

  function toggleExpand(meal: PlanMeal) {
    if (expandedId === meal.id) {
      setExpandedId(null)
      return
    }
    setExpandedId(meal.id)
    generateRecipe(meal)
  }

  // F-15 이 끼니만 새 메뉴로 바꾼다.
  async function regenerateMeal(meal: PlanMeal) {
    if (!isOwner || regeneratingId) return
    if (!window.confirm(`"${meal.name}"을(를) 다른 메뉴로 바꿀까요? 저장된 조리법과 완료 체크도 함께 지워져요.`)) {
      return
    }

    setRegeneratingId(meal.id)
    setError(null)
    setNotice(null)

    try {
      const response = await fetch(`/api/plans/${planId}/meals/${meal.id}/regenerate`, { method: 'POST' })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setError(result?.error?.message ?? '새 메뉴를 만들지 못했어요.')
        return
      }

      // 서버에서 지운 값들을 화면 상태에서도 맞춰 준다.
      // 이 값들은 useState 초기값이라 router.refresh()만으로는 갱신되지 않는다.
      setRecipes(prev => {
        const next = { ...prev }
        delete next[meal.id]
        return next
      })
      setMealDone(prev => ({ ...prev, [meal.id]: false }))
      setRecipeError(prev => ({ ...prev, [meal.id]: '' }))
      setExpandedId(null)
      setNotice(
        `"${meal.name}" → "${result.data.name}"으로 바꿨어요. 장보기 목록은 그대로예요. 새로 필요한 재료가 있는지 확인해 주세요.`
      )
      router.refresh()
    } catch {
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setRegeneratingId(null)
    }
  }

  async function toggleMeal(mealId: string) {
    if (!isOwner || pending[mealId]) return
    const next = !mealDone[mealId]

    setPending(prev => ({ ...prev, [mealId]: true }))
    setMealDone(prev => ({ ...prev, [mealId]: next }))
    setError(null)

    try {
      const response = await fetch(`/api/plans/${planId}/meals`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mealId, isDone: next }),
      })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setMealDone(prev => ({ ...prev, [mealId]: !next }))
        setError(result?.error?.message ?? '완료 상태를 저장하지 못했어요.')
      }
    } catch {
      setMealDone(prev => ({ ...prev, [mealId]: !next }))
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setPending(prev => ({ ...prev, [mealId]: false }))
    }
  }

  async function toggleItem(itemId: string) {
    if (!isOwner || pending[itemId]) return
    const next = !bought[itemId]

    setPending(prev => ({ ...prev, [itemId]: true }))
    setBought(prev => ({ ...prev, [itemId]: next }))
    setError(null)

    try {
      const response = await fetch(`/api/plans/${planId}/shopping/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isBought: next }),
      })
      const result = await response.json()
      if (!response.ok || !result.ok) {
        setBought(prev => ({ ...prev, [itemId]: !next }))
        setError(result?.error?.message ?? '장보기 상태를 저장하지 못했어요.')
      }
    } catch {
      setBought(prev => ({ ...prev, [itemId]: !next }))
      setError('네트워크 오류가 발생했어요.')
    } finally {
      setPending(prev => ({ ...prev, [itemId]: false }))
    }
  }

  function renderRecipePanel(meal: PlanMeal) {
    const recipe = recipes[meal.id]
    const isGenerating = generating[meal.id]
    const message = recipeError[meal.id]
    const shoppingNeeded = meal.needed_ingredients ?? []
    const athome = meal.used_ingredients ?? []

    return (
      <div className="col-span-full rounded-2xl border border-zinc-200 bg-white p-4 sm:p-5">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <h3 className="text-base font-semibold text-zinc-900">{meal.name}</h3>
          {recipe?.servings && (
            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-600">
              {recipe.servings}
            </span>
          )}
          {recipe?.minutes ? (
            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-600">
              약 {recipe.minutes}분
            </span>
          ) : null}
          {isOwner && (
            <button
              type="button"
              onClick={() => regenerateMeal(meal)}
              disabled={regeneratingId === meal.id}
              className="btn btn-secondary btn-sm ml-auto"
            >
              {regeneratingId === meal.id ? '바꾸는 중…' : '다른 메뉴로'}
            </button>
          )}
          <button
            type="button"
            onClick={() => setExpandedId(null)}
            className={`text-xs text-zinc-400 hover:text-zinc-700 ${isOwner ? '' : 'ml-auto'}`}
          >
            접기
          </button>
        </div>

        {/* 재료 분류는 조리법 생성 없이도 바로 보여줄 수 있다 (식단 생성 때 이미 저장된 값) */}
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-zinc-50 p-3">
            <p className="mb-1.5 text-xs font-medium text-zinc-500">집에 있는 재료</p>
            <p className="text-sm text-zinc-800">{athome.length > 0 ? athome.join(', ') : '없음'}</p>
          </div>
          <div className="rounded-xl bg-zinc-50 p-3">
            <p className="mb-1.5 text-xs font-medium text-zinc-500">사와야 하는 재료</p>
            <p className="text-sm text-zinc-800">
              {shoppingNeeded.length > 0 ? shoppingNeeded.join(', ') : '없음'}
            </p>
          </div>
        </div>

        {isGenerating && (
          <p className="rounded-xl bg-zinc-50 p-4 text-sm text-zinc-500">
            조리법을 만드는 중이에요… 10초쯤 걸려요.
          </p>
        )}

        {!isGenerating && message && (
          <div className="rounded-xl border border-danger-200 bg-danger-50 p-3 text-sm text-danger">
            <p>{message}</p>
            <button
              type="button"
              onClick={() => generateRecipe(meal)}
              className="btn btn-danger btn-sm mt-2"
            >
              다시 시도
            </button>
          </div>
        )}

        {!isGenerating && !message && !recipe && !isOwner && (
          <p className="rounded-xl bg-zinc-50 p-4 text-sm text-zinc-500">
            아직 조리법이 준비되지 않은 메뉴예요.
          </p>
        )}

        {!isGenerating && recipe && (
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[260px_1fr]">
            <div>
              <p className="mb-2 text-sm font-semibold text-zinc-900">재료</p>
              <ul className="flex flex-col gap-1">
                {recipe.ingredients.map(item => (
                  <li key={item} className="text-sm text-zinc-700">
                    · {item}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold text-zinc-900">만드는 법</p>
              <ol className="flex flex-col gap-2.5">
                {recipe.steps.map((step, index) => (
                  <li key={step} className="flex gap-2.5 text-sm text-zinc-700">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-medium text-white">
                      {index + 1}
                    </span>
                    <span className="pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>

              {recipe.tip && (
                <p className="mt-3 rounded-xl bg-accent-50 p-3 text-sm text-accent-900">
                  팁 · {recipe.tip}
                </p>
              )}
            </div>
          </div>
        )}

        <p className="mt-4 text-xs text-zinc-400">
          AI가 만든 참고용 조리법이에요. 실제 조리 시 재료 상태와 알레르기를 직접 확인해 주세요.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
      <div>
        {error && (
          <p className="mb-4 rounded-2xl border border-danger-200 bg-danger-50 p-3 text-sm text-danger">
            {error}
          </p>
        )}

        {notice && (
          <div className="mb-4 flex items-start gap-3 rounded-2xl border border-accent-200 bg-accent-50 p-3 text-sm text-accent-900">
            <p className="flex-1">{notice}</p>
            <button
              type="button"
              onClick={() => setNotice(null)}
              className="shrink-0 text-xs text-accent-900/70 hover:text-accent-900"
            >
              닫기
            </button>
          </div>
        )}

        {isOwner && (
          <div className="mb-6 rounded-2xl border bg-white p-4">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-medium text-zinc-900">실천율</span>
              <span className="text-zinc-500">
                {doneCount} / {total}끼 · {percent}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-brand transition-all"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-6">
          {days.map(day => {
            const sortedMeals = [...day.meals].sort(
              (a, b) => SLOT_ORDER.indexOf(a.slot) - SLOT_ORDER.indexOf(b.slot)
            )
            const expandedMeal = sortedMeals.find(meal => meal.id === expandedId)

            return (
              <section key={day.id} className="rounded-3xl border bg-white p-5">
                <h2 className="mb-3 text-base font-semibold text-zinc-900">Day {day.day_index}</h2>
                {day.tip && <p className="mb-3 text-sm text-zinc-500">{day.tip}</p>}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {sortedMeals.map(meal => {
                    const done = mealDone[meal.id]
                    const open = expandedId === meal.id
                    return (
                      <div
                        key={meal.id}
                        className={`relative rounded-2xl p-3.5 transition ${
                          open
                            ? 'bg-white ring-2 ring-brand'
                            : done
                              ? 'bg-brand-50 ring-1 ring-brand/15'
                              : 'bg-surface'
                        }`}
                      >
                        {isOwner && (
                          <label className="absolute right-3.5 top-3.5 z-10 flex cursor-pointer items-center gap-1 text-xs text-zinc-500">
                            <input
                              type="checkbox"
                              checked={done}
                              disabled={pending[meal.id]}
                              onChange={() => toggleMeal(meal.id)}
                              className="h-4 w-4 accent-brand"
                            />
                            완료
                          </label>
                        )}

                        <button
                          type="button"
                          onClick={() => toggleExpand(meal)}
                          aria-expanded={open}
                          className="w-full text-left"
                        >
                          <p
                            className={`mb-1 flex items-center gap-1.5 text-xs font-semibold ${
                              SLOT_TEXT[meal.slot] ?? 'text-zinc-400'
                            }`}
                          >
                            <span
                              className={`h-1.5 w-1.5 rounded-full ${SLOT_DOT[meal.slot] ?? 'bg-zinc-300'}`}
                            />
                            {SLOT_LABEL[meal.slot] ?? meal.slot}
                          </p>
                          <p
                            className={`mb-2 pr-12 text-sm font-semibold ${done ? 'text-zinc-400 line-through' : 'text-zinc-900'}`}
                          >
                            {meal.name}
                          </p>
                          {meal.reason && <p className="mb-2 text-xs text-zinc-500">{meal.reason}</p>}
                          <div className="mb-2 flex flex-wrap gap-1">
                            {(meal.tags ?? []).map(tag => (
                              <span
                                key={tag}
                                className="rounded-full bg-white px-2 py-0.5 text-xs text-zinc-500 ring-1 ring-zinc-200"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                          <span className="text-xs font-medium text-zinc-500 underline">
                            {open ? '접기' : '조리법 보기'}
                          </span>
                        </button>
                      </div>
                    )
                  })}

                  {expandedMeal && renderRecipePanel(expandedMeal)}
                </div>
              </section>
            )
          })}
        </div>
      </div>

      <aside className="h-fit rounded-3xl border bg-white p-5 lg:sticky lg:top-6">
        <h2 className="mb-4 text-base font-semibold text-zinc-900">장보기 목록</h2>
        <div className="flex flex-col gap-2">
          {shoppingItems.map(item => {
            const checked = bought[item.id]
            return (
              <label
                key={item.id}
                className={`flex items-start justify-between gap-2 border-b pb-2 text-sm last:border-0 ${isOwner ? 'cursor-pointer' : ''}`}
              >
                <div className="flex items-start gap-2">
                  {isOwner && (
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={pending[item.id]}
                      onChange={() => toggleItem(item.id)}
                      className="mt-0.5 h-4 w-4 shrink-0 accent-brand"
                    />
                  )}
                  <div>
                    <p className={checked && isOwner ? 'text-zinc-400 line-through' : 'text-zinc-800'}>
                      {item.name}
                    </p>
                    {item.reason && <p className="text-xs text-zinc-400">{item.reason}</p>}
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                  {PRIORITY_LABEL[item.priority] ?? item.priority}
                </span>
              </label>
            )
          })}
          {shoppingItems.length === 0 && (
            <p className="text-sm text-zinc-400">장보기 항목이 없어요.</p>
          )}
        </div>
      </aside>
    </div>
  )
}
