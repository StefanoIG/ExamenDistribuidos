"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { useSocket } from "@/context/socket-context"
import { UserPlus } from "lucide-react"

export function CreateAccountCard() {
  const [cedula, setCedula] = useState("")
  const [nombre, setNombre] = useState("")
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const { sendSocketMessage } = useSocket()

  const handleCreateAccount = async () => {
    if (!cedula || !nombre) {
      toast({
        title: "Error",
        description: "Por favor complete todos los campos",
        variant: "destructive",
      })
      return
    }

    if (!cedula.startsWith("0")) {
      toast({
        title: "Error",
        description: "La cédula debe comenzar con 0",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    try {
      const result = await sendSocketMessage("CREATE_ACCOUNT", { cedula, nombre })
      
      if (result.success) {
        toast({
          title: "✅ Cuenta creada",
          description: `Cuenta creada para ${nombre} con cédula ${cedula}`,
        })
        setCedula("")
        setNombre("")
      } else {
        toast({
          title: "Error",
          description: result.error || "No se pudo crear la cuenta",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Error al crear la cuenta",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserPlus className="h-5 w-5" />
          Crear Nueva Cuenta
        </CardTitle>
        <CardDescription>
          Registra una nueva cuenta bancaria. La cédula debe comenzar con 0 y el saldo inicial será $0.00
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="cedula-nueva">Cédula (debe comenzar con 0)</Label>
          <Input
            id="cedula-nueva"
            type="text"
            placeholder="0123456789"
            value={cedula}
            onChange={(e) => setCedula(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="nombre-completo">Nombre Completo</Label>
          <Input
            id="nombre-completo"
            type="text"
            placeholder="Juan Pérez García"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            disabled={loading}
          />
        </div>
        <Button 
          onClick={handleCreateAccount} 
          disabled={loading}
          className="w-full"
        >
          {loading ? "Creando..." : "Crear Cuenta"}
        </Button>
      </CardContent>
    </Card>
  )
}
