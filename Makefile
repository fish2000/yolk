check:
	pycodestyle --ignore=E302,E305,E266,E402,E722,E501,E127,W292,W293,E201,E202,E203,W293,W504 yolk setup.py
	python setup.py --long-description | rstcheck -
	check-manifest
	./check_readme.bash
