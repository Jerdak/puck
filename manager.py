import fields
import models
import databases
import sys
import os

def example_files():
	""" Example of building a database using local files
	"""
	#databases.database.add_model(models.FileModel,create_table=True,drop_existing=True)
	models.FileModel.create()
	for f in os.listdir('.'):
		if os.path.isfile(os.path.join('.',f)):
			path = os.path.abspath(os.path.join('.',f))
			info = os.stat(path)
			#print path
			#print info
			fm = models.FileModel()
			fm.path = path
			fm.name = f
			fm.size = info.st_size
			fm.save()
''' initializer list

# http://stackoverflow.com/questions/1389180/python-automatically-initialize-instance-variables
def initializer(fun):
    names, varargs, keywords, defaults = inspect.getargspec(fun)
    @wraps(fun)
    def wrapper(self, *args):
        for name, arg in zip(names[1:], args):
            setattr(self, name, arg)
        fun(self, *args)
    return wrapper

class process:
    @initializer
    def __init__(self, PID, PPID, cmd, FDs, reachable, user):
        pass
'''

def dump_fields(model_instance):
	""" Dump fields in model
	
		Because class 'Model' overrides the default get/set
		attribute behaviour the only way to get the true
		types of each field is to use object.__getattribute__
	"""
	isnt_attrs = object.__getattribute__(model_instance, '__dict__')
	print "fields in {0}: {1}".format(model_instance,isnt_attrs)
	
def foo_model_test():
	#TODO:  each model should be responsible for notifying the database of its creation (handled by metalclass)
	#databases.database.add_model(models.FooModel,create_table=True,drop_existing=True)
	models.FooModel.create()
	f = models.FooModel()
	f.fieldOne = 1
	f.fieldTwo = 2
	f.fieldThree = "3"
	f.save()
	print "Current id: ",f.id

	f = models.FooModel()
	f.fieldOne = 4
	f.fieldTwo = 5
	f.fieldThree = "6"
	f.save()
	
	# add a new FooModel object model
	f = models.FooModel()
	f.fieldOne = 12
	f.fieldTwo = -1
	f.fieldThree = "c"
	f.save()

	f.fieldOne = 42
	f.save()
	# fetch models resident in database 'db' (no django-like objects.all()... yet)
	fs = models.FooModel().fetch()
	print "Foo model test:"
	for f in fs:
		print " - "+str(f)
		
	databases.database.commit()

def baz_model_test():
	#databases.database.add_model(models.BazModel,create_table=True,drop_existing=True)
	# add a few dummy values manually
	#db.execute("INSERT into FooModel VALUES(NULL,1,2,\"3\")")
	#db.execute("INSERT into FooModel VALUES(NULL,4,5,\"6\")")
	models.BazModel.create()

	f = models.BazModel()
	f.lefsa = 'yum'
	f.date = "2014"
	f.save()

	f.lefsa = 'yummy'
	f.save()

	fs = models.BazModel().fetch()
	print "Baz model test:"
	for f in fs:
		print " - "+str(f)
		
	databases.database.commit()	

if __name__ == '__main__':	
	foo_model_test()
	baz_model_test()
	example_files()
	
	fs = models.FileModel().fetch()
	for f in fs:
		print str(f)
		

	
	fs[4].path = "C:\To\My\Pants.txt"
	fs[4].name = "Pants.txt"
	fs[4].size = 69
	
	fs[5].path = "D:\Foo\Bar.py"
	fs[5].size = 128
	
	fs[4].save()
	fs[5].save()
	
	fs = models.FileModel().fetch(filter='size__lt=129')
	for f in fs:
		print "filtered by size: ",str(f)

	fs = models.FileModel().fetch(filter='name__contains="%filters%"')
	for f in fs:
		print "filtered by name: ",str(f)
	databases.database.commit()