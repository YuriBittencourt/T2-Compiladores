.PHONY: run

run:
	@echo "Instalando Dependências..."
	pip3 install --user ply
	pip3 install --user pprint

	python3 semantic_syntatic_analyzer.py ${FILE}
