#!/bin/bash
# Script to remove malicious commit 78cfc0d from git history

echo "=== Git History Cleanup ==="
echo "This will remove the malicious commit 78cfc0d from history"
echo ""

# Create backup branch
echo "[1/5] Creating backup branch..."
git branch backup-before-cleanup-$(date +%Y%m%d_%H%M%S)
echo "✓ Backup created"
echo ""

# Show what will be removed
echo "[2/5] Malicious commit to be removed:"
git show 78cfc0d --stat
echo ""

read -p "Continue with cleanup? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Remove the malicious commit using filter-branch
echo "[3/5] Removing malicious commit from history..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch frontend/postcss.config.js || true' \
  --prune-empty --tag-name-filter cat -- 78cfc0d..HEAD

echo "✓ Commit removed from history"
echo ""

# Clean up refs
echo "[4/5] Cleaning up references..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✓ References cleaned"
echo ""

# Show new history
echo "[5/5] New git history:"
git log --oneline --graph --all -15
echo ""

echo "=== Cleanup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review the new history above"
echo "2. Force push to remote: git push origin main --force"
echo "3. WARNING: This rewrites history - coordinate with team if needed"
echo ""
echo "To restore backup: git reset --hard backup-before-cleanup-TIMESTAMP"
