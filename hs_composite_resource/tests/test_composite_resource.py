# coding=utf-8
import datetime
import os
import shutil
from zipfile import ZipFile

from dateutil import tz
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from unittest import skip

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare.utils import (
    ResourceVersioningException,
    add_file_to_resource, get_file_from_irods,
    get_resource_by_shortkey, resource_file_add_process
)
from hs_core.models import BaseResource, ResourceFile
from hs_core.tasks import FileOverrideException
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import (
    add_reference_url_to_resource,
    create_folder, delete_resource_file,
    edit_reference_url_in_resource,
    move_or_rename_file_or_folder,
    remove_folder,
    unzip_file, zip_by_aggregation_file
)
from hs_file_types.models import (
    FileSetLogicalFile,
    GenericFileMetaData,
    GenericLogicalFile,
    GeoFeatureLogicalFile,
    GeoRasterLogicalFile,
    ModelInstanceLogicalFile,
    ModelProgramLogicalFile,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile
)
from hs_file_types.models.base import METADATA_FILE_ENDSWITH, RESMAP_FILE_ENDSWITH
from hs_file_types.tests.utils import CompositeResourceTestMixin


class CompositeResourceTest(
    MockIRODSTestCaseMixin, TransactionTestCase, CompositeResourceTestMixin
):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "user1@nowhere.com",
            username="user1",
            password='mypassword1',
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[self.group],
        )

        self.res_title = "Testing Composite Resource"
        self.invalid_url = "http://i.am.invalid"
        self.valid_url = "https://www.google.com"
        self.raster_file_name = "small_logan.tif"
        self.raster_file = "hs_composite_resource/tests/data/{}".format(
            self.raster_file_name
        )

        self.generic_file_name = "generic_file.txt"
        self.generic_file = "hs_composite_resource/tests/data/{}".format(
            self.generic_file_name
        )

        self.netcdf_file_name = "netcdf_valid.nc"
        self.netcdf_file = "hs_composite_resource/tests/data/{}".format(
            self.netcdf_file_name
        )

        self.netcdf_file_name_no_coverage = "nc_no_spatial_ref.nc"
        self.netcdf_file_no_coverage = "hs_composite_resource/tests/data/{}".format(
            self.netcdf_file_name_no_coverage
        )

        self.sqlite_file_name = "ODM2.sqlite"
        self.sqlite_file = "hs_composite_resource/tests/data/{}".format(
            self.sqlite_file_name
        )

        self.watershed_dbf_file_name = "watersheds.dbf"
        self.watershed_dbf_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_dbf_file_name
        )
        self.watershed_shp_file_name = "watersheds.shp"
        self.watershed_shp_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_shp_file_name
        )
        self.watershed_shx_file_name = "watersheds.shx"
        self.watershed_shx_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_shx_file_name
        )

        self.json_file_name = "multi_sites_formatted_version1.0.refts.json"
        self.json_file = "hs_composite_resource/tests/data/{}".format(
            self.json_file_name
        )

        self.zip_file_name = "test.zip"
        self.zip_file = "hs_composite_resource/tests/data/{}".format(self.zip_file_name)

        self.zipped_aggregation_file_name = "multi_sites_formatted_version1.0.refts.zip"
        self.zipped_aggregation_file = "hs_composite_resource/tests/data/{}".format(
            self.zipped_aggregation_file_name
        )

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()

    def test_composite_resource_my_resources_scales(self):
        # TODO: this test passes but it should fail
        # Passing indicates that the my_resources page does not scale
        # test that db queries for "my_resources" remain constant when adding more resources

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)
        self.client.login(username='user1', password='mypassword1')
        self.create_composite_resource()
        with self.assertNumQueries(30):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

        self.create_composite_resource()

        with self.assertNumQueries(40):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        # there should be two resources at this point
        self.assertEqual(BaseResource.objects.count(), 2)

        self.create_composite_resource()

        with self.assertNumQueries(51):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        # there should be two resources at this point
        self.assertEqual(BaseResource.objects.count(), 3)

        self.create_composite_resource()

        with self.assertNumQueries(62):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        # there should be two resources at this point
        self.assertEqual(BaseResource.objects.count(), 4)
