# 🔒 Security Notice

## API Key Rotation Required

An API key was temporarily exposed in git history. The commits containing the key have been removed.

## Action Required

1. **Rotate your Groq API key immediately**
   - Visit: https://console.groq.com/keys
   - Delete the old key
   - Generate a new key
   - Update your `.env` file

2. **Verify .env is never committed**
   - `.env` is in `.gitignore` ✅
   - Only `.env.example` should be in git ✅

## Git History Status

✅ Cleaned - problematic commits removed
✅ Safe to push after key rotation

## Prevention

- Never paste real keys in documentation
- Always use placeholders in `.env.example`
- Rotate keys immediately if exposed
