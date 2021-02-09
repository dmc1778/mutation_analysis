import os
import re
import json
import codecs
import os
from pathlib import Path
import itertools
import csv
from DBadapter import DBHandler
from subprocess import call
import subprocess
import argparse

db_obj = DBHandler()


class CheckPotential:
    def __init__(self) -> None:
        self._method = ""
        self.malloc_counter = 0
        self.kmalloc_counter = 0
        self.xmalloc_counter = 0
        self.calloc_counter = 0
        self.kcalloc_counter = 0
        self.xcalloc_counter = 0

        self.free_counter = 0
        self.kfree_counter = 0
        self.null_counter = 0
        self.sizeOf_counter = 0
        self.palloc0_counter = 0

        self.REDAWN = 0
        self.REDAWZ = 0
        self.REM2A = 0
        self.RESOTPE = 0
        self.REMTOSP = 0
        self.RMFS = 0

        self.mutId = 0

    def reset_flag(self):
        self.line_reg = []

    def get(self):
        return self._method

    def set(self, _input):
        self._method = _input

    def get_equal_index(self, components):
        for i, item in enumerate(components):
            if item == 'calloc':
                components[i] = 'malloc'
            if item == ',':
                components[i] = ' *'
        return components

    def REC2M(self):
        # parser = c_parser.CParser()
        for line in self._method:
            components = re.findall(
                r'([^=]+)((?<!=)=(?!=))(?:^|\W)(calloc)(?:$|\W)(.*)', self._method[line])
            if components:
                components = list(components[0])
                components = self.get_equal_index(components)
                self._method[line] = ''.join(components)
                self.del_flag = True

    def func_UMA(self, current_file, filename):
        for line in self._method:
            if self._method[line] != '':
                # and "define" not in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]
                if "palloc0" in self._method[line]:
                    self.REDAWN += 1
                    self.REDAWZ += 1
                    self.REM2A += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], filename, "palloc", current_file)

                if 'free(' in self._method[line]:
                    self.RMFS += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], filename, "free", current_file)

                if 'pfree(' in self._method[line]:
                    self.RMFS += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], filename, "pfree", current_file)

                if 'palloc0(' in self._method[line] and 'sizeof(' in self._method[line]:
                    self.RESOTPE += 1
                    self.REMTOSP += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], filename, "sizeof", current_file)

            # if 'pfree (' in self._method[line] and 'sizeof' in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]:
            #     self.RESOTPE_COUNTER += 1
            #     db_obj.insert_data(
            #         line, self._method[line], filename, "sizeof")

            # if 'xmalloc (' in self._method[line] and "define" not in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]:
            #     self.xmalloc_counter += 1
            #     db_obj.insert_data(
            #         line, self._method[line], filename, "xmalloc")

            # if 'malloc (' in self._method[line] and "define" not in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]:
            #     self.malloc_counter += 1
            #     db_obj.insert_data(
            #         line, self._method[line], filename, "malloc")

    def apply(self, current_file, filename):
        self.func_UMA(current_file, filename)

    def buildWrite(self, methodName):
        with codecs.open(methodName, 'w') as f_method:
            for line in self._method:
                f_method.write("%s\n" % self._method[line])
            f_method.close()

    def read_code_file(self, file_path):
        code_lines = {}
        file_path = Path(file_path)
        if file_path.exists:
            ret = False
            with open(file_path) as fp:
                for ln, line in enumerate(fp):
                    assert isinstance(line, str)
                    line = line.strip()
                    if '//' in line:
                        line = line[:line.index('//')]
                    code_lines[ln + 1] = line
        else:
            ret = True
        return code_lines, ret

    def read_entire_code_file(self, file_path):
        with open(file_path, 'r') as content_file:
            content_list = content_file.r
        return content_list


def main(args):

    db_obj.build_database()

    target_path = args.target_path
    _obj = CheckPotential()

    for root, _, _files in os.walk(target_path):
        for sub_files in _files:
            current_file = os.path.join(root, sub_files)
            if current_file.endswith(".c"):
                call(['./lib/remove.sh', current_file, sub_files])
                data_dict, ret = _obj.read_code_file(current_file)
                _obj.set(data_dict)
                _obj.apply(current_file, sub_files)
                _obj.reset_flag()
                print("DYNAMIC MEMORY ALLOCATION")
                print("REDAWN:", _obj.REDAWN)
                print("REDAWZ:", _obj.REDAWZ)
                print("REM2A:", _obj.REM2A)
                print("RESOTPE:", _obj.RESOTPE)
                print("REMTOSP:", _obj.REMTOSP)
                print("RMFS", _obj.RMFS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze your project for potential mutations')
    parser.add_argument('target_path', type=str, help='your target directory')
    args = parser.parse_args()
    # args = "/home/nimashiri/postgres-REL_13_1/src/"
    main(args)
