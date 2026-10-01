<#
.SYNOPSIS
    Script de instalação global ou local da SKILL 'add_reference' (AI Knowledge Librarian v2.0).

.DESCRIPTION
    Instala ou atualiza a skill 'add_reference' no diretório global do Gemini/Antigravity
    ($HOME\.gemini\config\skills\add_reference) ou no diretório de workspace (.agents\skills\add_reference).

.PARAMETER TargetDir
    Caminho personalizado de destino para instalação da skill.

.PARAMETER Workspace
    Se definido, instala no workspace atual em .agents\skills\add_reference ao invés de global.

.PARAMETER SkipDeps
    Se definido, pula a verificação e instalação de dependências via pip.

.PARAMETER SkipTests
    Se definido, pula a execução dos testes unitários pós-instalação.

.PARAMETER DryRun
    Apenas simula os passos da instalação sem realizar alterações no disco.

.EXAMPLE
    .\install.ps1
    Instala globalmente em $HOME\.gemini\config\skills\add_reference

.EXAMPLE
    .\install.ps1 -Workspace
    Instala no workspace local em .agents\skills\add_reference
#>

[CmdletBinding()]
param(
    [string]$TargetDir = "",
    [switch]$Workspace,
    [switch]$SkipDeps,
    [switch]$SkipTests,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Instalação da SKILL: add_reference (AI Knowledge Librarian)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Determina o diretório de destino
if (-not $TargetDir) {
    if ($Workspace) {
        $TargetDir = Join-Path (Get-Location) ".agents\skills\add_reference"
    } else {
        $userHome = [System.Environment]::GetFolderPath('UserProfile')
        $TargetDir = Join-Path $userHome ".gemini\config\skills\add_reference"
    }
}

Write-Host "[1/4] Destino da instalação: $TargetDir" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "[DRY-RUN] Simulação ativada. Nenhuma alteração física será realizada." -ForegroundColor Magenta
    Write-Host "[DRY-RUN] Criaria diretório: $TargetDir"
    Write-Host "[DRY-RUN] Copiaria SKILL.md e pasta scripts/"
    if (-not $SkipDeps) { Write-Host "[DRY-RUN] Executaria: pip install -r requirements.txt" }
    if (-not $SkipTests) { Write-Host "[DRY-RUN] Executaria suíte de testes unitários" }
    Write-Host "Simulação concluída com sucesso!" -ForegroundColor Green
    exit 0
}

# 2. Criação do diretório e cópia dos artefatos
$sourceDir = $PSScriptRoot
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Host "  -> Diretório de destino criado." -ForegroundColor Green
}

$skillFile = Join-Path $sourceDir "SKILL.md"
$scriptsDir = Join-Path $sourceDir "scripts"

if (Test-Path $skillFile) {
    Copy-Item $skillFile (Join-Path $TargetDir "SKILL.md") -Force
    Write-Host "  -> SKILL.md copiado com sucesso." -ForegroundColor Green
} else {
    Write-Error "Arquivo SKILL.md não encontrado em $sourceDir"
}

if (Test-Path $scriptsDir) {
    $targetScripts = Join-Path $TargetDir "scripts"
    if (-not (Test-Path $targetScripts)) {
        New-Item -ItemType Directory -Path $targetScripts -Force | Out-Null
    }
    Copy-Item (Join-Path $scriptsDir "*") $targetScripts -Recurse -Force
    Write-Host "  -> Pasta scripts/ copiada com sucesso." -ForegroundColor Green
} else {
    Write-Error "Diretório scripts/ não encontrado em $sourceDir"
}

# 3. Resolução de dependências Python
Write-Host "[2/4] Verificando dependências Python..." -ForegroundColor Yellow
if (-not $SkipDeps) {
    $reqFile = Join-Path $sourceDir "requirements.txt"
    if (Test-Path $reqFile) {
        try {
            Write-Host "  -> Instalando pacotes recomendados via pip..." -ForegroundColor Gray
            & python -m pip install -r $reqFile --quiet
            Write-Host "  -> Dependências instaladas/atualizadas com sucesso." -ForegroundColor Green
        } catch {
            Write-Warning "Falha ao instalar dependências automaticamente via pip: $_"
            Write-Host "Você pode instalá-las manualmente executando: pip install -r requirements.txt" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  -> Instalação de dependências pulada (-SkipDeps)." -ForegroundColor Gray
}

# 4. Execução dos testes de validação
Write-Host "[3/4] Validando integridade da instalação..." -ForegroundColor Yellow
if (-not $SkipTests) {
    $testScript = Join-Path $TargetDir "scripts\test_convert_to_md.py"
    if (Test-Path $testScript) {
        Write-Host "  -> Executando suíte de testes unitários..." -ForegroundColor Gray
        & python $testScript
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  -> Todos os testes unitários passaram com sucesso!" -ForegroundColor Green
        } else {
            Write-Error "A suíte de testes falhou. Verifique as mensagens de erro acima."
        }
    }
} else {
    Write-Host "  -> Testes pulados (-SkipTests)." -ForegroundColor Gray
}

# 5. Finalização
Write-Host "[4/4] Finalização e Prontidão" -ForegroundColor Yellow
Write-Host ""
Write-Host "✓ A SKILL 'add_reference' foi instalada com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Como utilizar:" -ForegroundColor Cyan
Write-Host "1. No Antigravity / Gemini CLI, invoque com: /add_reference" -ForegroundColor White
Write-Host "2. Ou solicite em linguagem natural: 'Adicione o documento X como referência'" -ForegroundColor White
Write-Host "3. Para busca cirúrgica rápida via terminal:" -ForegroundColor White
Write-Host "   python `"$TargetDir\scripts\convert_to_md.py`" --query `"<termo>`" `"<workspace>/.referencias`"" -ForegroundColor Gray
Write-Host ""
