#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         build.py
# Purpose:      music21 documentation builder
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-10 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import os, sys, webbrowser
import types, inspect

import music21

from music21 import base
from music21 import clef
from music21 import chord
from music21 import common
from music21 import converter

from music21.corpus import base as corpus

from music21 import duration
from music21 import dynamics
from music21 import editorial
from music21 import environment
from music21 import graph
from music21 import instrument
from music21 import interval
from music21 import note
from music21 import node
from music21 import pitch
from music21 import meter
from music21 import musicxml
from music21 import scale
from music21 import serial
from music21 import stream
from music21 import tempo
from music21 import tinyNotation

from music21.trecento import cadencebook as trecentoCadencebook

#from music21 import environment #redundant
_MOD = "doc.build.py"
environLocal = environment.Environment(_MOD)

INDENT = ' '*4
OMIT_STR = 'OMIT_FROM_DOCS'
FORMATS = ['html', 'latex', 'pdf']

# this is added to generated files
WARN_EDIT = '.. WARNING: DO NOT EDIT THIS FILE: AUTOMATICALLY GENERATED\n\n'

MODULES = [
    base,
    clef, 
    common, 
    converter,
    corpus, 
    chord, 
    duration, 
    dynamics,
    editorial,
    environment, 
    graph,
    instrument,
    interval, 
    meter, 
    note, 
    node, 
    pitch, 
    stream,     
    serial,     
    tempo,     
    tinyNotation,

#   musicxml, 
#   #  scale,

# trecento
#    trecentoCadencebook
]



# sphinx notes:

# cross references:
# http://sphinx.pocoo.org/markup/inline.html?highlight=method




#-------------------------------------------------------------------------------
class PartitionedName(object):

    def __init__(self, srcNameEval=None):

        self.srcNameEval = srcNameEval
        self.names = []

        try:
            self.srcObj = self.srcNameEval()
        except TypeError:
            self.srcObj = None

    def getElement(self, partName):
        return None

    def getSignature(self, partName):
        '''Expand to include signatures when possible

        >>> from music21 import pitch, meter
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.getSignature('midi')
        ''

        >>> a = PartitionedClass(meter.MeterSequence)
        >>> a.getSignature('load')
        '(value, partitionRequest=None, autoWeight=False, targetWeight=None)'


        '''
        element = self.getElement(partName)
        if element.kind in ['method', 'function']:
            data = inspect.getargspec(element.object)
            #data = inspect.formatargspec()
            argStr = []
            # ordered list in same order as args
            defaults = data[3] 
            # get index offset to when defaults start
            if defaults != None:
                offset = len(data[0]) - len(defaults)
            else:
                offset = 0

            for p in range(len(data[0])): # these are required, include self
                arg = data[0][p]
                if arg == 'self': continue
                
                if defaults != None and p >= offset:
                    default = defaults[p-offset]
                    argStr.append('%s=%s' % (arg, default))
                else:
                    argStr.append('%s' % (arg))
            msg = '(%s)' % ', '.join(argStr)

        elif element.kind == 'property':
            msg = ''
        elif element.kind == 'data':
            msg = ''
        return msg


