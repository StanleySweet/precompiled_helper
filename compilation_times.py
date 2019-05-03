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