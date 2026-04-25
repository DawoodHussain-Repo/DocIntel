# Free OCR Solutions for Scanned PDFs

## Recommended: Tesseract OCR (Free & Open Source)

**Tesseract** is the industry-standard open-source OCR engine, originally developed by HP and now maintained by Google. It's completely free and works locally without sending data to external servers.

### Installation

#### Windows
```powershell
# Using Chocolatey
choco install tesseract

# Or download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Add to PATH:
# C:\Program Files\Tesseract-OCR
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-eng  # English language pack
```

#### macOS
```bash
brew install tesseract
```

### Verification
```bash
tesseract --version
```

### Language Packs
```bash
# Install additional languages
# Windows: Download from GitHub releases
# Linux:
sudo apt-get install tesseract-ocr-ara  # Arabic
sudo apt-get install tesseract-ocr-fra  # French
sudo apt-get install tesseract-ocr-deu  # German
```

## Alternative Free OCR Solutions

### 1. OCRmyPDF (Python Package)
- **Description:** Adds OCR text layer to scanned PDFs
- **Installation:** `pip install ocrmypdf`
- **Usage:** `ocrmypdf input.pdf output.pdf`
- **Pros:** Preserves original PDF, adds searchable text layer
- **Cons:** Requires Tesseract as backend

### 2. Google Cloud Vision API (Free Tier)
- **Description:** Cloud-based OCR with 1,000 free requests/month
- **Pros:** High accuracy, supports 50+ languages
- **Cons:** Requires internet, sends data to Google
- **Setup:** Requires Google Cloud account and API key

### 3. Azure Computer Vision (Free Tier)
- **Description:** Microsoft's OCR service with 5,000 free requests/month
- **Pros:** Good accuracy, REST API
- **Cons:** Requires internet, sends data to Microsoft
- **Setup:** Requires Azure account and API key

### 4. EasyOCR (Python Package)
- **Description:** Deep learning-based OCR
- **Installation:** `pip install easyocr`
- **Pros:** Good accuracy, supports 80+ languages
- **Cons:** Requires GPU for best performance, larger model downloads

## DocIntel Integration

DocIntel automatically uses Tesseract when available:

1. **Fast Strategy (Default):** No OCR, works for 90% of PDFs
2. **Auto-Fallback:** If no text found, tries OCR with `hi_res` strategy
3. **Clear Errors:** Provides specific error codes when OCR is needed but unavailable

### Configuration

No configuration needed! Just install Tesseract and ensure it's in your PATH.

### Error Messages

- **EMPTY_DOCUMENT:** PDF has no text (empty or corrupted)
- **OCR_NOT_AVAILABLE:** Scanned PDF detected but Tesseract not installed
- **PDF_PARSE_FAILED:** Other parsing errors

## Recommendations

**For DocIntel:**
1. **Install Tesseract** - Best balance of accuracy, speed, and privacy
2. **Keep it local** - No data leaves your machine
3. **Free forever** - No API limits or costs

**For Production:**
- Use Tesseract for most documents
- Consider cloud OCR (Google/Azure) for critical documents requiring highest accuracy
- Implement fallback chain: Fast → Tesseract → Cloud OCR (if configured)

## Performance Tips

1. **Preprocessing:** Clean scanned images before OCR (deskew, denoise)
2. **DPI:** Ensure scans are at least 300 DPI for best results
3. **Language:** Specify correct language pack for better accuracy
4. **Caching:** Cache OCR results to avoid re-processing

## Security Considerations

- **Tesseract:** Runs locally, no data transmission
- **Cloud OCR:** Data sent to third-party servers
- **Compliance:** For sensitive legal documents, prefer local OCR (Tesseract)
- **GDPR/HIPAA:** Local processing avoids data transfer concerns

## Links

- Tesseract GitHub: https://github.com/tesseract-ocr/tesseract
- Tesseract Windows Installer: https://github.com/UB-Mannheim/tesseract/wiki
- OCRmyPDF: https://github.com/ocrmypdf/OCRmyPDF
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- Google Cloud Vision: https://cloud.google.com/vision/docs/ocr
- Azure Computer Vision: https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/
