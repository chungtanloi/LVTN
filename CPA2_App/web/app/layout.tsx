import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CPA² — Trợ lý học vụ có chứng minh",
  description:
    "Tư vấn học vụ cá nhân hóa với kết luận ba trị và chứng chỉ truy về quy chế. CNTT K49 · Đại học Cần Thơ.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const configured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
    process.env.NEXT_PUBLIC_CONVEX_URL,
  );
  return (
    <html lang="vi">
      <body>
        <Providers configured={configured}>{children}</Providers>
      </body>
    </html>
  );
}
