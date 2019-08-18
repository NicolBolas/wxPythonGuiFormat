# wxPythonGuiBuilder

In wxWidgets, XRC is a decent tool for laying out application windows and dialogs. However, the format is not very easy for a human to use; its generic nature makes it useful mainly for tools to write, not humans.

The wxPython GUI Builder system is an alternative that is designed to be easy for a human to write and maintain. As it is a Python-based system, it makes it easy to provide hooks for events on specific controls, so that users can have specific functions called when those controls get updates.

Notable features include:

* Processing XInclude elements in XML files, so that you can put windows in separate files.

