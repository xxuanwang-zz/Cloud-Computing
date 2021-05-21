from __future__ import print_function
import boto3
import json
import sys
import time
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

class DynamoDBHandler:

    def __init__(self, region):
        self.client = boto3.client('dynamodb')
        self.resource = boto3.resource('dynamodb', region_name=region)
    
    def help(self):
        print("Supported Commands:")
        print("1. insert_movie")
        print("2. delete_movie")
        print("3. update_movie")
        print("4. search_movie_actor")
        print("5. search_movie_actor_director")
        print("6. print_stats")
        print("7. delete_table")

    # Failure reasons
    def _failure_reasons(self, issue):
        failure_reason_dict = {}
        failure_reason_dict['table_does_not_exist'] = 'Table does not exist'
        failure_reason_dict['invaild_para'] = 'Invalid parameter. Please try again'

        if issue:
            return failure_reason_dict[issue]
        else:
            return failure_reason['unknown_error']
			
			
    def create_and_load_data(self, table_Name, file_Name):
        # Followed AWS documentation
        table = self.resource.create_table(
            TableName = table_Name,
            KeySchema=[
            {
                'AttributeName': 'year',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'title',
                'KeyType': 'RANGE'  # Sort key
            }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'year',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'title',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        print('Creating the Table %s' % table_Name)
        waiter = self.client.get_waiter('table_exists')
        waiter.wait(TableName = table_Name)

        try:
            self.client.describe_table(TableName = table_Name)
            print('%s Table created. Loading data...' % table_Name)

        except ClientError as e:
            print("Table creation failed - %s" % e.response['Error']['Message'])

        with open(file_Name) as json_file:
            movie_list = json.load(json_file, parse_float = Decimal)

        table = self.resource.Table(table_Name) 
        for movie in movie_list:
            year = int(movie['year'])
            title = movie['title']
            title_lower = title.lower()
            info = movie['info']
            movie = {
                'year': year,
                'title': title,
                'title_lower': title_lower
                }
            movie['rating'] = 0
            try:
                movie['directors'] = info['directors']
                movie['directors_lower'] = [d.lower() for d in info['directors']]
                movie['actors'] = info['actors']
                movie['actors_lower'] = [a.lower() for a in info['actors']]
                movie['release_date'] = info['release_date'].split('T', 1)[0]
                movie['rating'] = info['rating']

            # In case some items do not have 'rating' attribute
            except:
                pass

            table.put_item(Item = movie)
            print('Movie:', year, title)

        print('%s table creation and data loading have been completed!' % table_Name)
    
    def insert_movie(self, year, title, directors, actors, release_date, rating):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return ('Movie %s could not be inserted - %s' %(title, e))
        
        table = self.resource.Table('Movies')
        try:
            movie = {
				'year': int(year),
				'title': title,
				'title_lower': title.lower()
			}

			# Split the directors list
            if directors:
                movie['directors'] = [x.strip() for x in directors.split(',')]
                movie['directors_lower'] = [d.lower() for d in directors.split(',')]

            if actors:
                movie['actors'] = [x.strip() for x in actors.split(',')]
                movie['actors_lower'] = [a.lower() for a in actors.split(',')]

			# Release date
            if release_date:
                movie['release_date'] = datetime.strptime(release_date, "%d %b %Y").strftime("%Y-%m-%d")

			# Ratings
            if rating:
                movie['rating'] = rating

            response = table.put_item(Item = movie)
            return ('Movie %s succesfully inserted' % title)
			
        except ClientError as e:
            return ('Movie %s could not be inserted - %s' %(title, e.response['Error']['Message']))
    
    def delete_movie(self, title):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return ('Movie %s could not be deleted - %s' %(title,e))

        table = self.resource.Table('Movies')
        response = table.scan(FilterExpression = Attr('title_lower').eq(title.lower()))
        if 'Items' in response:
            data = response['Items']

        # No items found
        if not data:
            return ('Movie %s does not exist' % title)
        
        # delete movies
        for movie in data:
            try:
                response = table.delete_item(
                    Key={
                        'year': movie['year'],
                        'title': movie['title']
                    }
                )
            except ClientError as e:
                return ('Movie %s could not be deleted - %s' %(title, e.response['Error']['Message']))

        return ('Movie %s succesfully deleted' % title)
    

    def update_movie(self, year, title, directors, actors, release_date, rating):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return ('Movie %s could not be updated- %s' %(title,e))

        table = self.resource.Table('Movies')
        response = table.query(KeyConditionExpression= Key('year').eq(year) & Key('title').eq(title))

        if 'Items' in response:
            item = response['Items']
        
        # No items found
        if not item:
            return ('Movie %s, %s does not exist' %(title, year))
        try:
            for i in range(0, len(item)):
                updated_movie = item[i]
                updated_movie['year'] = year
                updated_movie['title'] = title
                updated_movie['title_lower'] = title.lower()
                updated_movie['rating'] = rating

                # Attributes
                updated_movie['directors'] = [x.strip() for x in directors.split(',')]
                updated_movie['directors_lower'] = [x.lower() for x in directors.split(',')]

                updated_movie['actors'] = [x.strip() for x in actors.split(',')]
                updated_movie['actors_lower'] = [x.lower() for x in actors.split(',')]

                updated_movie['release_date'] = datetime.strptime(release_date, "%d %b %Y").strftime("%Y-%m-%d")
                updated_movie['rating'] = rating

                response = table.put_item(Item = updated_movie)
            return ('Movie %s succesfully updated' % title)

        except ClientError as e:
            return ('Movie %s could not be updated - %s' %(title, e.response['Error']['Message']))

    def search_movie_actor(self, actor):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return self._failure_reasons("tabel_does_not_exist")

        table = self.resource.Table('Movies')
        response = table.scan(FilterExpression=Attr('actors_lower').contains(actor.lower()))
        data = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('actors_lower').contains(actor.lower()),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            data.extend(response['Items'])

        # No movies found
        if not data:
            return ('No movies found for actor %s' % actor)

        items = []
        for movie in data:
            output = {
                'info': 
                {
                    'actors': movie['actors']
                    },
                    'title': movie['title'], 
                    'year': int(movie['year'])
                    }
            items.append(output)
        
        return items
    
    def search_movie_actor_director(self, actor, director):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return self._failure_reasons("tabel_does_not_exist")

        table = self.resource.Table('Movies')

        response = table.scan(FilterExpression= Attr('actors_lower').contains(actor.lower()) 
                                & Attr('directors_lower').contains(director.lower()))
        data = response['Items']

        # Get all movies
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('actors_lower').contains(actor.lower()) 
                                & Attr('directors_lower').contains(director.lower()),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            data.extend(response['Items'])

        # No movies found
        if not data:
            return ('No movies found for actor %s and director %s' % (actor, director))

        items = []
        for movie in data:
            output = {
                'info': 
                {
                    'actors': movie['actors'], 
                    'directors': movie['directors']
                    }, 
                    'title': movie['title'], 
                    'year': int(movie['year'])
                    }
                    
            items.append(output)
        
        return items

    def print_stats(self, stat):
        try:
            self.client.describe_table(TableName='Movies')
        except Exception as e:
            return ('Movies table does not exist')

        table = self.resource.Table('Movies')
        results = table.scan()

        highest_rating = -1000
        lowest_rating = 1000

        for movie in results['Items']:
            highest_rating = max(Decimal(movie['rating']), highest_rating)
            lowest_rating = min(Decimal(movie['rating']), lowest_rating)
        
        items = []
        if stat == 'highest_rating_movie':
            results = table.scan(FilterExpression=Attr('rating').eq(highest_rating))
            for movie in results['Items']:
                info = {}
                info['actors'] = movie['actors']
                info['directors'] = movie['directors']
                info['rating'] = float(movie['rating'])
                info['title'] = movie['title']
                info['year'] = int(movie['year'])
                items.append(info)
            return items

        elif stat == 'lowest_rating_movie':
            results = table.scan(FilterExpression=Attr('rating').eq(lowest_rating))
            for movie in results['Items']:
                info = {}
                info['actors'] = movie['actors']
                info['directors'] = movie['directors']
                info['rating'] = float(movie['rating'])
                info['title'] = movie['title']
                info['year'] = int(movie['year'])
                items.append(info)
            return items

    def delete_table(self, table_Name):
        try:
            table = self.resource.Table(table_Name)
            table.delete()

            # Add waiter()
            waiter = self.client.get_waiter('table_not_exists')
            waiter.wait(TableName = table_Name)
            return ('Table %s successfully deleted' % table_Name)

        except Exception as e:
            return ('Table %s does not exist' % table_Name)
    
    def dispatch(self, command_string):
        parts = command_string.split(" ")
        response = ''
        if parts[0] == 'insert_movie':
            year = input("Year>")
            if not year:
                return ("Year can not be empty")
            try:
                year_int = int(year)
            except Exception as e:
                return self._failure_reasons('invalid_para')

            title = input("Title>")
            if not title:
                return "Title can not be empty"

            directors = input("Directors>")
            if not directors:
                return ("Directors can not be empty")

            actors = input("Actors>")
            if not actors:
                return ("Actors can not be empty")

            release_date = input("Release date>")
            rating = input("Rating>")

            response = self.insert_movie(year_int, title, directors, actors, release_date, rating)

        elif parts[0] == 'delete_movie':
            title = input("Title>")
            if not title:
                return ("Title can not be empty")

            response = self.delete_movie(title)
            
        elif parts[0] == 'update_movie':
            year = input("Year>")
            if not year:
                return ("Year can not be empty")
            try:
                year_int = int(year)
            except Exception as e:
                return self._failure_reasons('invalid_para')

            title = input("Title>")
            if not title:
                return "Title can not be empty"

            directors = input("Directors>")
            if not directors:
                return ("Directors can not be empty")

            actors = input("Actors>")
            if not actors:
                return ("Actors can not be empty")

            release_date = input("Release date>")
            rating = input("Rating>")

            response = self.update_movie(year_int, title, directors, actors, release_date, rating)

        elif parts[0] == 'search_movie_actor':
            actor = input("Actor>")
            if not actor:
                return ("Actor can not be blank, please enter an actor's first and last name.")

            response = self.search_movie_actor(actor)

        elif parts[0] == 'search_movie_actor_director':
            actor = input("Actor>")
            if not actor:
                return ("Actor can not be empty. Please type in a full name")

            director = input("Director>")
            if not director:
                return("Director can not be empty. Please type in a full name")

            response = self.search_movie_actor_director(actor, director)

        elif parts[0] == 'print_stats':
            stat = input("stat>")
            if stat != "highest_rating_movie" and stat != "lowest_rating_movie":
                response = ("Unrecognized command %s" % stat)
            else:
                response = self.print_stats(stat)
            return response
            
        elif parts[0] == 'delete_table':
            tableName = input("table_name>")
            if not tableName:
                return ("Table name can not be empty")

            response = self.delete_table(tableName)
        else:
            response = 'Command not recognized.'
        return response

def main():
    # Parameter Validation (One argument - region)
    if len(sys.argv) != 2:
        print("Please try enter - python dynamodb_handler.py <region>")
        sys.exit()
    else:
        args = sys.argv
        region = sys.argv[1]
        dynamodb_handler = DynamoDBHandler(region)
        table_Name = "Movies"
        movie_data = "moviedata.json"

        try:
            dynamodb_handler.create_and_load_data(table_Name, movie_data)
        except Exception as e:
            if "table already exists" in str(e).lower():
                print('%s Table already exists' % table_Name)
            else:
                print(e)
            
        while True:
            try:
                command_string = ''
                if sys.version_info[0] < 3:
                    command_string = raw_input("Enter command ('help' to see all commands, 'exit' to quit)>")
                else:
                    command_string = input("Enter command ('help' to see all commands, 'exit' to quit)>")
        
                # Remove multiple whitespaces, if they exist
                command_string = " ".join(command_string.split())
                
                if command_string == 'exit':
                    print("Good bye!")
                    exit()
                elif command_string == 'help':
                    dynamodb_handler.help()
                else:
                    response = dynamodb_handler.dispatch(command_string)
                    if isinstance(response, list):
                        try:
                            for movie in response:
                                json_object = json.dumps(movie)
                                print(json_object)
                        except Exception as e:
                            print(response)
                    else:
                        print(response)
            except Exception as e:
                print(e)

if __name__ == '__main__':
    main()