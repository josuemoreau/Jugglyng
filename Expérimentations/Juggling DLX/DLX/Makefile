CC:=g++
DLX:=dlx_m
PYDLX:=dlxm

${DLX}: ${DLX}.hpp ${DLX}.cpp test_${DLX}.cpp
	${CC} -o $@ ${DLX}.cpp test_${DLX}.cpp

test: ${DLX}
	./${DLX}

${DLX}.o: ${DLX}.hpp ${DLX}.cpp
	${CC} -fPIC -c -o $@ ${DLX}.cpp

${DLX}.so: ${DLX}.o
	${CC} -shared -static-libstdc++ -o $@ $<

lib: ${DLX}.so

doctest-python: ${DLX}.so ${DLX}.hpp ${PYDLX}.py
	python -m doctest ${PYDLX}.py

test-python: ${DLX}.so ${DLX}.hpp ${PYDLX}.py doctest-python
	python test_${PYDLX}.py
