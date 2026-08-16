import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import {
  CATEGORIES,
  CATEGORY_ICONS,
  SORT_OPTIONS,
  type Restaurant,
  type SortOption,
} from "@/lib/types";
import { SearchInput } from "./search-input";
import { SortSelect } from "./sort-select";
import { RestaurantSidebar, type VisitedFilter } from "./restaurant-sidebar";

type Props = {
  searchParams: Promise<{
    q?: string;
    visited?: string;
    category?: string;
    sort?: string;
  }>;
};

export default async function Home({ searchParams }: Props) {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const sp = await searchParams;
  const q = (sp.q ?? "").trim();
  const visited: VisitedFilter =
    sp.visited === "todo" || sp.visited === "done" ? sp.visited : "all";
  const category = CATEGORIES.includes(
    sp.category as (typeof CATEGORIES)[number],
  )
    ? sp.category!
    : "";
  const sort: SortOption = SORT_OPTIONS.some((o) => o.value === sp.sort)
    ? (sp.sort as SortOption)
    : "recent";

  // 진행률 바는 필터와 무관하게 항상 "전체" 기준이어야 하므로 별도로 조회한다.
  const { data: allRows } = await supabase.from("restaurants").select("visited");
  const allCount = allRows?.length ?? 0;
  const visitedAllCount = allRows?.filter((r) => r.visited).length ?? 0;

  let query = supabase.from("restaurants").select("*");

  if (sort === "rating") {
    // 미방문(별점 null)은 항상 뒤로 보내고, 그 안에서는 최신순으로 묶는다.
    query = query
      .order("rating", { ascending: false, nullsFirst: false })
      .order("created_at", { ascending: false });
  } else {
    query = query.order("created_at", { ascending: false });
  }

  if (q) {
    query = query.ilike("name", `%${q}%`);
  }
  if (visited === "todo") {
    query = query.eq("visited", false);
  } else if (visited === "done") {
    query = query.eq("visited", true);
  }
  if (category) {
    query = query.eq("category", category);
  }

  const { data: restaurants, error } = await query;
  const filteredCount = restaurants?.length ?? 0;

  return (
    <RestaurantSidebar
      email={user.email ?? null}
      allCount={allCount}
      visitedAllCount={visitedAllCount}
      activeVisited={visited}
      activeCategory={category}
      activeQuery={q}
    >
      <>
        {error && (
          <p className="text-sm text-red-600">
            맛집 목록을 불러오지 못했습니다: {error.message}
          </p>
        )}

        {allCount === 0 && !error && (
          <div className="rounded-2xl border border-[#EAEAEA] bg-white py-20 text-center shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
            <Image
              src="/mascot-icon.png"
              alt=""
              width={96}
              height={96}
              className="mx-auto rounded-full"
            />
            <p className="mt-4 font-medium">아직 등록한 맛집이 없어요</p>
            <p className="mt-1 text-sm text-zinc-500">
              검색해도 안 나오는 그 집, 직접 기록해보세요
            </p>
            <Link
              href="/restaurants/new"
              className="mt-6 inline-block rounded-xl bg-accent px-5 py-3 text-sm font-medium text-white"
            >
              첫 맛집 등록하기
            </Link>
          </div>
        )}

        {allCount > 0 && (
          <div className="mb-6 flex gap-2">
            <SearchInput defaultValue={q} />
            <SortSelect defaultValue={sort} />
          </div>
        )}

        {allCount > 0 && filteredCount === 0 && !error && (
          <div className="rounded-2xl border border-[#EAEAEA] bg-white py-16 text-center shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
            <p className="text-sm text-zinc-500">조건에 맞는 맛집이 없어요</p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm font-medium"
            >
              필터 초기화
            </Link>
          </div>
        )}

        <ul className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-x-4 gap-y-6">
          {restaurants?.map((restaurant: Restaurant) => (
            <li key={restaurant.id}>
              <Link
                href={`/restaurants/${restaurant.id}`}
                className="block overflow-hidden rounded-2xl border border-[#EAEAEA] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
              >
                <div className="relative">
                  {restaurant.photo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={restaurant.photo_url}
                      alt={restaurant.name}
                      className={`aspect-square w-full object-cover ${
                        restaurant.visited ? "" : "opacity-70 grayscale-[0.25]"
                      }`}
                    />
                  ) : (
                    <div
                      className={`flex aspect-square w-full items-center justify-center bg-orange-50 text-5xl ${
                        restaurant.visited ? "" : "opacity-70 grayscale-[0.25]"
                      }`}
                    >
                      {CATEGORY_ICONS[restaurant.category] ?? "🍽️"}
                    </div>
                  )}
                  {restaurant.visited && (
                    <span className="absolute right-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-xs font-medium text-accent shadow-sm">
                      ✅ 방문
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex items-baseline justify-between gap-2">
                    <strong className="text-lg font-bold">
                      {restaurant.name}
                    </strong>
                    <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-[12px] font-medium text-zinc-600">
                      {restaurant.category}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-600">
                    {restaurant.visited
                      ? `${"★".repeat(restaurant.rating ?? 0)} · ${restaurant.visited_at ?? ""} 방문`
                      : "아직 안 가봄"}
                  </p>
                  {(restaurant.memo_summary || restaurant.memo) && (
                    <p className="mt-2 line-clamp-2 text-[13px] text-zinc-500">
                      {restaurant.memo_summary ??
                        // AI 요약이 아직 없는 예전 메모는 앞부분만 잘라서 보여준다.
                        `${restaurant.memo!.slice(0, 40)}${restaurant.memo!.length > 40 ? "…" : ""}`}
                    </p>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </>
    </RestaurantSidebar>
  );
}
