"""Initialize torch's native DLLs before collecting Windows UI/data tests.

On this Windows/Python 3.12 environment, initializing torch after the UI/data
native dependencies causes c10.dll WinError 1114. Importing it first works;
the early initialization is unnecessary on the Linux CI runner.
"""

import sys

if sys.platform == "win32":
    import torch  # noqa: F401
