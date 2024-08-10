run: clean
	@python3 quasar.py

requirements:
	@mkdir work
	@mkdir debug/work
	@pip install -r .piprequirements

test:
	@python3 -m src.utils.matematica
	@python3 -m src.utils.arquivos
	@python3 -m src.utils.concorrencia
	@python3 -m src.spiceInterface.spiceRunner
	@python3 -m src.spiceInterface.spiceFileManager
	@python3 -m src.simconfig.faultModel
	@python3 -m src.simconfig.simulationConfig
	@python3 -m src.simconfig.transistorModel
	@python3 -m src.letSearch.letFinder
	@python3 -m src.circuit.graph
	@python3 -m src.circuit.components
	@python3 -m src.circuit.circuito
	@python3 -m src.circuit.circuitManager

license:
	@cd /backup_and_restore_scripts/setup_machine; ./synopsys_start_licenses.sh

clean:
	@find . -type d -name '__pycache__' -exec rm -r {} +
	@find . -type d -name 'work' -exec rm -r {} +
	@mkdir work
	@mkdir debug/work
	@find . -name "scope.log*" -type f -delete
	@for dir in project debug/project; do \
		for ext in ava.* mpp0 ic0 crash mt0* mc0* st0 user* pa0 tr0 info* hsp*; do \
			find $$dir -name "*.$$ext" -type f -delete; \
		done; \
	done

veryclean: clean
	@for dir in project debug/project; do \
		for ext in *.csv MC_Context.json *_done.json *_jobs.json *.png Raw_data.csv; do \
			find $$dir -name "$$ext" -type f -delete; \
		done; \
	done
