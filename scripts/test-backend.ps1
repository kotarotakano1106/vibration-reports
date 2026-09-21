[CmdletBinding()]
param(
    [ValidateSet("quick", "unit", "integration", "api", "all", "coverage")]
    [string]$Mode = "quick"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BackendPath = Join-Path $ProjectRoot "backend"
$TestsPath = Join-Path $BackendPath "tests"
$ExpectedTestDatabase = "vibration_reports_test"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan

    & $Command
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host "FAILED: $Name (exit code: $exitCode)" -ForegroundColor Red
        exit $exitCode
    }

    Write-Host "PASSED: $Name" -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Write-Host "Pythonが見つかりません: $Python" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $TestsPath -PathType Container)) {
    Write-Host "Backend Testディレクトリが見つかりません: $TestsPath" -ForegroundColor Red
    exit 1
}

$RequiresTestDatabase = $Mode -in @("integration", "api", "all", "coverage")

if ($RequiresTestDatabase -and $env:POSTGRES_DB -ne $ExpectedTestDatabase) {
    Write-Host "テストを中止しました。POSTGRES_DBがテストDBではありません。" -ForegroundColor Red
    Write-Host "期待値: $ExpectedTestDatabase"
    Write-Host "現在値: $env:POSTGRES_DB"
    exit 2
}

Push-Location $ProjectRoot
try {
    switch ($Mode) {
        "quick" {
            Invoke-CheckedCommand "Ruff" {
                & $Python -m ruff check ".\backend\src" ".\backend\tests"
            }
            Invoke-CheckedCommand "Unit Test" {
                & $Python -m pytest ".\backend\tests\unit" -q
            }
        }
        "unit" {
            Invoke-CheckedCommand "Unit Test" {
                & $Python -m pytest ".\backend\tests\unit" -q
            }
        }
        "integration" {
            Invoke-CheckedCommand "Integration Test" {
                & $Python -m pytest ".\backend\tests\integration" -q
            }
        }
        "api" {
            Invoke-CheckedCommand "API Test" {
                & $Python -m pytest ".\backend\tests\api" -q
            }
        }
        "all" {
            Invoke-CheckedCommand "Ruff" {
                & $Python -m ruff check `
                    ".\backend\src" `
                    ".\backend\tests"
            }

            Invoke-CheckedCommand "mypy" {
                & $Python -m mypy ".\backend\src"
            }

            Invoke-CheckedCommand "Backend Test" {
                & $Python -m pytest ".\backend\tests" -q
            }
        }
        "coverage" {
            Invoke-CheckedCommand "Ruff" {
                & $Python -m ruff check `
                    ".\backend\src" `
                    ".\backend\tests"
            }

            Invoke-CheckedCommand "mypy" {
                & $Python -m mypy ".\backend\src"
            }

            Invoke-CheckedCommand "Backend Test with Coverage" {
                & $Python -m pytest ".\backend\tests" `
                    --cov=backend.src `
                    --cov-report=term-missing `
                    --cov-report=html `
                    --cov-fail-under=80
            }
        }
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "すべての検証が成功しました。Mode=$Mode" -ForegroundColor Green
exit 0


