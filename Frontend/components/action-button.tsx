"use client"

import type { LucideIcon } from "lucide-react"

interface ActionButtonProps {
  icon: LucideIcon
  label: string
  onClick: () => void
  disabled?: boolean
  variant?: "primary" | "success" | "error"
  className?: string
}

export default function ActionButton({
  icon: Icon,
  label,
  onClick,
  disabled = false,
  variant = "primary",
  className = "",
}: ActionButtonProps) {
  const variantClasses = {
    primary: "bg-slate-700/50 border-slate-600 hover:bg-slate-600 text-slate-200 hover:text-white shadow-lg hover:shadow-xl",
    success: "bg-emerald-600/20 border-emerald-500/50 hover:bg-emerald-500/30 text-emerald-400 hover:text-emerald-300 shadow-lg hover:shadow-emerald-500/20",
    error: "bg-rose-600/20 border-rose-500/50 hover:bg-rose-500/30 text-rose-400 hover:text-rose-300 shadow-lg hover:shadow-rose-500/20",
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex flex-col items-center gap-3 rounded-lg border p-5 transition-all duration-200 disabled:opacity-50 ${variantClasses[variant]} ${className}`}
    >
      <Icon className="h-7 w-7" />
      <span className="text-xs font-medium text-center">{label}</span>
    </button>
  )
}
