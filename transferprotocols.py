import sys
import os
import shutil
import ftplib


class TransferProtocol(object):
	def __init__(self):
		pass
	
	def ls(self):
		pass

	def get(self,remote_file_name,local_file_name):
		pass
	
	def put(self,local_file_name,remote_file_name):
		pass
	
	def exists(self,file_name):
		pass
	
	def delete(self,file_name):
		pass
		
class FileTransferProtocol(TransferProtocol):
	def __init__(self,host,**kwargs):
		self._ftp = ftplib(host,**kwargs)
	
	def __del__(self):
		self._ftp.quit()

	def ls(self,dir):
		return self._ftp.nlst(dir)

	def get(self,remote_file_name,local_file_name):
		source = "RETR {0}".format(remote_file_name)
		dest = "{0}".format(local_file_name)
		self._ftp.retrbinary(source, open(dest, 'wb').write)
	
	def put(self,local_file_name,remote_file_name):
		dest = "STOR {0}".format(remote_file_name)
		source = "{0}".format(local_file_name)
		self._ftp.storbinary(dest, open(source, "rb"), 1024)
	
	def exists(self,file_path):
		directory = os.path.dirname(file_path)
		file_name = os.path.basename(file_path)
		files = self.ls(directory)

		return file_name in files

	def delete(self,file_path):
		""" Delete remote FTP file

			Currently not supported, puck initially only supports
			non-destructive file I/O
		"""
		raise NotImplementedError("ftp delete not implemented")
		try:
			self._ftp.delete(file_path) 
		except Exception,e:
			raise ValueError("Invalid ftp file {0}".format(file_path))

class LocalFileTransferProtocol(TransferProtocol):
	
	def ls(self,path):
		return filter(lambda x: os.path.isfile(x),os.listdir("."))

	def get(self,remote_file_name,local_file_name):
		shutil.copy(remote_file_name,local_file_name)
	
	def put(self,local_file_name,remote_file_name):
		shutil.copy(local_file_name,remote_file_name)

	def exists(self,remote_file_name):
		try:
			with open(remote_file_name,'r') as f:
				pass
			return True
		except IOError:
			return False
	
	def delete(self,remote_file_name):
		""" Delete local FTP file

			Currently not supported, puck initially only supports
			non-destructive file I/O
		"""
		raise NotImplementedError("ftp delete not implemented")

		try:
			os.remove(remote_file_name)	
		except Exception,e:
			raise ValueError("Invalid local file {0}".format(file_path))


class HttpTransferProtocol(TransferProtocol):
	pass

class S3TransferProtocol(TransferProtocol):
	pass
	
TransferProtocols = {
	'file':LocalFileTransferProtocol,
	's3':S3TransferProtocol,
	'http':HttpTransferProtocol,
	'ftp':FileTransferProtocol
}

def get_protocol(path):
	index = path.find("://")
	if index == -1:
		return None
	
	prot = path[:index]
	
	if prot not in TransferProtocols:
		return None
	
	return TransferProtocols[prot]()
	