Plotting in PXC
===============

The plotting GUI is intended for quick overviews of your data, not beautiful plotting.  
However, it still ended up being flexible enough for most things.

In the center of the GUI, you have three tabs, each of which holds a single plot.
The plot axes can each accomodate an arbitrary number of curves, though, and you have the freedom to add an independent right y-axis if you want.
You can access the plot configuration options by double-clicking on the tab you want to configure.

The code only allows you to have one file open at a time, so all of the plots will be from the same file.
Furthermore, while you're running a sequence, you're *only* allowed to have the file which is currently being written as your source of plots.
If you change files or start a new sequence, it will do its best to retain similar types of graphs, but given that instrument names might change, I'm not going to make any guarantees.  It's easy enough to reset it to how you want it.

Other than that, though, I think the edit tools are quite intuitive, and you'll figure it out quickly.