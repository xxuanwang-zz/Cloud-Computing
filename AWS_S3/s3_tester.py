import sys
import s3_handler as s3h
import time
import subprocess
import unittest
import io
import re
import os

class S3Tester:
    
    def __init__(self):
        self.s3_handler = s3h.S3Handler()

    def aws_s3_ls(self, bucket_name=''):
        print("Verifying using aws command..")
        cmd = 'aws s3 ls'
        if bucket_name:
            cmd = cmd + " " + bucket_name
        try:
            print(cmd)
            out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()[0]
            out = out.decode("utf-8")
            return out
        except Exception as e:
            print(e)
    
    def test_create_bucket(self, bucket_name, fp):
        ret = self.s3_handler.createdir(bucket_name)
        fp.write(str(ret))
        out = self.aws_s3_ls('')
        bucket_created = False
        for line in out.split("\n"):
            if bucket_name in line:
                bucket_created = True
        return bucket_created

    def test_listdir(self, bucket_name, fp):
        ret = self.s3_handler.listdir(bucket_name)
        fp.write(str(ret))
        bucket_op = self.aws_s3_ls(bucket_name)
        if bucket_name == '':
            bucket_listed = False
            for line in bucket_op.split("\n"):
                if bucket_name in line:
                    bucket_listed = True
            return bucket_listed
        if bucket_name != '':
            return bucket_op, ret

    def test_upload(self, bucket_name, source_file, fp, dest_object=''):
        ret = self.s3_handler.upload(source_file, bucket_name, dest_object)
        fp.write(str(ret))
        return ret

    # New Download
    def test_download(self, dest_object, bucket_name, fp, source_file=''):
        ret = self.s3_handler.download(dest_object, bucket_name, source_file)
        fp.write(str(ret))
        return ret

    # New
    def test_delete(self, dest_object, bucket_name, fp):
        ret = self.s3_handler.delete(dest_object, bucket_name)
        fp.write(str(ret))
        return ret

    # New
    def test_deletedir(self, bucket_name, fp):
        ret = self.s3_handler.deletedir(bucket_name)
        #fp.write(str(ret))
        print(ret)
        bucket_op = self.aws_s3_ls(bucket_name)
        return ret, bucket_op

    # New find    
    def test_find(self, file_extension, bucket_name=''):
        ret = self.s3_handler.find(file_extension, bucket_name)
        return ret

    def check_object_created(self, output, file_name):
        for line in output.split("\n"):
            if file_name in line:
                return True
        return False 

    def check_object_deleted(self, output, file_name):
        for line in output.split("\n"):
            if file_name not in line:
                return True
        return False

    def check_bucket_deleted(self, output, bucket_to_delete):
        for line in output.split("\n"):
            if bucket_to_delete not in line:
                return True
        return False 

    # New
    def check_renamed_file(self):
        renamed_file = ''
        for file_name in os.listdir():
            if ".bak." in file_name:
                renamed_file += file_name
        return renamed_file

    # New
    def check_object_in_current_dir(self, file_name):
        if file_name in os.listdir():
            return True
        else:
            return False

    def run_tests(self, test_case_number, bucket_name, fp):
        total_points = 97
        points = 0
        bucket_name_2 = "2-" + bucket_name
        timeInMillis = round(time.time() * 1000)
        non_existent_bucket_name = "not_exist_bucket" + "-" + str(timeInMillis)
        non_existent_file = "README" + str(timeInMillis)

        if test_case_number == 1:
            fp.write("--------------------------------\n")
            fp.write("Create (1/3)\n")
            fp.write("Test case 1 (1 points): Create directory - valid name\n")
            ret = self.test_create_bucket(bucket_name, fp)
            fp.write("\n**For testing**\n")
            self.test_create_bucket(bucket_name_2, fp)
            fp.write("\n**end**")
            if ret:
                fp.write("\npassed\n")
                points = points + 1
            else:
                fp.write("\nfailed\n")

        if test_case_number == 2:
            fp.write("--------------------------------\n")
            fp.write("Create (2/3)\n")
            fp.write("Test case 2 (1 points): Create a valid directory twice\n")
            ret = self.test_create_bucket(bucket_name, fp)
            fp.write("\n**Check Return**\n")

        if test_case_number == 3:
            fp.write("--------------------------------\n")
            fp.write("Create (3/3)\n")
            fp.write("Test case 3 (1 points): Create directory - invalid name\n")
            ret = self.test_create_bucket("testbucket", fp)
            fp.write("\n**Check Return**\n")

        if test_case_number == 4:
            fp.write("--------------------------------\n")
            fp.write("Listdir (1/4)\n")
            fp.write("Test case 4 (5 points): List dir - without bucket name\n")
            time.sleep(3)
            ret = self.test_listdir('', fp)
            if ret:
                fp.write("\npassed\n")
                points = points + 5
            else:
                fp.write("\nfailed\n")

        if test_case_number == 5:
            fp.write("--------------------------------\n")
            fp.write("Listdir (2/4)\n")
            fp.write("Test case 5 (3 points): List dir - bucket does not exist\n")
            _, ret = self.test_listdir(non_existent_bucket_name, fp)
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("\npassed\n")
                points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 6:
            fp.write("--------------------------------\n")
            fp.write("Listdir (3/4)\n")
            fp.write("Test case 6 (3 points): List dir - an empty bucket\n")
            _, ret = self.test_listdir(bucket_name, fp)
            fp.write("\n**Check Return**\n")
            fp.write(str(ret))
            if isinstance(ret, list):
                if ret == []:
                    fp.write("\npassed\n")
                    points = points + 3
            elif isinstance(ret, str):
                if ret == '' or [] or 'empty' or 'no files found' in ret.lower():
                    fp.write("\npassed\n")
                    points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 7:
            fp.write("--------------------------------\n")
            fp.write("Upload (1/4)\n")
            fp.write("Test case 7 (3 points): Upload file - no dest name \n")
            file_to_upload = 'README.txt'
            self.test_upload(bucket_name, file_to_upload, fp, '')
            fp.write("\n**For testing**\n")
            self.test_upload(bucket_name_2, "requirements.txt", fp, '')
            fp.write("\n**End**\n")
            ret, _ = self.test_listdir(bucket_name, fp)
            object_created = self.check_object_created(ret, file_to_upload)
            if object_created:
                fp.write("\npassed\n")
                points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 8:
            fp.write("--------------------------------\n")
            fp.write("Upload (2/4)\n")
            fp.write("Test case 8 (9 points): Upload file - dest name given \n")
            file_to_upload = 'README.txt'
            dest_object = 'README1.txt' 
            self.test_upload(bucket_name, file_to_upload, fp, dest_object)
            ret1, _ = self.test_listdir(bucket_name, fp)
            object_created = self.check_object_created(ret1, dest_object)
            if object_created:
                fp.write("\npassed\n")
                points = points + 9
            else:
                fp.write("\nfailed\n")

        if test_case_number == 9:
            fp.write("--------------------------------\n")
            fp.write("Upload (3/4)\n")
            fp.write("Test case 9 (3 points): Upload file - non existent source file \n")
            dest_object = 'README1.txt'
            ret = self.test_upload(bucket_name, non_existent_file, fp, dest_object)
            fp.write("\n**Check Return**\n")

            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 10:
            fp.write("--------------------------------\n")
            fp.write("Upload (4/4)\n")
            fp.write("Test case 10 (3 points): Upload file - non existent bucket \n")
            file_to_upload = 'README.txt'
            dest_object = 'README1.txt'
            ret = self.test_upload(non_existent_bucket_name, file_to_upload, fp, dest_object)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 11:
            fp.write("--------------------------------\n")
            fp.write("Listdir (4/4)\n")
            fp.write("Test case 11 (3 points): List dir - bucket that is NOT empty\n")
            _, ret = self.test_listdir(bucket_name, fp)
            print("The type of the output: " + str(type(ret)))
            if isinstance(ret, list):
                if ret == ['README.txt', 'README1.txt']:
                    fp.write("\npassed\n")
                    points = points + 3
            elif isinstance(ret, str):
                if re.search(r'(.*)README.txt(.*?)README1.txt.*', ret) != None:
                    fp.write("\npassed\n")
                    points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 12:
            fp.write("--------------------------------\n")
            fp.write("Download (1/5)\n")
            fp.write("Test case 12 (5 points): Download file - with source file name (no need to rename) \n")
            file_to_download = 'README.txt'
            source_object = "README_DownloadTest.txt"
            self.test_download(file_to_download, bucket_name, fp, source_object)
            object_downloaded = self.check_object_in_current_dir(source_object)
            if object_downloaded:
                fp.write("\npassed\n")
                points = points + 5
            else:
                fp.write("\nfailed\n")

        if test_case_number == 13:            
            fp.write("--------------------------------\n")
            fp.write("Download (2/5)\n")
            fp.write("Test case 13 (8 points): Download file - need to rename \n")
            file_to_download = 'README.txt'
            source_object = "README.txt"
            self.test_download(file_to_download, bucket_name, fp, source_object)
            object_renamed_downloaded = self.check_renamed_file() # The renamed file name should be printed here
            if object_renamed_downloaded:
                fp.write("\npassed\n")
                points = points + 8
            else:
                fp.write("\nfailed\n")

        if test_case_number == 14:
            fp.write("--------------------------------\n")
            fp.write("Download (3/5)\n")
            fp.write("Test case 14 (3 points): Download file - non existent dest file \n")
            file_to_download = 'README.txt'
            source_object = "README2.txt"
            ret = self.test_download(non_existent_file, bucket_name, fp, source_object)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 15: 
            fp.write("--------------------------------\n")
            fp.write("Download (4/5)\n")
            fp.write("Test case 15 (3 points): Download file - non existent directory \n")
            file_to_download = 'README.txt'
            source_object = "README3.txt"
            ret = self.test_download(file_to_download, non_existent_bucket_name, fp, source_object)
            fp.write("\n**Check Return**\n")
            if ret == '' or None or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 16:
            fp.write("--------------------------------\n")
            fp.write("Download (5/5)\n")
            fp.write("Test case 16 (3 points): Download file - no source file name \n")
            file_to_download = 'README1.txt' # README1.txt already exists in s3 bucket 
            self.test_download(file_to_download, bucket_name, fp, '')
            object_downloaded = self.check_object_in_current_dir(file_to_download)
            if object_downloaded:        
                fp.write("\npassed\n")
                points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 17:
            fp.write("--------------------------------\n")
            fp.write("Find (1/4)\n")
            fp.write("Test case 17 (8 points): Find files with a given extension in a bucket\n")
            ret = self.test_find('txt', bucket_name)
            print("Find: ", ret)
            if isinstance(ret, list):
                if ret == ['README.txt', 'README1.txt']:
                    fp.write("\npassed\n")
                    points = points + 8
            elif isinstance(ret, str):
                if re.search(r'(.*)README.txt(.*?)README1.txt.*', ret) != None:
                    fp.write("\npassed\n")
                    points = points + 8
            else:
                fp.write("\nfailed\n")

        if test_case_number == 18:
            fp.write("--------------------------------\n")
            fp.write("Find (2/4)\n")
            fp.write("Test case 18 (8 points): Find files with a given extension from all buckets\n")
            ret = self.test_find('txt')
            print('Find: ', ret)
            if isinstance(ret, list):
                if ret == ['requirements.txt', 'README.txt', 'README1.txt']:
                    fp.write("\npassed\n")
                    points = points + 8
            elif isinstance(ret, str):
                if re.search(r'(.*)requirements.txt(.*?)README.txt(.*?)README1.txt.*', ret) != None:
                    fp.write("\npassed\n")
                    points = points + 8
            else:
                fp.write("\nfailed\n")

        if test_case_number == 19:
            fp.write("--------------------------------\n")
            fp.write("Find (3/4)\n")
            fp.write("Test case 19 (3 points): No file exist with the query extension from all buckets\n")
            file_extension = 'png'
            ret = self.test_find(file_extension)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'no files found' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 20:
            fp.write("--------------------------------\n")
            fp.write("Find (4/4)\n")
            fp.write("Test case 20 (3 points): Find files in a nonexistent bucket\n")
            file_extension = 'txt'
            ret = self.test_find(file_extension, non_existent_bucket_name)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 21:
            fp.write("--------------------------------\n")
            fp.write("Delete (1/3)\n")
            fp.write("Test case 21 (3 points): Delete an object that does not exist\n")
            ret = self.test_delete(non_existent_file, bucket_name, fp)
            time.sleep(6)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 22:
            fp.write("--------------------------------\n")
            fp.write("Delete (2/3)\n")
            fp.write("Test case 22 (3 points): Delete an object in a bucket that does not exist\n")
            file_to_delete = 'README1.txt'
            ret = self.test_delete(file_to_delete, non_existent_bucket_name, fp)
            time.sleep(6)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")            

        if test_case_number == 23:
            fp.write("--------------------------------\n")
            fp.write("Deletedir (1/3)\n")
            fp.write("Test case 23 (3 points): Delete a bucket that is NOT empty\n")
            ret, _ = self.test_deletedir(bucket_name, fp)
            time.sleep(6)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'not empty' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 24:
            fp.write("--------------------------------\n")
            fp.write("Deletedir (2/3)\n")
            fp.write("Test case 24 (3 points): Delete a bucket that does not exist\n")
            ret, _ = self.test_deletedir(non_existent_bucket_name, fp)
            time.sleep(6)
            fp.write("\n**Check Return**\n")
            if ret == '' or 'doesn\'t exists' or 'does not exist' in ret.lower():
                fp.write("passed\n")
                points = points + 3
            else:
                fp.write("failed\n")

        if test_case_number == 25:
            fp.write("--------------------------------\n")
            fp.write("Delete (3/3)\n")
            fp.write("Test case 25 (3 points): Delete an existed object\n")
            file_to_delete = 'README.txt'
            ret, _ = self.test_listdir(bucket_name, fp)
            fp.write('\n')
            self.test_delete(file_to_delete, bucket_name, fp)
            ## For testing
            fp.write("\n**For testing**\n")
            self.test_delete('README1.txt', bucket_name, fp)
            self.test_delete('requirements.txt', bucket_name_2, fp)
            fp.write("\n**End**\n")
            time.sleep(6)
            object_deleted = self.check_object_deleted(ret, file_to_delete)
            if object_deleted:            
                fp.write("\npassed\n")
                points = points + 3
            else:
                fp.write("\nfailed\n")

        if test_case_number == 26:
            fp.write("--------------------------------\n")
            fp.write("Deletedir (3/3)\n")
            fp.write("Test case 26 (3 points): Delete a bucket that is empty\n")
            _, ret = self.test_deletedir(bucket_name, fp)
            ## Clear s3 bucket
            self.test_deletedir(bucket_name_2, 'requirements.txt')
            time.sleep(6)
            bucket_deleted = self.check_bucket_deleted(ret, bucket_name)
            if bucket_deleted:
                fp.write("\npassed\n")
                points = points + 3
            else:
                fp.write("\nfailed\n")

        print("Total points:" + str(points))
        return points
        
