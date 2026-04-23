# DocIntel Frontend

Modern Next.js 15 frontend with real-time SSE streaming for legal document intelligence.

## Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx            # Root layout with fonts and metadata
│   ├── page.tsx              # Home page (main application)
│   └── globals.css           # Global styles and design system
├── components/               # React components
│   ├── ChatPane.tsx          # Chat interface with SSE streaming
│   └── UploadPane.tsx        # Document upload with drag-and-drop
├── hooks/                    # Custom React hooks
│   ├── useChatStream.ts      # SSE streaming and message state
│   ├── useContractUpload.ts  # Upload API integration
│   ├── useThreadId.ts        # Thread ID generation and validation
│   └── useUploadedDocuments.ts # Document list persistence
├── lib/                      # Utility libraries
│   ├── api.ts                # Backend API client
│   ├── config.ts             # Frontend configuration
│   ├── sse.ts                # SSE parser
│   └── types.ts              # TypeScript type definitions
├── public/                   # Static assets
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── Dockerfile                # Docker image definition
```

## Architecture

### Component Hierarchy

```
page.tsx (Root)
  ├── useThreadId()
  ├── useUploadedDocuments()
  ├── useChatStream(threadId)
  ├── useContractUpload()
  │
  ├── UploadPane
  │   └── Document list + drag-and-drop
  │
  └── ChatPane
      ├── Message list
      ├── Tool call indicators
      └── Input composer
```

### Data Flow

1. **Upload Flow:**
   ```
   User drops PDF → useContractUpload → API call → Backend
   → Success → Add to useUploadedDocuments → Update UI
   ```

2. **Chat Flow:**
   ```
   User sends message → useChatStream → SSE stream → Backend
   → Events (tool_call, token, done) → Update message state
   → Persist to sessionStorage
   ```

3. **State Persistence:**
   - Thread ID: `sessionStorage` (per tab)
   - Messages: `sessionStorage` (per thread)
   - Documents: `localStorage` (persistent)

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Configure environment
cp ../.env.example ../.env
# Edit .env with NEXT_PUBLIC_BACKEND_URL
```

### Running

```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Lint
npm run lint
```

## Configuration

Environment variables (`.env`):

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Important:** All public env vars must be prefixed with `NEXT_PUBLIC_`.

## Features

### Real-Time Streaming

- Server-Sent Events (SSE) for token-by-token streaming
- Automatic reconnection on network failures
- Graceful error handling with user-friendly messages

### Client-Side Validation

- File type validation (PDF only)
- File size validation (20MB limit)
- Query length validation (2000 chars max)
- Character counter when approaching limit
- UUID v4 validation for thread IDs

### Responsive Design

- Mobile-first approach
- Glassmorphism design system
- Dark theme with teal accents
- Smooth animations and transitions

### Accessibility

- Semantic HTML
- ARIA labels and live regions
- Keyboard navigation
- Focus indicators
- Screen reader support

## Development

### Adding New Components

1. Create component in `components/`
2. Use TypeScript for type safety
3. Follow existing naming conventions
4. Add proper TypeScript interfaces

### Adding New Hooks

1. Create hook in `hooks/`
2. Prefix with `use` (React convention)
3. Handle loading and error states
4. Add TypeScript types

### Styling

- Use Tailwind CSS utility classes
- Follow design system in `globals.css`
- Use CSS variables for colors
- Maintain consistent spacing

## API Integration

All API calls go through `lib/api.ts`:

```typescript
import { uploadContract, streamChat } from "@/lib/api";

// Upload
const result = await uploadContract(file);

// Stream chat
await streamChat(query, threadId, {
  onToolCall: (event) => { /* ... */ },
  onToken: (event) => { /* ... */ },
  onDone: (event) => { /* ... */ },
});
```

## Error Handling

### Upload Errors

- Client-side validation before upload
- Server error messages displayed inline
- Retry mechanism for transient failures

### Streaming Errors

- Connection failures handled gracefully
- Timeout messages displayed clearly
- Error state preserved in UI

### Network Failures

- Automatic retry with exponential backoff
- User-friendly error messages
- Fallback to cached data when possible

## Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build test
npm run build
```

## Deployment

### Docker

```bash
# Build image
docker build -t docintel-frontend .

# Run container
docker run -p 3000:3000 docintel-frontend
```

### Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Environment Variables

Set in deployment platform:
- `NEXT_PUBLIC_BACKEND_URL`: Backend API URL

## Troubleshooting

### "Failed to fetch" Error

1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_BACKEND_URL` in `.env`
3. Check CORS settings in backend
4. Restart Next.js dev server (env vars require restart)

### SSE Connection Issues

1. Check browser console for errors
2. Verify backend SSE endpoint is accessible
3. Check network tab for connection status
4. Ensure no proxy is blocking SSE

### Build Errors

1. Clear `.next` directory: `rm -rf .next`
2. Clear node_modules: `rm -rf node_modules && npm install`
3. Check TypeScript errors: `npm run type-check`

## Performance

### Optimization Techniques

- React Server Components for static content
- Client Components only where needed
- Lazy loading for heavy components
- Memoization for expensive computations
- Debouncing for input handlers

### Bundle Size

- Tree shaking enabled
- Code splitting by route
- Dynamic imports for large dependencies
- Optimized images and assets

## License

MIT
