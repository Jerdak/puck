import sqlite3 as lite
import fields
import sys
import os

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
		print "__del__"
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
			print "Committing"
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
	
	def get_objects(self,table_name):
		"""	Get all objects/rows from table
		"""
		statement = "SELECT * from {0}".format(table_name)
		self.execute(statement)
		results = self.fetchall()
		
		return results
		
	def get_next_id(self,table):
		""" Get next valid id from autoincrementing id field
		"""
		statement = "SELECT max(id) from {0}".format(table)
		self.execute(statement)
		result = self.fetchone()
		if 'max(id)' not in result:
			result = 0
		else:
			result = result['max(id)']
		return result
		
	def modify(self,model):
		""" Modify existing row or create if row doesn't exist
		
			TODO:
				[1] - Decide whether or not to autocreate missing files
				[2] - Decide how to handle someone manually setting 'id' in model
		"""
		table = model.__class__.__name__
		pkey = model.primary_key
		#test = model.primary_key
		print "pkey:",repr(pkey)
		fields = model.update_fields

		# todo: move insertion/update logic to separate functions or use 
		# 'insert or replace': http://stackoverflow.com/questions/3634984/insert-if-not-exists-else-update
		if pkey  == 'null':
			field_string = ','.join([str(value) for name,value in fields.items() if value is not None])	
			statement = "INSERT INTO {0} VALUES ({1})".format(table,field_string,pkey)
			self.execute(statement)
			
			# make sure insertion sends back the updated id
			model.id = self.get_next_id(table)
		else:
			field_string = ','.join(["{0}={1}".format(name,str(value)) for name,value in fields.items() if value is not None])	
			statement = "UPDATE {0} SET {1} WHERE Id = {2}".format(table,field_string,pkey)
			self.execute(statement)
		print statement
		
		
	def add_model(self,model_type,**kwargs):
		"""	Add ghost model to database
			
			Note:  Models added to the database don't immediately generate
			a table, `create_tables_from_models` must be called for that to happen
			
			Input
				model_type - string based name of the model
				fields - dictionary of fields and fieldtype.  ex: {"fieldOne":fields.IntField,"fieldTwo":fields.CharField}
		"""
		model_name = model_type.__name__
		
		self._models[model_name] = model_type

		# extract model.field types 
		self._model_fields[model_name] = dict(
			(field_name,field_type) 
			for field_name,field_type 
			in model_type.__fields__.items()
		)
		
		if 'create_table' in kwargs and kwargs['create_table']:
			self.create_table_from_model(model_name,**kwargs)
			
	def create_table_from_model(self,model_name,**kwargs):
		"""	Create new tables for *all* ghost models stored in cache
		
			Input
				drop_existing - Drop model table if it exists
		"""
		
		if model_name == None or model_name not in self._model_fields:
			print "[Warning] - Model <{0}> not is not valid.  (Either None or not added with add_model())".format(model_name)
			return
			
		#fields = self._model_fields[model_name]
		fields = dict(
			(field_name,field_type) 
			for field_name,field_type 
			in self._models[model_name].__fields__.items()
		)

		#test = sorted(fields,key=lambda key:key.primary_key,reverse=True)
		#print "test:",self._models[model_name].primary_key
		#for x in fields:
		#	print "x:",x,fields[x],fields[x].primary_key
		field_string = ','.join(["{0} {1}".format(name,self._field_types[type]) for name,type in fields.items()])
		
		if 'drop_existing' in kwargs and kwargs['drop_existing']:
			statement = "DROP TABLE IF EXISTS {0}".format(model_name)
			print statement
			self.execute(statement)
		
		field_string = str.replace(field_string,"id integer", "id integer PRIMARY KEY")
		statement = "CREATE TABLE {0} ({1})".format(model_name,field_string)
		print statement
		self.execute(statement)
			
	def test_model(self,model):
		model.called_from_db()
		
	def create_tables_from_models(self,**kwargs):
		"""	Create new tables for *all* ghost models stored in cache
		"""
		for model_name in self._model_fields.keys():
			self.create_table_from_model(model_name,**kwargs)

		
if __name__ == '__main__':		
	db = SqliteDatabase()
	db.connect('asd.db',True)
	db.add_model("dummy_model",{"field1":fields.IntField,"field2":fields.DoubleField,"field3":fields.CharField})
	db.create_tables_from_models(drop_existing=True)
