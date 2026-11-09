import { useEffect, useRef } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Metrics, Source } from '../types'
import { inr, KIND_LABEL, pct } from '../lib/format'

interface Props {
  metrics: Metrics | null
  sources: Source[]
  activeCitation: number | null
  onCitation: (n: number | null, pin?: boolean) => void
}

export default function EvidencePanel({ metrics, sources, activeCitation, onCitation }: Props) {
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (activeCitation == null || !listRef.current) return
    const el = listRef.current.querySelector<HTMLElement>(`[data-n="${activeCitation}"]`)
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [activeCitation])

  const delta = metrics ? pct(metrics.last_month_sales, metrics.prev_month_sales) : null
  const shortMonth = (label: string | null | undefined) => (label ? label.slice(0, 3) + label.slice(label.length - 5) : '')

  return (
    <aside className="flex h-full flex-col overflow-hidden border-l border-hairline bg-paper">
      <div className="border-b border-hairline px-5 py-4">
        <div className="grid grid-cols-3 gap-3">
          <Kpi
            label={metrics?.last_month_label ? `Sales ${shortMonth(metrics.last_month_label)}` : 'Sales'}
            value={inr(metrics?.last_month_sales, { short: true })}
            delta={delta}
            hint={metrics?.prev_month_label ? `vs ${shortMonth(metrics.prev_month_label)}` : undefined}
          />
          <Kpi label="Receivables" value={inr(metrics?.receivables, { short: true })} tone="warn" />
          <Kpi label="Payables" value={inr(metrics?.payables, { short: true })} />
        </div>
        {metrics && (
          <div className="mt-2 text-[11px] text-ink-faint">
            Month to date ({shortMonth(metrics.this_month_label)}): <span className="tabular text-ink-muted">{inr(metrics.mtd_sales)}</span>
          </div>
        )}
        <div className="mt-4">
          <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-ink-muted">
            <span>12 months</span>
            <span className="flex items-center gap-3 normal-case tracking-normal">
              <Legend color="var(--color-emerald)" label="Sales" />
              <Legend color="var(--color-saffron)" label="Purchases" />
            </span>
          </div>
          <div className="h-[120px] w-full">
            {metrics?.monthly?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.monthly} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
                  <XAxis
                    dataKey="label"
                    tickLine={false}
                    axisLine={{ stroke: 'var(--color-hairline)', strokeDasharray: '2 3' }}
                    tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'var(--color-ink-faint)' }}
                    interval={2}
                  />
                  <YAxis hide domain={['auto', 'auto']} />
                  <Tooltip
                    cursor={{ stroke: 'var(--color-hairline)' }}
                    content={({ active, payload, label }) =>
                      active && payload?.length ? (
                        <div className="rounded-md border border-hairline bg-paper px-3 py-2 text-[12px] shadow-sm">
                          <div className="mb-1 font-mono text-ink-muted">{label}</div>
                          {payload.map((p) => (
                            <div key={String(p.dataKey)} className="flex justify-between gap-4 tabular">
                              <span className="capitalize">{String(p.dataKey)}</span>
                              <span className="font-medium">{inr(Number(p.value))}</span>
                            </div>
                          ))}
                        </div>
                      ) : null
                    }
                  />
                  <Line type="monotone" dataKey="sales" stroke="var(--color-emerald)" strokeWidth={1.75} dot={false} activeDot={{ r: 3 }} isAnimationActive={false} />
                  <Line type="monotone" dataKey="purchases" stroke="var(--color-saffron)" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center text-[12px] text-ink-faint">Sync to see the trend</div>
            )}
          </div>
        </div>
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto px-5 py-4">
        <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
          {sources.length ? 'Sources for this answer' : 'Evidence'}
        </div>
        {sources.length === 0 ? (
          <TopDebtors metrics={metrics} />
        ) : (
          <ol className="space-y-2">
            {sources.map((s) => (
              <li
                key={s.id}
                data-n={s.n}
                onMouseEnter={() => onCitation(s.n)}
                onMouseLeave={() => onCitation(null)}
                onClick={() => onCitation(s.n, true)}
                className={`source-card cursor-pointer rounded-md border border-hairline bg-paper px-3 py-2.5 transition hover:border-emerald ${activeCitation === s.n ? 'is-active' : ''}`}
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className="grid h-5 min-w-5 place-items-center rounded border border-emerald px-1 font-mono text-[10.5px] text-emerald">{s.n}</span>
                  <span className="text-[10.5px] font-medium uppercase tracking-[0.12em] text-ink-muted">{KIND_LABEL[s.kind] ?? s.kind}</span>
                </div>
                <div className="text-[13px] font-medium leading-snug">{s.title}</div>
                <p className="mt-1 line-clamp-3 text-[12.5px] leading-relaxed text-ink-muted">{highlightNumbers(s.text)}</p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </aside>
  )
}

function Kpi({ label, value, delta, hint, tone }: { label: string; value: string; delta?: number | null; hint?: string; tone?: 'warn' }) {
  return (
    <div className="min-w-0">
      <div className="truncate text-[10.5px] font-semibold uppercase tracking-[0.14em] text-ink-muted">{label}</div>
      <div className={`font-display tabular mt-1 truncate text-[21px] leading-none ${tone === 'warn' ? 'text-saffron' : 'text-ink'}`}>{value}</div>
      {delta != null ? (
        <div className={`mt-1 text-[11px] tabular ${delta >= 0 ? 'text-emerald' : 'text-red'}`}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(1)}% <span className="text-ink-faint">{hint}</span>
        </div>
      ) : (
        <div className="mt-1 text-[11px] text-ink-faint">{hint ?? 'outstanding'}</div>
      )}
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] text-ink-muted">
      <span className="h-[2px] w-3 rounded" style={{ background: color }} /> {label}
    </span>
  )
}

function TopDebtors({ metrics }: { metrics: Metrics | null }) {
  if (!metrics) return <p className="text-[12.5px] text-ink-faint">Ask a question to see the passages behind the answer.</p>
  return (
    <div>
      <p className="mb-3 text-[12.5px] leading-relaxed text-ink-muted">
        Ask a question to see the passages behind the answer. Meanwhile, the largest outstanding balances:
      </p>
      <table className="w-full text-[12.5px]">
        <thead>
          <tr className="text-left text-[10.5px] uppercase tracking-[0.12em] text-ink-muted">
            <th className="pb-1.5 font-medium">Party</th>
            <th className="pb-1.5 pl-3 text-right font-medium">Pending</th>
            <th className="pb-1.5 pl-3 text-right font-medium">Overdue</th>
          </tr>
        </thead>
        <tbody>
          {metrics.receivables_rows.map((r) => (
            <tr key={r.party} className="border-t border-hairline">
              <td className="py-1.5 pr-2 leading-snug">{r.party}</td>
              <td className="tabular py-1.5 pl-3 text-right whitespace-nowrap">{inr(r.pending, { short: true })}</td>
              <td className={`tabular py-1.5 pl-3 text-right whitespace-nowrap ${r.overdue > 0 ? 'text-red' : 'text-ink-muted'}`}>{inr(r.overdue, { short: true })}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4">
        <div className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-ink-muted">Receivables ageing</div>
        <div className="flex h-2 overflow-hidden rounded-full bg-paper-3">
          {metrics.ageing.map((a, i) => (
            <div
              key={a.bucket}
              title={`${a.bucket}: ${inr(a.amount)}`}
              style={{ width: `${(a.amount / Math.max(1, metrics.receivables)) * 100}%`, background: ['#0F5C4A', '#5E9C86', '#E0862B', '#B3412E'][i] }}
            />
          ))}
        </div>
        <div className="mt-1.5 grid grid-cols-4 gap-1 text-[10.5px] text-ink-muted">
          {metrics.ageing.map((a) => (
            <div key={a.bucket} className="truncate">
              <div className="truncate">{a.bucket}</div>
              <div className="tabular text-ink">{inr(a.amount, { short: true })}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function highlightNumbers(text: string) {
  const parts = text.split(/(₹[\d,\.]+(?:\s?(?:L|Cr))?|\b\d[\d,\.]*%?)/g)
  return parts.map((p, i) => (/^(₹|\d)/.test(p) ? <strong key={i} className="tabular font-semibold text-ink">{p}</strong> : p))
}
