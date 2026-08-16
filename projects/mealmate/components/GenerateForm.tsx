'use client'

import { useState, type KeyboardEvent } from 'react'
import { DEFAULT_PLAN_DAYS, PLAN_DAYS, type PlanDays } from '@/lib/mealPlan'

const GOAL_OPTIONS = [
  { value: 'balanced', label: '균형 식단' },
  { value: 'loss', label: '체중 감량' },
  { value: 'maintain', label: '체중 유지' },
  { value: 'bulk', label: '벌크업' },
]

function TagInput({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string
  placeholder: string
  values: string[]
  onChange: (values: string[]) => void
}) {
  const [draft, setDraft] = useState('')

  function commit() {
    const value = draft.trim()
    if (value && !values.includes(value)) {
      onChange([...values, value])
    }
    setDraft('')
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      commit()
    }
  }

  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-zinc-700">{label}</label>
      <input
        type="text"
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={commit}
        placeholder={placeholder}
        className="w-full rounded-xl border px-3.5 py-2.5 text-sm outline-none focus:border-zinc-400"
      />
      {values.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {values.map(value => (
            <span
              key={value}
              className="flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700"
            >
              {value}
              <button
                type="button"
                onClick={() => onChange(values.filter(v => v !== value))}
                className="text-zinc-400 hover:text-zinc-700"
                aria-label={`${value} 삭제`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function GenerateForm() {
  const [ingredients, setIngredients] = useState<string[]>([])
  const [exclusions, setExclusions] = useState<string[]>([])
  const [goal, setGoal] = useState('balanced')
  const [mealsPerDay, setMealsPerDay] = useState<2 | 3>(2)
  const [days, setDays] = useState<PlanDays>(DEFAULT_PLAN_DAYS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (ingredients.length < 3) {
      setError('재료를 최소 3개 입력해 주세요.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredients, exclusions, goal, mealsPerDay, days }),
      })
      const result = await response.json()
      if (!response.ok) {
        setError(result.error?.message || '생성에 실패했어요.')
        return
      }
      window.location.href = `/plans/${result.data.id}`
    } catch {
      setError('생성 중 오류가 발생했어요. 다시 시도해 주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="mx-auto max-w-xl rounded-3xl border bg-white p-6 shadow-sm">
      <h1 className="mb-1 text-xl font-semibold text-zinc-900">새 식단 만들기</h1>
      <p className="mb-6 text-sm text-zinc-500">
        가지고 있는 재료를 알려주면 AI가 식단과 장보기 목록을 만들어드려요.
      </p>

      <div className="flex flex-col gap-5">
        <TagInput
          label="재료 (최소 3개)"
          placeholder="예: 닭가슴살 입력 후 Enter"
          values={ingredients}
          onChange={setIngredients}
        />

        <TagInput
          label="제외할 재료 (선택)"
          placeholder="예: 땅콩 입력 후 Enter"
          values={exclusions}
          onChange={setExclusions}
        />

        <div>
          <label className="mb-1.5 block text-sm font-medium text-zinc-700">목표</label>
          <select
            value={goal}
            onChange={e => setGoal(e.target.value)}
            className="w-full rounded-xl border px-3.5 py-2.5 text-sm outline-none focus:border-zinc-400"
          >
            {GOAL_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-zinc-700">며칠치</label>
          <div className="flex gap-2">
            {PLAN_DAYS.map(count => (
              <button
                key={count}
                type="button"
                onClick={() => setDays(count)}
                className={`flex-1 rounded-xl border px-3.5 py-2.5 text-sm font-medium transition ${
                  days === count
                    ? 'border-brand bg-brand text-white'
                    : 'text-zinc-600 hover:border-zinc-400'
                }`}
              >
                {count}일
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-xs text-zinc-500">
            장은 보통 2~3일에 한 번 보니 3일치를 권해요. 7일치는 만드는 데 더 오래 걸려요.
          </p>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-zinc-700">하루 식사 횟수</label>
          <div className="flex gap-2">
            {[2, 3].map(count => (
              <button
                key={count}
                type="button"
                onClick={() => setMealsPerDay(count as 2 | 3)}
                className={`flex-1 rounded-xl border px-3.5 py-2.5 text-sm font-medium transition ${
                  mealsPerDay === count
                    ? 'border-brand bg-brand text-white'
                    : 'text-zinc-600 hover:border-zinc-400'
                }`}
              >
                {count}끼
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="btn btn-primary btn-lg"
        >
          {loading ? '생성 중...' : '식단 생성하기'}
        </button>
      </div>
    </section>
  )
}
