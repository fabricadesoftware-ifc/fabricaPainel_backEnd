---
flow: submissao-ate-aprovacao
commit: back eabb8e9; front 9c2a5c4
status: A-01 a A-04 aprovados e implementados; A-05 a A-09 aguardando decisão
---

# Decisões: Submissão até aprovação

Marque cada achado com **aprovar**, **reprovar** ou **ajustar** (e comente).
Só os aprovados viram implementação. Fluxo mapeado em [flow.md](flow.md).

Ordem: severidade, depois custo.

## A-01 · Gerar o link do e-mail troca o token e invalida o link anterior · severidade: alta

- **Evidência:** `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/work_path.py:6-9`, `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/work_path.py:26-28`, `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/work_path.py:35-38`, `fabricaPainel_frontEnd/src/stores/advisorAcceptance.ts:132-135`
- **O que o código faz:** cada chamada de `work_path`, `work_collaborator_path` e `work_path_submission` grava um novo `verification_token` no registro. O backend responde 404 "Trabalho não encontrado" para token que não existe mais, e o front traduz 404 em "Esta decisão já foi tomada".
- **Por que importa:** qualquer novo e-mail (reenvio, lembrete, atualização do trabalho, troca de orientador) mata os links dos e-mails anteriores. Quem clica no e-mail antigo vê "decisão já tomada" ou 404 sem ter decidido nada. É uma das causas possíveis do 404 relatado. Vale em produção sempre que houver mais de um e-mail por trabalho.
- **Proposta:** gerar o token uma vez (já existe em F3) e só rotacionar depois de uma decisão. Separar no front "link antigo" de "já decidido" com mensagem própria e botão "abrir meu trabalho".
- **Custo:** médio · **Risco da mudança:** médio (mexe em todos os e-mails de convite)
- **Certeza:** verificado (comportamento do código). Inferido: quantos e-mails por trabalho saem na prática.
- **Decisão:** [x] aprovar  [ ] reprovar  [ ] ajustar
- **Implementado:** ajustes: token também troca quando o orientador é trocado (PATCH).

## A-02 · Aceite do orientador é feito em duas chamadas que podem ficar pela metade · severidade: alta

- **Evidência:** `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/accept_advisor_work.py:67-76`, `fabricaPainel_frontEnd/src/stores/advisorAcceptance.ts:100-126`, `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/submission_work.py:32-39`
- **O que o código faz:** `accept_advisor_work` grava `advisor_status` aprovado e rotaciona o token; só depois o front chama `accept_submission` com o token novo (3 tentativas). Se as 3 falharem, o trabalho fica com orientador aprovado e status Pendente, e o link original já não existe mais.
- **Por que importa:** o orientador vê "orientação aceita, mas falha ao concluir", recarrega a página do e-mail e recebe "decisão já tomada". O trabalho só sai de Pendente se ele achar o botão de aprovar dentro do painel.
- **Proposta:** aprovar o trabalho no mesmo request do aceite (extrair a lógica de `accept_submission` para uma função compartilhada e chamá-la dentro de `accept_advisor_work`), mantendo o endpoint antigo por compatibilidade.
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** verificado. Inferido: frequência da falha do segundo passo.
- **Decisão:** [x] aprovar  [ ] reprovar  [ ] ajustar
- **Implementado:** `accept_submission` ficou idempotente e continua existindo para trabalhos que já estavam presos; resposta mantém `verification_token: null` por compatibilidade com o front em cache.

## A-03 · Rota `needs-changes-work` quebrada e sem checagem de dono · severidade: média

