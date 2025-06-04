from django.shortcuts import render, redirect, get_object_or_404
from .models import ChitRegistration,Payment,WhatsAppMessageLog
from .forms import ChitForm
from datetime import datetime,date,timedelta
from django.db.models import Sum
from .models import AdminConfig
from .forms import AdminConfigForm
from django.contrib import messages
from django.db.models import Max
from django.contrib.auth import authenticate, login,logout
from .forms import RegisterForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import re
from django.views.decorators.csrf import csrf_exempt
import pywhatkit as kit
from django.db.models import Sum, Count
from django.utils.timezone import now
from django.contrib.auth.decorators import user_passes_test


@login_required
def index(request):
    return render(request, 'chitapp/index.html')

def is_admin_user(user):
    return user.is_authenticated and user.is_superuser

def admin_only(view_func):
    
    return user_passes_test(is_admin_user, login_url='/login/')(view_func)


@admin_only
def remove_admin(request):
    if request.method == "POST":
        username = request.POST.get('username')

        try:
            user = User.objects.get(username=username)
            if user.is_superuser:
                admin_count = User.objects.filter(is_superuser=True).count()
                if admin_count > 1:
                    user.is_superuser = False
                    user.is_staff = False
                    user.save()
                    messages.success(request, f"{user.username} is no longer an Admin!")
                else:
                    messages.error(request, "At least one admin must remain!")
            else:
                messages.warning(request, "User is not an admin!")
        except User.DoesNotExist:
            messages.error(request, "User does not exist!")

    return render(request, 'chitapp/remove_admin.html')

