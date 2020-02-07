# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plone.protect.authenticator import createToken
from redturtle.importer.volto.testing import (
    REDTURTLE_IMPORTER_VOLTO_FUNCTIONAL_TESTING,  # noqa: E501
)
from zope.component import queryUtility

import unittest


class TestMigration(unittest.TestCase):
    """"""

    layer = REDTURTLE_IMPORTER_VOLTO_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        # enable blocks behavior
        fti = queryUtility(IDexterityFTI, name='Document')
        behaviors = [x for x in fti.behaviors]
        behaviors.append('volto.blocks')
        fti.behaviors = tuple(behaviors)

    def test_migration_items_with_blocks(self):
        migration_view = api.content.get_view(
            name="data-migration", context=self.portal, request=self.request
        )
        self.request.form['_authenticator'] = createToken()
        migration_view.do_migrate()
        document = api.content.find(id='first-document')[0].getObject()
        self.assertEqual(document.text, None)
        self.assertNotEqual(document.blocks, {})

        news = api.content.find(id='a-news')[0].getObject()
        self.assertNotEqual(news.text, None)
        self.assertEqual(getattr(news, 'blocks', None), None)
