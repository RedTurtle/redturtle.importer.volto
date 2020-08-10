.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

========================
Redturtle Importer Volto
========================

Plugin for `redturtle.importer.base`__ to migrate old site into a new Volto-enabled site.

__ https://github.com/RedTurtle/redturtle.importer.base

Features
========

There is a new adapter for **redturtle.importer.base** for content-types with **volto.blocks** enabled behavior
that converts rich text from html (TinyMce) to json (DraftJs/blocks).

HTML to DraftJs converter
=========================

For content-types with blocks enabled, we need to convert old-style HTML text to a DraftJs compatible data structure.

The best library to do this, is the officiale one that is only available for Javascript.

For that reason, to convert HTML we need to connect to an external tool: https://github.com/RedTurtle/draftjs-converter

This is a nodejs rest api that accept some html and returns its DraftJs converted version.

To use this api, we need to set an environment variable with its address in our buildout::

    environment-vars +=
        ...
        DRAFTJS_CONVERTER_URL http://localhost:3000/html_converter


Blocks conversions
==================

Every piece of a RichText value should be converted into a Volto block element.

Some pieces can be converted into a specific block (for example tables, images, embed items).
Other standard html elements are converted into a *text* block that contains a DraftJs data structure.

We made some assumption when converting text into blocks.

Every paragraph is a new block
------------------------------

This allows editors to move text, insert elements between paragraphs, etc.


Images are wrapped into a separate paragraph
--------------------------------------------

Before launching the conversion tool, we wrap every image into a separate paragraph.

In this way we can handle them as an "image block" in Volto.

Image sizes conversion
----------------------

In Plone images in text can have also a miniature (images scales in Plone).

In Volto, right now, there are only 3 available sizes (S, M, L), so we mapped plone scales into these 3 sizes.


Types conversion
================

If a content-type have **volto.blocks** behavior enabled and a **text** field, that field will be converted in blocks.

**Collection** content-types will be converted into a **Document** with a **listing block** with its criteria filters.

**Folders** with a default view will be converted into a **Document** content-type with these rules for its blocks:

- If default view is a **Collection** content-type, we create a **listing block** with its criteria filters.
- If default view is a **Document** or **News Item**, we convert its text into blocks.
- If the folder doesn't have a default item as view, we create a **listing block** that shows first level contents.


Installation
============

Install redturtle.importer.volto by adding it to your buildout::

    [buildout]

    ...

    eggs =
        redturtle.importer.volto


and then running ``bin/buildout``

You don't have to install it. In this way, after the data migration, you can
remove it from the buildout and everything is clean.


Contribute
----------

- Issue Tracker: https://github.com/collective/redturtle.importer.volto/issues
- Source Code: https://github.com/collective/redturtle.importer.volto


Credits
-------

This product has been developed with some help from

.. image:: https://kitconcept.com/logo.svg
   :alt: kitconcept
   :width: 300
   :height: 80
   :target: https://kitconcept.com/

License
-------

The project is licensed under the GPLv2.
