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

from datetime import date, time
import StringIO

from django.test import TestCase

from multigtfs.models import (
    Block, Feed, Route, Service, Shape, Stop, StopTime, Trip)


class TripTest(TestCase):
    def setUp(self):
        self.feed = Feed.objects.create()
        self.route = Route.objects.create(
            feed=self.feed, route_id='R1', rtype=3)

    def test_string(self):
        trip = Trip.objects.create(route=self.route, trip_id='T1')
        self.assertEqual(str(trip), '1-R1-T1')

    def test_import_trips_txt_minimal(self):
        trips_txt = StringIO.StringIO("""\
route_id,service_id,trip_id
R1,S1,T1
""")
        service = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        Trip.import_txt(trips_txt, self.feed)
        trip = Trip.objects.get()
        self.assertEqual(trip.route, self.route)
        self.assertEqual(list(trip.services.all()), [service])
        self.assertEqual(trip.trip_id, 'T1')
        self.assertEqual(trip.headsign, '')
        self.assertEqual(trip.short_name, '')
        self.assertEqual(trip.direction, '')
        self.assertEqual(trip.block, None)
        self.assertEqual(trip.shape, None)
        self.assertEqual(trip.wheelchair_accessible, '')
        self.assertEqual(trip.bikes_allowed, '')

    def test_import_trips_txt_maximal(self):
        trips_txt = StringIO.StringIO("""\
route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,\
block_id,shape_id,wheelchair_accessible,bikes_allowed
R1,S1,T1,Headsign,HS,0,B1,S1,1,2
""")
        service = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        block = Block.objects.create(feed=self.feed, block_id='B1')
        shape = Shape.objects.create(feed=self.feed, shape_id='S1')
        Trip.import_txt(trips_txt, self.feed)
        trip = Trip.objects.get()
        self.assertEqual(trip.route, self.route)
        self.assertEqual(list(trip.services.all()), [service])
        self.assertEqual(trip.trip_id, 'T1')
        self.assertEqual(trip.headsign, 'Headsign')
        self.assertEqual(trip.short_name, 'HS')
        self.assertEqual(trip.direction, '0')
        self.assertEqual(trip.block, block)
        self.assertEqual(trip.shape, shape)
        self.assertEqual(trip.wheelchair_accessible, '1')
        self.assertEqual(trip.bikes_allowed, '2')

    def test_import_trips_txt_multiple_services(self):
        '''If a trip is associated with several services, one is created'''
        trips_txt = StringIO.StringIO("""\
route_id,service_id,trip_id
R1,S1,T1
R1,S2,T1
""")
        service1 = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        service2 = Service.objects.create(
            feed=self.feed, service_id='S2', start_date=date(2012, 1, 1),
            end_date=date(2012, 4, 14))

        Trip.import_txt(trips_txt, self.feed)
        trip = Trip.objects.get()
        self.assertEqual(trip.route, self.route)
        self.assertEqual(trip.services.count(), 2)
        self.assertTrue(service1 in trip.services.all())
        self.assertTrue(service2 in trip.services.all())

    def test_export_trips_txt_empty(self):
        trips_txt = Trip.objects.in_feed(feed=self.feed).export_txt()
        self.assertFalse(trips_txt)

    def test_export_trips_txt_minimal(self):
        service = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        trip = Trip.objects.create(route=self.route, trip_id='T1')
        trip.services.add(service)
        trips_txt = Trip.objects.in_feed(feed=self.feed).export_txt()
        self.assertEqual(trips_txt, """\
route_id,service_id,trip_id
R1,S1,T1
""")

    def test_export_trips_txt_maximal(self):
        service = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        block = Block.objects.create(feed=self.feed, block_id='B1')
        shape = Shape.objects.create(feed=self.feed, shape_id='S1')
        trip = Trip.objects.create(
            route=self.route, trip_id='T1', headsign='Headsign',
            short_name='HS', direction=0, block=block, shape=shape,
            wheelchair_accessible='2', bikes_allowed='1')
        trip.services.add(service)
        trips_txt = Trip.objects.in_feed(feed=self.feed).export_txt()
        self.assertEqual(trips_txt, """\
route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,\
block_id,shape_id,wheelchair_accessible,bikes_allowed
R1,S1,T1,Headsign,HS,0,B1,S1,2,1
""")

    def test_export_trips_txt_multiple_services(self):
        service1 = Service.objects.create(
            feed=self.feed, service_id='S1', start_date=date(2011, 4, 14),
            end_date=date(2011, 12, 31))
        service2 = Service.objects.create(
            feed=self.feed, service_id='S2', start_date=date(2012, 1, 1),
            end_date=date(2012, 4, 14))
        trip = Trip.objects.create(route=self.route, trip_id='T1')
        trip.services.add(service1, service2)
        trips_txt = Trip.objects.in_feed(feed=self.feed).export_txt()
        self.assertEqual(trips_txt, """\
route_id,service_id,trip_id
R1,S1,T1
R1,S2,T1
""")

    def test_update_geometry_no_shape_or_stoptime(self):
        trip = Trip.objects.create(route=self.route, trip_id='T1')
        trip.update_geometry()
        self.assertEqual(trip.geometry, None)

    def test_update_geometry_has_shape(self):
        shape = Shape.objects.create(
            feed=self.feed, shape_id='S1',
            geometry='LINESTRING(-117.133162 36.425288, -117.14 36.43)')
        trip = Trip.objects.create(route=self.route, trip_id='T1', shape=shape)
        trip.update_geometry()
        self.assertEqual(trip.geometry, shape.geometry)

    def test_update_geometry_has_stoptimes(self):
        stop1 = Stop.objects.create(
            feed=self.feed, stop_id='STAGECOACH',
            point="POINT(-117.133162 36.425288)")
        stop2 = Stop.objects.create(
            feed=self.feed, stop_id='TAVERN',
            point="POINT(-117.14 36.43)")
        trip = Trip.objects.create(route=self.route, trip_id='T1')
        StopTime.objects.create(
            trip=trip, stop=stop1, arrival_time=time(6),
            departure_time=time(6), stop_sequence=1)
        StopTime.objects.create(
            trip=trip, stop=stop2, arrival_time=time(7),
            departure_time=time(7), stop_sequence=2)
        trip.update_geometry()
        self.assertEqual(
            trip.geometry.coords,
            ((-117.133162, 36.425288), (-117.14, 36.43)))
