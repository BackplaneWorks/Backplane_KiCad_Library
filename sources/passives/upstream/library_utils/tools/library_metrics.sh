#! /usr/bin/env bash

set -ex

# This script is used to generate simple GitLab CI metrics for a repo.

repo="$1"
metrics_file="$2"

fp_count=$(find "$repo" -type f -name "*.kicad_mod" | wc -l)
fp_lib_count=$(find "$repo" -type d -name "*.pretty" | wc -l)

echo "generated_fp_count $fp_count" >> "${metrics_file}"
echo "generated_lib_count $fp_lib_count" >> "${metrics_file}"

# Print the metrics file to the console (so it shows in the CI logs)
cat "${metrics_file}"