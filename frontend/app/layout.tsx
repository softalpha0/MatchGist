import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MatchGist · the match, sized to fit every fan",
  description:
    "MatchGist explains what happened in a football match and why it mattered, then fits it to what each fan has: an SMS, a voice note, a watch glance or a full overlay, in their language and within their data budget.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased font-sans">{children}</body>
    </html>
  );
}
