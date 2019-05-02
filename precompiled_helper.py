import os
import glob
from pathlib import Path
import re

include_dirs = []

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

class ContinuousParser:
	def __init__(self, file):
		self.parsing_includes = False
		self.file = file

	def process(self, line, ret, to_parse):
		match = re.match(r'#include (("(.+?)")|(<(.+?)>))', line)

		if re.match(r'\n', line):
			return True

		if match is None:
			return not self.parsing_includes

		if not self.parsing_includes:
			self.parsing_includes = True

		is_system = match.group(3) is None
		header = "<" + match.group(5) + ">" if is_system else match.group(3)
		if True or header != 'precompiled.h':
			header = find_header(header, self.file)
			ret.append(header)
			if header not in parsed and not is_system:
				to_parse.append(header)

		return True

class UntilCodeParser:
	def __init__(self, file):
		self.file = file

	def process(self, line, ret, to_parse):
		if re.match(r'[^#].*?\{.+[^\\]\n', line):
			return False

		match = re.match(r'#include (("(.+?)")|(<(.+?)>))', line)

		if match is None:
			return True

		is_system = match.group(3) is None
		header = "<" + match.group(5) + ">" if is_system else match.group(3)
		if True or header != 'precompiled.h':
			header = find_header(header, self.file)
			ret.append(header)
			if header not in parsed and not is_system:
				to_parse.append(header)

		return True

class EverythingParser:
	def __init__(self, file):
		self.file = file

	def process(self, line, ret, to_parse):
		match = re.match(r'#include (("(.+?)")|(<(.+?)>))', line)

		if match is None:
			return True

		is_system = match.group(3) is None
		header = "<" + match.group(5) + ">" if is_system else match.group(3)
		if True or header != 'precompiled.h':
			header = find_header(header, self.file)
			ret.append(header)
			if header not in parsed and not is_system:
				to_parse.append(header)

		return True

def parse_includes(file):
	global parsed
	global to_parse
	ret = []
	parsed[Path(file).as_posix()] = ret

	parser = EverythingParser(file)

	if not Path(file).is_file():
		return
	with open(file) as f:
		line = f.readline()
		while line:
			if not parser.process(line, ret, to_parse):
				return
			line = f.readline()

scores = {}

def score_file(cpp_file):
	met = set()
	to_meet = [cpp_file]
	while len(to_meet):
		file = to_meet.pop()
		
		met.add(file)
		
		if file != cpp_file:
			if file not in scores:
				scores[file] = 0
			scores[file] = scores[file] + 1
		
		if file in parsed:
			to_meet = to_meet + list(set(parsed[file]).difference(met))

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

include_dirs = ['source/', 'source/pch/simulation2/']
working_dir = "/Users/lancelot/Documents/github_repos/0ad"

if __name__ == "__main__":
	os.chdir(working_dir)

	find_compilation_time('<algorithm>')
	print(compilation_times)

	files = fetch_all_cpp_files(["source/simulation2/components/CCmpAIManager.cpp"],["source/third_party", "source/**/test_*"])
	[parse_includes(file) for file in files]

	while len(to_parse):
		parse_includes(to_parse.pop())

	[score_file(file) for file in files]
	[find_compilation_time(file) for file in scores.keys()]

	print("header;n")
	for f in scores:
		print(f'{f};{scores[f]}')

	print("header;compilation_time")
	for f in compilation_times:
		print(f'{f};{compilation_times[f]}')

