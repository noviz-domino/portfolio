"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import {
  createRestaurant,
  type RestaurantFormState,
} from "@/app/actions/restaurants";
import { CATEGORIES } from "@/lib/types";
import { StarRating } from "@/components/star-rating";

const initialState: RestaurantFormState = {};

const inputClass =
  "rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-zinc-400";

export function NewRestaurantForm() {
  const [state, formAction, pending] = useActionState(
    createRestaurant,
    initialState,
  );
  const [name, setName] = useState("");
  const [visited, setVisited] = useState(false);

  return (
    <form action={formAction} className="flex flex-col gap-5">
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">
          가게 이름 <span className="text-red-500">*</span>
        </span>
        <input
          name="name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="봉평면 메밀국수"
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">
          카테고리 <span className="text-red-500">*</span>
        </span>
        <select name="category" required defaultValue="" className={inputClass}>
          <option value="" disabled>
            선택해주세요
          </option>
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">주소</span>
        <input
          name="address"
          placeholder="강원 평창군 봉평면 창동리"
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">대표 사진</span>
        <input
          type="file"
          name="photo"
          accept="image/*"
          className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-zinc-100 file:px-3 file:py-2 file:text-sm"
        />
      </label>

      <div className="flex flex-col gap-3 rounded-xl bg-zinc-50 p-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            name="visited"
            checked={visited}
            onChange={(e) => setVisited(e.target.checked)}
            className="size-4"
          />
          <span className="text-sm font-medium">이미 다녀왔어요</span>
        </label>

        {visited && (
          <>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm text-zinc-600">방문일</span>
              <input
                type="date"
                name="visited_at"
                className={`${inputClass} bg-white`}
              />
            </label>

            <div className="flex flex-col gap-1.5">
              <span className="text-sm text-zinc-600">별점</span>
              <StarRating name="rating" />
            </div>
          </>
        )}
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">메모</span>
        <textarea
          name="memo"
          rows={3}
          placeholder="현금만 받음. 재료 떨어지면 마감. 네비에 안 나와서 우체국 옆 골목."
          className={inputClass}
        />
        <span className="text-xs text-zinc-400">
          영업시간, 현금 여부, 찾아가는 길처럼 검색해도 안 나오는 정보를 적어두세요. 저장하면 목록 카드용 한 줄 요약을 AI가 자동으로 만들어줍니다.
        </span>
      </label>

      {state.error && <p className="text-sm text-red-600">{state.error}</p>}

      <div className="mt-2 flex gap-3">
        <Link
          href="/"
          className="flex-1 rounded-xl border border-zinc-200 py-3 text-center text-sm font-medium"
        >
          취소
        </Link>
        <button
          type="submit"
          disabled={pending || !name.trim()}
          className="flex-1 rounded-xl bg-accent py-3 text-sm font-medium text-white disabled:opacity-50"
        >
          {pending ? "저장 중..." : "저장"}
        </button>
      </div>
    </form>
  );
}
