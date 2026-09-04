import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BuildBot - Student AI Coding Assistant",
  description:
    "From Research Paper to SRS to Checklist to Working Code — with Any AI, Anywhere",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
