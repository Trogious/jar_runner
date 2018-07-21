#!/usr/bin/env python3
import base64
import io
import os
import zipfile


def write_code(file_name_in, file_out, spaced):
    with open(file_name_in, 'r') as file_in:
        last_line = None
        for line in file_in.readlines():
            file_out.write(spaced)
            file_out.write(line)
            last_line = line
        if last_line is not None:
            if not last_line.endswith(('\n', '\n\r')):
                file_out.write('\n')


def is_code_filename(f):
    return (f.startswith('jar_') and f.endswith('.py')) or f.startswith('jar_boot_')


def zip_website(path):
    zipped_buf = io.BytesIO()
    with zipfile.ZipFile(zipped_buf, 'w') as zip_file:
        for root, dirs, files in os.walk(path):
            for file in files:
                slash = ' ' if path.endswith('slash') else '/'
                path_to_write = os.path.join(root, file)
                in_arch_name = path_to_write.replace(path + slash, '')
                zip_file.write(path_to_write, in_arch_name)
    return base64.b64encode(zipped_buf.getvalue())


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
            # website = zip_website('./build').decode('ascii')
            for line in t_in.readlines():
                written = False
                spaces = len(line) - len(line.lstrip())
                spaced_line = ''.join([' ' for _ in range(spaces)])
                for jf in jar_functions:
                    if jf == line.strip():
                        write_code(os.path.join(start_path, jf), t_out, spaced_line)
                        written = True
                # if 'website.zip' == line.strip():
                #     t_out.write(spaced_line)
                #     t_out.write(website + '\n')
                #     written = True
                if not written:
                    t_out.write(line)


if __name__ == '__main__':
    main()
