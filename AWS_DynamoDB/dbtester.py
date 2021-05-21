import sys
import dynamodb_handler as dbh
import json
import pexpect
import time
import subprocess
import unittest
import io
import re
import os

class DBTester:
    
    def __init__(self):
        pass

    def aws_cli_db(self, table_name, key):

        print("Verifying using aws command..")
        cmd_describe = "aws dynamodb describe-table --table-name"
        cmd_ls = 'aws dynamodb list-tables'
        cmd_batch_getItem = 'aws dynamodb batch-get-item'
        if table_name:
            cmd = cmd_describe + " " + table_name
        if key:
            cmd = cmd_batch_getItem + " " + "--request-items file://" + key
        else:
            cmd = cmd_ls
        try:
            print(cmd)
            out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()[0]
            out = out.decode("utf-8")
            return out

        except Exception as e:
            print(e)
            print(e.response['Error']['Message'])
    
    def test_create_table(self, table_Name):
        result = self.aws_cli_db(table_Name,'')
        table_created = False
        if table_Name in result:
            table_created = True
        return table_created

    def test_delete_table(self, table_Name):
        result = self.aws_cli_db('', '')
        table_deleted = False
        if table_Name not in result:
            table_deleted = True
        return table_deleted

    def test_insert(self, key, year, title):
        out = self.aws_cli_db('', key)
        print(out)
        if year in out and title in out:
            return True
        else:
            return False
    
    def test_delete_movie(self, title, key):
        out = self.aws_cli_db('', key)
        #print(out)
        if title not in out:
            return True
        else:
            return False

    def test_update(self, test_updated, key):
        out = self.aws_cli_db('', key)
        print(out)
        if all([i in out for i in test_updated]):
            return True
        else: 
            return False

    def run_tests(self, test_case_number, table_Name, fp, p):
	
        total_points = 97
        points = 0

        if test_case_number == 1:
            fp.write("--------------------------------\n")
            fp.write("Create Table (1/1)\n")
            fp.write("Test case 1 (6 points): Create the table\n")
            ret = self.test_create_table(table_Name)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 6
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 2:
            fp.write("--------------------------------\n")
            fp.write("Insert a movie (1/1)\n")
            fp.write("Test case 2 (8 points): Insert an item with directors in comma separated list\n")
            year_2 = "2019"
            title_2 = "Avengers: Endgame"

            p.sendline('insert_movie') # command + <enter>

            p.expect(r'Year(.*?)')
            p.sendline(year_2)

            p.expect(r'Title(.*?)')
            p.sendline(title_2)

            p.expect(r'Director(.*?)')
            p.sendline('Anthony Russo, Joe Russo')

            p.expect(r'Actor(.*?)')
            p.sendline('Robert Downey Jr., Chris Evans, Mark Ruffalo')
            
            p.expect(r'Release date(.*?)')
            p.sendline('26 Apr 2019')

            p.expect(r'Rating(.*?)')
            p.sendline('8.4')
            
            time.sleep(5)
            key_2 = 'key_2.json'
            ret = self.test_insert(key_2, year_2, title_2)
            print("ret", ret)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 8
            else:
                print('failed', test_case_number)
                print('****************')
                print(p.before.decode())
                fp.write("\nfailed\n")

        if test_case_number == 3:
            fp.write("--------------------------------\n")
            fp.write("Update a Movie (1/2)\n")
            fp.write("Test case 3 (10 points): Update an item with directors in comma separated list")
            year_3 = "2013"
            title_3 = "Thor: The Dark World"
            key_3 = 'key_3.json'

            updated_actors = "Test_update, Chris Hemsworth, Natalie Portman, Tom Hiddleston"
            updated_release_date = "08 Nov 2014"
            test_updated = ["Test_update", "08", "2014"]

            p.sendline('update_movie') # command + <enter>

            p.expect(r'Year(.*?)')
            p.sendline(year_3)

            p.expect(r'Title(.*?)')
            p.sendline(title_3)

            p.expect(r'Director(.*?)')
            p.sendline('Alan Taylor')

            p.expect('Actor(.*?)')
            p.sendline(updated_actors)
            
            p.expect(r'Release date(.*?)')
            p.sendline(updated_release_date)

            p.expect(r'Rating(.*?)')
            p.sendline('7.2')

            ret = self.test_update(test_updated, key_3)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 10
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 4:
            fp.write("--------------------------------\n")
            fp.write("Update a Movie (2/2)\n")
            fp.write("Test case 4 (3 points): Update a movie item that does not exist")
            title_4 = "update-non-existent-movie"

            p.sendline('update_movie') # command + <enter>
            p.expect(r'Year(.*?)')
            p.sendline("2021")
            p.expect(r'Title(.*?)')
            p.sendline(title_4)
            p.expect(r'Director(.*?)')
            p.sendline('Alan Taylor')
            p.expect(r'Actor(.*?)')
            p.sendline('Chris Hemsworth, Natalie Portman, Tom Hiddleston')
            p.expect(r'Release date(.*?)')
            p.sendline('08 Nov 2014')
            p.expect(r'Rating(.*?)')
            p.sendline('7.2')

            index = p.expect([r'(.*?)does not exist(.*?)', r'(.*?)no(.*?)exists(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index == 1:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index != 0:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 5:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor (1/3)\n")
            fp.write("Test case 5 (3 points): Search an item that does not exist")
            actor_5 = "non-existent-actor"
            
            p.sendline('search_movie_actor')
            p.expect(r'Actor(.*?)')
            p.sendline(actor_5)

            index = p.expect([r'(.*?)No movies found for(.*?)', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index != 0:
                print(p.before.decode())
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 6:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor (2/3)\n")
            fp.write("Test case 6 (5 points): Search an item with the same given actor")
            actor_6 = "Holly Hunter"

            p.sendline('search_movie_actor')
            p.expect(r'Actor(.*?)')
            p.sendline(actor_6)

            expect_list = ["actors", "Brittany Murphy", "Ron Livingston", "Holly Hunter", "title", "Little Black Book", "year", "2004"]
            expect_string = '{"info": {"actors": ["Brittany Murphy", "Ron Livingston", "Holly Hunter"]}, "title": "Little Black Book", "year": 2004}'
            
            index = p.expect([expect_string, pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 5
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 7:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor (3/3)\n")
            fp.write("Test case 7 (8 points): Search an item with given actor - Case insensitivity Test")
            actor_7 = "hoLLY HunTER"
            
            p.sendline('search_movie_actor')
            p.expect('Actor(.*?)')
            p.sendline(actor_7)
            
            expect_list = ["actors", "Brittany Murphy", "Ron Livingston", "Holly Hunter", "title", "Little Black Book", "year", "2004"]
            expect_string = '{"info": {"actors": ["Brittany Murphy", "Ron Livingston", "Holly Hunter"]}, "title": "Little Black Book", "year": 2004}'
            index = p.expect([r'(.*?)' + expect_string + r'(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 8
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 8:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor and director (1/3)\n")
            fp.write("Test case 8 (3 points): Search an item that does not exist")
            actor_8 = "non-existent-actor"
            director_8 = "non-existent-director"
            
            p.sendline('search_movie_actor_director')
            p.expect(r'Actor(.*?)')
            p.sendline(actor_8)
            p.expect(r'Director(.*?)')
            p.sendline(director_8)
            
            index = p.expect([r'(.*?)No movies found for actor(.*?)and director(.*?)', r'(.*?)No(.*?)found(.*?)', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index == 1:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3                
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 9:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor and director (2/3)\n")
            fp.write("Test case 9 (5 points): Search an item with the same given actor and director")
            actor_9 = "Holly Hunter"
            director_9 = "Nick Hurran"

            p.sendline('search_movie_actor_director')
            p.expect(r'Actor(.*?)')
            p.sendline(actor_9)
            p.expect(r'Director(.*?)')
            p.sendline(director_9)

            expect_list = ["actors", "Brittany Murphy", "Ron Livingston", "Holly Hunter", "directors", "Nick Hurran", "title", "Little Black Book", "year", "2004"]
            expect_string = '{"info": {"actors": ["Brittany Murphy", "Ron Livingston", "Holly Hunter"], "directors": ["Nick Hurran"]}, "title": "Little Black Book", "year": 2004}'

            index = p.expect([r'(.*?)' + expect_string + r'(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 5
            else:
                print('failed', test_case_number)
                print('****************')
                print(p.before.decode())
                fp.write("\nfailed\n")

        if test_case_number == 10:
            fp.write("--------------------------------\n")
            fp.write("Search Movie(s) with given actor and director (3/3)\n")
            fp.write("Test case 10 (8 points): Search an item with given actor and director - Case insensitivity Test")
            actor_10 = "HoLLY HunTER"
            director_10 = "NiCK HurRAN"

            p.sendline('search_movie_actor_director')
            p.expect(r'Actor(.*?)')
            p.sendline(actor_10)
            p.expect(r'Director(.*?)')
            p.sendline(director_10)
            
            expect_list = ["actors", "Brittany Murphy", "Ron Livingston", "Holly Hunter", "directors", "Nick Hurran", "title", "Little Black Book", "year", "2004"]
            expect_string = '{"info": {"actors": ["Brittany Murphy", "Ron Livingston", "Holly Hunter"], "directors": ["Nick Hurran"]}, "title": "Little Black Book", "year": 2004}'

            index = p.expect([r'(.*?)' + expect_string + r'(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 8
            else:
                print('failed')
                print('****************')
                print(p.before.decode())
                fp.write("\nfailed\n")

        if test_case_number == 11:
            fp.write("--------------------------------\n")
            fp.write("Print Movie statistics (1/3)\n")
            fp.write("Test case 11 (2 points): Unrecognized commands")
            command_11 = "unrecognized-statistic-query"

            p.sendline('print_stats')
            p.expect(r'stat(.*?)')
            p.sendline(command_11)

            index = p.expect([r'(.*?)Unrecognized(.*?)', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 2
            elif index != 0:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 12:
            fp.write("--------------------------------\n")
            fp.write("Print Movie statistics (2/3)\n")
            fp.write("Test case 12 (6 points): Print the highest rating")
            command_12 = 'highest_rating_movie'

            p.sendline('print_stats')
            p.expect(r'stat(.*?)')
            p.sendline(command_12)

            expect_list = ["actors", "David Matthewman", "Ann Thomas", "Jonathan G. Neff", "directors", "Alice Smith", "Bob Jones", "rating", "9.2", "title", "Turn It Down!", "year", "2013"]
            expect_string = '"actors": ["David Matthewman", "Ann Thomas", "Jonathan G. Neff"], "directors": ["Alice Smith", "Bob Jones"], "rating": 9.2, "title": "Turn It Down!", "year": 2013'
            index = p.expect([r'(.*?)' + expect_string + r'(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 6
            else:
                print('failed', test_case_number)
                print('****************')
                print(p.before.decode())
                fp.write("\nfailed\n")

        if test_case_number == 13:
            fp.write("--------------------------------\n")
            fp.write("Print Movie statistics (3/3)\n")
            fp.write("Test case 13 (6 points): Print the lowest rating")
            command_13 = 'lowest_rating_movie'

            p.sendline('print_stats')
            p.expect(r'stat(.*?)')
            p.sendline(command_13)

            expect_list = ["actors", "Brittany Murphy", "Ron Livingston", "Holly Hunter", "directors", "Nick Hurran", "rating", "3.1", "title", "Little Black Book", "year", "2004"]
            expect_string = '"actors": ["Brittany Murphy", "Ron Livingston", "Holly Hunter"], "directors": ["Nick Hurran"], "rating": 3.1, "title": "Little Black Book", "year": 2004'
            index = p.expect([r'(.*?)' + expect_string + r'(.*?)', pexpect.EOF, pexpect.TIMEOUT])
            p.buffer

            if all([i in p.before.decode() for i in expect_list]):
                print('passed')
                fp.write("\npassed\n")
                points = points + 6
            else:
                print('failed', test_case_number)
                print('****************')
                print(p.before.decode())
                fp.write("\nfailed\n")

        if test_case_number == 14:
            fp.write("--------------------------------\n")
            fp.write("Delete a movie (1/3)\n")
            fp.write("Test case 14 (5 points): Delete all the movies with the same given movie title")
            title_14 = "Rush"
            key_14 = "key_14.json"

            p.sendline('delete_movie') # command + <enter>

            p.expect(r'Title(.*?)')
            p.sendline(title_14)
            time.sleep(3)

            ret = self.test_delete_movie(title_14, key_14)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 5
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 15:
            fp.write("--------------------------------\n")
            fp.write("Delete a movie (2/3)\n")
            fp.write("Test case 15 (3 points): Delete a movie item that does not exist")
            title_15 = "delete-non-existent-movie"

            p.sendline('delete_movie') # command + <enter>

            p.expect(r'Title(.*?)')
            p.sendline(title_15)
            index = p.expect(['(.*?)does not exist(.*?)', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index != 0:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 16:
            fp.write("--------------------------------\n")
            fp.write("Delete a movie (3/3)\n")
            fp.write("Test case 16 (8 points): Delete - Case insensitivity Test")
            title_16 = "the HUnger Games: catchING FIRE"
            key_16 = "key_16.json"

            p.sendline('delete_movie') # command + <enter>

            p.expect(r'Title(.*?)')
            p.sendline(title_16)

            ret = self.test_delete_movie(title_16, key_16)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 8
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 17:
            fp.write("--------------------------------\n")
            fp.write("Delete table (1/2)\n")
            fp.write("Test case 17 (3 points): Delete a table that does not exist")
            table_Name_17 = "delete-non-existent-table"

            p.sendline('delete_table') # command + <enter>

            p.expect(r'table(.*?)name(.*?)')
            p.sendline(table_Name_17)

            index = p.expect([r'(.*?)does not exist(.*?)', pexpect.EOF, pexpect.TIMEOUT])

            if index == 0:
                print('passed')
                fp.write("\npassed\n")
                points = points + 3
            elif index != 0:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        if test_case_number == 18:
            fp.write("--------------------------------\n")
            fp.write("Delete table (2/2)\n")
            fp.write("Test case 18 (5 points): Delete Movies table")

            p.sendline('delete_table') # command + <enter>

            p.expect(r'table(.*?)name(.*?)')
            p.sendline(table_Name)

            time.sleep(30)
            ret = self.test_delete_table(table_Name)
            if ret:
                print('passed')
                fp.write("\npassed\n")
                points = points + 5
            else:
                print('failed', test_case_number)
                fp.write("\nfailed\n")

        print("Total points:" + str(points))
        return points
        
def main():

    if len(sys.argv) < 2:
        print("python dynamodb_handler.py <region>\n")
        exit(0)

    name_prefix = sys.argv[1]
    final_score = 0

    db_tester = DBTester()
    
    table_name = "Movies"
    p = pexpect.spawn('python dynamodb_handler.py us-west-1')
    time.sleep(20) # Waiting for creating the table
    logFile = open(name_prefix + "-logfile.txt", 'ab')
    p.logfile = logFile
    fp = open(name_prefix + '.txt', 'a', encoding='utf-8')
    fp.write(name_prefix + "\n")

    while True:
        test_case_number = input("Enter test case>")
        if test_case_number == 'exit':
            fp.write("---------------------\n")
            fp.write("Final score:" + str(final_score))
            fp.close()
            logFile.close()
            exit()
        else:
            for i in range(int(test_case_number), 19):
                try:
                    score = db_tester.run_tests(i, table_name, fp, p)
                    final_score = final_score + score
                except Exception as e:
                    print(e)
                    print("An error occurred in Test case: " + str(i))
                    fp.write(str(e))
                    fp.write("\nAn error occurred in Test case: " + str(i) + '\n')
                    
                continue

if __name__ == '__main__':
    main()