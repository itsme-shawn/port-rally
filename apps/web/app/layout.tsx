import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Port-Rally",
  description: "Your Portfolio Tracker",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
