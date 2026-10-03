# Ensures the repo root is importable so `import plainsight` works under pytest.
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
