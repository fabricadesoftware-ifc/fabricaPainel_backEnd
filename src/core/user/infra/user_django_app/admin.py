from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User, Evaluator, Class, UserClass, Specialty, Certificate
from core.work.infra.work_django_app.models import Team

# class WithCrossCuttingTheme(admin.SimpleListFilter):
#     def lookups(self, request, model_admin):
#         return [
#             True, "Sim",
#             False, "Não",
#         ]

#     def queryset(self, request, queryset):
#         if self.value:
#             return queryset.filter(len(crosscuttingtheme_set.all())>0)
#         else:
#             return queryset


@admin.register(Evaluator)
class EvaluatorAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]


class TeamEditionYearFilter(admin.SimpleListFilter):
    title = "Ano (Equipe)"
    parameter_name = "team_edition_year"

    def lookups(self, request, model_admin):
        years = (
            Team.objects.values_list("edition__year", flat=True)
            .distinct()
            .order_by("edition__year")
        )
        options = [("none", "Não tem")]
        options.extend([(str(year), str(year)) for year in years if year is not None])
        return options

    def queryset(self, request, queryset):
        value = self.value()
        if value == "none":
            return queryset.filter(team__isnull=True)
        if value:
            return queryset.filter(team__edition__year=value).distinct()
        return queryset


class HasClassFilter(admin.SimpleListFilter):
    title = "Tem turma?"
    parameter_name = "has_class"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Tem"),
            ("no", "Não tem"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(user_classes__isnull=False).distinct()
        if value == "no":
            return queryset.filter(user_classes__isnull=True)
        return queryset


class ClassNameFilter(admin.SimpleListFilter):
    title = "Turma"
    parameter_name = "class_id"

    def lookups(self, request, model_admin):
        classes = Class.objects.all().order_by("name").values_list("id", "name")
        return [(str(cid), name) for cid, name in classes]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(user_classes__class_name__id=value).distinct()
        return queryset


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    @admin.display(boolean=True, description="É avaliador?")
    def is_evaluator_display(self, obj):
        return hasattr(obj, "evaluator")

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email",
        "name",
        "registration",
        "is_staff",
        "is_active",
        "is_advisor",
        "is_evaluator_display",
        "classes_display",
    )

    @admin.display(description="Turmas")
    def classes_display(self, obj):
        classes = obj.user_classes.all().select_related("class_name").order_by("-year")
        names = [uc.class_name.name for uc in classes if uc.class_name]
        return ", ".join(names) if names else "Sem turma"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("user_classes__class_name")

    list_filter = (
        "is_staff",
        "is_active",
        "is_advisor",
        "is_collaborator",
        "user_type",
        TeamEditionYearFilter,
        HasClassFilter,
        ClassNameFilter,
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "name",
                    "registration",
                    "specialities",
                )
            },
        ),
        (
            _("Personal info"),
            {
                "fields": (
                    [
                        "user_type",
                        "is_advisor",
                        "is_collaborator",
                        "is_evaluator_display",
                    ]
                )
            },
        ),
        (
            _("Permissions"),
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "registration",
                    "is_advisor",
                    "is_collaborator",
                    "specialities",
                    "user_type",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = (
        "email",
        "name",
        "registration",
        "user_classes__class_name__name",
        "=user_classes__year",
    )
    search_help_text = (
        "Pesquise por: email, nome, matrícula, nome da turma ou ano da turma (exato). "
        "Exemplos: 'joao', '2info1', '2025'"
    )
    ordering = ("email",)
    readonly_fields = ["date_joined", "last_login", "is_evaluator_display"]


admin.site.register(Specialty)
admin.site.register(Class)


@admin.register(UserClass)
class UserClassAdmin(admin.ModelAdmin):
    list_display = ("user", "class_name")
    search_fields = ("user__name", "user__email", "class_name__name", "=year")
    search_help_text = (
        "Pesquise por: nome do usuário, email, nome da turma ou ano (exato). "
        "Exemplos: 'maria', '1info2', '2025'"
    )
    list_filter = ("class_name", "year")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "work", "created_at", "updated_at")
    search_fields = ("user__name", "user__email", "work__title", "hash_validate")
    autocomplete_fields = ("user", "work")
    list_filter = ("created_at", "updated_at")
    raw_id_fields = ("user", "work")
    readonly_fields = ("hash_validate", "created_at", "updated_at")
    ordering = ("-created_at",)
