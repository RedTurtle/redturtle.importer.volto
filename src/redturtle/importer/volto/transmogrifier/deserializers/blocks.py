# -*- coding: utf-8 -*-
from collective.volto.blocksfield.interfaces import IBlocksField
from plone.app.textfield.value import RichTextValue
from redturtle.importer.base.interfaces import IDeserializer
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from redturtle.importer.volto.adapters.volto_blocks import ConvertToBlocks
from uuid import uuid4

import six


@implementer(IDeserializer)
@adapter(IBlocksField, Interface)
class BlocksDeserializer(object):
    def __init__(self, field, context):
        self.field = field
        self.context = context

    def __call__(
        self, value, filestore, item, disable_constraints=False, logger=None
    ):
        if not value:
            return {"blocks": {}, "blocks_layout": {"items": []}}

        if isinstance(value, six.string_types) and not value.startswith("<"):
            value = "<p>{}</p>".format(value)
        elif isinstance(value, RichTextValue):
            value = value.raw

        if value == "<p><br></p>":
            value = ""

        try:
            new_value = self.to_draftjs(value)
        except Exception as e:
            logger.error("[NOT DRAFTJS CONVERTED] - {}".format(item["_path"]))
            raise e

        return new_value

    def to_draftjs(self, html):
        if not html:
            return {"blocks": {}, "blocks_layout": {"items": []}}

        converter = ConvertToBlocks(context=self.context)
        html = html.replace("<span> </span>", " ")
        html = converter.fix_headers(html=html)
        html = converter.fix_html(html=html)

        blocks = {}
        blocks_layout = {"items": []}

        result = converter.conversion_tool(html=html)
        result = [x for x in result if not self._is_empty_block(x)]
        for block in result:
            block = self._fix_blocks(block)
            text_uuid = str(uuid4())
            blocks[text_uuid] = block
            blocks_layout["items"].append(text_uuid)
        return {"blocks": blocks, "blocks_layout": blocks_layout}

    def _is_empty_block(self, block):
        block_type = block.get("@type", "")
        if block_type == "text":
            text = block.get("text", {})["blocks"][0].get("text", "")
            if not text:
                return True
        return False

    def _fix_blocks(self, block):
        block_type = block.get("@type", "")
        if block_type == "text":
            entity_map = block.get("text", {}).get("entityMap", {})
            for entity in entity_map.values():
                if entity.get("type") == "LINK":
                    # draftjs set link in "url" but we want handle it in "href"
                    url = entity.get("data", {}).get("url", "")
                    entity["data"]["href"] = url
        return block
