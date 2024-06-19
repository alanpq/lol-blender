import ctypes


class Toolkit:
    version: str

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, path: str):
        self.cdll = ctypes.CDLL(path)
        self.cdll.version.restype = ctypes.c_char_p
        self.version = self.cdll.version().decode("utf-8")

    def destroy(self):
        del self.cdll


toolkit: list[None | Toolkit] = [None]


def get_toolkit():
    return toolkit[0]


def load_toolkit_lib(path: str):
    global toolkit
    print("Loading toolkit library...")
    try:
        if toolkit[0] is not None:
            toolkit[0].destroy()
        toolkit[0] = Toolkit(path)
        print(f"Loaded toolkit library! Version: {toolkit[0].version}")
    except Exception as e:
        print(f"Could not load toolkit library! {e}")
        toolkit[0] = None
