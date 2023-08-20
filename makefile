requirements:
	@pip install -r .piprequirements

test:
	@python3 debug/full_diagnosis.py

clean:
	@rm -rf __pycache__
	@rm -rf utils/__pycache__
	@find . -name "scope.log*" -type f -delete 
#I DONT KNOW HOT TO MAKE FOR LOOPS T-T
	@find circuitos -name "*.ava.*" -type f -delete
	@find circuitos -name "*.mpp0" -type f -delete
	@find circuitos -name "*.ic0" -type f -delete
	@find circuitos -name "*.crash" -type f -delete
	@find circuitos -name "*.mt0*" -type f -delete
	@find circuitos -name "*.mc0*" -type f -delete
	@find circuitos -name "*.st0" -type f -delete
	@find circuitos -name "*.user*" -type f -delete
	@find circuitos -name "*.pa0" -type f -delete
	@find circuitos -name "*.tr0" -type f -delete
	@find circuitos -name "*.info*" -type f -delete

	@find debug/test_circuits -name "*.ava.*" -type f -delete
	@find debug/test_circuits -name "*.mpp0" -type f -delete
	@find debug/test_circuits -name "*.ic0" -type f -delete
	@find debug/test_circuits -name "*.crash" -type f -delete
	@find debug/test_circuits -name "*.mt0*" -type f -delete
	@find debug/test_circuits -name "*.mc0*" -type f -delete
	@find debug/test_circuits -name "*.st0" -type f -delete
	@find debug/test_circuits -name "*.user*" -type f -delete
	@find debug/test_circuits -name "*.pa0" -type f -delete
	@find debug/test_circuits -name "*.tr0" -type f -delete
	@find debug/test_circuits -name "*.info*" -type f -delete