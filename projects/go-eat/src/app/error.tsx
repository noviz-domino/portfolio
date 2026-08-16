"use client";

import { useEffect } from "react";

type Props = {
  error: Error & { digest?: string };
  unstable_retry: () => void;
};

export default function Error({ error, unstable_retry }: Props) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center px-5 py-24 text-center">
      <p className="text-4xl">😵</p>
      <p className="mt-4 font-medium">문제가 생겼어요</p>
      <p className="mt-1 text-sm text-zinc-500">
        잠시 후 다시 시도해주세요
      </p>
      <button
        onClick={() => unstable_retry()}
        className="mt-6 rounded-xl bg-accent px-5 py-3 text-sm font-medium text-white"
      >
        다시 시도
      </button>
    </main>
  );
}
