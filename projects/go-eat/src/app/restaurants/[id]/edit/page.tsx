import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { RestaurantSidebar } from "@/app/restaurant-sidebar";
import { EditRestaurantForm } from "./restaurant-form";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function EditRestaurantPage({ params }: Props) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // RLS가 본인 것만 조회되게 걸러준다. 남의 id면 존재하지 않는 것처럼 온다.
  const { data: restaurant } = await supabase
    .from("restaurants")
    .select("*")
    .eq("id", id)
    .single();

  if (!restaurant) {
    notFound();
  }

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
      <div className="mx-auto max-w-lg">
        <Link href={`/restaurants/${id}`} className="text-sm text-zinc-500">
          ← 취소
        </Link>

        <div className="mt-4 rounded-2xl border border-[#EAEAEA] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <h1 className="mb-8 text-xl font-bold">맛집 수정</h1>
          <EditRestaurantForm restaurant={restaurant} />
        </div>
      </div>
    </RestaurantSidebar>
  );
}
