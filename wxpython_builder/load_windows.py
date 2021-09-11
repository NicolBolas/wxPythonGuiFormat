
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


class _CustomContainerTools:
    """Class holding tools for custom container child processing."""

    def __init__(self, wnd_procs):
        self._wnd_procs = wnd_procs

    
    def process_children(self, elem, wnd, sizer):
        """Process the child elements of the given XML element as though
        they were windows in this builder system. It is given an XML
        element whose child elements will be processed, a window to make
        child windows a child of, and a sizer to add child windows to."""
        return self._wnd_procs._process_children(elem,
            par_wnd = wnd, par_sizer = sizer)

    
    def create_sizer(self, elem):
        """Create a sizer from an XML element that has sizer flags.
        It raises an exception if inappropriate sizer flags are found."""
        return create_sizer(elem)


    def get_window_size(self, elem):
        """Get a wx.Size from an XML element that has size information."""
        return get_wnd_size_optional(elem)


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


    def static_line(self, elem):
        def wnd(self, elem, par, wnd_size):
            style = wx.LI_VERTICAL if get_attrib(elem, "orient", "horizontal") == "vertical" else wx.LI_HORIZONTAL
            
            return wx.StaticLine(par,
                size = wnd_size,
                style = style)

        return self._common_control(elem, wnd)


    def spin_ctrl_int(self, elem):
        def wnd(self, elem, par, wnd_size):
            style = wx.SP_ARROW_KEYS + wx.TE_PROCESS_ENTER
            
            min = int(get_attrib(elem, "min", "0"))
            max = int(get_attrib(elem, "max", "100"))
            if max <= min:
                raise SpinMinMaxError(elem, min, max)
            default = int(get_attrib(elem, "default", min))
            
            if get_attrib_bool(elem, "wrap", False):
                style += wx.SP_WRAP
            
            spin = wx.SpinCtrl(par,
                size = wnd_size,
                style = style,
                initial = default,
                min = min,
                max = max)
            
            bind_window_events(spin, self._modules, elem, {
                "py.change" : wx.EVT_SPINCTRL
                })

            return spin
        
        return self._common_control(elem, wnd)


    def spin_ctrl_float(self, elem):
        def wnd(self, elem, par, wnd_size):
            style = wx.SP_ARROW_KEYS
            
            min = float(get_attrib(elem, "min", "0"))
            max = float(get_attrib(elem, "max", "100"))
            if max <= min:
                raise SpinMinMaxError(elem, min, max)
            default = float(get_attrib(elem, "default", min))
            
            increment = float(get_attrib(elem, "increment", "1"))
            
            if get_attrib_bool(elem, "wrap", False):
                style += wx.SP_WRAP
            
            spin = wx.SpinCtrlDouble(par,
                size = wnd_size,
                style = style,
                initial = default,
                inc = increment,
                min = min,
                max = max)
                
            digits = int(get_attrib(elem, "min-digits", "0"))
            spin.SetDigits(digits)
            
            bind_window_events(spin, self._modules, elem, {
                "py.change" : wx.EVT_SPINCTRLDOUBLE
                })

            return spin
        
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


    def _common_container(self, elem,
        create_wnd):
        """Performs the common initialization and finalization tasks
        for a container, including processing the child elements.
        """
        wnd_size = get_wnd_size_optional(elem)
        
        wnd = create_wnd(self, elem, self._wnd_stack[-1], wnd_size)

        self._sizer_stack[-1].Add(wnd, *get_sizer_flags(elem))
        sizer = create_sizer(elem)
        wnd.SetSizer(sizer)
        wnd.SetMinSize(wnd_size)
        
        self._process_children(elem, par_wnd = wnd, par_sizer = sizer)
        self._finalize_control(wnd, elem)


    def _common_container2(self, elem,
        create_wnd,
        add_to_sizer = None,
        set_sizer = None,
        process_children = None,
        is_custom = False):
        """Performs the common initialization and finalization tasks
        for a container, including processing the child elements.
        
        This function fetches the window size, creates the window, 
        adds it to the parent sizer, create a sizer for the window,
        processes any XML child elements as child windows, and
        performs finalization tasks for the window.
        
        Certain steps can be customized by functions.
        
        `create_wnd` creates the wxWidgets window. It takes, in order:
        * `elem` the element
        * `par_wnd` the parent window
        * `size` the window size
        
        `add_to_sizer` returns the object to add to the parent sizer.
        If not provided, then the window is added to the parent.
        This is used for special cases like `box` needing to add
        its box-sizer to the parent rather than the window itself.
        This function takes, in order:
        * `elem`: the XML element
        * `wnd`: the window created from `create_wnd`
        
        `set_sizer` Sets the created sizer into the window. If not present
        then `wnd.SetSizer()` will be called to do so. This is useful for
        things like `wxCollapsablePane`, where the sizer applies to
        the `wxCollapsablePane.GetPane` rather than the collapsible
        pane itself.
        This function takes, in order:
        * `elem`: the XML element
        * `wnd`: the window.
        * `sizer`: the sizer to set into the window.
        
        `process_children` Allows user-defined child processing. If not
        present, then the direct child elements are assumed to be
        windows and will be processed accordingly. The parent window
        and parent sizer will be the window and sizer given here.
        This function takes, in order and with names:
        * `elem`: the XML element
        * `par_wnd`: the created window
        * `par_sizer`: the sizer created for this window, if any.
        * `tools`: an object containing processing utilities, defined
        by a _CustomContainerTools instance.
        """
        wnd_size = get_wnd_size_optional(elem)
        
        wnd = create_wnd(elem, self._wnd_stack[-1], wnd_size)

        if add_to_sizer is not None:
            obj = add_to_sizer(elem, wnd)
            self._sizer_stack[-1].Add(obj, *get_sizer_flags(elem))
        else:
            self._sizer_stack[-1].Add(wnd, *get_sizer_flags(elem))

        sizer = None
        try:
            sizer = create_sizer(elem)
            if set_sizer:
                set_sizer(elem, wnd, sizer)
            else:
                wnd.SetSizer(sizer)
        except MissingSizerAttributesError as e:
            #It's OK if an element has no sizer attributes if:
            #it is a custom control
            #it does not have a set_sizer function
            #it has a process_children function
            if not(is_custom and set_sizer is None and process_children is not None):
                raise e
            
        wnd.SetMinSize(wnd_size)
        
        if process_children is not None:
            process_children(elem,
                par_wnd = wnd,
                par_sizer = sizer,
                tools = _CustomContainerTools(self))
        else:
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
        
        #The reason why we cannot use `_common_container` is this:
        #we need to set the sizer to `wnd.GetPane()`, not `wnd`
        #itself, which is the window we would return.
        #Also, child windows need to be children of `wnd.GetPane()`,
        #not to `wnd` itself.
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


    def py_container(self, elem):
        """
        Processes a container whose window and XML processing can be
        customized.
        
        # Custom container interfaces:
        * `py.window`: Creates the window itself. Required.
        Event binding can happen here.
        * `py.set-sizer`: Sets a sizer into the window. Optional.
        Only attempted to be called if the XML element contains sizer
        attributes. If there are sizer attributes and this attribute
        is not present, then `wnd.SetSizer` will be used.
        If this returns `False`, and there are sizer attributes,
        an exception is raised.
        This is useful for things like wxCollapsiblePane, where the sizer
        should be placed in the `wxCollapsiblePane::GetPane()`
        window.        
        * `py.child-windows`: Allows custom child processing. Optional.
        When specified, this function is given the window, XML element,
        and various tools. It is expected to go through the XML child
        elements and build whatever windows, using the tools listed below.
        
        If this attribute is not specified, and the window has sizer
        attributes, then the system will assume that all
        XML element children are child windows, to be attached as
        children of this window and its sizer.
        
        So if you don't want to have your window contain any child 
        windows... well,
        you should have used `py.control`. But you can just set this
        attribute to a `"False"`-valued lambda.
        """
        py_window = require_attrib_py(elem, "py.window", self._modules,
            "elem, par_wnd, size")
        
        py_set_sizer = get_attrib_py(elem, "py.set-sizer", self._modules,
            "elem, wnd, sizer")
        
        py_child_windows = get_attrib_py(elem, "py.child-windows",
            self._modules, "elem, par_wnd, par_sizer, tools")
        
        return self._common_container2(elem,
            create_wnd = py_window,
            set_sizer = py_set_sizer,
            process_children = py_child_windows,
            is_custom = True)
        


        
