#!/usr/bin/env python3
"""
修復 main.py 的縮排問題
"""

import re

def fix_indentation():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修復常見的縮排問題
    lines = content.split('\n')
    fixed_lines = []
    indent_level = 0
    
    for i, line in enumerate(lines):
        # 跳過空行
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # 計算正確的縮排
        stripped = line.lstrip()
        if not stripped:
            fixed_lines.append(line)
            continue
            
        # 減少縮排的關鍵字
        if stripped.startswith(('except', 'else', 'elif', 'finally')):
            indent_level = max(0, indent_level - 1)
        elif stripped.startswith(('return', 'break', 'continue', 'pass')):
            pass
        elif stripped.startswith(('def ', 'class ', 'if __name__')):
            indent_level = 0
        elif stripped.startswith(('try:', 'if ', 'for ', 'while ', 'with ', 'def ')):
            pass
        elif stripped.endswith(':'):
            pass
            
        # 應用縮排
        indent = '    ' * indent_level
        fixed_line = indent + stripped
        
        # 如果這行以冒號結尾，下一行需要增加縮排
        if stripped.endswith(':'):
            indent_level += 1
            
        fixed_lines.append(fixed_line)
    
    # 寫回檔案
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ 縮排修復完成")

if __name__ == "__main__":
    fix_indentation()
