import pytest
from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.test import TestCase

from hs_core.hydroshare.utils import encode_resource_url, decode_resource_url


@pytest.mark.parametrize("decoded_url,encoded_url", [
    ("https://www.hydroshare.org/oh look/ a/ space /weird names.txt",
     "https://www.hydroshare.org/oh%20look/%20a/%20space%20/weird%20names.txt"),
    ("https://www.hydroshare.org/data/contents/just file.txt",
     "https://www.hydroshare.org/data/contents/just%20file.txt"),
    ("https://www.hydroshare.org/data/contents/just folder/",
     "https://www.hydroshare.org/data/contents/just%20folder/"),
    ("https://www.hydroshare.org/data/contents/just folder/file.txt",
     "https://www.hydroshare.org/data/contents/just%20folder/file.txt")
])
def test_encode_decode_resource_url(decoded_url, encoded_url):
    """
    Tests the encode/decode url functions work correctly
    """
    assert encode_resource_url(decoded_url) == encoded_url
    assert decode_resource_url(encoded_url) == decoded_url


class TestMigrations(TestCase):
    
    app = __package__
    migrate_from = None
    migrate_to = None

    def setUp(self):
        super(TestMigrations, self).setUp()
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass