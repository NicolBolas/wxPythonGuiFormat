"""
Contains a simplified function to load an XML file and start it as an application. It will only return when the main window is closed.
"""

from .load import load_gui
from .exceptions import *
import wx

def application(xml_path):
    """
    This function loads the given XML file, creates a `wxApp` class,
    opens the frame window named "main", and enters the main-loop.
    
    This function will raise any exception raised by the following functions:
        `load.load_gui`.
    """
    
    #print("here")
    app = wx.App()
    gui = load_gui(xml_path, app)
    #print("gui loaded")
    if not gui.has_main_wnd():
        raise MainWindowUnavailableError()
    frm = gui.get_main_wnd().wnd()
    #print("main frame found")
    #print(frm)
    frm.Show()
    #print("window shown")
    gui.app().MainLoop()
    #print("post main loop")
    return gui


