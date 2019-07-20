
class WxPythonBuilderError(Exception):
    """Common Base class for all exceptions raised by this system
    directly.
    
    All derived classes are supposed to create a `message` member.
    """

    def __str__(self):
        return self.message


class InvalidElementNameError(WxPythonBuilderError):
    """Raised when an element name is not, and never can be, used."""

    def __init__(self, elem_name):
        self.message = f"The element {elem_name} is never a legal element."


class ElementNotSupportedError(WxPythonBuilderError):
    """Raised when an element is found that doesn't match the given context."""
    
    def __init__(self, elem_name, context):
        self.message = f"The element {elem_name} cannot be used {context}."

class MissingRequiredAttribError(WxPythonBuilderError):
    """Raised when an element needs an attribute that is not found."""
    
    def __init__(self, elem, attrib):
        self.message = f"The element {elem.tag} must have the attribute {attrib}."
        

class MultipleUseOfIdError(WxPythonBuilderError):
    """Raised when ids conflict within the same context."""
    
    def __init__(self, id, elem, context):
        self.message = f"The element {elem.tag} has an id '{id}' which has already been used by a {context}."


class InvalidBooleanAttribute(WxPythonBuilderError):
    """Raised for boolean attributes that don't contain a boolean value."""
    
    def __init__(self, elem, attrib):
        self.message = f"The attribute {attrib} on element {elem.tag} must be either 'true' or 'false'"
    

class InvalidAttribValueError():
    """Raised for an attribute whose given value is invalid."""
    
    def __init__(self, elem, attrib, value):
        self.message = f"The attribute {attrib} on element {elem.tag} has the value '{value}', which is invalid."
    