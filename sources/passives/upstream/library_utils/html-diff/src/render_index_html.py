"""

Generate an index.html page that links to a set of ".diff" sub-directories.

html_diff.py calls generate_index_html() after writing the per-library diffs,
so the whole diff can be browsed from a single page. If there is only one
sub-directory, the index.html page redirects to the first HTML file in it.
"""

import os
from pathlib import Path

css = """
    :root {
        color-scheme: light dark;
    }
    html, body {
        height: 100%;
        margin: 0;
        justify-content: center;
        align-items: center;
    }
    .button-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .library-button {
        background-color: blue;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .library-button.disabled {
        background-color: grey;
    }

    @media (prefers-color-scheme: dark) {
        html, body {
            background-color: #1e1e1e;
            color: #ddd;
        }
        .library-button {
            background-color: #80a8e8;
            color: black;
        }
        .library-button.disabled {
            background-color: #555;
            color: #999;
        }
    }
"""


def generate_index_html(directory: str | Path, prefix: str) -> str:
    """
    Generate the index HTML page for a diff superdirectory.
    The diff superdirectory shall contain sub-directories, each of which
    with suffix ".diff" (e.g. "Regulator_Switching.diff").

    For diff superdirectories with only one sub-directory, the index HTML page
    will redirect to the first HTML file in the sub-directory.

    For diff superdirectories with multiple sub-directories, the index HTML page
    will contain buttons for each sub-directory. Clicking on a button will
    redirect to the first HTML file in the sub-directory.

    Args:
        directory (str): The directory path.

    Returns:
        str: The generated index HTML page.

    Raises:
        None
    """

    sub_dirs = []

    # Find sub-directories recursively
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if d.endswith(".diff"):
                sub_dirs.append(os.path.relpath(os.path.join(root, d), directory))

    sub_dirs.sort()

    if len(sub_dirs) == 0:
        return """<html>
    <h1>No diff sub-directories found</h1>
    <p>This probably means that this change did not produce any changes to the output files.</p>
<html>
"""
    if len(sub_dirs) == 1:
        # If there is only one sub-directory
        sub_dir = sub_dirs[0]
        sub_dir_path = Path(directory) / sub_dir

        html_files = sorted(sub_dir_path.glob("*.html"))

        if html_files and len(html_files) > 0:
            url = f"{prefix}{sub_dir}/{html_files[0].name}"
            return f"""
                <html>
                    <head>
                        <meta http-equiv="refresh"content="0; URL='{url}'" />
                    </head>
                </html>
            """
        return "<h1>No diff files found</h1>"
    else:
        # If there are multiple sub-directories
        buttons_html = ""
        for sub_dir in sub_dirs:
            sub_dir_path = Path(directory) / sub_dir

            html_files = sorted(sub_dir_path.glob("*.html"))

            if html_files:
                path = f"{prefix}{sub_dir}/{html_files[0].name}"
                buttons_html += f"""
                <a class="library-button" href=\'{path}\'" target="_blank">{sub_dir}</a><br>
                """
            else:
                buttons_html += f'<a class="library-button disabled">{sub_dir} (No HTML files)</a><br>'
        return f"""
            <html>
                <head>
                    <style>{css}</style>
                </head>
                <body>
                    <div class="button-container">
                        {buttons_html}
                    </div>
                </body>
            </html>
        """
