"use client"

import { useState } from "react"
import LoginScreen from "@/components/login-screen"
import Dashboard from "@/components/dashboard"
import { SocketProvider } from "@/context/socket-context"

type AppState = "login" | "dashboard"

export default function Home() {
  const [appState, setAppState] = useState<AppState>("login")
  const [userCedula, setUserCedula] = useState<string>("")

  const handleLoginSuccess = (cedula: string) => {
    setUserCedula(cedula)
    setAppState("dashboard")
  }

  const handleLogout = () => {
    setUserCedula("")
    setAppState("login")
  }

  return (
    <SocketProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        {appState === "login" ? (
          <LoginScreen onLoginSuccess={handleLoginSuccess} />
        ) : (
          <Dashboard cedula={userCedula} onLogout={handleLogout} />
        )}
      </div>
    </SocketProvider>
  )
}
