'''py2md.py - Simple docs generator for Python code documented to Google docstring standard.'''
import argparse
import glob
from time import strftime


def extract_code(end_mark, current_str, str_array, line_num):
    '''Extract a multi-line string from a string array, up to a specified end marker.

        Args:
            end_mark (str): The end mark string to match for.
            current_str (str): The first line of the string array.
            str_array (list): An array of strings (lines).
            line_num (int): The current offset into the array.

        Returns:
            Extended string up to line with end marker.
    '''
    if end_mark not in current_str:
        reached_end = False
        line_num += 1
        while reached_end is False:
            next_line = str_array[line_num]
            if end_mark in next_line:
                reached_end = True
            else:
                line_num += 1
            current_str += next_line
    clean_str = current_str.split(end_mark)[0]
    return {'current_str': clean_str, 'line_num': line_num}


def process_file(pyfile_name):
    '''Process a Python source file with Google style docstring comments.

    Reads file header comment, function definitions, function docstrings.
    Returns dictionary encapsulation for subsequent writing.

    Args:
        pyfile_name (str): file name to read.

    Returns:
        Dictionary object containing summary comment, with a list of entries for each function.
    '''
    print('Processing file: ' + pyfile_name)

    # load the source file
    with open(pyfile_name) as fpyfile:
        pyfile_str = fpyfile.readlines()

    # meta-doc for a source file
    file_dict = {'source_file': pyfile_name.replace('\\', '/')}

    # get file summary line at the top of the file
    if pyfile_str[0].startswith("'''"):
        file_dict['summary_comment'] = pyfile_str[0][:-1].strip("'")
    else:
        file_dict['summary_comment'] = pyfile_name

    file_dict['functions'] = []
    # find every function definition
    for line in pyfile_str:
        # process definition
        if line.startswith('def '):
            line_num = pyfile_str.index(line)
            fn_def = line[4:]
            fn_name = fn_def.split('(')[0]
            function_info = {'name': fn_name}
            extract = extract_code(':', fn_def, pyfile_str, line_num)
            function_info['definition'] = extract['current_str']
            # process docstring
            line_num = extract['line_num'] + 1
            doc_line = pyfile_str[line_num]
            if doc_line.startswith("    '''"):
                comment_str = doc_line[7:]
                extract = extract_code(
                    "'''", comment_str, pyfile_str, line_num)
                function_info['comments'] = extract['current_str']
            file_dict['functions'].append(function_info)
    return file_dict


def process_output(meta_file, outfile_name, code_links):
    '''Create a markdown format documentation file.

    Args:
        meta_file (dict): Dictionary with documentation metadata.
        outfile_name (str): Markdown file to write to.
    '''

    # Markdown title line
    doc_str = '# ' + meta_file['header'] + '\n'
    doc_str += 'Generated by [py2md](https://github.com/gbowerman/py2md) on '
    doc_str += strftime("%Y-%m-%d %H:%M:%S ") + '\n\n'

    # Create a table of contents if more than one module (i.e. more than one
    # source file)
    if len(meta_file['modules']) > 1:
        doc_str += "## Contents\n"
        chapter_num = 1
        for meta_doc in meta_file['modules']:
            chapter_name = meta_doc['summary_comment']
            chapter_link = chapter_name.lstrip().replace('.', '').replace(' ', '-').lower()
            doc_str += str(chapter_num) + \
                '. [' + chapter_name + '](#' + chapter_link + ')\n'
            chapter_num += 1


    # Document each meta-file
    for meta_doc in meta_file['modules']:
        doc_str += '## ' + meta_doc['summary_comment'] + '\n'
        doc_str += '[source file](' + meta_doc['source_file'] + ')' + '\n'
        for function_info in meta_doc['functions']:
            doc_str += '### ' + function_info['name'] + '\n'
            doc_str += function_info['definition'] + '\n\n'
            if 'comments' in function_info:
                doc_str += '```\n' + function_info['comments'] + '\n```\n\n'

    # write the markdown to file
    print('Writing file: ' + outfile_name)
    out_file = open(outfile_name, 'w')
    out_file.write(doc_str)
    out_file.close()


def main():
    '''Main routine.'''
    # validate command line arguments
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('--sourcedir', '-s', required=True, action='store',
                            help='Source folder containing python files.')
    arg_parser.add_argument('--docfile', '-o', required=True, action='store',
                            help='Name of markdown file to write output to.')
    arg_parser.add_argument('--projectname', '-n', required=False, action='store',
                            help='Project name (optional, otherwise sourcedir will be used).')
    arg_parser.add_argument('--codelinks', '-c', required=False, action='store_true',
                            help='Include links to source files (optional).')

    args = arg_parser.parse_args()

    source_dir = args.sourcedir
    doc_file = args.docfile
    code_links = args.codelinks
    proj_name = args.projectname
    if proj_name is None:
        proj_name = source_dir

    # main document dictionary
    meta_doc = {'header': proj_name + ' Technical Reference Guide'}
    meta_doc['modules'] = []

    # process each file
    for source_file in glob.glob(source_dir + '/*.py'):
        if '__' in source_file:
            print('Skipping: ' + source_file)
            continue
        file_meta_doc = process_file(source_file)
        meta_doc['modules'].append(file_meta_doc)

    # create output file
    process_output(meta_doc, doc_file, code_links)


if __name__ == "__main__":
    main()