- **Evidência:** `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/needs_changes_work.py:25`, `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/needs_changes_work.py:40`, `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/needs_changes_work.py:53`, `fabricaPainel_backEnd/src/django_project/urls.py:57-59`, `fabricaPainel_frontEnd/src/services/editions.ts:46-48`
- **O que o código faz:** usa `edition.final_advisor_date`, campo que não existe no modelo de edição (os campos são `final_advisor_acceptance` e `final_second_advisor_date`), então termina em erro 500. Carrega o trabalho por `pk` sem conferir se o usuário é o orientador dele. O front tem `submitFeedback` apontando para essa rota, mas passa `editionId` e nenhuma tela o chama.
- **Por que importa:** hoje é código morto que devolve 500. Se alguém "consertar" só o nome do campo, qualquer professor orientador passa a poder pedir ajustes em qualquer trabalho.
- **Proposta:** remover a rota e o `submitFeedback`, ou corrigi-los (campo certo, janela do orientador, `work.advisor_id == request.user.id`).
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** verificado (campo inexistente em `fabricaPainel_backEnd/src/core/edition/infra/edition_django_app/models.py:37-52`).
- **Decisão:** [x] aprovar  [ ] reprovar  [ ] ajustar
- **Implementado:** rota, view e `submitFeedback` do front removidos.

## A-04 · Aceitar ou recusar com token não confere se o usuário é o orientador do trabalho · severidade: média

- **Evidência:** `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/accept_advisor_work.py:25-33`, `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/submission_work.py:22-30`, `fabricaPainel_backEnd/src/django_project/permissions.py:93-98`
- **O que o código faz:** a permissão `IsAdvisor` só pede usuário professor com `is_advisor`; quem tiver o token decide. O token só aparece na API para o próprio orientador (`fabricaPainel_backEnd/src/core/work/infra/work_django_app/serializers.py:176-183`) e vai por e-mail para ele.
- **Por que importa:** depende do token vazar (e-mail encaminhado, link copiado). O risco é baixo na prática, mas a decisão é irreversível e envia e-mails aos alunos.
- **Proposta:** exigir `work.advisor_id == request.user.id` nas quatro views de decisão, com 403 e mensagem clara.
- **Custo:** pequeno · **Risco da mudança:** baixo (o orientador legítimo já é o dono)
- **Certeza:** verificado.
- **Decisão:** [x] aprovar  [ ] reprovar  [ ] ajustar
- **Implementado:** 403 nas 4 views quando o usuário não é o orientador do trabalho.

## A-05 · `reject_submission` não tem as travas do aceite · severidade: média

- **Evidência:** `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/submission_work.py:84-106`, comparar com `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/submission_work.py:32-56`
- **O que o código faz:** o aceite confere orientador aprovado e janela do orientador. A rejeição vai direto a "Pendente com Alterações", zera o token, grava a data e manda e-mail aos alunos, sem conferir janela, `advisor_status` nem status atual.
- **Por que importa:** fora do período, ou com o orientador ainda pendente, um clique manda e-mail aos alunos e muda o status. O aluno passa a acreditar que há prazo de ajuste que não existe.
- **Proposta:** aplicar as mesmas travas do aceite (janela e `advisor_status` aprovado) e recusar se o status já for Aprovado, Rejeitado ou Expirado.
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** verificado.
- **Decisão:** [ ] aprovar  [ ] reprovar  [ ] ajustar
- **Comentário:** as travas (orientação aprovada, janela do orientador e status em análise) entraram junto com A-04 por estarem na mesma view; confirmar ou reverter.

## A-06 · A expiração olha todas as edições e reenvia o PDF com todos os expirados · severidade: média

- **Evidência:** `fabricaPainel_backEnd/src/core/work/domain/tasks/change_status/change_status_to_expired_works.py:23-24`, `fabricaPainel_backEnd/src/core/work/domain/tasks/change_status/change_status_to_expired_works.py:43-45`, `fabricaPainel_backEnd/src/core/work/domain/tasks/change_status/change_status_to_expired_works.py:76-81`, `fabricaPainel_backEnd/src/core/edition/domain/tasks/work_expiration_task.py:20-53`
- **O que o código faz:** a task seleciona Pendente e Pendente com Alterações de qualquer edição, não da edição que gerou o agendamento. Marca como Expirado o `advisor_status` pendente de qualquer trabalho. O PDF enviado aos admins lista todos os trabalhos já expirados, de todas as edições, a cada execução. No bloco de erro, `to_email` só existe se o laço rodou; sem admin cadastrado, o `except` levanta `NameError`.
- **Por que importa:** com duas edições abertas, a task de uma edição expira trabalhos da outra. Os admins recebem PDFs cada vez maiores e repetidos. Depende de existir mais de uma edição com trabalhos pendentes ao mesmo tempo, e das tarefas estarem de fato agendadas (F13a, inferido).
- **Proposta:** passar o id da edição como argumento da task e filtrar por ela; listar no PDF só os trabalhos expirados nessa execução; inicializar `to_email` antes do laço.
- **Custo:** médio · **Risco da mudança:** médio (altera uma tarefa agendada que já existe no banco do beat)
- **Certeza:** verificado nos filtros. Inferido: comportamento em produção.
- **Decisão:** [ ] aprovar  [ ] reprovar  [ ] ajustar
- **Comentário:**

