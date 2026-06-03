from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.user.domain.value_objects import UserType
from core.work.domain.value_objects import WorkStatusType
from core.user.infra.user_django_app.models import Evaluator


class RolePermission(BasePermission):
    """
    Base genérica para permissões por papel (UserType).
    Se `require_auth` for True, exige autenticação sempre;
    caso contrário, permite leitura anônima.
    """
    role = None  # definir como UserType.*
    require_auth = False

    def has_permission(self, request, view):
        user = request.user
        if self.require_auth and not user.is_authenticated or user.is_anonymous:
            return False

        if request.method in SAFE_METHODS:
            return True

        if not user or not user.is_authenticated:
            return False

        return getattr(user, 'user_type', None) == self.role

class IsAdmin(RolePermission):
    role = UserType.Type.ADMIN
    require_auth = True

class IsAdminOrManagement(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated and (
                user.user_type == UserType.Type.ADMIN or
                getattr(user, 'is_management', False)
            )
        )

class IsAdminOrReadOnly(RolePermission):
    role = UserType.Type.ADMIN
    require_auth = False

class IsStudent(RolePermission):
    role = UserType.Type.STUDENT
    require_auth = True

class IsStudentOrReadOnly(RolePermission):
    role = UserType.Type.STUDENT
    require_auth = False

class IsTeacher(RolePermission):
    role = UserType.Type.TEACHER
    require_auth = True

class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated and
            user.user_type in [UserType.Type.TEACHER, UserType.Type.ADMIN]
        )
    
class IsAdvisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user.is_authenticated and
                    user.user_type == UserType.Type.TEACHER and
                    getattr(user, 'is_advisor', False))

class IsAdvisor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and
                    user.user_type == UserType.Type.TEACHER and
                    getattr(user, 'is_advisor', False))
        
class IsNotStudent(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and
                    user.user_type != UserType.Type.STUDENT)

class IsCollaboratorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user.is_authenticated and
                    user.user_type != UserType.Type.STUDENT and
                    getattr(user, 'is_collaborator', False))

class IsCollaborator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and
                    user.user_type != UserType.Type.STUDENT and
                    getattr(user, 'is_collaborator', False))

class IsUserOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj == request.user 
        return request.user.is_authenticated and request.user.user_type == UserType.Type.ADMIN

class IsAdvisorOrTeamMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if user.is_authenticated and user.user_type == UserType.Type.TEACHER and user.is_advisor:
            return True

        if request.method in SAFE_METHODS:
            return user.is_authenticated 

        return False

    def has_object_permission(self, request, view, obj):    
        user = request.user

        if request.method in SAFE_METHODS and user.is_authenticated and obj.work.team.team_members.filter(id=user.id).exists():
            return True

        return user.is_authenticated and obj.work.advisor == user
    

class IsAdvisorOrEvaluatorOrTeamMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if Evaluator.objects.filter(user=user.id).exists():
            return True

        if getattr(user, 'is_advisor', False):
            return True

        if request.method in SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):    
        user = request.user

        if not user.is_authenticated:
            return False

        is_team_member = obj.work.team.team_members.filter(id=user.id).exists()
        is_advisor = obj.work.advisor_id == user.id
        is_evaluator = obj.work.evaluator.filter(user=user.id).exists()

        if request.method in SAFE_METHODS:
            return is_team_member or is_advisor or is_evaluator

        return is_advisor or is_evaluator
    

    
class IsWorkOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        return request.user.user_type == UserType.Type.STUDENT

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            # Permite leitura se:
            # - o usuário for um dos avaliadores
            # - OU o trabalho estiver aprovado
            if user.is_authenticated and obj.evaluator.filter(user=user.id).exists():
                return True
            if obj.status == WorkStatusType.Type.APPROVED.value:
                return True
            return True

        if not user.is_authenticated:
            return False

        return bool(
            obj.team.team_members.filter(id=user.id).exists() or
            obj.advisor == user or
            obj.work_collaborator.filter(collaborator=user.id).exists()
        )
