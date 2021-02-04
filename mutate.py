from DBadapter import DBHandler
from analyze import CheckPotential
import os
import codecs
from subprocess import call

db_obj = DBHandler()
check_obj = CheckPotential()

project_name = "grep"
base_path = "/home/nimashiri/grep-3.6/src"
PotentialPath = "/home/nimashiri/grep-3.6/src"


class Mutate:
    def __init__(self) -> None:
        self.operators = {'REC2M': False, 'REDAWN': False, 'REDAWN': False,
                          'REDAWZ': False, 'RMFS': False, 'REC2A': False, 'REM2A': False}

    def write_to_disc(self, line, filename):
        temp_directory = './mutation_backend'
        temp_directory = os.path.join(temp_directory, filename)
        with codecs.open(temp_directory, 'w') as f_method:
            f_method.write("%s\n" % line)
        f_method.close()

    def determine_operator(self, opt):
        if opt == 'xmalloc' or opt == 'malloc' == opt == 'kmalloc':
            self.operators['REDAWN'] = True
            self.operators['REDAWZ'] = True
            self.operators['REC2A'] = True
        if opt == 'free' or opt == 'kfree':
            self.operators['RMFS'] = True
        if opt == 'xcalloc' or opt == 'calloc' or opt == 'kcalloc':
            self.operators['REC2M'] = True
            self.operators['REM2A'] = True

        filtered_operators = [k for k, v in self.operators.items() if v]
        return filtered_operators

    def apply_mutate(self, filtered_operators, data_dict, item):
        self.write_to_disc(item[1], item[2])
        for mkind in filtered_operators:
            if mkind == 'REDAWN':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('REDAWN'), str(item[2])),  shell=True)
                # save item to file
                # apply txl on file
                # load file
                # replace file with original file
                # compile program
                # reconstruct program
                None
            if mkind == 'REDAWZ':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('REDAWZ'), str(item[2])),  shell=True)
            if mkind == 'REC2A':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('REC2A'), str(item[2])),  shell=True)
            if mkind == 'RMFS':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('RMFS'), str(item[2])),  shell=True)
            if mkind == 'REC2M':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('REC2M'), str(item[2])),  shell=True)
            if mkind == 'REM2A':
                rc = call("./mutation_backend/run.sh %s %s" %
                          (str('REM2A'), str(item[2])),  shell=True)


def main():
    m = Mutate()
    ds_list = db_obj.filter_table()
    for item in ds_list:
        if ';' in item[1]:
            current_file = os.path.join(base_path, item[2])
            data_dict = check_obj.read_code_file(current_file)
            filtered_operators = m.determine_operator(item[3])
            m.apply_mutate(filtered_operators, data_dict, item)


if __name__ == "__main__":
    main()
