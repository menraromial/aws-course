# Figures du cours : src/*.tex -> PDF (diapositives) -> SVG inséré dans les pages
#   make          toutes les figures
#   make apercu   un PNG par figure dans build/, pour vérifier le rendu
#   make <nom>    une seule figure
SHELL  := /bin/bash
SRC    := $(wildcard src/*.tex)
NOMS   := $(patsubst src/%.tex,%,$(SRC))
SVG    := $(patsubst %,../src/figures/%.svg,$(NOMS))
PDF    := $(patsubst %,../static/figures/%.pdf,$(NOMS))
PNG    := $(patsubst %,build/%.png,$(NOMS))

all: $(SVG) $(PDF)
$(NOMS): %: ../src/figures/%.svg ../static/figures/%.pdf

lib/couleurs.tex ../src/css/figures.css: palette.tsv palette.py
	python3 palette.py

build/%.pdf: src/%.tex lib/awsfig.sty lib/couleurs.tex
	@mkdir -p build
	@cd build && TEXINPUTS=../lib:../src: lualatex -interaction=nonstopmode -halt-on-error ../src/$*.tex > $*.journal || (echo "ÉCHEC $*"; grep -m3 -A3 '^!' $*.journal; false)

../src/figures/%.svg: build/%.pdf svgpost.py palette.tsv
	@mkdir -p ../src/figures
	@pdftocairo -svg $< build/$*-brut.svg
	@python3 svgpost.py build/$*-brut.svg $@ && echo "SVG  $*"

../static/figures/%.pdf: build/%.pdf
	@mkdir -p ../static/figures
	@cp $< $@

build/%.png: build/%.pdf
	@pdftocairo -png -r 110 -singlefile $< build/$*

apercu: $(PNG)

clean:
	rm -rf build

.PHONY: all apercu clean $(NOMS)
.SECONDARY:
