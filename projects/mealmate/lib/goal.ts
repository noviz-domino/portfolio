// 목표(goal) 라벨과 badge 색.
// 홈 카드, 내 식단 카드, 상세 페이지 세 군데가 각자 GOAL_LABEL을 복사해 두고 있었다.
// 색까지 각자 정하면 또 갈라지므로 여기 한 곳에서만 정한다.

export const GOAL_LABEL: Record<string, string> = {
  loss: '체중 감량',
  maintain: '체중 유지',
  bulk: '벌크업',
  balanced: '균형 식단',
}

// 색은 globals.css의 --color-goal-* 토큰에서 온다. 여기서 hex를 직접 쓰지 않는다.
const GOAL_BADGE: Record<string, string> = {
  loss: 'bg-goal-loss text-goal-loss-ink',
  maintain: 'bg-goal-maintain text-goal-maintain-ink',
  bulk: 'bg-goal-bulk text-goal-bulk-ink',
  balanced: 'bg-goal-balanced text-goal-balanced-ink',
}

export function goalLabel(goal: string) {
  return GOAL_LABEL[goal] ?? goal
}

export function goalBadgeClass(goal: string) {
  return GOAL_BADGE[goal] ?? 'bg-zinc-100 text-zinc-700'
}
