import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoPilot",
  description: "Repo-aware AI software engineering agent"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
