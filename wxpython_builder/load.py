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


def _get_aui_pane_info(elem):
    """Parses the AUI info from the element's attributes."""
    pane_info = wx.aui.AuiPaneInfo()
    
    is_toolbar = False
    if elem.tag == "toolbar":
        pane_info.Toolbar()
        is_toolbar = True

    #The pane name can be specified, or taken from the id, or generated.
    aui_name = get_attrib(elem, "aui-name")
    if not aui_name:
        aui_name = get_attrib(elem, "id")
        if not aui_name:
            aui_name = _calc_aui_default_name()
            
    pane_info.Name(aui_name)
    
    title = get_attrib(elem, "title")
    if title:
        pane_info.Caption(title)
    
    #Handling anchoring direction.
    anchor = require_attrib(elem, "anchor")
    if anchor == "top":
        pane_info.Top()
    elif anchor == "bottom":
        pane_info.Bottom()
    elif anchor == "left":
        pane_info.Left()
    elif anchor == "right":
        pane_info.Right()
    elif anchor == "center":
        pane_info.Center()
    else:
        raise InvalidAttribValueError(elem, "anchor", anchor)

    row = get_attrib(elem, "row")
    if row:
        pane_info.Row(int(row))

    layer = get_attrib(elem, "layer")
    if layer:
        pane_info.Layer(int(layer))

    if get_attrib_bool(elem, "maximize-button", False):
        pane_info.MaximizeButton()
    
    pane_info.BestSize(get_wnd_size_optional(elem))
    pane_info.CloseButton(False)
    
    
    pane_info.Resizable(get_attrib_bool(elem, "resizable", False if is_toolbar else True))
    
    if not get_attrib_bool(elem, "gripper", True):
        if is_toolbar:
            pane_info.Gripper(False)
        else:
            pane_info.CaptionVisible(False)
    
    if not get_attrib_bool(elem, "floatable", True):
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

        self._aui = wx.aui.AuiManager(self._frame)
        
        self._frame.Bind(wx.EVT_CLOSE, _FrameCloser(self._frame, self._aui))
        
        #Contains panels and toolbars.
        self._containers = []
        
        #Maps from ID to the actual window.
        self._id_wnd_map = {}

        
    def panel(self, elem):

        panel_size = get_wnd_size_optional(elem)
        id = get_attrib(elem, "id")
        
        #TODO: Compute an AUI-identifier if `id` is not found.
        aui_id = id
        
        panel = wx.Panel(self._frame, size = panel_size)
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
