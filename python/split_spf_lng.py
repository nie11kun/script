import re
import os
import argparse

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pattern_lang = r'\$AN_LANGUAGE_ON_HMI==3'
    
    # 检查文件是否包含 $AN_LANGUAGE_ON_HMI==3
    if not any(re.search(pattern_lang, line) for line in lines):
        # 如果不包含，直接将原文件内容写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return

    pattern_msg = r'MSG\(".*[\u4e00-\u9fff]+.*"\)'
    new_lines = []
    
    i = 0
    while i < len(lines):
        # 检查是否需要添加 ;ifIsENGBegin
        if re.search(pattern_lang, lines[i]):
            new_lines.append(align_line(';ifIsENGBegin', lines[i]))
        
        new_lines.append(lines[i])
        match = re.search(pattern_msg, lines[i])
        
        if match:
            if i + 2 < len(lines):
                new_lines.extend([lines[i+1], lines[i+2]])
                new_lines.append(align_line(';ifIsENGEnd', lines[i+2]))
                aligned_line = align_line(lines[i], lines[i+2])
                new_lines.append(aligned_line.rstrip() + ';ifIsCHS\n')
                i += 2
            else:
                remaining_lines = len(lines) - i - 1
                new_lines.extend(lines[i+1:])
                new_lines.extend(['\n'] * (2 - remaining_lines))
                prev_line = lines[i+1] if i+1 < len(lines) else lines[i]
                new_lines.append(align_line(';ifIsENGEnd', prev_line))
                aligned_line = align_line(lines[i], prev_line)
                new_lines.append(aligned_line.rstrip() + ';ifIsCHS\n')
                break
        
        i += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def align_line(source_line, reference_line):
    leading_spaces = len(reference_line) - len(reference_line.lstrip())
    return ' ' * leading_spaces + source_line.strip() + '\n'

def process_path(input_path, output_path=None):
    if os.path.isfile(input_path):
        final_output = output_path or input_path  # 如果没有指定输出文件，则覆盖原文件
        process_file(input_path, final_output)
        print(f"处理完成: {input_path} -> {final_output}")
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for filename in files:
                if filename.lower().endswith('.spf'):  # 忽略文件扩展名大小写
                    input_file = os.path.join(root, filename)
                    if output_path:
                        # 如果指定了输出路径，则保持相同的目录结构
                        relative_path = os.path.relpath(root, input_path)
                        output_dir = os.path.join(output_path, relative_path)
                        os.makedirs(output_dir, exist_ok=True)
                        output_file = os.path.join(output_dir, filename)
                    else:
                        output_file = input_file  # 覆盖原文件
                    process_file(input_file, output_file)
                    print(f"处理完成: {input_file} -> {output_file}")
    else:
        print(f"错误: {input_path} 不是有效的文件或目录")

def main():
    parser = argparse.ArgumentParser(description="处理包含 MSG 函数的文件或目录")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="输入文件的路径")
    group.add_argument("-d", "--directory", help="输入目录的路径")
    parser.add_argument("-o", "--output", help="输出文件或目录的路径，未指定时默认修改原文件")
    args = parser.parse_args()

    if args.file:
        process_path(args.file, args.output)
    elif args.directory:
        process_path(args.directory, args.output)

if __name__ == "__main__":
    main()
