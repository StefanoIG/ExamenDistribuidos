"use client"

import { useState, useEffect } from "react"
import { useSocket } from "@/context/socket-context"
import { X, Calendar, ArrowUpRight, ArrowDownLeft } from "lucide-react"

interface Transaction {
  date: string
  type: string
  amount: number
  newBalance: number
}

interface TransactionHistoryProps {
  cedula: string
  onClose: () => void
}

export default function TransactionHistory({ cedula, onClose }: TransactionHistoryProps) {
  const { sendSocketMessage, isLoading } = useSocket()
  const [transactions, setTransactions] = useState<Transaction[]>([])

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await sendSocketMessage("GET_TRANSACTIONS", { cedula })
        if (response && typeof response === "object" && "transactions" in response) {
          setTransactions(response.transactions as Transaction[])
        }
      } catch (error) {
        console.error("Error fetching transactions:", error)
      }
    }

    fetchTransactions()

    // Escuchar actualizaciones de transacciones vía WebSocket
    const handleTransactionsUpdate = (event: Event) => {
      const customEvent = event as CustomEvent
      const data = customEvent.detail as { cedula: string; transactions: Array<{tipo: string; monto: number; saldo_final: number; fecha: string}> }
      
      if (data.cedula === cedula) {
        console.log("🔄 Actualizando historial en modal por WebSocket:", data.transactions.length)
        // Mapear formato del backend al frontend
        const mappedTransactions = data.transactions.map(tx => ({
          date: tx.fecha,
          type: tx.tipo === 'DEPOSITO' ? 'Depósito' : 'Retiro',
          amount: tx.monto,
          newBalance: tx.saldo_final
        })) as Transaction[]
        setTransactions(mappedTransactions)
      }
    }

    window.addEventListener("transactionsUpdate", handleTransactionsUpdate)

    return () => {
      window.removeEventListener("transactionsUpdate", handleTransactionsUpdate)
    }
  }, [cedula, sendSocketMessage])

  const isDeposit = (type: string) => {
    if (!type) return false
    const normalized = type.toLowerCase()
    return normalized === "deposito" || normalized === "depósito" || normalized.includes("deposit")
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl scale-in w-full max-w-3xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-blue-600/20 p-3">
              <Calendar className="h-6 w-6 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">Historial de Transacciones</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="overflow-x-auto overflow-y-auto flex-1">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-800/95 backdrop-blur-sm">
              <tr className="border-b border-slate-600">
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Fecha</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Tipo</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-300">Monto</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-300">Saldo Final</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx, idx) => (
                <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-3 text-slate-300">{tx.date}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {isDeposit(tx.type) ? (
                        <ArrowDownLeft className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <ArrowUpRight className="h-4 w-4 text-rose-400" />
                      )}
                      <span className={isDeposit(tx.type) ? "text-emerald-400 font-medium" : "text-rose-400 font-medium"}>
                        {tx.type}
                      </span>
                    </div>
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-semibold ${
                      isDeposit(tx.type) ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isDeposit(tx.type) ? "+" : "-"}${tx.amount.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right text-white font-semibold">${tx.newBalance.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 rounded-xl border border-slate-600 bg-slate-700/30 px-4 py-3 font-medium text-white hover:bg-slate-600/50 transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}
