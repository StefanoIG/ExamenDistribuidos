"use client"

import { useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, XCircle, X } from "lucide-react"

interface AlertToastProps {
  title: string
  description: string
  variant?: "default" | "success" | "error" | "destructive"
  duration?: number
  onClose?: () => void
}

export function AlertToast({ 
  title, 
  description, 
  variant = "default", 
  duration = 5000,
  onClose 
}: AlertToastProps) {
  const [isVisible, setIsVisible] = useState(true)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose()
    }, duration)
    
    return () => clearTimeout(timer)
  }, [duration])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => {
      setIsVisible(false)
      onClose?.()
    }, 300)
  }

  if (!isVisible) return null

  const styles = {
    success: {
      bg: "bg-emerald-600 border-emerald-500",
      icon: CheckCircle2,
      iconColor: "text-emerald-100"
    },
    error: {
      bg: "bg-rose-600 border-rose-500",
      icon: XCircle,
      iconColor: "text-rose-100"
    },
    destructive: {
      bg: "bg-rose-600 border-rose-500",
      icon: AlertCircle,
      iconColor: "text-rose-100"
    },
    default: {
      bg: "bg-blue-600 border-blue-500",
      icon: AlertCircle,
      iconColor: "text-blue-100"
    }
  }

  const style = styles[variant] || styles.default
  const Icon = style.icon

  return (
    <div
      className={`fixed top-4 right-4 z-50 ${isExiting ? 'animate-slide-out-right' : 'animate-slide-in-right'}`}
      style={{ maxWidth: '400px' }}
    >
      <div className={`${style.bg} border-2 rounded-xl shadow-2xl p-4 backdrop-blur-sm`}>
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 ${style.iconColor}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-white font-bold text-sm mb-1">{title}</h4>
            <p className="text-white/90 text-sm break-words">{description}</p>
          </div>
          <button
            onClick={handleClose}
            className="flex-shrink-0 text-white/70 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
