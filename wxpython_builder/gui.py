"""
Defines the object which stores the windows and mapping tables loaded from an XML file.
"""

class GuiContainer:
    def __init__(self, window, wnd_map):
        self._wnd = window
        self._wnd_map = wnd_map
        
    
    def get_wnd(self):
        return self._wnd



class Gui:
    def __init__(self, app, frame_map):
        self._app = app
        self._frame_map = frame_map


    def app(self):
        return self._app


    def get_frame(self, id):
        return self._frame_map[id]


    def get_frame_wnd(self, id):
        return self._frame_map[id].get_wnd()
