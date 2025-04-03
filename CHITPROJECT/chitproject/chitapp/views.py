from django.shortcuts import render, redirect, get_object_or_404
from .models import ChitRegistration,Payment
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


def index(request):
    return render(request, 'chitapp/index.html')

def is_admin(user):
    return user.is_superuser

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
        chit_types = chit_type_entry.value.split(',')  
        for chit in chit_types:
            parts = chit.split('-')
            if len(parts) > 1 and parts[1].isdigit():  
                config_values[chit] = int(parts[1])  

def config_view(request):
    configs = AdminConfig.objects.order_by("id")  

    if request.method == "POST":
        for config in configs:
            key_name = f"key_{config.id}"
            value_name = f"value_{config.id}"
            
            if key_name in request.POST and value_name in request.POST:
                config.key = request.POST[key_name]
                config.value = request.POST[value_name]
                config.save()

        return redirect("config_view")  
    return render(request, "config_view.html", {"configs": configs})

def admin_config_view(request):
    configs = AdminConfig.objects.order_by("id")
    form = AdminConfigForm()

    if request.method == 'POST':
        key_list = request.POST.getlist('key')
        value_list = request.POST.getlist('value')

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

def register_chit(request):

    chit_register()
    
    chitvalue = AdminConfig.objects.filter(key="CHIT_TYPE").values_list("value", flat=True).first()
    chit_type = chitvalue.split(",") 
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

    app_config()

    chit = None
    chit_amount = 0
    total_paid_week = 0
    paid_weeks = []

    chit_Type = request.GET.get("chit_Type")
    chit_Number = request.GET.get("chit_Number")

    if chit_Type and chit_Number:

        chit = ChitRegistration.objects.filter(chit_Type=chit_Type, chit_Number=chit_Number).first()

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
            num_Of_Chits=num_of_chits,
        )

        return redirect('payment_summary', chit_id=chit_id)  

    return render(request, 'view_chits.html', {'chit': chit})

def payment_summary(request, chit_id):

    payments = Payment.objects.filter(chit_id=chit_id).order_by('-payment_id')

    return render(request, 'payment_summary.html', {'payments': payments})


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