@admin_only
def make_admin(request):
    if request.method == "POST":
        if "back" in request.POST:
            return redirect('index')
        username = request.POST['username']

        try:
            user = User.objects.get(username=username)
            user.is_staff = True  
            user.is_superuser = True  
            user.save()
            messages.success(request, f"{user.username} is now an Admin!")
        except User.DoesNotExist:
            messages.error(request, "User does not exist!")
    return render(request, 'chitapp/make_admin.html')


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('/Login')
    else:
        form = RegisterForm()
    return render(request, "chitapp/registration.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/index')
        else:
            messages.error(request, "Invalid Username or Password")

    return render(request, 'chitapp/login.html')


def login_redirect(request):
    return redirect('/login/')


def logout_page(request):
        logout(request)
        messages.success(request,"Logged Out Successfuly")
        return redirect("/login")


def admin_login(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in Successfully")
                if user.is_superuser:  
                    request.session['is_admin'] = True  
                return redirect("/")
            else:
                messages.error(request, "Invalid User Name or Password")
            return redirect('/index')
    return render(request, 'chitapp/adminlogin.html')


def app_config():
    global config_values
    config_values = {}

    chit_type_entry = AdminConfig.objects.filter(key="CHIT_TYPE").first()
    
    if chit_type_entry:

        config_values["CHIT_TYPE"] = chit_type_entry.value

        chit_types = chit_type_entry.value.split(',')  
        for chit in chit_types:
            parts = chit.split('-')
            if len(parts) > 1 and parts[1].isdigit():  
                config_values[chit] = int(parts[1])  
    return config_values


@admin_only
def config_view(request):
    configs = AdminConfig.objects.order_by("id")  

    if request.method == "POST":
        for config in configs:
            key_name = f"key_{config.id}"
            value_name = f"value_{config.id}"
            
            if key_name in request.POST and value_name in request.POST:
                config.key = request.POST[key_name].strip()
                config.value = request.POST[value_name].strip()
                config.save()

        return redirect("config_view")  
    return render(request, "config_view.html", {"configs": configs})


@admin_only
def admin_config_view(request):
    configs = AdminConfig.objects.order_by("id")
    form = AdminConfigForm()

    if request.method == 'POST':
        key_list = request.POST.getlist('key').strip()
        value_list = request.POST.getlist('value').strip()

        for key, value in zip(key_list, value_list):
            if key and value and not AdminConfig.objects.filter(key=key, value=value).exists():
                AdminConfig.objects.create(key=key, value=value)
        return redirect('admin_config')

    return render(request, 'admin_config.html', {'configs': configs, 'form': form})


register_values = {}

def chit_register():
    global register_values
    register_values = {
        row['chit_Type']: row['max'] if row['max'] else 0
        for row in ChitRegistration.objects.values('chit_Type').annotate(max=Max('chit_Number'))
    }


def get_chit_number_firsttime():
    chit_type_with_number = {}
    chit_type_as_list = AdminConfig.objects.filter(key="CHIT_TYPE").values_list("value", flat=True).first().split(",")
    #print(chit_type_as_list)
    for item in chit_type_as_list:
        #print(item)
        prefix = item.split("-")[0]
        chit_type_with_number[item] = prefix+"0000"
    return chit_type_with_number


def register_chit(request):

    chit_register()
    global register_values

    if not register_values:
        register_values = get_chit_number_firsttime()
    
    first_time_values = get_chit_number_firsttime()
    for key in first_time_values.keys():
        if key not in register_values:
            register_values[key] = first_time_values[key]
            
 
    #register_values = dict(sorted(register_values.items(), key=lambda item: item[1][-3:]))

    register_values = dict(sorted(register_values.items(), key=lambda item: item[0]))
    
    chit_type = register_values

    if request.method == "POST":
        form = ChitForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Chit Registered Successfully!")
            return redirect('success')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ChitForm()

    return render(request, 'register_chit.html', {'form': form, 'chit_type': chit_type})


def success(request):
    return render(request, 'success.html')


def view_chits(request):

    config_values = app_config() 

    chit = None
    chit_amount = 0
    total_paid_week = 0
    paid_weeks = []
    ongoing_week = 0  

    chit_Type = request.GET.get("chit_Type")
    chit_Number = request.GET.get("chit_Number")

    chit_type_list = config_values.get('CHIT_TYPE').split(',')

    
    date_entry = AdminConfig.objects.filter(key="START_DATE").first()
    start_date = None

    if date_entry:
        try:
            start_date = datetime.strptime(date_entry.value, "%d/%m/%Y").date()
        except ValueError:
            start_date = None  

    if start_date:
        
        day_last_sunday = (start_date.weekday() + 1) % 7
        last_sunday = start_date - timedelta(days=day_last_sunday)
        ongoing_week = (date.today() - last_sunday).days // 7
    else:
        ongoing_week = 0

    chit_number_combined = None
    if chit_Type and chit_Number:
        prefix = chit_Type.split('-')[0].upper()

        if chit_Number.isdigit(): 
            formatted_number = chit_Number.zfill(4)
            chit_number_combined = f"{prefix}{formatted_number}"
        else:
            chit_number_combined = chit_Number.upper()

        chit = ChitRegistration.objects.filter(
            chit_Number__iexact=chit_number_combined
        ).first()

    if chit:
            base_amount = config_values.get(chit.chit_Type, 0)
            num_of_chits = chit.num_Of_Chits  
            chit_amount = base_amount * num_of_chits 

            last_payment = Payment.objects.filter(chit_id=chit.id).order_by('-total_paid_week').first()
            total_paid_week = last_payment.total_paid_week if last_payment else 0

            paid_weeks = list(
                Payment.objects.filter(chit_id=chit.id)
                .values_list('payment_weeks', flat=True)
            )

    return render(request, 'view_chits.html', {
        'chit': chit,
        'chit_amount': chit_amount,
        'total_paid_week': total_paid_week,
        'paid_weeks': paid_weeks,
        'weeks': range(1, 53),
        'chit_type_list': chit_type_list,
        'selected_chit_type': chit_Type,
        'ongoing_week': ongoing_week,  
    })


def edit_chit(request, chit_id):
    chit = get_object_or_404(ChitRegistration, id=chit_id)

    if request.method == "POST":
        form = ChitForm(request.POST, instance=chit)
        if form.is_valid():
            form.instance.chit_Type = chit.chit_Type
            form.instance.chit_Number = chit.chit_Number
            form.instance.num_Of_Chits = chit.num_Of_Chits
            form.save()
            return redirect('view_chits')

    else:
        form = ChitForm(instance=chit)

    return render(request, 'edit_chit.html', {'form': form, 'chit': chit})


def handle_payment(request, chit_id):
    app_config()

    chit = get_object_or_404(ChitRegistration, id=chit_id)

    last_payment = Payment.objects.filter(chit_id=chit_id).order_by('-total_paid_week').first()
    total_paid_week = last_payment.total_paid_week if last_payment else 0  

    if request.method == "POST":
        chitnumber = request.POST.get("chitnumber", "").strip()
        payment_weeks = int(request.POST.get("payment_weeks", "0") or 0)
        overdue_fees = int(request.POST.get("overdue_fees", "0") or 0)
        cash_received = int(request.POST.get("cash_received", "0") or 0)
        amount_per_week = config_values.get(chit.chit_Type, 0) * chit.num_Of_Chits
    

        num_of_chits = chit.num_Of_Chits if chit.num_Of_Chits else 1 

        total_amount = (payment_weeks * amount_per_week) + overdue_fees
        balance = cash_received - total_amount
        new_total_paid_week = total_paid_week + payment_weeks

        payment = Payment.objects.create(
            chit_id=chit_id,
            chitnumber=chitnumber,
            payment_weeks=payment_weeks,
            amount_per_week=amount_per_week,
            total_amount=total_amount,
            overdue_fees=overdue_fees,
            cash_received=cash_received,
            balance=balance,
            total_paid_week=new_total_paid_week,
            timestamp=datetime.now(),
            num_of_chits=num_of_chits 
        )

        return redirect('payment_summary', chit_id=chit_id)  

    return render(request, 'view_chits.html', {'chit': chit})


def payment_summary(request, chit_id):

    payments = Payment.objects.filter(chit_id=chit_id).order_by('-payment_id')

    return render(request, 'payment_summary.html', {'payments': payments})


@admin_only
def summary_page(request):
    
    app_config()
    
    date_entry = AdminConfig.objects.filter(key="START_DATE").first()
    start_date = None

    if date_entry:
        try:
            start_date = datetime.strptime(date_entry.value, "%d/%m/%Y").date()
        except ValueError:
            start_date = None  

    if start_date:
        day_last_sunday = (start_date.weekday() + 1) % 7
        last_sunday = start_date - timedelta(days=day_last_sunday)
        total_weeks_now = (date.today() - last_sunday).days // 7
    else:
        total_weeks_now = 0

    summary_data = []
    
    for chit_type, amount_per_week in config_values.items():
        if chit_type == "CHIT_TYPE":
            continue

        chit_type = chit_type.strip()

        chits = ChitRegistration.objects.filter(chit_Type=chit_type)
        total_people = chits.count()

        if total_people == 0:
            summary_data.append({
                'chit_type': chit_type,
                'chit_amount': amount_per_week,
                'total_people': total_people,
                'total_weeks_now': total_weeks_now,
                'total_paid_weeks': 0,
                'total_amount_paid': 0,
                'expected_paid_total': 0,
                'pending_amount': 0,
                'total_people_paid': 0,
                'total_chits': 0,
                'total_amount': 0,
            })
            continue  

        total_paid_weeks = Payment.objects.filter(chit_id__in=chits.values_list('id', flat=True)).aggregate(total_weeks=Sum('payment_weeks'))['total_weeks'] or 0

        total_amount_paid = Payment.objects.filter(chit_id__in=chits.values_list('id', flat=True)).aggregate(amount_paid=Sum('total_amount'))['amount_paid'] or 0

        total_people_paid = Payment.objects.filter(chit_id__in=chits.values_list('id', flat=True)).values('chit_id').distinct().count()

        total_chits = chits.aggregate(total_chits=Sum('num_Of_Chits'))['total_chits'] or 0

        expected_paid_total = total_chits * total_weeks_now * amount_per_week

        pending_amount = expected_paid_total - total_amount_paid
        
        total_amount = total_chits * 52 * amount_per_week


        summary_data.append({
            'chit_type': chit_type,
            'chit_amount': amount_per_week,
            'total_people': total_people,
            'total_weeks_now': total_weeks_now,
            'total_paid_weeks': total_paid_weeks,
            'total_amount_paid': total_amount_paid,
            'expected_paid_total': expected_paid_total,
            'pending_amount': pending_amount,
            'total_people_paid': total_people_paid,
            'total_chits': total_chits,
            'total_amount': total_amount,
        })
    
    return render(request, 'summary.html', {'summary_data': summary_data})


def daily_summary_page(request):
    app_config()

    today = date.today()
    start_date = today - timedelta(days=7)
    date_range = [start_date + timedelta(days=i) for i in range(8)]

    chit_types = [k.strip() for k in config_values.keys() if k != "CHIT_TYPE"]
    summary_data = []
    grand_total = 0  
    
    daily_grand_totals = [0] * len(date_range)
    for chit_type in chit_types:
        amount_per_week = config_values[chit_type]
        chit_ids = ChitRegistration.objects.filter(chit_Type=chit_type).values_list('id', flat=True)

        daily_amounts = []
        for idx, day in enumerate(date_range):
            day_amount = Payment.objects.filter(
                chit_id__in=chit_ids,
                timestamp__date=day
            ).aggregate(day_total=Sum('total_amount'))['day_total'] or 0
            daily_amounts.append(day_amount)

            daily_grand_totals[idx] += day_amount

        total_amount = sum(daily_amounts)
        grand_total += total_amount  

        summary_data.append({
            'chit_type': chit_type,
            'chit_amount': amount_per_week,
            'daily_amounts': daily_amounts,
            'total_amount_in_range': total_amount,
        })

    context = {
        'summary_data': summary_data,
        'date_range': date_range,
        'grand_total': grand_total,
        'daily_grand_totals': daily_grand_totals,
        'colspan_total': 2 + len(date_range), 
    }

    return render(request, 'daily_summary.html', context)


@admin_only
def pending_week(request):
    
    date_entry = AdminConfig.objects.filter(key="START_DATE").first()
    start_date = None
    ongoing_week = 0

    if date_entry:
        try:
            start_date = datetime.strptime(date_entry.value, "%d/%m/%Y").date()
        except ValueError:
            start_date = None

    if start_date:
        day_last_sunday = (start_date.weekday() + 1) % 7
        last_sunday = start_date - timedelta(days=day_last_sunday)
        ongoing_week = (date.today() - last_sunday).days // 7
    else:
        ongoing_week = 0  

    chitnumbers_below = (
        Payment.objects
        .values('chitnumber')
        .annotate(max_paid_week=Max('total_paid_week'))
        .filter(max_paid_week__lt=ongoing_week)
        .values_list('chitnumber', flat=True)
    )

    pending_people = ChitRegistration.objects.filter(chit_Number__in=chitnumbers_below)

    payments_sum = (
        Payment.objects
        .filter(chitnumber__in=chitnumbers_below)
        .values('chitnumber')
        .annotate(total_paid=Max('total_paid_week'))
    )
    payment_map = {item['chitnumber']: item['total_paid'] for item in payments_sum}

    pending_data = []

    for person in pending_people:
        paid = payment_map.get(person.chit_Number, 0)
        pending_data.append({
            'chitid': person.id,
            'person': person,
            'total_weeks_now': ongoing_week,
            'paid_weeks': paid,
            'pending_weeks': ongoing_week - paid
        })

    context = {
        'pending_data': pending_data,
        'ongoing_week': ongoing_week,  
    }
    return render(request, 'unpaid_week.html', context)


@admin_only
def chit_payment_detail(request, chit_id):

    person = get_object_or_404(ChitRegistration, id=chit_id)
    payments = Payment.objects.filter(chitnumber=person.chit_Number).order_by('-timestamp')

    payment_details = []
    for pay in payments:
        formatted_time=pay.timestamp.strftime('%d.%m.%y %H:%M:%S')
        payment_details.append({
            'chit_id': pay.chit_id,
            'chitnumber': pay.chitnumber,
            'payment_weeks': pay.payment_weeks,
            'amount_per_week': pay.amount_per_week,
            'total_amount': pay.total_amount,
            'overdue_fees': pay.overdue_fees,
            'cash_received': pay.cash_received,
            'balance': pay.balance,
            'total_paid_week': pay.total_paid_week,
            'timestamp': formatted_time,
            'num_of_chits': pay.num_of_chits,
        })

    context = {
        'person': person,
        'payment_details': payment_details,
    }
    return render(request, 'payment_week_detail.html', context)


@admin_only
@csrf_exempt
def send_all_whatsapp_messages(request):
    if request.method == 'POST':
        date_entry = AdminConfig.objects.filter(key="START_DATE").first()
        start_date = None
        ongoing_week = 0

        if date_entry:
            try:
                start_date = datetime.strptime(date_entry.value, "%d/%m/%Y").date()
            except ValueError:
                start_date = None

        if start_date:
            day_last_sunday = (start_date.weekday() + 1) % 7
            last_sunday = start_date - timedelta(days=day_last_sunday)
            ongoing_week = (date.today() - last_sunday).days // 7

        chitnumbers_below = (
            Payment.objects
            .values('chitnumber')
            .annotate(max_paid_week=Max('total_paid_week'))
            .filter(max_paid_week__lt=ongoing_week)
            .values_list('chitnumber', flat=True)
        )

        pending_people = ChitRegistration.objects.filter(chit_Number__in=chitnumbers_below)

        payments_sum = (
            Payment.objects
            .filter(chitnumber__in=chitnumbers_below)
            .values('chitnumber')
            .annotate(total_paid=Max('total_paid_week'))
        )
        payment_map = {item['chitnumber']: item['total_paid'] for item in payments_sum}

        already_sent_today_chits = set(
            WhatsAppMessageLog.objects
            .filter(sent_time__date=date.today(), status='Sent')
            .values_list('chit_number', flat=True)
        )

        for person in pending_people:
            chit_number = person.chit_Number

            if chit_number in already_sent_today_chits:
                print(f"⏭️ Already messaged today for {chit_number}")
                continue

            name = person.name
            phone = person.phoneNumber
            whatsapp_enabled = person.whatsapp.strip().lower() == 'yes' 
            paid_weeks = payment_map.get(chit_number, 0)
            pending = max(ongoing_week - paid_weeks, 0)

            msg = f'''
            அன்பார்ந்த மகிழ் வாடிக்கையாளர்களே!
            தங்கள் தீபாவளி வாராந்திர சீட்டு எண் மற்றும் பெயர்:
            சீட்டு எண்: {chit_number}
            பெயர்: {name}

            இதுவரை செலுத்திய வாரங்கள்: {paid_weeks}
            மொத்தம் செலுத்த வேண்டிய வாரங்கள்: {ongoing_week}
            பாக்கி வாரங்கள்: {pending}

            தயவுசெய்து உங்கள் பாக்கி தொகையை சீக்கிரம் செலுத்தவும்.

            நன்றி,
            அன்புடன்,
            மகிழ் கஃபே!
            '''

            status = "Failed"
            error_message = ""

            if whatsapp_enabled:
                valid_phone = re.fullmatch(r'[6-9]\d{9}', phone)
                if valid_phone:
                    try:
                        kit.sendwhatmsg_instantly(f'+91{phone}', msg, 15, 20)
                        print(f"✅ Message sent to {chit_number} - {name}")
                        status = "Sent"
                    except Exception as e:
                        print(f"❌ Failed to send message to {chit_number} - {name}: {e}")
                        error_message = str(e)
                else:
                    error_message = "Invalid phone number"
            else:
                error_message = "WhatsApp not enabled for this chitnumber"

            WhatsAppMessageLog.objects.create(
                chit_number=chit_number,
                name=name,
                phone_number=phone,
                message=msg.strip(),
                status=status,
                error_message=error_message,
                
            )

    return redirect('pending_week')


@admin_only
def show_whatsapp_messages(request):

    #file_path = 'pyWhatKit_DB.txt'  
    messages = []

    """if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            file_messages = content.strip().split('--------------------')
            messages.extend([msg.strip() for msg in file_messages if msg.strip()])"""

    db_messages = WhatsAppMessageLog.objects.all().values('message', 'phone_number','sent_time','status').order_by('sent_time')
    messages.extend(list(db_messages))

    context = {
        'messages': messages
    }
    return render(request, 'show_messages.html', context)

def daily_view_payment_summary(request):
    today = now().date()
    payments = Payment.objects.filter(timestamp__date=today)

    summary = payments.values('chit_id', 'chitnumber').annotate(
        payment_weeks=Sum('payment_weeks'),
        amount_per_week=Sum('amount_per_week'),
        total_amount=Sum('total_amount'),
        overdue_fees=Sum('overdue_fees'),
        cash_received=Sum('cash_received'),
        balance=Sum('balance'),
        total_paid_week=Sum('total_paid_week'),
        num_of_chits=Count('chit_id'),
        timestamp=Max('timestamp') 
    )

    context = {
        'summary': summary
    }
    return render(request, 'daily_view_payment_summary.html', context)


def total_payment_summary(request):
  
    selected_date = request.GET.get('date')  

    all_dates_qs = Payment.objects.values_list('timestamp__date', flat=True).distinct().order_by('timestamp__date')
    all_dates = [d.strftime('%Y-%m-%d') for d in all_dates_qs if d]

    chits = ChitRegistration.objects.all()

    summary_data = []

    for chit in chits:
        payments = Payment.objects.filter(chit_id=chit.id)

        if selected_date:
            payments = payments.filter(timestamp__date=selected_date)

        total_paid_weeks = payments.aggregate(Max('total_paid_week'))['total_paid_week__max'] or 0
        total_amount_paid = payments.aggregate(Sum('cash_received'))['cash_received__sum'] or 0

        payment_details = []
        for p in payments.order_by('timestamp'):
            payment_details.append({
                'date': p.timestamp.strftime('%Y-%m-%d') if p.timestamp else 'N/A',
                'weeks_paid': p.payment_weeks,
                'amount_paid': p.cash_received,
                'amount_per_week': p.amount_per_week,
            })

        summary_data.append({
            'name': chit.name,
            'chit_number': chit.chit_Number,
            'total_weeks_paid': total_paid_weeks,
            'total_amount_paid': total_amount_paid,
            'payment_details': payment_details,
        })

    return render(request, 'total_payment_summary.html', {
        'summary_data': summary_data,
        'all_dates': all_dates,
        'selected_date': selected_date,
    })
