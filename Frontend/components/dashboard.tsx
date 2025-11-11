"use client"

import { useState, useEffect } from "react"
import { useSocket } from "@/context/socket-context"
import BalanceCard from "./balance-card"
import ActionButton from "./action-button"
import TransactionModal from "./transaction-modal"
import TransactionHistory from "./transaction-history"
import AdminPanel from "./admin-panel"
import FinancialChart from "./financial-chart"
import { LogOut, DollarSign, TrendingDown, History } from "lucide-react"

interface DashboardProps {
  cedula: string
  onLogout: () => void
}

interface UserData {
  name: string
  balance: number
  role?: string
}

interface Transaction {
  date: string
  type: "Depósito" | "Retiro"
  amount: number
  newBalance: number
}

type ModalType = "deposit" | "withdraw" | "history" | null

export default function Dashboard({ cedula, onLogout }: DashboardProps) {
  const { sendSocketMessage, isLoading } = useSocket()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [modalType, setModalType] = useState<ModalType>(null)
  const [toasts, setToasts] = useState<{ id: string; message: string; type: "success" | "error" }[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])

  useEffect(() => {
    // Fetch user data and transactions on mount
    const fetchData = async () => {
      try {
        const response = await sendSocketMessage("LOGIN", cedula)
        if (response && typeof response === "object" && "user" in response) {
          const user = response.user as Record<string, unknown>
          setUserData({
            name: user.name as string,
            balance: user.balance as number,
            role: user.role as string,
          })
        }

        const txResponse = await sendSocketMessage("GET_TRANSACTIONS", { cedula })
        if (txResponse && typeof txResponse === "object" && "transactions" in txResponse) {
          setTransactions(txResponse.transactions as Transaction[])
        }
      } catch (error) {
        console.error("Error fetching data:", error)
      }
    }

    fetchData()
  }, [cedula, sendSocketMessage])

  const addToast = (message: string, type: "success" | "error" = "success") => {
    const id = Math.random().toString()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 3000)
  }

  const handleDeposit = async (amount: number) => {
    try {
      const response = await sendSocketMessage("DEPOSIT", { cedula, amount })
      if (response && typeof response === "object" && "success" in response && response.success) {
        const newBalance = (response as Record<string, unknown>).newBalance as number
        setUserData((prev) => (prev ? { ...prev, balance: newBalance } : null))
        addToast(`✅ Depósito de $${amount} realizado exitosamente`, "success")
        setModalType(null)
        
        // Refrescar historial después de depósito
        const txResponse = await sendSocketMessage("GET_TRANSACTIONS", { cedula })
        if (txResponse && typeof txResponse === "object" && "transactions" in txResponse) {
          setTransactions(txResponse.transactions as Transaction[])
        }
      } else if (response && typeof response === "object" && "message" in response) {
        addToast(`❌ ${(response as Record<string, unknown>).message as string}`, "error")
      }
    } catch (error) {
      console.error(error)
      addToast("❌ Error al procesar el depósito", "error")
    }
  }

  const handleWithdraw = async (amount: number) => {
    try {
      const response = await sendSocketMessage("WITHDRAW", { cedula, amount })
      if (response && typeof response === "object" && "success" in response && response.success) {
        const newBalance = (response as Record<string, unknown>).newBalance as number
        setUserData((prev) => (prev ? { ...prev, balance: newBalance } : null))
        addToast(`✅ Retiro de $${amount} realizado exitosamente`, "success")
        setModalType(null)
        
        // Refrescar historial después de retiro
        const txResponse = await sendSocketMessage("GET_TRANSACTIONS", { cedula })
        if (txResponse && typeof txResponse === "object" && "transactions" in txResponse) {
          setTransactions(txResponse.transactions as Transaction[])
        }
      } else if (response && typeof response === "object" && "message" in response) {
        addToast(`❌ ${(response as Record<string, unknown>).message as string}`, "error")
      }
    } catch (error) {
      console.error(error)
      addToast("❌ Error al procesar el retiro", "error")
    }
  }

  const isAdmin = userData?.role === "admin"

  return (
    <div className="w-full max-w-4xl">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 shadow-xl">
        <div>
          <h1 className="text-3xl font-bold text-white">{userData?.name || "Usuario"}</h1>
          <p className="text-sm text-slate-300 mt-1">Cédula: <span className="font-mono">{cedula}</span></p>
          {isAdmin && (
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 bg-amber-500/20 border border-amber-500/50 rounded-full">
              <span className="text-amber-400 text-lg">👑</span>
              <span className="text-xs text-amber-300 font-bold uppercase tracking-wide">Administrador</span>
            </div>
          )}
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 rounded-xl bg-rose-600/20 border border-rose-500/50 px-5 py-3 text-rose-400 hover:bg-rose-500/30 hover:text-rose-300 transition-all shadow-lg"
        >
          <LogOut className="h-5 w-5" />
          <span className="text-sm font-semibold">Salir</span>
        </button>
      </div>

      {/* Balance Card */}
      <BalanceCard balance={userData?.balance || 0} isLoading={isLoading} />

      {/* Action Buttons Grid */}
      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-2">
        <ActionButton
          icon={DollarSign}
          label="Depositar"
          onClick={() => setModalType("deposit")}
          disabled={isLoading}
          variant="success"
        />
        <ActionButton
          icon={TrendingDown}
          label="Retirar"
          onClick={() => setModalType("withdraw")}
          disabled={isLoading}
          variant="error"
        />
        <ActionButton
          icon={History}
          label="Historial"
          onClick={() => setModalType("history")}
          disabled={isLoading}
          className="md:col-span-2"
        />
      </div>

      {/* Financial Chart - visible to all users */}
      {transactions.length > 0 && <FinancialChart transactions={transactions} />}

      {/* Admin Panel - only visible to admins */}
      {isAdmin && <AdminPanel cedula={cedula} />}

      {/* Modals */}
      {modalType === "deposit" && (
        <TransactionModal
          title="Depositar Dinero"
          icon={DollarSign}
          onConfirm={handleDeposit}
          onClose={() => setModalType(null)}
          isLoading={isLoading}
          type="deposit"
        />
      )}

      {modalType === "withdraw" && (
        <TransactionModal
          title="Retirar Dinero"
          icon={TrendingDown}
          onConfirm={handleWithdraw}
          onClose={() => setModalType(null)}
          isLoading={isLoading}
          type="withdraw"
          maxAmount={userData?.balance || 0}
        />
      )}

      {modalType === "history" && <TransactionHistory cedula={cedula} onClose={() => setModalType(null)} />}

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 space-y-2 z-40">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`p-4 rounded-lg shadow-lg backdrop-blur-sm border animate-slide-in ${
              toast.type === "success"
                ? "bg-success/10 text-success border-success/30"
                : "bg-error/10 text-error border-error/30"
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}
