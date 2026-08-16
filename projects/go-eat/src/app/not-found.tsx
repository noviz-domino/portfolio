import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-2xl flex-col items-center px-5 py-24 text-center">
      <p className="text-4xl">🍜</p>
      <p className="mt-4 font-medium">그런 맛집은 없어요</p>
      <p className="mt-1 text-sm text-zinc-500">
        주소가 잘못됐거나, 이미 삭제된 맛집일 수 있어요
      </p>
      <Link
        href="/"
        className="mt-6 rounded-xl bg-accent px-5 py-3 text-sm font-medium text-white"
      >
        목록으로
      </Link>
    </main>
  );
}
