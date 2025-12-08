import sys

file_path = "src/web/api/routers.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

chunk_size = 50  # Можно менять для детализации
for start in range(0, len(lines), chunk_size):
    end = min(start + chunk_size, len(lines))
    chunk = "".join(lines[:end])
    try:
        compile(chunk, file_path, "exec")
    except SyntaxError as e:
        print(f"Ошибка в строках {start+1}-{end}: {e}")
        break
else:
    print("Синтаксических ошибок не найдено.")
