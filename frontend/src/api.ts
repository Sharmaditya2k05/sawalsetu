import type { Metrics, Source, Status } from './types'

async function json<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(input, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  status: () => json<Status>('/api/status'),
  metrics: () => json<Metrics>('/api/metrics'),
  suggestions: () => json<{ suggestions: string[] }>('/api/suggestions').then((r) => r.suggestions),
  sync: () => json<Status>('/api/sync', { method: 'POST' }),
}

export type ChatEvent =
  | { type: 'sources'; sources: Source[] }
  | { type: 'token'; text: string }
  | { type: 'done'; model: string | null; usage: unknown }
  | { type: 'error'; message: string }

/** POST /api/chat and yield server-sent events as they stream in. */
export async function* streamChat(
  question: string,
  history: { role: string; content: string }[],
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ question, history }),
    signal,
  })
  if (!res.ok || !res.body) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let sep: number
    while ((sep = buffer.search(/\r?\n\r?\n/)) !== -1) {
      const raw = buffer.slice(0, sep)
      buffer = buffer.slice(sep).replace(/^\r?\n\r?\n/, '')
      const data = raw
        .split(/\r?\n/)
        .filter((l) => l.startsWith('data:'))
        .map((l) => l.slice(5).trimStart())
        .join('\n')
      if (!data) continue
      try {
        yield JSON.parse(data) as ChatEvent
      } catch {
        /* keep-alive or malformed chunk */
      }
    }
  }
}
