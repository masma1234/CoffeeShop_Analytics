param(
    [Parameter(Mandatory=$true)][string]$Plan,
    [Parameter(Mandatory=$true)][string]$Record,
    [switch]$Execute
)
$ErrorActionPreference = 'Stop'
$auditRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$proposal = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($proposal.root).TrimEnd('\') -ne $auditRoot) { throw 'Plan root differs from project root' }
if (Test-Path -LiteralPath $Record) { throw 'Record already exists' }
if (-not $Execute) { throw 'Review the exact plan, then provide -Execute' }
$checkedParents = @{}
$deletedBytes = 0L
$deletedCount = 0
$skippedCount = 0
$recordPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Record))
$recordStream = [IO.FileStream]::new($recordPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$writer = [IO.StreamWriter]::new($recordStream,[Text.UTF8Encoding]::new($false))
try {
foreach ($entry in $proposal.files) {
    $row = [ordered]@{path=$entry.path; bytes=$entry.bytes; sha256=$entry.sha256; source=$entry.source; status='SKIPPED'}
    try {
        $cachePath = [IO.Path]::GetFullPath((Join-Path $auditRoot $entry.path))
        $sourcePath = [IO.Path]::GetFullPath((Join-Path $auditRoot $entry.source))
        foreach ($targetPath in @($cachePath,$sourcePath)) {
            if (-not $targetPath.StartsWith($auditRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Outside workspace' }
            $target = Get-Item -LiteralPath $targetPath -Force
            if ($target.PSIsContainer -or ($target.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Not a regular file' }
            $parent = $target.Directory
            while ($parent.FullName -ne $auditRoot) {
                if ($null -eq $parent -or -not $parent.FullName.StartsWith($auditRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid parent path' }
                if ($checkedParents.ContainsKey($parent.FullName)) { break }
                if ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse parent' }
                $checkedParents[$parent.FullName] = $true
                $parent = $parent.Parent
            }
        }
        if ([IO.Path]::GetExtension($cachePath) -ne '.pyc' -or [IO.Path]::GetFileName([IO.Path]::GetDirectoryName($cachePath)) -ne '__pycache__') { throw 'Not an approved bytecode cache' }
        if ((Get-Item -LiteralPath $cachePath -Force).Length -ne $entry.bytes) { throw 'Cache size changed' }
        if ((Get-FileHash -LiteralPath $cachePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Cache hash changed' }
        if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.source_sha256) { throw 'Source hash changed' }
        # Persist intent before removing anything; a failed log write must stop
        # this deletion. Keep one shared-readable stream open for the whole run.
        $row.status='VERIFIED_DELETE_INTENT'
        $writer.WriteLine(($row | ConvertTo-Json -Compress))
        $writer.Flush()
        # Only this verified file is removed. Never recurse or invoke another shell.
        Remove-Item -LiteralPath $cachePath -Force
        $row.status='DELETED'
        $deletedBytes += $entry.bytes
        $deletedCount++
    } catch {
        $row.status='SKIPPED'
        $row.reason=$_.Exception.Message
        $skippedCount++
    }
    $writer.WriteLine(($row | ConvertTo-Json -Compress))
    $writer.Flush()
}
} finally { $writer.Dispose() }
[pscustomobject]@{deleted_files=$deletedCount; deleted_logical_bytes=$deletedBytes; skipped_files=$skippedCount; record=$Record} | ConvertTo-Json
