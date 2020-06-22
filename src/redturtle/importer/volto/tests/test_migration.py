# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plone.protect.authenticator import createToken
from redturtle.importer.volto.testing import (
    REDTURTLE_IMPORTER_VOLTO_DOCKER_FUNCTIONAL_TESTING,  # noqa: E501
)
from zope.component import queryUtility

import unittest


class TestMigration(unittest.TestCase):
    """
    This test suite works in conjunction with a docker image that runs
    redturtle.exporter.base install profile to pre-populate a site with some
    contents: https://github.com/RedTurtle/redturtle.exporter.base/blob/master/src/redturtle/exporter/base/setuphandlers.py
    """

    layer = REDTURTLE_IMPORTER_VOLTO_DOCKER_FUNCTIONAL_TESTING

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

        migration_view = api.content.get_view(
            name="data-migration", context=self.portal, request=self.request
        )
        self.request.form["_authenticator"] = createToken()
        migration_view.do_migrate()

    def test_migration_items_with_blocks(self):
        document = api.content.find(id="first-document")[0].getObject()
        self.assertEqual(document.text, None)
        self.assertNotEqual(document.blocks, {})

        news = api.content.find(id="a-news")[0].getObject()
        self.assertEqual(news.text, None)
        self.assertNotEqual(news.blocks, {})

    def test_migration_collection(self):
        # we don't have collection items
        collections = api.content.find(portal_type="Collection")
        self.assertEqual(len(collections), 0)

        # but migration converts collections into pages with listing block
        collections = api.content.find(id="collection-item")
        self.assertEqual(len(collections), 1)
        collection = collections[0].getObject()
        self.assertNotEqual(collection.blocks, {})
        self.assertEqual(collection.portal_type, "Document")
        listing = [x for x in collection.blocks.values()][1]
        self.assertEqual(listing["@type"], "listing")
        self.assertEqual(
            listing["query"],
            [
                {
                    "i": "portal_type",
                    "o": "plone.app.querystring.operation.selection.any",
                    "v": ["Document", "News Item"],
                }
            ],
        )

    def test_migration_folders(self):
        # we don't have folders
        folders = api.content.find(portal_type="Folder")
        self.assertEqual(len(folders), 0)

        # but migration converts folders into pages with listing block
        folders = api.content.find(id="folder-foo")
        self.assertEqual(len(folders), 1)
        folder = folders[0].getObject()
        self.assertNotEqual(folder.blocks, {})
        self.assertEqual(folder.portal_type, "Document")
        listing = [x for x in folder.blocks.values()][1]
        self.assertEqual(listing["@type"], "listing")
        self.assertEqual(
            listing["query"],
            [
                {
                    "i": "path",
                    "o": "plone.app.querystring.operation.string.path",
                    "v": "{}::1".format(folder.UID()),
                }
            ],
        )
        self.assertEqual(listing["sort_on"], "getObjPositionInParent")
        self.assertEqual(listing["b_size"], "30")
        self.assertEqual(folder.keys(), ["second-document"])

    def test_migration_default_views(self):
        """
        in origin we have:
        - folder-bar
          - folder-baz
            - third-document
            - example-image
            - example-file

        and third-document is the default view
        """
        folder = api.content.get("/plone/folder-bar/folder-baz")
        self.assertNotIn("third-document", folder.keys())
        self.assertEqual(len(folder.keys()), 2)
        self.assertEqual(folder.portal_type, "Document")
        self.assertNotEqual(folder.blocks, {})
