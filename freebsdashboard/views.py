from django.shortcuts import render, redirect
import pytz


def set_timezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')
    else:
        return render(request, 'set_timezone.html',
                      {'timezones': pytz.common_timezones})
