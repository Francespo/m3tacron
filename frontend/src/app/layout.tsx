import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
    subsets: ["latin"],
    variable: "--font-sans",
    display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
    subsets: ["latin"],
    variable: "--font-mono",
    display: "swap",
});

export const metadata: Metadata = {
    title: "M3taCron — Meta Snapshot",
    description:
        "M3taCron — X-Wing Miniatures Meta Analytics Platform. Discover the competitive landscape, ship stats, and tournament results for AMG, XWA, and Legacy formats.",
    openGraph: {
        title: "M3taCron — X-Wing Meta Analytics",
        description:
            "Superior meta analytics for the X-Wing Miniatures game. Tracking AMG, XWA, and Legacy formats.",
        type: "website",
    },
};

import { AppShell } from "@/components/AppShell";

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
            <head>
                <link rel="stylesheet" href="/xwing-miniatures-font/xwing-miniatures.css" />
            </head>
            <body className="bg-terminal-bg text-text-primary font-mono antialiased min-h-screen">
                <AppShell>
                    {children}
                </AppShell>
            </body>
        </html>
    );
}
