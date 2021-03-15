from DBadapter import DBHandler
from analyze import CheckPotential
import os
import codecs
from subprocess import call
import subprocess
import re
import time
from mutate import runProcess, write_to_disc
import argparse
import os.path
import errno
from func_extract_clang import source_to_ast

db_obj = DBHandler()
check_obj = CheckPotential()


def write_to_disc(filecontent, filename, vari_flag, address, flag):
    if flag == 1:
        target_path = filename
    else:
        target_path = os.path.join(address, str(vari_flag)+filename)

    if not os.path.exists(os.path.dirname(target_path)):
        try:
            os.makedirs(os.path.dirname(target_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with codecs.open(target_path, 'w') as f_method:
        for line in filecontent:
            f_method.write("%s\n" % filecontent[line])
        f_method.close()


def read_code_file(file_path):
    code_lines = {}
    ret = True
    if os.path.exists(file_path):
        with open(file_path) as fp:
            for ln, line in enumerate(fp):
                assert isinstance(line, str)
                line = line.strip()
                if '//' in line:
                    line = line[:line.index('//')]
                code_lines[ln + 1] = line
    else:
        ret = False
    return code_lines, ret


class MutatePOSTGRE:
    def __init__(self, project_name, mutantSourcesDir, targetBuggyDir, targetCleanDir):
        self.killed = 0
        self.alive = 0
        self.project_name = project_name
        self.mutantSourcesDir = mutantSourcesDir
        self.targetBuggyDir = targetBuggyDir
        self.targetCleanDir = targetCleanDir

        self.operators = {'REDAWN': False,
                          'REDAWN2': False,
                          'REDAWN3': False,
                          'REDAWN4': False,
                          'REDAWN5': False,
                          'REDAWZ': False,
                          'RMFS': False,
                          'REM2A': False,
                          'REMTOSP': False,
                          'FAA': False,
                          'OBW': False
                          }

        self.REDAWN_COUNTER_alive = 0
        self.REDAWN_COUNTER_killed = 0

        self.REDAWN2_COUNTER_alive = 0
        self.REDAWN2_COUNTER_killed = 0

        self.REDAWN3_COUNTER_alive = 0
        self.REDAWN3_COUNTER_killed = 0

        self.REDAWN4_COUNTER_alive = 0
        self.REDAWN4_COUNTER_killed = 0

        self.REDAWN5_COUNTER_alive = 0
        self.REDAWN5_COUNTER_killed = 0

        self.OBW_COUNTER_alive = 0
        self.OBW_COUNTER_killed = 0

        self.FAA_COUNTER_alive = 0
        self.FAA_COUNTER_killed = 0

        self.REDAWZ_COUNTER_alive = 0
        self.REDAWZ_COUNTER_killed = 0

        self.RMFS_COUNTER_alive = 0
        self.RMFS_COUNTER_killed = 0

        self.REM2A_COUNTER_alive = 0
        self.REM2A_COUNTER_killed = 0

        self.REMTOSP_COUNTER_killed = 0
        self.REMTOSP_COUNTER_alive = 0

    def reset_flag(self):
        self.operators = {'REDAWN': False,
                          'REDAWN2': False,
                          'REDAWN3': False,
                          'REDAWN4': False,
                          'REDAWN5': False,
                          'REDAWZ': False,
                          'RMFS': False,
                          'REM2A': False,
                          'REMTOSP': False,
                          'FAA': False,
                          'OBW': False}

    def determine_operator(self, opt):
        if 'palloc0' in opt or 'palloc' in opt:
            self.operators['REDAWN'] = True
            self.operators['REDAWZ'] = True
            self.operators['REM2A'] = True
            self.operators['FAA'] = True

        if 'free' in opt or 'pfree' in opt:
            self.operators['RMFS'] = True

        if 'memcpy' in opt:
            self.operators['OBW'] = True
            self.operators['REDAWN2'] = True
            self.operators['REDAWN3'] = True
        
        if 'strcpy' in opt:
            self.operators['REDAWN4'] = True
            self.operators['REDAWN5'] = True

        if 'sizeof' in opt:
            self.operators['REMTOSP'] = True

        filtered_operators = [k for k, v in self.operators.items() if v]
        return filtered_operators

    def REDAWN_schemata(self, components):
        for i, item in enumerate(components):
            if item == '=':
                del components[i+1:len(components)]
                pass
        components.append(' NULL;')
        return components

    def REDAWN2_schemata(self, components):
        x = components[1].split(',')
        x[0] = 'NULL'
        xp = ','.join(x)
        newCom = components[0] + '(' + xp
        return newCom

    def REDAWN3_schemata(self, components):
        x = components[1].split(',')
        x[1] = ' NULL'
        xp = ','.join(x)
        newCom = components[0] + '(' + xp
        return newCom

    def REDAWN4_schemata(self, components):
        x = components[1].split(',')
        x[0] = 'NULL'
        xp = ','.join(x)
        newCom = components[0] + '(' + xp
        return newCom

    def REDAWN5_schemata(self, components):
        x = components[1].split(',')
        x[1] = ' NULL);'
        xp = ','.join(x)
        newCom = components[0] + '(' + xp
        return newCom

    def OBW_schemata(self, components):
        x = components[1].split(',')
        x[2] = ' INT_MAX);'
        xp = ','.join(x)
        newCom = components[0] + '(' + xp
        return newCom

    def FAA_schemata(self, components):
        for i, item in enumerate(components):
            if item == '=':
                del components[i+1:len(components)]
                pass
        components.append(' 0x08040000;')
        return components

    def REDAWZ_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'palloc0' or item == 'palloc':
                components[i+1] = '(0)'
        return components

    def REMTOSP_schemata(self, components):
        for i, s in enumerate(components):
            if 'sizeof(' in s:
                subCom = re.findall(r'sizeof\((.*)\)', s)
                if '*' not in subCom[0]:
                    subCom[0] = subCom[0].replace(')', '')
                    subCom[0] = subCom[0] + ' *' + ')'
                    components[i] = '(' + subCom[0]
            elif '=' in s:
                s = s.replace('=', '= ')
                components[i] = s
        components = ''.join(components)
        return components

    def REM2A_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'palloc0' or item == 'palloc':
                components[i] = 'alloca('
        return components

    def apply_REDAWN(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            selected = components2
        if not selected:
            return None
        selected = list(selected[0])
        selected = self.REDAWN_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWN_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWN_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REDAWN2(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'(?:^|\W)(memcpy)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            return None
        selected = list(selected[0])
        selected = self.REDAWN2_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)
        
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWN2_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWN2_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REDAWN3(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'(?:^|\W)(memcpy)(?:$|\W)(.*)', item[2])
           
        print(item[2])
        if components:
            selected = components
        else:
            return None
        selected = list(selected[0])
        selected = self.REDAWN3_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        
        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWN3_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWN3_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REDAWN4(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(r'(?:^|\W)(strcpy)(?:$|\W)(.*)', item[2])
        print(item[2])
        if components:
            selected = components
        else:
            return None
        selected = list(selected[0])
        selected = self.REDAWN4_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        
        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWN4_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWN4_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REDAWN5(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'(?:^|\W)(strcpy)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            return None
        selected = list(selected[0])
        selected = self.REDAWN5_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWN5_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWN5_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_OBW(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'(?:^|\W)(memcpy)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            return None
        selected = list(selected[0])
        selected = self.OBW_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.OBW_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.OBW_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_FAA(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            selected = components2
        if not selected:
            return None
        selected = list(selected[0])
        selected = self.FAA_schemata(selected)
        temp_mutant = ''.join(selected)

        temp_data_dict[item[1]] = temp_mutant
        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                print('Mutant Killed!')
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.FAA_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.FAA_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REDAWZ(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            selected = components2
        if not selected:
            return None
        selected = list(selected[0])
        selected = self.REDAWZ_schemata(selected)
        temp_mutant = ''.join(selected)
        temp_data_dict[item[1]] = temp_mutant

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REDAWZ_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REDAWZ_COUNTER_alive += 1
            db_obj.update(item[0], 1)
            db_obj.updateMstatus(item[0], 'alive')

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REM2A(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            selected = components2
        if not selected:
            return None
        selected = list(selected[0])
        selected = self.REM2A_schemata(selected)
        temp_mutant = ''.join(selected)
        temp_data_dict[item[1]] = temp_mutant

        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REM2A_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REM2A_COUNTER_alive += 1
            db_obj.updateMstatus(item[0], 'alive')
            db_obj.update(item[0], 1)

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_REMTOSP(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc0)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(palloc)(?:$|\W)(.*)', item[2])
        if components:
            selected = components
        else:
            selected = components2
        if not selected:
            return None
        selected = list(selected[0])
        selected = self.REMTOSP_schemata(selected)
        temp_mutant = ''.join(selected)
        temp_data_dict[item[1]] = temp_mutant

        db_obj.updateMutatedLine(item[0], temp_mutant)

        flag = 1
        write_to_disc(temp_data_dict, item[6],
                      item[0], self.mutantSourcesDir, flag)

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        kill_flag = False
        for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            # print(line)
            if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                kill_flag = True
                break

        print('Mutant Killed!')
        if kill_flag:
            self.REMTOSP_COUNTER_killed += 1
            db_obj.updateMstatus(item[0], 'killed')
        else:
            self.REMTOSP_COUNTER_alive += 1
            db_obj.updateMstatus(item[0], 'alive')
            db_obj.update(item[0], 1)

            flag = 2
            write_to_disc(original_data_dict, item[4],
                          item[0], self.targetCleanDir, flag)

            write_to_disc(temp_data_dict, item[4],
                          item[0], self.targetBuggyDir, flag)

    def apply_RMFS(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict.copy()
        call("./compilation_scripts/unzip.sh")
        components = re.findall(r'(?:^|\W)(free)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'(?:^|\W)(pfree)(?:$|\W)(.*)', item[2])
        if components or components2:

            del temp_data_dict[item[1]]

            flag = 1

            write_to_disc(temp_data_dict,
                          item[6], item[0], self.mutantSourcesDir, flag)
                          
                          
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Mutation of ========> {original} =====to====> {mutated}".format(original=item[2], mutated=temp_mutant))
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

            kill_flag = False
            for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                # print(line)
                if re.findall(r'\b(FAILED)\b', str(line)) or re.findall(r'\b(failed 1 among)\b', str(line)):
                    kill_flag = True
                    print('Mutant Killed!')
                    break

            if kill_flag:
                self.RMFS_COUNTER_killed += 1
                db_obj.updateMstatus(item[0], 'killed')
            else:
                self.RMFS_COUNTER_alive += 1
                db_obj.update(item[0], 1)
                db_obj.updateMstatus(item[0], 'alive')

                flag = 2

                write_to_disc(original_data_dict,
                              item[4], item[0], self.targetCleanDir, flag)

                write_to_disc(temp_data_dict,
                              item[4], item[0], self.targetBuggyDir, flag)

    def apply_mutate(self, filtered_operators, temp_data_dict, item, operator):
        for mkind in filtered_operators:
            if mkind == 'REDAWN' and operator == 'REDAWN':
                self.apply_REDAWN(filtered_operators,
                                  temp_data_dict, item, operator)

            if mkind == 'REDAWN2' and operator == 'REDAWN2':
                self.apply_REDAWN2(filtered_operators,
                                   temp_data_dict, item, operator)

            if mkind == 'REDAWN3' and operator == 'REDAWN3':
                self.apply_REDAWN3(filtered_operators,
                                   temp_data_dict, item, operator)

            if mkind == 'REDAWN4' and operator == 'REDAWN4':
                self.apply_REDAWN4(filtered_operators,
                                   temp_data_dict, item, operator)

            if mkind == 'REDAWN5' and operator == 'REDAWN5':
                self.apply_REDAWN5(filtered_operators,
                                   temp_data_dict, item, operator)

            if mkind == 'OBW' and operator == 'OBW':
                self.apply_OBW(filtered_operators,
                               temp_data_dict, item, operator)

            if mkind == 'FAA' and operator == 'FAA':
                self.apply_FAA(filtered_operators,
                               temp_data_dict, item, operator)

            if mkind == 'REDAWZ' and operator == 'REDAWZ':
                self.apply_REDAWZ(filtered_operators,
                                  temp_data_dict, item, operator)

            if mkind == 'REM2A' and operator == 'REM2A':
                self.apply_REM2A(filtered_operators,
                                 temp_data_dict, item, operator)

            if mkind == 'RMFS' and operator == 'RMFS':
                self.apply_RMFS(filtered_operators,
                                temp_data_dict, item, operator)
            if mkind == 'REMTOSP' and operator == 'REMTOSP':
                self.apply_REMTOSP(filtered_operators,
                                   temp_data_dict, item, operator)

    def report_summary(self):
        print("#######################MUTATION ANALYSIS############")
        print("COMPILATION of {project_name} project is finished.".format(
            project_name=self.project_name))
        print("TOTAL NUMBER OF GENERATED MUTANTS: {totalM}".format(
            totalM=self.alive + self.killed))
        print("ALIVE MUTANTS: {alive}".format(alive=self.alive))
        print("KILLED MUTANS: {killed}".format(killed=self.killed))
        print("#######################STATISTICS####################")
        print("THE NUMBER OF GENERATED MUTANTS FOR EACH OPERATOR:")
        print('--------------------------------------------------')
        print("REDAWZ ALIVE: {redawza}".format(
            redawza=self.REDAWZ_COUNTER_alive))
        print("REDAWZ KILLED: {redawzk}".format(
            redawzk=self.REDAWZ_COUNTER_killed))
        print('--------------------------------------------------')
        print("REDAWN ALIVE: {redawna}".format(
            redawna=self.REDAWN_COUNTER_alive))
        print("REDAWN KILLED: {redawnk}".format(
            redawnk=self.REDAWN_COUNTER_killed))
        print('--------------------------------------------------')
        print("REDAWN2 ALIVE: {redawn2a}".format(
            redawn2a=self.REDAWN2_COUNTER_alive))
        print("REDAWN2 KILLED: {redawn2k}".format(
            redawn2k=self.REDAWN2_COUNTER_killed))
        print('--------------------------------------------------')
        print("REDAWN3 ALIVE: {redawn3a}".format(
            redawn3a=self.REDAWN3_COUNTER_alive))
        print("REDAWN3 KILLED: {redawn3k}".format(
            redawn3k=self.REDAWN3_COUNTER_killed))
        print('--------------------------------------------------')
        print("REDAWN4 ALIVE: {redawn4a}".format(
            redawn4a=self.REDAWN4_COUNTER_alive))
        print("REDAWN4 KILLED: {redawn4k}".format(
            redawn4k=self.REDAWN4_COUNTER_killed))
        print('--------------------------------------------------')
        print("REDAWN5 ALIVE: {redawn5a}".format(
            redawn5a=self.REDAWN5_COUNTER_alive))
        print("REDAWN5 KILLED: {redawn5k}".format(
            redawn5k=self.REDAWN5_COUNTER_killed))
        print('--------------------------------------------------')
        print("OBW ALIVE: {obwa}".format(obwa=self.OBW_COUNTER_alive))
        print("OBW KILLED: {obwk}".format(obwk=self.OBW_COUNTER_killed))
        print('--------------------------------------------------')
        print("FAA ALIVE: {faaa}".format(faaa=self.FAA_COUNTER_alive))
        print("FAA KILLED: {faak}".format(faak=self.FAA_COUNTER_killed))
        print('--------------------------------------------------')
        print("RMFS ALIVE: {rmfsa}".format(rmfsa=self.RMFS_COUNTER_alive))
        print("RMFS KILLED: {rmfsk}".format(rmfsk=self.RMFS_COUNTER_killed))
        print('--------------------------------------------------')
        print("REM2A: {rem2aa}".format(rem2aa=self.REM2A_COUNTER_alive))
        print("REM2A: {rem2ak}".format(rem2ak=self.REM2A_COUNTER_killed))
        print('--------------------------------------------------')
        print("REMTOSP ALIVE: {remtospa}".format(
            remtospa=self.REMTOSP_COUNTER_alive))
        print("REMTOSP KILLED: {remtospk}".format(
            remtospk=self.REMTOSP_COUNTER_killed))


def main(args):
    mpost = MutatePOSTGRE(args.project_name, args.mutantSourcesDir,
                          args.targetBuggyDir, args.targetCleanDir)
    ds_list = db_obj.filter_table()
    db_obj.delete_null()
    for item in ds_list:
        item = list(item)
        call("./compilation_scripts/unzip.sh")
        if item[2] is None:
            pass
        if ';' in list(item[2])[-1]:
            data_dict, ret = read_code_file(item[6])
            if ret:
                print('File found for mutation. Please wait until the process finishs')
                filtered_operators = mpost.determine_operator(item[5])
                mpost.apply_mutate(filtered_operators,
                                   data_dict, item, args.operator)
                mpost.reset_flag()
                mpost.report_summary()
            else:
                print('File not found for mutation.')
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mutation Analysis of Your Project')
    parser.add_argument('operator', type=str,
                        help="Please choose your mutation operator. Type all if you want apply all of them at this execution.")
    parser.add_argument('project_name', type=str, help='name of your project')
    parser.add_argument('mutantSourcesDir', type=str,
                        help='main source of project')
    parser.add_argument('targetBuggyDir', type=str,
                        help='your target source for storing buggy source files')
    parser.add_argument('targetCleanDir', type=str,
                        help='your target source for storing clean source files')
    args = parser.parse_args()

    print(
        "MUTATION ANALYSIS STARTED FOR --- {project}".format(project=args.project_name))
    start_time = time.time
    main(args)
    print("TIME ELAPSED %s SECONDS ---" % (time.time() - start_time))
