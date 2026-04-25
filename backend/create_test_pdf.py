"""Create a simple test PDF to verify the extraction pipeline works."""

def create_test_pdf():
    """Create a simple contract PDF for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
    except ImportError:
        print("❌ reportlab not installed. Install with: pip install reportlab")
        return False
    
    filename = "test_contract.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "SERVICE AGREEMENT")
    
    # Content
    c.setFont("Helvetica", 12)
    y = height - 1.5*inch
    
    lines = [
        "This Service Agreement ('Agreement') is entered into as of January 1, 2024",
        "between Party A ('Client') and Party B ('Service Provider').",
        "",
        "1. SERVICES",
        "Service Provider agrees to provide consulting services as described in Exhibit A.",
        "",
        "2. COMPENSATION",
        "Client agrees to pay Service Provider $5,000 per month for services rendered.",
        "Payment shall be made within 30 days of invoice receipt.",
        "",
        "3. TERM AND TERMINATION",
        "This Agreement shall commence on January 1, 2024 and continue for one year.",
        "Either party may terminate with 30 days written notice.",
        "",
        "4. CONFIDENTIALITY",
        "Both parties agree to maintain confidentiality of proprietary information.",
        "",
        "5. GOVERNING LAW",
        "This Agreement shall be governed by the laws of the State of California.",
        "",
        "IN WITNESS WHEREOF, the parties have executed this Agreement.",
        "",
        "_________________________          _________________________",
        "Party A                            Party B",
        "Date: January 1, 2024              Date: January 1, 2024",
    ]
    
    for line in lines:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
        if y < 1*inch:  # New page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 1*inch
    
    c.save()
    
    print(f"✅ Created {filename}")
    print(f"   This is a text-based PDF that should work with fast/hi-res extraction")
    print(f"\nTest it with:")
    print(f"   python quick_test.py {filename}")
    
    return True


if __name__ == "__main__":
    create_test_pdf()
