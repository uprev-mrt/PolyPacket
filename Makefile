
include .env 

$(eval export $(shell sed -ne 's/ *#.*$$//; /./ s/=.*$$// p' .env))


.PHONY: deploy version test 

version: 
	mrt-version .env -p +1

deploy:
	sed -E -i 's/version=.*?,/version="${VERSION_STRING}",/g' setup.py
	rm -rf dist/* 
	python3 setup.py sdist 
	twine upload dist/*