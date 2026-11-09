import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { PanelRightOpen, X } from 'lucide-react'
import { api, streamChat } from './api'
import type { Message, Metrics, Status } from './types'
import Sidebar, { Wordmark } from './components/Sidebar'
import Conversation from './components/Conversation'
import EvidencePanel from './components/EvidencePanel'

let seq = 0
const uid = () => `${Date.now().toString(36)}-${++seq}`

export default function App() {
  const [status, setStatus] = useState<Status | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [busy, setBusy] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  const [hoverCitation, setHoverCitation] = useState<number | null>(null)
  const [pinnedCitation, setPinnedCitation] = useState<number | null>(null)
  const [mobilePanel, setMobilePanel] = useState<'answers' | 'evidence'>('answers')
  const abortRef = useRef<AbortController | null>(null)

  const refresh = useCallback(async () => {
    const s = await api.status()
    setStatus(s)
    if (s.ready) {
      api.metrics().then(setMetrics).catch(() => setMetrics(null))
    }
    return s
  }, [])

  useEffect(() => {
    api.suggestions().then(setSuggestions).catch(() => {})
    refresh().catch(() => {})
    const t = setInterval(() => refresh().catch(() => {}), 60_000)
    return () => clearInterval(t)
  }, [refresh])

  const sync = useCallback(async () => {
    setSyncing(true)
    setSyncError(null)
    try {
      const s = await api.sync()
      setStatus(s)
      api.metrics().then(setMetrics).catch(() => {})
    } catch (e) {
      setSyncError(e instanceof Error ? e.message : String(e))
    } finally {
      setSyncing(false)
    }
  }, [])

  const send = useCallback(
    async (question: string) => {
      if (busy) return
      const userMsg: Message = { id: uid(), role: 'user', content: question, at: Date.now() }
      const assistantId = uid()
      const assistant: Message = { id: assistantId, role: 'assistant', content: '', streaming: true, at: Date.now() }
      const history = messages.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }))
      setMessages((prev) => [...prev, userMsg, assistant])
      setSelectedMessageId(assistantId)
      setPinnedCitation(null)
      setBusy(true)
      const controller = new AbortController()
      abortRef.current = controller
      const patch = (fn: (m: Message) => Message) =>
        setMessages((prev) => prev.map((m) => (m.id === assistantId ? fn(m) : m)))
      try {
        for await (const ev of streamChat(question, history, controller.signal)) {
          if (ev.type === 'sources') patch((m) => ({ ...m, sources: ev.sources }))
          else if (ev.type === 'token') patch((m) => ({ ...m, content: m.content + ev.text }))
          else if (ev.type === 'done') patch((m) => ({ ...m, streaming: false, model: ev.model }))
          else if (ev.type === 'error') patch((m) => ({ ...m, streaming: false, error: ev.message }))
        }
      } catch (e) {
        if (!(e instanceof DOMException && e.name === 'AbortError')) {
          patch((m) => ({ ...m, streaming: false, error: e instanceof Error ? e.message : String(e) }))
        }
      } finally {
        patch((m) => ({ ...m, streaming: false }))
        setBusy(false)
        abortRef.current = null
      }
    },
    [busy, messages],
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])

  const selected = useMemo(
    () => messages.find((m) => m.id === selectedMessageId) ?? [...messages].reverse().find((m) => m.role === 'assistant'),
    [messages, selectedMessageId],
  )
  const activeCitation = hoverCitation ?? pinnedCitation

  const onCitation = useCallback((n: number | null, pin?: boolean) => {
    if (pin) {
      setPinnedCitation((p) => (p === n ? null : n))
      setMobilePanel('evidence')
    } else {
      setHoverCitation(n)
    }
  }, [])

  return (
    <div className="h-full lg:grid lg:grid-cols-[280px_minmax(0,1fr)_360px]">
      {/* Mobile top bar */}
      <div className="flex items-center justify-between border-b border-hairline bg-paper-2 px-4 py-3 lg:hidden">
        <Wordmark compact />
        <button
          onClick={() => setMobilePanel((p) => (p === 'answers' ? 'evidence' : 'answers'))}
          className="inline-flex items-center gap-1.5 rounded-full border border-hairline px-3 py-1.5 text-[12px] font-medium"
        >
          {mobilePanel === 'answers' ? <PanelRightOpen className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
          {mobilePanel === 'answers' ? 'Evidence' : 'Close'}
        </button>
      </div>

      <div className="hidden lg:block">
        <Sidebar status={status} suggestions={suggestions} syncing={syncing || !!status?.syncing} onSync={sync} onAsk={send} syncError={syncError} />
      </div>

      <div className={`${mobilePanel === 'answers' ? 'block' : 'hidden'} h-[calc(100%-57px)] lg:block lg:h-full`}>
        <Conversation
          status={status}
          messages={messages}
          busy={busy}
          suggestions={suggestions}
          activeCitation={activeCitation}
          onCitation={onCitation}
          onSend={send}
          onStop={stop}
          onSelectMessage={setSelectedMessageId}
          selectedMessageId={selected?.id ?? null}
        />
      </div>

      <div className={`${mobilePanel === 'evidence' ? 'block' : 'hidden'} h-[calc(100%-57px)] lg:block lg:h-full`}>
        <EvidencePanel metrics={metrics} sources={selected?.sources ?? []} activeCitation={activeCitation} onCitation={onCitation} />
      </div>
    </div>
  )
}
