from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.simple_tag(takes_context=True)
def metadata_display(context, metadata):
    metadata = metadata.metadatarevision.supersenserevision
    display = '<h2> Supersense: '+ metadata.name + '</h2>' + '<ul><li>Animacy: '+ str(metadata.animacy) +'</li>'
    if metadata.counterpart:
        display += '<li>Counterpart: <a href=/'+metadata.counterpart.current_revision.supersenserevision.name+'>' + metadata.counterpart.current_revision.supersenserevision.name +'</a></li></ul>'
    else:
        display += '<li>This supersense does not have a counterpart.</li></ul>'
    return mark_safe(display)