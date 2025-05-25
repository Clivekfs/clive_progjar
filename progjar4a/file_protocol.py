import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""

class FileProtocol:
    def __init__(self):
        self.f = FileInterface()

    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk[:80]}...")  # agar tidak panjang di log

        try:
            if string_datamasuk.startswith("UPLOAD"):
                cmd, filename, base64data = string_datamasuk.split(' ', 2)
                hasil = self.f.upload([filename, base64data])
                return json.dumps(hasil)

            elif string_datamasuk.startswith("GET"):
                parts = shlex.split(string_datamasuk)
                hasil = self.f.get(parts[1:])
                return json.dumps(hasil)

            elif string_datamasuk.startswith("DELETE"):
                parts = shlex.split(string_datamasuk)
                hasil = self.f.delete(parts[1:])
                return json.dumps(hasil)

            elif string_datamasuk.startswith("LIST"):
                hasil = self.f.list()
                return json.dumps(hasil)

            else:
                return json.dumps(dict(status='ERROR', data='Unknown command'))

        except Exception as e:
            return json.dumps(dict(status='ERROR', data=f'Exception: {str(e)}'))
