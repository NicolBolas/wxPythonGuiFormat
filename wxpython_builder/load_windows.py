
import wx
from .load_common import *


_box_sizer_orient = {
    "horizontal" : wx.HORIZONTAL,
    "vertical" : wx.VERTICAL,
}

def create_sizer(elem):
    """Builds a WX sizer for the given window element, based on its
    attributes."""
    
    orient = get_attrib(elem, "box.orient")
    if orient:
        #TODO: Implement wrap-box sizer.
        sizer = wx.BoxSizer(_box_sizer_orient[orient])
        return sizer
    #TODO: Implement grid sizers.


_horiz_alignment = {
    "left" : wx.ALIGN_LEFT,
    "right" : wx.ALIGN_RIGHT,
    "center" : wx.ALIGN_CENTER_HORIZONTAL,
}

_vert_alignment = {
    "top" : wx.ALIGN_TOP,
    "bottom" : wx.ALIGN_BOTTOM,
    "center" : wx.ALIGN_CENTER_VERTICAL,
}

_border_directions = {
    "all" : wx.ALL,
    "top" : wx.TOP,
    "bottom" : wx.BOTTOM,
    "left" : wx.LEFT,
    "right" : wx.RIGHT,
}


def get_sizer_flags(elem):
    """Returns the 3 sizer flags as a tuple in the order appropriate to
    wx.Sizer::Add."""
    #TODO: Implement sizer flags.
    proportion = 0
    flags = 0
    border = 0
    
    halign = get_attrib(elem, "halign")
    if halign:
        flags += _horiz_alignment[halign]
    
    valign = get_attrib(elem, "valign")
    if valign:
        flags += _vert_alignment[valign]
    
    if get_attrib_bool(elem, "expand", False):
        flags += wx.EXPAND
    
    proportion_value = get_attrib(elem, "proportion")
    if proportion_value:
        proportion = int(proportion_value)
    
    border_size = get_attrib(elem, "border.size")
    if border_size:
        border = int(border_size)
        dirs = require_attrib(elem, "border.dir")
        for dir in dirs.split("|"):
            flags += _border_directions[dir]
    
    return (proportion, flags, border)
    

def add_tooltip(wnd, elem):
    """Adds the tooltip to the window, if any."""
    tip = get_attrib(elem, "tooltip")
    if tip:
        wnd.SetToolTip(tip)


def bind_window_events(wnd, modules, elem, event_map):
    """Takes the events in the event_map and binds them to the
    given window.
    
    `elem` has some number of attributes which represent Python
    code to execute when a particular event passes.
    `event_map` maps from the attribute name to the wxPython
    event type to register. This function iterates through
    those events, and if the corresponding attribute exists,
    will compile that expression as a lambda and register
    it as the event handler.
    """
    
    #TODO: Deal with parameter differences for special event types.
    for attrib, event in event_map.items():
        action = get_attrib(elem, attrib)
        if action:
            func = eval("lambda event: " + action, modules)
            wnd.Bind(event, func)


_static_text_label_align = {
    "left" : wx.ALIGN_LEFT,
    "right" : wx.ALIGN_RIGHT,
    "center" : wx.ALIGN_CENTRE_HORIZONTAL,
}

_button_label_align = {
    "top" : wx.BU_TOP,
    "bottom" : wx.BU_BOTTOM,
    "left" : wx.BU_LEFT,
    "right" : wx.BU_RIGHT,
    "center" : 0,
}


class WindowElementProcs:
    def __init__(self, parent_wnd, parent_sizer, modules, insert_wnd_func):
        """
        `insert_wnd_func` is a function that is given an ID, a window,
        and the XML element for that window.
        It inserts the window into the mapping of IDs to windows for this
        frame container window. It will raise exceptions if the ID is
        already present.
        """
        self._modules = modules
        self._wnd_stack = [parent_wnd]
        self._sizer_stack = [parent_sizer]
        
        self._insert_wnd_func = insert_wnd_func
    
    
    def _add_to_id_map(self, wnd, elem):
        """Gets the ID element and adds it to the mapping, if available."""
        id = get_attrib(elem, "id")
        if id:
            insert_wnd_func(id, wnd, elem)


    def _finalize_control(self, wnd, elem):
        """For controls, adds tooltip and inserts into ID map."""
        add_tooltip(wnd, elem)
        self._add_to_id_map(wnd, elem)


    #Controls
    def _common_control(self, elem, func):
        """Performs the common initialization and finalization tasks
        for a control, with the creation of the window being
        farmed out to the given function.
        This function gets the window size, adds the window to the sizer,
        adds it to the id map as appropriate, etc. All you need to do is
        provide a function that returns a window.

        The function must return a window.
        
        The given function takes, in order:
            self
            the element
            the parent window
            the window size
        """
        wnd_size = get_wnd_size_optional(elem)
        
        wnd = func(self, elem, self._wnd_stack[-1], wnd_size)

        self._sizer_stack[-1].Add(wnd, *get_sizer_flags(elem))
        self._finalize_control(wnd, elem)
    

    def static_text(self, elem):
        def wnd(self, elem, par, wnd_size):
            text = require_attrib(elem, "label")
            
            style = 0
            halign = get_attrib(elem, "label-align")
            if halign:
                style += _static_text_label_align[halign]
            
            return wx.StaticText(par, label = text, size = wnd_size, style = style)
        
        return self._common_control(elem, wnd)


    def button(self, elem):
        def wnd(self, elem, par, wnd_size):
            text = require_attrib(elem, "label")
            
            style = 0
            halign = get_attrib(elem, "label-align")
            if halign:
                style += _button_label_align[halign]
            
            btn = wx.Button(par, label = text, size = wnd_size, style = style)
            
            bind_window_events(btn, self._modules, elem, {
                "py.action" : wx.EVT_BUTTON
            })
            
            return btn
        
        return self._common_control(elem, wnd)


    def spacer(self, elem):
        size = int(get_attrib(elem, "size", "0"))
        proportion = int(get_attrib(elem, "proportion", "0"))
        
        self._sizer_stack[-1].Add(size, size, proportion)


    #Containers
    def _process_children(self, elem, par_wnd = None, par_sizer = None):
        """Does the necessary pushing and popping of the 
        window/sizer"""
        
        self._wnd_stack.append(par_wnd if par_wnd else self._wnd_stack[-1])
        self._sizer_stack.append(par_sizer if par_sizer else self._sizer_stack[-1])
        
        process_elements(self, elem, "as the child of a window")
        
        self._wnd_stack.pop()
        self._sizer_stack.pop()


    def sizer(self, elem):
        wnd_size = get_wnd_size_optional(elem)
        
        sizer = create_sizer(elem)
        sizer.SetMinSize(wnd_size)
        
        self._sizer_stack[-1].Add(sizer, *get_sizer_flags(elem))
        
        #Parse children.
        self._process_children(elem, par_sizer = sizer)
        
        


