# Preview by default. -Apply removes only the reproducible targets below.
# -RemoveResearchEnvironments keeps the independent .venv-candidate CPU/video
# environment, and removes old GPU/notebook/base environments after inventory.
[CmdletBinding()]
param([switch]$Apply, [switch]$RemoveResearchEnvironments)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git')) -or
    -not (Test-Path -LiteralPath (Join-Path $repoRoot 'coffee_ops'))) {
    throw 'Expected the CoffeeShop_Analytics repository containing .git and coffee_ops.'
}
$targets = @(
    'var/post-publication-20261115/production.tar',
    'var/post-publication-20261115/clean-env',
    'var/post-publication-20261115/trivy-cache',
    'var/model-benchmark/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct',
    'var/model-validation-20261116/annotations_trainval2017.zip',
    'var/engineering-audit-20261112/tools/trivy_0.76.2_windows-64bit.zip',
    'var/post-publication-20261115/tools/gitleaks_8.30.1_windows_x64.zip',
    'var/engineering-audit-20261112/inventory-before.json',
    'var/engineering-audit-20261112/inventory-complete.json',
    'var/engineering-audit-20261112/inventory-handoff.json',
    'var/post-publication-20261115/windows-video/.mypy_cache',
    'var/post-publication-20261115/windows-cpu/.mypy_cache',
    'var/post-publication-20261115/linux-video/.mypy_cache',
    'var/post-publication-20261115/linux-cpu/.mypy_cache',
    'var/engineering-audit-20261112/linux-run2/.mypy_cache',
    'var/model-validation-20261116/windows-video/.mypy_cache',
    'var/model-validation-20261116/linux-cpu/.mypy_cache',
    '.venv-ci',
    'var/post-publication-20261115/document-tools',
    'var/post-publication-20261115/candidate-scan',
    'var/post-publication-20261115/clean-checkout',
    'var/post-publication-20261115/clean-checkout.tar',
    'var/post-publication-20261115/clean-git',
    'var/release-verification-20261117/clean-source',
    'var/release-verification-20261117/checkpoint',
    'var/engineering-audit-20261112/clean-checkout',
    'var/engineering-audit-20261112/tools/trivy.exe',
    'var/post-publication-20261115/tools/gitleaks.exe',
    'var/model-benchmark/weights',
    '.pytest_cache',
    '.ruff_cache'
)
if ($RemoveResearchEnvironments) {
    foreach ($name in @('.venv', '.venv-bench', '.venv-notebook')) {
        $record = Join-Path $repoRoot ('var/storage-cleanup/' + $name.TrimStart('.') + '-inventory.json')
        if ((Test-Path -LiteralPath (Join-Path $repoRoot $name)) -and -not (Test-Path -LiteralPath $record)) {
            throw "Preserve the package inventory before removing $name"
        }
    }
    $targets += @('.venv', '.venv-bench', '.venv-notebook')
}
# Refuse to delete the duplicate model until the original verified cache exists.
$checkpoint = Join-Path $repoRoot 'var/release-verification-20261117/checkpoint/model.safetensors'
if (Test-Path -LiteralPath $checkpoint) {
    $expected = 'd18309d0d7ea57048138885c4c6ecfcb1e24506fc6153b94ad484f8ab62c7115'
    $original = Join-Path $repoRoot ('var/model-benchmark/huggingface/hub/models--PekingU--rtdetr_v2_r18vd/blobs/' + $expected)
    if (-not (Test-Path -LiteralPath $original) -or
        (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected -or
        (Get-FileHash -LiteralPath $checkpoint -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Duplicate RT-DETR checkpoint is not safely reproducible from the retained model cache.'
    }
}
# Discover regenerable caches without traversing directory links or .git.
$cacheNames = @('__pycache__', '.mypy_cache', '.pytest_cache', '.ruff_cache', '.ipynb_checkpoints')
$pending = [Collections.Generic.Stack[string]]::new()
$pending.Push($repoRoot)
while ($pending.Count) {
    $directory = $pending.Pop()
    foreach ($entry in @(Get-ChildItem -LiteralPath ('\\?\' + $directory) -Directory -Force)) {
        if ($entry.Name -eq '.git' -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
        $absolute = $entry.FullName
        if ($absolute.StartsWith('\\?\')) { $absolute = $absolute.Substring(4) }
        $relative = $absolute.Substring($repoRoot.Length + 1).Replace('\', '/')
        if ($targets -contains $relative) { continue }
        # Keep compiled runtime imports. Publisher test/benchmark bytecode is
        # dispensable; their source and all project tests remain untouched.
        if ($entry.Name -eq '__pycache__' -and $relative.StartsWith('.venv-candidate/', [StringComparison]::OrdinalIgnoreCase)) {
            $components = $relative.Split('/')
            if ($components -contains 'tests' -or $components -contains 'benchmarks') { $targets += $relative }
            continue
        }
        if ($cacheNames -contains $entry.Name) { $targets += $relative } else { $pending.Push($absolute) }
    }
}
# Deduplicate nested targets and protect existing source files, including the
# uncommitted new files. Nothing under .git is a cleanup target.
$targets = @($targets | Sort-Object -Unique | Where-Object {
    $candidate = $_
    -not @($targets | Where-Object { $candidate.StartsWith($_.TrimEnd('/') + '/', [StringComparison]::OrdinalIgnoreCase) }).Count
})
$protected = @(& git -C $repoRoot -c core.quotepath=false ls-files --cached --others --exclude-standard)
if ($LASTEXITCODE -ne 0) { throw 'Cannot establish the protected source inventory.' }
foreach ($relative in $targets) {
    if ($relative -eq '.git' -or $relative.StartsWith('.git/')) { throw 'Git metadata is protected.' }
    foreach ($source in $protected) {
        if ($source -eq $relative -or $source.StartsWith($relative.TrimEnd('/') + '/', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Cleanup target contains source: $relative"
        }
    }
}
$running = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID })
foreach ($relative in $targets) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $repoRoot $relative))
    foreach ($process in $running) {
        if (($process.ExecutablePath -and $process.ExecutablePath.StartsWith($absolute + '\', [StringComparison]::OrdinalIgnoreCase)) -or
            ($process.CommandLine -and [regex]::IsMatch($process.CommandLine,
                [regex]::Escape($absolute) + '(?=$|[\\/\s\x22\x27])',
                [Text.RegularExpressions.RegexOptions]::IgnoreCase))) {
            throw "Cleanup target is used by process $($process.ProcessId): $relative"
        }
    }
}
$manifest = @()
# Validate every target before deleting any target. Reject directory links and
# external file links; allow verified internal Hugging Face blob links only.
# Extended paths handle long wheel paths on Windows PowerShell 5.1.
foreach ($relative in $targets) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $repoRoot $relative))
    if (-not $absolute.StartsWith($repoRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target outside workspace: $relative"
    }
    $native = '\\?\' + $absolute
    if (-not (Test-Path -LiteralPath $native)) { continue }
    $parent = $absolute
    while ($parent -ne $repoRoot) {
        $item = Get-Item -LiteralPath ('\\?\' + $parent) -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $relative" }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
    $target = Get-Item -LiteralPath $native -Force
    $files = @($target)
    if ($target.PSIsContainer) {
        $entries = @(Get-ChildItem -LiteralPath $native -Recurse -Force)
        foreach ($entry in @($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })) {
            # Hugging Face stores file symlinks to blobs inside the same cache.
            # Never allow directory links or links outside the exact removed tree.
            if ($entry.PSIsContainer -or $entry.LinkType -ne 'SymbolicLink' -or @($entry.Target).Count -ne 1) {
                throw "Unsupported nested reparse point: $relative"
            }
            $linkTarget = @($entry.Target)[0]
            $destination = [IO.Path]::GetFullPath([IO.Path]::Combine($entry.DirectoryName, $linkTarget))
            if ($destination.StartsWith('\\?\')) { $destination = $destination.Substring(4) }
            if (-not $destination.StartsWith($absolute + '\', [StringComparison]::OrdinalIgnoreCase)) {
                throw "File symlink escapes cleanup target: $relative"
            }
            $linked = Get-Item -LiteralPath ('\\?\' + $destination) -Force
            if ($linked.PSIsContainer -or ($linked.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Chained or directory link rejected: $relative"
            }
        }
        $files = @($entries | Where-Object { -not $_.PSIsContainer })
    }
    $bytes = ($files | Measure-Object Length -Sum).Sum
    $manifest += [pscustomobject]@{ path=$relative; bytes=[long]$bytes; files=$files.Count; state='planned' }
}
$total = ($manifest | Measure-Object bytes -Sum).Sum
$manifest | Sort-Object bytes -Descending | Select-Object -First 25 path,bytes,files | Format-Table -AutoSize
Write-Output ('Targets: {0}. Showing the 25 largest; the apply log retains every target.' -f $manifest.Count)
Write-Output ('Reproducible targets: {0:N2} GiB. Apply={1}' -f ($total / 1GB), $Apply)
if (-not $Apply) { return }
$evidenceDirectory = Join-Path $repoRoot 'var'
$logPath = Join-Path $evidenceDirectory ('workspace-cleanup-executed-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $logPath -Encoding UTF8
foreach ($row in $manifest) {
    # Recheck the exact normalized target immediately before removal.
    $absolute = [IO.Path]::GetFullPath((Join-Path $repoRoot $row.path))
    if (-not $absolute.StartsWith($repoRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path changed' }
    try {
        # Unlink validated file links without recursion before removing the tree.
        if ((Get-Item -LiteralPath ('\\?\' + $absolute)).PSIsContainer) {
            $links = @(Get-ChildItem -LiteralPath ('\\?\' + $absolute) -Recurse -Force -Attributes ReparsePoint)
            foreach ($link in $links) {
                if ($link.PSIsContainer -or $link.LinkType -ne 'SymbolicLink') { throw 'Unexpected directory link' }
                $linkTarget = @($link.Target)[0]
                $destination = [IO.Path]::GetFullPath([IO.Path]::Combine($link.DirectoryName, $linkTarget))
                if ($destination.StartsWith('\\?\')) { $destination = $destination.Substring(4) }
                if (-not $destination.StartsWith($absolute + '\', [StringComparison]::OrdinalIgnoreCase)) {
                    throw 'Link target changed'
                }
                Remove-Item -LiteralPath $link.FullName -Force -ErrorAction Stop
            }
        }
        Remove-Item -LiteralPath ('\\?\' + $absolute) -Recurse -Force -ErrorAction Stop
        $row.state = 'removed'
    } catch {
        $row.state = 'failed: ' + $_.Exception.Message
        throw
    } finally {
        $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $logPath -Encoding UTF8
    }
}
Write-Output "Cleanup log: $logPath"
Write-Output 'Trivy must download a fresh vulnerability database before its next complete scan.'
