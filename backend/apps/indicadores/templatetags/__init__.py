from django import template

register = template.Library()


@register.filter
def dict_key(d, key):
    """Retorna el valor de un dict por key. Útil en templates."""
    try:
        return d.get(key)
    except (AttributeError, TypeError):
        return None
