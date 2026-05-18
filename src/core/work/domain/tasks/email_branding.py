def build_panel_email(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
</head>
<body style="margin:0;background:#f4f7fb;font-family:Poppins,Segoe UI,Arial,sans-serif;color:#243447;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #dfe7ef;border-radius:8px;overflow:hidden;">
          <tr>
            <td style="background:#1F8BDD;padding:22px 28px;color:#ffffff;">
              <div style="font-size:13px;font-weight:600;letter-spacing:.2px;">Painel de Integração</div>
              <div style="font-size:24px;font-weight:700;line-height:1.25;margin-top:4px;">{title}</div>
              <div style="font-size:14px;opacity:.9;margin-top:6px;">IFC Araquari</div>
            </td>
          </tr>
          <tr>
            <td style="padding:28px;font-size:16px;line-height:1.6;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="background:#f8fafc;padding:18px 28px;color:#66788a;font-size:13px;line-height:1.5;border-top:1px solid #edf2f7;">Mensagem automática do Painel de Integração do IFC Araquari. Em caso de dúvidas, entre em contato com a equipe da Fábrica de Software.</td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
