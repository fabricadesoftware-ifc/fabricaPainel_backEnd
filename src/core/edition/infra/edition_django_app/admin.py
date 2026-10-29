from django.contrib import admin, messages
from .models import Edition, EvaluationDailyWindow


class EvaluationDailyWindowInline(admin.TabularInline):
    model = EvaluationDailyWindow
    extra = 1


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    inlines = [EvaluationDailyWindowInline]
    list_display = ("edition_name", "year", "theme", "event_date", "final_event_date")
    search_fields = ("edition_name", "theme", "=year")
    search_help_text = "Pesquise por: nome, tema ou ano (exato). Exemplos: 'integração', '2025'"
    ordering = ("-year",)
    actions = ["preview_pending_grades", "send_pending_grades_reminders"]

    @admin.action(description="Ver quem ainda deve nota (não envia e-mail)")
    def preview_pending_grades(self, request, queryset):
        from core.work.domain.grade_reminders import send_grade_reminders

        for edition in queryset:
            summary = send_grade_reminders(edition, dry_run=True)
            self.message_user(
                request,
                f"{edition}: {summary['advisors']} orientador(es) e "
                f"{summary['evaluators']} avaliador(es) com nota pendente. "
                f"Orientadores: {', '.join(summary['advisor_names']) or '-'}. "
                f"Avaliadores: {', '.join(summary['evaluator_names']) or '-'}.",
                messages.INFO,
            )

    @admin.action(description="Enviar lembrete de nota pendente (orientadores e avaliadores)")
    def send_pending_grades_reminders(self, request, queryset):
        from core.work.domain.grade_reminders import send_grade_reminders

        for edition in queryset:
            summary = send_grade_reminders(edition)
            level = messages.WARNING if summary["failed"] else messages.SUCCESS
            self.message_user(
                request,
                f"{edition}: {summary['emails_sent']} e-mail(s) enviado(s) "
                f"({summary['advisors']} orientador(es), {summary['evaluators']} avaliador(es)); "
                f"{summary['failed']} falha(s).",
                level,
            )


@admin.register(EvaluationDailyWindow)
class EvaluationDailyWindowAdmin(admin.ModelAdmin):
    list_display = ("edition", "date", "opens_at", "closes_at")
    list_filter = ("edition", "date")
    ordering = ("edition", "date")