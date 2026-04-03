from django.contrib import admin
from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'amount', 'category', 'date', 'created_at']
    list_filter = ['type', 'category', 'date']
    search_fields = ['user__username', 'category', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']
