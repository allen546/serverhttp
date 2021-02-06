@git commit -am "Release"
@git push origin master
@rm dist/*
@python setup.py sdist bdist_wheel
@set TWINE_USERNAME=haha1234346364
@set TWINE_PASSWORD=dl110426
@python -m twine upload dist/*
@pause