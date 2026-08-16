"use client";

import { useActionState, useState } from "react";
import { login, signup, type AuthState } from "@/app/actions/auth";

const initialState: AuthState = {};

const inputClass =
  "rounded-xl border border-zinc-200 px-4 py-3 text-sm outline-none focus:border-zinc-400";

function LoginFields() {
  const [state, formAction, pending] = useActionState(login, initialState);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">이메일</span>
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">비밀번호</span>
        <input
          name="password"
          type="password"
          required
          autoComplete="current-password"
          className={inputClass}
        />
      </label>

      {state.error && <p className="text-sm text-red-600">{state.error}</p>}

      <button
        type="submit"
        disabled={pending}
        className="mt-2 rounded-xl bg-accent py-3 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "처리 중..." : "로그인"}
      </button>
    </form>
  );
}

function SignupFields() {
  const [state, formAction, pending] = useActionState(signup, initialState);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">이메일</span>
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium">비밀번호</span>
        <input
          name="password"
          type="password"
          required
          autoComplete="new-password"
          className={inputClass}
        />
      </label>

      {state.error && <p className="text-sm text-red-600">{state.error}</p>}
      {state.message && (
        <p className="text-sm text-zinc-600">{state.message}</p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="mt-2 rounded-xl bg-accent py-3 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "처리 중..." : "가입하기"}
      </button>
    </form>
  );
}

export function LoginForm() {
  const [mode, setMode] = useState<"login" | "signup">("login");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex rounded-xl bg-zinc-100 p-1">
        <button
          type="button"
          onClick={() => setMode("login")}
          className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
            mode === "login" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500"
          }`}
        >
          로그인
        </button>
        <button
          type="button"
          onClick={() => setMode("signup")}
          className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
            mode === "signup" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500"
          }`}
        >
          회원가입
        </button>
      </div>

      <h2 className="text-center text-lg font-bold">
        {mode === "login" ? "로그인" : "회원가입"}
      </h2>

      {mode === "login" ? <LoginFields /> : <SignupFields />}
    </div>
  );
}
