from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.user.domain.value_objects import UserType

class IsAuthenticated(BasePermission):
    """
    Permissão para apenas usuários autenticados acessarem a view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

class IsAdminOrReadOnly(BasePermission):
    """
    Permissão para permitir apenas administradores escreverem, enquanto outros usuários podem apenas ler.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.Type == UserType.ADMIN
    
class IsAdmin(BasePermission):
    """
    Permissão para permitir apenas administradores escreverem e ler.
    """
    def has_permission(self, request, view):
        return request.user and request.user.Type == UserType.ADMIN
    
class IsStudentOrReadOnly(BasePermission):
    """
    Permissão para permitir apenas estudantes escreverem, enquanto outros usuários podem apenas ler.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.Type == UserType.STUDENT
    
class IsStudent(BasePermission):
    """
    Permissão para permitir apenas estudantes escreverem e ler.
    """
    def has_permission(self, request, view):
        return request.user and request.user.Type == UserType.STUDENT
    
class IsAdvisorOrReadOnly(BasePermission):
    """
    Permissão para permitir apenas advisors escreverem, enquanto outros usuários podem apenas ler.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.Type == UserType.TEACHER and request.user.is_advisor
    
class IsAdvisor(BasePermission):
    """
    Permissão para permitir apenas advisors escreverem e ler.
    """
    def has_permission(self, request, view):
        return request.user and request.user.Type == UserType.TEACHER and request.user.is_advisor
    
class IsCollaboratorOrReadOnly(BasePermission):
    """
    
    Permissão para permitir apenas colaboradores escreverem, enquanto outros usuários podem apenas ler.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.Type != UserType.STUDENT and request.user.is_collaborator
    
class IsCollaborator(BasePermission):
    """
    Permissão para permitir apenas colaboradores escreverem e ler.
    """
    def has_permission(self, request, view):
        return request.user and request.user.Type != UserType.STUDENT and request.user.is_collaborator

class IsUserOwnerOrReadOnly(BasePermission):
    """
    Permissão para permitir apenas o proprietário do objeto escrever e ler.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return obj == request.user

class IsWorkOwnerOrReadOnly(BasePermission):
    """
    Permissão para permitir apenas o proprietário do trabalho escrever e ler.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.team.team_members.filter(id=request.user.id).exists() or obj.advisor == request.user

