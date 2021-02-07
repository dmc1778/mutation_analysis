import os
from pickle import TRUE
import re
import json
import codecs
import nltk
from nltk.tokenize import word_tokenize, WhitespaceTokenizer
import os
from pathlib import Path
import itertools
import csv
from sklearn import metrics
from pycparser import c_parser, c_ast
from DBadapter import DBHandler
from subprocess import call
import subprocess

project_name = "postgres-REL_13_1"

base_path = "/home/nimashiri/postgres-REL_13_1/src"

PotentialPath = "/home/nimashiri/postgres-REL_13_1/src"

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
                if "palloc0" in self._method[line] and "define" not in self._method[line] and ":" not in self._method[line] and "?" not in self._method[line]:
                    self.REDAWN += 1
                    self.REDAWZ += 1
                    self.REM2A += 1
                    db_obj.insert_data(
                        line, self._method[line], filename, "palloc")

                if 'free(' in self._method[line]:
                    self.RMFS += 1
                    db_obj.insert_data(
                        line, self._method[line], filename, "free")

                if 'pfree(' in self._method[line]:
                    self.RMFS += 1
                    db_obj.insert_data(
                        line, self._method[line], filename, "pfree")

                if 'palloc0(' in self._method[line] and 'sizeof(' in self._method[line]:
                    self.RESOTPE += 1
                    self.REMTOSP += 1
                    db_obj.insert_data(
                        line, self._method[line], filename, "resotpe")

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
        with open(file_path) as fp:
            for ln, line in enumerate(fp):
                assert isinstance(line, str)
                line = line.strip()
                if '//' in line:
                    line = line[:line.index('//')]
                code_lines[ln + 1] = line
        return code_lines

    def read_entire_code_file(self, file_path):
        with open(file_path, 'r') as content_file:
            content_list = content_file.r
        return content_list


def main():
    _obj = CheckPotential()
    # filelist = os.listdir(Path)
    i = 0
    for root, dirnames, _files in os.walk(base_path):
        for sub_files in _files:
            current_file = os.path.join(root, sub_files)
            if current_file.endswith(".c"):
                ret = call(['./lib/remove.sh', current_file, sub_files])
                data_dict = _obj.read_code_file(current_file)
                # with codecs.open(full_path, "r", encoding="ascii") as f:
                # data_dict = f.readlines()
                _obj.set(data_dict)
                _obj.apply(current_file, sub_files)
                # _obj.buildWrite(current_file)
                _obj.reset_flag()
                print("DYNAMIC MEMORY ALLOCATION")
                print("REDAWN:", _obj.REDAWN)
                print("REDAWZ:", _obj.REDAWZ)
                print("REM2A:", _obj.REM2A)
                print("RESOTPE:", _obj.RESOTPE)
                print("REMTOSP:", _obj.REMTOSP)
                print()


if __name__ == '__main__':
    # db_obj.delete_table()
    db_obj.create_table()
    main()
