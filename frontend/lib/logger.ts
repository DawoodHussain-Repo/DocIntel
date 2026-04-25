type LogLevel = 'error' | 'warn' | 'info'

function shouldLog(): boolean {
  return process.env.NODE_ENV === 'development'
}

function write(level: LogLevel, message: string, meta?: unknown): void {
  if (!shouldLog()) {
    return
  }

  if (level === 'error') {
    console.error(message, meta)
    return
  }

  if (level === 'warn') {
    console.warn(message, meta)
    return
  }

  console.info(message, meta)
}

export const logger = {
  error(message: string, meta?: unknown): void {
    write('error', message, meta)
  },
  warn(message: string, meta?: unknown): void {
    write('warn', message, meta)
  },
  info(message: string, meta?: unknown): void {
    write('info', message, meta)
  },
}