## A-07 · Aviso de prazo no e-mail de atualização usa a janela errada · severidade: baixa

- **Evidência:** `fabricaPainel_backEnd/src/core/work/domain/tasks/send_email_advisor/send_work_update_to_advisor.py:43-47`, `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/acceptance_window.py:9-24`
- **O que o código faz:** o aviso "ainda não pode decidir" é calculado com as datas de submissão dos alunos. A decisão do orientador usa `advisor_decision_windows`, e o próprio docstring dessa função explica por que as submissões não servem para isso.
- **Por que importa:** o e-mail pode dizer que o orientador já pode decidir quando a janela dele ainda não abriu (ou o contrário).
- **Proposta:** usar `advisor_decision_windows(work.edition)` no aviso.
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** verificado.
- **Decisão:** [ ] aprovar  [ ] reprovar  [ ] ajustar
- **Comentário:**

## A-08 · Botões do e-mail de aprovação apontam para a API, não para o painel · severidade: baixa

- **Evidência:** `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/work_path.py:35-49`, `fabricaPainel_backEnd/src/core/__seedwork/domain/actions/work_path.py:11-14`, `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/work.py:1476-1489`
- **O que o código faz:** `work_path_submission` monta links diretos para `GET /api/accept-submission/<token>/` e `reject-submission`, que exigem JWT no cabeçalho e têm efeito colateral. O comentário em `work_path` diz que os outros botões foram movidos para uma página do painel justamente para evitar isso.
- **Por que importa:** quem clica no e-mail cai em resposta crua da API (401 ou JSON), não em tela de decisão. Só vale se o fluxo `action: submission` do PATCH ainda for usado pelo front (inferido: não achei chamada no front).
- **Proposta:** confirmar se `action=submission` está em uso; se não, remover `work_path_submission` e `notify_advisor_on_data_update`; se sim, levar os links para uma página do painel como a de `/decidir-orientacao`.
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** inferido (falta confirmar uso em produção).
- **Decisão:** [ ] aprovar  [ ] reprovar  [ ] ajustar
- **Comentário:**

## A-09 · Recusa repetida devolve 204 com corpo e checa o campo errado · severidade: baixa

- **Evidência:** `fabricaPainel_backEnd/src/core/work/infra/work_django_app/views/reject_advisor_work.py:28-35`
- **O que o código faz:** para trabalho "já rejeitado" confere `work.status == 4` (status do trabalho), mas a recusa do orientador grava `advisor_status`, então essa condição nunca reflete a própria recusa. A resposta usa 204 (sem conteúdo) com um corpo de erro e com texto cortado ("rejeitad").
- **Por que importa:** pequeno, mas confunde quem integra e o front, que só trata 404 como "já decidido".
- **Proposta:** checar `advisor_status`, responder 400 ou 409 com mensagem completa.
- **Custo:** pequeno · **Risco da mudança:** baixo
- **Certeza:** verificado.
- **Decisão:** [ ] aprovar  [ ] reprovar  [ ] ajustar
- **Comentário:** a checagem de `advisor_status` e a resposta 400 com mensagem completa entraram junto com A-04; confirmar ou reverter.

## Registro de reprovados

| ID | Motivo da reprovação | Data |
|----|----------------------|------|
