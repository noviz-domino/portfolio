import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "가봐야 알지",
  description:
    "검색해도 안 나오는 시골 맛집을 직접 저장하고, 다녀온 곳을 체크·평가해 나만의 맛집 목록을 만드는 앱",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
