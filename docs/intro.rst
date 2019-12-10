Introduction
=====================

**PXC** stands for **P**\ython e\ **X**\periment **C**\ontroller.

What PXC is
-----------------
The primary motivation behind writing this code is support for quick and flexible experiments in homebuilt cryostats.
This is accomplished through the following principles:

* Relatively simple driver-based system to support adding any instrument one can hook up to a computer

* Sequence-based measurement

* Flexible plotting interface

* Parallelized processing for all of these tasks

What PXC is NOT
--------------------
PXC is **not** intended as a data analysis suite.
Plotting functions and basic math are provided because they can be crucial to see while the experiment is running, but after the run you should use a dedicated analysis codebase.


PXC is also **not** generally intended for time-sensitive projects.
While the code has been parallelized to run quickly, timing is still generally subject to GPIB/computer latency.
If you need a specific data acquisition rate, you'd be better off buffering data into one of the devices, then reading that buffer with PXC afterward.


Plan of the documentation
--------------------------------
This document is split into three parts:

1. How to install and use PXC in your lab (See :doc:`usage`)
2. How to add new instruments or sequence commands (See :doc:`dev`)
3. Full-blown code listings and function/class descriptions, for those who are really serious about editing this thing. (see :doc:`funcs`)

I will assume you already have a grasp on the following topics:

* Python programming, datatypes, and object-oriented code practices [#]_
* Basic GPIB communication through NIMAX or a similar terminal


Acknowledgements
-------------------------
Everything in this is open source, and makes use of the packages below.

* Matplotlib
* Numpy
* Pyvisa
* Tkinter
* tzlocal
* Sphinx (documentation)


Getting help
-------------------------
I (Josh Straquadine) was a grad student, but I have since moved on, and I don't really want to do in-depth tech support for PXC.  Depending on the nature of your request, though, I might be able to help anyway.  You can contact me at jstraquadine@gmail.com.

You should also feel free to edit whatever code you think you need to make this work for you.  This project is stored in a Github repository, and you can either fork it to your own account or create a new branch for your fiddling.  Please do follow basic git etiquette rules such as submitting pull requests, reporting issues, and the like: don't just push or merge to `master` without talking to me.

**For errors or unexpected behavior:** if you've read this documentation through, and something is throwing strange errors, send me all of the log files for the runs in question, as well as a description of what you were trying to do and what was hooked up at the time.

**For feature addition**: if you really need some guidance or coding support, and you've read this through, send me an email.


.. [#] Except, of course, for the installation bit.
