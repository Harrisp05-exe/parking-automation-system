import re
import uuid
from secrets import compare_digest
from django.conf import settings
from django.db import IntegrityError, OperationalError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import never_cache
from .models import Spot, Visit

def map_data(current=None):
    occupied = set(Visit.objects.filter(exited_at__isnull=True).values_list('spot_id', flat=True))
    spots = [{'label': s.label, 'state': 'yours' if current and current.exited_at is None and current.spot_id == s.id else 'occupied' if s.id in occupied else 'free'} for s in Spot.objects.all()]
    return {'spots': spots, 'capacity': len(spots), 'occupied': len(occupied), 'free': len(spots)-len(occupied)}

@require_GET
@never_cache
def home(request):
    return render(request, 'parking/dashboard.html', {**map_data(), 'rate': settings.PARKING_RATE, 'currency':settings.PARKING_CURRENCY})

@require_GET
@never_cache
def availability(request):
    return JsonResponse(map_data())

@csrf_exempt
@require_POST
@never_cache
def check_in(request):
    if not compare_digest(request.headers.get('X-Kiosk-Key',''), settings.KIOSK_API_KEY):
        return HttpResponse('Invalid kiosk key.', status=403)
    values = {key: request.POST.get(key,'').strip() for key in ('owner','plate','car_model','color')}
    values['plate'] = re.sub(r'[\s-]+', '', values['plate']).upper()
    if any(not v for v in values.values()) or any(len(values[k]) > n for k,n in [('owner',100),('plate',20),('car_model',80),('color',40)]) or not re.fullmatch(r'[A-Z0-9]{3,20}', values['plate']):
        return HttpResponse('Enter all details. Plate must contain 3–20 letters/digits.', status=400)
    try:
        request_id = uuid.UUID(request.POST.get('request_id',''))
    except ValueError:
        return HttpResponse('A valid request ID is required.', status=400)
    for attempt in range(4):
        try:
            with transaction.atomic():
                existing = Visit.objects.filter(request_id=request_id).first()
                if existing:
                    if any(getattr(existing,k) != v for k,v in values.items()):
                        return HttpResponse('Request ID already used for different details.', status=409)
                    return HttpResponse(reverse('visit', args=[existing.token]), content_type='text/plain')
                if Visit.objects.filter(plate=values['plate'], exited_at__isnull=True).exists():
                    return HttpResponse('This car is already parked.', status=409)
                occupied = Visit.objects.filter(exited_at__isnull=True).values('spot_id')
                spot = Spot.objects.select_for_update().exclude(pk__in=occupied).first()
                if not spot:
                    return HttpResponse('Parking is full. No spot was assigned.', status=409)
                visit = Visit.objects.create(spot=spot, request_id=request_id, hourly_rate=settings.PARKING_RATE, currency=settings.PARKING_CURRENCY, **values)
            return HttpResponse(reverse('visit', args=[visit.token]), status=201, content_type='text/plain')
        except (IntegrityError, OperationalError):
            if attempt == 3:
                return HttpResponse('Parking is busy. Retry with the same details.', status=503)

@require_GET
@never_cache
def visit(request, token):
    record = get_object_or_404(Visit.objects.select_related('spot'), token=token)
    return render(request, 'parking/dashboard.html', {**map_data(record), 'visit':record, 'amount':record.total if record.exited_at else record.bill(), 'hours':record.hours(), 'rate':record.hourly_rate, 'currency':record.currency})

@require_POST
@never_cache
def checkout(request, token):
    with transaction.atomic():
        record = get_object_or_404(Visit.objects.select_for_update(), token=token)
        if record.exited_at is None:
            end = timezone.now()
            # Conditional update also prevents double checkout on SQLite.
            Visit.objects.filter(pk=record.pk, exited_at__isnull=True).update(exited_at=end, total=record.bill(end))
    return redirect('visit', token=token)
