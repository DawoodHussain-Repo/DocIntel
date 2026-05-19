'use client'

import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowUpRight,
  Bot,
  MessageSquare,
  Send,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { MAX_QUERY_LENGTH, QUERY_WARNING_THRESHOLD } from '@/lib/config'
import { cn } from '@/lib/utils'
import type { ChatMessage, ContractType, RiskLevel, ToolCallEvent } from '@/lib/types'

interface ChatPanelProps {
  activeFile: string | null
  contractType?: ContractType
  riskLevel?: RiskLevel
  riskScore?: number
  messages: ChatMessage[]
  isStreaming: boolean
  streamError: string | null
  currentToolCall: ToolCallEvent | null
  draftMessage: string
  onDraftChange: (value: string) => void
  onSend: () => Promise<void>
  onClear: () => void
}

function riskBadgeVariant(level: RiskLevel) {
  if (level === 'red') return 'high'
  if (level === 'yellow') return 'medium'
  return 'low'
}

const suggestedQuestions = [
  'What are the payment terms?',
  'Can the agreement be terminated early?',
  'What happens to my IP?',
]

export function ChatPanel({
  activeFile,
  contractType,
  riskLevel,
  riskScore,
  messages,
  isStreaming,
  streamError,
  currentToolCall,
  draftMessage,
  onDraftChange,
  onSend,
  onClear,
}: ChatPanelProps) {
  const trimmedLength = draftMessage.trim().length
  const queryTooLong = trimmedLength > MAX_QUERY_LENGTH
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, currentToolCall])

  return (
    <aside className="sticky top-[100px]">
      <div className="flex h-[calc(100vh-120px)] min-h-[640px] flex-col overflow-hidden rounded-3xl border border-border bg-white shadow-card">
        {/* Header */}
        <div className="border-b border-slate-100 p-8 pb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="rounded-xl bg-accent/10 p-2 text-accent">
              <MessageSquare size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">Legal Copilot</h2>
          </div>
          <p className="text-sm text-text-sub">
            Ask questions grounded entirely in the context of the uploaded agreement.
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {contractType ? <Badge variant="type">{contractType}</Badge> : null}
            {riskLevel && typeof riskScore === 'number' ? (
              <Badge variant={riskBadgeVariant(riskLevel)}>{riskScore} risk</Badge>
            ) : null}
          </div>

          {activeFile ? (
            <div className="surface-muted mt-4 px-4 py-3">
              <p className="label">Active document</p>
              <p className="mt-1.5 truncate text-sm font-medium text-text">
                {activeFile}
              </p>
            </div>
          ) : null}
        </div>

        {/* Chat Body */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 bg-slate-50/30">
          {messages.length === 0 ? (
            <div className="mt-auto flex h-full flex-col justify-end gap-3">
              <p className="label mb-2">Suggested Queries</p>
              {suggestedQuestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => onDraftChange(suggestion)}
                  className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-4 text-left text-sm transition-all hover:border-accent/30 hover:shadow-sm group"
                >
                  <span className="font-medium text-slate-600 group-hover:text-accent transition-colors">
                    {suggestion}
                  </span>
                  <ArrowUpRight
                    size={16}
                    className="text-slate-300 group-hover:text-accent transition-colors"
                  />
                </button>
              ))}
            </div>
          ) : (
            <AnimatePresence initial={false}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.2, ease: 'easeOut' }}
                    className={cn(
                      'flex gap-3',
                      message.role === 'user' ? 'justify-end' : 'justify-start',
                    )}
                  >
                    {message.role === 'assistant' ? (
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white">
                        <Bot className="h-4 w-4" />
                      </div>
                    ) : null}
                    <div
                      className={cn(
                        'max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                        message.role === 'assistant'
                          ? 'bg-slate-900 text-white shadow-sm'
                          : 'border border-border bg-white text-text shadow-sm',
                      )}
                    >
                      {message.content ||
                        (message.role === 'assistant' && isStreaming ? (
                          <span className="inline-flex gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-white/60 animate-pulse" />
                            <span className="h-1.5 w-1.5 rounded-full bg-white/60 animate-pulse [animation-delay:150ms]" />
                            <span className="h-1.5 w-1.5 rounded-full bg-white/60 animate-pulse [animation-delay:300ms]" />
                          </span>
                        ) : (
                          ''
                        ))}
                    </div>
                    {message.role === 'user' ? (
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-white text-text">
                        <UserRound className="h-4 w-4" />
                      </div>
                    ) : null}
                  </motion.div>
                ))}
              </div>
            </AnimatePresence>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-100 bg-white p-6">
          <div className="flex flex-col gap-3">
            <AnimatePresence>
              {currentToolCall ? (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                  className="surface-muted flex items-center gap-2 px-3 py-2 text-xs text-text-sub"
                >
                  <Sparkles className="h-3.5 w-3.5 text-accent" />
                  Searching with {currentToolCall.tool}
                </motion.div>
              ) : null}
            </AnimatePresence>

            {streamError ? (
              <div className="rounded-2xl border border-danger/20 bg-danger/5 px-3 py-3 text-sm text-danger">
                {streamError}
              </div>
            ) : null}

            <textarea
              rows={3}
              placeholder="Ask anything about this contract..."
              className="w-full resize-none rounded-2xl border-none bg-slate-50 px-5 py-4 text-sm text-slate-900 shadow-inner-soft placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all"
              value={draftMessage}
              onChange={(event) => onDraftChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void onSend()
                }
              }}
              disabled={!activeFile || isStreaming}
            />

            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-1.5">
                <div className="flex items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-600">
                  <ShieldCheck size={14} />
                  <span>Grounded Mode</span>
                </div>
                <p
                  className={cn(
                    'ml-2 text-xs',
                    queryTooLong
                      ? 'text-danger'
                      : trimmedLength >= QUERY_WARNING_THRESHOLD
                        ? 'text-warning'
                        : 'text-text-sub',
                  )}
                >
                  {trimmedLength}/{MAX_QUERY_LENGTH}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={onClear}>
                  Clear
                </Button>
                <button
                  type="button"
                  onClick={() => void onSend()}
                  disabled={!draftMessage.trim() || !activeFile || isStreaming || queryTooLong}
                  className={cn(
                    'flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium transition-all',
                    draftMessage.trim().length > 0 && !isStreaming && !queryTooLong
                      ? 'bg-accent text-white shadow-md shadow-accent/20 hover:bg-accent-glow'
                      : 'bg-slate-100 text-slate-400 cursor-not-allowed',
                  )}
                >
                  <span>{isStreaming ? 'Answering' : 'Send'}</span>
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
