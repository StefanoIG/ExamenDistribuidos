"use client"

import type React from "react"

import { useState } from "react"
import { useSocket } from "@/context/socket-context"
import { LogIn, Loader2 } from "lucide-react"

interface LoginScreenProps {
  onLoginSuccess: (cedula: string) => void
}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [cedula, setCedula] = useState("")
  const [error, setError] = useState("")
  const { sendSocketMessage, isLoading } = useSocket()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!cedula.trim()) {
      setError("Por favor ingresa tu número de cédula")
      return
    }

    if (!/^\d+$/.test(cedula)) {
      setError("La cédula debe contener solo números")
      return
    }

    try {
      const response = await sendSocketMessage("LOGIN", cedula)
      if (response && typeof response === "object" && "success" in response && response.success) {
        onLoginSuccess(cedula)
      } else if (response && typeof response === "object" && "message" in response) {
        setError(response.message as string)
      } else {
        setError("Error al validar la cédula")
      }
    } catch (err) {
      setError("Error al conectar con el servidor")
      console.error(err)
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center">
            <div className="rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 p-4 shadow-lg">
              <LogIn className="h-10 w-10 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">Cajero ATM</h1>
          <p className="text-sm text-slate-400">Sistema Distribuido de Banca</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="cedula" className="block text-sm font-medium text-slate-300 mb-3">
              Número de Cédula
            </label>
            <input
              id="cedula"
              type="text"
              value={cedula}
              onChange={(e) => setCedula(e.target.value)}
              placeholder="Ej: 1234567890"
              disabled={isLoading}
              className="w-full rounded-xl bg-slate-700/50 border border-slate-600 px-4 py-3 text-white text-lg placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all"
            />
            {error && (
              <div className="mt-3 bg-rose-600/20 border border-rose-500/50 rounded-lg p-3">
                <p className="text-sm text-rose-400">{error}</p>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3.5 font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-blue-600/20"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 smooth-spin" />
                Conectando...
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                Ingresar
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-400 bg-slate-700/30 rounded-lg p-3 border border-slate-600">
          💡 Ingresa tu número de cédula para acceder al sistema
        </p>
      </div>
    </div>
  )
}
