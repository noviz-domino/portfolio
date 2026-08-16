"use client";

import { useState } from "react";

type Props = {
  name: string;
  defaultValue?: number | null;
};

export function StarRating({ name, defaultValue = null }: Props) {
  const [rating, setRating] = useState<number>(defaultValue ?? 0);

  return (
    <div className="flex items-center gap-1">
      {/* 폼 전송용 실제 값 */}
      <input type="hidden" name={name} value={rating || ""} />

      {[1, 2, 3, 4, 5].map((score) => (
        <button
          key={score}
          type="button"
          onClick={() => setRating(score === rating ? 0 : score)}
          aria-label={`별점 ${score}점`}
          aria-pressed={score <= rating}
          className="text-2xl leading-none"
        >
          <span className={score <= rating ? "text-amber-400" : "text-zinc-300"}>
            ★
          </span>
        </button>
      ))}

      {rating > 0 && (
        <span className="ml-2 text-sm text-zinc-500">{rating}점</span>
      )}
    </div>
  );
}
