Installing PXC
==============

.. note::
	
	I've only ever tested this code on Windows...I'm guessing there will at least be a few hardcoded paths which will fail, but I'm not going to screw with it until I need a mac or linux system.



Python
---------

Begin by installing Python 3.5 or greater.  I like to be simple and use a distribution like Anaconda--it has a lot of extra features we won't use, but it seems to work fairly well with minimal fiddling.

You'll then need to make sure you have the following packages.  (You'll probably have some of these already)

* **matplotlib**	 	1.5.1 or greater
* **PyVISA**    	 	1.8 or greater [#]_
* **numpy**    		  	1.17.3 or greater
* **multiprocessing** 	0.70.4 or greater
* **tzlocal**			2.0.0 or greater

If you plan on doing any developing, then also make sure you have **sphinx** installed as well (2.2.0 or later) so you can update this documentation.

The easiest way to install a packages is to use either ``pip`` or ``conda`` package manager commands, as in ``pip install matplotlib``.  This sometimes requires you to make sure ``pip`` is added to your path, but I think using the Anaconda prompt takes care of that for you and installs pip automatically.


Cloning the Git repo
------------------------
The repository is located at ``https://github.com/JStraq/PXC``.
See the git documentation to figure that out if you've never done that before.
If you decide you want push access, contact me. [#]_


Running the program
------------------------

The full program can be run by launching ``Main.py`` from any terminal.  You can set up a desktop shortcut to Main.py, and set it to ``start in`` the program in the ``PXC\\code`` folder.

Also, this program will generate all of its data and log files into subdirectories of ``C:\Data\``.

.. [#] yes, this *is* case-sensitive.
.. [#] jstraquadine@gmail.com