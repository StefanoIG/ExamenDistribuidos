"use client"

import { Eye, EyeOff } from "lucide-react"
import { useState } from "react"

interface BalanceCardProps {
  balance: number
  isLoading?: boolean
}

export default function BalanceCard({ balance, isLoading = false }: BalanceCardProps) {
  const [showBalance, setShowBalance] = useState(true)

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 p-6 shadow-2xl border border-blue-500/30">
      <div className="relative z-10">
        <p className="text-sm font-semibold text-blue-100 mb-4 uppercase tracking-wide">Saldo Disponible</p>

        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="flex items-baseline gap-3">
              <span className="text-5xl font-bold text-white drop-shadow-lg">
                {showBalance ? `$${balance.toFixed(2)}` : "••••••"}
              </span>
              <span className="text-lg text-blue-200 font-semibold">USD</span>
            </div>
          </div>

          <button
            onClick={() => setShowBalance(!showBalance)}
            disabled={isLoading}
            className="p-3 rounded-xl bg-white/20 hover:bg-white/30 text-white transition-all disabled:opacity-50 backdrop-blur-sm shadow-lg"
          >
            {showBalance ? <Eye className="h-5 w-5" /> : <EyeOff className="h-5 w-5" />}
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-white/20">
          <p className="text-xs text-blue-100">Última actualización: hace unos momentos</p>
        </div>
      </div>
      
      {/* Decorative background pattern */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl"></div>
    </div>
  )
}
