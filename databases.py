import sqlite3 as lite
import fields
import sys
import os
import filters

'''
	TODO
		[1] - Decide whether to rethrow database errors or to return FALSE or NONE
		[2] - Add handlers for MySQL and may PostGRE or MongoDB
		[3] - Move methods in subclasses up to parent where appropriate.  'class Database'
		should be an interface.
		[4] - Optimize commits (leverage transcations and bulk updates)
		[5] - Replace optional args with kwarg parse
'''
class Database(object):
	
	def __init__(self):
		self._db = None
		self._cursor = None
		self._connection = None
	
	def build_field_types(self):
		raise NotImplementedError("build_field_types() not implemented")
		
	def connected(self):
		raise NotImplementedError("connected() not implemented")
	def commit(self):
		raise NotImplementedError("commit() not implemented")
	def connect(self,db):
		raise NotImplementedError("connect() not implemented")	
	def disconnect(self):
		raise NotImplementedError("disconnect() not implemented")	
	def execute(self,statement):
		raise NotImplementedError("execute() not implemented")
	def fetchone(self):
		raise NotImplementedError("fetchone() not implemented")	
	def fetchall(self):
		raise NotImplementedError("fetchall() not implemented")
	def create_models_table(self,table_name,models):
		raise NotImplementedError("create_models_table() not implemented")
		
