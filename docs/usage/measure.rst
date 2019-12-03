Setting up a measurement
========================


Overview
-----------
To set up a measurement in PXC, there are two main steps:

1. Select which instruments you want to use
2. Write a sequence of commands to perform the desired operations.

Both of these are fairly straightforward, but for completeness, here we go.


Selecting instruments
--------------------------
Click on the ``Edit Instruments`` button, and a smaller window will pop up.  The instruments which are currently connected should automatically populate, but you can hit the ``Refresh`` button to check it again as you rewire things.


The instrument address syntax is the ``N:MODEL`` where ``N`` is the GPIB address and the model name is whatever the driver specified.

To activate an instrument, just select it on the left panel, put in a unique name in the center and press the ``>>`` button to activate it.  The names can be as simple or complex as you want,