import os
import json
import base64
from glob import glob

class FileInterface:
    def __init__(self):
        # Ensure the 'files' directory exists, create if not
        if not os.path.exists('files'):
            os.makedirs('files')
        os.chdir('files/') # Change current directory to files/

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            # Go back to parent directory after listing to keep main path consistent
            # os.chdir('..') 
            return dict(status='OK',data=filelist)
        except Exception as e:
            # os.chdir('..')
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            fp.close() # Close the file
            # os.chdir('..')
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            # os.chdir('..')
            return dict(status='ERROR',data=str(e))

    def upload(self, params=[]):
        try:
            filename = params[0]
            encoded_content = params[1]
            if not filename or not encoded_content:
                return dict(status='ERROR', data='Filename or content missing')
            
            file_content = base64.b64decode(encoded_content, validate=True)
            
            with open(filename, 'wb+') as fp:
                fp.write(file_content)

            return dict(status='OK', data=f"File {filename} uploaded successfully")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        try:
            filename = params[0]
            if not filename:
                # os.chdir('..')
                return dict(status='ERROR', data='Filename missing')
            
            if os.path.exists(filename):
                os.remove(filename)
                return dict(status='OK', data=f"File {filename} deleted successfully")
            else:
                return dict(status='ERROR', data=f"File {filename} not found")
        except Exception as e:
            return dict(status='ERROR', data=str(e))

if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))
    print(f.upload(['test_upload.txt', base64.b64encode(b"Hello Upload").decode()]))
    print(f.list())
    print(f.delete(['test_upload.txt']))
    print(f.list())