class SqliteDatabase(Database):
	def __init__(self):
		super(SqliteDatabase,self).__init__()
		
		self._models = {}
		self._model_fields = {}
		self.build_field_types()
	
	def __del__(self):
		self.disconnect()
		
	def build_field_types(self):
		self._field_types = {
			fields.IntField : "integer",
			fields.CharField : "text",
			fields.DoubleField : "real",
		}
		
	def connected(self):
		return (self._cursor != None and self._connection != None)
		
	def connect(self,db_name,force_creation=False):
		""" Make a single database connection
		"""
		if self.connected():
			print "[Warning] - Already connected to db {0}".format(db_name)
			self.disconnect()
		
		if not force_creation:
			try:
				with open(db_name):
					pass
			except IOError:
				print "[Warning] - Db {0} does not exist".format(db_name)
				return False
		
		# sqlite3.Row not supported in this verison of sqlite3, using custom dict factory
		def dict_factory(cursor, row):
			d = {}
			for idx, col in enumerate(cursor.description):
				d[col[0]] = row[idx]
			return d	
			
		try:
			self._db_name = db_name
			self._connection = lite.connect(self._db_name)
			self._connection.row_factory = dict_factory
			self._cursor = self._connection.cursor()
		except lite.Error, e:
			print "Sqlite3 Error %s:" % e.args[0]
			return False
		return True
	
	def commit(self):
		"""	Commit all recent changes
		"""
		if not self._connection == None:
			self._connection.commit()
			
	def disconnect(self):
		""" Disconnect from current connection
		
			TODO:  All commits are handled here on disconnect which is
			probably poor design.  Revamp and consider using block transactions
			(http://stackoverflow.com/questions/5055314/combine-inserts-into-one-transaction-python-sqlite3)
			to ease the latency
		"""
		if not self._connection == None:
			self._connection.commit()
			self._connection.close()
			self._connection = None
			self._cursor = None
			self._db_name = None		
		
	def execute(self,statement):
		"""	Execute a single statement
		"""
		if not self.connected():
			raise Exception('database not connected')

		self._cursor.execute(statement)	
	
	def fetchone(self):
		"""	Fetch one result from last execute(statement)
		"""
		if not self.connected():
			raise Exception('database not connected')
		try:
			result = self._cursor.fetchone()
			return result
		except lite.Error, e:
			print "Sqlite3 Error %s:" % e.args[0]
			return None
		
	def fetchall(self):
		"""	Fetch all results from last execute(statement)
		"""
		if not self.connected():
			raise Exception('database not connected')
		try:
			results = self._cursor.fetchall()
			return results
		except lite.Error, e:
			print "Sqlite3 Error %s:" % e.args[0]
			return None
	
	def get_objects(self,table_name,**kwargs):
		"""	Get all objects/rows from table
		
			Args
				table_name:  String.  Name of table(model)
				filter: String.  Type of filter to use on results

			Notes:
				Queries use ad-hoc filtering so it's expected that results aren't cached (TODO:  But it might be worthwhile to do so)
		"""
		
		if 'filter' in kwargs:
			filter = filters.get_filter(kwargs['filter'])
			statement = "SELECT * from {0} WHERE {1} {2} {3}".format(table_name,filter[0],filter[1],filter[2])
		else:
			statement = "SELECT * from {0}".format(table_name)

		print statement
		self.execute(statement)
		results = self.fetchall()
		
		return results
		
	def get_next_id(self,table,pkey):
		""" Get next valid id from autoincrementing id field

		    Pretty much assumes the id column is INTEGER
		"""
		max_pkey = "max({0})".format(pkey)
		statement = "SELECT {0} from {1}".format(max_pkey,table)
		self.execute(statement)
		result = self.fetchone()
		return 0 if max_pkey not in result else result[max_pkey] 
		
	def modify(self,table_name,pkey,fields):
		""" Modify/Insert a row for `table_name`

			Args:
				pkey - Any Field Type.  Primary key for table_name
				fields - Any Field [] types.  List of field tuples (name,value) to change

			Todo:
				[1] - Split function in to Insert and Update. 
				[2] - Handle edge case when Fields = None
				[3] - Dev. method to cache inserts to do a bulk commit later. (maybe add flush method?)
		"""
		for f in fields:
			print "Updating field: ",f

		# todo:  fix this expensive hack.  Right now it's important for the pkey to be
		#        the first element since it's necessary for proper  column order.
		#        pkey should be treated special depending on whether we're inserting or updating
		fields = [(pkey.name,pkey)] + fields
		# todo: move insertion/update logic to separate functions or use 
		# 'insert or replace': http://stackoverflow.com/questions/3634984/insert-if-not-exists-else-update
		if str(pkey)  == 'null':
			field_string = ','.join([str(value) for name,value in fields if value is not None])	
			statement = "INSERT INTO {0} VALUES ({1})".format(table_name,field_string,pkey)
			print statement
			self.execute(statement)
			
			# make sure insertion sends back the updated id
			# TODO:
			#  [1] - Fix broken single responsiblity principle.  Database should not have
			#  to update the primary key like it does here but because of __setattr__ being
			#  overridden in `model` there isn't a mechanism currently to test if references
			#  to fields are fields themselves.  SO model.primary_key = 1 makes model.primary_key
			#  and int instead of passing that to the IntField's data member
			pkey.set_data(self.get_next_id(table_name,pkey.name))
			pkey.modified = False
			print "New primary key: ",pkey,repr(pkey)
		else:
			field_string = ','.join(["{0}={1}".format(name,str(value)) for name,value in fields if value is not None])	
			statement = "UPDATE {0} SET {1} WHERE {2} = {3}".format(table_name,field_string,pkey.name,pkey)
			print statement
			self.execute(statement)
		
		
	def create_table(self,table_name,fields,**kwargs):
		""" Create a new table

			Args
				table_name - String.  Table name.
				fields - List.  List of (field_name,field_type) tuples.
				drop_table - bool.  If true, drop table if it exists
		

		"""

		if table_name == None:
			print "[Warning] - Model <{0}> not is not valid.".format(table_name)
			return

		field_string = ','.join(["{0} {1}".format(name,self._field_types[type]) for name,type in fields])
		if 'drop_table' in kwargs and kwargs['drop_table']:
			statement = "DROP TABLE IF EXISTS {0}".format(table_name)
			print statement
			self.execute(statement)

		# replace primary key in field string "<pkey_name> <field_type>" w/ "<pkey_name> <field_type> PRIMARY KEY"
		pkey_name = fields[0][0]
		pkey_type = self._field_types[fields[0][1]]
		field_string = str.replace(field_string,"{0} {1}".format(pkey_name,pkey_type), "{0} {1} PRIMARY KEY".format(pkey_name,pkey_type))

		statement = "CREATE TABLE {0} ({1})".format(table_name,field_string)
		print statement
		self.execute(statement)

database = SqliteDatabase()
database.connect('asd.db',True)

if __name__ == '__main__':		
	db = SqliteDatabase()
	db.connect('asd.db',True)
	db.add_model("dummy_model",{"field1":fields.IntField,"field2":fields.DoubleField,"field3":fields.CharField})
	db.create_tables_from_models(drop_existing=True)
