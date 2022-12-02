# This script echoes the command line usage for script tools to files in this
# directory that can then be transcluded into markdown files using the python
# markdown extension markdown-include. The syntax is:
#
# {!path/to/file!}
#
# Note that the path is from the root directory running the mkdocs build/serve
# process, not relative to the markdown file in which the included file is 
# referenced.


echo "cl_prompt $ vr_run -h" > vr_run.txt
vr_run -h >> vr_run.txt
