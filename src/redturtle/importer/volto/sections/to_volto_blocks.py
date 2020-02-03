# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from Products.CMFPlone.utils import safe_unicode
from urllib.parse import urlparse
from uuid import uuid4
from zope.interface import provider
from zope.interface import implementer

import json
import lxml
import logging
import os
import tempfile
import subprocess

logger = logging.getLogger(__name__)


@implementer(ISection)
@provider(ISectionBlueprint)
class ToVoltoBlocks(object):
    """ """

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.base = options.get("base", "")
        self.tool_path = options.get("tool_path", os.getcwd())
        self.previous = previous
        self.context = getattr(transmogrifier, 'context', None)
        self.types = options.get('types-to-convert', [])

        # if "path-key" in options:
        #     pathkeys = options["path-key"].splitlines()
        # else:
        #     pathkeys = defaultKeys(options["blueprint"], name, "path")
        # self.pathkey = Matcher(*pathkeys)

    def fix_headers(self, html):
        document = lxml.html.fromstring(html)

        # https://codepen.io/tomhodgins/pen/ybgMpN
        selector = '//*[substring-after(name(), "h") >= 4]'
        for header in document.xpath(selector):
            header.tag = 'h3'
        if document.tag != 'div':
            return lxml.html.tostring(document)
        return ''.join(
            safe_unicode(lxml.html.tostring(c))
            for c in document.iterchildren()
        )

    def outline(self, img):
        return ' > '.join(
            [
                '{0}(text)'.format(p.tag)
                if p.text and p.text.strip()
                else p.tag
                for p in img.iterancestors()
            ][::-1]
            + ['img']
        )

    def extract_img_from_tags(self, html):
        document = lxml.html.fromstring(html)
        root = document
        if root.tag != 'div':
            root = root.getparent()
        for image in document.xpath('//img'):
            logger.info("Image outline: {}".format(self.outline(image)))

            # Get the current paragraph
            paragraph = image.getparent()
            while paragraph.getparent() != root:
                paragraph = paragraph.getparent()
            # Get the current paragraph

            # Deal with images with links
            img_parent = image.getparent()
            if img_parent.tag == 'a':
                image.attrib['data-href'] = img_parent.attrib.get('href', '')
            # Deal with images with links

            # Move image to a new paragraph before current
            root.insert(
                root.index(paragraph),
                lxml.html.builder.P(image),  # Wrap with a paragraph
            )
            # Move image to a new paragraph before current

            # clenup empty tags
            text = ''
            if img_parent.text is not None:
                text = img_parent.text.strip()
            while len(img_parent.getchildren()) == 0 and text == '':
                parent = img_parent.getparent()
                parent.remove(img_parent)
                img_parent = parent
                text = ''
                if img_parent.text is not None:
                    text = img_parent.text.strip()
            # clenup empty tags

        return ''.join(
            safe_unicode(lxml.html.tostring(c)) for c in root.iterchildren()
        )

    def fix_url(self, data, type_, parent={}):
        for k, v in list(data.items()):
            if isinstance(v, dict):
                data[k] = self.fix_url(v, type_, parent=data)
                continue
            if k not in ["src", "url"] or not v.startswith("http://nohost"):
                continue
            url = urlparse(v).path
            url = '/' + '/'.join(url.split('/')[2::1])
            if parent.get('type', '') == 'IMAGE' or type_ == 'image':
                if "@@images" in url:
                    url = url.split("@@images")[0]
                    url += "@@images/image/large"
                else:
                    url += "/@@images/image/large"
            data[k] = url
        return data

    def conversion_tool(self, html):
        fd, filename = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(safe_unicode(html))
            subprocess.call(
                [
                    'yarn',
                    '--silent',
                    'convert-to-draftjs-debug'
                    if os.environ.get('DEBUG', False)
                    else 'convert-to-draftjs',
                    filename,
                ],
                cwd=self.tool_path,
            )
            with open(filename, 'r') as tmp:
                result = json.load(tmp)
        finally:
            os.remove(filename)
        return result

    def __iter__(self):
        for item in self.previous:
            if (
                not item.get("text", False)
                or item.get('_type', '') not in self.types
            ):
                yield item
                continue

            html = item["text"]
            html = self.fix_headers(html)
            html = self.extract_img_from_tags(html)

            title_uuid = str(uuid4())
            item['blocks'] = {title_uuid: {"@type": "title"}}
            item['blocks_layout'] = {"items": [title_uuid]}

            try:
                result = self.conversion_tool(html)
            except (ValueError, UnicodeDecodeError):
                logger.error("Failed to convert HTML {}".format(item["_path"]))
                yield item
                continue

            for paragraph in result:
                paragraph = self.fix_url(paragraph, type_=paragraph['@type'])

                text_uuid = str(uuid4())
                item['blocks'][text_uuid] = paragraph
                item['blocks_layout']["items"].append(text_uuid)
            item['text'] = None
            yield item
