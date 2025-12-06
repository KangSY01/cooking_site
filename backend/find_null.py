import pathlib

base = pathlib.Path(__file__).resolve().parent

for path in base.rglob("*.py"):
    try:
        data = path.read_bytes()
    except Exception as e:
        print("읽기 실패:", path, e)
        continue

    if b"\x00" in data:
        print("⚠️ NULL BYTE 발견:", path)
