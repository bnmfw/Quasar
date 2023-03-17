# Import modules
import os
import sys

# Define package-level variable
PACKAGE_NAME = "Quasar"

# Define package-level function
def greet():
    print("Hello from my_package!")

# Run initialization code
print("Initializing my_package...")

# Import submodules
from . import arquivos
from . import backend
from . import circuitManager
from . import circuito
from . import components
from . import concorrencia
from . import letFinder
from . import matematica
from . import mcManager
from . import spiceManager
