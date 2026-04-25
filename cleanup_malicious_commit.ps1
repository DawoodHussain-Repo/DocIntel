# PowerShell script to remove malicious commit 78cfc0d from git history

Write-Host "=== Git History Cleanup ===" -ForegroundColor Cyan
Write-Host "This will remove the malicious commit 78cfc0d from history" -ForegroundColor Yellow
Write-Host ""

# Create backup branch
Write-Host "[1/6] Creating backup branch..." -ForegroundColor Cyan
$backupBranch = "backup-before-cleanup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
git branch $backupBranch
Write-Host "✓ Backup created: $backupBranch" -ForegroundColor Green
Write-Host ""

# Show what will be removed
Write-Host "[2/6] Malicious commit to be removed:" -ForegroundColor Cyan
git show 78cfc0d --stat
Write-Host ""

$confirm = Read-Host "Continue with cleanup? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Cleanup cancelled" -ForegroundColor Yellow
    exit
}

# Option 1: Interactive rebase (cleaner method)
Write-Host "[3/6] Starting interactive rebase..." -ForegroundColor Cyan
Write-Host "In the editor that opens:" -ForegroundColor Yellow
Write-Host "  1. Find the line with '78cfc0d doc: Status Update'" -ForegroundColor White
Write-Host "  2. Change 'pick' to 'drop' (or delete the entire line)" -ForegroundColor White
Write-Host "  3. Save and close the editor" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to open the rebase editor..."

# Start interactive rebase
git rebase -i 78cfc0d^

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Rebase failed or was aborted" -ForegroundColor Red
    Write-Host "To restore: git rebase --abort" -ForegroundColor Yellow
    Write-Host "Or restore backup: git reset --hard $backupBranch" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Malicious commit removed" -ForegroundColor Green
Write-Host ""

# Verify the commit is gone
Write-Host "[4/6] Verifying removal..." -ForegroundColor Cyan
$commitExists = git log --all --oneline | Select-String "78cfc0d"
if ($commitExists) {
    Write-Host "✗ Commit still exists in history" -ForegroundColor Red
} else {
    Write-Host "✓ Commit successfully removed" -ForegroundColor Green
}
Write-Host ""

# Show new history
Write-Host "[5/6] New git history:" -ForegroundColor Cyan
git log --oneline --graph --all -15
Write-Host ""

# Check if we need to force push
Write-Host "[6/6] Checking remote status..." -ForegroundColor Cyan
$status = git status -sb
Write-Host $status
Write-Host ""

Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the new history above" -ForegroundColor White
Write-Host "2. Force push to remote:" -ForegroundColor White
Write-Host "   git push origin main --force" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: Force push rewrites remote history!" -ForegroundColor Red
Write-Host "- Anyone who pulled the malicious commit will need to reset" -ForegroundColor Yellow
Write-Host "- They should run: git fetch origin && git reset --hard origin/main" -ForegroundColor Yellow
Write-Host ""
Write-Host "To restore backup if needed:" -ForegroundColor Yellow
Write-Host "   git reset --hard $backupBranch" -ForegroundColor Cyan
Write-Host ""
