PXC Architecture
================

This page describes the basic architecture of the PXC program, and this whole section gives you a really brief intro to how the code is set up.  The nitty-gritty class/function level documentation is in the next major section, :doc:`../funcs`.

I know for a fact that all of the packages and python features are documented online, though, since I relied heavily on them while building this.

Initialization
--------------

Launching the ``Main.py`` code does a few things: 

* Start a log file for the session, where each nontrivial action (and, heaven forfend, *error*) will be recorded.

* Sets up a lightly customized ``multiprocessing.BaseManager`` object--this will act as our main communication hub between different processes.  In particular, this manager includes an ``ExpController`` object which has a bunch of relevant attributes, as well as two separate ``Queue`` objects.  The ``ExpController`` stores and provides access to the current state of the program, while the ``Queue`` objects allow for signaling between different processes.


This then kicks off the GUI, (contained within the ``ExpGUI.py`` module) which enters a ``tk`` mainloop, where it stays until the GUI exits.


Up to this point, everything has happened on a single processor: initialization, hosting of the ExpController, and control of the GUI are all controlled by the primary parent process.



Experiment Setup
----------------
Within this parent process, the ``tk`` mainloop allows the user to interactively set up the experiment.  
All of the buttons and indicators visible to the user are controlled by the functions within ``ExpGUI.py`` module.
For the most part, all of the functions behind the scenes are straightforward, if a bit tedious, as is usually the case for GUI programming.


As the experiment details are entered by the user, all of the information about the setup is stored within an ``Apparatus`` object, from he ``Apparatus.py`` module.  This object stores lists and names of instruments objects (all of which are instances of specialized subclasses of the ``Instrument`` class in the ``instruments.InstClass.py`` module) as well as the list of sequence commands (specialized subclasses of ``SeqCmd`` object from the ``commands.SeqCommand.py`` module).



Running a Measurement
---------------------

When the user presses the "Run Sequence" button, things get a bit more complicated.  The immediate actions are:

* Alter the GUI state to enable/disable different buttons

* Create a new directory and file based on the information supplied

* Collect and write the metadata to a file (more on the actual format of this later **TODO**)

* Kick off two new processes:

	- The first one executes a function called ``instHandler``, which lives in the module of the same name.	This function takes the settings in the ``Apparatus`` object as defined by the user through the GUI [#]_ and basically just runs the sequence.	By "runs the sequence" I mean that the ``Apparatus`` will walk through the sequence of commands item by item, jumping around to handle loops or skipping disabled steps as required, and execute the ``SeqCmd.execute()`` function for each one.	The sequence command subclasses themselves, defined in their own modules in the ``code/commands/`` subdirectory, describe the *actual* functionality of each step.The ``instHandler`` process is completely autonomous and communicates with the instruments as required.	This runs until it finishes the sequence, until the sequence is aborted, or until the GUI is closed which kills the program.
	
	- As the ``instHandler`` produces data from the measurement, the first priority is to get it written to the file. [#]_ The second process runs a function called ``fileHandler``, which takes care of all of this reading and writing.	This one is not autonomous, but rather continuously waits for instructions to come from the parent or instrument processes.	These instructions are placed into the ``fileReqQ`` as objects of type ``fileRequest`` (defined in ``FileHandlers.py``) and tell the ``fileHandler`` to do things like "write a line of data", "open a new file", etc.	To streamline the common tasks I've wrapped the file in yet another object called a ``DataBase``. This opens closes, writes, and reads the file, but also keeps track of things like which data has already been sent to the GUI for plotting, and which datapoints are new.	But really the ``DataBase`` object lurks behind the scenes and does the grunt work.
	
	- While all of this happens, the parent process continues to update the GUI.	Based on the setup of the plot window or the variable monitors, the parent process sends requests to the ``fileHandler`` asking for the most recent measurements for certain variables.	Other than that, it's just business as usual, still controlled by the ``tk`` mainloop.
	
	
* Once the sequence completes, both of these extra processes terminate and we go back to the single parent process, as we started.
	

It's worth mentioning a few subtle points here which might create confusion.
When the program is **not** running a sequence, the user may still want to see the present values on a particular variable: this would require that a measurement be made.
Or, a user may want to look at some data from the previous run to compare: this would require a file to be read.
These are tasks which, during the measurement, would be handled by the child ``instHandler`` and ``fileHandler`` processes respectively.
However, since low latency is not as important between measurements, I've opted to run them within the parent process.
This means that there are functions within the ``ExpGUI`` and ``Plotter`` modules which might seem at firs glance to be redundant with the ``instHandler`` and ``fileHandler`` processes, but in reality they cover very different use cases.



Plotting and the GUI
--------------------
As mentioned above, the GUI programming bits are tedious.  Unless you're super excited about learning Tk (which I don't think any sane person should be) then try to minimize the amount of fiddling you do with that.
If you go for it anyway, I'm not really doing anything fancy--and it's all pretty well documented online.
I've also tried my best to keep the code commented, keep my GUI bits sensibly-named, and keep it all organized and modular, but it will require significant time investments to make changes to the GUI itself.
	
	
.. [#] Technically, ``instHandler`` takes a serialized version (that is, all of its relevant info is compressed into a string) of the ``Apparatus`` object, and then reconstructs a copy....this is because of some silly rules about what kind of data can be sent between processes.  Though the parent process still has the original ``Apparatus`` object, it simply does nothing during the measurement, and therefore avoids any bus contention.

.. [#] Note that plotting the data is only secondary.  This ordering of priorities is what led me to adopt the relatively inefficient strategy of sending the data from the instruments to the file and *then* to the GUI.  Given the flexibility I need, this system works well enough.
