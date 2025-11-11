"use client"

import { useState, useEffect } from "react"
import { type LucideIcon, X, Loader2 } from "lucide-react"

interface TransactionModalProps {
  title: string
  icon: LucideIcon
  onConfirm: (amount: number) => Promise<void>
  onClose: () => void
  isLoading?: boolean
  type: "deposit" | "withdraw"
  maxAmount?: number
}

export default function TransactionModal({
  title,
  icon: Icon,
  onConfirm,
  onClose,
  isLoading = false,
  type,
  maxAmount = Number.POSITIVE_INFINITY,
}: TransactionModalProps) {
  const [amount, setAmount] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    setError("")
  }, [amount])

  const handleConfirm = async () => {
    const parsedAmount = Number.parseFloat(amount)

    if (!amount.trim()) {
      setError("Por favor ingresa un monto")
      return
    }

    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError("Ingresa un monto válido mayor a 0")
      return
    }

    if (type === "withdraw" && parsedAmount > maxAmount) {
      setError(`No tienes suficientes fondos. Disponible: $${maxAmount}`)
      return
    }

    try {
      await onConfirm(parsedAmount)
    } catch {
      setError("Error al procesar la transacción")
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl scale-in w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`rounded-full p-3 ${type === "deposit" ? "bg-emerald-600/20" : "bg-rose-600/20"}`}>
              <Icon className={`h-6 w-6 ${type === "deposit" ? "text-emerald-400" : "text-rose-400"}`} />
            </div>
            <h2 className="text-2xl font-bold text-white">{title}</h2>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="text-slate-400 hover:text-white disabled:opacity-50 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-5">
          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-slate-300 mb-3">
              Monto a {type === "deposit" ? "Depositar" : "Retirar"}
            </label>
            <div className="flex items-center gap-3 bg-slate-700/50 border border-slate-600 rounded-xl px-4 py-3">
              <span className="text-white font-bold text-xl">$</span>
              <input
                id="amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                disabled={isLoading}
                className="flex-1 bg-transparent text-white text-xl font-semibold placeholder-slate-500 focus:outline-none disabled:opacity-50"
              />
            </div>
            {error && (
              <div className="mt-3 bg-rose-600/20 border border-rose-500/50 rounded-lg p-3">
                <p className="text-sm text-rose-400">{error}</p>
              </div>
            )}
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={handleConfirm}
              disabled={isLoading || !amount}
              className={`w-full rounded-xl py-3 font-semibold text-white disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg ${
                type === "deposit"
                  ? "bg-emerald-600 hover:bg-emerald-700 hover:shadow-emerald-600/20"
                  : "bg-rose-600 hover:bg-rose-700 hover:shadow-rose-600/20"
              }`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 smooth-spin" />
                  Procesando...
                </>
              ) : (
                "Confirmar Transacción"
              )}
            </button>
            <button
              onClick={onClose}
              disabled={isLoading}
              className="w-full rounded-xl border border-slate-600 bg-slate-700/30 px-4 py-3 font-medium text-white hover:bg-slate-600/50 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
