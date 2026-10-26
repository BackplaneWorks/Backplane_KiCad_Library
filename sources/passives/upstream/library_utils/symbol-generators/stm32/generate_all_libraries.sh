#!/bin/sh

set -e

if [ $# -lt 1 ]; then
    echo "Error: $0 requires at least one argument: CUBEMX_MCU_DB_DIR"
fi

mx_mcu_db_dir=$1
shift

# We roll L4+ into L4 since the part numbers overlap.
# We roll WBA into WB since one is a prefix of the other.
for family in $(python3 stm32_list_families.py $mx_mcu_db_dir | grep -v L4+ | grep -v WBA | grep -v WB0); do
    python3 stm32_generator.py $mx_mcu_db_dir "MCU_ST_$family.kicad_symdir" -p "$family*" --verify-datasheets --url-cache url_cache.json --skip-without-footprint $@
done

wait

