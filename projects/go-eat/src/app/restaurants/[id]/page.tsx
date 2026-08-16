import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { toggleVisited, deleteRestaurant } from "@/app/actions/restaurants";
import { CATEGORY_ICONS } from "@/lib/types";
import { RestaurantSidebar } from "@/app/restaurant-sidebar";
import { DeleteButton } from "./delete-button";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function RestaurantDetailPage({ params }: Props) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // RLS가 이미 "본인 것만" 조회되게 걸러준다.
  // 남의 id로 접근하면 존재하지 않는 것처럼 data가 null로 온다.
  const { data: restaurant } = await supabase
    .from("restaurants")
    .select("*")
    .eq("id", id)
    .single();

  if (!restaurant) {
    notFound();
  }

  // 사이드바 진행률은 목록 화면과 동일하게 항상 "전체" 기준으로 보여준다.
  const { data: allRows } = await supabase.from("restaurants").select("visited");
  const allCount = allRows?.length ?? 0;
  const visitedAllCount = allRows?.filter((r) => r.visited).length ?? 0;

  return (
    <RestaurantSidebar
      email={user.email ?? null}
      allCount={allCount}
      visitedAllCount={visitedAllCount}
      activeVisited="all"
      activeCategory=""
      activeQuery=""
    >
      <Link href="/" className="text-sm text-zinc-500">
        ← 목록으로
      </Link>

      <div className="mt-4 grid gap-8 md:grid-cols-2 md:items-start">
        {restaurant.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={restaurant.photo_url}
            alt={restaurant.name}
            className="aspect-[4/3] w-full rounded-2xl border border-[#EAEAEA] object-cover shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
          />
        ) : (
          <div className="flex aspect-[4/3] w-full items-center justify-center rounded-2xl border border-[#EAEAEA] bg-orange-50 text-6xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
            {CATEGORY_ICONS[restaurant.category] ?? "🍽️"}
          </div>
        )}

        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600">
              {CATEGORY_ICONS[restaurant.category] ?? "🍽️"} {restaurant.category}
            </span>
            {restaurant.visited ? (
              <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-medium text-accent">
                ✅ 방문 완료
              </span>
            ) : (
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-500">
                아직 안 가봄
              </span>
            )}
          </div>

          <h1 className="mt-3 text-2xl font-bold">{restaurant.name}</h1>

          {restaurant.address && (
            <p className="mt-2 text-sm text-zinc-600">
              📍 {restaurant.address}
            </p>
          )}

          {restaurant.visited && (
            <p className="mt-2 text-sm text-zinc-600">
              {restaurant.rating ? "★".repeat(restaurant.rating) : ""}
              {restaurant.rating ? " · " : ""}
              {restaurant.visited_at ?? ""} 방문
            </p>
          )}

          {restaurant.memo && (
            <p className="mt-4 whitespace-pre-wrap rounded-xl bg-zinc-50 p-4 text-sm text-zinc-600">
              📝 {restaurant.memo}
            </p>
          )}

          <form action={toggleVisited} className="mt-6">
            <input type="hidden" name="id" value={restaurant.id} />
            <button
              type="submit"
              className="w-full rounded-xl border border-zinc-200 bg-white py-3 text-sm font-medium hover:bg-zinc-50"
            >
              {restaurant.visited ? "방문 체크 해제" : "방문 체크"}
            </button>
          </form>

          <div className="mt-3 flex gap-3">
            <Link
              href={`/restaurants/${restaurant.id}/edit`}
              className="flex-1 rounded-xl border border-zinc-200 bg-white py-3 text-center text-sm font-medium hover:bg-zinc-50"
            >
              수정
            </Link>
            <DeleteButton id={restaurant.id} action={deleteRestaurant} />
          </div>
        </div>
      </div>
    </RestaurantSidebar>
  );
}
