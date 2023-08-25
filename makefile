run:
	@python3 Quasar.py

requirements:
	@pip install -r .piprequirements

test:
	@for module in matematica graph concorrencia spiceInterface circuito letFinder circuitManager mcManager; do \
		python3 -m utils.$$module; \
	done

clean:
	@rm -rf __pycache__
	@rm -rf utils/__pycache__
	@find . -name "scope.log*" -type f -delete
	@for dir in circuitos debug/test_circuits; do \
		for ext in ava.* mpp0 ic0 crash mt0* mc0* st0 user* pa0 tr0 info* hsp*; do \
			find $$dir -name "*.$$ext" -type f -delete; \
		done; \
	done

veryclean: clean
	@for dir in circuitos debug/test_circuits; do \
		for ext in *.csv MC_Context.json *_done.json *_jobs.json; do \
			find $$dir -name "$$ext" -type f -delete; \
		done; \
	done