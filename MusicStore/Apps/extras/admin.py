from django.contrib import admin
from django.utils.html import format_html
from .models import Reviews, Feedback, Analytics


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    """Административная панель для отзывов"""
    list_display = ("reviews_id", "reviews_product", "reviews_user", "reviews_rating_display", "reviews_approved", "reviews_date")
    list_filter = ("reviews_rating", "reviews_approved", "reviews_date")
    search_fields = ("reviews_product__products_name", "reviews_user__users_email", "reviews_comment")
    list_display_links = ("reviews_id", "reviews_product")
    list_editable = ("reviews_approved",)
    date_hierarchy = "reviews_date"
    ordering = ("-reviews_date",)
    readonly_fields = ("reviews_date",)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('reviews_product', 'reviews_user', 'reviews_rating', 'reviews_approved')
        }),
        ('Отзыв', {
            'fields': ('reviews_comment',)
        }),
        ('Дата', {
            'fields': ('reviews_date',),
            'classes': ('collapse',)
        }),
    )
    
    def reviews_rating_display(self, obj):
        """Отображение рейтинга звездочками"""
        stars = '★' * obj.reviews_rating + '☆' * (5 - obj.reviews_rating)
        colors = {
            5: 'green',
            4: 'lightgreen',
            3: 'orange',
            2: 'orangered',
            1: 'red',
        }
        color = colors.get(obj.reviews_rating, 'gray')
        return format_html('<span style="color: {}; font-size: 1.2em;">{}</span>', color, stars)
    reviews_rating_display.short_description = 'Рейтинг'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Административная панель для обратной связи"""
    list_display = ("feedback_id", "feedback_user", "feedback_message_preview", "feedback_responded", "feedback_date")
    list_filter = ("feedback_responded", "feedback_date")
    search_fields = ("feedback_user__users_email", "feedback_message")
    list_display_links = ("feedback_id", "feedback_user")
    list_editable = ("feedback_responded",)
    date_hierarchy = "feedback_date"
    ordering = ("-feedback_date",)
    readonly_fields = ("feedback_date",)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('feedback_user', 'feedback_responded')
        }),
        ('Сообщение', {
            'fields': ('feedback_message',)
        }),
        ('Дата', {
            'fields': ('feedback_date',),
            'classes': ('collapse',)
        }),
    )
    
    def feedback_message_preview(self, obj):
        """Превью сообщения"""
        if obj.feedback_message:
            preview = obj.feedback_message[:50] + '...' if len(obj.feedback_message) > 50 else obj.feedback_message
            return preview
        return "—"
    feedback_message_preview.short_description = 'Сообщение'


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    """Административная панель для аналитики"""
    list_display = ("analytics_id", "analytics_report_type", "analytics_period_start", "analytics_period_end", "analytics_generated_at")
    list_filter = ("analytics_report_type", "analytics_period_start", "analytics_period_end")
    search_fields = ("analytics_report_type",)
    list_display_links = ("analytics_id", "analytics_report_type")
    date_hierarchy = "analytics_period_start"
    ordering = ("-analytics_period_start",)
    readonly_fields = ("analytics_generated_at",)
    
    fieldsets = (
        ('Тип отчета', {
            'fields': ('analytics_report_type',)
        }),
        ('Период', {
            'fields': ('analytics_period_start', 'analytics_period_end')
        }),
        ('Данные', {
            'fields': ('analytics_data',),
            'classes': ('collapse',)
        }),
        ('Дата генерации', {
            'fields': ('analytics_generated_at',),
            'classes': ('collapse',)
        }),
    )
