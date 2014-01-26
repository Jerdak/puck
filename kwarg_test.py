
def test2(**kwargs):
	test3(**kwargs)
	
def test3(**kwargs):
	print "kwargs: ",kwargs
	
def test(a=12,b=32,*args,**kwargs):
	print "a: ",a
	print "b: ",b
	print "args: ",args
	print "kwargs: ",kwargs
	print "---------------"

def test4(a,b=None):
	print "a: ",a
	print "b: ",b


	#,test=12,1,2,3,4
test(a=34,b=42)
test(b=42,a=34)
test(b=42,a=34)
test(b="jeremy",c="12",a="42")
test(1,2,3,4,5,6,d=1,e=2)

test2(a=1,b=2,c=3)

#test4(1,a=12) #error, results in 'got multiple values for keywrod argument 'a''
test4(12,1)