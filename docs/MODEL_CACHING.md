# Model Caching and Download Behavior

## What You're Seeing

When you see messages like:
```
model.safetensors: 100%|████████████| 115M/115M [02:46<00:00, 692kB/s]
```

This is **NOT pip reinstalling packages**. This is **HuggingFace downloading AI models**.

## The Difference

### Python Packages (pip)
- Installed in: `backend/venv/Lib/site-packages/`
- Installed once with: `pip install -r requirements.txt`
- Size: ~500MB total
- **These are NOT re-downloaded** unless you reinstall

### AI Models (HuggingFace)
- Cached in: `C:\Users\<username>\.cache\huggingface\`
- Downloaded on first use
- Size: ~300MB total
- **Should only download once**, then use cache

## Why Models Re-download

### 1. Cache Not Found
If the cache directory is empty or corrupted, models re-download.

**Check cache:**
```powershell
dir "$env:USERPROFILE\.cache\huggingface\hub"
```

**Expected:** Several folders like:
- `models--sentence-transformers--all-MiniLM-L6-v2`
- `models--unstructuredio--yolo_x_layout`
- `models--timm--resnet18.a1_in1k`

### 2. Network Check
HuggingFace checks for model updates even when cached.

**Solution:** Set offline mode in `.env`:
```env
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

### 3. Incomplete Download
If download was interrupted, it may restart.

**Solution:** Let it complete once, then it's cached forever.

## Models Used by DocIntel

| Model | Purpose | Size | When Downloaded |
|-------|---------|------|-----------------|
| `all-MiniLM-L6-v2` | Text embeddings | ~80MB | First document upload |
| `yolo_x_layout` | Layout detection | ~115MB | First hi-res PDF |
| `resnet18.a1_in1k` | Image analysis | ~46MB | First hi-res PDF |
| `table-transformer` | Table detection | ~46MB | First table in PDF |

**Total:** ~300MB (downloaded once, cached forever)

## Pre-download All Models

To avoid downloads during production use:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python preload_models.py
```

This will:
1. Download all models upfront
2. Cache them properly
3. Verify they work
4. Show cache location and size

**Run this once after installation!**

## Verify Models Are Cached

```powershell
# Check cache size
$cache = "$env:USERPROFILE\.cache\huggingface"
$size = (Get-ChildItem -Path $cache -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Cache size: $([math]::Round($size, 1)) MB"

# List cached models
Get-ChildItem -Path "$cache\hub" -Directory | Where-Object { $_.Name -like "models--*" } | Select-Object Name
```

**Expected output:**
```
Cache size: 287.3 MB

Name
----
models--sentence-transformers--all-MiniLM-L6-v2
models--unstructuredio--yolo_x_layout
models--timm--resnet18.a1_in1k
models--microsoft--table-transformer-detection
```

## Prevent Re-downloads

### Option 1: Pre-download (Recommended)
```powershell
python preload_models.py
```

### Option 2: Set Offline Mode
Add to `.env`:
```env
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

**Warning:** This prevents downloading new models. Only use after pre-downloading.

### Option 3: Use Local Model Cache
Set custom cache location in `.env`:
```env
HF_HOME=D:\AI_Models\huggingface
TRANSFORMERS_CACHE=D:\AI_Models\transformers
```

Then move existing cache:
```powershell
Move-Item "$env:USERPROFILE\.cache\huggingface" "D:\AI_Models\huggingface"
```

## Troubleshooting

### "Downloading model every time"

**Check 1:** Is cache directory writable?
```powershell
Test-Path "$env:USERPROFILE\.cache\huggingface" -PathType Container
```

**Check 2:** Are models actually cached?
```powershell
Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub" -Recurse -File | Measure-Object -Property Length -Sum
```

**Check 3:** Is antivirus blocking cache writes?
- Add exception for `%USERPROFILE%\.cache\huggingface`

### "Download is slow"

**Cause:** HuggingFace CDN speed varies by location.

**Solutions:**
1. Use a VPN to different region
2. Download during off-peak hours
3. Use `hf_xet` for faster downloads:
   ```powershell
   pip install huggingface_hub[hf_xet]
   ```

### "Out of disk space"

**Models need ~300MB + working space (~500MB total)**

**Check space:**
```powershell
Get-PSDrive C | Select-Object Used,Free
```

**Free up space:**
```powershell
# Clear pip cache
pip cache purge

# Clear npm cache
npm cache clean --force

# Clear old Python packages
pip uninstall <unused-package>
```

## Production Deployment

### Docker
Pre-download models in Dockerfile:

```dockerfile
FROM python:3.10-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download models
COPY preload_models.py .
RUN python preload_models.py --non-interactive

# Copy application
COPY . /app
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Kubernetes
Use init container to pre-download:

```yaml
initContainers:
- name: model-downloader
  image: docintel:latest
  command: ["python", "preload_models.py", "--non-interactive"]
  volumeMounts:
  - name: model-cache
    mountPath: /root/.cache/huggingface
```

### Shared Cache
Multiple instances can share cache:

```yaml
volumes:
- name: model-cache
  persistentVolumeClaim:
    claimName: huggingface-models
```

## Summary

| Issue | Solution |
|-------|----------|
| Models download every time | Run `preload_models.py` once |
| Slow downloads | Install `hf_xet` or use VPN |
| Disk space issues | Clear pip/npm cache |
| Production deployment | Pre-download in Docker image |
| Multiple instances | Use shared volume for cache |

**Key Point:** Models are downloaded once and cached. If you see downloads repeatedly, the cache isn't working properly - check permissions and disk space.