#-------------------------------------------------------------------------------
class PartitioinedModule(PartitionedName):
    '''Given a module name, manage and present data.
    '''
    def __init__(self, srcNameEval):
        PartitionedName.__init__(self, srcNameEval)

        self.srcNameStr = self.srcNameEval.__name__

        self.namesOrdered = [] # any defined order for names
        if hasattr(self.srcNameEval, '_DOC_ORDER'):
            # these are evaluated class names, not strings
            for orderedObj in self.srcNameEval._DOC_ORDER:
                if hasattr(orderedObj, 'func_name'):
                    orderedName = orderedObj.func_name
                elif hasattr(orderedObj, '__name__'):
                    orderedName = orderedObj.__name__
                else:
                    environLocal.printDebug(['cannot get a string name of object:', orderedObj])
                    continue
                self.namesOrdered.append(orderedName)

        else:
            environLocal.printDebug('module %s missing _DOC_ORDER' % 
                                    self.srcNameStr)

        self.names = dir(self.srcNameEval)
        self._data = self._fillData()
        self._sort()

    def _fillData(self):
        '''
        >>> from music21 import pitch
        >>> a = PartitioinedModule(pitch)
        >>> len(a.names) == len(a._data)
        True
        >>> a.namesOrdered
        ['Pitch', 'Accidental']
        >>> a.names[0]
        'Pitch'
        >>> a.names[0] == a._data[0].name
        True
        '''
        post = []
        for name in self.names:
            objName = '%s.%s' % (self.srcNameStr, name)
            obj = eval(objName)

            # skip for now
            homecls = self.srcNameEval
            if hasattr(obj, '__module__'):
                if self.srcNameStr not in obj.__module__:
                    homecls = obj.__module__

            # get kind
            if isinstance(obj, types.ModuleType):
                kind = 'module'
            elif (isinstance(obj, types.StringTypes) or 
                isinstance(obj, types.DictionaryType) or 
                isinstance(obj, types.ListType) or 
                common.isNum(obj) or common.isListLike(obj)): 
                kind = 'data'
            elif isinstance(obj, types.FunctionType):
                kind = 'function'
            elif isinstance(obj, types.TypeType):
                kind = 'class'
            elif isinstance(obj, environment.Environment):
                kind = 'data' # skip environment object
            else:
                environLocal.printDebug(['cannot process module level name: %s' % self.srcNameStr])
                kind = None

            post.append(inspect.Attribute(name, kind, homecls, obj))

        return post


    def _sort(self):
        namesSupply = self.names[:]
        names = []
        _data = []

        for name in self.namesOrdered:
            if name not in namesSupply:
                raise Exception('module %s does not have name %s' % (self.srcNameStr, name))
            junk = namesSupply.pop(namesSupply.index(name))
    
            i = self.names.index(name)
            names.append(self.names[i])
            _data.append(self._data[i])

        # get all others that are not defined
        for name in namesSupply:
            i = self.names.index(name)
            names.append(self.names[i])
            _data.append(self._data[i])

        self.names = names
        self._data = _data


    def getElement(self, partName):
        '''
        '''
        if partName not in self.names:
            raise Exception('cannot find %s name in %s' % (partName,    
                                     self.srcNameEval))
        return self._data[self.names.index(partName)]


    def getNames(self, nameKind, public=True, local=True):
        '''Local determines if the name is from this module or imported.

        >>> from music21 import pitch
        >>> a = PartitioinedModule(pitch)
        >>> a.getNames('classes')
        ['Pitch', 'Accidental']
        >>> a.getNames('functions')    
        ['convertFqToPs', 'convertPsToFq', 'convertPsToOct', 'convertPsToStep', 'convertStepToPs']
        '''

        post = []
        if nameKind.lower() in ['classes', 'class']:
            nameKind = 'class'
        elif nameKind.lower() in ['modules', 'imports', 'module']:
            nameKind = 'module'
        elif nameKind.lower() in ['functions', 'function']:
            nameKind = 'function'
        elif nameKind.lower() in ['data', 'attributes', 'attribute']:
            nameKind = 'data'

        for name in self.names:
            element = self.getElement(name)
            if local:
                # this is really defining module
                if element.defining_class != self.srcNameEval:
                    continue

            if public:
                if name.startswith('__'): # ignore private variables
                    continue
                if name.startswith('_'): # ignore private variables
                    continue
                elif 'Test' in name: # ignore test classes
                    continue
                elif 'Exception' in name: # ignore exceptions
                    continue

            if not element.kind == nameKind:
                continue

            post.append(name)
        return post


    def getDoc(self, partName):
        element = self.getElement(partName)
        if element.kind in ['class', 'function']:
            return element.object.__doc__


