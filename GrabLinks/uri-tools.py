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


def get_reg(name):
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, uri_item, 0,
                                       winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None


def delete_reg(path):
    try:
        path = uri_item + f"\\{path}"
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, path)

        return True
    except WindowsError:
        return False


def register_uri():
    print("Registering URI handler")
    py_exe = input("Input filepath of python.exe > ").strip('"').strip("'")
    file_location = input("Input GrabLinks folder path > ").strip('"').strip("'")

    rs = [set_reg("", name="", value="URL:nexusdlscraper"),
          set_reg("", name="URL Protocol", value=""),
          set_reg("shell"),
          set_reg("shell\\open"),
          set_reg("shell\\open\\command", name="", value='"{}" "{}" "{}" "%1"'.format(py_exe, file_location + "\\handleuri.py", file_location))
    ]

    if False not in rs:
        print("\nSUCCESS")
    else:
        print(f"\nUnsuccessful ({rs})")

def disable_uri():
    rs = [delete_reg("shell\\open\\command"),
          delete_reg("shell\\open"),
          delete_reg("shell"),
          delete_reg(""),
    ]

    if False not in rs:
        print("\nSUCCESS")
    else:
        print(f"\nUnsuccessful ({rs})")

if is_admin():

    if get_reg("") is None:
        # there is no key
        print("Would you like to register or disable the URI handler? (R/d) r")
        register_uri()
    else:
        if input("Would you like to register or disable the URI handler? (R/d) ").lower() == "d":
            disable_uri()
        else:
            register_uri()

    input("Press <ENTER> to exit")
else:
    print("Relaunching as admin")
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
