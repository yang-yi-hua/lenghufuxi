import re

with open('quiz-style.css', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查大括号是否匹配
open_braces = content.count('{')
close_braces = content.count('}')

print(f'开括号数量: {open_braces}')
print(f'闭括号数量: {close_braces}')
print(f'是否匹配: {open_braces == close_braces}')

# 检查是否有未闭合的规则
lines = content.split('\n')
brace_stack = []
for i, line in enumerate(lines, 1):
    for char in line:
        if char == '{':
            brace_stack.append(i)
        elif char == '}':
            if brace_stack:
                brace_stack.pop()
            else:
                print(f'第 {i} 行: 多余的闭括号')

if brace_stack:
    print(f'未闭合的括号出现在以下行: {brace_stack}')