#-------------------------------------------------------------------------------
class PartitionedClass(PartitionedName):
    '''Given an evaluated class name as an argument, mange and present
    All data for all attributes, methods, and properties.

    Note that this only gets data attributes that are defined outside
    of the __init__ definition of the Class. 
    '''
    def __init__(self, srcNameEval):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> len(a.names) > 30
        True
        >>> a.mro
        (<class 'music21.pitch.Pitch'>, <class 'music21.base.Music21Object'>, <type 'object'>)

        '''
        PartitionedName.__init__(self, srcNameEval)

        self.mro = inspect.getmro(self.srcNameEval)
        self.mroLive = self._createMroLive()

        # store both a list of names as well as name/mro index pairs
        self.names = []
        self.namesMroIndex = []

        # this is not a complete list of names
        self.namesOrdered = [] # any defined order for names
        if hasattr(self.srcNameEval, '_DOC_ORDER'):
            self.namesOrdered += self.srcNameEval._DOC_ORDER

        # this will get much but not all data
        self._dataClassify = inspect.classify_class_attrs(self.srcNameEval)
        for element in self._dataClassify:
            # get mro index number
            self.names.append(element.name)
            mroIndexMatch = self.mro.index(element.defining_class)
            self.namesMroIndex.append((element.name, mroIndexMatch))

        # add dataLive after processing names from classify
        # this assures that names are not duplicated
        self._dataLive = self._fillDataLive()
        for element in self._dataLive:
            # get mro index number
            self.names.append(element.name)
            mroIndexMatch = self.mro.index(element.defining_class)            
            self.namesMroIndex.append((element.name, mroIndexMatch))

        # create a combined data storage
        # this will match the order in names, and namesMroIndex
        self._data = self._dataClassify + self._dataLive

        self._sort()

    def _sort(self):
        '''Sort _data, self.namesMroIndex, and self.names by placing anything defined in self.srcNameEval first.
        '''
        namesSupply = self.names[:]

        names = []
        namesMroIndex = []
        _data = []

        # always put first
        for forceName in ['__init__']:
            if forceName in namesSupply:
                junk = namesSupply.pop(namesSupply.index(forceName))
                i = self.names.index(forceName)
                names.append(self.names[i])
                namesMroIndex.append(self.namesMroIndex[i])
                _data.append(self._data[i])

        for name in self.namesOrdered:
            if name in forceName:
                continue # already supplied
            # cannot be sure this is the same index as that in self.names
            junk = namesSupply.pop(namesSupply.index(name))

            i = self.names.index(name)
            names.append(self.names[i])
            namesMroIndex.append(self.namesMroIndex[i])
            _data.append(self._data[i])

        # get all others that are not defined
        for name in namesSupply:
            i = self.names.index(name)
            names.append(self.names[i])
            namesMroIndex.append(self.namesMroIndex[i])
            _data.append(self._data[i])

        self.names = names
        self.namesMroIndex = namesMroIndex
        self._data = _data


    def _createMroLive(self):
        '''Try to create the mro order but with live objects.

        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> len(a._createMroLive()) == 3
        True
        '''
        post = []
        for entry in self.mro:
            try:
                obj = entry()
            except TypeError:
                obj = None
            post.append(obj)
        return post

    def _fillDataLive(self):
        post = []
        # we cannot get this data if the object cannot be instantiated
        if self.srcObj == None: 
            return post
        # dir(self.srcObj) will get all names
        # want only writable attributes: 
        for name in self.srcObj.__dict__.keys():
            if name in self.names:
                continue # already have all the info we need
            # using an attribute class to match the form given by 
            # inspect.classify_class_attrs
            obj = self.srcObj.__dict__[name]
            kind = 'data' # always from __dict__, it seems
            # go through live mroLive objects and try to find
            # this attribute
            mroIndices = self.mroIndices()
            mroIndices.reverse()
            homecls = None
            for mroIndex in mroIndices:
                if (hasattr(self.mroLive[mroIndex], '__dict__') and 
                    name in self.mroLive[mroIndex].__dict__.keys()):
                    # if found, set class name to heomcls
                    homecls = self.mro[mroIndex]
                    break
            if homecls == None:
                homecls = self.srcNameEval

            post.append(inspect.Attribute(name, kind, homecls, obj))
        return post

    def findMroIndex(self, partName):
        '''Given an partName, find from where (in the list of methods) the part is derived. Returns an index number value.

        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.findMroIndex('midi')
        0
        >>> a.findMroIndex('id')
        1
        '''        
        i = self.names.index(partName)
        name, mroIndex = self.namesMroIndex[i]
        return mroIndex

    def mroIndices(self):
        return range(len(self.mro))

    def lastMroIndex(self):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.lastMroIndex()
        2
        '''
        return len(self.mro)-1

    def getElement(self, partName):
        '''
        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)
        >>> a.getElement('midi')
        Attribute(name='midi', kind='property', defining_class=<class 'music21.pitch.Pitch'>, object=<property object...
        >>> a.getElement('id')
        Attribute(name='id', kind='data', defining_class=<class 'music21.base.Music21Object'>, object=None)
        >>> a.getElement('_getDiatonicNoteNum')
        Attribute(name='_getDiatonicNoteNum', kind='method', defining_class=<class 'music21.pitch.Pitch'>, object=<function...

        '''
        if partName not in self.names:
            raise Exception('cannot find %s name in %s' % (partName,    
                                     self.srcNameEval))
        return self._data[self.names.index(partName)]


    def getDefiningClass(self, partName):
        element = getElement(partName)
        return element.defining_class

    def getClassFromMroIndex(self, mroIndex):
        return self.mro[mroIndex]


    def getDoc(self, partName):
        element = self.getElement(partName)

        if hasattr(self.srcNameEval, '_DOC_ATTR'):
            docAttr = self.srcNameEval._DOC_ATTR
        else:
            docAttr = {}

        match = None
                
        if partName in docAttr.keys():
            match = docAttr[partName]
        # if its an undocumented public attribute and basic python
        # data structure, we do not want to show that documentation
        elif (element.kind in ['data'] and (
            common.isStr(element.object) or 
            common.isListLike(element.object) or
            common.isNum(element.object)
            )):
            pass
        else:
            try:
                match = element.object.__doc__
            except AttributeError:
                match = None


        if match == None:
            return 'No documentation.'
        else:
            return match

    def getNames(self, nameKind, mroIndex=None, public=True, getInit=True):
        '''Name type can be method, data, property

        >>> from music21 import pitch
        >>> a = PartitionedClass(pitch.Pitch)

        >>> len(a.getNames('property')) > 10
        True

        >>> len(a.getNames('method')) > 7
        True

        >>> a.getNames('method', mroIndex=0)
        ['__init__']
        >>> a.getNames('data', mroIndex=0)
        ['defaultOctave']
        >>> a.getNames('data', mroIndex=1)
        ['id', 'groups']
        >>> a.getNames('data', mroIndex=a.lastMroIndex())
        []

        >>> from music21 import converter
        >>> a = PartitionedClass(converter.Converter)
        >>> a.getNames('methods')
        ['__init__', 'parseData', 'parseFile', 'parseURL']

        >>> from music21 import meter
        >>> a = PartitionedClass(meter.TimeSignature)
        >>> len(a.getNames('methods')) > 10
        True
        >>> a.getNames('attributes', 1)
        ['id', 'groups']

        '''
        post = []
        if nameKind.lower() in ['properties', 'property']:
            nameKind = 'property'
        elif nameKind.lower() in ['methods', 'method']:
            nameKind = 'method'
        elif nameKind.lower() in ['data', 'attributes', 'attribute']:
            nameKind = 'data'

        for name in self.names:
            element = self.getElement(name)
            if public:
                # special handling for init methods
                if name == '__init__':
                    if not getInit:
                        continue
                elif name.startswith('__') or name.startswith('_'): 
                    continue

            #environLocal.printDebug(['kinds', name, element.kind])

            if not element.kind == nameKind:
                continue
            if mroIndex != None: # select by mro
                #environLocal.printDebug(['mroindex', self.findMroIndex(name)])
                if mroIndex == self.findMroIndex(name):
                    post.append(name)
            else:
                post.append(name)
        return post



