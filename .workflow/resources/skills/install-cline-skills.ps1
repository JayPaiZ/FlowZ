[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string] $ProjectRoot = (Join-Path $PSScriptRoot '..' '..' '..'),

    [Parameter(Mandatory = $false)]
    [string[]] $Skill,

    [Parameter(Mandatory = $false)]
    [switch] $IncludeOptional,

    [Parameter(Mandatory = $false)]
    [string] $TargetDirectory
)

$ErrorActionPreference = 'Stop'

function Get-ExpandedPath {
    param([Parameter(Mandatory = $true)][string] $Path)

    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    return [IO.Path]::GetFullPath($expanded)
}

function Assert-ContainedPath {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $Candidate
    )

    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $candidateFull = [IO.Path]::GetFullPath($Candidate)
    if (-not $candidateFull.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the allowed root: $Candidate"
    }
}

$project = Get-ExpandedPath $ProjectRoot
$manifestPath = Join-Path $project '.workflow\resources\skills\manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Manifest not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$resourceBase = Join-Path (Split-Path -Parent $manifestPath) $manifest.resourceRoot
$cline = $manifest.installation.cline

$requested = @($Skill | Where-Object { $_ -and $_.Trim() } | ForEach-Object { $_.Trim() })
$allEntries = @($manifest.skills)
$unsupportedRequested = @($allEntries | Where-Object { ($requested -contains $_.name) -and ($_.hosts.cline.installable -eq $false) })
if ($unsupportedRequested.Count) {
    throw ("The following Skill entries are not installable for Cline: {0}" -f (($unsupportedRequested | ForEach-Object name) -join ', '))
}

$entries = @($allEntries | Where-Object {
    $isDefault = $_.hosts.cline.default -eq $true
    ($requested.Count -eq 0 -and $isDefault) -or ($requested -contains $_.name)
})

if ($IncludeOptional -and $requested.Count -eq 0) {
    $entries = @($allEntries | Where-Object { $_.hosts.cline.installable -ne $false })
}
if ($entries.Count -eq 0) {
    throw 'No matching Cline Skill entries were found in the manifest.'
}

$target = if ($TargetDirectory) { Get-ExpandedPath $TargetDirectory } else { Get-ExpandedPath $cline.preferredTarget }
if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

$installed = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]
$conflicts = New-Object System.Collections.Generic.List[string]

foreach ($entry in $entries) {
    $sourceDir = Get-ExpandedPath (Join-Path $resourceBase ($entry.sourcePath -replace '^sources[/\\]', ''))
    Assert-ContainedPath -Root $resourceBase -Candidate $sourceDir
    $sourceSkill = Join-Path $sourceDir $entry.skillFile
    if (-not (Test-Path -LiteralPath $sourceSkill -PathType Leaf)) {
        throw "Skill entry '$($entry.name)' is missing its source file: $sourceSkill"
    }

    $actualHash = (Get-FileHash -LiteralPath $sourceSkill -Algorithm SHA256).Hash
    if ($actualHash -ne $entry.skillSha256) {
        throw "Skill entry '$($entry.name)' failed source hash verification. Expected $($entry.skillSha256), got $actualHash."
    }

    $destinationDir = Join-Path $target $entry.name
    Assert-ContainedPath -Root $target -Candidate $destinationDir
    if (Test-Path -LiteralPath $destinationDir) {
        $destinationSkill = Join-Path $destinationDir $entry.skillFile
        if ((Test-Path -LiteralPath $destinationSkill -PathType Leaf) -and ((Get-FileHash -LiteralPath $destinationSkill -Algorithm SHA256).Hash -eq $entry.skillSha256)) {
            $skipped.Add($entry.name)
            continue
        }
        $conflicts.Add($entry.name)
        continue
    }

    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    foreach ($relativeFile in $entry.installFiles) {
        $sourceFile = Join-Path $sourceDir $relativeFile
        $destinationFile = Join-Path $destinationDir $relativeFile
        Assert-ContainedPath -Root $sourceDir -Candidate $sourceFile
        Assert-ContainedPath -Root $destinationDir -Candidate $destinationFile
        if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
            throw "Skill entry '$($entry.name)' is missing install file: $sourceFile"
        }
        $destinationParent = Split-Path -Parent $destinationFile
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile -Destination $destinationFile -Force
    }

    $installedHash = (Get-FileHash -LiteralPath (Join-Path $destinationDir $entry.skillFile) -Algorithm SHA256).Hash
    if ($installedHash -ne $entry.skillSha256) {
        throw "Skill entry '$($entry.name)' failed destination hash verification."
    }
    $installed.Add($entry.name)
}

Write-Output ("Cline Skill target: {0}" -f $target)
Write-Output ("Installed: {0}" -f ($(if ($installed.Count) { $installed -join ', ' } else { 'none' })))
Write-Output ("Already matching: {0}" -f ($(if ($skipped.Count) { $skipped -join ', ' } else { 'none' })))
if ($conflicts.Count) {
    Write-Error ("Conflicts not overwritten: {0}" -f ($conflicts -join ', '))
    exit 2
}

Write-Output 'Reload or refresh Cline before using newly installed Skills.'
