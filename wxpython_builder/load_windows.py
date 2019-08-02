
import wx
from .load_common import *


_box_sizer_orient = {
    "horizontal" : wx.HORIZONTAL,
    "vertical" : wx.VERTICAL,
}

def create_sizer(elem):
    """Builds a WX sizer for the given window element, based on its
    attributes."""
    
    attrib = elem.attrib
    
    if "box.orient" in attrib:
        #TODO: Implement wrap-box sizer.
        sizer = wx.BoxSizer(_box_sizer_orient[attrib["box.orient"]])
        return sizer
    if "grid.columns" in attrib or "grid.rows" in attrib:
        num_columns = int(attrib.get("grid.columns", "0"))
        num_rows = int(attrib.get("grid.rows", "0"))
        
        hgap = int(attrib.get("grid.hgap", "0"))
        vgap = int(attrib.get("grid.vgap", "0"))
        
        if get_attrib_bool(elem, "grid.fixed", False):
            return wx.GridSizer(num_rows, num_columns, hgap, vgap)
            
        #TODO: Implement proportional spacing for flex grid sizer.
        
        return wx.FlexGridSizer(num_rows, num_columns, hgap, vgap)
    else:
        raise MissingSizerAttributesError(elem)


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
    proportion = 0
    flags = 0
    border = 0
    
    halign = get_attrib(elem, "layout.halign")
    if halign:
        flags += _horiz_alignment[halign]
    
    valign = get_attrib(elem, "layout.valign")
    if valign:
        flags += _vert_alignment[valign]
    
    if get_attrib_bool(elem, "layout.expand", False):
        flags += wx.EXPAND
    
    proportion_value = get_attrib(elem, "layout.proportion")
    if proportion_value:
        proportion = int(proportion_value)
    
    border_size = get_attrib(elem, "layout.border-size")
    if border_size:
        border = int(border_size)
        dirs = require_attrib(elem, "layout.border-dir")
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
    def _common_control(self, elem, func, *args, **kwdargs):
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
        
        wnd = func(self, elem, self._wnd_stack[-1], wnd_size, *args, **kwdargs)

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
        
        self._sizer_stack[-1].Add(size, size, *get_sizer_flags(elem))

    
    def checkbox(self, elem):
        def wnd(self, elem, par, wnd_size):
            text = require_attrib(elem, "label")
            
            style = 0
            
            states = get_attrib(elem, "states", "two")
            if states == "three":
                style += wx.CHK_3STATE
            elif states == "three-user":
                style += wx.CHK_3STATE + wx.CHK_ALLOW_3RD_STATE_FOR_USER
            
            
            box = wx.CheckBox(par, label = text, size = wnd_size, style = style)
            
            default = get_attrib(elem, "default", "false")
            if default == "undef":
                if states == "two":
                    raise CannotDefaultTwoStateCheckBoxUndefError()
                box.Set3StateValue(wx.CHK_UNDETERMINED)
            elif default == "true":
                box.SetValue(True)
            else:
                box.SetValue(False)
            
            bind_window_events(box, self._modules, elem, {
                "py.action" : wx.EVT_CHECKBOX
            })
            
            return box
        
        return self._common_control(elem, wnd)


    def radiobox(self, elem):
        def wnd(self, elem, par, wnd_size):
            text = require_attrib(elem, "label")
            
            style = 0
            
            orient = get_attrib(elem, "orient", "vertical")
            if orient == "horizontal":
                style += wx.RA_SPECIFY_ROWS
            elif orient == "vertical":
                style += wx.RA_SPECIFY_COLS
            else:
                raise InvalidAttribValueError(elem, "orient", orient)
            
            radios = [require_attrib(radio, "label") for radio in elem]

            box = wx.RadioBox(par,
                label = text,
                size = wnd_size,
                choices = radios,
                majorDimension = 1,
                style = style)
            
            #Default value may be an integer index or a string name.
            default = get_attrib(elem, "default", "0")
            
            if default.isdigit():
                test = int(default)
                if test >= len(radios):
                    raise InvalidAttribValueError(elem, "default", default)
                default = test
            else:
                test = box.FindString(default)
                if test == wx.NOT_FOUND:
                    raise InvalidAttribValueError(elem, "default", default)
                default = test
            
            box.SetSelection(default)
            
            bind_window_events(box, self._modules, elem, {
                "py.action" : wx.EVT_RADIOBOX
            })
                
            return box

        
        return self._common_control(elem, wnd)


    def text_ctrl(self, elem):
        def wnd(self, elem, par, wnd_size):
            style = wx.TE_NOHIDESEL
            
            if get_attrib_bool(elem, "multiline", False):
                style += wx.TE_MULTILINE
            if get_attrib_bool(elem, "readonly", False):
                style += wx.TE_READONLY
            if not get_attrib_bool(elem, "wrap", True):
                style += wx.TE_DONTWRAP
            if get_attrib_bool(elem, "rich", False):
                style += wx.TE_RICH + wx.TE_RICH2

            if get_attrib(elem, "py.entry"):
                style += wx.TE_PROCESS_ENTER

            text_ctrl = wx.TextCtrl(par,
                size = wnd_size,
                style = style,
                value = get_attrib(elem, "default", ""))

            bind_window_events(text_ctrl, self._modules, elem, {
                "py.entry" : wx.EVT_TEXT_ENTER,
                "py.change" : wx.EVT_TEXT
            })
            
            return text_ctrl
    
        return self._common_control(elem, wnd)


    def py_control(self, elem):
        create_wnd = require_attrib(elem, "py.window")
        
        print(create_wnd)
        
        create_wnd = eval("lambda elem, par_wnd, wnd_size: " + create_wnd, self._modules)
        
        def wnd(self, elem, par, wnd_size, create_wnd):
            ctrl = create_wnd(elem, par, wnd_size)
            
            return ctrl
        
        return self._common_control(elem, wnd, create_wnd)


    #Containers
    def _process_children(self, elem, par_wnd = None, par_sizer = None):
        """Does the necessary pushing and popping of the 
        window/sizer"""
        
        self._wnd_stack.append(par_wnd if par_wnd else self._wnd_stack[-1])
        self._sizer_stack.append(par_sizer if par_sizer else self._sizer_stack[-1])
        
        process_elements(self, elem, "as the child of a window")
        
        self._wnd_stack.pop()
        self._sizer_stack.pop()


    def _common_container(self, elem, func):
        """Performs the common initialization and finalization tasks
        for a container, including processing the child elements.
        The creation of the window is farmed out to the given function.
        
        This function gets the window size, adds the window to
        the sizer, adds it to the id map as appropriate, etc.
        All you need to do is provide a function that returns a window.

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
        sizer = create_sizer(elem)
        wnd.SetSizer(sizer)
        wnd.SetMinSize(wnd_size)
        
        self._process_children(elem, par_wnd = wnd, par_sizer = sizer)
        self._finalize_control(wnd, elem)


    def sizer(self, elem):
        wnd_size = get_wnd_size_optional(elem)
        
        sizer = create_sizer(elem)
        sizer.SetMinSize(wnd_size)
        
        self._sizer_stack[-1].Add(sizer, *get_sizer_flags(elem))
        
        #Parse children.
        self._process_children(elem, par_sizer = sizer)
        

    def pane(self, elem):
        def _wnd(self, elem, par, wnd_size):
            return wx.Panel(par, size = wnd_size, style = wx.TAB_TRAVERSAL + wx.NO_BORDER);
        
        return self._common_container(elem, _wnd)


    def scroll_window(self, elem):
        def _wnd(self, elem, par, wnd_size):
            wnd = wx.ScrolledWindow(par, size = wnd_size)
            
            hscroll = int(get_attrib(elem, "hscroll", "0"))
            vscroll = int(get_attrib(elem, "vscroll", "0"))
            wnd.SetScrollRate(hscroll, vscroll)
            
            return wnd
    
        return self._common_container(elem, _wnd)


    def box(self, elem):
        wnd_size = get_wnd_size_optional(elem)
        
        wnd = wx.StaticBox(self._wnd_stack[-1],
            label = require_attrib(elem, "label"),
            size = wnd_size)
        
        #We have to create this box sizer for our static box
        #But the actual sizer may be something else, so we don't
        #really want to use the box sizer. So we add a new
        #sizer to it.
        static_sizer = wx.StaticBoxSizer(wnd, wx.VERTICAL)
        static_sizer.SetMinSize(wnd_size)

        sizer = create_sizer(elem)
        static_sizer.Add(sizer, 1, wx.EXPAND, 0)
        wnd.SetSizer(sizer)
        wnd.SetMinSize(wnd_size)
        
        #Note that we add the box's sizer rather than the box itself.
        #... I have no idea why, but the world breaks if we
        #add the window instead of the sizer.
        self._sizer_stack[-1].Add(static_sizer, *get_sizer_flags(elem))

        self._process_children(elem, par_wnd = wnd, par_sizer = sizer)
        self._finalize_control(wnd, elem)
        

    def coll_pane(self, elem):
        wnd_size = get_wnd_size_optional(elem)
        
        wnd = wx.CollapsiblePane(self._wnd_stack[-1],
            label = get_attrib(elem, "label", ""),
            size = wnd_size,
            style = wx.CP_DEFAULT_STYLE + wx.CP_NO_TLW_RESIZE)

        self._sizer_stack[-1].Add(wnd, *get_sizer_flags(elem))
        sizer = create_sizer(elem)
        wnd.GetPane().SetSizer(sizer)
        wnd.SetMinSize(wnd_size)
        
        self._process_children(elem,
            par_wnd = wnd.GetPane(),
            par_sizer = sizer)
        self._finalize_control(wnd, elem)
        
        wnd.Collapse(get_attrib_bool(elem, "collapsed", False))
        
        def evt(event):
            parent = event.GetEventObject().GetParent()
            while parent:
                parent.Layout()
                parent = parent.GetParent()
        
        wnd.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, evt)

