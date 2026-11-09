import { useEffect, useRef, useState } from 'react'
import { ArrowUp, Square } from 'lucide-react'
import type { Message, Status } from '../types'
import AnswerMarkdown from './AnswerMarkdown'

interface Props {
  status: Status | null
  messages: Message[]
  busy: boolean
  suggestions: string[]
  activeCitation: number | null
  onCitation: (n: number | null, pin?: boolean) => void
  onSend: (q: string) => void
  onStop: () => void
  onSelectMessage: (id: string) => void
  selectedMessageId: string | null
}

export default function Conversation(props: Props) {
  const { status, messages, busy, suggestions, activeCitation, onCitation, onSend, onStop, onSelectMessage, selectedMessageId } = props
  const [draft, setDraft] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages.length, messages[messages.length - 1]?.content.length])

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = '0px'
    ta.style.height = Math.min(ta.scrollHeight, 180) + 'px'
  }, [draft])

  const submit = () => {
    const q = draft.trim()
    if (!q || busy) return
    setDraft('')
    onSend(q)
  }

  return (
    <section className="flex h-full min-w-0 flex-col">
      <header className="flex items-center justify-between border-b border-hairline px-6 py-3 lg:px-10">
        <div className="min-w-0">
          <div className="truncate font-display text-[17px]">{status?.company ?? 'Loading…'}</div>
          <div className="text-[11.5px] text-ink-muted">
            {status?.ready
              ? `${status.documents.toLocaleString('en-IN')} passages indexed · ${status.embeddings === 'bm25-only' ? 'lexical retrieval' : `hybrid retrieval (${status.embeddings})`}`
              : 'Waiting for first sync'}
          </div>
        </div>
        <div className="hidden items-center gap-1 rounded-full border border-hairline bg-paper-2 p-0.5 text-[12px] lg:flex">
          <span className="rounded-full bg-paper px-3 py-1 font-medium shadow-[0_1px_0_rgba(20,32,28,0.06)]">Answers</span>
          <span className="px-3 py-1 text-ink-muted">Evidence →</span>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 lg:px-10">
        <div className="mx-auto w-full max-w-[760px] py-8">
          {messages.length === 0 && <EmptyState company={status?.company} suggestions={suggestions} onAsk={onSend} />}
          {messages.map((m) =>
            m.role === 'user' ? (
              <UserTurn key={m.id} text={m.content} />
            ) : (
              <AssistantTurn
                key={m.id}
                message={m}
                selected={selectedMessageId === m.id}
                activeCitation={selectedMessageId === m.id ? activeCitation : null}
                onCitation={(n, pin) => {
                  onSelectMessage(m.id)
                  onCitation(n, pin)
                }}
                onSelect={() => onSelectMessage(m.id)}
              />
            ),
          )}
        </div>
      </div>

      <div className="px-6 pb-5 pt-2 lg:px-10">
        <div className="mx-auto w-full max-w-[760px]">
          <div className="flex items-end gap-2 rounded-lg border border-hairline bg-paper-2 p-2 pl-4 shadow-[inset_0_1px_2px_rgba(20,32,28,0.06)] focus-within:border-emerald">
            <textarea
              ref={textareaRef}
              rows={1}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  submit()
                }
              }}
              placeholder="Ask anything about your books… e.g. kis party ka udhaar sabse zyada hai?"
              className="max-h-[180px] flex-1 resize-none bg-transparent py-2 text-[15px] leading-relaxed text-ink placeholder:text-ink-faint focus:outline-none"
            />
            {busy ? (
              <button
                onClick={onStop}
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-ink text-paper transition hover:bg-emerald"
                aria-label="Stop"
              >
                <Square className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={!draft.trim() || !status?.ready}
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-emerald text-paper transition hover:bg-emerald-deep disabled:bg-hairline disabled:text-ink-faint"
                aria-label="Send"
              >
                <ArrowUp className="h-4.5 w-4.5" />
              </button>
            )}
          </div>
          <p className="mt-2 text-center text-[11.5px] text-ink-faint">
            Answers are grounded in your MargBooks data ·{' '}
            {status?.llm.provider === 'claude' ? 'Claude' : 'offline retrieval mode'} · Enter to send, Shift+Enter for a new line
          </p>
        </div>
      </div>
    </section>
  )
}

function EmptyState({ company, suggestions, onAsk }: { company?: string; suggestions: string[]; onAsk: (q: string) => void }) {
  return (
    <div className="rise pt-10">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald">Namaste</p>
      <h1 className="font-display mt-2 text-[40px] font-light leading-[1.05] tracking-tight text-ink">
        What would you like to know about <span className="italic">{company ?? 'your business'}</span>?
      </h1>
      <p className="mt-4 max-w-[560px] text-[15px] leading-relaxed text-ink-muted">
        SawalSetu reads your MargBooks sales, purchases, parties and items, builds a private index, and answers in
        plain language with a citation for every number.
      </p>
      <div className="mt-8 grid gap-2 sm:grid-cols-2">
        {suggestions.slice(0, 4).map((q) => (
          <button
            key={q}
            onClick={() => onAsk(q)}
            className="rounded-lg border border-hairline bg-paper-2/60 px-4 py-3 text-left text-[13.5px] leading-snug transition hover:border-emerald hover:bg-emerald-tint"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

function UserTurn({ text }: { text: string }) {
  return (
    <div className="rise mt-10 border-l-2 border-saffron pl-4 first:mt-0">
      <p className="font-display text-[21px] font-light italic leading-snug text-ink">{text}</p>
    </div>
  )
}

function AssistantTurn({
  message,
  selected,
  activeCitation,
  onCitation,
  onSelect,
}: {
  message: Message
  selected: boolean
  activeCitation: number | null
  onCitation: (n: number | null, pin?: boolean) => void
  onSelect: () => void
}) {
  const time = new Date(message.at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  return (
    <div className={`rise mt-5 rounded-lg px-4 py-4 transition ${selected ? 'bg-paper-2/70' : ''}`} onClick={onSelect}>
      <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-emerald">
        <span className="font-semibold">SawalSetu</span>
        <span className="text-ink-faint">·</span>
        <span className="font-mono normal-case tracking-normal text-ink-faint">{time}</span>
        {message.sources && message.sources.length > 0 && (
          <>
            <span className="text-ink-faint">·</span>
            <span className="normal-case tracking-normal text-ink-faint">{message.sources.length} sources</span>
          </>
        )}
      </div>
      {message.error ? (
        <p className="rounded-md border border-red/30 bg-red-tint px-3 py-2 text-[14px] text-red">{message.error}</p>
      ) : message.content ? (
        <AnswerMarkdown text={message.content} streaming={message.streaming} activeCitation={activeCitation} onCitation={onCitation} />
      ) : (
        <div className="flex items-center gap-2 text-[14px] text-ink-muted">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald" />
          Reading your books…
        </div>
      )}
    </div>
  )
}
