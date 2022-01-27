import csv
from django.core.management.base import BaseCommand
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified


class Command(BaseCommand):
    help = "Fix versioning chain violation resources captured in an csv input file with three columns: " \
           "isVersionOf, Resource, and isReplacedby"

    def add_arguments(self, parser):
        # csv filename with full path to load versioning chain violation resources from
        parser.add_argument('input_file', help='input csv file name with full path to be processed and '
                                               'load versioning chain violation resources from')

    def handle(self, *args, **options):
        input_file = options['input_file']
        with open(input_file) as f:
            reader = csv.reader(f)
            headers = next(reader)
            version_of_col = 0
            res_col = 1
            replace_by_col = 2
            if len(headers) < 3 or headers[version_of_col].lower() != 'isversionof' or \
                    headers[res_col].lower() != 'resource' \
                    or headers[replace_by_col].lower() != 'isreplacedby':
                print('headers are not correct, exit', flush=True)
                return
            count = 0
            for row in reader:
                if not row[res_col]:
                    print('Resource column in the csv file cannot be empty, exit', flush=True)
                    return
                fixed = False
                res_id = row[res_col]
                try:
                    res = get_resource_by_shortkey(res_id)
                except Exception:
                    print(f'Resource {res_id} does not exist', flush=True)
                    continue

                if not row[version_of_col] and not row[replace_by_col]:
                    # both isVersionOf and isReplacedby are empty, so clean up any versioning
                    # relationships for this resource if any
                    if res.metadata.relations.filter(type='isVersionOf').exists():
                        res.metadata.relations.filter(type='isVersionOf').delete()
                        resource_modified(res, overwrite_bag=False)
                        fixed = True
                    if res.metadata.relations.filter(type='isReplacedBy').exists():
                        res.metadata.relations.filter(type='isReplacedBy').delete()
                        resource_modified(res, overwrite_bag=False)
                        fixed = True
                    if res_id == '4111306529e74503b090494ef1e808e2':
                        # for this single resource, isCopyOf relation needs to be added
                        copy_of_res_id = 'fdc3a06e6ad842abacfa5b896df73a76'
                        try:
                            copy_of_res = get_resource_by_shortkey(copy_of_res_id)
                        except Exception:
                            print(f'Resource {copy_of_res_id} does not exist, so isCopyOf relation cannot be added',
                                  flush=True)
                            continue
                        hs_identifier = copy_of_res.metadata.identifiers.filter(name="hydroShareIdentifier").first()
                        if hs_identifier:
                            res.metadata.create_element('source', derived_from=hs_identifier.url)
                            print(f'{res_id} is made a copy of {copy_of_res_id}', flush=True)
                            fixed = True
                elif not row[replace_by_col]:
                    # isVersionOf is not empty but isReplacedBy is empty
                    version_res_id = row[version_of_col]
                    try:
                        version_res = get_resource_by_shortkey(version_res_id)
                    except Exception:
                        print(f'Resource {version_res_id} does not exist', flush=True)
                        continue
                    hs_identifier = version_res.metadata.identifiers.filter(name="hydroShareIdentifier").first()
                    res.metadata.relations.filter(type='isVersionOf').delete()
                    res.metadata.create_element('relation', type='isVersionOf', value=hs_identifier.url)
                    resource_modified(res, overwrite_bag=False)
                    fixed = True
                elif not row[version_of_col]:
                    # isVersionOf is empty but isReplacedBy is not empty
                    replace_by_res_id = row[replace_by_col]
                    try:
                        replace_by_res = get_resource_by_shortkey(replace_by_res_id)
                    except Exception:
                        print(f'Resource {replace_by_res_id} does not exist', flush=True)
                        continue
                    hs_identifier = replace_by_res.metadata.identifiers.filter(name="hydroShareIdentifier").first()
                    res.metadata.relations.filter(type='isReplacedBy').delete()
                    res.metadata.create_element('relation', type='isReplacedBy', value=hs_identifier.url)
                    resource_modified(res, overwrite_bag=False)
                    fixed = True
                else:
                    # both isReplacedBy and isVersionOf are not empty - need to only keep this pair of relationship
                    # and delete other pairs to meet the single obsolecense chain requirement
                    version_res_id = row[version_of_col]
                    try:
                        version_res = get_resource_by_shortkey(version_res_id)
                    except Exception:
                        print(f'Resource {version_res_id} does not exist', flush=True)
                        continue
                    replace_res_id = row[replace_by_col]
                    try:
                        replace_res = get_resource_by_shortkey(replace_res_id)
                    except Exception:
                        print(f'Resource {replace_res_id} does not exist', flush=True)
                        continue
                    res.metadata.relations.filter(type='isVersionOf').delete()
                    hs_identifier = version_res.metadata.identifiers.filter(name="hydroShareIdentifier").first()
                    res.metadata.create_element('relation', type='isVersionOf', value=hs_identifier.url)
                    res.metadata.relations.filter(type='isReplacedBy').delete()
                    hs_identifier = replace_res.metadata.identifiers.filter(name="hydroShareIdentifier").first()
                    res.metadata.create_element('relation', type='isReplacedBy', value=hs_identifier.url)
                    resource_modified(res, overwrite_bag=False)
                    fixed = True
                if fixed:
                    count += 1
        print(f'versioning relationships for {count} resources have been fixed', flush=True)
