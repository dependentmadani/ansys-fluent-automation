import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def test_import_modules_without_ansys_installed():
    # These imports must not try to import Ansys at module import time
    import src.meshing as _ # noqa
    import src.solver as _ # noqa
    import src.run as _ # noqa
