import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF Editor",
  description: "Real PDF editor using Next.js and FastAPI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
