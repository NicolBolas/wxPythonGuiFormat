
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


def get_sizer_flags(elem):
    """Returns the 3 sizer flags as a tuple in the order appropriate to
    wx.Sizer::Add."""
    #TODO: Implement sizer flags.
    return (0, 0, 0)
    

def add_tooltip(wnd, elem):
    """Adds the tooltip to the window, if any."""
    tip = get_attrib(elem, "tooltip")
    if tip:
        wnd.SetToolTip(tip)
    
    

class WindowElementProcs:
    def __init__(self, parent_wnd, parent_sizer, insert_wnd_func):
        """
        `insert_wnd_func` is a function that is given an ID, a window,
        and the XML element for that window.
        It inserts the window into the mapping of IDs to windows for this
        frame container window. It will raise exceptions if the ID is
        already present.
        """
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

    
    def static_text(self, elem):
        wnd_size = get_wnd_size_optional(elem)
        
        text = require_attrib(elem, "label")
        text_wnd = wx.StaticText(self._wnd_stack[-1], label = text, size = wnd_size)
        self._sizer_stack[-1].Add(text_wnd, *get_sizer_flags(elem))
        
        self._finalize_control(text_wnd, elem)