#-------------------------------------------------------------------------------
class RestructuredWriter(object):

    def __init__(self):
        pass

    def _heading(self, line, headingChar='=', indent=0):
        '''Format an RST heading. Indent is in number of spaces.
        '''
        indent = ' ' * indent
        #environLocal.printDebug(['got indent', indent])
        msg = []
        msg.append(indent + line)
        msg.append(indent + '\n')
        msg.append(indent + headingChar*len(line))
        msg.append(indent + '\n'*2)
        return msg

    def _para(self, doc):
        '''Format an RST paragraph.
        '''
        if doc == None:
            return []
        doc = doc.strip()
        msg = []
        msg.append('\n'*2)
        msg.append(doc)
        msg.append('\n'*2)
        return msg

    def _list(self, elementList, indent=''):
        '''Format an RST list.
        '''
        msg = []
        for item in elementList:
            item = item.strip()
            msg.append('%s+ ' % indent)
            msg.append(item)
            msg.append('\n'*1)
        msg.append('\n'*1)
        return msg

    def formatParent(self, mroEntry):
        '''Return a class name as a parent, showing module when necessary

        >>> from music21 import note
        >>> rw = RestructuredWriter()
        >>> post = rw.formatParent(inspect.getmro(note.Note)[1])
        >>> 'note.NotRest' in post      
        True
        >>> post = rw.formatParent(inspect.getmro(note.Note)[4])
        >>> 'object' in post      
        True
        '''
        modName = mroEntry.__module__
        className = mroEntry.__name__
        if modName == '__builtin__':
            return className
        else:
            return ':class:`%s.%s`' % (modName, className)

    def formatXRef(self, partName, group, mroEntry):
        '''Given the name and a containing object, get a cross references
        '''
        modName = mroEntry.__module__
        className = mroEntry.__name__
        if group in ['attributes', 'properties']:
            return ':attr:`%s.%s.%s`' % (modName, className, partName)            
        elif group in ['methods']:
            return ':meth:`%s.%s.%s`' % (modName, className, partName)

    def formatClassInheritance(self, mro):
        '''Given a list of classes from inspect.getmro, return a formatted
        String

        >>> from music21 import note
        >>> rw = RestructuredWriter()
        >>> post = rw.formatClassInheritance(inspect.getmro(note.Note))
        >>> 'note.GeneralNote' in post
        True
        >>> 'base.Music21Object' in post
        True
        '''
        msg = []
        msg.append('inherits from:')
        sub = []
        for i in range(len(mro)):
            if i == 0: continue # first is always the class itself
            if i == len(mro) - 1: continue # last is object
            sub.append(self.formatParent(mro[i]))
        if len(sub) == 0:
            return ''
        msg.append(', '.join(sub))
        return ' '.join(msg)


    def formatDocString(self, doc, indent=''):
        '''Given a docstring, clean it up for RST presentation.

        Note: can use inspect.getdoc() or inspect.cleandoc(); though
        we need customized approach demonstrated here.
        '''
        if doc == None:
            return ''
            #return '%sNo documentation.\n' % indent

        # define the start of lines that should not be changed
        rstExclude = ['.. image::', ':width:']

        lines = doc.split('\n')
        sub = []
        for line in lines:
            if OMIT_STR in line.strip(): # permit blocking doctest examples
                break # do not gather any more lines
            
            match = False
            for stub in rstExclude:
                if line.strip().startswith(stub):
                    # do not strop
                    environLocal.printDebug(['found rst in doc string:', line.strip()])
                    if stub == '.. image::':
                        sub.append('\n\n' + line) # do not strip
                    else:
                        sub.append('\n' + line) # do not strip
                    match = True
                    break
            # else, add a stripped line
            if not match:
                sub.append(line.strip())

        # find double breaks in text
        post = []
        for i in range(len(sub)):
            line = sub[i]
            if line == '' and i != 0 and sub[i-1] == '':
                post.append(None) # will be replaced with line breaks
            elif line == '':
                pass
            else: 
                post.append(line)

        msg = [indent] # can add indent here
        inExamples = False
        for line in post:
            if line == None: # insert breaks from two spaces
                msg.append('\n\n' + indent) # can add indent here
            elif line.startswith('>>>'): # python examples
                if inExamples == False:
                    space = '\n\n'
                    inExamples = True
                else:
                    space = '\n'
                msg.append(space + indent + line)
            else: # continuing an existing line
                if inExamples == False:
                    msg.append(line + ' ')
                else: # assume we are in examples; 
                # need to get lines python lines that do not start with delim
                    msg.append('\n' + indent + line + ' ')
        msg.append('\n')

        return ''.join(msg)


