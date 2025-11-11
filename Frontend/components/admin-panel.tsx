"use client"

import { useState, useEffect } from "react"
import { Users as UsersIcon, Activity, Database, Users } from "lucide-react"

interface AdminPanelProps {
  cedula: string
}

interface ServerStats {
  clientes_activos: number
  operaciones_simultaneas: number
  conexiones_activas: number
}

export default function AdminPanel({ cedula }: AdminPanelProps) {
  const [isRunningSimulation, setIsRunningSimulation] = useState(false)
  const [stats, setStats] = useState<ServerStats>({
    clientes_activos: 0,
    operaciones_simultaneas: 0,
    conexiones_activas: 0
  })

  // Fetch stats from server
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("http://localhost:5001/api/stats")
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.estadisticas) {
            setStats({
              clientes_activos: data.estadisticas.clientes_activos || 0,
              operaciones_simultaneas: data.estadisticas.operaciones_simultaneas || 0,
              conexiones_activas: data.estadisticas.conexiones_activas || 0
            })
          }
        }
      } catch (error) {
        console.error("Error fetching stats:", error)
      }
    }

    // Initial fetch
    fetchStats()

    // Listen to WebSocket updates
    const handleStatsUpdate = (event: CustomEvent) => {
      const data = event.detail
      if (data.success && data.estadisticas) {
        setStats({
          clientes_activos: data.estadisticas.clientes_activos || 0,
          operaciones_simultaneas: data.estadisticas.operaciones_simultaneas || 0,
          conexiones_activas: data.estadisticas.conexiones_activas || 0
        })
      }
    }

    window.addEventListener("statsUpdate", handleStatsUpdate as EventListener)

    return () => {
      window.removeEventListener("statsUpdate", handleStatsUpdate as EventListener)
    }
  }, [])

  const handleRunSimulation = async () => {
    setIsRunningSimulation(true)
    try {
      // Call API endpoint that will execute socket_client.py
      const response = await fetch("http://localhost:5001/api/simulate", {
        method: "POST",
      })
      if (response.ok) {
        alert("Simulación iniciada correctamente. Revisa la consola del servidor.")
      } else {
        alert("Error al iniciar la simulación")
      }
    } catch (error) {
      console.error("Error running simulation:", error)
      alert("Error al conectar con el servidor")
    } finally {
      setIsRunningSimulation(false)
    }
  }

  return (
    <div className="mt-8 space-y-4">
      {/* Admin Title */}
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-amber-500/20 rounded-lg border border-amber-500/50">
          <UsersIcon className="h-5 w-5 text-amber-400" />
        </div>
        <h2 className="text-xl font-bold text-white">Panel de Administración</h2>
      </div>
      
      {/* Concurrency Indicators */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <Users className="h-5 w-5 text-blue-400" />
            <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
          </div>
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Clientes Conectados</p>
          <p className="text-2xl font-bold text-white mt-2">{stats.clientes_activos}</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <Activity className="h-5 w-5 text-amber-400" />
            <div className="w-2.5 h-2.5 bg-amber-400 rounded-full animate-pulse shadow-lg shadow-amber-400/50"></div>
          </div>
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Ops. Simultáneas</p>
          <p className="text-2xl font-bold text-white mt-2">{stats.operaciones_simultaneas}</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <Database className="h-5 w-5 text-purple-400" />
            <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-pulse shadow-lg shadow-purple-400/50"></div>
          </div>
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Conexiones Activas</p>
          <p className="text-2xl font-bold text-white mt-2">{stats.conexiones_activas}</p>
        </div>
      </div>

      {/* Simulation Button */}
      <button
        onClick={handleRunSimulation}
        disabled={isRunningSimulation}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 backdrop-blur-sm rounded-xl p-5 border border-blue-500/50 shadow-lg flex items-center justify-between hover:from-blue-700 hover:to-purple-700 transition-all group disabled:opacity-50"
      >
        <div className="flex items-center gap-3">
          <Users className="h-6 w-6 text-white" />
          <div className="text-left">
            <p className="text-sm font-semibold text-white">Demostración de Concurrencia</p>
            <p className="text-xs text-blue-100">
              {isRunningSimulation ? "Ejecutando pruebas de concurrencia..." : "Probar operaciones simultáneas en múltiples cuentas"}
            </p>
          </div>
        </div>
        <span className="text-white text-lg">▶</span>
      </button>
    </div>
  )
}
