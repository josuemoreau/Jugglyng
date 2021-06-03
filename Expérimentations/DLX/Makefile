CC:=g++
DLX:=dlx-m

${DLX}: ${DLX}.hpp ${DLX}.cpp test-${DLX}.cpp
	${CC} -o $@ ${DLX}.cpp test-${DLX}.cpp

test: ${DLX}
	./${DLX}

${DLX}.o: ${DLX}.hpp ${DLX}.cpp
	${CC} -fPIC -c -o $@ ${DLX}.cpp

${DLX}.so: ${DLX}.o
	${CC} -shared -static-libstdc++ -o $@ $<

lib: ${DLX}.so

test-python: ${DLX}.so ${DLX}.hpp ${DLX}.py
	python ${DLX}.py
