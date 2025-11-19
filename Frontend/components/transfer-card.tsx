"use client"

import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { useSocket } from "@/context/socket-context"
import { ArrowLeftRight, Loader2 } from "lucide-react"

interface TransferCardProps {
  currentCedula: string
  currentBalance: number
  onTransferComplete?: () => void
}

export function TransferCard({ currentCedula, currentBalance, onTransferComplete }: TransferCardProps) {
  const [cedulaDestino, setCedulaDestino] = useState("")
  const [monto, setMonto] = useState("")
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const { sendSocketMessage } = useSocket()

  const handleTransfer = async () => {
    const amount = parseFloat(monto)
    
    if (!cedulaDestino || !monto) {
      toast({
        title: "Error",
        description: "Por favor complete todos los campos",
        variant: "destructive",
      })
      return
    }

    if (isNaN(amount) || amount <= 0) {
      toast({
        title: "Error",
        description: "El monto debe ser mayor a 0",
        variant: "destructive",
      })
      return
    }

    if (amount > currentBalance) {
      toast({
        title: "Error",
        description: "Saldo insuficiente para realizar la transferencia",
        variant: "destructive",
      })
      return
    }

    if (cedulaDestino === currentCedula) {
      toast({
        title: "Error",
        description: "No puedes transferir a tu propia cuenta",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    try {
      const result = await sendSocketMessage("TRANSFER", {
        cedula_origen: currentCedula,
        cedula_destino: cedulaDestino,
        amount
      }) as { success?: boolean; error?: string; detalles?: any }
      
      console.log("Resultado de transferencia:", result)
      
      if (result && result.success === true) {
        toast({
          title: "✅ Transferencia exitosa",
          description: `$${amount.toFixed(2)} transferidos a ${cedulaDestino}`,
          className: "bg-emerald-600 border-emerald-500 text-white",
        })
        setCedulaDestino("")
        setMonto("")
        onTransferComplete?.()
      } else {
        // Mostrar error específico
        const errorMsg = (result && result.error) || "No se pudo completar la transferencia"
        toast({
          title: "❌ Error en transferencia",
          description: errorMsg,
          variant: "destructive",
          className: "bg-rose-600 border-rose-500 text-white",
        })
        console.error("Error de transferencia:", errorMsg, result)
      }
    } catch (error) {
      toast({
        title: "❌ Error de conexión",
        description: "No se pudo conectar con el servidor",
        variant: "destructive",
        className: "bg-rose-600 border-rose-500 text-white",
      })
      console.error("Error en catch:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 shadow-lg">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-blue-500/20 rounded-lg border border-blue-500/50">
            <ArrowLeftRight className="h-5 w-5 text-blue-400" />
          </div>
          <h3 className="text-xl font-bold text-white">Transferir a Otra Cuenta</h3>
        </div>
        <p className="text-sm text-slate-400 ml-12">
          Saldo disponible: <span className="text-emerald-400 font-semibold">${currentBalance.toFixed(2)}</span>
        </p>
      </div>
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="cedula-destino" className="block text-sm font-medium text-slate-300">
            Cédula Destino
          </label>
          <input
            id="cedula-destino"
            type="text"
            placeholder="Cédula de la cuenta destino"
            value={cedulaDestino}
            onChange={(e) => setCedulaDestino(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl bg-slate-700/50 border border-slate-600 px-4 py-3 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="monto-transferencia" className="block text-sm font-medium text-slate-300">
            Monto a Transferir
          </label>
          <input
            id="monto-transferencia"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl bg-slate-700/50 border border-slate-600 px-4 py-3 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all"
          />
        </div>
        <button
          onClick={handleTransfer}
          disabled={loading}
          className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg mt-6"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Transfiriendo...
            </>
          ) : (
            <>
              <ArrowLeftRight className="h-4 w-4" />
              Transferir
            </>
          )}
        </button>
      </div>
    </div>
  )
}
