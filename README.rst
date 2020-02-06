.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

========================
Redturtle Importer Volto
========================

Plugin for `redturtle.importer.base`__ to migrate old site into a new Volto-enabled site.

__ https://github.com/RedTurtle/redturtle.importer.base

Features
--------

There is a new adapter for **redturtle.importer.base** for content-types with **volto.blocks** enabled behavior
that converts rich text from html (TinyMce) to json (DraftJs/blocks).

Text converter
--------------

To convert text from HTML to json we use the official DraftJs available library.

This library is a javascript library, so we need to run a python subprocess that runs a
javascript file that take an HTML input and generates a proper json file.
The script is located in `draftjs` folder and is called in `volto_blocks_converter` section.

To run this code you need a quite recent `node` version (>= 10.x) installed locally.

nvm is not an option right now because we had some problems running nvm in python subprocess.


Installation
------------

Install redturtle.importer.volto by adding it to your buildout::

    [buildout]

    ...

    eggs =
        redturtle.importer.volto


and then running ``bin/buildout``

You don't have to install it. In this way, after the data migration, you can
remove it from the buildout and everything is clean.

You also need to install javascript dependencies (see `Text converter` section)::

    > yarn


Contribute
----------

- Issue Tracker: https://github.com/collective/redturtle.importer.volto/issues
- Source Code: https://github.com/collective/redturtle.importer.volto


Support
-------

If you are having issues, please let us know.
We have a mailing list located at: project@example.com


License
-------

The project is licensed under the GPLv2.
