#!/usr/bin/env python3
"""
修復 main.py 的縮排問題
"""

def fix_main_py():
    with open('main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修復特定的縮排問題
    fixed_lines = []
    in_try_block = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.lstrip()
        
        # 跳過空行
        if not stripped:
            fixed_lines.append(line)
            continue
            
        # 計算正確的縮排
        if stripped.startswith('try:'):
            in_try_block = True
            indent_level = 0
        elif stripped.startswith('except') or stripped.startswith('else:') or stripped.startswith('finally:'):
            if in_try_block:
                indent_level = max(0, indent_level - 1)
        elif stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('if __name__'):
            indent_level = 0
            in_try_block = False
        elif stripped.endswith(':'):
            if not stripped.startswith(('if ', 'for ', 'while ', 'with ', 'def ', 'class ', 'try:', 'except', 'else:', 'finally:')):
                indent_level += 1
        
        # 應用縮排
        indent = '    ' * indent_level
        fixed_line = indent + stripped
        
        # 特殊處理某些行
        if line_num == 295:  # 問題行
            fixed_line = '                        else:\n'
        elif line_num == 296:
            fixed_line = '                            print("⚠️ 無法解析時間格式")\n'
        elif line_num == 297:
            fixed_line = '                            continue\n'
        
        fixed_lines.append(fixed_line)
    
    # 寫回檔案
    with open('main.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ main.py 縮排修復完成")

if __name__ == "__main__":
    fix_main_py()
