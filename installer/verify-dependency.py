import importlib.metadata as m
import sysconfig
assert m.version('autocad-mcp-pro') == '1.5.1'
import win32com.client
import PIL
print(sysconfig.get_path('scripts'))
