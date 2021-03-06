# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows transcription of music21 data to braille
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

"""
Methods for exporting music21 data as braille.


This module was made in consultation with the manual "Introduction to Braille
Music Transcription, Second Edition" by Mary Turner De Garmo, 2005. It is
available from the Library of Congress `here <http://www.loc.gov/nls/music/>`_,
and will henceforth be referred to as BMTM.


The most important method, and the only one that is needed to translate music
into braille, is :meth:`~music21.braille.translate.objectToBraille`. This method,
as well as the others, accept keyword arguments that serve to modify the output.
If no keyword arguments are needed, then using the method is equivalent to
calling :meth:`~music21.base.Music21Object.show` on the music.


Keywords:


* **inPlace** (False): If False, then :meth:`~music21.stream.Stream.makeNotation` is called
  on all :class:`~music21.stream.Measure`, :class:`~music21.stream.Part`, and
  :class:`~music21.stream.PartStaff` instances. Copies of those objects are then
  used to transcribe the music. If True, the transcription is done "as is."
  This is useful for strict transcription because sometimes :meth:`~music21.stream.Stream.makeNotation`
  introduces some unwanted artifacts in the music. However, the music needs
  to be organized into measures for transcription to work.
* **debug** (False): If True, a braille-english representation of the music is returned. Useful
  for knowing how the music was interpreted by the braille transcriber.


The rest of the keywords are segment keywords. A segment is "a group of measures occupying
more than one braille line." Music is divided into segments so as to "present the music to
the reader in a meaningful manner and to give him convenient reference points to use in
memorization" (BMTM, 71). Some of these keywords are changed automatically in context.


* **cancelOutgoingKeySig** (True): If True, whenever a key signature change is encountered, the new
  signature should be preceded by the old one.
* **descendingChords** (True): If True, then chords are spelled around the highest note. If False,
  then chords are spelled around the lowest note. This keyword is overriden by any valid clefs
  present in the music.
* **dummyRestLength** (None) For a given positive integer n, adds n "dummy rests" near the beginning
  of a segment. Designed for test purposes, as the rests are used to demonstrate measure division at
  the end of braille lines.
* **maxLineLength** (40): The maximum amount of braille characters that should be present in a line of braille.
* **segmentBreaks** ([]): A list consisting of (measure number, offset start) tuples indicating where the
  music should be broken into segments.
* **showClefSigns** (False): If True, then clef signs are displayed. Since braille does not use clefs and
  staves to represent music, they would instead be shown for referential or historical purposes.
* **showFirstMeasureNumber** (True): If True, then a measure number is shown following the heading
  (if applicable) and preceding the music.
* **showHand** (None): If set to "right" or "left", the corresponding hand sign is shown before the music. In
  keyboard music, the hand signs are shown automatically.
* **showHeading** (True): If True, then a braille heading is created above the initial segment. A heading consists
  of an initial :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`,
  :class:`~music21.tempo.TempoText`, and :class:`~music21.tempo.MetronomeMark`, or any subset thereof. The heading
  is centered above the music automatically.
* **showLongSlursAndTiesTogether** (False), **showShortSlursAndTiesTogether** (False): If False, then the slur on
  either side of the phrase is reduced by the amount that ties are present. If True, then slurs and ties are shown
  together (i.e. the note can have both a slur and a tie).
* **slurLongPhraseWithBrackets** (True): If True, then the slur of a long phrase (4+ consecutive notes) is brailled
  using the bracket slur. If False, the double slur is used instead.
* **suppressOctaveMarks** (True): If True, then all octave marks are suppressed. Designed for test purposes, as
  octave marks were not presented in BMTM until Chapter 7.
* **upperFirstInNoteFingering** (True): If True, then whenever there is a choice fingering (i.e. 5|4), the upper
  number is transcribed before the lower number. If False, the reverse is the case.
"""

