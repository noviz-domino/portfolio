import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { RestaurantSidebar } from "@/app/restaurant-sidebar";
import { NewRestaurantForm } from "./restaurant-form";

export default async function NewRestaurantPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
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
        <Link href="/" className="text-sm text-zinc-500">
          ← 취소
        </Link>

        <div className="mt-4 rounded-2xl border border-[#EAEAEA] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <h1 className="mb-8 text-xl font-bold">맛집 등록</h1>
          <NewRestaurantForm />
        </div>
      </div>
    </RestaurantSidebar>
  );
}
