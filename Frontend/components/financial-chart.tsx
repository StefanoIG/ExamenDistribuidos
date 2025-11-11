"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { TrendingUp } from "lucide-react"

interface Transaction {
  date: string
  type: string
  amount: number
  newBalance: number
}

interface FinancialChartProps {
  transactions: Transaction[]
}

export default function FinancialChart({ transactions }: FinancialChartProps) {
  const chartData = transactions
    .slice()
    .reverse()
    .map((t) => ({
      date: t.date,
      balance: t.newBalance,
      amount: t.amount,
      type: t.type,
    }))

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 shadow-lg mt-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-600/20 rounded-lg">
          <TrendingUp className="h-5 w-5 text-blue-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Historial de Saldo</h3>
          <p className="text-xs text-slate-400">Evolución de tu balance en el tiempo</p>
        </div>
      </div>
      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
            <XAxis 
              dataKey="date" 
              stroke="rgba(148, 163, 184, 0.6)" 
              style={{ fontSize: "11px", fill: "#94a3b8" }}
              tick={{ fill: "#94a3b8" }}
            />
            <YAxis 
              stroke="rgba(148, 163, 184, 0.6)" 
              style={{ fontSize: "12px", fill: "#94a3b8" }}
              tick={{ fill: "#94a3b8" }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{ 
                backgroundColor: "rgba(30, 41, 59, 0.95)", 
                border: "1px solid rgba(148, 163, 184, 0.3)",
                borderRadius: "8px",
                color: "#ffffff"
              }}
              labelStyle={{ color: "#e2e8f0", fontWeight: "bold", marginBottom: "4px" }}
              formatter={(value) => [`$${typeof value === 'number' ? value.toFixed(2) : value}`, "Saldo"]}
            />
            <Legend 
              wrapperStyle={{ fontSize: "13px", color: "#e2e8f0" }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="balance"
              stroke="#60a5fa"
              dot={{ fill: "#60a5fa", r: 5, strokeWidth: 2, stroke: "#1e40af" }}
              activeDot={{ r: 7, fill: "#3b82f6", stroke: "#1e40af", strokeWidth: 2 }}
              strokeWidth={3}
              name="Saldo"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
