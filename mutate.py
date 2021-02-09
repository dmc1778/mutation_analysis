from DBadapter import DBHandler
from analyze import CheckPotential
import os
import codecs
from subprocess import call
import subprocess
import re
import time

db_obj = DBHandler()
check_obj = CheckPotential()


base_path = "/home/nimashiri/coreutils-8.32/src"


def runProcess(exe):
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll()
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break


def write_to_disc(filecontent, filename):
    target_path = os.path.join(base_path, filename)
    with codecs.open(target_path, 'w') as f_method:
        for line in filecontent:
            f_method.write("%s\n" % filecontent[line])
        f_method.close()


class MutateGNU:
    def __init__(self, project_name):
        self.killed = 0
        self.alive = 0
        self.project_name = project_name
        self.operators = {'REC2M': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False, 'RESOTPE': False}

        self.REC2M_COUNTER_alive = 0
        self.REC2M_COUNTER_killed = 0
        self.REDAWN_COUNTER_alive = 0
        self.REDAWN_COUNTER_killed = 0
        self.REDAWZ_COUNTER_alive = 0
        self.REDAWZ_COUNTER_killed = 0
        self.RMFS_COUNTER_alive = 0
        self.RMFS_COUNTER_killed = 0
        self.REC2A_COUNTER_alive = 0
        self.REC2A_COUNTER_killed = 0
        self.REM2A_COUNTER_alive = 0
        self.REM2A_COUNTER_killed = 0

    def reset_flag(self):
        self.operators = {'REC2M': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False, 'RESOTPE': False}

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
        print("REC2M ALIVE: {rec2ma}".format(rec2ma=self.REC2M_COUNTER_alive))
        print("REC2M KILLED: {rec2mk}".format(
            rec2mk=self.REC2M_COUNTER_killed))
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
        print("RMFS ALIVE: {rmfsa}".format(rmfsa=self.RMFS_COUNTER_alive))
        print("RMFS KILLED: {rmfsk}".format(rmfsk=self.RMFS_COUNTER_killed))
        print('--------------------------------------------------')
        print("REC2A ALIVE: {rec2aa}".format(rec2aa=self.REC2A_COUNTER_alive))
        print("REC2A KILLED: {rec2ak}".format(
            rec2ak=self.REC2A_COUNTER_killed))
        print('--------------------------------------------------')
        print("REM2A: {rem2aa}".format(rem2aa=self.REM2A_COUNTER_alive))
        print("REM2A: {rem2ak}".format(rem2ak=self.REM2A_COUNTER_killed))

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
                if not selected:
                    break
                selected = list(selected[0])
                selected = self.REDAWN_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                write_to_disc(temp_data_dict, item[2])

                # rc = call("./compilation_scripts/grep-exec.sh")
                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAILED)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        self.REDAWN_COUNTER_killed += 1
                        break
                if not kill_flag:
                    self.alive += 1
                    self.REDAWN_COUNTER_alive += 1

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
                if not selected:
                    break
                selected = list(selected[0])
                selected = self.REDAWZ_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAILED)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        self.REDAWZ_COUNTER_killed += 1
                        break
                if not kill_flag:
                    self.alive += 1
                    self.REDAWZ_COUNTER_alive += 1

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
                if not selected:
                    break
                selected = list(selected[0])
                selected = self.REC2A_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAILED)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        self.REC2A_COUNTER_killed += 1
                        break
                if not kill_flag:
                    self.alive += 1
                    self.REC2A_COUNTER_alive += 1
                # self.write_to_disc(original_data_dict, item[2])

            if mkind == 'RMFS':
                call("./compilation_scripts/unzip.sh")
                components = re.findall(r'(?:^|\W)(free)(?:$|\W)(.*)', item[1])
                if components:
                    del temp_data_dict[item[0]]
                    write_to_disc(temp_data_dict, item[2])
                    rc = call("./compilation_scripts/grep-exec.sh")
                    if rc == 0:
                        self.alive += 1
                    else:
                        self.killed += 1
                    # self.write_to_disc(original_data_dict, item[2])
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
                if not selected:
                    break
                selected = list(selected[0])
                selected = self.REC2M_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAILED)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        self.REC2M_COUNTER_killed += 1
                        break
                if not kill_flag:
                    self.alive += 1
                    self.REC2M_COUNTER_alive += 1

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
                if not selected:
                    break
                selected = list(selected[0])
                selected = self.REM2A_schemata(selected)
                temp_mutant = ''.join(selected)
                temp_data_dict[item[0]] = temp_mutant
                write_to_disc(temp_data_dict, item[2])

                kill_flag = False
                for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                    # print(line)
                    if re.findall(r'\b(FAILED)\b', str(line)):
                        self.killed += 1
                        kill_flag = True
                        self.REM2A_COUNTER_killed += 1
                        break
                if not kill_flag:
                    self.alive += 1
                    self.REM2A_COUNTER_alive += 1


def main(project_name):
    mgnu = MutateGNU(project_name)
    ds_list = db_obj.filter_table()
    for item in ds_list:
        call("./compilation_scripts/unzip.sh")
        item = list(item)
        if ';' in item[1]:
            current_file = os.path.join(base_path, item[2])
            data_dict = check_obj.read_code_file(current_file)
            filtered_operators = mgnu.determine_operator(item[3])
            mgnu.apply_mutate(filtered_operators, data_dict, item)
            mgnu.reset_flag()
            mgnu.report_summary()


if __name__ == "__main__":

    project_name = "postgre"
    print(
        "MUTATION ANALYSIS STARTED FOR --- {project}".format(project=project_name))
    start_time = time.time
    main(project_name)
    print("TIME ELAPSED %s SECONDS ---" % (time.time() - start_time))
