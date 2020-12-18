# -*- coding: utf-8 -*-s
from Products.CMFPlone.utils import safe_unicode
from redturtle.importer.base.interfaces import IMigrationContextSteps
from uuid import uuid4
from zope.interface import implementer
from plone import api

import logging
import lxml
import os
import re
import requests

logger = logging.getLogger(__name__)

draftjs_converter = os.environ.get("DRAFTJS_CONVERTER_URL")

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
            safe_unicode(lxml.html.tostring(c))
            for c in document.iterchildren()
        )

    def fix_html(self, html):
        # cleanup html
        portal_transforms = api.portal.get_tool(name="portal_transforms")
        data = portal_transforms.convertTo(
            "text/x-html-safe", html, mimetype="text/html"
        )
        html = data.getData()

        if not html:
            return ""
        document = lxml.html.fromstring(html)
        root = document
        if root.tag != "div":
            root = root.getparent()
        if not root:
            return ""
        self._extract_img_from_tags(document=document, root=root)
        self._remove_empty_tags(root=root)
        return "".join(
            safe_unicode(lxml.html.tostring(c)) for c in root.iterchildren()
        )

    def _remove_empty_tags(self, root):
        if root is None:
            return
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
            while paragraph.getparent() not in [root, None]:
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
                        img_parent.index(image),
                        lxml.html.builder.SPAN(image.tail),
                    )
                else:
                    paragraph.insert(
                        paragraph.index(image),
                        lxml.html.builder.SPAN(image.tail),
                    )
                image.tail = ""

            # move image before paragraph
            if paragraph.getparent() is None:
                root.insert(root.index(image), lxml.html.builder.P(image))
            else:
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
        if not draftjs_converter:
            raise Exception(
                "DRAFTJS_CONVERTER_URL environment varialbe not set. Unable to convert html to draftjs."  #  noqa
            )
        resp = requests.post(draftjs_converter, data={"html": html})
        if resp.status_code != 200:
            raise Exception(
                "Unable to convert to draftjs this html: {}".format(html)
            )
        return resp.json()["data"]

    def doSteps(self, item={}):
        """
        do something here
        """
        # if getattr(self.context, "blocks", {}):
        #     return
        text = getattr(self.context, "text", None)

        if text:
            text = text.raw
        else:
            text = item.get("text", "")

        if not text:
            return
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

        title_uuid = str(uuid4())
        blocks = {title_uuid: {"@type": "title"}}
        blocks_layout = {"items": [title_uuid]}

        try:
            result = self.conversion_tool(html)
        except Exception:
            logger.error(
                "Failed to convert HTML {}".format(self.context.absolute_url())
            )
            return
        for block in result:
            block = self.fix_blocks(block)
            text_uuid = str(uuid4())
            blocks[text_uuid] = block
            blocks_layout["items"].append(text_uuid)
        self.context.blocks = blocks
        self.context.blocks_layout = blocks_layout
        self.context.text = None
