Setting up a measurement
========================


Overview
-----------
To set up a measurement in PXC, there are two main steps:

1. Select which instruments you want to use
2. Write a sequence of commands to perform the desired operations.

Both of these are actually fairly straightforward, but for completeness, here we go.


Selecting instruments
--------------------------
Click on the ``Edit Instruments`` button, and a smaller window will pop up.  The instruments which are currently connected should automatically populate, but you can hit the ``Refresh`` button to check it again as you rewire things.


The instrument address syntax is the ``N:MODEL`` where ``N`` is the GPIB address and the model name is whatever the driver specified.

To activate an instrument, just select it on the left panel, put in a unique name in the center and press the ``>>`` button to activate it.  The names can be as simple or complex as you want, but you have to insert a name, even if there's only one instrument.

Apply your changes with the button on the bottom, and those instruments should now show up on the main GUI.


Writing a sequence
-----------------------
The buttons on the right hand side are all about the sequences, and again, they are fairly self-explanatory.  Each one will open a new dialog window to help you configure the command's function.  Closing that window accepts the changes, and you can double-click on the command after creation to reopen that editing window.

You can currently choose between five different command types:

*	**Wait**: Does just that, either by waiting for a specific amount of time or by waiting for a value (such as a temperature) to stabilize.

*	**Single Measurement**: This allows you to make a one-time measurement of any number of parameters you want.

*	**Continuous Measurement**: This allows you to repeatedly measure any number of parameters--this is probably the most useful command for temperature sweeps, for instance.

*	**Change Settings**: This allows you to make a one-time alteration to any number of parameters.

*	**Loop**: A bit more complicated.  This one allows you to repeat a chunk of sequence while altering a single parameter on each iteration.  The loop actually inserts two lines into the sequence window, marking the start and end of the loop, and will repeat any commands sandwiched between them.  The program automatically indents these for you, so it's pretty easy to tell what is inside and what isn't.

.. note:: The ``timeout`` option included in several of these commands sets a maximum amount of time to run: when that time is exceeded, the command **will** exit, regardless of any other wait condition being met.  If you want it to continue indefinitely, set the timeout to zero.

Once you've established a sequence, you can save it: the output files from this are human readable, so you can keep track of what you did.  (This same information also goes into the metadata file, though, so it's always saved regardless.)

Steps can also be enabled and disabled at will, and moved up and down in order.  Steps will run from top to bottom (respecting any loops) and skipping anything that has been disabled.

Every time you press the run button, you'll get a data file and a metadata file, and they will save your data directly to the disk as it's being taken, so you can make a copy of that file and analyze it elsewhere while it runs.