"""
Defines the object which stores the windows and mapping tables loaded from an XML file.
"""

from .exceptions import *


class GuiContainer:
    """The interface encapsulating a `frame` or `dialog`.
    It stores the WX window associated with the frame/dialog."""
    
    def __init__(self, window, wnd_map):
        self._wnd = window
        self._wnd_map = wnd_map
        
    
    def get_wnd(self):
        """Retrieves the frame/dialog's window object."""
        return self._wnd


class Gui:
    """The interface encapsulating the data parsed from an `app`
    element. It stores lists of containers, indexed by their `id`
    attributes. It also stores the `wx.App` that the Gui was 
    created with."""

    def __init__(self, app, frame_map, main_wnd_id = None):
        self._app = app
        self._frame_map = frame_map
        
        if main_wnd_id:
            if not main_wnd_id in self._frame_map:
                raise MainWindowNameNotFoundError(main_wnd_id)
            self._main_wnd = self._frame_map[main_wnd_id]
        else:
            self._main_wnd = self._frame_map.get("main")


    def app(self):
        """Retrieves the `wx.App` the Gui was created with."""
        return self._app


    def get_frame(self, id):
        """Retrieves the GuiContainer for the `frame` that
        matches `id`."""
        return self._frame_map[id]

    
    def get_frame_wnd(self, id):
        """Retrieves the WX window for the frame with the matching `id`."""
        return self._frame_map[id].get_wnd()


    def has_main_wnd(self):
        """Return True if the Gui has specified a main window."""
        return self._main_wnd is not None


    def get_main_wnd(self):
        """Retrieves the main window GuiContainer, or None if none was found."""
        return self._main_wnd

