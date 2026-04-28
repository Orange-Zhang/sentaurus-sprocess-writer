# Minimal synthetic SProcess-style example for parser demos.
# This is not an official Synopsys example and is not a calibrated process.

AdvancedCalibration
math coord.ucs

line x location= 0.0<um> spacing= 0.02<um> tag= top
line x location= 1.0<um> spacing= 0.10<um> tag= bottom
line y location= 0.0<um> spacing= 0.05<um> tag= left
line y location= 2.0<um> spacing= 0.05<um> tag= right

region silicon xlo= top xhi= bottom ylo= left yhi= right
init silicon field= Boron concentration= 1e15<cm-3> wafer.orient= 100

mask name= ACTIVE left= 0.25<um> right= 1.75<um>
mask name= NPLUS segments= "0.35 0.75 1.25 1.65"
mask name= CONTACTS segments= "0.45 0.65 1.35 1.55"

deposit oxide thickness= 0.02<um> isotropic
photo mask= NPLUS thickness= 1.0<um>
implant Phosphorus dose= 1e15<cm-2> energy= 40<keV> tilt= 0 rotation= 0
strip photoresist

diffuse temperature= 950<C> time= 10<min>

deposit oxide thickness= 0.20<um> isotropic
etch mask= CONTACTS oxide thickness= 0.25<um> anisotropic

refinebox name= r.surface min= "-0.05 0.0" max= "0.20 2.0" \
  refine.min.edge= "0.02 0.02" refine.max.edge= "0.1 0.1" Silicon add
grid remesh

contact name= "left" box Silicon ylo= 0.45 yhi= 0.65 xlo= -0.02 xhi= 0.12
contact name= "right" box Silicon ylo= 1.35 yhi= 1.55 xlo= -0.02 xhi= 0.12
contact name= "substrate" bottom Silicon

struct tdr= minimal_oxidation_implant !gas
exit
