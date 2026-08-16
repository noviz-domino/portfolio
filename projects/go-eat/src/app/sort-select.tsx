"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { SORT_OPTIONS, type SortOption } from "@/lib/types";

type Props = {
  defaultValue: SortOption;
};

export function SortSelect({ defaultValue }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleChange(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value && value !== "recent") {
      params.set("sort", value);
    } else {
      params.delete("sort");
    }
    const qs = params.toString();
    router.push(qs ? `/?${qs}` : "/");
  }

  return (
    <select
      defaultValue={defaultValue}
      onChange={(e) => handleChange(e.target.value)}
      className="shrink-0 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm"
    >
      {SORT_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
