all:
	make common_layer

common_layer:
	mkdir python
	cp -a ./common python
	pip install -U aws_lambda_powertools --target "python" >/dev/null
	pip install -U pydantic --target "python" >/dev/null
	pip install -U slack_sdk --target "python" >/dev/null
	zip -r common.zip python >/dev/null
	rm -r python
