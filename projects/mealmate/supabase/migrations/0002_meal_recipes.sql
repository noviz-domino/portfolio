-- F-16 조리법 상세
-- meals 테이블에 조리법 컬럼을 추가한다. 조리법은 카드를 처음 펼칠 때 한 끼씩 생성해서 저장한다.
-- 기존 행은 모두 빈 배열/NULL로 시작하며, 펼칠 때 채워진다.

alter table public.meals
  add column if not exists recipe_ingredients text[] not null default '{}',
  add column if not exists recipe_steps text[] not null default '{}',
  add column if not exists recipe_servings text,
  add column if not exists recipe_minutes int,
  add column if not exists recipe_tip text,
  add column if not exists recipe_generated_at timestamptz;

-- RLS 정책은 새로 만들 필요가 없다.
--   읽기: meals_select_visible_plan (공개 식단이거나 본인 식단)
--   쓰기: meals_update_own (auth.uid() = user_id) → 소유자만 조리법 생성 가능
