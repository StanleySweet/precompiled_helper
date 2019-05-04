import os
import glob
from pathlib import Path
import re
from include_parser import IncludeParser

input_folders = ["source/maths", "source/ps", "source/soundmanager", "source/network/scripting"]
exclusions = ["source/third_party", "source/**/test_*"]
include_dirs = ['source/', 'source/pch/engine/']
working_dir = "/Users/lancelot/Desktop/git-0ad"

precompiled = 'source/pch/engine/precompiled.h'
remove_precompiled = True
stop_at_headers = [precompiled]
prune_solo = True

def unlist(lists):
	from itertools import chain as unlist
	return list(unlist.from_iterable(lists))

def sanitize_glob(regex):
	return ".*?".join([st.replace('*', '[^/]+?') for st in	 re.split(r"\*\*/", regex)])

def exclude (file, excludes):
	return any([re.search(sanitize_glob(exclude), file) is not None for exclude in excludes])

def fetch_cpp_files(folder, excludes):
	path = folder if re.search('.(cpp|h|hpp)$',folder) is not None else folder + "/**/*.cpp"
	files = glob.glob(path, recursive=True)
	return [file for file in files if not exclude(file, excludes)]

def fetch_all_cpp_files(folders, excludes):
	files = [fetch_cpp_files(folder, excludes) for folder in folders]
	return unlist(files)

directly_includes = {}
included_directly_by = {}
includes = {}
included_by = {}

if __name__ == "__main__":
	wd = os.getcwd()
	os.chdir(working_dir)

	#find_compilation_time('<algorithm>')

	files = fetch_all_cpp_files(input_folders, exclusions)

	def pretend(parser):
		parser.pretend_being('clang')
		parser.define('MOZJS_MAJOR_VERSION 38')
		parser.define('MOZJS_MINOR_VERSION 3')
		parser.define('CONFIG_ENABLE_PCH 1')
		parser.define('USING_PCH 1')
		parser.define('SDL_VERSION_ATLEAST(a,b,c) 1')
		return parser

	if remove_precompiled:
		parser = IncludeParser(precompiled, include_dirs, directly_includes, included_directly_by, includes, included_by)
		pretend(parser).run()
		stop_at_headers = stop_at_headers + list(included_by.keys())
		print(stop_at_headers)
		directly_includes = {}
		included_directly_by = {}
		includes = {}
		included_by = {}

	def run(file):
		parser = IncludeParser(file, include_dirs, directly_includes, included_directly_by, includes, included_by)
		parser.add_stop_at(stop_at_headers)
		pretend(parser).run()
		print(f"Ran {file}")

	[run(file) for file in files]

	os.chdir(wd)

	with open('scores.csv','w') as out:
		out.write("header;n;prop;leaf\n")
		for f in included_by:
			if prune_solo and f in included_directly_by and len(included_directly_by[f]) ==1:
				continue
			out.write(f'{f};{len(included_by[f])};{len(included_by[f])/len(files)};{0 if f in directly_includes else 1}\n')

	with open('direct_includes.txt','w') as out:
		for f in directly_includes:
			out.write(f'{f} : {directly_includes[f]}\n')

	with open('direct_included_by.txt','w') as out:
		for f in included_directly_by:
			out.write(f'{f} : {included_directly_by[f]}\n')
