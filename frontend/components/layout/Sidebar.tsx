"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { href: "/", label: "Dashboard", icon: "⬡" },
  { href: "/jobs", label: "Jobs", icon: "⚙" },
  { href: "/create", label: "Create job", icon: "+" },
  { href: "/dlq", label: "Dead-letter queue", icon: "⚠" },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 shrink-0 h-screen sticky top-0 flex flex-col border-r border-neutral-200 bg-white px-3 py-5">
      {/* Logo */}
      <div className="flex items-center gap-2 px-2 mb-8">
        <div className="w-7 h-7 rounded-md bg-emerald-600 flex items-center justify-center">
          <span className="text-white text-xs font-bold">D</span>
        </div>
        <div>
          <p className="text-sm font-medium text-neutral-900 leading-none">Dilamme</p>
          <p className="text-[10px] text-neutral-400 mt-0.5">Job scheduler</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
                ${isActive
                  ? "bg-emerald-50 text-emerald-700 font-medium"
                  : "text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900"
                }
              `}
            >
              <span className="text-base leading-none">{item.icon}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pt-4 border-t border-neutral-100">
        <p className="text-[10px] text-neutral-400">
          Workers <span className="text-emerald-600 font-medium">online</span>
        </p>
      </div>
    </aside>
  )
}