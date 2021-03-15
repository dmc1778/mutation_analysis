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
import re
# from func_extract_clang import main
from func_extract_clang import source_to_ast
from subprocess import call

db_obj = DBHandler()


class CheckPotential:
    def __init__(self) -> None:
        self._method = ""
        self.REDAWN = 0
        self.REDAWZ = 0
        self.REM2A = 0
        self.RESOTPE = 0
        self.REMTOSP = 0
        self.RMFS = 0
        self.REDAWN2 = 0
        self.REDAWN3 = 0
        self.REDAWN4 = 0
        self.REDAWN5 = 0
        self.OBW = 0
        self.FAA = 0

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

    def rangeCheck(self, line):
        metaInfo = self.read_txt()
        for item in metaInfo:
            splitItems = item.split(',')
            if int(splitItems[2]) < line < int(splitItems[3]):
                x = ', '.join([splitItems[2], splitItems[3]])
                return x
            else:
                x = 'not found'
        return 'not found'

    def func_UMA(self, current_file, filename):
        for line in self._method:
            if self._method[line] != '':
                # and "define" not in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]
                if 'memcpy' in self._method[line]:
                    myrange = self.rangeCheck(line)
                    self.REDAWN2 += 1
                    self.REDAWN3 += 1
                    self.OBW += 1
                    self.mutId += 1
                    db_obj.insert_data(
                        self.mutId, line, self._method[line], '', filename, "memcpy", current_file, '', myrange)
                

                if 'strcpy' in self._method[line]:
                    myrange = self.rangeCheck(line)
                    self.REDAWN4 += 1
                    self.REDAWN5 += 1
                    self.mutId += 1
                    db_obj.insert_data(
                        self.mutId, line, self._method[line], '', filename, "strcpy", current_file, '', myrange)

                if "palloc0" in self._method[line]:
                    myrange = self.rangeCheck(line)
                    self.FAA += 1
                    self.REDAWN += 1
                    self.REDAWZ += 1
                    self.REM2A += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], '', filename, "palloc", current_file, '', myrange)

                if 'free(' in self._method[line]:
                    myrange = self.rangeCheck(line)
                    self.RMFS += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], '', filename, "free", current_file, '', myrange)

                if 'pfree(' in self._method[line]:
                    myrange = self.rangeCheck(line)
                    self.RMFS += 1
                    self.mutId += 1
                    db_obj.insert_data(self.mutId,
                                       line, self._method[line], '', filename, "pfree", current_file, '', myrange)

                if "palloc0" in self._method[line] or 'palloc' in self._method[line] and 'sizeof' in self._method[line]:
                    myrange = self.rangeCheck(line)
                    components = re.findall(
                        r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', self._method[line])
                    if components:
                        components = list(components[0])
                        for s in components:
                            if 'sizeof(' in s:
                                subComponents = re.findall(
                                    r'sizeof\((.*)\)', s)
                                if '*' not in subComponents[0]:
                                    self.REMTOSP += 1
                                    self.mutId += 1
                                    db_obj.insert_data(self.mutId,
                                                       line, self._method[line], '', filename, "sizeof", current_file, '', myrange)
                                    pass

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

    def read_txt(self):
        with open('result.txt', 'r') as fileReader:
            data = fileReader.read().splitlines()
        return data


def main(args):
    db_obj.build_database()

    # target_path = '/home/nimashiri/benchmarks/run1/postgres-REL_13_1/src/'
    target_path = args.target_path
    _obj = CheckPotential()

    for root, _, _files in os.walk(target_path):
        for sub_files in _files:
            current_file = os.path.join(root, sub_files)
            if current_file.endswith(".c"):
                call(['./lib/remove.sh', current_file, sub_files])
                source_to_ast(current_file, 'result.txt')
                data_dict, ret = _obj.read_code_file(current_file)
                _obj.set(data_dict)
                _obj.apply(current_file, sub_files)
                call("./remove-clang.sh")
                _obj.reset_flag()
                print("DYNAMIC MEMORY ALLOCATION")
                print("REDAWZ:", _obj.REDAWZ)
                print("REDAWN:", _obj.REDAWN)
                print("REDAWN2:", _obj.REDAWN2)
                print("REDAWN3:", _obj.REDAWN3)
                print("REDAWN4:", _obj.REDAWN4)
                print("REDAWN5:", _obj.REDAWN5)
                print("OBW:", _obj.OBW)
                print("FAA:", _obj.FAA)
                print("REM2A:", _obj.REM2A)
                print("RESOTPE:", _obj.RESOTPE)
                print("REMTOSP:", _obj.REMTOSP)
                print("RMFS", _obj.RMFS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze your project for potential mutations')
    parser.add_argument('target_path', type=str, help='your target directory')
    args = parser.parse_args()
    # args = "/home/nimashiri/postgres-REL_13_1/src/"
    main(args)
