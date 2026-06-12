import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./global.css"
import Sidebar from "@/components/layout/Sidebar"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Dilamme — Job Scheduler",
  description: "Background job scheduler dashboard",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-neutral-50 text-neutral-900`}
      >
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 min-w-0 p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}