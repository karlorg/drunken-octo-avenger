###
This file based on https://github.com/neagle/smartgame, which is
released under the license shown below.  Since it's unclear whether
this file counts as a 'copy or substantial portion' of the original,
this file is made available under the same licence instead of the CC0
dedication applied to the larger project.

---

The MIT License (MIT)

Copyright (c) 2014 Nate Eagle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

###

window.tesuji_charm ?= {}
tesuji_charm = window.tesuji_charm

tesuji_charm.smartgame ?= {}

exports = tesuji_charm.smartgame

exports.parse = (sgf) ->
  "Convert SGF files to a JS object

  @param {string} sgf A valid SGF file
  @see http://www.red-bean.com/sgf/sgf4.html
  @return {object} The SGF file represented as a JS object"
  parse = null
  collection = {}
  sequence = null  # tracks our current position in the object being built
  node = null
  lastPropIdent = null

  parser =
    beginSequence: (sgf) ->
      if not sequence
        sequence = collection
        key = 'gameTrees'
      else if sequence.gameTrees
        key = 'gameTrees'
      else
        key = 'sequences'

      newSequence = { parent: sequence }

      sequence[key] or= []
      sequence[key].push newSequence
      sequence = newSequence

      return parse(sgf.substring(1))

    endSequence: (sgf) ->
      if sequence.parent
        sequence = sequence.parent
      else
        sequence = null
      return parse(sgf.substring(1))

    node: (sgf) ->
      node = {}
      sequence.nodes or= []
      sequence.nodes.push node
      return parse(sgf.substring(1))

    property: (sgf) ->
      # search for the first unescaped ]
      firstPropEnd = sgf.search(/[^\\]\]/) + 1

      # XXX: isn't this always true?  String::search returns an index
      # on success, -1 on failure, which with 1 added will always be
      # >= 0
      if firstPropEnd > -1
        property = sgf.substring 0, firstPropEnd + 1
        propValueBegin = property.indexOf '['
        propIdent = property.substring 0, propValueBegin

        # Point lists don't declare a PropIdent for each PropValue
        # Instead, they should use the last declared property
        # See: http://www.red-bean.com/sgf/sgf4.html#move/pos
        unless propIdent
          propIdent = lastPropIdent
          # if this is the first property in a list of multiple
          # properties, we need to wrap the PropValue in an array
          unless Array.isArray node[propIdent]
            node[propIdent] = [node[propIdent]]

        lastPropIdent = propIdent
        propValue = property.substring propValueBegin + 1, property.length - 1

        # we have no problem parsing PropIdents of any length, but the spec
        # says they should be no longer than two characters.
        #
        # http://www.red-bean.com/sgf/sgf4.html#2.2
        if propIdent.length > 2
          # TODO: what's the best way to issue a warning?
          console.warn (
            "SGF PropIdents should be no longer than two " +
            "characters: #{propIdent}")

        if Array.isArray node[propIdent]
          node[propIdent].push propValue
        else
          node[propIdent] = [propValue]

        return parse(sgf.substring(firstPropEnd+1))
      else
        throw new Error 'malformed SGF'

    # whitespace, tabs, or anything else we don't recognize
    unrecognized: (sgf) ->
      return parse (sgf.substring(1))

  # processes an SGF file character by character
  parse = (sgf) ->
    initial = sgf.substring 0, 1
    return collection unless initial
    type = switch
      when initial == '(' then 'beginSequence'
      when initial == ')' then 'endSequence'
      when initial == ';' then 'node'
      when initial.search(/[A-Z\[]/) != -1 then 'property'
      else 'unrecognized'
    return parser[type] sgf

  return parse sgf

exports.generate = (record) ->
  "Generate an SGF string from a SmartGame Record JS object

  @param {object} record A record object.
  @return {string} The record as a string suitable for saving as an SGF file"
  stringifySequences = (sequences) ->
    contents = ''

    for sequence in sequences
      contents += '('

      # parse all nodes in this sequence
      if sequence.nodes
        for node in sequence.nodes
          nodeString = ';'
          for own property of node
            prop = node[property]
            if Array.isArray(prop)
              prop = prop.join ']['
            nodeString += "#{property}[#{prop}]"
          contents += nodeString

      # call the function we're in recursively for any child sequences
      if sequence.sequences
        contents += stringifySequences sequence.sequences

      contents += ')'

    return contents

  return stringifySequences record.gameTrees
