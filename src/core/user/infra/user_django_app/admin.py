from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User, Evaluator

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
    list_display = ("user",)
    search_fields = ("user",)
    ordering = ("user",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
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
        "count_crosscuttingtheme",
    )

    def count_crosscuttingtheme(self, obj):
        return obj.crosscuttingtheme_set.count()

    list_filter = (
        "email",
        "name",
        "registration",
        "is_staff",
        "is_active",
        "is_advisor",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            _("Personal info"),
            {"fields": (["user_type", "is_advisor"])},
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
                    "user_type",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = ["date_joined", "last_login"]
