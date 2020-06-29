# -*- coding: utf-8 -*-s
from App.Common import package_home
from Products.CMFPlone.utils import safe_unicode
from redturtle.importer.base.interfaces import IMigrationContextSteps
from uuid import uuid4
from zope.interface import implementer

import json
import logging
import lxml
import os
import re
import subprocess
import tempfile

logger = logging.getLogger(__name__)

RESOLVEUID_RE = re.compile(
    r"""(['"]resolveuid/)(.*?)(['"])""", re.IGNORECASE | re.DOTALL
)


@implementer(IMigrationContextSteps)
class ConvertToBlocks(object):
    """
    Convert text from HTML to DraftJs compatibile json and set blocks fields
    """

    def __init__(self, context):
        self.context = context

    def fix_headers(self, html):
        document = lxml.html.fromstring(html)

        # https://codepen.io/tomhodgins/pen/ybgMpN
        selector = '//*[substring-after(name(), "h") >= 4]'
        for header in document.xpath(selector):
            header.tag = "h3"
        if document.tag != "div":
            return lxml.html.tostring(document)
        return "".join(
            safe_unicode(lxml.html.tostring(c)) for c in document.iterchildren()
        )

    def fix_html(self, html):
        document = lxml.html.fromstring(html)
        root = document
        if root.tag != "div":
            root = root.getparent()
        self._extract_img_from_tags(document=document, root=root)
        self._remove_empty_tags(root=root)
        return "".join(safe_unicode(lxml.html.tostring(c)) for c in root.iterchildren())

    def _remove_empty_tags(self, root):
        if root.tag in ["br", "img", "iframe", "embed", "video"]:
            # it's a self-closing tag
            return

        children = root.getchildren()
        if not children:
            if root.text in [None, "", "\xa0", " ", "\r\n"]:
                # empty element
                root.getparent().remove(root)
            return
        for child in children:
            self._remove_empty_tags(root=child)
        if not root.getchildren():
            # root had empty children that has been removed
            root.getparent().remove(root)

    def _extract_img_from_tags(self, document, root):
        for image in document.xpath("//img"):
            # Get the current paragraph
            paragraph = image.getparent()
            while paragraph.getparent() != root:
                paragraph = paragraph.getparent()
            # Get the current paragraph

            # Deal with images with links
            img_parent = image.getparent()
            if img_parent.tag == "a":
                image.attrib["data-href"] = img_parent.attrib.get("href", "")
            # Deal with images with links

            # If image has a tail, insert a new span to replace it
            if image.tail:
                if img_parent != paragraph:
                    img_parent.insert(
                        img_parent.index(image), lxml.html.builder.SPAN(image.tail)
                    )
                else:
                    paragraph.insert(
                        paragraph.index(image), lxml.html.builder.SPAN(image.tail)
                    )
                image.tail = ""

            # move image before paragraph
            root.insert(root.index(paragraph), lxml.html.builder.P(image))

            # clenup empty tags
            text = ""
            if img_parent.text is not None:
                text = img_parent.text.strip()
            while len(img_parent.getchildren()) == 0 and text == "":
                parent = img_parent.getparent()
                parent.remove(img_parent)
                img_parent = parent
                text = ""
                if img_parent.text is not None:
                    text = img_parent.text.strip()
            # clenup empty tags

    def fix_blocks(self, block):
        block_type = block.get("@type", "")
        if block_type == "text":
            entity_map = block.get("text", {}).get("entityMap", {})
            for entity in entity_map.values():
                if entity.get("type") == "LINK":
                    # draftjs set link in "url" but we want handle it in "href"
                    url = entity.get("data", {}).get("url", "")
                    entity["data"]["href"] = url
        return block

    def conversion_tool(self, html):
        fd, filename = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "w") as tmp:
                tmp.write(safe_unicode(html))
            subprocess.call(
                [
                    "yarn",
                    "--silent",
                    "convert-to-draftjs-debug"
                    if os.environ.get("DEBUG", False)
                    else "convert-to-draftjs",
                    filename,
                ],
                cwd=package_home(globals()),
            )
            with open(filename, "r") as tmp:
                result = json.load(tmp)
        finally:
            os.remove(filename)
        return result

    def doSteps(self, item={}):
        """
        do something here
        """
        text = getattr(self.context, "text", None)

        if text:
            text = text.raw
        else:
            text = item.get("text", "")

        if not text:
            return ""

        try:
            html = self.fix_headers(text)
        except ValueError:
            logger.warning(
                "Unable to parse html for {}. Skipping.".format(
                    self.context.absolute_url()
                )
            )
            return
        html = self.fix_html(html)
        blocks = self.context.blocks
        blocks_layout = self.context.blocks_layout
        if not blocks:
            # add title as default. blocks can be already populated by
            # redturtle.importer.volto.voltomappings step
            title_uuid = str(uuid4())
            blocks = {title_uuid: {"@type": "title"}}
            blocks_layout = {"items": [title_uuid]}
        try:
            result = self.conversion_tool(html)
        except (ValueError, UnicodeDecodeError):
            logger.error(
                "Failed to convert HTML {}".format(self.context.absolute_url())
            )

        for block in result:
            block = self.fix_blocks(block)
            text_uuid = str(uuid4())
            blocks[text_uuid] = block
            blocks_layout["items"].append(text_uuid)
        self.context.blocks = blocks
        self.context.blocks_layout = blocks_layout
        self.context.text = None
