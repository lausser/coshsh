
clean:
	find . -name \*.pyc -exec rm {} \;

pack:
	tar --exclude .git -zcvf coshsh.tgz .
