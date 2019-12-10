Command development
===================

Should you decide to make a new command, what do you need to know?

The commands are all subclasses of the parent ``SeqCmd`` class, and they inherit most of the useful bits from that.
You'll need to implement at least two functions: ``edit`` and ``execute``, in order to have this new command be accessible to the user.
``edit`` is what runs when you first create it or double-click on it, and execute is the actual sequence.

Without knowing what you're planning to do, the best I can suggest is to copy the one which is most similar to what you have in mind, and fiddle with it further from there.

As long as the subclass is in its own module and in the ``commands`` subdirectory, the framework I've built should detect it and present it as an option to the user.
Keep in mind that you might need to edit other code, though, if you require any kind of special accommodations.
(For example, moving ``LoopCommand``s up and down in the sequence is nontrivial because I also have to drag the ``LoopEnd`` along, so that case is handled explicitly in the GUI code.)

The components, though, which basically just include reading and writing to instruments, are all fairly straightforward.