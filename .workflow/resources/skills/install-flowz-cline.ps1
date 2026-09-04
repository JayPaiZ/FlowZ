[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string] $ProjectRoot = (Join-Path $PSScriptRoot '..\..\..'),

    [Parameter(Mandatory = $false)]
    [string[]] $Skill,

    [Parameter(Mandatory = $false)]
    [switch] $IncludeOptional,

    [Parameter(Mandatory = $false)]
    [string] $TargetDirectory,

    [Parameter(Mandatory = $false)]
    [string] $RulesTargetDirectory
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

function Assert-SafeOverridePath {
    param([Parameter(Mandatory = $true)][string] $Path)

    $full = Get-ExpandedPath $Path
    $root = [IO.Path]::GetPathRoot($full).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $withoutTrailing = $full.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    if ($withoutTrailing -eq $root) {
        throw "Refusing to use a filesystem root as an installation override: $full"
    }

    $profile = Get-ExpandedPath '%USERPROFILE%'
    if ($withoutTrailing.Equals($profile.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to use the user-profile root as an installation override: $full"
    }

    return $full
}

function Get-Names {
    param([System.Collections.Generic.List[string]] $Items)

    if ($Items.Count) { return ($Items -join ', ') }
    return 'none'
}

function Copy-VerifiedFile {
    param(
        [Parameter(Mandatory = $true)][string] $Source,
        [Parameter(Mandatory = $true)][string] $Destination,
        [Parameter(Mandatory = $true)][string] $ExpectedHash,
        [Parameter(Mandatory = $true)][string] $Label,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]] $Installed,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]] $Skipped,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]] $Conflicts
    )

    if (Test-Path -LiteralPath $Destination) {
        if (-not (Test-Path -LiteralPath $Destination -PathType Leaf)) {
            $Conflicts.Add($Label)
            return $false
        }
        $existingHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
        if ($existingHash -eq $ExpectedHash) {
            $Skipped.Add($Label)
            return $true
        }

        $Conflicts.Add($Label)
        return $false
    }

    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $Source -Destination $Destination

    $installedHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
    if ($installedHash -ne $ExpectedHash) {
        throw "File '$Label' failed destination hash verification."
    }
    $Installed.Add($Label)
    return $true
}

$project = Get-ExpandedPath $ProjectRoot
$manifestPath = Join-Path $project '.workflow\resources\skills\manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Manifest not found: $manifestPath"
}

$manifestDirectory = Split-Path -Parent $manifestPath
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$resourceBase = Get-ExpandedPath (Join-Path $manifestDirectory $manifest.resourceRoot)
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

$target = if ($TargetDirectory) {
    Assert-SafeOverridePath $TargetDirectory
} else {
    Get-ExpandedPath $cline.preferredTarget
}
$rulesTarget = if ($RulesTargetDirectory) {
    Assert-SafeOverridePath $RulesTargetDirectory
} elseif ($TargetDirectory) {
    Join-Path (Split-Path -Parent $target) 'rules'
} else {
    Get-ExpandedPath $cline.preferredRulesTarget
}

$profileRoot = Get-ExpandedPath '%USERPROFILE%'
if (-not $TargetDirectory) { Assert-ContainedPath -Root $profileRoot -Candidate $target }
if (-not $RulesTargetDirectory -and -not $TargetDirectory) { Assert-ContainedPath -Root $profileRoot -Candidate $rulesTarget }

if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $rulesTarget -PathType Container)) {
    New-Item -ItemType Directory -Path $rulesTarget -Force | Out-Null
}

$installedSkills = New-Object 'System.Collections.Generic.List[string]'
$skippedSkills = New-Object 'System.Collections.Generic.List[string]'
$skillConflicts = New-Object 'System.Collections.Generic.List[string]'
$installedRules = New-Object 'System.Collections.Generic.List[string]'
$skippedRules = New-Object 'System.Collections.Generic.List[string]'
$ruleConflicts = New-Object 'System.Collections.Generic.List[string]'

