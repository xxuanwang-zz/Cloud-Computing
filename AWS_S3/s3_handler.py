import ast
import boto3
import logging
import os
from os import path
import sys
import traceback

import time

LOG_FILE_NAME = 'output.log'

REGION = 'us-east-2'


class S3Handler:
    """S3 handler."""

    def __init__(self):
        self.client = boto3.client('s3')
        self.resource = boto3.resource('s3')
        
        logging.basicConfig(filename=LOG_FILE_NAME,
                            level=logging.DEBUG, filemode='w',
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger("S3Handler")

    def help(self):
        print("Supported Commands:")
        print("1. createdir <bucket_name>")
        print("2. upload <source_file_name> <bucket_name> [<dest_object_name>]")
        print("3. download <dest_object_name> <bucket_name> [<source_file_name>]")
        print("4. delete <dest_object_name> <bucket_name>")
        print("5. deletedir <bucket_name>")
        print("6. find <file_extension> [<bucket_name>] -- e.g.: 1. find txt  2. find txt bucket1 --")
        print("7. listdir [<bucket_name>]")
        
    def _notifications(self, notice):
        notice_dict = {}
        #notice_dict['overwrite'] = 'Overwrite. The destination file already exists.'
        notice_dict['no_files_found'] = 'No files found.'
        notice_dict['bucket_empty'] = 'This bucket is empty.'
        notice_dict['s3_empty'] = 'No buckets found.'
        if notice:
            return notice_dict[notice]
        else: 
            return notice_dict['unknown_notice']
        
    def _error_messages(self, issue):
        error_message_dict = {}
        error_message_dict['operation_not_permitted'] = 'Not authorized to access resource.'
        error_message_dict['incorrect_parameter_number'] = 'Incorrect number of parameters provided'
        error_message_dict['not_implemented'] = 'Functionality not implemented yet!'
        error_message_dict['bucket_name_exists'] = 'Directory already exists.'
        error_message_dict['bucket_name_empty'] = 'Directory name cannot be empty.'
        error_message_dict['non_empty_bucket'] = 'Directory is not empty.'
        error_message_dict['missing_source_file'] = 'Source file cannot be found.'
        error_message_dict['non_existent_bucket'] = 'Directory does not exist.'
        error_message_dict['non_existent_object'] = 'Destination File does not exist.'
        error_message_dict['unknown_error'] = 'Something was not correct with the request. Try again.'

        error_message_dict['rename_failed'] = 'Rename failed.'
        error_message_dict['download_failed'] = 'Download failed.'
        error_message_dict['delete_obj_failed'] = 'The file was not deleted successfully'
        error_message_dict['delete_failed'] = 'The folder was not deleted successfully'
		
        if issue:
            return error_message_dict[issue]
        else:
            return error_message['unknown_error']

    def _get_file_extension(self, file_name):
        if os.path.exists(file_name):
            return os.path.splitext(file_name)

    def _get(self, bucket_name):
        response = ''
        try:
            response = self.client.head_bucket(Bucket=bucket_name)
        except Exception as e:
            response_code = e.response['Error']['Code']
            if response_code == '404':
                return False
            elif response_code == '200':
                return True
            else:
                raise e
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def createdir(self, bucket_name):
        if not bucket_name:
            return self._error_messages('bucket_name_empty')

        try:
            if self._get(bucket_name):
                return self._error_messages('bucket_name_exists')
            self.client.create_bucket(Bucket=bucket_name,
                                      CreateBucketConfiguration={'LocationConstraint': REGION})
        except Exception as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                return self._error_messages('operation_not_permitted')

        # Success response
        operation_successful = ('Directory %s created.' % bucket_name)
        return operation_successful

    def listdir(self, bucket_name):
        # If bucket_name is empty then display the names of all the buckets
        item_names = []
        response = self.client.list_buckets()['Buckets']
        if bucket_name == '':
            for bucket in response:
                item_names.append(bucket['Name'])
            if not item_names:
                return self._notifications('s3_empty')
        else:
            # If bucket_name is provided, check that bucket exits.
            try:
                if not self._get(bucket_name):
                    return self._error_messages('non_existent_bucket')
            except Exception as e:
                return e

        if bucket_name != '':
            # If bucket_name is not empty, then display the names of all the objects
            num_objects = self.client.list_objects_v2(Bucket = bucket_name)['KeyCount']
            if num_objects == 0:
                return self._notifications('bucket_empty')
            for key in self.client.list_objects_v2(Bucket = bucket_name)['Contents']:
                item_names.append(key['Key'])

        # Success response
        return item_names

    def upload(self, source_file_name, bucket_name, dest_object_name):

        if not os.path.isfile(source_file_name):
            return self._error_messages('missing_source_file')
        
        try:
            if not self._get(bucket_name):
                return self._error_messages('non_existent_bucket')
            self.client.head_bucket(Bucket = bucket_name)
            
        except Exception as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                return self._error_messages('operation_not_permitted')
        
        try:
            if self._get(bucket_name):
                if dest_object_name == '':
                    dest_object_name = source_file_name
            
            file_name = self._get_file_extension(source_file_name)[0]
            file_extension = self._get_file_extension(source_file_name)[1]

            ExtraArgs = {
                'Metadata':{
                    'file_name': file_extension
                    }
                }
                
            self.client.upload_file(source_file_name, bucket_name, dest_object_name, ExtraArgs)
            response = self.client.put_object_tagging(
                Bucket = bucket_name,
                Key = source_file_name,
                Tagging = {
                    'TagSet': [
                        {
                            'Key': file_name,
                            'Value': file_extension
                            },
                        ]
                    }
                )

        except Exception as e:
            raise ("Failed to upload %s to %s: %s" % (source_file_name, '/'.join([bucket_name, file_name]), e))

        # Success response
        operation_successful = ('File %s uploaded to bucket %s.' % (source_file_name, bucket_name))
        return operation_successful
    
    def download(self, dest_object_name, bucket_name, source_file_name):
        download_timestamp = time.time() * 1000
        try:
            if not self._get(bucket_name):
                return self._error_messages('non_existent_bucket')
            self.client.head_bucket(Bucket = bucket_name)
            
        except Exception as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                return self._error_messages('operation_not_permitted')

        if source_file_name == '':
            source_file_name = dest_object_name

        try:
            if source_file_name in os.listdir():
                new_name = source_file_name + '.bak.' + str(download_timestamp)
                os.rename(source_file_name, new_name)
                print("The existing file is renamed to %s." % new_name)
        except:
            return self._error_messages('rename_failed')
            
        # Check if Destination Object exists
        try:
            self.client.head_object(Bucket = bucket_name, Key = dest_object_name)
        except:
            return self._error_messages('non_existent_object')
        
        try:
            self.client.download_file(bucket_name, dest_object_name, source_file_name)
        except Exception as e:
            return self._error_messages('download_failed')

        # Success response
        operation_successful = ('Object %s downloaded from bucket %s.' % (dest_object_name, bucket_name))
        return operation_successful

    def delete(self, dest_object_name, bucket_name):
        # Validate if Directory Exists and Destination Object exists
        if not self._get(bucket_name):
            return self._error_messages('non_existent_bucket')
        
        try:
            self.client.head_object(Bucket = bucket_name, Key = dest_object_name)
        except:
            return self._error_messages('non_existent_object')

        try:
            self.client.delete_object(Bucket = bucket_name, Key = dest_object_name)
        except Exception as e:
            return self._error_messages('delete_obj_failed')
        
        # Success response
        operation_successful = ('Object %s deleted from bucket %s.' % (dest_object_name, bucket_name))
        return operation_successful

    def deletedir(self, bucket_name):
        # Validation: Bucket exists, bucket empty
        if not self._get(bucket_name):
            return self._error_messages('non_existent_bucket')
        
        num_objects = self.client.list_objects_v2(Bucket = bucket_name)['KeyCount']
        if (num_objects > 0):
            # The bucket not empty
            return self._error_messages('non_empty_bucket')

        # Delete the bucket
        try:
            self.client.delete_bucket(Bucket = bucket_name)
        except Exception as e:
            return self._error_messages('delete_failed')

        # Success response
        operation_successful = ("Deleted bucket %s." % bucket_name)
        return operation_successful

    def find(self, file_extension, bucket_name):
        extension = "." + file_extension
        search_objects = []
        # If bucket name not specified, search all buckets
        try:
            if bucket_name == '':
                specific_buckets = []
                for bucket in self.client.list_buckets()['Buckets']:
                    specific_buckets.append(bucket['Name'])
                for i in specific_buckets:
                    num_objects = self.client.list_objects_v2(Bucket = i)['KeyCount']
                    if num_objects != 0:
                        obj_names = []
                        for key in self.client.list_objects_v2(Bucket = i)['Contents']:
                            obj_names.append(key['Key'])
                        for j in obj_names:
                            metadata_dict = self.client.head_object(Bucket = i, Key = j)['Metadata']
                            if metadata_dict['file_name'] == extension:
                                search_objects.append(j)
            # If bucket name provided, check the existence. Search for objects if the bucket exist
            if bucket_name != '':
                try:
                    if not self._get(bucket_name):
                        return self._error_messages('non_existent_bucket')
                except Exception as e:
                    return e

                num_objects = self.client.list_objects_v2(Bucket = bucket_name)['KeyCount']
                if num_objects != 0:
                    obj_names = []
                    for key in self.client.list_objects_v2(Bucket = bucket_name)['Contents']:
                        obj_names.append(key['Key'])
                    for j in obj_names:
                        metadata_dict = self.client.head_object(Bucket = bucket_name, Key = j)['Metadata']
                        if metadata_dict['file_name'] == extension:
                            search_objects.append(j)

            if not search_objects:
                return self._notifications('no_files_found')

        except Exception as e:
            return self._error_messages('unknown_error')

        # Success response
        operation_successful = ("Search results: %s" % search_objects)
        return operation_successful
    
    def dispatch(self, command_string):
        parts = command_string.split(" ")
        response = ''

        if parts[0] == 'createdir':
            # Figure out bucket_name from command_string
            if len(parts) > 1:
                bucket_name = parts[1]
                response = self.createdir(bucket_name)
            else:
                # Parameter Validation
                # - Bucket name is not empty
                response = self._error_messages('bucket_name_empty')
                
        elif parts[0] == 'listdir':
            if len(parts) == 2:
                bucket_name = parts[1]
            else:
                bucket_name = ''
            response = self.listdir(bucket_name)
            
        elif parts[0] == 'upload':
            if len(parts) == 4:
                source_file_name = parts[1]
                bucket_name = parts[2]
                dest_object_name = parts[3]
                response = self.upload(source_file_name, bucket_name, dest_object_name)
            elif len(parts) == 3:
                source_file_name = parts[1]
                bucket_name = parts[2]
                response = self.upload(source_file_name, bucket_name, dest_object_name = '')
            else:
                response = self._error_messages('incorrect_parameter_number')
                
        elif parts[0] == 'download':
            if len(parts) == 4:
                dest_object_name = parts[1]
                bucket_name = parts[2]
                source_file_name = parts[3]
                response = self.download(dest_object_name, bucket_name, source_file_name)
            elif len(parts) == 3:
                dest_object_name = parts[1]
                bucket_name = parts[2]
                response = self.download(dest_object_name, bucket_name, source_file_name = '')
            else:
                response = self._error_messages('incorrect_parameter_number')
                
        elif parts[0] == 'delete':
            if len(parts) == 3:
                dest_object_name = parts[1]
                bucket_name = parts[2]
                response = self.delete(dest_object_name, bucket_name)
            else:
                response = self._error_messages('incorrect_parameter_number')
                
        elif parts[0] == 'deletedir':
            if len(parts) == 2:
                bucket_name = parts[1]
                response = self.deletedir(bucket_name)
            else:
                response = self._error_messages('bucket_name_empty')
                
        elif parts[0] == 'find':
            file_extension = parts[1]
            if len(parts) == 3:
                bucket_name = parts[2]
                response = self.find(file_extension, bucket_name)
            elif len(parts) == 2:
                response = self.find(file_extension, bucket_name = '')
            else:
                response = self._error_messages('incorrect_parameter_number')
 
        else:
            response = "Command not recognized."
        return response

def main():

    s3_handler = S3Handler()
    
    while True:
        try:
            command_string = ''
            if sys.version_info[0] < 3:
                command_string = input("Enter command ('help' to see all commands, 'exit' to quit)>")
            else:
                command_string = input("Enter command ('help' to see all commands, 'exit' to quit)>")

            command_string = " ".join(command_string.split())
            
            if command_string == 'exit':
                print("Good bye!")
                exit()
            elif command_string == 'help':
                s3_handler.help()
            else:
                response = s3_handler.dispatch(command_string)
                print(response)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()