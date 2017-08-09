from django import template
from django.utils.safestring import mark_safe


register = template.Library()

def deepest_instance(x):
    """
    Simulate true inheritance given an instance of
    an object that uses multi-table inheritance.
    E.g., if Z is a subclass of Y which is a subclass of X,
    instantiating a Z() will result in an X whose .y is a Y, whose .z is a Z.
    deepest_instance(x) returns x.y.z.
    This is only necessary to access a database field defined by Z
    (methods inherit normally).
    """
    inst = x
    typ = type(x)
    #s = str(inst)
    while inst:
        # list the subclasses of 'typ' which are instantiated as attributes of 'inst'
        sub = [cls for cls in typ.__subclasses__() if hasattr(inst, cls.__name__.lower())]
        if not sub:
            break
        typ = sub[0]
        # dot into the corresponding attribute of the instance
        inst = getattr(inst, typ.__name__.lower())
        #s += '.' + y.__name__.lower()
    return inst

@register.simple_tag(takes_context=True)
def metadata_display(context, metadata):
    md = deepest_instance(metadata)
    # metadata = metadata.metadatarevision.supersenserevision
    display = '<h2> Supersense: '+ md.name + '</h2>' + '<ul><li>Animacy: '+ str(md.animacy) +'</li>'
    if md.counterpart:
        display += '<li>Counterpart: <a href=/'+deepest_instance(md.counterpart.current_revision).name+'>' + deepest_instance(md.counterpart.current_revision).name +'</a></li></ul>'
    else:
        display += '<li>This supersense does not have a counterpart.</li></ul>'
    return mark_safe(display)
