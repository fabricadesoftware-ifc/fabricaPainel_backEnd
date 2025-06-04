@echo off
cls
echo ========================================
echo    COMPILADOR DE TEMPLATES MJML
echo ========================================
echo.
echo Iniciando compilacao de todos os templates...
echo.

echo [1/8] Colaborador...
mjml templates/mjml/send_collaborator_email_template.mjml -o templates/send_collaborator_email_template.html

echo [2/8] Orientador...
mjml templates/mjml/send_advisor_email_template.mjml -o templates/send_advisor_email_template.html

echo [3/8] Aprovacao Estudante...
mjml templates/mjml/send_work_aaprove_to_student_template.mjml -o templates/send_work_aaprove_to_student_template.html

echo [4/8] Rejeicao Estudante...
mjml templates/mjml/send_work_reject_advisor_to_student_template.mjml -o templates/send_work_reject_advisor_to_student_template.html

echo [5/8] Recuperacao Senha...
mjml templates/mjml/send_forget_password_email_template.mjml -o templates/send_forget_password_email_template.html

echo [6/8] Mudancas Necessarias...
mjml templates/mjml/send_needs_changes_to_work_template.mjml -o templates/send_needs_changes_to_work_template.html

echo [7/8] Convite Membro...
mjml templates/mjml/send_email_to_member.template.mjml -o templates/send_email_to_member.template.html

echo [8/8] Atualizacao Orientador...
mjml templates/mjml/send_work_update_email_to_advisor_template.mjml -o templates/send_work_update_email_to_advisor_template.html

echo.
echo ========================================
echo    COMPILACAO FINALIZADA COM SUCESSO!
echo ========================================
echo.
echo Todos os 8 templates foram processados.
echo Verifique o diretorio templates/ para os arquivos HTML gerados.
echo.
echo Pressione qualquer tecla para continuar...
pause >nul 