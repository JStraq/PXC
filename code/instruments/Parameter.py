class Param:
    def __init__(self, name, w=None, q=None, t=None, pmin=None, pmax=None, prec=None,
                 vals=None, labels=None, units=None, wmacro=None, qmacro=None, comps=None):
        self.name = name
        self.write = w
        self.query = q
        self.comps = comps  # if compound, what are the names of the components?

        if t in ('cont', 'disc', 'act'):
            self.type = t
        else:
            self.type= 'act'    #assume it doesn't take a value

        self.prec = prec
        self.pmin = pmin
        self.pmax = pmax
        
        
        if vals is not None:
            self.vals = [str(x) for x in vals]
        else:
            self.vals = vals
            try:
                if len(labels) is not len(vals):
                    labels=None
            except TypeError:
                labels=None
        self.labels = labels  # for discrete parameters: a list of human-readable names for the values
        self.units = units  # string, or list of strings if comps is not None
        self.wmacro = wmacro  # Function to run when it's too complicated to write one line at a time
        self.qmacro = qmacro  # Function to run when it's too complicated to read one line at a time

        if self.type == "cont":
            if self.comps is not None:
                if not isinstance(self.units, list):            # if there's a list of components but only one unit
                    self.units = [self.units for comp in self.comps]  # assume all components have the same unit
                elif len(self.comps) != len(self.units):
                    raise ValueError("Error in parameter {:s}: component and unit list\
                                     have different lengths!".format(self.name))
    
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name