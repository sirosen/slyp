import datetime
import importlib.metadata

project = "slyp"
copyright = f"2023-{datetime.datetime.today().strftime('%Y')}, Stephen Rosen"
author = "Stephen Rosen"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version("slyp")

extensions = ["sphinx_issues"]
issues_github_path = "sirosen/slyp"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build"]

# HTML theme options
html_theme = "furo"
pygments_style = "friendly"
pygments_dark_style = "monokai"  # this is a furo-specific option
html_theme_options = {
    "source_repository": "https://github.com/sirosen/slyp/",
    "source_branch": "main",
    "source_directory": "docs/",
}
