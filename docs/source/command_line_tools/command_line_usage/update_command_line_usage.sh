#!/usr/bin/env bash
# This script echoes the command line usage for script tools to files in this directory
# that can then be transcluded into markdown files using MyST's built include
# capability. The syntax is:
#
# ```{include} command_line_usage/vr_run.txt
# ```
#
# Note that the path is from the root directory running the mkdocs build/serve
# process, not relative to the markdown file in which the included file is 
# referenced.


echo "\`\`\`" > vr_run.txt
echo "cl_prompt $ vr_run -h" >> vr_run.txt
vr_run -h >> vr_run.txt
echo "\`\`\`" >> vr_run.txt