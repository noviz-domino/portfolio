export type Restaurant = {
  id: string;
  name: string;
  category: string;
  address: string | null;
  rating: number | null;
  visited: boolean;
  visited_at: string | null;
  memo: string | null;
  memo_summary: string | null;
  photo_url: string | null;
  user_id: string;
  created_at: string;
};

export const SORT_OPTIONS = [
  { value: "recent", label: "최신순" },
  { value: "rating", label: "별점순" },
] as const;

export type SortOption = (typeof SORT_OPTIONS)[number]["value"];

export const CATEGORIES = [
  "한식",
  "중식",
  "일식",
  "양식",
  "카페·디저트",
  "기타",
] as const;

// 사진을 안 쓰기로 한 기획 원칙 대신, 카드에 시각적 앵커를 주기 위한 카테고리별 이모지.
export const CATEGORY_ICONS: Record<string, string> = {
  한식: "🍚",
  중식: "🥡",
  일식: "🍣",
  양식: "🍝",
  "카페·디저트": "☕",
  기타: "🍽️",
};
