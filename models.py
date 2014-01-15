"""
	puck - a pull client for the ages
"""
import copy
import new
import types
import sys
import databases

from fields import *
from collections import *
		
class Model(object):
	#id = IntField()
	
	class __metaclass__(type):
		__inheritors__ = defaultdict(list)

		def __new__(meta, name, bases, dct):
			klass = type.__new__(meta, name, bases, dct)
			for base in klass.mro()[1:-1]:
				meta.__inheritors__[base].append(klass)

			attrs = []
			klass.__fields__ = {}
			klass.__primary_key__ = None

			# -- Do following only for subclasses of Model, not model itself. --
			if bases[0] == object:
				return klass
			
			# cache class atrributes (only subclasses of Field)
			for k,v in klass.__dict__.items():
				if issubclass(type(v),Field):
					if v.primary_key:
						klass.__primary_key__ = k
					klass.__fields__[k] = type(v)

			# if no pkey assigned, create one manually
			if klass.__primary_key__ == None:
				klass.__fields__['id'] = IntField
				klass.__primary_key__ = 'id'
				setattr(klass,klass.__primary_key__,klass.__fields__[klass.__primary_key__](primary_key=True))
			
			return klass
	
	def __init__(self):
		self._data = None
		self._modified = False
		self._field_instances = []

		# Convert static members (subclasses of Model) to instance members of object(self)
		for k,field_type in self.__fields__.items():
			self.__dict__[k] = field_type()
			self.__dict__[k].parent = self
			self.__dict__[k].name = k
			self._field_instances.append(self.__dict__[k])

			if k == self.__primary_key__:
				self.primary_key = self.__dict__[k]			# todo: make property
				self.__dict__[k]._primary_key = True

		#self._field_instances = sorted()
	'''@property
	def primary_key(self):
		print "primary_key.getter"
		return self.__dict__[self.__primary_key__]

	@primary_key.setter
	def primary_key(self,value):
		print "primary_key.setter"
		self.__dict__[self.__primary_key__] = value
'''
	def set_modified(self,value):
		#print self," was modified"
		self._modified = value
		
	@property 
	def fields(self):
		""" Get all fields sorted by primary_key

			e.g. fields[0] will always be self.primary_key
		"""
		if self._fields == None:
			temp_fields = list(
				(field_name,field_type) 
				for field_name,field_type 
				in self.__fields__.items()
			)
			self._fields = sorted(temp_fields,key=lambda key:self.__dict__[key[0]].primary_key,reverse=True)


	def save(self,force=False):
		if not self._modified and not force:
			return
		
		# extract model.field types 
		if self._field_list == None:
			self._field_list = list(
				(field_name,field_type) 
				for field_name,field_type 
				in self.__fields__.items()
			)

		updated_fields = [(self.__primary_key__,self.primary_key)]
		for k,v in self.__fields__.items():
			if self.__dict__[k].modified and self.__dict__[k] != self.primary_key:
				updated_fields.append((k,self.__dict__[k]))

		databases.database.modify2(self.__class__.__name__,self.primary_key,updated_fields)

		return
		'''self.update_fields = {}
		for k,v in self.__fields__.items():
			if self.__dict__[k].modified:
				#print "save update: ",k,v
				self.update_fields[k] = self.__dict__[k]
		'''
		# db loads fields from this.update_fields
		databases.database.modify(self)
		
		# purge updated field cache
		self.update_fields = None
	
	@classmethod
	def create(cls):
		print "cls name: ", cls.__name__
		for k,field_type in cls.__fields__.items():
			print "create",k,field_type		
		fields = [(cls.__primary_key__,cls.__fields__[cls.__primary_key__])]

		for k,field_type in cls.__fields__.items():
			if k != cls.__primary_key__:
				fields.append((k,field_type))
		databases.database.create_table(cls.__name__,fields,drop_table=True)

	def __getattr__(self, attr):
		""" Get attribute (called when attr doesn't exist)
		"""
		# Todo:  scrap this method when it's clear instances of Model types
		# are properly being instanced and called
		print "Warning, get attr called:",attr
		return self.__dict__[attr] if attr in self.__dict__ else None
	
	def __getattribute__(self,name):
		"""	Get attribute (called no matter what for ALL gets)
		"""
		#print "get attribute:",name
		
		# prefer 'object.__getattribute__' to something like self.__dict__ ( which
		# calls self.__getattribute__ again) or risk ending up in an infinite loop.  
		stat_attrs = object.__getattribute__(self, '__fields__')
		isnt_attrs = object.__getattribute__(self, '__dict__')
		
		# check if 'name' is a static Model attribute (one added by Model metaclass)
		if name in stat_attrs and name in isnt_attrs:
			# return raw data only for now, forces user to use owning object
			# to set values. (TODO:  In the future, fields should be able to modify owner)
			return isnt_attrs[name].get_data() #directly return pointer to data stored by Model type
	
		# if not, return actual value
		return object.__getattribute__(self,name)

	def __setattr__(self, attr, value):
		""" Override set attribute
		
			Certain Model attributes are caught pre get/set to mimic
			properties.  These attrs were created dynamically 
			by the Model metaclass.
		"""
		#print "setattr: ",repr(self),attr,value
		
		# use 'object.__getattribute__' instead of self.__dict__ or risk infinite loop
		stat_attrs = object.__getattribute__(self, '__fields__')
		inst_attrs = object.__getattribute__(self, '__dict__')
		if attr in stat_attrs:
			#print "  - inst attr set"
			inst_attrs[attr].set_data(value)
			return 
	
		# default __setattr__
		inst_attrs[attr] = value
		
	def _direct_set_attr(self,attr,value):
		""" Bypass __setattr__
		"""
		inst_attrs = object.__getattribute__(self, '__dict__')
		inst_attrs[attr] = value
		
	
	def _direct_get_attr(self,name):
		""" Bypass __getattr__
		"""
		#print "Direct get: ",name,repr(object.__getattribute__(self,name))
		return object.__getattribute__(self,name)
		
