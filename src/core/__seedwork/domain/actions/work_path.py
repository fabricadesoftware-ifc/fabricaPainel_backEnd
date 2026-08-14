from uuid import uuid4
from django.urls import reverse
from django_project.settings import API_URL, PAINEL_URL


def work_path(instance, **kwargs):
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    # Os botões do email (aceitar/rejeitar) levam para a mesma página no
    # painel (frontend), que mostra os dois botões de verdade e chama a API
    # por trás — em vez do clique ir direto pro backend e mostrar JSON cru
    # (ou um erro sem contexto) pro usuário.
    painel_url = PAINEL_URL.rstrip('/')
    advisor_decision_link = f"{painel_url}/decidir-orientacao/{token}"
    collaborator_decision_link = f"{painel_url}/decidir-colaboracao/{token}"

    return advisor_decision_link, advisor_decision_link, collaborator_decision_link, collaborator_decision_link

def work_collaborator_path(work_collaborator_instance):
    """
    Gera o link (por convite de colaborador) que leva à página de decisão no
    painel — usa o token do próprio WorkCollaborator.
    """
    token: str = str(uuid4())
    work_collaborator_instance.verification_token = token
    work_collaborator_instance.save()

    painel_url = PAINEL_URL.rstrip('/')
    collaborator_decision_link = f"{painel_url}/decidir-colaboracao/{token}"

    return collaborator_decision_link, collaborator_decision_link

def work_path_submission(instance, **kwargs):
    token: str = str(uuid4())
    instance.verification_token = token
    instance.save()

    # Remove qualquer barra dupla do API_URL
    base_url = API_URL.rstrip('/')

    accept_work_path = reverse("accept-submission", kwargs={"verification_token": token})
    reject_work_path = reverse("reject-submission", kwargs={"verification_token": token})
    
    accept_work_link = f"{base_url}{accept_work_path}"
    reject_work_link = f"{base_url}{reject_work_path}"

    return accept_work_link, reject_work_link