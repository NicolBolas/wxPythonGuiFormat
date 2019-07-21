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


_aui_default_name_ix = None

def _calc_aui_default_name():
    name = f"__BuilderDefaultPanel__{_aui_default_name_ix}"
    ++_aui_default_name_ix
    return name


_aui_dock_directions = {
    "top" : wx.aui.AUI_DOCK_TOP,
    "bottom" : wx.aui.AUI_DOCK_BOTTOM,
    "left" : wx.aui.AUI_DOCK_LEFT,
    "right" : wx.aui.AUI_DOCK_RIGHT,
    "center" : wx.aui.AUI_DOCK_CENTER,
}

def _get_aui_pane_info(elem):
    """Parses the AUI info from the element's attributes."""
    pane_info = wx.aui.AuiPaneInfo()
    
    is_toolbar = False
    if elem.tag == "toolbar":
        pane_info.ToolbarPane()
        is_toolbar = True

    #The pane name can be specified, or taken from the id, or generated.
    aui_name = get_attrib(elem, "aui.name")
    if not aui_name:
        aui_name = get_attrib(elem, "id")
        if not aui_name:
            aui_name = _calc_aui_default_name()
            
    pane_info.Name(aui_name)
    
    caption = get_attrib(elem, "aui.caption")
    if caption:
        pane_info.Caption(caption)
    
    #Handling anchoring dock.
    anchor = require_attrib(elem, "aui.dock")
    try:
        pane_info.Direction(_aui_dock_directions[anchor])
    except:
        raise InvalidAttribValueError(elem, "aui.dock", anchor)

    row = get_attrib(elem, "aui.row")
    if row:
        pane_info.Row(int(row))

    layer = get_attrib(elem, "aui.layer")
    if layer:
        pane_info.Layer(int(layer))

    pane_info.CloseButton(False)
    buttons = get_attrib(elem, "aui.buttons")
    if buttons:
        for button in buttons.split("|"):
            if button == "maximize":
                pane_info.MaximizeButton()
            elif button == "minimize":
                pane_info.MinimizeButton()
            elif button == "close":
                pane_info.CloseButton()
            elif button == "pin":
                pane_info.PinButton()
            else:
                raise InvalidAttribValueError(elem, "aui.buttons", buttons)
        
    pane_info.BestSize(get_wnd_size_optional(elem))
    
    pane_info.Resizable(get_attrib_bool(elem, "aui.resizable", False if is_toolbar else True))
    
    if not get_attrib_bool(elem, "aui.gripper", True):
        if is_toolbar:
            pane_info.Gripper(False)
        else:
            pane_info.CaptionVisible(False)
    
    if not get_attrib_bool(elem, "aui.floatable", True):
        pane_info.Floatable(False)
    
    return pane_info


class _FrameElemProcs:
    """
    Class whose attributes are functions that process elements which are children of frames.
    """
    
    def __init__(self, frame_elem):
        self._id = require_attrib(frame_elem, "id")
        
        frame_size = get_wnd_size(frame_elem)
        title = require_attrib(frame_elem, "title")
        
        self._frame = wx.Frame(None, title = title, size = frame_size)

        self._aui = wx.aui.AuiManager(self._frame, flags = wx.aui.AUI_MGR_DEFAULT + wx.aui.AUI_MGR_LIVE_RESIZE)
        
        self._frame.Bind(wx.EVT_CLOSE, _FrameCloser(self._frame, self._aui))
        
        #Contains panels and toolbars.
        self._containers = []
        
        #Maps from ID to the actual window.
        self._id_wnd_map = {}

        
    def panel(self, elem):

        panel_size = get_wnd_size_optional(elem)
        id = get_attrib(elem, "id")
        
        panel = wx.Panel(self._frame)
        self._containers.append(panel)
        
        #TODO: Get and apply sizer information.
        
        #Get and apply AUI information.
        pane_info = _get_aui_pane_info(elem)
        self._aui.AddPane(panel, pane_info)

        if id:
            if id in self._id_wnd_map:
                raise MultipleUseOfIdError(id, elem, "frame window")
            self._id_wnd_map[id] = panel
        
        #TODO: Process children.
    

    def toolbar(self, elem):
        """The difference between toolbars and panels is detected
        through `elem.tag`, not which function was called."""
        return self.panel(elem)


class _RootElemProcs:
    """
    Class whose attributes are functions that process elements which are
    children of the root.
    """

    def __init__(self):
        self._frames = {}
        pass
    
    
    def frame(self, elem):
        _aui_default_name_ix = 0
        
        frame_procs = _FrameElemProcs(elem)
        if frame_procs._id in self._frames:
            raise MultipleUseOfIdError(frame_procs._id, elem, "main application")

        self._frames[frame_procs._id] = frame_procs
        
        process_elements(frame_procs, elem, "as the child of a frame")
        
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
