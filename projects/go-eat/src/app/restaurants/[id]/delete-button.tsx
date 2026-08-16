"use client";

type Props = {
  id: string;
  action: (formData: FormData) => void | Promise<void>;
};

export function DeleteButton({ id, action }: Props) {
  return (
    <form
      action={action}
      onSubmit={(e) => {
        if (!confirm("이 맛집을 삭제하시겠습니까?")) {
          e.preventDefault();
        }
      }}
      className="flex-1"
    >
      <input type="hidden" name="id" value={id} />
      <button
        type="submit"
        className="w-full rounded-xl border border-red-200 bg-red-50 py-3 text-sm font-medium text-red-600 hover:bg-red-100"
      >
        삭제
      </button>
    </form>
  );
}
