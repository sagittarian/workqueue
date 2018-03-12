from pathlib import Path

# Directory to be used to store pending tasks (one task per file)
QUEUEDIR = Path(__file__).parent.parent.parent / 'data'

# Default priority for new tasks (a higher number is a higher priority)
DEFAULT_PRIORITY = 100
