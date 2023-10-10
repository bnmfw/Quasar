run: clean
	@python3 Quasar.py
	
setup:
	@mkdir work
	@mkdir debug/work

requirements:
	@pip install -r .piprequirements

test:
	@for module in matematica graph concorrencia dataAnalysis spiceInterface circuito letFinder circuitManager mcManager; do \
		python3 -m utils.$$module; \
	done

license:
	@cd /backup_and_restore_scripts/setup_machine; ./synopsys_start_licenses.sh

clean:
	@rm -rf __pycache__
	@rm -rf utils/__pycache__
	@rm -rf work/
	@mkdir work
	@rm -rf debug/work
	@mkdir debug/work
	@find . -name "scope.log*" -type f -delete
	@for dir in circuitos debug/test_circuits; do \
		for ext in ava.* mpp0 ic0 crash mt0* mc0* st0 user* pa0 tr0 info* hsp*; do \
			find $$dir -name "*.$$ext" -type f -delete; \
		done; \
	done

veryclean: clean
	@for dir in circuitos debug/test_circuits; do \
		for ext in *.csv MC_Context.json *_done.json *_jobs.json *.png; do \
			find $$dir -name "$$ext" -type f -delete; \
		done; \
	done
