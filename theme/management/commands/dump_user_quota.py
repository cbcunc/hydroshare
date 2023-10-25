import csv
from django.core.management.base import BaseCommand
from theme.models import UserQuota
from hs_core.hydroshare import get_data_zone_usage_from_irods, get_user_zone_usage_from_irods
from hs_core.hydroshare.utils import convert_file_size_to_unit


class Command(BaseCommand):
    help = "Output quota allocations and used values for all users in HydroShare"

    def add_arguments(self, parser):
        parser.add_argument('output_file_name_with_path', help='output file name with path')

    def handle(self, *args, **options):
        with open(options['output_file_name_with_path'], 'w') as csvfile:
            w = csv.writer(csvfile)
            fields = [
                'User id',
                'User name',
                'Allocated quota value',
                'Used quota value',
                'Quota unit',
                'Storage zone',
                'Data Zone used',
                'User Zone used'
            ]
            w.writerow(fields)

            for uq in UserQuota.objects.filter(
                    user__is_active=True).filter(user__is_superuser=False):
                data_zone = get_data_zone_usage_from_irods(uq.user.username)
                user_zone = get_user_zone_usage_from_irods(uq.user.username)
                data_zone = convert_file_size_to_unit(data_zone, 'GB')
                user_zone = convert_file_size_to_unit(user_zone, 'GB')
                values = [
                    uq.user.id,
                    uq.user.username,
                    uq.allocated_value,
                    uq.used_value,
                    uq.unit,
                    uq.zone,
                    data_zone,
                    user_zone
                ]
                w.writerow([str(v) for v in values])
