"""
Contains all of the files for loading XML data and building wxWidgets objects from it. It requires the lxml module.
"""

from .gui import Gui

def build_gui(root_element):
    """
    Builds the `Gui` object from the given root XML element, which must be
    an `app` element.
    
    Any XIncludes are expected to have already been processed.
    """
    pass


def load_gui(xml_path):
    """
    Loads the XML file (processing XIncludes), and builds a `Gui` object
    out of them.
    """
    pass
