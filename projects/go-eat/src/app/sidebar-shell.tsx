"use client";

import { useState } from "react";

type Props = {
  full: React.ReactNode;
  collapsed: React.ReactNode;
  children: React.ReactNode;
};

// 데스크톱에서만 화면 왼쪽에 완전히 붙는 고정 레일로 만들고, 접으면 아이콘만 남긴다.
// 모바일은 접기 기능 없이 항상 펼쳐진 내용을 화면 위쪽에 그대로 쌓아 보여준다.
export function SidebarShell({ full, collapsed, children }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div>
      <aside
        className={`mb-8 border-b border-zinc-200 pb-8 md:fixed md:inset-y-0 md:left-0 md:mb-0 md:flex md:flex-col md:overflow-y-auto md:border-b-0 md:border-r md:border-zinc-200 md:bg-white md:px-4 md:py-8 md:transition-[width] md:duration-150 ${
          isCollapsed ? "md:w-20" : "md:w-64"
        }`}
      >
        <button
          type="button"
          onClick={() => setIsCollapsed((v) => !v)}
          className="mb-4 hidden h-8 w-8 items-center justify-center self-end rounded-full border border-zinc-200 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-600 md:flex"
          aria-label={isCollapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          {isCollapsed ? "›" : "‹"}
        </button>

        <div className="flex flex-col gap-6 md:hidden">{full}</div>
        <div className="hidden md:flex md:flex-1 md:flex-col md:gap-6 md:overflow-y-auto">
          {isCollapsed ? collapsed : full}
        </div>
      </aside>

      <main className={isCollapsed ? "md:pl-20" : "md:pl-64"}>
        <div className="mx-auto max-w-6xl px-5 py-8">{children}</div>
      </main>
    </div>
  );
}
