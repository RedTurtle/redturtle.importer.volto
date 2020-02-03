# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from redturtle.importer.volto.sections.to_volto_blocks import ToVoltoBlocks
from redturtle.importer.volto.testing import (
    REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING,  # noqa: E501
)

import unittest

SAMPLE_HTML = '''
<p><em>Nulla</em> sit amet est. Morbi mattis <strong>ullamcorper</strong> velit.</p>
<p></p>
<p><a href="http://www.plone.com" data-linktype="external" data-val="http://www.plone.com">this is a link</a></p>
<ul>
<li>one</li>
<li>two</li>
<li>three</li>
</ul>
'''


class TestDraftjsConverter(unittest.TestCase):
    """"""

    layer = REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.tool = ToVoltoBlocks(
            transmogrifier=None, name=None, options={}, previous=None
        )

    def test_simple_text(self):
        result = self.tool.conversion_tool(html='<p>foo</p>')
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], 'foo')
        self.assertEqual(entityMap, {})

    def test_text_with_inline_styles(self):

        result = self.tool.conversion_tool(
            html='<p><em>foo</em> bar <strong>baz</strong></p>'
        )
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['text'], 'foo bar baz')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(
            p['inlineStyleRanges'],
            [
                {'length': 3, 'offset': 0, 'style': 'ITALIC'},
                {'length': 3, 'offset': 8, 'style': 'BOLD'},
            ],
        )
        self.assertEqual(entityMap, {})

    def test_text_empty(self):
        result = self.tool.conversion_tool(html='<p></p>')
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], '')
        self.assertEqual(entityMap, {})

    def test_text_with_links(self):
        result = self.tool.conversion_tool(
            html='<p><a href="http://www.plone.com" data-linktype="external" data-val="http://www.plone.com">this is a link</a></p>'  # noqa
        )
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['text'], 'this is a link')
        self.assertEqual(
            p['entityRanges'], [{'key': 0, 'length': 14, 'offset': 0}]
        )
        self.assertEqual(
            entityMap,
            {
                '0': {
                    'data': {
                        'data-linktype': 'external',
                        'data-val': 'http://www.plone.com',
                        'url': 'http://www.plone.com',
                    },
                    'mutability': 'MUTABLE',
                    'type': 'LINK',
                }
            },
        )

    def test_text_with_callout(self):
        result = self.tool.conversion_tool(
            html='<p class="callout"><span>callout!</span></p>'
        )
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], 'callout!')
        self.assertEqual(p['type'], 'callout')
        self.assertEqual(entityMap, {})

    def test_text_with_strong(self):
        result = self.tool.conversion_tool(html='<p><strong>foo</strong></p>')
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], 'foo')
        self.assertEqual(
            p['inlineStyleRanges'],
            [{'offset': 0, 'length': 3, 'style': 'BOLD'}],
        )
        self.assertEqual(entityMap, {})

    def test_text_with_code(self):
        result = self.tool.conversion_tool(html='<p><code>foo</code></p>')
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], 'foo')
        self.assertEqual(
            p['inlineStyleRanges'],
            [{'offset': 0, 'length': 3, 'style': 'CODE'}],
        )
        self.assertEqual(entityMap, {})

    def test_text_with_blockquote(self):
        result = self.tool.conversion_tool(
            html='<blockquote><p>foo</p></blockquote>'
        )
        self.assertEqual(len(result), 1)
        p = result[0]['text']['blocks'][0]
        entityMap = result[0]['text']['entityMap']
        self.assertEqual(result[0]['@type'], 'text')
        self.assertEqual(p['entityRanges'], [])
        self.assertEqual(p['text'], 'foo')
        self.assertEqual(p['type'], 'blockquote')
        self.assertEqual(entityMap, {})

    def test_text_with_image(self):
        result = self.tool.conversion_tool(
            html='<p><img alt="" src="https://www.plone.org/logo.png" class="image-right" data-linktype="image"/></p>'  # noqa
        )
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block['@type'], 'image')
        self.assertEqual(block['align'], 'right')
        self.assertEqual(block['url'], 'https://www.plone.org/logo.png')

        result = self.tool.conversion_tool(
            html='<p><img alt="" src="https://www.plone.org/logo.png" class="image-inline" data-linktype="image"/></p>'  # noqa
        )
        block = result[0]
        self.assertEqual(block['align'], 'full')

    def test_text_with_multiple_items(self):
        result = self.tool.conversion_tool(html=SAMPLE_HTML)
        self.assertEqual(len(result), 4)

    def test_text_with_table(self):
        html = '''
        <table border="1">
            <tbody>
                <tr>
                    <td><strong>foo</strong></td>
                    <td><strong>bar</strong></td>
                    <td>baz</td>
                </tr>
            </tbody>
        </table>
        '''
        result = self.tool.conversion_tool(html=html)
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block['@type'], 'table')
        rows = block['table']['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]['cells']), 3)
        self.assertEqual(rows[0]['cells'][0]['type'], 'data')
        self.assertEqual(
            rows[0]['cells'][0]['value']['blocks'][0]['text'], 'foo'
        )