#-------------------------------------------------------------------------------
class ClassDoc(RestructuredWriter):

    def __init__(self, className):
        RestructuredWriter.__init__(self)

        self.className = className
        self.classNameEval = eval(className)
        self.partitionedClass = PartitionedClass(self.classNameEval)
        # this is a tuple of class instances that are in the order
        # of this class to base class
        self.mro = inspect.getmro(self.classNameEval)
        self.docCooked = self.formatDocString(self.classNameEval.__doc__, 
                                             INDENT)
        self.name = self.classNameEval.__name__


    #---------------------------------------------------------------------------
    def _fmtRstAttribute(self, name, signature):
        msg = []
        msg.append('%s.. attribute:: %s\n\n' %  (INDENT, name))
        #msg.append('**%s%s**\n\n' % (nameFound, postfix))   
        docRaw = self.partitionedClass.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw, INDENT))
        return ''.join(msg)

    def _fmtRstMethod(self, name, signature):
        msg = []
        msg.append('%s.. method:: %s%s\n\n' %  (INDENT, name, signature))
        #msg.append('**%s%s**\n\n' % (nameFound, postfix))   
        # do not need indent as doc is already formatted with indent
        docRaw = self.partitionedClass.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw, INDENT))
        return ''.join(msg)

    def getRestructuredClass(self):
        '''Return a string of a complete RST specification for a class.
        '''
        msg = []

        classNameStr = 'class %s' % self.name
        msg += self._heading(classNameStr, '-')
        titleStr = '.. class:: %s\n\n' % self.name
        msg += titleStr

        msg.append('%s\n' % self.docCooked)
        msg.append('%s%s\n\n' % (INDENT, self.formatClassInheritance(self.mro)))

        for group in ['attributes', 'properties', 'methods']:    
            msgGroup = []
            for mroIndex in self.partitionedClass.mroIndices():
                if mroIndex == self.partitionedClass.lastMroIndex():
                    continue
                names = self.partitionedClass.getNames(group, mroIndex, public=True)
                if len(names) == 0: continue

                if mroIndex != 0:
                    parentSrc = self.formatParent(
                        self.partitionedClass.getClassFromMroIndex(mroIndex))
                    groupStr = group.title()
                    msgGroup.append('%s%s inherited from %s: ' % (INDENT, groupStr, parentSrc))

                    msgSub = []
                    for partName in names:
                        #postfix = self.partitionedClass.getSignature(partName)
                        #msgSub.append('``%s%s``' % (partName, postfix))   

                        msgSub.append(self.formatXRef(partName, group,
                         self.partitionedClass.getClassFromMroIndex(mroIndex)))

                    msgGroup.append('%s\n\n' % ', '.join(msgSub))
                else: # locally defined, provide complete documentation
                    for partName in names:
                        signature = self.partitionedClass.getSignature(partName)
                        if group in ['properties', 'attributes']:
                            msgGroup.append(self._fmtRstAttribute(partName,
                                                            signature))
                        elif group == 'methods':
                            msgGroup.append(self._fmtRstMethod(partName,
                                                            signature))

            if len(msgGroup) > 0:
                msg.append('%s**%s** **%s**\n\n' % (INDENT, classNameStr, group))
                msg.append(''.join(msgGroup))

        msg.append('\n'*1)
        return msg




