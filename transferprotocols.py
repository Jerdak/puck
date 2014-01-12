import sys
import os
import shutil



class TransferProtocol(object):
	def __init__(self):
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
	pass
	
class LocalFileTransferProtocol(TransferProtocol):
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
		os.remove(remote_file_name)	

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
	