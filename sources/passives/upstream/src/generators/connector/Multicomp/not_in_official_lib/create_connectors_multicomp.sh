# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

mkdir Connectors_Multicomp.pretty

# Wire-To-Board-Steckverbinder, Straight
for i in "10" "14" "16" "20" "26" "34" "40" "50" "60" "64"
do
    i_2=$((i/2))
    if [ $i_2 -lt 10 ]
    then
        PIN_NUMBER="0${i_2}"
    else
        PIN_NUMBER=${i_2}
    fi
    
   ./connectors_multicomp_mc9a12.py $i > "Connectors_Multicomp.pretty/Multicomp_MC9A12-${i}34_2x${PIN_NUMBER}x2.54mm_Straight.kicad_mod"
done

# Wire-To-Board-Steckverbinder, Right Angle
for i in "10" "14" "16" "20" "26" "34" "40" "50" "60"
do
    i_2=$((i/2))
    if [ $i_2 -lt 10 ]
    then
        PIN_NUMBER="0${i_2}"
    else
        PIN_NUMBER=${i_2}
    fi
    
   ./connectors_multicomp_mc9a22.py $i > "Connectors_Multicomp.pretty/Multicomp_MC9A22-${i}34_2x${PIN_NUMBER}x2.54mm_Angled.kicad_mod"
done
