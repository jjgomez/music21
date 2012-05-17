# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         webapps.commands.py
# Purpose:      music21 functions for implementing web interfaces
#
# Authors:      Lars Johnson
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------  
'''
Webapps is a module designed for using music21 with a webserver.

This file includes templates detailing different output formats available for the CommandProcessor

Each template returns a tuple of the form (data, contentType).

'''
import unittest
import doctest

from music21 import corpus
import music21
from string import Template

  
def musicxmlText(outputStream):
    '''
    Takes in a stream outputStream and returns its musicxml with content-type 'text/plain' for displaying in a browser
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = musicxmlText(sc)
    >>> contentType
    'text/plain'
    >>> 'score-partwise' in output
    True
    '''
    musicxml = outputStream.musicxml
    return (musicxml, 'text/plain')

def musicxmlFile(outputStream):
    '''
    Takes in a stream outputStream and returns its musicxml with content-type 'application/vnd.recordare.musicxml+xml' for downloading
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = musicxmlFile(sc)
    >>> contentType
    'application/vnd.recordare.musicxml+xml'
    >>> 'score-partwise' in output
    True
    '''
    musicxml = outputStream.musicxml
    return (musicxml,'application/vnd.recordare.musicxml+xml')
    
def vexflow(outputStream):
    '''
    Takes in a stream outputStream, generates an HTML representation of it using vexflow, and
    outputs it with content-type text/html for displying in a browser.
    
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = vexflow(sc)
    >>> contentType
    'text/html'
    '''
    from music21 import vexflow
    outputHTML = vexflow.fromObject(outputStream, mode='html')
    return (outputHTML,'text/html')
 
def braille(outputStream):
    '''
    Takes in a stream outputStream, generates the braille representation of it, and returns
    the unicode output with content-type text/html for display in a browser
  
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = braille(sc)
    >>> contentType
    'text/html; charset=utf-8'
    '''
    from music21 import braille
    from music21.braille import translate as btranslate
    
    brailleOutput = u"<html><body><pre>" + btranslate.objectToBraille(outputStream) + u"</pre></body></html>"
    return (brailleOutput.encode('utf-8'), 'text/html; charset=utf-8')   

def noteflightEmbed(outputStream, title):
    '''
    Takes in a stream outputStream, and a string title. Returns the HTML for a page containing a noteflight
    flash embed of the stream and the title title
    
    TODO: Change javascript and noteflight embed to relate to be server-specific
  
    >>> sc = corpus.parse('bwv7.7').measures(0,2)
    >>> (output, contentType) = noteflightEmbed(sc, "My Title")
    >>> contentType
    'text/html'
    >>> "My Title" in output
    True
    '''
    
    musicxml = outputStream.musicxml
    musicxml = musicxml.replace('\n','')
    musicxml = musicxml.replace('\'','\\\'')
    htmlStr = """
<html>
<head>
<title>Music21 URL App Response</title>
<script language="javascript" src="http://ciconia.mit.edu/music21/webapps/client/javascript/music21.js"></script>
<script>
    // Event handling function
    function noteflightEventHandler(e)
    {
        if(e.type == 'scoreDataLoaded') {
            m21.noteflight.sendMusicXMLToNoteflightEmbed('nfscore','$musicxml')
        }
    }
</script>
<script language="javascript">
m21 = new Music21interface();

function setup() {
    m21.noteflight.createNoteflightEmbed('noteflightembed','nfscore','fc79df30896da6aa03f90ff771015913ca6880be',800,450,1.0);
}
</script>

</head>
<body onload="setup()">

<h1>$title</h1> 
<div id="noteflightembed">
</div>


</body>
</html>
    """
    htmlData = Template(htmlStr)
    
    htmlData = htmlData.safe_substitute(musicxml=musicxml, title=title)
    return (htmlData, 'text/html')

#-------------------------------------------------------------------------------
# Tests 
#-------------------------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == '__main__':
    music21.mainTest(Test)
        