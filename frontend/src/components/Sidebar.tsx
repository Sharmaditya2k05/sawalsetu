import { RefreshCw, Sparkles, Database, Cpu, Settings2 } from 'lucide-react'
import type { Status } from '../types'
import { relativeTime } from '../lib/format'

interface Props {
  status: Status | null
  suggestions: string[]
  syncing: boolean
  onSync: () => void
  onAsk: (q: string) => void
  syncError?: string | null
}

const COUNT_ROWS: [string, string][] = [
  ['sale_bills', 'Sales invoices'],
  ['purchase_bills', 'Purchase bills'],
  ['sale_orders', 'Sales orders'],
  ['ecom_orders', 'Marketplace orders'],
  ['ledgers', 'Parties'],
  ['items', 'Items'],
]

export function Wordmark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <span className="grid h-9 w-9 place-items-center rounded-[10px] bg-emerald text-paper shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]">
        <svg viewBox="0 0 32 32" className="h-6 w-6" aria-hidden>
          <path d="M8 21c3-7 13-7 16 0" stroke="currentColor" strokeWidth="2.4" fill="none" strokeLinecap="round" />
          <circle cx="16" cy="11.5" r="2.3" fill="#E0862B" />
        </svg>
      </span>
      <div className="leading-none">
        <div className="font-display text-[22px] font-medium tracking-tight">SawalSetu</div>
        {!compact && (
          <div className="mt-1 text-[10.5px] font-medium uppercase tracking-[0.18em] text-ink-muted">Ask your books</div>
        )}
      </div>
    </div>
  )
}

export default function Sidebar({ status, suggestions, syncing, onSync, onAsk, syncError }: Props) {
  const live = status?.mode === 'live'
  return (
    <aside className="flex h-full flex-col gap-7 overflow-y-auto border-r border-hairline bg-paper-2 px-6 py-6">
      <Wordmark />

      <section className="rounded-lg border border-hairline bg-paper p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
            <Database className="h-3.5 w-3.5" /> Data source
          </div>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium ${
              status?.ready ? 'bg-emerald-tint text-emerald' : 'bg-saffron-tint text-saffron'
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${status?.ready ? 'bg-emerald' : 'bg-saffron'}`} />
            {syncing ? 'Syncing…' : status?.ready ? `Synced ${relativeTime(status.last_sync)}` : 'Not synced'}
          </span>
        </div>
        <div className="mb-3">
          <div className="font-display text-[17px] leading-tight">MargBooks</div>
          <div className="mt-0.5 text-[12px] text-ink-muted">
            {live ? 'Open API · live' : 'Demo dataset · MargBooks schema'}
          </div>
        </div>
        <ul className="space-y-1.5 text-[13px]">
          {COUNT_ROWS.map(([key, label]) => (
            <li key={key} className="leaders">
              <span className="text-ink-muted">{label}</span>
              <span className="tabular font-mono text-[12.5px]">{(status?.counts?.[key] ?? 0).toLocaleString('en-IN')}</span>
            </li>
          ))}
        </ul>
        <button
          onClick={onSync}
          disabled={syncing}
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md border border-hairline bg-paper-2 px-3 py-2 text-[13px] font-medium text-ink transition hover:border-emerald hover:text-emerald disabled:opacity-60"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Pulling from MargBooks' : 'Sync now'}
        </button>
        {syncError && <p className="mt-2 text-[12px] leading-snug text-red">{syncError}</p>}
      </section>

      <section>
        <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
          <Sparkles className="h-3.5 w-3.5" /> Ask about
        </div>
        <div className="flex flex-col gap-2">
          {suggestions.map((q) => (
            <button
              key={q}
              onClick={() => onAsk(q)}
              className="rounded-full border border-hairline bg-paper px-3.5 py-2 text-left text-[13px] leading-snug text-ink transition hover:border-emerald hover:bg-emerald-tint"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      <div className="mt-auto space-y-3 pt-2">
        <div className="flex items-center gap-2 text-[12px] text-ink-muted">
          <Cpu className="h-3.5 w-3.5" />
          {status?.llm.provider === 'claude' ? (
            <span>
              Answers by <span className="font-medium text-ink">{status.llm.model}</span>
            </span>
          ) : (
            <span>
              Offline mode · <span className="font-medium text-ink">set ANTHROPIC_API_KEY</span>
            </span>
          )}
        </div>
        <div className="flex items-center justify-between text-[12px] text-ink-muted">
          <span>
            {status?.company ?? '—'} · FY {fyLabel()}
          </span>
          <Settings2 className="h-4 w-4 opacity-60" />
        </div>
      </div>
    </aside>
  )
}

function fyLabel() {
  const d = new Date()
  const start = d.getMonth() + 1 >= 4 ? d.getFullYear() : d.getFullYear() - 1
  return `${start}-${String(start + 1).slice(-2)}`
}
