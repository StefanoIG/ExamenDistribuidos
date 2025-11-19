"use client"

import type React from "react"

import { useState } from "react"
import { useSocket } from "@/context/socket-context"
import { LogIn, Loader2, UserPlus } from "lucide-react"

interface LoginScreenProps {
  onLoginSuccess: (cedula: string) => void
}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [cedula, setCedula] = useState("")
  const [nombre, setNombre] = useState("")
  const [error, setError] = useState("")
  const [isCreateMode, setIsCreateMode] = useState(false)
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

    if (isCreateMode) {
      // Modo crear cuenta
      if (!nombre.trim()) {
        setError("Por favor ingresa tu nombre completo")
        return
      }

      if (!cedula.startsWith("0")) {
        setError("La cédula debe comenzar con 0 para cuentas nuevas")
        return
      }

      try {
        const response = await sendSocketMessage("CREATE_ACCOUNT", { cedula, nombre })
        if (response && typeof response === "object" && "success" in response && response.success) {
          setError("")
          setIsCreateMode(false)
          setNombre("")
          // Mostrar mensaje de éxito y cambiar a modo login
          setError("") // Limpiar error para mostrar mensaje de éxito
          setTimeout(() => {
            setError("✅ Cuenta creada exitosamente. Ya puedes ingresar con tu cédula.")
          }, 100)
        } else if (response && typeof response === "object" && "error" in response) {
          setError(response.error as string)
        } else {
          setError("Error al crear la cuenta")
        }
      } catch (err) {
        setError("Error al conectar con el servidor")
        console.error(err)
      }
    } else {
      // Modo login normal
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
              {isCreateMode ? "Número de Cédula (debe comenzar con 0)" : "Número de Cédula"}
            </label>
            <input
              id="cedula"
              type="text"
              value={cedula}
              onChange={(e) => setCedula(e.target.value)}
              placeholder={isCreateMode ? "Ej: 0123456789" : "Ej: 1234567890"}
              disabled={isLoading}
              className="w-full rounded-xl bg-slate-700/50 border border-slate-600 px-4 py-3 text-white text-lg placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all"
            />
          </div>

          {isCreateMode && (
            <div>
              <label htmlFor="nombre" className="block text-sm font-medium text-slate-300 mb-3">
                Nombre Completo
              </label>
              <input
                id="nombre"
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej: Juan Pérez García"
                disabled={isLoading}
                className="w-full rounded-xl bg-slate-700/50 border border-slate-600 px-4 py-3 text-white text-lg placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 transition-all"
              />
            </div>
          )}

          {error && (
            <div className={`mt-3 ${error.startsWith("✅") ? "bg-emerald-600/20 border-emerald-500/50" : "bg-rose-600/20 border-rose-500/50"} border rounded-lg p-3`}>
              <p className={`text-sm ${error.startsWith("✅") ? "text-emerald-400" : "text-rose-400"}`}>{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3.5 font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-blue-600/20"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 smooth-spin" />
                {isCreateMode ? "Creando..." : "Conectando..."}
              </>
            ) : (
              <>
                {isCreateMode ? <UserPlus className="h-4 w-4" /> : <LogIn className="h-4 w-4" />}
                {isCreateMode ? "Crear Cuenta" : "Ingresar"}
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setIsCreateMode(!isCreateMode)
              setError("")
              setNombre("")
            }}
            disabled={isLoading}
            className="w-full rounded-xl bg-slate-700/50 border border-slate-600 text-slate-300 py-2.5 font-medium hover:bg-slate-700 disabled:opacity-50 transition-all duration-200 flex items-center justify-center gap-2"
          >
            {isCreateMode ? (
              <>
                <LogIn className="h-4 w-4" />
                Ya tengo cuenta
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" />
                Crear nueva cuenta
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-400 bg-slate-700/30 rounded-lg p-3 border border-slate-600">
          💡 {isCreateMode ? "Las cuentas nuevas inician con saldo $0.00" : "Ingresa tu número de cédula para acceder al sistema"}
        </p>
      </div>
    </div>
  )
}
