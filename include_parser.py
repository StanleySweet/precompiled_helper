from pathlib import Path
from pcpp import Preprocessor
import os

to_parse = []
parsed = {}
included_by = {}


class IncludeParser(Preprocessor):
    def __init__(self,
                 file_to_parse,
                 include_dirs,
                 directly_includes,
                 included_directly_by,
                 includes,
                 included_by):
        # For internal consistency, we throw if the file to be parsed doesn't
        # exist.
        if not Path(file_to_parse).is_file():
            print("error")
        super().__init__()

        self.file_path = Path(file_to_parse).as_posix()

        self.includes = includes
        self.directly_includes = directly_includes
        self.included_directly_by = included_directly_by
        self.included_by = included_by

        self.stop_at = set()
        self.file_to_parse = file_to_parse
        [self.add_path(path) for path in include_dirs]

    def add_stop_at(self, stop_at):
        self.stop_at = self.stop_at.union(set(stop_at))
        return self

    def pretend_being(self, compiler):
        if compiler not in ['clang', 'gcc']:
            print(f"Unknown compiler {compiler}")
            return
        import subprocess
        defines = subprocess.run(
            [compiler, '-x', 'c', '/dev/null', '-dM', '-E'],
            capture_output=True)
        defines = defines.stdout.decode("utf-8").split('\n')
        for define in defines:
            if not define.startswith('#define'):
                continue
            self.define(define.replace('#define ', ''))
        return self

    # Hook into parsegen to detect valide includes
    def parsegen(self, input, source=None, abssource=None):
        if not abssource:
            return super().parsegen(input, source, abssource)

        if os.path.relpath(abssource) in self.stop_at:
            return []

        if hasattr(self, 'source'):
            self.curr_file = os.path.relpath(self.source)
        self.handle_header(os.path.relpath(abssource))
        return super().parsegen(input, source, abssource)

    def on_include_not_found(self, is_system_include, curdir, includepath):
        path = '<' + includepath + '>' if is_system_include else includepath
        if path in self.stop_at:
            return
        self.handle_header(path)

    def handle_header(self, header):
        if header == self.file_path:
            return

        if self.curr_file not in self.directly_includes:
            self.directly_includes[self.curr_file] = set()
        self.directly_includes[self.curr_file].add(header)

        if header not in self.included_directly_by:
            self.included_directly_by[header] = set()
        self.included_directly_by[header].add(self.curr_file)

        if self.file_path not in self.includes:
            self.includes[self.file_path] = set()
        self.includes[self.file_path].add(header)

        if header not in self.included_by:
            self.included_by[header] = set()
        self.included_by[header].add(self.file_path)

    def run(self):
        self.curr_file = self.file_to_parse
        self.parse(open(self.file_to_parse, 'r'))
        while self.token():
            pass
