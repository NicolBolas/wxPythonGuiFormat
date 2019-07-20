"""Common tools used by the loaders"""


import wx



def process_elements(procs, element, context):
    """
    Iterates through the children of `element`, calling the
    member of `procs` which matches that child element's name.
    `context` is a text description of the kind of processing we're doing.
    """
    for elem in element:
        if elem.tag[0] == "_":
            raise InvalidElementNameError(elem.tag)

        proc = getattr(procs, elem.tag, None)
        if proc:
            proc(elem)
        else:
            raise ElementNotSupportedError(elem.tag, context)

    #`procs` may be stateful, so return it.
    return procs


def get_attrib(elem, attrib, default):
    value = elem.get(attrib, None)
    if not value:
        return default
    return value


def get_attrib_bool(elem, attrib, default):
    value = get_attrib(elem, attrib, default)
    if(value == "false"):
        return False
    if(value == "true"):
        return True
    raise InvalidBooleanAttribute(elem, attrib)


def require_attrib(elem, attrib):
    value = elem.get(attrib, None)
    if not value:
        raise MissingRequiredAttribError(elem, attrib)
    
    return value


def get_wnd_size(elem):
    """Use when size is required."""
    return wx.Size(int(require_attrib(elem, "width")),
            int(require_attrib(elem, "height")))


def get_wnd_size_optional(elem)
    """Use for optional sizes"""
    width = int(get_attrib_bool(elem, "width", "-1"))
    height = int(get_attrib_bool(elem, "height", "-1"))
    return wx.Size(width, height)

