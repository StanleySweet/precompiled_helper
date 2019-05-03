import os
import glob
from pathlib import Path
import re
from include_parser import IncludeParser

input_folders = ["source/simulation2"]
exclusions = ["source/third_party", "source/**/test_*"]
include_dirs = ['source/', 'source/pch/simulation2/']
working_dir = "/Users/lancelot/Documents/github_repos/0ad"

precompiled = 'source/pch/simulation2/precompiled.h'
remove_precompiled = True
stop_at_headers = []

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

	if remove_precompiled:
		IncludeParser(precompiled, include_dirs, directly_includes, included_directly_by, includes, included_by).run()
		stop_at_headers = included_by.keys()

		directly_includes = {}
		included_directly_by = {}
		includes = {}
		included_by = {}

	def run(file):
		IncludeParser(file, include_dirs, directly_includes, included_directly_by, includes, included_by).add_stop_at(stop_at_headers).run()

	[run(file) for file in files]

	print(directly_includes)
	print(included_directly_by)
	print(includes)
	print(included_by)

	os.chdir(wd)

	with open('scores.csv','w') as out:
		out.write("header;n\n")
		for f in included_by:
			out.write(f'{f};{len(included_by[f])}\n')
