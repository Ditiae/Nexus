import sys

try:
    import colorama
    colorama_installed = True
    colorama.init()
except ModuleNotFoundError:
    colorama_installed = False


def _form_output(p, m):
    o = "["
    if colorama_installed:

        cols = {"*": colorama.Fore.GREEN,
                "+": colorama.Fore.YELLOW,
                "-": colorama.Fore.YELLOW,
                "!": colorama.Fore.RED,
                "?": colorama.Fore.BLUE
        }

        o += cols[p]
        o += p
        o += colorama.Style.RESET_ALL
        o += "]"
    else:
        o += f"{p}]"
    lio = ""
    if m is not None:
        for i in m:
            lio += str(i) + " "
    else:
        lio = ""
    o += (" " + lio)
    return o


def _stdout_wrapper(m):
    sys.stdout.write(m)
    sys.stdout.flush()


# Colour helper functions
def icol():
    return _form_output("*", None)


def acol():
    return _form_output("+", None)


def rcol():
    return _form_output("-", None)


def ecol():
    return _form_output("!", None)


def qcol():
    return _form_output("?", None)


# Print helper functions
def iprint(*m, end="\n"):
    o = _form_output("*", m)
    _stdout_wrapper(o + end)


def aprint(*m, end="\n"):
    o = _form_output("+", m)
    _stdout_wrapper(o + end)


def rprint(*m, end="\n"):
    o = _form_output("-", m)
    _stdout_wrapper(o + end)


def eprint(*m, end="\n"):
    o = _form_output("!", m)
    _stdout_wrapper(o + end)


def qprint(*m, end="\n"):
    o = _form_output("?", m)
    _stdout_wrapper(o + end)
