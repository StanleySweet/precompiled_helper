import os
import glob
from pathlib import Path
import re
from include_parser import IncludeParser

input_folders = []
exclusions = []
include_dirs = []
working_dir = None
precompiled = None
remove_headers_from_precompiled = True
stop_at_headers = []

prune_solo = False


def unlist(lists):
    from itertools import chain as unlist
    return list(unlist.from_iterable(lists))


def sanitize_glob(regex):
    return ".*?".join([st.replace('*', '[^/]+?')
                       for st in re.split(r"\*\*/", regex)])


def exclude(file, excludes):
    return any([re.search(sanitize_glob(exclude), file)
                is not None for exclude in excludes])


def fetch_cpp_files(folder, excludes):
    path = folder if re.search(
        '.(cpp|h|hpp)$', folder) is not None else folder + "/**/*.cpp"
    files = glob.glob(path, recursive=True)
    return [file for file in files if not exclude(file, excludes)]


def fetch_all_cpp_files(folders, excludes):
    files = [fetch_cpp_files(folder, excludes) for folder in folders]
    return unlist(files)


directly_includes = {}
included_directly_by = {}
includes = {}
included_by = {}
wd = os.getcwd()


def pretend(parser):
    parser.pretend_being('clang')
    parser.define('MOZJS_MAJOR_VERSION 38')
    parser.define('MOZJS_MINOR_VERSION 3')
    parser.define('CONFIG_ENABLE_PCH 1')
    parser.define('USING_PCH 1')
    parser.define('HAVE_PCH 1')
    parser.define('BOOST_VERSION 106000')
    parser.define('UNICODE')
    parser.define('SDL_VERSION_ATLEAST(a,b,c) 1')
    return parser


def parse_args():
    global working_dir
    global input_folders
    global exclusions
    global include_dirs
    global precompiled
    global remove_headers_from_precompiled
    global stop_at_headers

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Load settings from a config file")
    args = parser.parse_args()

    if args.file:
        import json
        config = json.load(open(args.file, 'r'))
        working_dir = config["working_dir"]
        input_folders = config["input_folders"]
        exclusions = config["exclusions"]
        include_dirs = config["include_dirs"]
        precompiled = config["precompiled"]
        remove_headers_from_precompiled =
        config["remove_headers_from_precompiled"]
        stop_at_headers = config["stop_at_headers"]

    if precompiled:
        include_dirs.append(os.path.relpath(Path(precompiled).parent))
        stop_at_headers.append(precompiled)

    if working_dir:
        os.chdir(working_dir)

    if remove_headers_from_precompiled and precompiled:
        directly_includes = {}
        included_directly_by = {}
        includes = {}
        included_by = {}
        parser = IncludeParser(precompiled, include_dirs, directly_includes,
                               included_directly_by, includes, included_by)
        pretend(parser).run()
        stop_at_headers = stop_at_headers + list(included_by.keys())


if __name__ == "__main__":
    parse_args()

    files = fetch_all_cpp_files(input_folders, exclusions)

    def run(file):
        parser = IncludeParser(file, include_dirs, directly_includes,
                               included_directly_by, includes, included_by)
        parser.add_stop_at(stop_at_headers)
        pretend(parser).run()
        print(f"Ran {file}")

    [run(file) for file in files]

    os.chdir(wd)

    with open('scores.csv', 'w') as out:
        out.write("header;n;ndir;prop;explo;leaf\n")
        for f in included_by:
            if prune_solo and f in included_directly_by and
            len(included_directly_by[f]) == 1:
                continue
            out.write(
                f'{f};{len(included_by[f])}; \
                {len(included_directly_by[f])}; \
                {len(included_by[f])/len(files)}; \
                {(len(directly_includes[f])  \
                if f in directly_includes else 0)*len(included_by[f])}; \
                {0 if f in directly_includes else 1}\n')

    with open('direct_includes.txt', 'w') as out:
        for f in directly_includes:
            out.write(f'{f} : {directly_includes[f]}\n')

    with open('direct_included_by.txt', 'w') as out:
        for f in included_directly_by:
            out.write(f'{f} : {included_directly_by[f]}\n')