#-------------------------------------------------------------------------------
class ModuleDoc(RestructuredWriter):
    def __init__(self, modNameEval):
        RestructuredWriter.__init__(self)

        self.partitionedModule = PartitioinedModule(modNameEval)
        self.docCooked = self.formatDocString(modNameEval.__doc__)
        self.modNameEval = modNameEval
        self.modName = self.modNameEval.__name__

        # file name for this module; leave off music21 part
        fn = self.modName.split('.')
        self.fileRef = 'module' + fn[1][0].upper() + fn[1][1:]
        self.fileName = self.fileRef + '.rst'
        # references used in rst table of contents

    def _fmtRstFunction(self, name, signature):
        msg = []
        msg.append('.. function:: %s%s\n\n' %  (name, signature))
        docRaw = self.partitionedModule.getDoc(name)
        msg.append('%s\n' % self.formatDocString(docRaw))
        return ''.join(msg)

    def getRestructured(self):
        '''Produce RST documentation for a complete module.
        '''
        # produce a simple string name of module to tag top of rst file
        modNameStr = self.modName.replace('music21.', '')
        modNameStr = modNameStr[0].upper() + modNameStr[1:]

        msg = []
        # the heading needs to immediately follow the underscore identifier
        msg.append('.. _module%s:\n\n' % modNameStr)
        msg += self._heading(self.modName , '=')

        msg.append(WARN_EDIT)
        # this defines this rst file as a module; does not create output
        msg += '.. module:: %s\n\n' % self.modName
        msg += self.docCooked
        msg.append('\n\n')

        for group in ['functions', 'classes']:
            names = self.partitionedModule.getNames(group)
            if len(names) == 0: continue

            for partName in names:
                if group == 'functions':
                    signature = self.partitionedModule.getSignature(partName)
                    msg.append(self._fmtRstFunction(partName, signature))
                    #msg += '.. function:: %s()\n\n' % partName
                     #msg.append('%s\n' % self.functions[funcName]['doc'])
                if group == 'classes':
                    qualifiedName = '%s.%s' % (self.modName, partName)
                    classDoc = ClassDoc(qualifiedName)
                    msg += classDoc.getRestructuredClass()

        return ''.join(msg)





