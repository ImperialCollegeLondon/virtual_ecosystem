---
jupyter:
  jupytext:
    cell_metadata_filter: all,-trusted
    main_language: python
    notebook_metadata_filter: settings,mystnb,language_info,execution
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
---

# Debugging the Virtual Ecosystem

This guide will walk you through the process of debugging the Virtual Ecosystem.

```{important}

Debugging the model requires the development tools and VSCode, so you will need to
install the project using `poetry` before running debugging.

```

## Using the `pytest` system

By far the easiest way of debugging the model is to use the `pytest` framework and
the existing suite of unit tests. If there is unusual behaviour in part of the model
then see if you can identify a test that runs that part of the model. You can then use
debugging mode on the test to run through it and watch what happens.

This approach is easier because it allows you to dive straight into the specific bit of
the code where you think there are issues. You don't have to set the full model running
and wait for it to get to the bit you want to check. However, it does only check the
code with the fixed set of inputs used to run the unit test. You can of course add a new
test that uses new inputs that you think are relevant to the issue.

To run a test in debug mode, open the test file in VSCode. You should see a green arrow
icon in the left margin of the editor at the start of the test. If you right click on
this arrow, one of the options will be "Debug Test". Some tests are parameterized - they
run multiple different times with different inputs - in which case you can choose which
version of the test to debug.

### Setting breakpoints

Before running a test in debugging mode, you will need to set breakpoints in either the
test function or the model code: the process works by running the code until it gets to
a breakpoint. If you do not set any breakpoints, the debugger will just run the test
through without interruption!

You can set these in the codebase by opening a Python file (either a test or the main
model code) and clicking in the left margin of the code editor window (to the left of
the line numbers). A simple click sets the breakpoint but a right click brings up a
bigger range of breakpoint options. Some gotchas:

* Do not put a breakpoint on a comment.
* Do not put a breakpoint where a function, method or class is defined (`def` or
    `class`). This makes the code pause when that object is _imported_ and not it is
    executed.
* So select a line of code _inside_ of a function, method or class.

The code should now halt at your breakpoint and you can use a range of tools to explore
the code behaviour.

### Stepping through the code

You should now see a small pane in the edit window showing play, pause, stop and other
icons. These allow you to control the continuing execution of the code:

* Continue: starts the code running to the next breakpoint or until you use the same
  button to pause the code again.
* Step over: execute the line and move to the next line of code.
* Step into: execute the line but **step into** any function called in the line. A high
  level piece of code may well call a function, that calls a function and so on down. If
  you use the step over button, then all of those functions are run and the code goes to
  the next line. If you choose step into, then the debugger moves _into_ the called
  function and steps through that code, allowing you to follow the code down into the
  lower level functions.

  It's often easier to set a breakpoint at the lower level and let the code get there by
  itself!
* Step out: when you have stepped into a function, this button resumes normal code
  running until the function ends and then pauses again at the point in the code that
  called the function.
* Stop: Abandon the debugging run.

### The Run and Debug pane

When you are debugging, the Run and Debug pane should appear on the left of the VSCode
window. This provides lost of panels with information for exploring the code state:

* The "Call Stack" panel shows the position of the line being debugged within the stack
  of calls within the model. The call stack records which function has been called by
  which function all the way up to the initial start of the code. The position on this
  stack is what the "step into" and "step out" buttons control in debugging: as you
  step into functions, you move deeper into the stack and stepping out moves back out to
  the calling function on the stack.

* The "Variables" panel shows all of the variables that are defined within the current
  stack environment (or frame). You can use the variables panel to explore the data.

* The "Breakpoints" panel shows all of the breakpoints currently set in your project by
  file and line number.

### The Debug Console

The console panel, usually at the bottom of the VSCode window, has a Debug Console pane.
This can be used to run snippets of code within the current stack environment. You can
use this to tweak data within the code or try experiments - none of this changes the
actual code in any way but it can be useful for exploring what the model is doing at any
point.

## Debugging an model scenario

If you are experiencing model issues with a particular set of inputs for a model
scenario, and cannot easily replicate the problem using tests or simpler code, then it
may be necessary to debug an entire model run. This is not ideal - it is much slower to
debug a big complex model run than a specific subsection - but it is sometimes needed to
identify the point at which a bug arises.

The workflow to run a test on a scenario is:

1. Make a `testing` directory in the repo root and copy the scenario folder into that.
1. Change directory to that scenario and create a python file `ve_run_scenario.py`
1. In that file include:

    ```python
    from virtual_ecosystem.entry_points import ve_run_cli

    ve_run_cli(["config", "--out", "out", "--logfile", "logfile.log"])
    ```

    This is basically _exactly_ the same as running the shell command
    `ve_run config --out out --logfile logfile.log` but we can set it running within the
    python debugger more easily.

1. In the VSCode "Run and Debug" panel, click on the dropdown at the top and choose "Add
   Configuration". This will open the `launch.json` file and you need to add the
   following within the `configurations` section:

   ```json
           {
            "name": "Python: Current File in local directory",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "cwd": "${fileDirname}",
            "purpose": [
                "debug-in-terminal"
            ]
        },
    ```

    This configuration is needed to run that `ve_run_scenario.py` file from its actual
    location in `testing/scenario_folder` rather than from the project root directory.

1. As with debugging through `pytest` above, you now need to set some breakpoints to
   catch the code execution at the point you want to explore. With running a scenario,
   there is no unit test code to break into - you need to set breakpoints within the
   model code itself.

1. Now to set the debug job running:
    * Make sure the `ve_run_scenario.py` is open and is selected as the active file in
      the VSCode editor window (there should be a blue line above the file name tab).
    * Go to the Run and Debug panel on the left of VSCode.
    * Make sure you have the  "Python: Current File in local directory" configuration
      selected in the drop down.
    * Press the Run button next to the configuration selector.

    ```{warning}
    There is also a debug button that shows up within the editor panel for the Python
    file. This does not use the launch configurations - do not use this and make sure
    you do use the option in the Run and Debug pane!
    ```

1. As with debugging a test, the code will pause when it hits a breakpoint. You will
   have exactly the same options for exploring the model and data as described in the
   `pytest` debugging section above.
