:tocdepth: 2

Writing instrument drivers
=============================

Overview
------------
For each new type of instrument, you will need to make a new file (a python "module") to do the following things:

* Make a new subclass which inherits the basic functionality of the embryonic ``instruments.InstClass.Instrument`` class, but which stores model-specific data
* Build up the list of commands the code can use to interface with this instrument by generating ``Parameter`` instances.  This basically amounts to copying the GPIB command tables from the manual.
* If a particular action requires more than one command to be sent, or if the output should be parsed in a particular way, you can also set up macro functions within this new class.

Once you've set this up, most of which will be copied from the manual and other existing instruments, the rest of the code should be able to handle the new instrument.


Creating your instrument file
--------------------------------
Go to the ``PXC/code/instruments/`` directory and make a copy of one of the existing instrument files, excluding ``Parameter.py`` and ``InstClass.py``.  Rename the file, and open it in a Python editor.

You'll see a ``class <instname>(InstClass.Instrument):`` command near the top.  Replace the instname with your own unique identifier.

Beneath that, you'll want to set the subclass attribute ``idnString`` to a unique chunk of what the instrument returns when queried over GPIB with the standard ``*IDN?`` command.  (Connect to the instrument with NIMAX or some other terminal and query that command by itself to see what this is.)

**Do not** include the serial number information, as that usually comes along for most modern instruments.  Unless, of course, you have a specific reason for treating different units with the same model number differently, such as dedicated temperature controllers with custom thermometers or something.

.. note::
	
	A few instruments, especially older ones (old SR analog lockins for example) don't respond well to the standard `*IDN?` command.
	In order to take care of these instruments, I have **reserved GPIB addresses 20-28** to handle special cases.
	
	
	This is not intended for instruments which simply spit back some sort of syntax error notifier, but for those which **actually lock up** when they receive that command.  In most other cases, even if the `*IDN?` command isn't accepted, the error message will likely be unique enough to assign the address to an instrument type.
	
	
	If you need a different command other than ``*IDN?``, determine what that new command is.  In that case, I'd recommend setting a fixed address >20 for this instrument, and then hard-coding the command into the ``Apparatus.findInstruments()`` function.  You do still want to set the expected response to the ``self.idnString`` class variable in your new class.



If necessary, you can also set the inherited attribute ``self.writeDelay`` to a nonzero value.  This parameter is useful for slowing down queries slightly to allow the instrument enough time to process the request.  This number is in seconds.  if it is too short, you will likely get errors from your instrument, and if it's too long you're just wasting time.  The SRS830 lockin uses 0.01 s, for instance, whereas a few other instruments need more like 0.1.  Play around.

Defining the parameters
----------------------------
The options which will be presented on the GUI for writing or reading are all captured within the parameter list, ``self.params``.  This is a list of ``instruments.Parameter.Param`` objects.  One ``Param`` produces one option in the GUI.  You will basically translate the GPIB communication table from the instrument manual into this list.  This list is created within the subclass constructor ``__init__.py``

A single parameter object can cover a wide variety of cases.
For instance, a given command could return a discrete value, a floating-point measurement, or nothing at all.
It also may not be a parameter which is writeable (like the SNAP function on a lockin), or it may not be something one can query (like the AutoGain function on a lockin).
all of these cases are distinguished by the arguments to the ``Param`` constructor.

The relevant options are described below.

Options for parameters
```````````````````````````
.. note :: We first assume that the command we're implementing is a single line.  If that's not the case, check out the `Writing macro functions`_ section below.



:name: The first argument must be a string describing the name of the parameter.  This is what will be presented to the user.


:w: If the command describes something which can be **w**\ritten, such as when one sets a frequency or other configuration values, place here a string of the text you want sent to the instrument.  If you don't specify the ``w``, the code assumes that it is not writeable and no longer presents this as an option where writing would occur.  When writing to an instrument, usually an argument is passed along to the instrument: the standard syntax is to append a space, then the value of the argument as defined in the GUI.  If your instrument needs something else, you'll probably need a macro.


:q: Similar to ``w``, set this argument to a string which should be sent to the instrument when you want to **q**\uery a particular variable.  If unspecified, code will not show this parameter as an option in some places.  A single parameter *can* have both ``q`` and ``w`` values if desired, there's no conflict.


:t: This argument specifies the **t**\ype of the command.  This tells the ``Param`` what kind of data to expect, as well as which of the other arguments are required or ignored.  Options for ``t`` are: 

==========  ==========  ============================  =====================================================
``t``	    name        description                   examples
==========  ==========  ============================  =====================================================
``'cont'``  continuous  floating point values         Lockin frequency, temperature setpoint
``'disc'``  discrete    discrete markers with labels  Lockin sensitivity, heater range
``'act'``   action      no response expected          Autogain on a lockin, turning off heater ramp control
==========  ==========  ============================  =====================================================


Arguments needed only if ``t == 'cont'``
:::::::::::::::::::::::::::::::::::::::::::

:pmin: Sets the minimum value the parameter is allowed to take.  Attempting to write a value smaller (or more negative) than this will truncate the output back to this value.  If not specified, there will be no limit.


:pmax: Sets the maximum value the parameter is allowed to take.  Attempting to write a value larger (or more positive) than this will truncate the output back to this value.  If not specified, there will be no limit.


:prec: The precision (number of digits after the decimal point in whatever units) with which to write or report this parameter.  If not specified, the values from the user and from the instrument will not be rounded.


:units: The units of the continuous parameter: V, Hz, T, etc, as a string.


:comps: Sometimes, a command gives back several values at a time.  This is seen, for example, in the SNAP command of a lock-in amplifier, where you get both X and Y quadratures simulataneously.  In these cases, you'll need to specify the ``comps`` argument with a list of strings naming those different components in the order you expect them.  

.. important::
	If the ``comps`` contains more than one element, then the ``units`` parameter **also** needs to be a list of strings of the same length specifying the units of both components



Arguments needed only if ``t == 'disc'``
:::::::::::::::::::::::::::::::::::::::::::
:vals: This should be a list of whatever discrete flags the instruments expects.  For example, a temperature controller might expect integers 0,1,2,3 to specify different heater power ranges.  These are most often ``int`` type, but can be ``str``.


:labels: The numerical or otherwise encoded indicators in the ``vals`` list above are often not very illuminating to the user.  The ``labels`` argument specifies a human-readable version of the ``vals``, usually strings.




Writing macro functions
----------------------------
If you cannot get the behavior you want using only the single strings included in the ``w`` and ``q`` arguments, then you'll need to write a macro.  A macro is just a class function which is defined below the constructor.  You can name the function whatever you want, and then pass the name of that function to the ``Param`` object through either the ``wmacro`` or ``qmacro`` keyword arguments.  If ``wmacro`` is defined, then the program ignores any value given to ``w``, and similarly for ``qmacro``.

When writing these files, you can directly write and query strings to and from the instrument using the ``self.visa.write()`` and self.visa.read_raw()`` functions, which are inherited from the superclass ``instruments.InstClass.Instrument``.

It is possible to pass arguments into your macro, but this feature isn't bulletproof.  I've only really tested it using ``lambda`` functions, for example in the SRS830 module.

