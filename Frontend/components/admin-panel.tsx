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

interface SimulationSummary {
  totalOperations: number
  deposits: number
  withdrawals: number
  errors: number
  avgMs: number
  minMs: number
  maxMs: number
}

interface SimulationOperation {
  thread: string
  cedula: string
  operation: string
  amount: number
  durationMs: number
  timestamp: string
  status: "success" | "error"
  message?: string | null
  newBalance?: number | null
}

export default function AdminPanel({ cedula }: AdminPanelProps) {
  const [isRunningSimulation, setIsRunningSimulation] = useState(false)
  const [stats, setStats] = useState<ServerStats>({
    clientes_activos: 0,
    operaciones_simultaneas: 0,
    conexiones_activas: 0
  })
  const [simulationSummary, setSimulationSummary] = useState<SimulationSummary | null>(null)
  const [recentOperations, setRecentOperations] = useState<SimulationOperation[]>([])
  const [simulationError, setSimulationError] = useState<string | null>(null)
  const [lastSimulationAt, setLastSimulationAt] = useState<string | null>(null)

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
    setSimulationError(null)
    try {
      // Call API endpoint that executes the concurrency demo and returns results
      const response = await fetch("http://localhost:5001/api/simulate", {
        method: "POST",
      })
      const data = await response.json()

      if (response.ok && data.success) {
        const summary = data.summary ?? {}
        const tiempos = summary.tiempos_ms ?? {}

        setSimulationSummary({
          totalOperations: summary.total_operaciones ?? 0,
          deposits: summary.depositos ?? 0,
          withdrawals: summary.retiros ?? 0,
          errors: summary.errores ?? 0,
          avgMs: tiempos.promedio ?? 0,
          minMs: tiempos.minimo ?? 0,
          maxMs: tiempos.maximo ?? 0,
        })

        const operations = Array.isArray(data.operations) ? data.operations : []
        const mappedOperations: SimulationOperation[] = operations
          .slice(-6)
          .reverse()
          .map((operation: Record<string, unknown>) => ({
            thread: (operation.thread as string) || "-",
            cedula: (operation.cedula as string) || "-",
            operation: (operation.operacion as string) || "-",
            amount: Number(operation.monto) || 0,
            durationMs: Number(operation.duracion_ms) || 0,
            timestamp: (operation.timestamp as string) || "",
            status: (operation.estado as string) === "error" ? "error" : "success",
            message: (operation.mensaje as string) || null,
            newBalance: operation.nuevo_saldo !== undefined && operation.nuevo_saldo !== null
              ? Number(operation.nuevo_saldo)
              : null,
          }))

        setRecentOperations(mappedOperations)
        setLastSimulationAt(new Date().toISOString())
      } else {
        setSimulationError((data && data.error) || "Error al ejecutar la simulación")
      }
    } catch (error) {
      console.error("Error running simulation:", error)
      setSimulationError("Error al conectar con el servidor")
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

      {simulationError && (
        <div className="mt-4 bg-error/10 text-error border border-error/30 rounded-xl p-4 text-sm">
          {simulationError}
        </div>
      )}

      {simulationSummary && (
        <div className="mt-4 bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 shadow-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Resultados de la simulación</h3>
              <p className="text-xs text-slate-400">Resumen de las últimas pruebas ejecutadas</p>
            </div>
            {lastSimulationAt && (
              <span className="text-xs text-slate-500">
                Actualizado: {new Date(lastSimulationAt).toLocaleTimeString()}
              </span>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Operaciones totales</p>
              <p className="text-2xl font-bold text-white mt-1">{simulationSummary.totalOperations}</p>
            </div>
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Depósitos / Retiros</p>
              <p className="text-lg font-semibold text-white mt-1">
                {simulationSummary.deposits} / {simulationSummary.withdrawals}
              </p>
            </div>
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Operaciones con error</p>
              <p className={`text-lg font-semibold mt-1 ${simulationSummary.errors > 0 ? "text-error" : "text-success"}`}>
                {simulationSummary.errors}
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Tiempo promedio</p>
              <p className="text-lg font-semibold text-white mt-1">{simulationSummary.avgMs.toFixed(1)} ms</p>
            </div>
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Tiempo mínimo</p>
              <p className="text-lg font-semibold text-white mt-1">{simulationSummary.minMs.toFixed(1)} ms</p>
            </div>
            <div className="bg-slate-900/40 rounded-lg border border-slate-700 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">Tiempo máximo</p>
              <p className="text-lg font-semibold text-white mt-1">{simulationSummary.maxMs.toFixed(1)} ms</p>
            </div>
          </div>

          {recentOperations.length > 0 && (
            <div className="mt-6">
              <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Últimas operaciones registradas</p>
              <div className="space-y-2">
                {recentOperations.map((operation) => (
                  <div
                    key={`${operation.timestamp}-${operation.thread}-${operation.cedula}`}
                    className="bg-slate-900/30 border border-slate-700 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between text-sm text-slate-300">
                      <span className="font-mono text-xs text-slate-400">{operation.timestamp}</span>
                      <span className="font-semibold text-white">
                        {operation.operation === "DEPOSITO" ? "Depósito" : "Retiro"}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-200">
                      <span>Cuenta: <span className="font-mono">{operation.cedula}</span></span>
                      <span>Monto: ${operation.amount.toFixed(2)}</span>
                      <span>Duración: {operation.durationMs.toFixed(1)} ms</span>
                      {operation.newBalance !== null && operation.newBalance !== undefined && (
                        <span>Nuevo saldo: ${operation.newBalance.toFixed(2)}</span>
                      )}
                      {operation.status === "error" && operation.message && (
                        <span className="text-error">{operation.message}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
