# -*- coding: utf-8 -*-
from collective.volto.blocksfield.interfaces import IBlocksField
from design.plone.contenttypes.upgrades.draftjs_converter import to_draftjs
from plone.app.textfield.value import RichTextValue
from redturtle.importer.base.interfaces import IDeserializer
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer

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

        if isinstance(value, six.string_types):
            value = "<p>{}</p>".format(value)
        elif isinstance(value, RichTextValue):
            value = value.raw

        if value == "<p><br></p>":
            value = ""

        try:
            new_value = to_draftjs(value)
        except Exception as e:
            logger.error("[NOT DRAFTJS CONVERTED] - {}".format(item["_path"]))
            raise e

        return new_value
