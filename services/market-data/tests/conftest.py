import sys
from pathlib import Path

# s
# src 경로를 테스트에서 인식하도록 추가
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
