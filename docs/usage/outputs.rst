File Outputs
==================

PXC produces several different types of files.  All of them are designed to be human readable and are stored as plain text.

Data files
-------------
Each time the user starts a sequence, PXC creates a new data file.
This file is saved in the directory ``C:/Data/<User>/<Project>/<Sample>/``, where the three parameters are defined by the user on the top of the GUI.
It is given a file name which includes the project and sample designators, as well as the date and time when the sequence started.

The file is made up of tab-delimited columns, with each one corresponding to a single measurement, although there are some subtleties described in the :doc:`../dev/instruments` section.
The first line to follow the start flag contains the headers, which include the instrument, parameter, and unit in a somewhat verbose format.
Each line corresponds to a single measurement event as defined by the sequence steps.

It is possible that a sequence would include segments where not all variables are being measured on every line.
If this is the case, the spot in that row and column will be held with a dash `-` to preserve the structure.

Metadata files
--------------------
At the beginning of each run, a metadata file is also generated.
This file includes all of the configuration details for the instrument, sequence commands, and other useful information.
These files are located within the same directory as the data files on the same sample, but in a subdirectory ``meta``.
They have the same file name except for the extension, which is also ``*.meta``.


Log files
-------------
While data files are created for every run, a log file is generated for every session: that is, whenever the program starts up.
The log files are all stored into the ``C:/Data/PXCLogs/`` directory.
During normal operation, these files record each action taken by the code and by the user.
They will also record error tracebacks to ease troubleshooting.

Each event is logged with its time, module, process name, and plain text message: for more details on how the logs are generated and formatted, check out :doc:`../dev/logging`.

Sequence files
---------------