#-------------------------------------------------------------------------------
class Documentation(RestructuredWriter):

    def __init__(self):
        RestructuredWriter.__init__(self)

        self.titleMain = 'Music21 Documentation'

        # include additional rst files that are not auto-generated
        # order here is the order presented in text
        self.chaptersMain = ['what',
                             'quickStart',
                             'overviewNotes', 
                             'overviewStreams', 
                             'overviewFormats', 
                             'overviewPostTonal', 
                             'examples', 

                             'install', 
                             'about', 
                             'environment', 
                             'graphing', 
                             'advancedGraphing', 
                             'faq',
                             'glossary',
                             ]
        self.chaptersDeveloper = ['documenting',
                                ]
    
        self.chaptersGenerated = [] # to be populated

        self.titleAppendix = 'Indices and Tables'
        self.chaptersAppendix = ['glossary']
    
        self.modulesToBuild = MODULES
        self.updateDirs()


    def updateDirs(self):
        self.dir = os.getcwd()
        self.parentDir = os.path.dirname(self.dir)
        parentContents = os.listdir(self.parentDir)
        # make sure we are in the the proper directory
        if (not self.dir.endswith("buildDoc") or 
            'music21' not in parentContents):
            raise Exception("not in the music21%sbuildDoc directory: %s" % (os.sep, self.dir))
    
        parentDir = os.path.dirname(self.dir)
        self.dirBuild = os.path.join(parentDir, 'music21', 'doc')
        self.dirRst = os.path.join(self.dir, 'rst')
        self.dirBuildHtml = os.path.join(self.dirBuild, 'html')
        #self.dirBuildLatex = os.path.join(self.dirBuild, 'latex')
        #self.dirBuildPdf = os.path.join(self.dirBuild, 'pdf')
        self.dirBuildDoctrees = os.path.join(self.dir, 'doctrees')

        for fp in [self.dirBuild, self.dirBuildHtml, 
                  #self.dirBuildLatex,
                  self.dirBuildDoctrees]:
                  #self.dirBuildPdf]:
            if os.path.exists(fp):
                # delete old paths?
                pass
            else:
                os.mkdir(fp)

    def writeContents(self):
        '''This writes the main table of contents file, contents.rst. 
        '''
        msg = []
        msg.append('.. _contents:\n\n')
        msg += self._heading(self.titleMain, '=')

        msg.append(WARN_EDIT)
        # first toc has expanded tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 2\n\n')
        for name in self.chaptersMain:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

        msg += self._heading('Module Reference', '=')
        # second toc has collapsed tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 1\n\n')
        for name in self.chaptersGenerated:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')

        msg += self._heading('Developer Reference', '=')
        # second toc has collapsed tree
        msg.append('.. toctree::\n')
        msg.append('   :maxdepth: 2\n\n')
        for name in self.chaptersDeveloper:
            msg.append('   %s\n' % name)        
        msg.append('\n\n')


        msg += self._heading(self.titleAppendix, '=')
        for name in self.chaptersAppendix:
            msg.append("* :ref:`%s`\n" % name)
        msg.append('\n')

        fp = os.path.join(self.dirRst, 'contents.rst')
        f = open(fp, 'w')
        f.write(''.join(msg))
        f.close()

