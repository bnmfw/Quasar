requirements:
	@pip install -r .piprequirements

test:
	@python3 debug/full_diagnosis.py

clean:
	@rm -rf __pycache__

MYDIR = circuitos
list: $(MYDIR)/*
		for file in $^ ; do \
			echo $${file} ; \
		done
