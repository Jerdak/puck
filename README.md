Puck
=========

Puck is a semi-automatic object-relational mapping (ORM) framework for multisource data tracking.
The intent is to provide a wrapping framework for data sources from multiple locations, e.g.
html, local, ftp, sftp, Amazon, Dropbox, http.  Data are tracked by the ORM and cached locally
on first use.  

e.g.  
* puck.get("ftp://1.1.1.1/myfile.py",user="foo",pass="bar")
* puck.get("http:/foosite.come/myfile.obj")
* puck.get("s3://foobucket/myfile.py",user="foo",pass="bar")


Only the object-relational model is currently in place.  This framework intentionally bears 
a *small* resemblance to Django.  While I enjoy the power and flexibility of Django
I have **alot** of small projects that would benefit from a lighter ORM.  Eventually this
framework should become a separate module.

TODO
=====
* Finish writing basic query filtering
* Cache query's
* Write data getters for HTTP, SFTP, FTP, and S3
* Write data putters for SFTP, FTP, and S3
* Add functionality to queries: JOIN, FOREIGN KEY, ETC

License:
========

This code is available on [github] under the [BSD] license.

[github]:http://github.com/jerdak/puck
[BSD]:http://www.seethroughskin.com/blog/?page_id=2468