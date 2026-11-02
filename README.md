# Fabrica Painel backend.

API do Painel de Integração da SEPE (Semana de Ensino, Pesquisa e Extensão) do IFC Campus Araquari. Django 5 + Django REST Framework, Celery para e-mails e tarefas agendadas.

Licença: [MIT](LICENSE).

## Rodando na sua máquina

Pré-requisitos: Python 3.12, [PDM](https://pdm-project.org/) e, para gerar o PDF do certificado, as bibliotecas do WeasyPrint (Pango; veja a [documentação](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)). RabbitMQ só é necessário para e-mails/tarefas em segundo plano (veja mais abaixo).

1. Instale as dependências: `pdm install`
2. Copie `.env-exemplo` para `.env` e preencha (o mínimo é `SECRET_KEY`; sem `DATABASE_URL` usa SQLite local)
3. Crie as tabelas: `pdm run migrate`
4. Crie seu usuário admin: `pdm run createsuperuser`
5. (Opcional) Dados de teste: `pdm run populate edition` (veja a seção Populate)
6. Suba a API: `pdm run dev` (http://localhost:8000, admin em `/admin/`)

O front-end roda em http://localhost:3000; veja o README do repositório `fabricaPainel_frontEnd`.

### Variáveis de ambiente

| Variável | Para que serve | Padrão |
|---|---|---|
| `SECRET_KEY` | chave secreta do Django (obrigatória) | – |
| `DEBUG` | `true` em desenvolvimento | `False` |
| `DATABASE_URL` | banco, ex.: `postgres://user:senha@localhost:5432/painel` | SQLite (`db.sqlite3` na pasta onde o comando roda) |
| `PAINEL_URL` | endereço do front (links de e-mail e do certificado) | `http://localhost:3000` |
| `API_URL` | endereço desta API | `http://localhost:8000` |
| `BROKER_URL` | fila do Celery (RabbitMQ), ex.: `amqp://usuario:senha@localhost/fabricapainel` | veja `settings.py` |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | envio de e-mail (em dev use `django.core.mail.backends.console.EmailBackend`) | – |

Testes: `python src/manage.py test --noinput core/<app>/infra/<app>_django_app/tests -t .` (a partir da raiz do repositório).

### Dados de teste e dados reais

O `populate` usa dados **fictícios** (`@exemplo.test`). Dados reais de alunos, professores e servidores **nunca** devem ir para o git. Para popular com dados reais, coloque `students.json`, `teachers.json`, `tae.json` e `advisors.json` numa pasta fora do repositório e aponte `PAINEL_PRIVATE_DATA_DIR` para ela.

## Fila de tarefas (RabbitMQ e Celery)

Para e-mails e tarefas agendadas é necessário fazer as seguintes etapas:
- Instalar o RabbitMQ no seu computador, para sistemas derivados do Debian de o seguinte comando:
```powershell
sudo apt-get update
sudo apt-get install rabbitmq-server
```
- Rodar o servidor RabbitMQ:
  
```powershell
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```
  - Criar o vhost:
    
```powershell
  sudo rabbitmqctl add_vhost fabricapainel
```

- De permissão ao seu usuario no vhost:

```powershell
  sudo rabbitmqctl set_permissions -p fabricapainel SEUUSUARIO ".*" ".*" ".*"
```


## Para rodar o RabbitMQ e o Celery: 

```powershell
 pdm run celery -A django_project worker --loglevel=info
```

- Acessar o Painel de controle do flower:

```powershell
  pdm run python -m celery -A django_project flower
```

## Populate: 

Script created to speed up the process of creating database registers. Used for testing purposes only.

```powershell
pdm run populate [models] [--locale] [--instances]
``` 

- Modes: Obligatory argument. If it's more than one model, it MUST be separated by space.
- Locale: Optional argument. Used to specify the localization to the generator. [Faker's Documentation](https://faker.readthedocs.io/en/stable/index.html#localization).
- Instances: Optional argument. Used to specify the number of created registers to the selected model(s).

Example 1:
```powershell
pdm run populate field
``` 
This command will create: 1 instance (the default can be changed) of the edition model, using brazilian portuguese localization (this default can also be changed).

Example 2:
```powershell
pdm run populate edition --locale it_IT,ja_JP --instances 5
``` 
This command will create: 5 instances of the edition model, using italian and japanese localization.

## Diagrama do banco de dados.

![alt text](images/diagram.png)

## Caso de uso do projeto.

![alt text](images/fabricaPainel.png)

## Fluxo do Lider do trabalho.

![alt text](images/fabricaPainel%20(3).png)

## Fluxo do Usuário

![alt text](images/fabricaPainel%20(2).png)




