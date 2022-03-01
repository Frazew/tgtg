image:
	docker build -f Dockerfile -t tgtg-scanner:latest .

install:
	pip install -r requirements.dev.txt

start:
	python -m tgtg_scanner

bash:
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.dev.yml run --rm bash

executable:
	pyinstaller app.spec

test:
	python -m unittest discover -v

clean:
	docker-compose -f docker-compose.dev.yml down --remove-orphans

package:
	pip install -U build twine
	python -m build
	python -m twine upload dist/*