from hs_core import hydroshare
from hs_core.management.utils import find_resource_file_duplicates
from hs_core.tests.utils.test_utils import TestMigrations
from django.core.management import call_command
from django.contrib.auth.models import Group
from hs_core.models import ResourceFile, BaseResource


class ResourceFileDuplicateTestCase(TestMigrations):
    app = 'hs_core'
    migrate_from = '0072_remove_duplicate_res_files'
    migrate_to = '0073_resource_file_unique_constraint'

    def setUpBeforeMigration(self, apps):
        self.update_command = 'fix_resourcefile_duplicates'

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'mp_resource_migration@email.com',
            username='mp_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.resource = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

        ResourceFileOld = apps.get_model('hs_core', 'ResourceFile')
        self.file = f"{self.resource.short_id}/data/contents/testfile.txt"

        # TODO: We want to create duplicate ResourceFile entries
        # So that we can later test the removal of duplicates
        # I haven't been able to get this to work...

        # EXECUTE WITH:
        # ./hsctl managepy test hs_core.tests.api.native.test_fix_resourcefile_duplicates_management_command

        # kwargs = {}
        # kwargs['file_folder'] = None
        # kwargs['content_object'] = self.resource
        # kwargs['resource_file'] = self.file
        # self.res_file_id = ResourceFileOld.objects.create(**kwargs).id
        
        # ResourceFileOld.create(resource=self.resource, file=self.file, folder='')
        # ResourceFileOld.objects.create(resource=self.resource, file=self.file, folder='')

        # from django.db import connection
        # with connection.cursor() as cursor:
        #     sql = f'INSERT INTO "public"."hs_core_resourcefile" \
        #         ("id", "object_id", "resource_file", "content_type_id", "fed_resource_file", "file_folder", "_size") \
        #         VALUES (1, {self.resource.id}, "{self.file}", {self.resource.content_type_id}, EMPTY, EMPTY, 1);'
        #     cursor.execute(sql)
    
    def tearDown(self):
        super(ResourceFileDuplicateTestCase, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        BaseResource.objects.all().delete()
        ResourceFile.objects.all().delete()

    def test_duplicates_removed(self):
        dups = find_resource_file_duplicates()
        self.assertEqual(dups.count(), 2)
        call_command(self.update_command)
        # ResourceFile = self.apps.get_model('hs_core', 'ResourceFile')
        # file_object = ResourceFile.objects.get(id=self.res_file_id)
        dups = find_resource_file_duplicates()
        self.assertEqual(dups.count(), 0)
    
    def test_ensure_one_resourcefile_is_retained(self):
        pass