import { CATEGORIES } from "@/lib/types";

export type ParsedRestaurantForm = {
  name: string;
  category: string;
  address: string | null;
  memo: string | null;
  visited: boolean;
  visitedAt: string | null;
  rating: number | null;
};

export type ParseResult =
  | { ok: true; value: ParsedRestaurantForm }
  | { ok: false; error: string };

// createRestaurant, updateRestaurant이 공유하는 입력 검증.
// "use server" 파일 안에 두면 export된 모든 함수가 Server Action으로 취급되므로
// 별도 파일로 뺀다.
export function parseRestaurantForm(formData: FormData): ParseResult {
  const name = String(formData.get("name") ?? "").trim();
  const category = String(formData.get("category") ?? "");
  const address = String(formData.get("address") ?? "").trim();
  const memo = String(formData.get("memo") ?? "").trim();
  const visited = formData.get("visited") === "on";
  const visitedAtRaw = String(formData.get("visited_at") ?? "");
  const ratingRaw = String(formData.get("rating") ?? "");

  if (!name) {
    return { ok: false, error: "가게 이름을 입력해주세요." };
  }

  if (!CATEGORIES.includes(category as (typeof CATEGORIES)[number])) {
    return { ok: false, error: "카테고리를 선택해주세요." };
  }

  // 미방문이면 별점·방문일은 저장하지 않는다 (기획서의 데이터 규칙)
  let rating: number | null = null;
  let visitedAt: string | null = null;

  if (visited) {
    if (ratingRaw) {
      const parsed = Number(ratingRaw);
      if (!Number.isInteger(parsed) || parsed < 1 || parsed > 5) {
        return { ok: false, error: "별점은 1~5 사이여야 합니다." };
      }
      rating = parsed;
    }
    visitedAt = visitedAtRaw || null;
  }

  return {
    ok: true,
    value: {
      name,
      category,
      address: address || null,
      memo: memo || null,
      visited,
      visitedAt,
      rating,
    },
  };
}
