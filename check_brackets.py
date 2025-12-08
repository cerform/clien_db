file_path = "src/web/api/routers.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

stack = []
for i, c in enumerate(code):
    if c in '{[(': stack.append((c, i))
    elif c in '}])':
        if not stack:
            print(f"Лишняя закрывающая скобка {c} на позиции {i}")
            break
        last, pos = stack.pop()
        if (last, c) not in [('(', ')'), ('[', ']'), ('{', '}')]:
            print(f"Несоответствие скобок: {last} на {pos}, {c} на {i}")
            break
else:
    if stack:
        print(f"Незакрытая скобка {stack[-1][0]} на позиции {stack[-1][1]}")
    else:
        print("Все скобки закрыты корректно.")
