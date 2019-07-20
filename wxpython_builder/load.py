"""
Provides the definitions for `build_gui` and `load_gui`, as well as the code for loading the app element and children thereof.
"""

from .gui import Gui, GuiContainer
from .exceptions import *
from .load_common import *
from lxml import etree
import wx
import wx.aui


class _FrameCloser:
    """Used for closing frame windows. You have to remove the AUI
    before they get destroyed."""
    
    def __init__(self, frame, aui):
        self._frame = frame
        self._aui = aui


    def __call__(self, event):
        self._aui.UnInit()
        self._frame.Destroy()
        

class _FrameElemProcs:
    """
    Class whose attributes are functions that process elements which are children of frames.
    """
    
    def __init__(self, frame_elem):
        self._id = require_attrib(frame_elem, "id")
        
        frame_size = get_wnd_size(frame_elem)
        title = require_attrib(frame_elem, "title")
        
        self._frame = wx.Frame(None, title = title, size = frame_size)

        self._aui = wx.aui.AuiManager(self._frame)
        
        self._frame.Bind(wx.EVT_CLOSE, _FrameCloser(self._frame, self._aui))
        
        #Contains panels and toolbars.
        self._panels = []
        self._id_map = {}

        
    def panel(self, elem):
        pl = wx.Panel(self._frame)
        self._panels.append(pl)
        
        panel = self._panels[-1]
        pane_info = wx.aui.AuiPaneInfo().Center() 
        self._aui.AddPane(panel, pane_info)


class _RootElemProcs:
    """
    Class whose attributes are functions that process elements which are
    children of the root.
    """

    def __init__(self):
        self._frames = {}
        pass
    
    
    def frame(self, elem):
        frame_procs = _FrameElemProcs(elem)
        if frame_procs._id in self._frames:
            raise MultipleUseOfIdError(frame_procs._id, elem, "main window")

        self._frames[frame_procs._id] = frame_procs
        
        process_elements(frame_procs, elem, "as the child of a frame")
        
        print(frame_procs._frame)
        frame_procs._frame.Hide()
        frame_procs._frame.Layout()
        frame_procs._aui.Update()

    
def build_gui(app_element, app):
    """
    Builds the `Gui` object from the given root XML element, which must be
    an `app` element.
    
    Any XIncludes are expected to have already been processed.
    """
    
    if app_element.tag != "app":
        raise ElementNotSupportedError(app_element, "as the root")
    
    root_data = process_elements(_RootElemProcs(), app_element,
        "as the child of the root element")

    #TODO: Generate GUI from `root_data`.
    
    frame_map = {}
    for id, frame in root_data._frames.items():
        container = GuiContainer(frame._frame, None)
        container._aui = frame._aui
        frame_map[id] = container
        
    
    return Gui(app, frame_map)


def load_gui(xml_path, app):
    """
    Loads the XML file (processing XIncludes), and builds a `Gui` object
    out of them.
    """
    root = etree.parse(xml_path)
    return build_gui(root.getroot(), app)
