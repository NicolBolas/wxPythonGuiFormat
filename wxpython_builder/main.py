"""
Contains a simplified function to load an XML file and start it as an application. It will only return when the main window is closed.
"""

from .load import load_gui

def application(xml_path):
    """
    This function loads the given XML file, creates a `wxApp` class,
    opens the main window, and enters the app's main-loop.
    
    This function will raise any exception raised by the following functions:
        `load.load_gui`.
    """
    pass
