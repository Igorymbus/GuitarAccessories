from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Безопасно получить значение из словаря по ключу в шаблоне."""
    try:
        return dictionary.get(key)
    except Exception:
        return None


