@echo off
echo Compilando todos os templates MJML...

mjml templates/mjml/send_collaborator_email_template.mjml -o templates/send_collaborator_email_template.html

mjml templates/mjml/send_advisor_email_template.mjml -o templates/send_advisor_email_template.html

mjml templates/mjml/send_work_aaprove_to_student_template.mjml -o templates/send_work_aaprove_to_student_template.html

mjml templates/mjml/send_work_reject_advisor_to_student_template.mjml -o templates/send_work_reject_advisor_to_student_template.html

mjml templates/mjml/send_forget_password_email_template.mjml -o templates/send_forget_password_email_template.html

mjml templates/mjml/send_needs_changes_to_work_template.mjml -o templates/send_needs_changes_to_work_template.html

mjml templates/mjml/send_email_to_member.template.mjml -o templates/send_email_to_member.template.html

mjml templates/mjml/send_work_update_email_to_advisor_template.mjml -o templates/send_work_update_email_to_advisor_template.html

echo Compilacao concluida! 