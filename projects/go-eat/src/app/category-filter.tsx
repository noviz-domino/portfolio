"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { CATEGORIES } from "@/lib/types";

type Props = {
  defaultValue: string;
};

export function CategoryFilter({ defaultValue }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set("category", value);
    } else {
      params.delete("category");
    }
    const qs = params.toString();
    router.push(qs ? `/?${qs}` : "/");
  }

  return (
    <select
      defaultValue={defaultValue}
      onChange={(e) => handleChange(e.target.value)}
      className="rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm"
    >
      <option value="">카테고리 전체</option>
      {CATEGORIES.map((category) => (
        <option key={category} value={category}>
          {category}
        </option>
      ))}
    </select>
  );
}
