# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from redturtle.importer.volto.sections.to_volto_blocks import ToVoltoBlocks
from redturtle.importer.volto.testing import (
    REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING,  # noqa: E501
)

import unittest


class TestDraftjsConverter(unittest.TestCase):
    """"""

    layer = REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_simple_text(self):
        section = ToVoltoBlocks(
            transmogrifier=None, name=None, options={}, previous=None
        )
        result = section.conversion_tool(html='<p>foo</p>')
        self.assertEqual(len(result), 1)
        p = result[0]
        self.assertEqual(p['@type'], 'text')
        self.assertEqual(p['text']['blocks'][0]['text'], 'foo')
