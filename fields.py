"""
	puck - a pull client for the ages
"""
import copy
import new
import types
import sys

class Field(object):
	def __init__(self,**kwargs):
		self._db = None
		self._data = None
		self._owner = None
		self._modified = True
		self._primary_key = False

	@property
	def modified(self):
		return self._modified
	
	@property
	def primary_key(self):
		return self._primary_key
	
	# TODO:  replace get/set data methods with proper properties
	# but for now this was easier to wrangle with than dynamic property access
	def get_data(self):
		#print "getting data: ",type(self._data),self._db_repr_()
		#TODO:  Each field should override this method (virtual equivalent)
		#so that data are packed by the field prior to database entry.
		return self._db_repr_()
		
	def set_data(self,value):
		if value == self._data:
			return
		x = None

		self._modified = True
		self._parent.set_modified(True)
		self._data = value	
	
	def _db_repr_(self):
		""" Database representation
		
			This method returns the database representation of the encapsulated
			data.  The default value is string since most 'data' are PODs
		"""
		ret = 'null' if self._data == None else str(self._data)
		return ret
		
	def _db_type_(self):
		raise NotImplementedError("db_type() not implemented")
		
class IntField(Field):
	def __init__(self):
		super(IntField,self).__init__()
	@property
	def primary_key(self):
		return self._primary_key
	def __str__(self):
		return self._db_repr_()	
		
	def __unicode__(self):
		return self._db_repr_()	
		
class CharField(Field):
	def __init__(self):
		super(CharField,self).__init__()
	
	def __str__(self):
		return self._db_repr_()	
		
	def __unicode__(self):
		return self._db_repr_()	
		
	def _db_repr_(self):
		""" Database representation
		
			CharFields require additional quotation marks
		"""
		data = "" if self._data == None else self._data
		return unicode("\""+data+"\"").encode('utf-8')
		
class DoubleField(Field):
	def __init__(self):
		super(DoubleField,self).__init__()
	
	def __str__(self):
		return self._db_repr_()	
		
	def __unicode__(self):
		return self._db_repr_()	