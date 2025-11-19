"use client"

import type React from "react"
import { createContext, useContext, useCallback, useState, useEffect, useRef } from "react"
import { io, Socket } from "socket.io-client"

interface SocketContextType {
  sendSocketMessage: (type: string, data: unknown) => Promise<unknown>
  isLoading: boolean
  socket: Socket | null
  isConnected: boolean
}

const SocketContext = createContext<SocketContextType | undefined>(undefined)

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isMounted, setIsMounted] = useState(false)
  const socketRef = useRef<Socket | null>(null)

  // Evitar hidratación mismatch - solo inicializar después del montaje
  useEffect(() => {
    setIsMounted(true)
  }, [])

  useEffect(() => {
    // Solo inicializar WebSocket en el cliente después del montaje
    if (!isMounted) return

    // Inicializar WebSocket
    const newSocket = io("http://localhost:5001", {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })

    newSocket.on("connect", () => {
      console.log("✅ WebSocket conectado")
      setIsConnected(true)
    })

    newSocket.on("disconnect", () => {
      console.log("❌ WebSocket desconectado")
      setIsConnected(false)
    })

    newSocket.on("balance_updated", (data: { cedula: string; balance: number }) => {
      console.log("💰 Balance actualizado:", data)
      // Emitir evento personalizado para que los componentes se actualicen
      window.dispatchEvent(new CustomEvent("balanceUpdate", { detail: data }))
    })

    newSocket.on("transactions_updated", (data: { cedula: string; transactions: unknown[] }) => {
      console.log("📜 Transacciones actualizadas:", data)
      window.dispatchEvent(new CustomEvent("transactionsUpdate", { detail: data }))
    })

    newSocket.on("stats_updated", (data: unknown) => {
      console.log("📊 Stats actualizadas:", data)
      window.dispatchEvent(new CustomEvent("statsUpdate", { detail: data }))
    })

    socketRef.current = newSocket

    return () => {
      newSocket.disconnect()
    }
  }, [isMounted])

  const sendSocketMessage = useCallback(async (type: string, data: unknown) => {
    setIsLoading(true)
    try {
      const API_URL = "http://localhost:5001"

      // Mapear tipos de mensajes a endpoints de API
      let endpoint = ""
      let method = "POST"
      let body: Record<string, unknown> = {}

      if (typeof data === "string") {
        // Para LOGIN - consulta simple
        if (type === "LOGIN") {
          endpoint = "/api/consulta"
          body = { cedula: data }
        }
      } else if (typeof data === "object" && data !== null) {
        const dataObj = data as Record<string, unknown>
        
        switch (type) {
          case "CHECK_BALANCE":
            endpoint = "/api/consulta"
            body = { cedula: dataObj.cedula as string }
            break
          case "DEPOSIT":
            endpoint = "/api/deposito"
            body = { cedula: dataObj.cedula as string, monto: dataObj.amount as number }
            break
          case "WITHDRAW":
            endpoint = "/api/retiro"
            body = { cedula: dataObj.cedula as string, monto: dataObj.amount as number }
            break
          case "GET_TRANSACTIONS":
            endpoint = `/api/historial/${dataObj.cedula as string}`
            method = "GET"
            break
          default:
            break
        }
      }

      if (!endpoint) {
        return { success: false, message: "Tipo de mensaje no soportado" }
      }

      const url = `${API_URL}${endpoint}`
      const options: RequestInit = {
        method,
        headers: { "Content-Type": "application/json" },
      }

      if (method === "POST") {
        options.body = JSON.stringify(body)
      }

      const response = await fetch(url, options)
      const result = await response.json()

      // La API devuelve { success: boolean, data: {...}, error?: string }
      if (result.success && result.data) {
        if (type === "LOGIN") {
          // CONSULTA devuelve: { nombres, apellidos, saldo }
          const clientData = result.data as Record<string, unknown>
          const cedulaStr = typeof data === 'string' ? data : ''
          const isAdmin = cedulaStr === '1350509525' // Stefano Aguilar es admin
          
          return {
            success: true,
            user: {
              name: `${clientData.nombres} ${clientData.apellidos}`,
              cedula: data,
              balance: clientData.saldo || 0,
              role: isAdmin ? "admin" : "user",
            },
          }
        } else if (type === "CHECK_BALANCE") {
          const clientData = result.data as Record<string, unknown>
          return {
            success: true,
            balance: clientData.saldo || 0,
          }
        } else if (type === "DEPOSIT" || type === "WITHDRAW") {
          const txData = result.data as Record<string, unknown>
          return {
            success: true,
            newBalance: txData.nuevo_saldo || 0,
            message: txData.mensaje || "Operación exitosa",
          }
        } else if (type === "GET_TRANSACTIONS") {
          const txData = result.data as Record<string, unknown>
          const rawTransactions = txData.transacciones as Array<Record<string, unknown>>
          
          // Mapear formato de API a formato del frontend
          const mappedTransactions = rawTransactions.map((tx: Record<string, unknown>) => ({
            date: tx.fecha as string,
            type: tx.tipo as string,
            amount: tx.monto as number,
            newBalance: tx.saldo_final as number,
          }))
          
          return {
            success: true,
            transactions: mappedTransactions,
          }
        }
      }

      return { success: false, message: result.error || "Error en operación" }
    } catch (error) {
      console.error("Socket error:", error)
      return { success: false, message: "Error conectando al servidor" }
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <SocketContext.Provider 
      value={{ 
        sendSocketMessage, 
        isLoading, 
        socket: socketRef.current, 
        isConnected 
      }}
    >
      {children}
    </SocketContext.Provider>
  )
}

export function useSocket() {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error("useSocket must be used within SocketProvider")
  }
  return context
}