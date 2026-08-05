import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "AI Kids Video Studio",
  description:
    "Turn a simple topic into a complete, reviewed, kid-safe educational video.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

// Pre-paint theme init prevents light/dark flash
const themeInit = `
(function(){try{var t=localStorage.getItem('studio.theme');
if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme: dark)').matches)){
document.documentElement.classList.add('dark');}}catch(e){}})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
