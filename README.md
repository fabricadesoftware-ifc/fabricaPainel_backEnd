# Fabrica Painel backend.

## Diagrama do banco de dados.

## Para rodar o sistema é necessário fazer as seguintes etapas:
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
  sudo rabbitmqctl set_permissions -p fabricahistologia SEUUSUARIO ".*" ".*" ".*"
```


## Para rodar o RabbitMQ e o Celery: 

```powershell
 pdm run celery -A django_project worker --loglevel=info
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


![alt text](images/diagram.png)

## Caso de uso do projeto.

![alt text](images/fabricaPainel.png)

## Fluxo do Lider do trabalho.

![alt text](images/fabricaPainel%20(3).png)

## Fluxo do Usuário

![alt text](images/fabricaPainel%20(2).png)




