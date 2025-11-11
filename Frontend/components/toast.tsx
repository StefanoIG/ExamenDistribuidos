"use client"

import { AlertCircle, CheckCircle, X } from "lucide-react"
import { useState, useEffect } from "react"

interface ToastProps {
  message: string
  type: "success" | "error"
}

export default function Toast({ message, type }: ToastProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(false), 3000)
    return () => clearTimeout(timer)
  }, [])

  if (!isVisible) return null

  const isSuccess = type === "success"
  const bgColor = isSuccess ? "bg-success/10 border-success/30" : "bg-error/10 border-error/30"
  const textColor = isSuccess ? "text-success" : "text-error"
  const Icon = isSuccess ? CheckCircle : AlertCircle

  return (
    <div className={`slide-in card border ${bgColor} flex items-start gap-3`}>
      <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${textColor}`} />
      <p className="text-sm text-foreground flex-1">{message}</p>
      <button
        onClick={() => setIsVisible(false)}
        className="text-foreground-secondary hover:text-foreground flex-shrink-0"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
