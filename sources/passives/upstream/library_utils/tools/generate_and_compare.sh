#! /usr/bin/env bash

set -ex

# Default values

# Guess the directory of the repo from the script if not given
# TODO this is ugly, because it breaks when the script is moved to another directory
#      ask me how I know..
kfg_repo_dir=$(realpath "$(dirname "$0")/../..")

# This is the URL to download the baseline footprints archive
# set to the default URL for the upstream repo's main branch
# which allows users to get the latest baseline footprints faster (probably) than
# generating them themselves.
baseline_branch="main"
base_url="https://gitlab.com/api/v4/projects/21610360/jobs/artifacts/${baseline_branch}/raw/footprints.tar.xz?job=fp-generate"
skip_dl=false
base_rev=""
script_subdirs=()
open_result=false
output_dir="./output"
diff_output_dir=""

usage() {
    set +x
    echo "Usage: $(basename "$0") [-d directory] [-u base-url] [-b base-rev] [-o output-dir]"
    echo "  -r repo           kicad-footprint-generator repo (default: work it out
                              from the script location)"
    echo "  -u base-url       base URL to download a baseline footprints archive
                              (default KiCad generator repo main branch archive)"
    echo "  -U                skip downloading the baseline footprints archive if the file exists"
    echo "  -b base-rev       base revision to generate the baseline footprints.
                              Overrides the URL. (e.g. 'HEAD^' or 'main')"
    echo "  -t temp-dir       Put temporary files in this directory (default: ./output)"
    echo "  -o output-dir     output directory for diffs (default: ./output/diffs)"
    echo "  -g generator      generator directories to run the generate in (default: no subdir,
                              run in scripts, which means generate everything). Can give multiple
                              times."
    echo "  -O                open the result in a browser"
}

# Parse options
while getopts ":r:u:b:o:g:t:h:OU" opt; do
    case ${opt} in
        r )
            kfg_repo_dir=$(realpath "$OPTARG")
            ;;
        u )
            base_url=$OPTARG
            ;;
        U )
            skip_dl=true
            ;;
        b )
            base_rev=$OPTARG
            ;;
        t )
            output_dir=$OPTARG
            ;;
        o )
            diff_output_dir=$OPTARG
            ;;
        g )
            script_subdirs+=("$OPTARG")
            ;;
        O)
            open_result=true
            ;;
        h )
            usage
            exit 0
            ;;
        \? )
            echo "Invalid option: -${OPTARG}" >&2
            usage
            exit 1
            ;;
        : )
            echo "Option -${OPTARG} requires an argument." >&2
            usage
            exit 1
            ;;
    esac
done

set -x

echo "KiCad footprint generator directory: $kfg_repo_dir"
echo "Base URL: $base_url"
echo "Base revision: $base_rev"
echo "Output dir: $output_dir"

mkdir -p "${output_dir}"
base_output_dir=$(realpath "${output_dir}/base_footprints")
curr_output_dir=$(realpath "${output_dir}/generated_footprints")

# If the user didn't specify a diff output directory, default to output/diffs
if [ -z "$diff_output_dir" ]; then
    diff_output_dir="${output_dir}/diffs"
fi
diff_output_dir=$(realpath "$diff_output_dir")

# if we clone the repo, we will store it here
base_repo_dir=$(realpath "${output_dir}/base_repo")

# Function to delete a directory only if it contains only files that end in .kicad_mod
function delete_if_only_kicad_mod() {
    local dir="$1"
    if [ -d "$dir" ]; then
        # Find all files that do not end in .kicad_mod
        non_kicad_mod_files=$(find "$dir" -type f ! -name "*.kicad_mod")
        if [ -z "$non_kicad_mod_files" ]; then
            rm -rf "$dir"
            echo "Deleted directory: $dir"
        else
            echo "Directory $dir contains non-kicad_mod files, not deleting."
        fi
    else
        echo "Directory $dir does not exist."
    fi
}

# Clear footprint output directories
delete_if_only_kicad_mod "${base_output_dir}"
delete_if_only_kicad_mod "${curr_output_dir}"

# clear output directories (without nuking everything if the user passes
# a path they don't mean to, like ~)
rm -rf "${diff_output_dir}/index.html"
rm -rf "${diff_output_dir}"/*.diff

# Run the script to generate the footprints
# $1: The script directory (scripts in the repo)
# $2: The output directory
function generate_all_footprints() {
    pushd .

    src_root="$1"
    dest_root="$2"

    # Generate in the main script directory = all
    cd "$src_root/src/generators"

    if [ ${#script_subdirs[@]} -ne 0 ]; then
        # Select the generators to run with -g
        time ./generate.py --output-dir-footprints "${dest_root}" --separate-outputs -g "${script_subdirs[@]}"
    else
        time ./generate.py --output-dir-footprints "${dest_root}" --separate-outputs
    fi

    popd
}

if [ -n "$base_rev" ]; then
    # checkout the repo at the base revision
    cd "$kfg_repo_dir"

    # Get the commit in the kfg_repo_dir repo, in case it's a local branch/ref
    base_rev_commit=$(git rev-parse "$base_rev")

    # Don't re-clone the repo if it's already there
    if [ -d "${base_repo_dir}" ]; then
        cd "$base_repo_dir"
        git fetch origin
        git clean -fdx
    else
        git clone "$kfg_repo_dir" "$base_repo_dir"
        cd "$base_repo_dir"
    fi

    git reset --hard "${base_rev_commit}"

    generate_all_footprints "${base_repo_dir}" "${base_output_dir}"
else
    cd "$output_dir"

    # if the URL is set, download the file now
    baseline_file="footprints.tar.xz"

    if [ "$skip_dl" = false ] || [ ! -f "$baseline_file" ]; then
        curl -L -o "$baseline_file" "$base_url"
    fi

    tar -xf "$baseline_file"
    mv footprints "$base_output_dir"
fi

fp_file_count=$(find "$base_output_dir" -type f | wc -l)
echo "Baseline generation result: $fp_file_count footprints"

generate_all_footprints "${kfg_repo_dir}" "${curr_output_dir}"

fp_file_count=$(find "$curr_output_dir" -type f | wc -l)
echo "Current generation result: $fp_file_count footprints"

open_result_args=()
if [ "$open_result" = true ]; then
    open_result_args+=(--open-result)
fi

# Produce the HTML diff of the two directories
"${kfg_repo_dir}/library_utils/html-diff/src/html_diff.py" \
    -j0 \
    --verbose \
    --output "$diff_output_dir" \
    "${open_result_args[@]}" \
    "$base_output_dir" \
    "$curr_output_dir"
