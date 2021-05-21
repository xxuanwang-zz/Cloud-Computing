## <a2>
## -tar.gz
## <assignment2>
## -git commit
## <a2>
## - rm -rf assignment2, dynamodb_handler.py, logfile, outputfile
import os
import sys

class Command:
    def __init__(self):
        pass

    def compress_File(self, path, name_prefix):
        
        logfile = name_prefix + "-logfile.txt"
        output = name_prefix + ".txt"
        tar_file = name_prefix + ".tar.gz"

        try:
            os.chdir(path)
            cmd = os.system("tar czvf " + tar_file + " " + logfile + " " + output)
        except Excepetion as e:
            print(e)
        if tar_file in os.listdir(path):
            print("file created!")
            return True
        else:
            print("failed...")
            return False

    def first_Commit(self, path):
        try:
            os.chdir(path)
            print("Current dir: ", os.getcwd())
            print("First commit: Mar 4th")
            print("Due date: Mar 8th")
            cmd = os.system('git log --pretty=format:"%h%x09%an%x09%ad%x09%s"')
        except Excepetion as e:
            print(e)

        return True

    def delete_Files(self, path, name_prefix):
        logfile = name_prefix + "-logfile.txt"
        output = name_prefix + ".txt"
        tar_file = name_prefix + ".tar.gz"
        file_list = [tar_file, logfile, output, "dynamodb_handler.py"]
        print("all files: ", file_list)

        try:
            os.chdir(path)
            cmd = os.system("rm -rf " + tar_file + " " + logfile + " " + output + " " + "dynamodb_handler.py")
        except Excepetion as e:
            print(e)
            
        if all([i not in os.listdir(path) for i in file_list]):
            print("files deleted!")
            return True
        else:
            print("failed...")
            return False

    def delete_Dir(self, path, dir):
        try:
            os.chdir(path)
            cmd = os.system("rm -rf " + dir)
        except Excepetion as e:
            print(e)
            
        if dir not in os.listdir(path):
            print("directory deleted!")
            return True
        else:
            print("failed...")
            return False

def main():
    if len(sys.argv) < 2:
        print("invalid input\n")
        exit(0)

    name_prefix = sys.argv[1]

    cmd = Command()
    path_a2 = "/mnt/c/Users/DELL/Desktop/cloud/a2"
    path_assignment2 = "/mnt/c/Users/DELL/Desktop/cloud/a2/assignment2/"
    
    while True:
        function_number = input("Enter>")
        if function_number == '':
            exit()
        elif function_number == 'git':
            cmd.first_Commit(path_assignment2)

        elif function_number == 'tar':
            cmd.compress_File(path_a2, name_prefix)

        elif function_number == 'del':
            cmd.delete_Files(path_a2, name_prefix)

        elif function_number == 'dir':
            cmd.delete_Dir(path_a2, "assignment2")

    return

if __name__ == '__main__':
    main()
