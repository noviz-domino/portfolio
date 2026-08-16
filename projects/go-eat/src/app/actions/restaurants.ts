"use server";

import { randomUUID } from "crypto";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import type { SupabaseClient } from "@supabase/supabase-js";
import { parseRestaurantForm } from "@/lib/restaurant-form";
import { summarizeMemo } from "@/app/actions/ai";

export type RestaurantFormState = { error?: string };

const MAX_PHOTO_SIZE = 5 * 1024 * 1024;

// 사진이 있으면 Supabase Storage에 올리고 공개 URL을 돌려준다.
// 사진이 없으면(용량 0) null을 돌려주고, 실패해도 예외 대신 error 메시지로만 알린다.
async function uploadRestaurantPhoto(
  supabase: SupabaseClient,
  userId: string,
  file: FormDataEntryValue | null,
): Promise<{ url: string | null; error?: string }> {
  if (!(file instanceof File) || file.size === 0) {
    return { url: null };
  }

  if (file.size > MAX_PHOTO_SIZE) {
    return { url: null, error: "사진은 5MB 이하만 업로드할 수 있어요." };
  }

  if (!file.type.startsWith("image/")) {
    return { url: null, error: "이미지 파일만 업로드할 수 있어요." };
  }

  const ext = file.name.includes(".") ? file.name.split(".").pop() : "jpg";
  const path = `${userId}/${randomUUID()}.${ext}`;

  const { error } = await supabase.storage
    .from("restaurant-photos")
    .upload(path, file, { contentType: file.type });

  if (error) {
    return { url: null, error: `사진 업로드에 실패했습니다: ${error.message}` };
  }

  const { data } = supabase.storage.from("restaurant-photos").getPublicUrl(path);
  return { url: data.publicUrl };
}

export async function createRestaurant(
  _prev: RestaurantFormState,
  formData: FormData,
): Promise<RestaurantFormState> {
  const supabase = await createClient();

  // Server Action은 UI를 거치지 않고 직접 POST로도 호출될 수 있다.
  // 따라서 화면에서 이미 막았더라도 여기서 로그인 여부를 다시 확인한다.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "로그인이 필요합니다." };
  }

  const parsed = parseRestaurantForm(formData);

  if (!parsed.ok) {
    return { error: parsed.error };
  }

  // 목록 카드용 한 줄 요약을 미리 만들어둔다. AI 호출이 실패해도 저장은 계속 진행한다.
  const memoSummary = parsed.value.memo
    ? await summarizeMemo(parsed.value.memo)
    : null;

  const photo = await uploadRestaurantPhoto(
    supabase,
    user.id,
    formData.get("photo"),
  );

  if (photo.error) {
    return { error: photo.error };
  }

  const { error } = await supabase.from("restaurants").insert({
    name: parsed.value.name,
    category: parsed.value.category,
    address: parsed.value.address,
    memo: parsed.value.memo,
    memo_summary: memoSummary,
    visited: parsed.value.visited,
    visited_at: parsed.value.visitedAt,
    rating: parsed.value.rating,
    photo_url: photo.url,
    // 클라이언트가 보낸 값을 쓰지 않고 서버가 확인한 사용자 id를 넣는다.
    user_id: user.id,
  });

  if (error) {
    return { error: `저장에 실패했습니다: ${error.message}` };
  }

  revalidatePath("/");
  redirect("/");
}

export async function updateRestaurant(
  _prev: RestaurantFormState,
  formData: FormData,
): Promise<RestaurantFormState> {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "로그인이 필요합니다." };
  }

  const id = String(formData.get("id") ?? "");

  if (!id) {
    return { error: "잘못된 요청입니다." };
  }

  const parsed = parseRestaurantForm(formData);

  if (!parsed.ok) {
    return { error: parsed.error };
  }

  // 메모가 바뀌었을 수 있으니 수정할 때도 요약을 새로 만든다.
  const memoSummary = parsed.value.memo
    ? await summarizeMemo(parsed.value.memo)
    : null;

  const photo = await uploadRestaurantPhoto(
    supabase,
    user.id,
    formData.get("photo"),
  );

  if (photo.error) {
    return { error: photo.error };
  }

  // user_id는 애초에 수정 대상에 없다. RLS가 이 id의 소유자가 아니면 0행을 갱신한다.
  const { error } = await supabase
    .from("restaurants")
    .update({
      name: parsed.value.name,
      category: parsed.value.category,
      address: parsed.value.address,
      memo: parsed.value.memo,
      memo_summary: memoSummary,
      visited: parsed.value.visited,
      visited_at: parsed.value.visitedAt,
      rating: parsed.value.rating,
      // 새 사진을 올리지 않았으면 기존 사진을 그대로 둔다.
      ...(photo.url ? { photo_url: photo.url } : {}),
    })
    .eq("id", id);

  if (error) {
    return { error: `수정에 실패했습니다: ${error.message}` };
  }

  revalidatePath("/");
  revalidatePath(`/restaurants/${id}`);
  redirect(`/restaurants/${id}`);
}

export async function toggleVisited(formData: FormData) {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const id = String(formData.get("id") ?? "");

  if (!id) {
    redirect("/");
  }

  const { data: current } = await supabase
    .from("restaurants")
    .select("visited")
    .eq("id", id)
    .single();

  if (!current) {
    redirect("/");
  }

  const nextVisited = !current.visited;

  await supabase
    .from("restaurants")
    .update({
      visited: nextVisited,
      // 방문 체크를 해제하면 별점·방문일도 함께 지운다 (기획서 데이터 규칙)
      ...(nextVisited ? {} : { rating: null, visited_at: null }),
    })
    .eq("id", id);

  revalidatePath("/");
  revalidatePath(`/restaurants/${id}`);
  redirect(`/restaurants/${id}`);
}

export async function deleteRestaurant(formData: FormData) {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const id = String(formData.get("id") ?? "");

  if (id) {
    // RLS가 본인 소유 행만 지우도록 걸러준다. 남의 id를 보내도 아무 일도 안 일어난다.
    await supabase.from("restaurants").delete().eq("id", id);
  }

  revalidatePath("/");
  redirect("/");
}