#         ex = '''.. _contents:
# 
# music21 Documentation
# ==============================
# 
# .. toctree::
#    :maxdepth: 2
# 
#    objects
#    examples
#    glossary
#    faq
# 
#    moduleNote_
# 
# Indices and Tables
# ==================
# 
# * :ref:`glossary`
# 
#         '''



    def writeModuleReference(self):
        '''Write a .rst file for each module defined in modulesToBuild.
        Add the file reference to the list of chaptersGenerated.
        '''
        for module in self.modulesToBuild:
            environLocal.printDebug(['writing rst documentation:', module])
            a = ModuleDoc(module)
            #a.scanModule()
            f = open(os.path.join(self.dirRst, a.fileName), 'w')
            f.write(a.getRestructured())
            f.close()
            self.chaptersGenerated.append(a.fileRef)

    def main(self, format):
        '''Create the documentation. 
        '''
        if format not in FORMATS:
            raise Exception, 'bad format'

        self.writeModuleReference()    
        self.writeContents()    

        if format == 'html':
            dirOut = self.dirBuildHtml
            pathLaunch = os.path.join(self.dirBuildHtml, 'contents.html')
        elif format == 'latex':
            dirOut = self.dirBuildLatex
            #pathLaunch = os.path.join(dirBuildHtml, 'contents.html')
        elif format == 'pdf':
            dirOut = self.dirBuildPdf
        else:
            raise Exception('undefined format %s' % format)

        if common.getPlatform() in ['darwin', 'nix', 'win']:
            # -b selects the builder
            import sphinx
            sphinxList = ['sphinx', '-E', '-b', format, '-d', self.dirBuildDoctrees,
                         self.dirRst, dirOut] 
            sphinx.main(sphinxList)
    
        if format == 'html':
            webbrowser.open(pathLaunch)





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testToRoman(self):
        self.assertEqual(True, True)



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        music21.mainTest(Test)
        buildDoc = False
    elif len(sys.argv) == 2 and sys.argv[1] in FORMATS:
        format = [sys.argv[1]]
        buildDoc = True
    else:
        format = ['html']#, 'pdf']
        buildDoc = True

    if buildDoc:
        for fmt in format:
            a = Documentation()
            a.main(fmt)
