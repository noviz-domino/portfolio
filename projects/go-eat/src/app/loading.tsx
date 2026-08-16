export default function Loading() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 py-8 md:flex-row md:items-start md:gap-10">
      <aside className="w-full shrink-0 md:w-64">
        <div className="h-40 animate-pulse rounded-2xl border border-[#EAEAEA] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.04)]" />
      </aside>
      <main className="min-w-0 flex-1">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-x-4 gap-y-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="overflow-hidden rounded-2xl border border-[#EAEAEA] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
            >
              <div className="aspect-square w-full animate-pulse bg-zinc-100" />
              <div className="space-y-2 p-4">
                <div className="h-4 w-2/3 animate-pulse rounded bg-zinc-100" />
                <div className="h-3 w-1/2 animate-pulse rounded bg-zinc-100" />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
