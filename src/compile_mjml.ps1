# Script PowerShell para compilar todos os templates MJML
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "          COMPILANDO TEMPLATES MJML" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Lista de templates para compilar
$templates = @(
    @{
        Name = "Template de Colaborador"
        Input = "templates/mjml/send_collaborator_email_template.mjml"
        Output = "templates/send_collaborator_email_template.html"
    },
    @{
        Name = "Template de Orientador"
        Input = "templates/mjml/send_advisor_email_template.mjml"
        Output = "templates/send_advisor_email_template.html"
    },
    @{
        Name = "Template de Aprovação para Estudante"
        Input = "templates/mjml/send_work_aaprove_to_student_template.mjml"
        Output = "templates/send_work_aaprove_to_student_template.html"
    },
    @{
        Name = "Template de Rejeição para Estudante"
        Input = "templates/mjml/send_work_reject_advisor_to_student_template.mjml"
        Output = "templates/send_work_reject_advisor_to_student_template.html"
    },
    @{
        Name = "Template de Recuperação de Senha"
        Input = "templates/mjml/send_forget_password_email_template.mjml"
        Output = "templates/send_forget_password_email_template.html"
    },
    @{
        Name = "Template de Mudanças Necessárias"
        Input = "templates/mjml/send_needs_changes_to_work_template.mjml"
        Output = "templates/send_needs_changes_to_work_template.html"
    },
    @{
        Name = "Template de Convite para Membro"
        Input = "templates/mjml/send_email_to_member.template.mjml"
        Output = "templates/send_email_to_member.template.html"
    },
    @{
        Name = "Template de Atualização para Orientador"
        Input = "templates/mjml/send_work_update_email_to_advisor_template.mjml"
        Output = "templates/send_work_update_email_to_advisor_template.html"
    }
)

$totalTemplates = $templates.Count
$successCount = 0
$errorCount = 0

for ($i = 0; $i -lt $totalTemplates; $i++) {
    $template = $templates[$i]
    $progress = $i + 1
    
    Write-Host "[$progress/$totalTemplates] Compilando $($template.Name)..." -ForegroundColor Yellow
    
    # Verificar se o arquivo de entrada existe
    if (-not (Test-Path $template.Input)) {
        Write-Host "❌ Arquivo não encontrado: $($template.Input)" -ForegroundColor Red
        $errorCount++
        Write-Host ""
        continue
    }
    
    # Executar o comando mjml
    try {
        $result = & mjml $template.Input -o $template.Output 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $($template.Name) compilado com sucesso!" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "❌ Erro ao compilar $($template.Name)" -ForegroundColor Red
            Write-Host "   Detalhes: $result" -ForegroundColor DarkRed
            $errorCount++
        }
    }
    catch {
        Write-Host "❌ Erro ao executar mjml para $($template.Name)" -ForegroundColor Red
        Write-Host "   Detalhes: $($_.Exception.Message)" -ForegroundColor DarkRed
        $errorCount++
    }
    
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "           COMPILAÇÃO FINALIZADA!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resultados:" -ForegroundColor White
Write-Host "✅ Sucessos: $successCount" -ForegroundColor Green
Write-Host "❌ Erros: $errorCount" -ForegroundColor Red
Write-Host "📁 Total processados: $totalTemplates" -ForegroundColor White
Write-Host ""

if ($successCount -eq $totalTemplates) {
    Write-Host "🎉 Todos os templates foram compilados com sucesso!" -ForegroundColor Green
} elseif ($successCount -gt 0) {
    Write-Host "⚠️ Alguns templates foram compilados com sucesso, mas houveram erros." -ForegroundColor Yellow
} else {
    Write-Host "💥 Nenhum template foi compilado com sucesso. Verifique os erros acima." -ForegroundColor Red
}

Write-Host ""
Write-Host "Verifique o diretório templates/ para os arquivos HTML gerados." -ForegroundColor Cyan
Write-Host ""
Read-Host "Pressione Enter para continuar" 