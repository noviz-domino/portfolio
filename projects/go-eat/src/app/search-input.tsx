"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useRef, useState } from "react";

type Props = {
  defaultValue: string;
};

export function SearchInput({ defaultValue }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [value, setValue] = useState(defaultValue);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function handleChange(next: string) {
    setValue(next);

    if (timer.current) {
      clearTimeout(timer.current);
    }

    // 한 글자씩 입력할 때마다 서버에 요청하지 않도록 300ms 기다린다.
    timer.current = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (next) {
        params.set("q", next);
      } else {
        params.delete("q");
      }
      const qs = params.toString();
      router.replace(qs ? `/?${qs}` : "/");
    }, 300);
  }

  return (
    <div className="relative min-w-0 flex-1">
      <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-zinc-400">
        🔍
      </span>
      <input
        type="search"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="가게 이름 검색"
        className="w-full rounded-full border border-zinc-200 bg-white py-2.5 pl-10 pr-4 text-sm leading-normal outline-none focus:border-zinc-400"
      />
    </div>
  );
}
