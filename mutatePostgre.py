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

db_obj = DBHandler()
check_obj = CheckPotential()


def write_to_disc(filecontent, filename, address, flag=1):
    if flag == 1:
        target_path = filename
    else:
        target_path = os.path.join(address, filename)
    with codecs.open(target_path, 'w') as f_method:
        for line in filecontent:
            f_method.write("%s\n" % filecontent[line])
        f_method.close()


class MutatePOSTGRE:
    def __init__(self, project_name, mutantSourcesDir, targetBuggyDir, targetCleanDir):
        self.killed = 0
        self.alive = 0
        self.project_name = project_name
        self.mutantSourcesDir = mutantSourcesDir
        self.targetBuggyDir = targetBuggyDir
        self.targetCleanDir = targetCleanDir

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
        self.RESOTPE_COUNTER_alive = 0
        self.RESOTPE_COUNTER_killed = 0

    def reset_flag(self):
        self.operators = {'REC2M': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False, 'RESOTPE': False}

    def determine_operator(self, opt):
        if 'palloc0' in opt or 'palloc' in opt:
            self.operators['REDAWN'] = True
            self.operators['REDAWZ'] = True
            self.operators['REC2A'] = True
        if 'free' in opt or 'pfree' in opt:
            self.operators['RMFS'] = True
        if 'sizeof' in opt:
            self.operators['RESOTPE'] = True

        filtered_operators = [k for k, v in self.operators.items() if v]
        return filtered_operators

    def REDAWN_schemata(self, components):
        for i, item in enumerate(components):
            if item == '=':
                del components[i+1:len(components)]
                pass
        components.append(' NULL;')
        return components

    def REDAWZ_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'palloc0' or item == 'palloc':
                components[i+1] = '(0)'
        return components

    def RESOTPE_schemata(self, components):
        for i, item in enumerate(components):
            if 'sizeof' in item:
                if '*' in item[i+1]:
                    item[i+1] = item[i+1].replace('*', '')
        return components

    def REC2A_schemata(self, components):
        for i, item in enumerate(components):
            if item == 'palloc0' or item == 'palloc':
                components[i] = 'alloca('
        return components

    def apply_REDAWN(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict
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

        write_to_disc(temp_data_dict, item[3], self.targetCleanDir, flag=2)

        temp_data_dict[item[1]] = temp_mutant

        write_to_disc(temp_data_dict, item[5], self.mutantSourcesDir)
        write_to_disc(temp_data_dict, item[3], self.targetBuggyDir, flag=2)

        # print("Mutation of {original} to {mutated}".format(
        #     original=item[2], mutated=temp_mutant))

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
            db_obj.update(item[0], 1)

    def apply_REDAWZ(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict
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

        write_to_disc(temp_data_dict, item[3], self.mutantSourcesDir)
        write_to_disc(temp_data_dict, item[3], self.targetBuggyDir)
        write_to_disc(original_data_dict, item[3], self.targetCleanDir)

        # print("Mutation of {original} to {mutated}".format(
        #     original=item[1], mutated=temp_mutant))

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
            db_obj.update(item[1], 1)

    def apply_REC2A(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict
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
        selected = self.REC2A_schemata(selected)
        temp_mutant = ''.join(selected)
        temp_data_dict[item[1]] = temp_mutant

        write_to_disc(temp_data_dict, item[3], self.mutantSourcesDir)
        write_to_disc(temp_data_dict, item[3], self.targetBuggyDir)
        write_to_disc(original_data_dict, item[3], self.targetCleanDir)

        # print("Mutation of {original} to {mutated}".format(
        #     original=item[1], mutated=temp_mutant))

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
            db_obj.update(item[0], 1)

    def apply_RMFS(self, filtered_operators, original_data_dict, item, operator):
        temp_data_dict = original_data_dict
        call("./compilation_scripts/unzip.sh")
        components = re.findall(r'(?:^|\W)(free)(?:$|\W)(.*)', item[2])
        components2 = re.findall(
            r'(?:^|\W)(pfree)(?:$|\W)(.*)', item[2])
        if components or components2:
            del temp_data_dict[item[1]]

            write_to_disc(temp_data_dict,
                          item[3], self.mutantSourcesDir)
            write_to_disc(temp_data_dict, item[3], self.targetBuggyDir)

            write_to_disc(original_data_dict,
                          item[3], self.targetCleanDir)

            kill_flag = False
            for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
                print(line)
                if re.findall(r'\b(FAILED)\b', str(line)):
                    self.killed += 1
                    kill_flag = True
                    self.RMFS_COUNTER_killed += 1
                    break

            if not kill_flag:
                self.alive += 1
                self.RMFS_COUNTER_alive += 1
                db_obj.update(item[0], 1)

    def apply_mutate(self, filtered_operators, temp_data_dict, item, operator):
        for mkind in filtered_operators:
            if mkind == 'REDAWN':
                self.apply_REDAWN(filtered_operators,
                                  temp_data_dict, item, operator)

            if mkind == 'REDAWZ':
                self.apply_REDAWZ(filtered_operators,
                                  temp_data_dict, item, operator)

            if mkind == 'REC2A':
                self.apply_REC2A(filtered_operators,
                                 temp_data_dict, item, operator)

            if mkind == 'RMFS':
                self.apply_RMFS(filtered_operators,
                                temp_data_dict, item, operator)

            # if mkind == 'RESOTPE':
            #     call("./compilation_scripts/unzip.sh")
            #     components = re.findall(
            #         r'([^=]+)((?<!=)=(?!=))(?:^|\W)(.*)(sizeof)(?:$|\W)(.*)', item[1])

            #     components = list(components[0])
            #     components = self.RESOTPE_schemata(components)
            #     temp_mutant = ''.join(components)
            #     temp_data_dict[item[0]] = temp_mutant
            #     write_to_disc(temp_data_dict, item[4])

            # kill_flag = False
            # for line in runProcess('./compilation_scripts/grep-exec.sh'.split()):
            #     print(line)
            #     if re.findall(r'\b(FAILED)\b', str(line)):
            #         self.killed += 1
            #         kill_flag = True
            #         self.RESOTPE_COUNTER_killed += 1
            #         break
            # if not kill_flag:
            #     self.alive += 1
            #     self.RESOTPE_COUNTER_alive += 1

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


def main(args):
    mpost = MutatePOSTGRE(args.project_name, args.mutantSourcesDir,
                          args.targetBuggyDir, args.targetCleanDir)
    ds_list = db_obj.filter_table()
    for item in ds_list:
        item = list(item)
        call("./compilation_scripts/unzip.sh")
        if ';' in item[2]:
            data_dict, ret = check_obj.read_code_file(item[5])
            if not ret:
                filtered_operators = mpost.determine_operator(item[4])
                mpost.apply_mutate(filtered_operators,
                                   data_dict, item, operator)
                mpost.reset_flag()
                mpost.report_summary()


if __name__ == "__main__":
    # project_name = "postgre"
    # mutantSourcesDir = "/home/nimashiri/postgres-REL_13_1/src"
    # targetBuggyDir = "/home/nimashiri/vsprojects/mutation_analysis/postgres/buggy"
    # targetCleanDir = "/home/nimashiri/vsprojects/mutation_analysis/postgres/clean"

    parser = argparse.ArgumentParser(
        description='Mutation Analysis of Your Project')
    parser.add_argument('Mutation_operator', type=str,
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