from music21 import metadata, stream, tinyNotation, exceptions21
from music21.braille import segment
from music21.ext import six

import re
import unittest

if six.PY3:
    unicode = str # @ReservedAssignment

try:
    from future_builtins import zip
except ImportError: # not 2.6+ or is 3.x
    pass


#------------------------------------------------------------------------------

def objectToBraille(music21Obj, **keywords):
    u"""

    Translates an arbitrary object to braille.

    >>> from music21.braille import translate
    >>> from music21 import tinyNotation
    >>> samplePart = tinyNotation.TinyNotationStream("3/4 C4 D16 E F G# r4 e2.")
    >>> #_DOCS_SHOW samplePart.show()


        .. image:: images/objectToBraille.*
            :width: 700


    >>> print(translate.objectToBraille(samplePart))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    For normal users, you'll just call this, which starts a text editor:


    >>> #_DOCS_SHOW samplePart.show('braille')
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    Other examples:


    >>> from music21 import note
    >>> sampleNote = note.Note("C3")
    >>> print(translate.objectToBraille(sampleNote))
    ⠸⠹

    >>> from music21 import dynamics
    >>> sampleDynamic = dynamics.Dynamic("fff")
    >>> print(translate.objectToBraille(sampleDynamic))
    ⠜⠋⠋⠋
    """
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, **keywords)
    else:
        music21Measure = stream.Measure()
        music21Measure.append(music21Obj)
        keywords['inPlace'] = True
        return measureToBraille(music21Measure, **keywords)

def streamToBraille(music21Stream, **keywords):
    """
    Translates a :class:`~music21.stream.Stream` to braille.
    """

    if isinstance(music21Stream, stream.Part) or isinstance(music21Stream, tinyNotation.TinyNotationStream):
        return partToBraille(music21Stream, **keywords)
    if isinstance(music21Stream, stream.Measure):
        return measureToBraille(music21Stream, **keywords)
    keyboardParts = music21Stream.getElementsByClass(stream.PartStaff)
    if len(keyboardParts) == 2:
        return keyboardPartsToBraille(keyboardParts[0], keyboardParts[1], **keywords)
    if isinstance(music21Stream, stream.Score):
        return scoreToBraille(music21Stream, **keywords)
    if isinstance(music21Stream, stream.Opus):
        return opusToBraille(music21Stream, **keywords)
    raise BrailleTranslateException("Stream cannot be translated to Braille.")

def scoreToBraille(music21Score, **keywords):
    """
    Translates a :class:`~music21.stream.Score` to braille.
    """
    allBrailleLines = []
    for music21Metadata in music21Score.getElementsByClass(metadata.Metadata):
        allBrailleLines.append(metadataToString(music21Metadata))
    for p in music21Score.getElementsByClass(stream.Part):
        braillePart = partToBraille(p, **keywords)
        allBrailleLines.append(braillePart)
    return u"\n".join(allBrailleLines)

def metadataToString(music21Metadata):
    """
    >>> from music21.braille import translate
    >>> from music21 import corpus
    >>> corelli = corpus.parse("corelli")
    >>> corelli.getElementsByClass('Metadata')[0].__class__
    <class 'music21.metadata.Metadata'>
    >>> print(translate.metadataToString(corelli.getElementsByClass('Metadata')[0]))
    Movement Name: [Movement 1]
    Movement Number: 1
    Number: 3
    Title: Church Sonatas, Op. 3: Sonata I
    """
    allBrailleLines = []
    for key in music21Metadata._workIds:
        value = music21Metadata._workIds[key]
        if value is not None:
            n = u" ".join(re.findall(r"([A-Z]*[a-z]+)", key))
            allBrailleLines.append("{0}: {1}".format(n.title(), value))
    return u'\n'.join(sorted(allBrailleLines))

