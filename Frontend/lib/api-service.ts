/**
 * Servicio de API para comunicarse con el bridge Flask
 * Usado por el frontend Next.js
 */

// En Next.js, las variables NEXT_PUBLIC_ están disponibles en tiempo de build
const API_BASE_URL: string = 'http://localhost:5001/api'

export interface ClienteData {
  cedula: string
  nombres: string
  apellidos: string
  saldo: number
}

export interface TransactionData {
  tipo: 'DEPOSITO' | 'RETIRO'
  monto: number
  saldo_final: number
  fecha: string
}

export interface ApiResponse {
  success: boolean
  action?: string
  data?: any
  error?: string
  detalles?: string
}

class ApiService {
  async request(endpoint: string, method: string = 'GET', body?: any): Promise<ApiResponse> {
    try {
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      }

      if (body) {
        options.body = JSON.stringify(body)
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, options)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `HTTP Error: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error(`Error en ${endpoint}:`, error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error desconocido',
      }
    }
  }

  async consultar(cedula: string): Promise<ApiResponse> {
    return this.request('/consulta', 'POST', { cedula })
  }

  async depositar(cedula: string, monto: number): Promise<ApiResponse> {
    return this.request('/deposito', 'POST', { cedula, monto })
  }

  async retirar(cedula: string, monto: number): Promise<ApiResponse> {
    return this.request('/retiro', 'POST', { cedula, monto })
  }

  async crearCliente(cedula: string, nombres: string, apellidos: string, saldo: number): Promise<ApiResponse> {
    return this.request('/cliente', 'POST', { cedula, nombres, apellidos, saldo })
  }

  async obtenerHistorial(cedula: string): Promise<ApiResponse> {
    return this.request(`/historial/${cedula}`, 'GET')
  }

  async obtenerStats(): Promise<ApiResponse> {
    return this.request('/stats', 'GET')
  }
}

export const apiService = new ApiService()
