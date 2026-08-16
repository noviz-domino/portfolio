import Image from "next/image";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { LoginForm } from "./login-form";

export default async function LoginPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();

  if (data.user) {
    redirect("/");
  }

  return (
    <main className="flex min-h-dvh items-center justify-center px-5">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <Image
            src="/logo-hero.png"
            alt="가봐야 알지 - 맛있는 곳을 찾아 떠나요"
            width={240}
            height={240}
            className="mx-auto"
            priority
          />
        </div>

        <LoginForm />
      </div>
    </main>
  );
}
