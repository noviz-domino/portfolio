// 검색 입력창. 공개 홈과 내 식단 목록이 같이 쓴다.
// 돋보기 아이콘을 입력창 안에 겹쳐 두어, placeholder를 읽기 전에도 검색칸임이 보이게 한다.
// 아이콘은 클릭을 가로채지 않도록 pointer-events-none 을 준다.
export function SearchInput({
  defaultValue,
  placeholder,
}: {
  defaultValue?: string
  placeholder: string
}) {
  return (
    <div className="relative">
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.4-3.4" />
      </svg>
      <input
        type="search"
        name="q"
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="w-44 rounded-full border border-zinc-300 bg-white py-2 pl-10 pr-4 text-sm text-zinc-900 shadow-sm placeholder:text-zinc-400 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30 sm:w-60"
      />
    </div>
  )
}
