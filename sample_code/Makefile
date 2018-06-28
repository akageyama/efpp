#
# Makefile for efpp sample code
#
# Akira Kageyama,
#       Kobe University, Japan
#       kage@port.kobe-u.ac.jp
#       2018.06.28
#

.SUFFIXES:

e03list := $(shell ls *.e03)   # e.g., example.e03
filebase := $(basename $(notdir $(e03list))) # => example
f90list := $(addsuffix .F90, $(filebase)) # => example.F90
modlist := $(addsuffix .mod, $(filebase)) # => example.mod
objlist := $(addsuffix .o, $(filebase)) # => example.o

.SECONDARY: $(f90list)  # to avoid deleting F90 files.
       # .SECONDARY: obj/%.F90 does not work (GNU Make 3.81).


.PHONY: clean

FC = gfortran


%.F90: %.e03
	../efpp.py $< > $@

%.o: %.F90
	$(FC) $(FFLAGS) -o $@ -c $<

main.o: constants.o namelist.o


clean:
	rm -rf *.o *.lst *.F90 *.mod