class FooModel(Model):
	fieldOne = IntField()
	fieldTwo = IntField()
	fieldThree = CharField()

	def __init__(self):
		super(FooModel,self).__init__()
		
	@staticmethod
	def fetch_all():
		""" Fetch all objects of this type
		
			TODO:  make db global so we don't need to pass it in
		"""
		results = databases.database.get_objects('FooModel')
		ret = []
		for result in results:
			f = FooModel()
			for field,value in result.items():
				#print field,value
				setattr(f,field,value)
				
				#todo:  this is a shit hack to remove modified flag
				#when values are loaded from a db.  Fix.
				f._direct_get_attr(field)._modified = False
			ret.append(f)
		return ret
		
	def __str__(self):
		return "FooModel[{0}]: {1} {2} {3}".format(self.id,self.fieldOne,self.fieldTwo,self.fieldThree)	

class BazModel(Model):
	pkey = IntField(primary_key=True)
	date = IntField()
	lefsa = CharField()

	def __init__(self):
		super(BazModel,self).__init__()
		
	@staticmethod
	def fetch_all():
		""" Fetch all objects of this type
		
			TODO:  make db global so we don't need to pass it in
		"""
		results = databases.database.get_objects('BazModel')
		ret = []
		for result in results:
			f = BazModel()
			for field,value in result.items():
				#print field,value
				setattr(f,field,value)
				
				#todo:  this is a shit hack to remove modified flag
				#when values are loaded from a db.  Fix.
				f._direct_get_attr(field)._modified = False
			ret.append(f)
		return ret
		
	def __str__(self):
		return "BazModel[{0}]: {1} {2}".format(self.pkey,self.date,self.lefsa)	


class FileModel(Model):
	path = CharField()
	name = CharField()
	size = IntField()
		
	@staticmethod
	def fetch_all():
		""" Fetch all objects of this type
		
			TODO:  
			[1] make db global so we don't need to pass it in
			[2] make this a generic method of parent. (if possible)
		"""
		results = databases.database.get_objects('FileModel')
		ret = []
		for result in results:
			f = FileModel()
			for field,value in result.items():
				setattr(f,field,value)
				
				#todo:  this is a shit hack to remove modified flag
				#when values are loaded from a db.  Fix.
				f._direct_get_attr(field)._modified = False
			ret.append(f)
		return ret
	
	def called_from_db(self):
		print "File model called from db"
	
	def call_from_db(self,db):
		db.test_model(self)
	
	def __init__(self):
		super(FileModel,self).__init__()	
	
	def __str__(self):
		return "FileMode[{0}]: {1} {2} {3}".format(self.id,self.path,self.name,self.size)
#def method6():
#	return ''.join([repr(num) for num in xrange(12)])	

def get_dict_attr(obj,attr):
	""" Utility method for returning a specific class attribute, *!!including
		properties*.
	"""
	
	for obj in [obj]+obj.__class__.mro():
		if attr in obj.__dict__:
			return obj.__dict__[attr]
	raise AttributeError
	
def dump_dict_attr(obj):
	""" Utility method for dumping all attributes, *including
		properties*.
	"""
	for obj in [obj]+obj.__class__.mro():
		print obj

if __name__ == '__main__':
	f = FooModel()

	f2 = FooModel()
	f.fieldOne = 12
	f.fieldTwo = -1
	f.fieldThree = 'c'

	f2.fieldOne = 42
	f2.fieldTwo = 99
	f2.fieldThree = 'a'

	print "fieldOne: ",f.fieldOne
	print "fieldTwo data: ",f.fieldTwo
	print "fieldThree data: ",f.fieldThree
	print "f modified:", f._modified

	f._modified = False
	print "f modified (should be false):", f._modified
	f.fieldOne = 12
	print "f modified (should be false):", f._modified
	f.fieldOne = 13
	print "f modified (should be true):", f._modified
	f.save()

	print "fieldOne2: ",f2.fieldOne
	print "fieldTwo data2: ",f2.fieldTwo
	print "fieldThree data2: ",f2.fieldThree



#print "FieldOne2: ",f2.fieldOne
#print Model.__inheritors__
#print dir(f)

#for k,v in FooModel.__dict__.items():
	#if type(k) == 'IntField':
	#print issubclass(type(v),Model)#type(v)