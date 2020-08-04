# -*- coding: utf-8 -*-
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from redturtle.importer.base.interfaces import IMigrationContextSteps
from redturtle.importer.volto.testing import (
    REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING,  # noqa: E501
)
from zope.component import queryUtility

import unittest

SAMPLE_HTML = """
<p><em>Nulla</em> sit amet est. Morbi mattis <strong>ullamcorper</strong> velit.</p>
<p></p>
<p><a href="http://www.plone.com" data-linktype="external" data-val="http://www.plone.com">this is a link</a></p>
<ul>
<li>one</li>
<li>two</li>
<li>three</li>
</ul>
"""


class TestContentConverter(unittest.TestCase):
    """"""

    layer = REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        # enable blocks behavior
        fti = queryUtility(IDexterityFTI, name="Document")
        behaviors = [x for x in fti.behaviors]
        behaviors.append("volto.blocks")
        fti.behaviors = tuple(behaviors)

        self.document = api.content.create(
            container=self.portal, type="Document", title="Foo"
        )
        self.news = api.content.create(
            container=self.portal, type="News Item", title="News"
        )
        self.converter = IMigrationContextSteps(self.document)

    def test_converter_works_only_where_behavior_is_active(self):
        news = api.content.create(container=self.portal, type="News Item", title="News")
        with self.assertRaises(TypeError):
            IMigrationContextSteps(news)

    def test_document_with_simple_text(self):
        html = "<p>foo</p>"
        self.document.text = RichTextValue(html, "text/html", "text/html")
        self.assertNotEqual(self.document.text, None)
        self.assertEqual(self.document.text.output, html)
        self.assertEqual(self.document.blocks, {})
        self.assertEqual(self.document.blocks_layout, {"items": []})
        self.converter.doSteps()
        blocks = self.document.blocks
        blocks_layout = self.document.blocks_layout
        self.assertEqual(len(blocks.keys()), 2)
        self.assertEqual(len(blocks_layout["items"]), 2)
        block_values = [x for x in blocks.values()]
        self.assertEqual(block_values[0], {"@type": "title"})
        self.assertEqual(block_values[1]["@type"], "text")
        self.assertEqual(block_values[1]["text"]["blocks"][0]["text"], "foo")
