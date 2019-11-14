import winreg
import ctypes
import sys

uri_item = "nxm"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def set_reg(path, name="", value=None):
    try:
        path = uri_item + "\\" + path
        winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, path)
        if value is not None:
            registry_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0,
                                           winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False


if is_admin():

    py_exe = input("Input filepath of python.exe > ").strip('"').strip("'")
    handler_file = input("Input filepath of handleuri.py > ").strip('"').strip("'")

    rs = [set_reg("", name="", value="URL:nexusdlscraper"),
          set_reg("", name="URL Protocol", value=""),
          set_reg("shell"),
          set_reg("shell\\open"),
          set_reg("shell\\open\\command", name="", value='"{}" "{}" "%1"'.format(py_exe, handler_file))
    ]

    if False not in rs:
        print("SUCCESS - <ENTER> to exit")
    else:
        print("Unsuccessful - <ENTER> to exit")
    input()
else:
    print("Relaunching as admin")
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
