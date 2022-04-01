import csv 

from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from signup.access import is_coordinator, EA_THRESHOLD, LD_THRESHOLD, is_ea, is_ld
from signup.models import Coordinator, Job, Role, Volunteer, Global

DAYFORMAT = "%A"
TIMEFORMAT = "%I:%M %p"
DAYTIMEFORMAT = DAYFORMAT + " " + TIMEFORMAT
            
@user_passes_test(lambda u: is_coordinator(u))
def download_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="StaffSheet.csv"'
    writer = csv.writer(response, dialect='excel')
    writer.writerow(["Role", "Protected", "EA/LD", "Job", "Start Day", "Start Time", "End Day", "End Time", "Volunteer Name", "Email", "Comment"])
    total = 0
    taken = 0;
    
    for j in Job.objects.order_by('source_id', 'start') :
        cnt = 0
        if j.protected : 
            prot = "Yes"
        else:
            prot = "";
        
        eald=""    
        if is_ea(j) :
            eald = "Early Arrival"
        
        if is_ld(j) :
            eald = "Late Departure"

        for v in Volunteer.objects.filter(source__exact=j.source.pk, title__exact=j.title, start__exact=j.start).select_related('user') :
            writer.writerow([j.source.pk, prot, eald, j.title, j.start.strftime(DAYFORMAT), j.start.strftime(TIMEFORMAT), j.end.strftime(DAYFORMAT), j.end.strftime(TIMEFORMAT), v.user.first_name + " " + v.user.last_name,  v.user.email, v.comment])
            cnt += 1
            
        for _ in range(j.needs - cnt) :
            writer.writerow([j.source.pk, prot, eald, j.title, j.start.strftime(DAYFORMAT), j.start.strftime(TIMEFORMAT), j.end.strftime(DAYFORMAT), j.end.strftime(TIMEFORMAT), '', '', '', ''])

        total += j.needs
        taken += cnt


    writer.writerow([])
    writer.writerow(['Total staff', str(total)])
    writer.writerow(['Jobs unfilled', str(total-taken)])
    return response

@user_passes_test(lambda u: is_coordinator(u))
def eald_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EA_LD.csv"'
    writer = csv.writer(response)
    writer.writerow(["Early/Late", "Role", "Job", "Start Time", "End Time", "Person"])
    
    ea_total = 0 
    ea_filled = 0 
    ld_total = 0 
    ld_filled = 0 
        
    for j in Job.objects.filter(Q(start__lte = EA_THRESHOLD) | Q(end__gt = LD_THRESHOLD)).order_by('source_id', 'start') :
        cnt = 0

        if is_ea(j) :
            eald = "Early Arrival"
        
        if is_ld(j) :
            eald = "Late Departure"
            
        for v in Volunteer.objects.filter(source__exact=j.source, title__exact=j.title, start__exact=j.start) :                
            writer.writerow([eald, j.source.pk, j.title, j.start.strftime(DAYTIMEFORMAT), j.end.strftime(DAYTIMEFORMAT), v.name])
            cnt += 1
            
        for _ in range(j.needs - cnt) :
            writer.writerow([eald, j.source.pk, j.title, j.start.strftime(DAYTIMEFORMAT), j.end.strftime(DAYTIMEFORMAT), ""])

        if is_ea(j) :
            ea_total += j.needs
            ea_filled += cnt
        
        if is_ld(j) :
            ld_total += j.needs
            ld_filled += cnt

    writer.writerow([])
    writer.writerow(['Total Early Arrivals', str(ea_total)])
    writer.writerow(['Taken Early Arrivals', str(ea_filled)])
    writer.writerow(['Total Late Departures', str(ld_total)])
    writer.writerow(['Taken Late Departures', str(ld_filled)])
    
    return response
