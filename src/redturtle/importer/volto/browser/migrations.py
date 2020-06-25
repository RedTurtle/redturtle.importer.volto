# -*- coding: utf-8 -*-
from copy import deepcopy
from itertools import groupby
from redturtle.importer.base.browser.migrations import RedTurtlePlone5MigrationMain
from plone import api
from urllib.parse import urlparse


class VoltoMigrationMain(RedTurtlePlone5MigrationMain):
    """
    """

    def scripts_post_migration(self):
        super(VoltoMigrationMain, self).scripts_post_migration()
        self.fix_volto_references()

    def fix_volto_references(self):
        brains = api.content.find(object_provides="plone.restapi.behaviors.IBlocks")
        for brain in brains:
            item = brain.getObject()
            blocks = getattr(item, "blocks", {})
            if not blocks:
                continue
            item.blocks = self.fix_references_in_blocks(
                item=item, data=deepcopy(blocks)
            )

    def path2uuid(self, is_image, path, url):
        try:
            ref_obj = api.content.get(path)
        except Exception:
            return ""
        if not ref_obj or ref_obj == api.portal.get():
            return ""
        if is_image:
            return "resolveuid/{uid}/@@images/{scale}".format(
                uid=ref_obj.UID(), scale=url.split("@@images/")[1]
            )
        else:
            try:
                return "resolveuid/{}".format(ref_obj.UID())
            except AttributeError:
                return ""

    def fix_references_in_blocks(self, item, data, parent={}):
        for k, v in list(data.items()):
            if isinstance(v, dict):
                data[k] = self.fix_references_in_blocks(item=item, data=v, parent=data)
            if k not in ["src", "url"] or "resolveuid" in v:
                continue
            is_image = "@@images" in v
            url_parsed = urlparse(v)
            path = url_parsed.path
            if is_image:
                path = path.split("@@images")[0]
            scheme = url_parsed.scheme
            if scheme != "":
                resolveuid_url = self.path2uuid(is_image=is_image, path=path, url=v)
                if resolveuid_url:
                    data[k] = resolveuid_url
                continue

            parent_levels = 0
            for key, group in groupby(path.split("../")):
                if key == "":
                    parent_levels = len(list(group))
            item_path = (
                parent_levels
                and item.getPhysicalPath()[:-parent_levels]
                or item.getPhysicalPath()
            )
            path = "/".join(item_path + tuple([x for x in path.split("../") if x]))

            resolveuid_url = self.path2uuid(is_image=is_image, path=path, url=v)
            if resolveuid_url:
                data[k] = resolveuid_url
        return data
