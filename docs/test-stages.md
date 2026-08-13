# Estagios de teste manual

Use o comando abaixo para preparar o banco local em um ponto especifico do fluxo:

```powershell
pdm run tests --stage 4
```

Para ver todos os estagios:

```powershell
pdm run tests --list
```

O comando cria um cenario guiado com usuarios, edicao, equipe, trabalho e avaliacoes conforme o estagio solicitado. Ele tambem reposiciona o trabalho de teste quando voce volta para um estagio anterior.

Senha padrao dos usuarios criados:

```text
Painel@123
```

## Estagios

1. Base pronta: usuarios, turma, area, tema, ODS e edicao com datas abertas.
2. Equipe criada para o aluno testar a tela de criacao/edicao da proposta.
3. Trabalho submetido, aguardando aceite do orientador.
4. Orientador aceitou e aprovou o trabalho, colaborador ainda pendente.
5. Colaborador aceitou e avaliador foi vinculado, pronto para tela de avaliacao.
6. Avaliacoes lancadas e relatorio pronto para conferencia.

## Contas

- Aluno: `stage.student@ifc.local`
- Segundo aluno: `stage.student2@ifc.local`
- Orientador: `stage.advisor@ifc.local`
- Colaborador: `stage.collaborator@ifc.local`
- Avaliador: `stage.evaluator@ifc.local`
- Admin: `stage.admin@ifc.local`

Ao final da execucao, o comando imprime a URL sugerida para abrir no frontend e o usuario recomendado para aquele estagio.
