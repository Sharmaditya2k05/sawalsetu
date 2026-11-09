import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  text: string
  streaming?: boolean
  activeCitation: number | null
  onCitation: (n: number | null, pin?: boolean) => void
}

/** Turn "[3]" and "[2, 5]" into markdown links we can render as citation chips. */
function linkCitations(text: string): string {
  return text.replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\](?!\()/g, (_m, group: string) =>
    group
      .split(',')
      .map((n) => n.trim())
      .map((n) => `[${n}](#cite-${n})`)
      .join(''),
  )
}

export default function AnswerMarkdown({ text, streaming, activeCitation, onCitation }: Props) {
  return (
    <div className={`prose-answer ${streaming ? 'caret' : ''}`}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const m = href?.match(/^#cite-(\d+)$/)
            if (m) {
              const n = Number(m[1])
              return (
                <a
                  href={href}
                  className={`cite ${activeCitation === n ? 'is-active' : ''}`}
                  onMouseEnter={() => onCitation(n)}
                  onMouseLeave={() => onCitation(null)}
                  onClick={(e) => {
                    e.preventDefault()
                    onCitation(n, true)
                  }}
                >
                  {n}
                </a>
              )
            }
            return (
              <a href={href} target="_blank" rel="noreferrer" className="text-emerald underline">
                {children}
              </a>
            )
          },
        }}
      >
        {linkCitations(text)}
      </Markdown>
    </div>
  )
}
