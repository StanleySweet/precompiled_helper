import os
import glob
from pathlib import Path
import re

input_folders = ["source/simulation2/"]
exclusions = ["source/third_party", "source/**/test_*"]
include_dirs = ['source/', 'source/pch/simulation2/']
working_dir = "/Users/lancelot/Desktop/git-0ad"
follow_precompiled = False

def unlist(lists):
	from itertools import chain as unlist
	return list(unlist.from_iterable(lists))

def sanitize_glob(regex):
	return ".*?".join([st.replace('*', '[^/]+?') for st in	 re.split(r"\*\*/", regex)])

def exclude (file, excludes):
	return any([re.search(sanitize_glob(exclude), file) is not None for exclude in excludes])

def fetch_cpp_files(folder, excludes):
	path = folder if re.search('.(cpp|h|hpp)',folder) else folder + "/**/*.cpp"
	files = glob.glob(path, recursive=True)
	return [file for file in files if not exclude(file, excludes)]

def fetch_all_cpp_files(folders, excludes):
	files = [fetch_cpp_files(folder, excludes) for folder in folders]
	return unlist(files)

def find_header(header, og):
	if re.search(r'/', header) is None:
		if (Path(og).parent / header).is_file():
			return (Path(og).parent / header).as_posix()
	for path in include_dirs:
		if (Path(path) / header).is_file():
			return (Path(path) / header).as_posix()
	return header

to_parse = []
parsed = {}
included_by = {}

class EverythingParser:
	def __init__(self, file):
		self.file = file

	def process(self, line, ret, to_parse):
		match = re.match(r'#include (("(.+?)")|(<(.+?)>))', line)

		if match is None:
			return True

		is_system = match.group(3) is None
		header = "<" + match.group(5) + ">" if is_system else match.group(3)

		if follow_precompiled or header != 'precompiled.h':
			header = find_header(header, self.file)
			ret.append(header)

			if header not in included_by:
				included_by[header] = set()
			included_by[header].add(self.file)
			
			if header not in parsed and not is_system:
				to_parse.append(header)

		return True

def parse_includes(file):
	global parsed
	global to_parse

	if not Path(file).is_file():
		return

	ret = []
	parsed[Path(file).as_posix()] = ret

	parser = EverythingParser(file)

	with open(file) as f:
		line = f.readline()
		while line:
			if not parser.process(line, ret, to_parse):
				return
			line = f.readline()

scores = {}
cpp_include_all = {}

def score_file(cpp_file):
	met = set()
	to_meet = set([cpp_file])
	while len(to_meet):
		file = to_meet.pop()
		
		met.add(file)
		
		if file != cpp_file:
			if file not in scores:
				scores[file] = 0
			scores[file] = scores[file] + 1
		
		if file in parsed:
			to_meet = to_meet.union(set(parsed[file]).difference(met))
	cpp_include_all[cpp_file] = list(met)

compilation_times = {}

def find_compilation_time(file):
	import subprocess
	import time

	global compilation_times

	if re.match(r'<.+?>', file):
		
		with open('___lambda.h','w') as f:
			f.write(f"#include {file}\n")
		
		start = time.perf_counter()
		res = subprocess.run(["clang++","-std=c++11", "-Wno-everything", "-DNDEBUG", "-DMINIMAL_PCH=1", "-DCONFIG_ENABLE_BOOST=0", "___lambda.h"], capture_output=True, cwd=working_dir)
		duration = time.perf_counter() - start
		if res.returncode == 0:
			compilation_times[file] = duration
		else:
			print(f'Error compiling {file}')
		return

	if not Path(file).is_file():
		compilation_times[file] = None
		return

	start = time.perf_counter()
	res = subprocess.run(["clang++","-std=c++11", "-Wno-everything", "-includesource/pch/simulation2/precompiled.h", "-DNDEBUG", "-DMINIMAL_PCH=1", "-DCONFIG_ENABLE_BOOST=0"] + ["-I" + directory for directory in include_dirs] + [file], capture_output=True, cwd=working_dir)
	duration = time.perf_counter() - start
	if res.returncode == 0:
		compilation_times[file] = duration
	else:
		print(f'Error compiling {file}')

if __name__ == "__main__":
	wd = os.getcwd()
	os.chdir(working_dir)

	#find_compilation_time('<algorithm>')

	files = fetch_all_cpp_files(input_folders, exclusions)
	[parse_includes(file) for file in files]

	while len(to_parse):
		parse_includes(to_parse.pop())

	os.chdir(wd)

	[score_file(file) for file in files]
	#[find_compilation_time(file) for file in scores.keys()]

	with open('scores.csv','w') as out:
		out.write("header;n\n")
		for f in scores:
			out.write(f'{f};{scores[f]}\n')

	with open('included_by.csv','w') as out:
		[out.write(header + " : " + str(included_by[header]) + '\n') for header in included_by]

	print("header;compilation_time")
	for f in compilation_times:
		print(f'{f};{compilation_times[f]}')

