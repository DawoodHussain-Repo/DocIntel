# Groq Models Reference (April 2026)

## Current Production Models

### Recommended for DocIntel

**Llama 3.3 70B Versatile** (Current Default)
- Model ID: `llama-3.3-70b-versatile`
- Speed: 280 tokens/sec
- Context: 131,072 tokens
- Max completion: 32,768 tokens
- Pricing: $0.59 input / $0.79 output per 1M tokens
- Rate limits: 300K TPM, 1K RPM
- **Best for**: Document analysis, complex reasoning, high-quality outputs

### Alternative Options

**Llama 3.1 8B Instant**
- Model ID: `llama-3.1-8b-instant`
- Speed: 560 tokens/sec (fastest)
- Context: 131,072 tokens
- Pricing: $0.05 input / $0.08 output per 1M tokens
- Rate limits: 250K TPM, 1K RPM
- **Best for**: Cost-sensitive applications, simple queries

**GPT OSS 120B**
- Model ID: `openai/gpt-oss-120b`
- Speed: 500 tokens/sec
- Context: 131,072 tokens
- Max completion: 65,536 tokens
- Pricing: $0.15 input / $0.60 output per 1M tokens
- **Best for**: High-quality outputs, large completions

**GPT OSS 20B**
- Model ID: `openai/gpt-oss-20b`
- Speed: 1000 tokens/sec (very fast)
- Context: 131,072 tokens
- Max completion: 65,536 tokens
- Pricing: $0.075 input / $0.30 output per 1M tokens
- **Best for**: Balance of speed and quality

## Deprecated Models

⚠️ **These models are no longer available:**
- `llama-3.1-70b-versatile` (decommissioned)
- `llama-3.1-405b-reasoning` (decommissioned)
- `kimi-k2-0905` (deprecated April 2026)

See [Groq Deprecations](https://console.groq.com/docs/deprecations) for full list.

## How to Change Models

### Option 1: Environment Variable (Recommended)
Edit `.env` file:
```env
GROQ_MODEL=llama-3.3-70b-versatile
```

### Option 2: Runtime Override
Pass model name when initializing LLM:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
```

## Model Selection Guide

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| Document analysis (default) | `llama-3.3-70b-versatile` | Best balance of quality and speed |
| Cost optimization | `llama-3.1-8b-instant` | Cheapest, still good quality |
| Maximum quality | `openai/gpt-oss-120b` | Largest model, best reasoning |
| Maximum speed | `openai/gpt-oss-20b` | 1000 tokens/sec |
| Long outputs | `openai/gpt-oss-120b` | 65K max completion |

## Rate Limits (Developer Plan)

All production models have:
- **RPM**: 1,000 requests per minute
- **TPM**: 250K-300K tokens per minute

If you hit rate limits:
1. Add retry logic with exponential backoff (already implemented)
2. Upgrade to paid plan for higher limits
3. Use faster model to reduce token usage time

## Checking Available Models

Use Groq API to list current models:
```bash
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

Or in Python:
```python
import requests
import os

response = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
)
print(response.json())
```

## Troubleshooting

### "Model has been decommissioned"
- Update `GROQ_MODEL` in `.env` to a current model
- See [Groq Models](https://console.groq.com/docs/models) for latest list

### "Rate limit exceeded"
- Wait 60 seconds and retry
- Reduce concurrent requests
- Upgrade to paid plan

### "Invalid API key"
- Check `GROQ_API_KEY` in `.env`
- Get new key from [Groq Console](https://console.groq.com/)

## References

- [Groq Models Documentation](https://console.groq.com/docs/models)
- [Groq Pricing](https://groq.com/pricing)
- [Groq Deprecations](https://console.groq.com/docs/deprecations)
- [Groq API Reference](https://console.groq.com/docs/api-reference)

---

**Last Updated**: April 2026  
**Current Default**: `llama-3.3-70b-versatile`
