import uuid
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.conf import settings
from django.utils import timezone
from .models import Spot, Visit

class ParkingTests(TestCase):
    def setUp(self):
        Spot.objects.create(label='A01')
        Spot.objects.create(label='A02')
        self.details = dict(owner='Test Driver', plate='KA 01 AB 1234', car_model='Honda City', color='White', request_id=str(uuid.uuid4()))
    def arrive(self, **changes):
        return self.client.post('/api/check-in/', {**self.details, **changes}, HTTP_X_KIOSK_KEY=settings.KIOSK_API_KEY)
    def test_assignment_and_private_page(self):
        response=self.arrive()
        self.assertEqual(response.status_code,201)
        record=Visit.objects.get()
        self.assertEqual(record.spot.label,'A01')
        self.assertEqual(record.plate,'KA01AB1234')
        self.assertIsNotNone(record.entered_at)
        self.assertContains(self.client.get(response.content.decode()),'A01')
        public=self.client.get('/api/availability/').json()
        self.assertEqual(public['free'],1)
        self.assertNotIn('KA01AB1234',str(public))
    def test_retry_and_duplicate_car(self):
        first=self.arrive()
        second=self.arrive()
        self.assertEqual(first.content,second.content)
        self.assertEqual(Visit.objects.count(),1)
        self.assertEqual(self.arrive(request_id=str(uuid.uuid4())).status_code,409)
        self.assertEqual(self.arrive(owner='Someone else').status_code,409)
    def test_full_and_reuse_after_checkout(self):
        first=self.arrive().content.decode()
        self.assertEqual(self.arrive(plate='OTHER123',request_id=str(uuid.uuid4())).status_code,201)
        self.assertEqual(self.arrive(plate='THIRD123',request_id=str(uuid.uuid4())).status_code,409)
        self.client.post(first+'checkout/')
        self.assertEqual(self.arrive(plate='THIRD123',request_id=str(uuid.uuid4())).status_code,201)
        self.assertEqual(Visit.objects.filter(exited_at__isnull=True).count(),2)
    def test_billing_boundaries_and_frozen_receipt(self):
        url=self.arrive().content.decode()
        record=Visit.objects.get()
        start=timezone.now()-timedelta(hours=1,seconds=1)
        record.entered_at=start
        record.save()
        self.assertEqual(record.bill(start),Decimal('50'))
        self.assertEqual(record.bill(start+timedelta(hours=1)),Decimal('50'))
        self.assertEqual(record.bill(start+timedelta(hours=1,microseconds=1)),Decimal('100'))
        self.client.post(url+'checkout/')
        record.refresh_from_db()
        exit_time=record.exited_at
        self.assertEqual(record.total,Decimal('100'))
        self.client.post(url+'checkout/')
        record.refresh_from_db()
        self.assertEqual(record.exited_at,exit_time)
        self.assertContains(self.client.get(url),'Visit complete')
    def test_validation_auth_and_methods(self):
        self.assertEqual(self.client.post('/api/check-in/',self.details).status_code,403)
        self.assertEqual(self.arrive(plate='???').status_code,400)
        self.assertEqual(self.arrive(request_id='bad').status_code,400)
        self.assertEqual(self.arrive(owner='').status_code,400)
        self.assertEqual(self.arrive(owner='x'*101).status_code,400)
        self.assertEqual(self.client.get('/api/check-in/').status_code,405)
        url=self.arrive().content.decode()
        self.assertEqual(self.client.get(url+'checkout/').status_code,405)
    def test_checkout_csrf(self):
        url=self.arrive().content.decode()
        browser=Client(enforce_csrf_checks=True)
        self.assertEqual(browser.post(url+'checkout/').status_code,403)
        browser.get(url)
        csrf=browser.cookies['csrftoken'].value
        self.assertEqual(browser.post(url+'checkout/', {'csrfmiddlewaretoken':csrf}).status_code,302)
    def test_unknown_pass(self):
        self.assertEqual(self.client.get(f'/visit/{uuid.uuid4()}/').status_code,404)
