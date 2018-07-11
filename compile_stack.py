#!/usr/bin/env python3
import os


def write_code(file_name_in, file_out, spaced):
    with open(file_name_in, 'r') as file_in:
        for line in file_in.readlines():
            file_out.write(spaced)
            file_out.write(line)


def is_code_filename(f):
    return (f.startswith('jar_') and f.endswith('.py')) or f.startswith('jar_boot_')


def main():
    jar_functions = []
    start_path = os.getenv('JAR_START_PATH', '.')
    for root, dirs, files in os.walk(start_path):
        if root == '.':
            for f in files:
                if is_code_filename(f):
                    jar_functions.append(f)
            break
    TEMPLATE_IN = 'JarRunnerStackIn.yaml'
    TEMPLATE_OUT = 'JarRunnerStackCompiled.yaml'
    with open(os.path.join(start_path, TEMPLATE_OUT), 'w') as t_out:
        with open(os.path.join(start_path, TEMPLATE_IN), 'r') as t_in:
            for line in t_in.readlines():
                written = False
                for jf in jar_functions:
                    if jf in line:
                        spaces = len(line) - len(line.lstrip())
                        spaced_line = ''.join([' ' for _ in range(spaces)])
                        write_code(os.path.join(start_path, jf), t_out, spaced_line)
                        written = True
                if not written:
                    t_out.write(line)


if __name__ == '__main__':
    main()
