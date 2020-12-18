# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone import api
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


class TestDraftjsConverter(unittest.TestCase):
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
        self.converter = IMigrationContextSteps(self.document)

    def test_converter_simple_text(self):
        result = self.converter.conversion_tool(html="<p>foo</p>")
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "foo")
        self.assertEqual(entityMap, {})

    def test_converter_text_with_inline_styles(self):

        result = self.converter.conversion_tool(
            html="<p><em>foo</em> bar <strong>baz</strong></p>"
        )
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["text"], "foo bar baz")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(
            p["inlineStyleRanges"],
            [
                {"length": 3, "offset": 0, "style": "ITALIC"},
                {"length": 3, "offset": 8, "style": "BOLD"},
            ],
        )
        self.assertEqual(entityMap, {})

    def test_converter_text_empty(self):
        result = self.converter.conversion_tool(html="<p></p>")
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "")
        self.assertEqual(entityMap, {})

    def test_converter_text_with_links(self):
        result = self.converter.conversion_tool(
            html='<p><a href="http://www.plone.com" data-linktype="external" data-val="http://www.plone.com">this is a link</a></p>'  # noqa
        )
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["text"], "this is a link")
        self.assertEqual(
            p["entityRanges"], [{"key": 0, "length": 14, "offset": 0}]
        )
        self.assertEqual(
            entityMap,
            {
                "0": {
                    "data": {
                        "data-linktype": "external",
                        "data-val": "http://www.plone.com",
                        "url": "http://www.plone.com",
                    },
                    "mutability": "MUTABLE",
                    "type": "LINK",
                }
            },
        )

    def test_converter_text_with_callout(self):
        result = self.converter.conversion_tool(
            html='<p class="callout"><span>callout!</span></p>'
        )
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "callout!")
        self.assertEqual(p["type"], "callout")
        self.assertEqual(entityMap, {})

    def test_converter_text_with_strong(self):
        result = self.converter.conversion_tool(
            html="<p><strong>foo</strong></p>"
        )
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "foo")
        self.assertEqual(
            p["inlineStyleRanges"],
            [{"offset": 0, "length": 3, "style": "BOLD"}],
        )
        self.assertEqual(entityMap, {})

    def test_converter_text_with_code(self):
        result = self.converter.conversion_tool(html="<p><code>foo</code></p>")
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "foo")
        self.assertEqual(
            p["inlineStyleRanges"],
            [{"offset": 0, "length": 3, "style": "CODE"}],
        )
        self.assertEqual(entityMap, {})

    def test_converter_text_with_blockquote(self):
        result = self.converter.conversion_tool(
            html="<blockquote><p>foo</p></blockquote>"
        )
        self.assertEqual(len(result), 1)
        p = result[0]["text"]["blocks"][0]
        entityMap = result[0]["text"]["entityMap"]
        self.assertEqual(result[0]["@type"], "text")
        self.assertEqual(p["entityRanges"], [])
        self.assertEqual(p["text"], "foo")
        self.assertEqual(p["type"], "blockquote")
        self.assertEqual(entityMap, {})

    def test_converter_text_with_image(self):
        result = self.converter.conversion_tool(
            html='<p><img alt="" src="https://www.plone.org/logo.png" class="image-right" data-linktype="image"/></p>'  # noqa
        )
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block["@type"], "image")
        self.assertEqual(block["align"], "right")
        self.assertEqual(block["url"], "https://www.plone.org/logo.png")

        result = self.converter.conversion_tool(
            html='<p><img alt="" src="https://www.plone.org/logo.png" class="image-inline" data-linktype="image"/></p>'  # noqa
        )
        block = result[0]
        self.assertEqual(block["align"], "center")

    def test_converter_insert_images_in_separate_tags(self):
        html = '<p><img src="/image.png"/>Some text</p>'
        result = self.converter.fix_html(html=html)
        self.assertEqual(
            result,
            '<p><img src="/image.png"></p><p><span>Some text</span></p>',
        )

        converted = self.converter.conversion_tool(result)
        self.assertEqual(len(converted), 2)
        image = converted[0]
        text = converted[1]

        self.assertEqual(image["@type"], "image")
        self.assertEqual(image["url"], "/image.png")
        self.assertEqual(text["@type"], "text")
        self.assertEqual(text["text"]["blocks"][0]["text"], "Some text")

    def test_converter_split_image_tag_correctly(self):
        html = '<p>Some text<img src="/image.png"/>other text</p>'
        result = self.converter.fix_html(html=html)
        self.assertEqual(
            result,
            '<p><img src="/image.png"></p><p>Some text<span>other text</span></p>',
        )

        html1 = '<p>Some text <span>foo</span><img src="/image.png"/><b>other</b> funny <b>text</b></p>'
        result = self.converter.fix_html(html=html1)
        self.assertEqual(
            result,
            '<p><img src="/image.png"></p><p>Some text <span>foo</span><b>other</b> funny <b>text</b></p>',
        )

    def test_converter_insert_images_in_separate_tags_and_keep_text(self):
        html = '<p><img src="/image.png"/>foo <strong>BAR</strong>, baz</p>'
        result = self.converter.fix_html(html=html)
        self.assertEqual(
            result,
            '<p><img src="/image.png"></p><p><span>foo </span><strong>BAR</strong>, baz</p>',
        )

        converted = self.converter.conversion_tool(result)
        self.assertEqual(len(converted), 2)
        image = converted[0]
        text = converted[1]

        self.assertEqual(image["@type"], "image")
        self.assertEqual(image["url"], "/image.png")
        self.assertEqual(text["@type"], "text")
        self.assertEqual(text["text"]["blocks"][0]["text"], "foo BAR, baz")
        self.assertEqual(
            text["text"]["blocks"][0]["inlineStyleRanges"],
            [{"length": 3, "offset": 4, "style": "BOLD"}],
        )

    def test_converter_do_not_add_img_size_if_scale_not_present(self):
        html = '<p><img src="http://www.foo.com/img.png"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertNotIn("size", image.keys())

        html = '<p><img src="resolveuid/qwertyuiop"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertNotIn("size", image.keys())

    def test_converter_add_img_size_if_scale_is_present(self):
        html = '<p><img src="resolveuid/foo/@@images/image/mini"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertIn("size", image.keys())

        html = '<p><img src="resolveuid/foo/image_mini"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertIn("size", image.keys())

    def test_converter_add_img_size_l_if_scale_is_large(self):
        html = '<p><img src="resolveuid/foo/@@images/image/large"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertEqual(image["size"], "l")

        html = '<p><img src="resolveuid/foo/image_large"/></p>'
        converted = self.converter.conversion_tool(html)

        self.assertEqual(len(converted), 1)
        image = converted[0]

        self.assertEqual(image["size"], "l")

    def test_converter_add_img_size_s_if_scale_is_thumb_or_tile(self):
        examples = [
            '<p><img src="resolveuid/foo/@@images/image/thumb"/></p>',
            '<p><img src="resolveuid/foo/@@images/image/tile"/></p>',
            '<p><img src="resolveuid/foo/image_thumb"/></p>',
            '<p><img src="resolveuid/foo/image_tile"/></p>',
        ]
        for html in examples:
            converted = self.converter.conversion_tool(html)

            self.assertEqual(len(converted), 1)
            image = converted[0]

            self.assertEqual(image["size"], "s")

    def test_converter_add_img_size_m_as_default(self):
        examples = [
            '<p><img src="resolveuid/foo/@@images/image/original"/></p>',
            '<p><img src="resolveuid/foo/@@images/image/preview"/></p>',
            '<p><img src="resolveuid/foo/@@images/image/mini"/></p>',
            '<p><img src="resolveuid/foo/@@images/image/foo"/></p>',
            '<p><img src="resolveuid/foo/image_original"/></p>',
            '<p><img src="resolveuid/foo/image_preview"/></p>',
            '<p><img src="resolveuid/foo/image_mini"/></p>',
            '<p><img src="resolveuid/foo/image_foo"/></p>',
        ]
        for html in examples:
            converted = self.converter.conversion_tool(html)

            self.assertEqual(len(converted), 1)
            image = converted[0]

            self.assertEqual(image["size"], "m")

    def test_converter_text_with_multiple_items(self):
        result = self.converter.conversion_tool(html=SAMPLE_HTML)
        self.assertEqual(len(result), 4)

    def test_converter_text_with_table(self):
        html = """
        <table border="1">
            <tbody>
                <tr>
                    <td><strong>foo</strong></td>
                    <td><strong>bar</strong></td>
                    <td>baz</td>
                </tr>
            </tbody>
        </table>
        """
        result = self.converter.conversion_tool(html=html)
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block["@type"], "table")
        rows = block["table"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["cells"]), 3)
        self.assertEqual(rows[0]["cells"][0]["type"], "data")
        self.assertEqual(
            rows[0]["cells"][0]["value"]["blocks"][0]["text"], "foo"
        )

    def test_converter_remove_empty_tags_from_html(self):
        self.assertEqual(
            self.converter.fix_html(html="<p>Foo</p>"), "<p>Foo</p>"
        )
        self.assertEqual(self.converter.fix_html(html="<p> </p>"), "")
        self.assertEqual(
            self.converter.fix_html(html="<p><strong><br /></strong></p>"),
            "<p><strong><br></strong></p>",
        )
        self.assertEqual(self.converter.fix_html(html="<p><i> </i></p>"), "")
        self.assertEqual(
            self.converter.fix_html(html="<p><strong> </strong></p>"), ""
        )
        self.assertEqual(
            self.converter.fix_html(html="<p><i><br /></i></p>"),
            "<p><i><br></i></p>",
        )
        self.assertEqual(
            self.converter.fix_html(html='<p><img src="/image.png"/></p>'),
            '<p><img src="/image.png"></p>',
        )
        self.assertEqual(self.converter.fix_html(html="<i>"), "")

    def test_converter_generate_draftjs_without_empty_tags(self):
        html = """
        <p>Foo</p>
        <p> </p>
        <p><strong><br /></strong></p>
        <p><i> </i></p>
        <p><strong> </strong></p>
        <p> </p>
        <p><i><br /></i></p>
        <i>
        """
        result = self.converter.conversion_tool(html=html)
        self.assertEqual(len(result), 8)

    def test_converter_embed_yt_video(self):
        html = """
        <iframe src="https://www.youtube.com/embed/VASywEuqFd8"></iframe>
        """
        result = self.converter.conversion_tool(html=html)
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block["@type"], "video")
        self.assertEqual(block["url"], "https://youtu.be/VASywEuqFd8")

    def test_converter_iframe_block(self):
        html = '<iframe src="https://foo/bar" width="200"></iframe>'
        result = self.converter.conversion_tool(html=html)
        self.assertEqual(len(result), 1)
        block = result[0]
        self.assertEqual(block["@type"], "html")
        self.assertEqual(block["html"], html)

    def test_converter_cleanup_nasty_html(self):
        result = self.converter.fix_html(
            html="<script>asdad</script><p>Some text</p>"
        )
        self.assertEqual(result, "<p>Some text</p>")

        result = self.converter.fix_html(
            html="<html><head><script>asdad</script></head><body><p>Some text</p></body></html>"  # noqa
        )
        self.assertEqual(result, "<p>Some text</p>")
