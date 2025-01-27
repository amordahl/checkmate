# Installation

First, create a virtual environment for ECSTATIC. From the ECSTATIC directory, type

`python -m venv .venv`

*where 'python' points to a python 3.10 or higher installation.*
We recommend using  [PyEnv](https://github.com/pyenv/pyenv) to manage
multiple Python versions on a single system.

Running this command will create a new folder, `.venv`, in your ECSTATIC directory. We next have to activate the virtual environment:

`source ./.venv/bin/activate`

You should see your shell prompt preceded with (.venv), which indicates that you have activated the virtual environment.

In order to install ECSTATIC's dependencies, run

`python -m pip install -r requirements.txt`

This will install all of the Python dependencies required. Then, in order to install
the application, run

`python -m pip install -e .`

We require the `-e .` to build in-place. Currently, omitting this option will cause the Dockerfile resolution to fail when we try to build tool-specific images.

This installation will put three executables in your virtual environment's `/bin/` folder (as long as you have the virtual environment enabled, this directory is on your PATH, so the commands will be accessible): `dispatcher`, `tester`, and `deltadebugger`.
`dispatcher` is the command you run from your host, while `tester` is the command you run from inside the Docker container (under normal usage, a user
will never invoke `tester` themselves, but it can be useful for debugging to skip
container creation.)

Simply run `dispatcher --help` from anywhere in order to see the helpdoc on how to
invoke ECSTATIC. Specific instructions on how to replicate the experiments from our paper and how to extend the tool with new benchmarks/interfaces are available in README.md.
