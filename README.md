A code sample I did for a job interview. Represents a store and a cart using a
local file as a database. Realistically, a cute example of creating a user 
friendly CLI for interacting with, e.g., configuration files.

## Installation

I recommend using virtualenv for the CLI

```pip install virtualenv```

Create a virtual env 

```virtualenv venv```

And activate it

```. venv/bin/activate```

Install the CLI (and dependencies) in the virtualenv

```pip install .```

This will make the "cart" and "products" commands available from the command 
line. See additional documentation contained in the application and the 
example script for typical usage.

```products --help```

```cart --help```

Tested on Python 3.5.2

pip freeze output:

click==6.7
grocery==0.1
ilock==1.0.1
portalocker==1.2.1