def main():
    
    s3_tester = S3Tester()

    if len(sys.argv) < 2:
        print("python s3tester.py <bucket-name-prefix>\n")
        exit(0)

    bucket_name_prefix = sys.argv[1]
    final_score = 0

    # Create a bucket for testing use
    timeInMillis = round(time.time() * 1000)
    bucket_name = bucket_name_prefix.lower() + "-" + str(timeInMillis)
    fp = open(bucket_name_prefix + '.txt', 'a', encoding='utf-8')
    fp.write("Bucket name:" + bucket_name + '\n')

    while True:
    
        test_case_number = input("Enter test case>")
        # After finish running all the 26 test cases
        if test_case_number == 'exit':
            fp.write("---------------------\n")
            fp.write("Final score: " + str(final_score))
            fp.close()
            exit()
        else:
            # This tester follows a specific operation order
            # When a bucket is not created/ deleted, or an object is not uploaded/downloaded/deleted
            # an error will occur.
            # While the tester will continue running until the last test case.
            # When input 'exit', all the processes will be wrote into an output.txt accordingly.
            for i in range(int(test_case_number), 27):
                try:
                    score = s3_tester.run_tests(i, bucket_name, fp)
                    final_score = final_score + score
                    
                except Exception as e:
                    print("An error occurred in Test case %s: " % str(i))
                    print(e)
                    fp.write("\nAn error occurred in Test case: " + str(i) + '\n')
                    fp.write(str(e) + '\n')
                    
                continue

if __name__ == '__main__':
    main()