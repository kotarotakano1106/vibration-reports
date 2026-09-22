param(
    [string]$ProjectRoot = ".",
    [string]$OutputFile = "project-source-bundle.txt"
)

$ErrorActionPreference = "Stop"

$projectRootPath = (Resolve-Path $ProjectRoot).Path
$outputPath = Join-Path $projectRootPath $OutputFile

$excludedDirectoryNames = @(
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "coverage",
    "htmlcov",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
    "source-review-chunks"
)

$allowedExtensions = @(
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mts",
    ".cts",
    ".json",
    ".toml",
    ".ini",
    ".yml",
    ".yaml",
    ".sql",
    ".md",
    ".ps1",
    ".sh",
    ".css",
    ".scss",
    ".txt"
)

$allowedFileNames = @(
    ".gitignore",
    ".dockerignore",
    "Dockerfile",
    "Makefile"
)

function Get-ProjectRelativePath {
    param([string]$FullName)

    return $FullName.Substring($projectRootPath.Length).TrimStart("\", "/")
}

function Test-ExcludedPath {
    param([string]$FullName)

    $relativePath = Get-ProjectRelativePath -FullName $FullName
    $pathParts = $relativePath -split '[\\/]'

    foreach ($part in $pathParts) {
        if ($part -in $excludedDirectoryNames) {
            return $true
        }
    }

    return $false
}

$sourceFiles = Get-ChildItem $projectRootPath -Recurse -File -Force |
    Where-Object {
        $extension = $_.Extension.ToLowerInvariant()

        -not (Test-ExcludedPath -FullName $_.FullName) -and
        $_.Name -notmatch '^\.env($|\.)' -and
        $_.Name -notmatch '\.bak$' -and
        $_.FullName -ne $outputPath -and
        $_.Length -le 1MB -and
        (
            $extension -in $allowedExtensions -or
            $_.Name -in $allowedFileNames
        )
    } |
    Sort-Object FullName

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($outputPath, $false, $utf8NoBom)

try {
    $writer.WriteLine("=" * 100)
    $writer.WriteLine("VIBRATION REPORTS - SOURCE BUNDLE")
    $writer.WriteLine("=" * 100)
    $writer.WriteLine("Generated: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
    $writer.WriteLine("Project root: " + $projectRootPath)
    $writer.WriteLine("Included files: " + $sourceFiles.Count)
    $writer.WriteLine("")
    $writer.WriteLine("Excluded: environment files, Git internals, dependencies, caches, coverage, builds, binary files")
    $writer.WriteLine("")

    $writer.WriteLine("=" * 100)
    $writer.WriteLine("FILE INDEX")
    $writer.WriteLine("=" * 100)

    foreach ($sourceFile in $sourceFiles) {
        $relativePath = Get-ProjectRelativePath -FullName $sourceFile.FullName
        $writer.WriteLine($relativePath)
    }

    foreach ($sourceFile in $sourceFiles) {
        $relativePath = Get-ProjectRelativePath -FullName $sourceFile.FullName

        $writer.WriteLine("")
        $writer.WriteLine("=" * 100)
        $writer.WriteLine("FILE START")
        $writer.WriteLine("PATH: " + $relativePath)
        $writer.WriteLine("SIZE: " + $sourceFile.Length + " bytes")
        $writer.WriteLine("=" * 100)
        $writer.WriteLine("")

        try {
            $content = Get-Content $sourceFile.FullName -Raw -Encoding UTF8
            if ($null -eq $content) {
                $content = ""
            }
            $writer.WriteLine($content)
        }
        catch {
            $writer.WriteLine("[READ ERROR] " + $_.Exception.Message)
        }

        $writer.WriteLine("")
        $writer.WriteLine("=" * 100)
        $writer.WriteLine("FILE END")
        $writer.WriteLine("PATH: " + $relativePath)
        $writer.WriteLine("=" * 100)
    }
}
finally {
    $writer.Dispose()
}

$result = Get-Item $outputPath

Write-Host ""
Write-Host "Created source bundle:"
Write-Host $result.FullName
Write-Host "Included files:" $sourceFiles.Count
Write-Host "Bundle size (bytes):" $result.Length
