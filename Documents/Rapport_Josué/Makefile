
all: main.pdf

figs: figures.ml
	mlpost $<
	rm -f *.mps

main.pdf: main.tex biblio.bib figs
	rubber -d main.tex

clean:
	rm -f main.aux main.blg main.bbl main.out main.log main.pdf
	rm -f *.pdf *.mps
	rm -f *.cmi *.cmo
	rm -r slidefigs

slidefigs: figs
	mkdir -p slidefigs
	for file in *.pdf ; do \
	if [ $${file} != "main.pdf" ] ; then \
        gs -q -dNOPAUSE -dBATCH -sOutputFile="slidefigs/$(basename $${file} .pdf).png" -sDEVICE=png16m -r1000 "$${file}" ; \
    fi ; \
	done
