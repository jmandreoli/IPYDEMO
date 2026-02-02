# Creation date:        2022-01-15
# Contributors:         Jean-Marc Andreoli
# Language:             python
# Purpose:              Doc generation script
#
# Fill in the following variables and save as Makefile. Alternatively
# you can set these variables from the command line, and also
# from the environment for the first two.
#
SPHINXOPTS    ?=
SPHINXBUILD   ?=
SOURCEDIR     = .
BUILDDIR      = _build
# needed for _resource
RSCMAKE       =
#
# There should be no need to change below this line
#--------------------------------------------------------------------------------------------------
override SPHINXOPTS    = -T # local
override SPHINXBUILD   = /home/andreoli/Tools/anaconda/bin/sphinx-build # local
override RSCMAKE       = /storage/tools/anaconda/202501/bin/python -Wignore -m myutil.make # change to /home/andreoli/Tools/anaconda/bin/python when mip is OK # local
#
# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
#
.PHONY: help Makefile
#
rsc: $(addprefix _resource/mod_,odesimu.out odesimu.gif fractals.out fractals.gif polyhedra.out sudoku.out) ;
#
rsc-clean:
	@echo Removing everything under _resource ...
	@rm -rf _resource/*
#
_resource/%.out:: %.py
	@echo Generating $@ ...
	@export PYTHONPATH=$(realpath ../.pythonpath):$(PYTHONPATH); ${RSCMAKE} $< $@
#
_resource/%.gif:: _resource/%.mp4
	@echo Generating $@ ...
	@ffmpeg -loglevel panic -y -i $< $@
_resource/%.mp4:: _resource/%.out ;
#
MAKEFILE:: Makefile # local
	@echo Generating $@ ... # local
	@sed 's/^.*\# local$$//g' $< | sed '/^$$/d' > $@ # local

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
