import io
import qrcode
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import Student
from accounts.views import get_role
from .models import OutpassRequest, MovementLog
from .forms import OutpassRequestForm
from twilio.rest import Client
from django.core.mail import send_mail


@login_required
def request_outpass(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile found. Ask admin to create one.')
        return redirect('home')

    if request.method == 'POST':
        form = OutpassRequestForm(request.POST)
        if form.is_valid():
            outpass = form.save(commit=False)
            if outpass.expected_return <= outpass.out_date:
                form.add_error('expected_return', 'Return time must be after out time.')
            else:
                outpass.student = student
                outpass.save()
                messages.success(request, 'Outpass request submitted.')
                return redirect('my_requests')
    else:
        form = OutpassRequestForm()
    return render(request, 'outpass/request_form.html', {'form': form})


@login_required
def my_requests(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile found. Ask admin to create one.')
        return redirect('home')
    requests_list = OutpassRequest.objects.filter(student=student).order_by('-created_at')
    return render(request, 'outpass/my_requests.html', {'requests_list': requests_list})

@login_required
def warden_requests(request):
    if get_role(request.user) != 'Warden':
        messages.error(request, 'Only wardens can access this page.')
        return redirect('home')
    status = request.GET.get('status', 'Pending')
    qs = OutpassRequest.objects.select_related('student__user').order_by('-created_at')
    if status in ('Pending', 'Approved', 'Rejected'):
        qs = qs.filter(status=status)
    return render(request, 'outpass/warden_requests.html', {'requests_list': qs, 'status': status})


@login_required
def update_status(request, pk):
    if get_role(request.user) != 'Warden' or request.method != 'POST':
        return redirect('home')
    outpass = get_object_or_404(OutpassRequest, pk=pk)
    action = request.POST.get('action')
    if action in ('Approved', 'Rejected'):
        outpass.status = action
        outpass.remark = request.POST.get('remark', '')
        outpass.save()
        messages.success(request, f'Request {action.lower()}.')
    return redirect('warden_requests')


def notify_parent(student, text):
    print(f"[Notification: {student.parent_phone} / {student.parent_email}] {text}")
    if not (student.parent_email and settings.MAIL_USER and settings.MAIL_PASSWORD):
        return
    try:
        send_mail('Hostel Outpass Alert', text, settings.MAIL_USER, [student.parent_email])
    except Exception as e:
        print(f"Email failed: {e}")


@login_required
def my_id(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile found.')
        return redirect('home')
    return render(request, 'outpass/my_id.html', {'student': student})


@login_required
def my_qr(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('home')
    img = qrcode.make(student.student_id)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')


def process_scan(sid):
    try:
        student = Student.objects.select_related('user').get(student_id__iexact=sid)
    except Student.DoesNotExist:
        return {'ok': False, 'message': 'Invalid ID. Student not found.'}

    now = timezone.now()
    when = timezone.localtime(now).strftime('%d %b %Y, %I:%M %p')
    name = student.user.username

    # Student already outside -> this scan is ENTRY
    open_log = MovementLog.objects.filter(
        student=student, out_time__isnull=False, in_time__isnull=True
    ).order_by('-out_time').first()
    if open_log:
        open_log.in_time = now
        open_log.save()
        notify_parent(student, f'{name} entered the hostel at {when}.')
        return {'ok': True, 'direction': 'IN', 'student': student, 'log': open_log,
                'message': 'Entry recorded.'}

    # Student inside -> this scan is EXIT, needs an approved unused outpass
    outpass = OutpassRequest.objects.filter(
        student=student, status='Approved', movementlog__isnull=True
    ).order_by('created_at').first()
    if not outpass:
        return {'ok': False, 'student': student,
                'message': 'No approved outpass. Do NOT allow exit.'}

    log = MovementLog.objects.create(
        outpass=outpass, student=student, out_time=now, reason=outpass.reason
    )
    notify_parent(student, f'{name} left the hostel at {when}. Reason: {outpass.reason}')
    return {'ok': True, 'direction': 'OUT', 'student': student, 'log': log,
            'message': 'Exit recorded.'}


@login_required
def gate_scan(request):
    if get_role(request.user) not in ('Security', 'Warden'):
        messages.error(request, 'Only security or warden can access this page.')
        return redirect('home')
    result = None
    if request.method == 'POST':
        result = process_scan(request.POST.get('student_id', '').strip())
    return render(request, 'outpass/gate_scan.html', {'result': result})


@login_required
def movement_logs(request):
    if get_role(request.user) not in ('Security', 'Warden'):
        return redirect('home')

    q = request.GET.get('q', '').strip()
    date = request.GET.get('date', '').strip()
    status = request.GET.get('status', '')

    qs = MovementLog.objects.select_related('student__user', 'outpass').order_by('-out_time')
    if q:
        qs = qs.filter(student__student_id__icontains=q)
    if date:
        qs = qs.filter(out_time__date=date)

    now = timezone.now()
    logs = []
    for l in qs[:200]:
        expected = l.outpass.expected_return if l.outpass else None
        if l.in_time:
            l.late = bool(expected and l.in_time > expected)
            l.state = 'Late return' if l.late else 'On time'
        else:
            l.late = bool(expected and now > expected)
            l.state = 'OVERDUE' if l.late else 'Outside'
        logs.append(l)

    if status == 'late':
        logs = [l for l in logs if l.late]
    elif status == 'outside':
        logs = [l for l in logs if not l.in_time]

    return render(request, 'outpass/movement_logs.html', {
        'logs': logs, 'q': q, 'date': date, 'status': status,
    })