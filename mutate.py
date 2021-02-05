from DBadapter import DBHandler
from analyze import CheckPotential
import os
import codecs
from subprocess import call
import subprocess
import re

db_obj = DBHandler()
check_obj = CheckPotential()


base_path = "/home/nimashiri/grep-3.6/src"
PotentialPath = "/home/nimashiri/grep-3.6/src"


def runProcess(exe):
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        # returns None while subprocess is running
        retcode = p.poll()
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break


class Mutate:
    def __init__(self, project_name):
        self.killed = 0
        self.alive = 0
        self.project_name = project_name
        self.operators = {'REC2M': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False, 'RESOTPE': False}

    def reset_flag(self):
        self.operators = {'REC2M': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False, 'RESOTPE': False}

    def report_summary(self):
        print("COMPILATION of {project_name} project is finished.".format(
            project_name=self.project_name))
        print("TOTAL NUMBER OF GENERATED MUTANTS: {totalM}".format(
            totalM=self.alive + self.killed))
        print("ALIVE MUTANTS: {alive}".format(alive=self.alive))
        print("KILLED MUTANS: {killed}".format(killed=self.killed))
        # print("MUTATION SCORE: {score}".format(
        #     score=(self.killed) / (self.alive + self.killed)))

    def write_to_disc(self, filecontent, filename):
        target_path = os.path.join(base_path, filename)
        with codecs.open(target_path, 'w') as f_method:
            for line in filecontent:
                f_method.write("%s\n" % filecontent[line])
            f_method.close()

    def determine_operator(self, opt):
        if 'xmalloc' in opt or 'malloc' in opt or 'kmalloc' in opt:
            self.operators['REDAWN'] = True
            self.operators['REDAWZ'] = True
            self.operators['REC2A'] = True
        if 'free' in opt or 'kfree' in opt:
            self.operators['RMFS'] = True
        if 'xcalloc' in opt or 'calloc' in opt or 'kcalloc' in opt:
            self.operators['REC2M'] = True
            self.operators['REM2A'] = True
        if 'sizeof' in opt:
            self.operators['RESOTPE'] = True

        filtered_operators = [k for k, v in self.operators.items() if v]
        return filtered_operators

    def REDAWN_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'xmalloc' or item == 'malloc':
                components.pop(i)
                components.pop(i)
        components.append(' NULL;')
        return components

    def REDAWZ_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'xmalloc' or item == 'malloc':
                components[i+1] = '()'
        return components

    def REC2A_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'xmalloc' or item == 'malloc':
                components[i] = 'alloca'
        return components

    def REC2M_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'calloc':
                components[i] = 'malloc'
            if item == 'xcalloc':
                components[i] = 'xmalloc'
            if '(' in item:
                components[i] = components[i].replace(',', '*')
        return components

    def REM2A_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'calloc':
                components[i] = 'alloca'
            if item == 'xcalloc':
                components[i] = 'alloca'
            if '(' in item:
                components[i] = components[i].replace(',', '*')
        return components

    def apply_mutate(self, filtered_operators, original_data_dict, item):
        for mkind in filtered_operators:
            temp_data_dict = original_data_dict
            if mkind == 'REDAWN':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(xmalloc)(?:$|\W)(.*)', item[1])
                components2 = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(malloc)(?:$|\W)(.*)', item[1])
                if components:
                    selected = components
                else:
                    selected = components2
                selected = list(selected[0])
                selected = self.REDAWN_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                #self.write_to_disc(temp_data_dict, item[2])

                #rc = call("./compilation_scripts/grep-exec.sh")
                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAIL)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        break
                if not kill_flag:
                    self.alive += 1

                #self.write_to_disc(original_data_dict, item[2])

            if mkind == 'REDAWZ':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(xmalloc)(?:$|\W)(.*)', item[1])
                components2 = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(malloc)(?:$|\W)(.*)', item[1])
                if components:
                    selected = components
                else:
                    selected = components2
                selected = list(selected[0])
                selected = self.REDAWZ_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                self.write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAIL)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        break
                if not kill_flag:
                    self.alive += 1
                # self.write_to_disc(original_data_dict, item[2])

            if mkind == 'REC2A':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(xmalloc)(?:$|\W)(.*)', item[1])
                components2 = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(malloc)(?:$|\W)(.*)', item[1])
                if components:
                    selected = components
                else:
                    selected = components2
                selected = list(selected[0])
                selected = self.REC2A_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                self.write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAIL)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        break
                if not kill_flag:
                    self.alive += 1
                # self.write_to_disc(original_data_dict, item[2])

            if mkind == 'RMFS':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(r'(?:^|\W)(free)(?:$|\W)(.*)', item[1])
                if components:
                    del temp_data_dict[item[0]]
                    self.write_to_disc(temp_data_dict, item[2])
                    rc = call("./compilation_scripts/grep-exec.sh")
                    if rc == 0:
                        self.alive += 1
                    else:
                        self.killed += 1
                    #self.write_to_disc(original_data_dict, item[2])
                else:
                    rc = call(
                        "./compilation_scripts/grep-exec.sh")
                    if rc == 0:
                        self.alive += 1
                    else:
                        self.killed += 1

            if mkind == 'REC2M':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(calloc)(?:$|\W)(.*)', item[1])
                components2 = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(xcalloc)(?:$|\W)(.*)', item[1])
                if components:
                    selected = components
                else:
                    selected = components2
                selected = list(selected[0])
                selected = self.REC2M_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                self.write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAIL)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        break
                if not kill_flag:
                    self.alive += 1
                # self.write_to_disc(original_data_dict, item[2])

            if mkind == 'REM2A':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(calloc)(?:$|\W)(.*)', item[1])
                components2 = re.findall(
                    r'([^=]+)((?<!=)=(?!=))(?:^|\W)(xcalloc)(?:$|\W)(.*)', item[1])
                if components:
                    selected = components
                else:
                    selected = components2
                selected = list(selected[0])
                selected = self.REM2A_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                self.write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # rint(line)
                    if re.findall(r'\b(FAIL)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        break
                if not kill_flag:
                    self.alive += 1

                # self.write_to_disc(original_data_dict, item[2])


def main():
    project_name = "grep"
    m = Mutate(project_name)
    ds_list = db_obj.filter_table()
    for item in ds_list:
        call("./compilation_scripts/unzip.sh")
        item = list(item)
        if ';' in item[1]:
            current_file = os.path.join(base_path, item[2])
            data_dict = check_obj.read_code_file(current_file)
            if 'free' not in item[3]:
                if 'xnmalloc' not in item[1]:
                    filtered_operators = m.determine_operator(item[3])
                    m.apply_mutate(filtered_operators, data_dict, item)
                m.reset_flag()
                m.report_summary()


if __name__ == "__main__":
    main()