def opusToBraille(music21Opus, **keywords):
    """
    Translates an :class:`~music21.stream.Opus` to braille.
    """
    allBrailleLines = []
    for score in music21Opus.getElementsByClass(stream.Score):
        allBrailleLines.append(scoreToBraille(score, **keywords))
    return u"\n\n".join(allBrailleLines)

def measureToBraille(music21Measure, **keywords):
    """
    Translates a :class:`~music21.stream.Measure` to braille.
    
    >>> p = stream.Part()
    >>> p.append(note.Note('C4', type='whole'))
    >>> p.makeMeasures(inPlace=True)
    >>> p.show('t')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline style=final>    
    >>> print(braille.translate.objectToBraille(p))
    ⠀⠀⠼⠙⠲⠀⠀
    ⠼⠁⠀⠐⠽⠣⠅
    >>> print(braille.translate.measureToBraille(p.measure(1)))
    ⠼⠙⠲⠀⠐⠽⠣⠅
    
    """
    (inPlace, unused_debug) = _translateArgs(**keywords)
    if not 'showHeading' in keywords:
        keywords['showHeading'] = False
    if not 'showFirstMeasureNumber' in keywords:
        keywords['showFirstMeasureNumber'] = False
    measureToTranscribe = music21Measure
    if not inPlace:
        measureToTranscribe = music21Measure.makeNotation(cautionaryNotImmediateRepeat=False)
    music21Part = stream.Part()
    music21Part.append(measureToTranscribe)
    keywords['inPlace'] = True
    return partToBraille(music21Part, **keywords)

def partToBraille(music21Part, **keywords):
    """
    Translates a :class:`~music21.stream.Part` to braille.
    """
    (inPlace, debug) = _translateArgs(**keywords)
    partToTranscribe = music21Part
    if not inPlace:
        partToTranscribe = music21Part.makeNotation(cautionaryNotImmediateRepeat=False)
    allSegments = segment.findSegments(partToTranscribe, **keywords)
    allBrailleText = []
    for brailleSegment in allSegments:
        transcription = brailleSegment.transcribe()
        if not debug:
            allBrailleText.append(transcription)
        else:
            allBrailleText.append(str(brailleSegment))
    return u"\n".join([unicode(bt) for bt in allBrailleText])

def keyboardPartsToBraille(music21PartStaffUpper, music21PartStaffLower, **keywords):
    """
    Translates two :class:`~music21.stream.Part` instances to braille, an upper part and a lower
    part. Assumes that the two parts are aligned and well constructed. Bar over bar format is used.
    """
    (inPlace, debug) = _translateArgs(**keywords)
    upperPartToTranscribe = music21PartStaffUpper
    if not inPlace:
        upperPartToTranscribe = music21PartStaffUpper.makeNotation(cautionaryNotImmediateRepeat=False)
    lowerPartToTranscribe = music21PartStaffLower
    if not inPlace:
        lowerPartToTranscribe = music21PartStaffLower.makeNotation(cautionaryNotImmediateRepeat=False)
    rhSegments = segment.findSegments(upperPartToTranscribe, **keywords)
    lhSegments = segment.findSegments(lowerPartToTranscribe, **keywords)
    allBrailleText = []
    for (rhSegment, lhSegment) in zip(rhSegments, lhSegments):
        bg = segment.BrailleGrandSegment(rhSegment, lhSegment)
        if not debug:
            allBrailleText.append(bg.transcription)
        else:
            allBrailleText.append(str(bg))
    return u"\n".join([unicode(bt) for bt in allBrailleText])


def _translateArgs(**keywords):
#    inPlace = False
#    debug = False
#    if 'inPlace' in keywords:
#        inPlace = keywords['inPlace']
#    if 'debug' in keywords:
#        debug = keywords['debug']
    inPlace = keywords.get('inPlace', False)
    debug = keywords.get('debug', False)
    return (inPlace, debug)

_DOC_ORDER = [objectToBraille]

#------------------------------------------------------------------------------


class BrailleTranslateException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
