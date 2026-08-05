"""wxPython backend package (legacy, unsupported).

Kept lazy: importing this package must not pull in ``wx`` until a primitives
module is actually requested. This matters more here than for the other
backends - wxPython is frequently not installed at all.
"""
