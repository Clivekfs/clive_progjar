import sys
import os.path
import uuid
import re
from glob import glob
from datetime import datetime

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)

		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		return response

	def proses(self, data_as_bytes):
		header_part, _, body_part = data_as_bytes.partition(b'\r\n\r\n')
		
		try:
			headers_text = header_part.decode('utf-8')
		except UnicodeDecodeError:
			return self.response(400, 'Bad Request', b'Invalid header encoding', {})

		requests = headers_text.split('\r\n')
		if not requests or not requests[0]:
			return self.response(400, 'Bad Request', b'Empty request', {})

		baris = requests[0]
		all_headers = requests[1:]
		
		j = baris.split(" ")
		try:
			method = j[0].upper().strip()
			object_address = j[1].strip()

			if method == 'GET':
				return self.http_get(object_address, all_headers)
			elif method == 'POST':
				return self.http_post(object_address, all_headers, body_part)
			elif method == 'DELETE':
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(405, 'Method Not Allowed', b'', {})
		except IndexError:
			return self.response(400, 'Bad Request', b'', {})

	def http_get(self, object_address, headers):
		thedir = '.'
		full_path = thedir + object_address

		if os.path.isdir(full_path):
			try:
				files_and_dirs = os.listdir(full_path)
				response_body = "<html><head><title>Directory Listing</title></head><body><h1>Listing for " + object_address + "</h1><ul>"
				for item in files_and_dirs:
					item_path = os.path.join(object_address, item).replace("\\", "/")
					if not item_path.startswith('/'):
						item_path = '/' + item_path
					response_body += '<li><a href="' + item_path + '">' + item + '</a></li>'
				response_body += "</ul></body></html>"
				return self.response(200, 'OK', response_body.encode(), {'Content-Type': 'text/html'})
			except OSError as e:
				return self.response(500, 'Internal Server Error', str(e).encode(), {})
		
		filepath = object_address.lstrip('/')
		if not os.path.exists(filepath):
			return self.response(404, 'Not Found', b'', {})

		with open(filepath, 'rb') as fp:
			isi = fp.read()

		fext = os.path.splitext(filepath)[1]
		content_type = self.types.get(fext, 'application/octet-stream')
		
		headers_dict = {'Content-type': content_type}
		return self.response(200, 'OK', isi, headers_dict)

	def http_post(self, object_address, headers, body):
		content_type_header = next((h for h in headers if h.lower().startswith('content-type:')), None)
		if not content_type_header or 'multipart/form-data' not in content_type_header:
			return self.response(400, 'Bad Request', b'Content-Type must be multipart/form-data.', {})

		try:
			boundary = content_type_header.split('boundary=')[1].encode()
			parts = body.split(b'--' + boundary)
			
			for part in parts:
				if b'Content-Disposition: form-data;' in part and b'filename=' in part:
					header_part, content = part.split(b'\r\n\r\n', 1)
					filename_match = re.search(b'filename="(.+?)"', header_part)

					if filename_match:
						filename = filename_match.group(1).decode()
						
						if content.endswith(b'\r\n'):
							content = content[:-2]
						
						with open(filename, 'wb') as f:
							f.write(content)
						
						return self.response(200, 'OK', f'File {filename} uploaded successfully.'.encode(), {})
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', str(e).encode(), {})
			
		return self.response(400, 'Bad Request', b'Invalid form data.', {})

	def http_delete(self, object_address, headers):
		filepath = object_address.strip('/')
		if os.path.exists(filepath):
			try:
				os.remove(filepath)
				return self.response(200, 'OK', f'File {filepath} deleted.'.encode(), {})
			except OSError as e:
				return self.response(500, 'Internal Server Error', str(e).encode(), {})
		else:
			return self.response(404, 'Not Found', b'File not found.', {})













