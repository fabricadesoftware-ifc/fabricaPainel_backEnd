# 📧 Compilação de Templates MJML

Este diretório contém scripts para compilar todos os templates MJML para HTML.

## 🔧 Scripts Disponíveis

### 1. `compile_mjml_final.bat` ⭐ **RECOMENDADO**
Script principal otimizado para Windows:
```bash
.\compile_mjml_final.bat
```

### 2. `compile_all_mjml.bat`
Script simples e direto:
```bash
.\compile_all_mjml.bat
```

### 3. `compile_mjml.bat`
Script com verificação de erros (pode ter problemas no PowerShell):
```bash
.\compile_mjml.bat
```

### 4. `compile_mjml.ps1`
Script PowerShell avançado (use apenas se necessário):
```powershell
PowerShell -ExecutionPolicy Bypass -File .\compile_mjml.ps1
```

## 📁 Templates Compilados

Os seguintes templates são compilados automaticamente:

| Template MJML | Arquivo HTML Gerado | Descrição |
|---------------|---------------------|-----------|
| `send_collaborator_email_template.mjml` | `send_collaborator_email_template.html` | Convite para colaboração |
| `send_advisor_email_template.mjml` | `send_advisor_email_template.html` | Notificação para orientador |
| `send_work_aaprove_to_student_template.mjml` | `send_work_aaprove_to_student_template.html` | Aprovação de trabalho |
| `send_work_reject_advisor_to_student_template.mjml` | `send_work_reject_advisor_to_student_template.html` | Rejeição de orientação |
| `send_forget_password_email_template.mjml` | `send_forget_password_email_template.html` | Recuperação de senha |
| `send_needs_changes_to_work_template.mjml` | `send_needs_changes_to_work_template.html` | Mudanças necessárias |
| `send_email_to_member.template.mjml` | `send_email_to_member.template.html` | Convite para membro |
| `send_work_update_email_to_advisor_template.mjml` | `send_work_update_email_to_advisor_template.html` | Atualização para orientador |

## ✅ Verificação

Após executar qualquer script, verifique se os arquivos HTML foram gerados no diretório `templates/`:

```bash
ls templates/*.html
```

## 🎯 Uso Rápido

Para compilar todos os templates rapidamente:

1. Abra o terminal no diretório `src/`
2. Execute: `.\compile_mjml_final.bat`
3. Aguarde a mensagem de sucesso
4. Verifique os arquivos HTML gerados

## 🔍 Resolução de Problemas

- **MJML não encontrado**: Instale globalmente com `npm install -g mjml`
- **Erro de permissão PowerShell**: Use o script `.bat` em vez do `.ps1`
- **Arquivo não compilado**: Verifique se o arquivo MJML fonte existe e está válido
- **PowerShell com problemas**: Use o `compile_mjml_final.bat` que é mais estável

## 📋 Pré-requisitos

- Node.js instalado
- MJML instalado globalmente (`npm install -g mjml`)
- Windows com PowerShell ou Command Prompt 