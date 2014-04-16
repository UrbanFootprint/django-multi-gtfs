#
# Copyright 2012-2014 John Whitlock
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from multigtfs.models.feed import Feed


class Command(BaseCommand):
    args = '<gtfsfeed.zip>'
    help = 'Imports a GTFS Feed from a zipped feed file'
    option_list = BaseCommand.option_list + (
        make_option(
            '-n', '--name', type='string', dest='name', help='Set the name of the imported feed'),
        make_option(
            '-D', '--directory', action='store_true', dest='directory', default=False,
            help='Pass in a directory of GTFS files and import them'),
        make_option(
            '-r', '--rename', action='store_true', dest='rename', default=False,
            help='Rename the .zip files with their agency before importing them.'),
        make_option(
            '-R', '--rename-only', action='store_true', dest='rename_only', default=False,
            help='Rename the .zip files, but do not import them.'),

    )

from datetime import datetime
from optparse import make_option
import os
import glob
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from multigtfs.models.feed import Feed
from zipfile import ZipFile
import csv

class Command(BaseCommand):
    args = '<gtfsfeed.zip>'
    help = 'Imports a GTFS Feed from a zipped feed file'
    option_list = BaseCommand.option_list + (
        make_option('-n', '--name', type='string', dest='name',help='Set the name of the imported feed'),
        make_option('-D', '--dir',  default=False, action='store_true', help='Import all zipfiles in a dir'),
        make_option('-R', '--rename_source',  default=False, action='store_true', help='rename the zipfile with agency name'),
        make_option('-O', '--overwrite', default=False, action='store_true', help='overwrite Agencies already in system'),
    )

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('You must pass in the path to the feed.')
        if len(args) > 1:
            raise CommandError('Import multiple GTFS in a directory with the -D or --directory flag')
        if options.get('overwrite'):
            raise NotImplementedError

        if options.get('dir', None):
            path = args[0]
            os.chdir(path)
            files_to_import = glob.glob("*.zip")
            raw_feeds = [os.path.join(path, filename) for filename in files_to_import]
        else:
            raw_feeds = [args[0]]
        feeds = []
        if options['rename_source']:
            for gtfs_feed in raw_feeds:

                z = ZipFile(gtfs_feed)

                if not 'agency.txt' in z.namelist(): # and not os.path.join(zip_name, 'agency.txt') in z.namelist():
                    print "No agency.txt found in " + gtfs_feed
                    os.rename(gtfs_feed, gtfs_feed + '.broken')
                    continue

                agency_file = z.open('agency.txt')
                agency_file_reader = csv.DictReader(agency_file, delimiter=',')

                rows = [r for r in agency_file_reader]
                agency_name = rows[0].get('agency_name', 'undefined')

                print "\t" + agency_name
                os.rename(gtfs_feed, agency_name.replace(' ', '_').replace('-','').lower() + '.zip')
                feeds.append(gtfs_feed)
        else:
            feeds = raw_feeds

        for gtfs_feed in feeds:
            try:
                import_filename = os.path.basename(gtfs_feed)[:-4]
                name = options.get('name') or import_filename + ' %s' % datetime.now()
                print('\t' + name)
                feed = Feed.objects.create(name=name)
                feed.import_gtfs(gtfs_feed)
                self.stdout.write("Successfully imported Feed %s\n" % (feed))
            except Exception, E:
                self.stdout.write(str(E))
                os.rename(gtfs_feed, os.path.basename(gtfs_feed) + '.breaks')
                print E
