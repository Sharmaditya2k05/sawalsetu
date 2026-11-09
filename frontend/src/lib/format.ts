/** Indian-style rupee formatting: ₹12,34,567 and short forms like ₹12.3 L / ₹1.2 Cr. */
export function inr(value: number | null | undefined, opts: { short?: boolean } = {}): string {
  if (value == null || Number.isNaN(value)) return '—'
  const abs = Math.abs(value)
  const sign = value < 0 ? '−' : ''
  if (opts.short) {
    if (abs >= 1e7) return `${sign}₹${(abs / 1e7).toFixed(2)} Cr`
    if (abs >= 1e5) return `${sign}₹${(abs / 1e5).toFixed(1)} L`
  }
  return `${sign}₹${new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(abs)}`
}

export function relativeTime(iso: string | null): string {
  if (!iso) return 'never'
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.round(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h} h ago`
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export function pct(a: number, b: number): number | null {
  if (!b) return null
  return ((a - b) / b) * 100
}

export const KIND_LABEL: Record<string, string> = {
  analytics: 'Summary',
  sale_bill: 'Sales invoice',
  sale_order: 'Sales order',
  sale_challan: 'Delivery challan',
  purchase_bill: 'Purchase bill',
  purchase_order: 'Purchase order',
  purchase_challan: 'Purchase challan',
  purchase_return: 'Purchase return',
  ledger: 'Party master',
  item: 'Item master',
  ecom_order: 'Marketplace order',
}