foreach ($rule in @($cline.globalRules)) {
    $source = Get-ExpandedPath (Join-Path $manifestDirectory $rule.sourcePath)
    Assert-ContainedPath -Root (Join-Path $manifestDirectory '..') -Candidate $source
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Global rule '$($rule.name)' is missing its source file: $source"
    }
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ($sourceHash -ne $rule.sha256) {
        throw "Global rule '$($rule.name)' failed source hash verification. Expected $($rule.sha256), got $sourceHash."
    }

    $destination = Join-Path $rulesTarget $rule.installFile
    Assert-ContainedPath -Root $rulesTarget -Candidate $destination
    [void](Copy-VerifiedFile -Source $source -Destination $destination -ExpectedHash $rule.sha256 -Label $rule.name -Installed $installedRules -Skipped $skippedRules -Conflicts $ruleConflicts)
}

foreach ($entry in $entries) {
    $relativeSource = $entry.sourcePath -replace '^sources[/\\]', ''
    $sourceDir = Get-ExpandedPath (Join-Path $resourceBase $relativeSource)
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
        $allFilesMatch = $true
        foreach ($relativeFile in @($entry.installFiles)) {
            $sourceFile = Join-Path $sourceDir $relativeFile
            $destinationFile = Join-Path $destinationDir $relativeFile
            if (-not (Test-Path -LiteralPath $destinationFile -PathType Leaf)) {
                $allFilesMatch = $false
                break
            }
            $expectedFileHash = if ($relativeFile -eq $entry.skillFile) { $entry.skillSha256 } else { (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash }
            if ((Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash -ne $expectedFileHash) {
                $allFilesMatch = $false
                break
            }
        }
        if ($allFilesMatch) {
            $skippedSkills.Add($entry.name)
        } else {
            $skillConflicts.Add($entry.name)
        }
        continue
    }

    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    foreach ($relativeFile in @($entry.installFiles)) {
        $sourceFile = Join-Path $sourceDir $relativeFile
        $destinationFile = Join-Path $destinationDir $relativeFile
        Assert-ContainedPath -Root $sourceDir -Candidate $sourceFile
        Assert-ContainedPath -Root $destinationDir -Candidate $destinationFile
        if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
            throw "Skill entry '$($entry.name)' is missing install file: $sourceFile"
        }
        $expectedFileHash = if ($relativeFile -eq $entry.skillFile) { $entry.skillSha256 } else { (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash }
        Copy-Item -LiteralPath $sourceFile -Destination $destinationFile
        if ((Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash -ne $expectedFileHash) {
            throw "Skill entry '$($entry.name)' failed destination hash verification for '$relativeFile'."
        }
    }
    $installedSkills.Add($entry.name)
}

Write-Output ("Cline rules target: {0}" -f $rulesTarget)
Write-Output ("Rules installed: {0}" -f (Get-Names $installedRules))
Write-Output ("Rules already matching: {0}" -f (Get-Names $skippedRules))
Write-Output ("Cline Skill target: {0}" -f $target)
Write-Output ("Skills installed: {0}" -f (Get-Names $installedSkills))
Write-Output ("Skills already matching: {0}" -f (Get-Names $skippedSkills))

$allConflicts = New-Object 'System.Collections.Generic.List[string]'
foreach ($name in $ruleConflicts) { $allConflicts.Add("rule:$name") }
foreach ($name in $skillConflicts) { $allConflicts.Add("skill:$name") }
if ($allConflicts.Count) {
    Write-Warning ("Conflicts not overwritten: {0}" -f ($allConflicts -join ', '))
    exit 2
}

Write-Output 'Reload or refresh Cline before using the installed global workflow and Skills.'
Write-Output 'Project-layer onboarding occurs when the Agent handles the first task in each workspace.'
exit 0
