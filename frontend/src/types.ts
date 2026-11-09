export interface Status {
  company: string
  mode: 'demo' | 'live'
  source: string
  base_url: string | null
  llm: { provider: 'claude' | 'offline'; model: string | null }
  embeddings: string
  documents: number
  last_sync: string | null
  sync_window: { from: string; to: string } | null
  counts: Record<string, number>
  syncing: boolean
  ready: boolean
}

export interface MonthPoint {
  month: string
  label: string
  sales: number
  purchases: number
  invoices: number
}

export interface Metrics {
  total_sales: number
  total_purchases: number
  receivables: number
  payables: number
  invoices: number
  customers: number
  suppliers: number
  items: number
  mtd_sales: number
  last_month_sales: number
  last_month_label: string | null
  prev_month_sales: number
  prev_month_label: string | null
  this_month_label: string
  monthly: MonthPoint[]
  top_customers: { party: string; total: number }[]
  receivables_rows: { party: string; pending: number; overdue: number; invoices: number; oldest: string | null }[]
  ageing: { bucket: string; amount: number; invoices: number }[]
}

export interface Source {
  n: number
  id: string
  title: string
  kind: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  streaming?: boolean
  error?: string
  model?: string | null
  at: number
}
