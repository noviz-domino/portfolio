import type { Metadata } from "next";
import { Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";

// 기획서 2-2: 한글 가독성 좋은 sans-serif.
// 화면이 거의 전부 한글이라 라틴 전용 폰트(Geist 등)를 쓰면 한글은 시스템 폰트로 fallback된다.
// next/font가 파일을 직접 호스팅하므로 외부 CDN 요청이 없다.
const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MealMate",
  description: "냉장고 재료로 만드는 AI 주간 식단 플래너",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className={`${notoSansKr.className} min-h-full flex flex-col`}>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
