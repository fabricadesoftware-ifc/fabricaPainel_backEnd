@echo off
echo ================================================
echo          COMPILANDO TEMPLATES MJML
echo ================================================
echo.

echo [1/8] Compilando template de colaborador...
mjml templates/mjml/send_collaborator_email_template.mjml -o templates/send_collaborator_email_template.html
if %errorlevel% == 0 (
    echo ✅ Template de colaborador compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de colaborador
)
echo.

echo [2/8] Compilando template de orientador...
mjml templates/mjml/send_advisor_email_template.mjml -o templates/send_advisor_email_template.html
if %errorlevel% == 0 (
    echo ✅ Template de orientador compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de orientador
)
echo.

echo [3/8] Compilando template de aprovação para estudante...
mjml templates/mjml/send_work_aaprove_to_student_template.mjml -o templates/send_work_aaprove_to_student_template.html
if %errorlevel% == 0 (
    echo ✅ Template de aprovação compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de aprovação
)
echo.

echo [4/8] Compilando template de rejeição para estudante...
mjml templates/mjml/send_work_reject_advisor_to_student_template.mjml -o templates/send_work_reject_advisor_to_student_template.html
if %errorlevel% == 0 (
    echo ✅ Template de rejeição compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de rejeição
)
echo.

echo [5/8] Compilando template de recuperação de senha...
mjml templates/mjml/send_forget_password_email_template.mjml -o templates/send_forget_password_email_template.html
if %errorlevel% == 0 (
    echo ✅ Template de recuperação de senha compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de recuperação de senha
)
echo.

echo [6/8] Compilando template de mudanças necessárias...
mjml templates/mjml/send_needs_changes_to_work_template.mjml -o templates/send_needs_changes_to_work_template.html
if %errorlevel% == 0 (
    echo ✅ Template de mudanças necessárias compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de mudanças necessárias
)
echo.

echo [7/8] Compilando template de convite para membro...
mjml templates/mjml/send_email_to_member.template.mjml -o templates/send_email_to_member.template.html
if %errorlevel% == 0 (
    echo ✅ Template de convite para membro compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de convite para membro
)
echo.

echo [8/8] Compilando template de atualização para orientador...
mjml templates/mjml/send_work_update_email_to_advisor_template.mjml -o templates/send_work_update_email_to_advisor_template.html
if %errorlevel% == 0 (
    echo ✅ Template de atualização para orientador compilado com sucesso!
) else (
    echo ❌ Erro ao compilar template de atualização para orientador
)
echo.

echo ================================================
echo           COMPILAÇÃO FINALIZADA!
echo ================================================
echo.
echo Todos os templates foram processados.
echo Verifique o diretório templates/ para os arquivos HTML gerados.
echo.
pause 