from django.shortcuts import render,redirect,reverse
# from . import forms,models
# from .
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from .models import Doctor, Patient
from .forms import AppointmentForm,AdminSigupForm, DoctorUserForm,DoctorForm,PatientUserForm,PatientForm,PatientAppointmentForm,ContactusForm
from .models import UploadedFile
from .forms import UploadFileForm
from .mlmodels.typeGetter import getFileType
from .mlmodels.model_loader import load_model
from .mlmodels.upload_report import upload_to_s3 

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/index.html')


#for showing signup/login button for admin(by sumit)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/adminclick.html')


#for showing signup/login button for doctor(by sumit)
def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/doctorclick.html')


#for showing signup/login button for patient(by sumit)
def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'hospital/patientclick.html')




def admin_signup_view(request):
    form=AdminSigupForm()
    if request.method=='POST':
        form=AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request,'hospital/adminsignup.html',{'form':form})




def doctor_signup_view(request):
    userForm=DoctorUserForm()
    doctorForm=DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=DoctorUserForm(request.POST)
        doctorForm=DoctorForm(request.POST,request.FILES)
        print('docrt valid:',userForm.is_valid(),doctorForm.is_valid())
        print(doctorForm.errors)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            print('user:',user,user.id)
            user.save()
            print('after user:',user,user.id)
            doctor=doctorForm.save(commit=False)
            doctor.user=user
            print('doctor:',doctor,doctor.user.id)
            doctor.save()
            print('after save doctor:',doctor,doctor.user.id)
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return HttpResponseRedirect('doctorlogin')
    return render(request,'hospital/doctorsignup.html',context=mydict)


def patient_signup_view(request):
    userForm=PatientUserForm()
    patientForm=PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=PatientUserForm(request.POST)
        patientForm=PatientForm(request.POST,request.FILES)
        print('validation:',userForm.is_valid(),patientForm.is_valid())
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient=patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return HttpResponseRedirect('patientlogin')
    return render(request,'hospital/patientsignup.html',context=mydict)







#-----------for checking user is doctor , patient or admin(by sumit)
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        accountapproval=models.Doctor.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('doctor-dashboard')
        else:
            return render(request,'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        accountapproval=models.Patient.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('patient-dashboard')
        else:
            return render(request,'hospital/patient_wait_for_approval.html')








#---------------------------------------------------------------------------------
#-------------------admin views------------------------------------------------
# ----------------------------------------------------------------
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from datetime import date
from . import models, forms
from django.template.loader import get_template
import io
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404, redirect
from .models import Doctor
from .models import Doctor
from django.shortcuts import render, get_object_or_404, redirect
from .models import Doctor
from .forms import DoctorForm

# 1. Admin Doctor List View
def admin_doctor_view(request):
    doctors = Doctor.objects.all()
    return render(request, 'hospital/admin_doctor.html', {'doctors': doctors})

# 2. Delete Doctor View
def delete_doctor_from_hospital_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor.delete()
    return redirect('admin-doctor')

# 3. Update Doctor View
def update_doctor_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('admin-doctor')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'hospital/update_doctor.html', {'form': form, 'doctor': doctor})


def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    doctors = models.Doctor.objects.all().order_by('-id')
    patients = models.Patient.objects.all().order_by('-id')

    doctorcount = doctors.filter(status=True).count()
    pendingdoctorcount = doctors.filter(status=False).count()

    patientcount = patients.filter(status=True).count()
    pendingpatientcount = patients.filter(status=False).count()

    appointmentcount = models.Appointment.objects.filter(status=True).count()
    pendingappointmentcount = models.Appointment.objects.filter(status=False).count()

    context = {
        'doctors': doctors,
        'patients': patients,
        'doctorcount': doctorcount,
        'pendingdoctorcount': pendingdoctorcount,
        'patientcount': patientcount,
        'pendingpatientcount': pendingpatientcount,
        'appointmentcount': appointmentcount,
        'pendingappointmentcount': pendingappointmentcount,
    }
    return render(request, 'hospital/admin_dashboard.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)


def delete_doctor_from_hospital_view(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor.delete()
    return redirect('admin-doctor')  # Adjust the redirect as needed

def admin_add_doctor_view(request):
    if request.method == 'POST':
        userForm = DoctorUserForm(request.POST)
        doctorForm =DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save(commit=False)
            user.set_password(user.password)
            user.save()

            doctor = doctorForm.save(commit=False)
            doctor.user = user
            doctor.status = True
            doctor.save()

            doctor_group, created = Group.objects.get_or_create(name='DOCTOR')
            doctor_group.user_set.add(user)

            return redirect('admin-view-doctor')
    else:
        userForm = DoctorUserForm()
        doctorForm =DoctorForm()

    context = {'userForm': userForm, 'doctorForm': doctorForm}
    return render(request, 'hospital/admin_add_doctor.html', context)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors = models.Doctor.objects.filter(status=True)
    return render(request, 'hospital/admin_view_doctor.html', {'doctors': doctors})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)

            try:
                appointment.doctorId = int(request.POST.get('doctorId'))
                appointment.patientId = int(request.POST.get('patientId'))

                appointment.doctorName = User.objects.get(id=appointment.doctorId).first_name
                appointment.patientName = User.objects.get(id=appointment.patientId).first_name

                appointment.status = True
                appointment.save()

                return redirect('admin-view-appointment')
            except (User.DoesNotExist, ValueError):
                form.add_error(None, 'Invalid Doctor or Patient ID')

    else:
        form = AppointmentForm()

    return render(request, 'hospital/admin_add_appointment.html', {'appointmentForm': form})




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request, pk):
    doctor = get_object_or_404(models.Doctor, id=pk)
    doctor.status = True
    doctor.save()
    return redirect('admin-approve-doctor')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assignedDoctorId=request.POST.get('assignedDoctorId')
            patient.save()

            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request, pk):
    doctor = get_object_or_404(models.Doctor, id=pk)
    doctor.user.delete()
    doctor.delete()
    return redirect('admin-approve-doctor')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    #those whose approval are needed
    patients=models.Patient.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_patient.html',{'patients':patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    patient.status=True
    patient.save()
    return redirect(reverse('admin-approve-patient'))



def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    days=(date.today()-patient.admitDate) #2 days, 0:00:00
    assignedDoctor=models.User.objects.all().filter(id=patient.assignedDoctorId)
    d=days.days # only how many day that is 2
    patientDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'day':d,
        'assignedDoctorName':assignedDoctor[0].first_name,
    }
    if request.method == 'POST':
        feeDict ={
            'roomCharge':int(request.POST['roomCharge'])*int(d),
            'doctorFee':request.POST['doctorFee'],
            'medicineCost' : request.POST['medicineCost'],
            'OtherCharge' : request.POST['OtherCharge'],
            'total':(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        }
        patientDict.update(feeDict)
        #for updating to database patientDischargeDetails (pDD)
        pDD=models.PatientDischargeDetails()
        pDD.patientId=pk
        pDD.patientName=patient.get_name
        pDD.assignedDoctorName=assignedDoctor[0].first_name
        pDD.address=patient.address
        pDD.mobile=patient.mobile
        pDD.symptoms=patient.symptoms
        pDD.admitDate=patient.admitDate
        pDD.releaseDate=date.today()
        pDD.daySpent=int(d)
        pDD.medicineCost=int(request.POST['medicineCost'])
        pDD.roomCharge=int(request.POST['roomCharge'])*int(d)
        pDD.doctorFee=int(request.POST['doctorFee'])
        pDD.OtherCharge=int(request.POST['OtherCharge'])
        pDD.total=(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        pDD.save()
        return render(request,'hospital/patient_final_bill.html',context=patientDict)
    return render(request,'hospital/patient_generate_bill.html',context=patientDict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_discharge_patient.html',{'patients':patients})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def download_pdf_view(request, pk):
    dischargeDetails = models.PatientDischargeDetails.objects.filter(patientId=pk).order_by('-id').first()
    if dischargeDetails:
        context = {
            'patientName': dischargeDetails.patientName,
            'assignedDoctorName': dischargeDetails.assignedDoctorName,
            'address': dischargeDetails.address,
            'mobile': dischargeDetails.mobile,
            'symptoms': dischargeDetails.symptoms,
            'admitDate': dischargeDetails.admitDate,
            'releaseDate': dischargeDetails.releaseDate,
            'daySpent': dischargeDetails.daySpent,
            'medicineCost': dischargeDetails.medicineCost,
            'roomCharge': dischargeDetails.roomCharge,
            'doctorFee': dischargeDetails.doctorFee,
            'OtherCharge': dischargeDetails.OtherCharge,
            'total': dischargeDetails.total,
        }
        return render_to_pdf('hospital/download_bill.html', context)
    return HttpResponse("No discharge details available.")



# #---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    patients = models.Patient.objects.all().order_by('-id')  # Fetch all patients in descending order

    context = {
        'patients': patients,
    }
    return render(request, 'hospital/admin_patient.html', context)





#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    #for three cards
    patientcount=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).count()
    appointmentcount=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).count()
    patientdischarged=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name).count()

    #for  table in doctor dashboard
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id).order_by('-id')
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid).order_by('-id')
    appointments=zip(appointments,patients)
    mydict={
    'patientcount':patientcount,
    'appointmentcount':appointmentcount,
    'patientdischarged':patientdischarged,
    'appointments':appointments,
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_dashboard.html',context=mydict)



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)





@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    patients=models.Patient.objects.all().filter(status=True,assignedDoctorId=request.user.id).filter(Q(symptoms__icontains=query)|Q(user__first_name__icontains=query))
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients=models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_discharge_patient.html',{'dischargedpatients':dischargedpatients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):

    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId__user_id=request.user.id)

    # patient_ids = appointments.values_list('patientId_id', flat=True)
    patient_ids = appointments.values_list('patientId_id', flat=True).distinct()
    patients = Patient.objects.filter(status=True, id__in=patient_ids) if patient_ids else Patient.objects.none()
    patient_map = {patient.id: patient for patient in patients}
    appointments_with_patients = [(appointment, patient_map.get(appointment.patientId_id)) for appointment in appointments]

    # patients = Patient.objects.filter(status=True, id__in=patient_ids)
    
    # patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    # appointments=zip(appointments,patients)
    # patient_map = {patient.id: patient for patient in patients}
    # appointments_with_patients = [(appointment, patient_map.get(appointment.patientId_id)) for appointment in appointments] 
    # print('pts:',appointments)
    return render(request,'hospital/doctor_view_appointment.html',{'appointments':appointments_with_patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    print('check route')
    return render(request,'hospital/index.html')
    # return redirect('')

# Doctor Workload View
def doctor_workload_view(request):
    model = load_model()
    if not model:
        return
    print('modelloaded succ')
    appointments=models.Appointment.objects.all().filter(status=True,doctorId__user_id=request.user.id)
    patient_ids = appointments.values_list('patientId_id', flat=True).distinct()
    patients = Patient.objects.filter(status=True, id__in=patient_ids) if patient_ids else Patient.objects.none()
    patient_map = {patient.id: patient for patient in patients}
    appointments_with_patients = [(appointment, patient_map.get(appointment.patientId_id)) for appointment in appointments]

    print('patients:',patients)
    # sample = [[1, 10, 0.5, 1, 1, 0, 0, 1, 1, 2, 3, 3, 2023, 3, 5, 2023, 3, 7]]
    # print('predicted values:',pred)
    for a,p in appointments_with_patients:
        print('patient:',p.mobile)
        gender = 1 if a.gender == 'Male' else 0
        pred = model.predict([[
            gender,
            a.age,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        ]])
        print('res:',pred)
        p.workload = pred
    return render(request, 'hospital/doctor_workload.html',{"apPatients":appointments_with_patients})
    # return render(request, 'hospital/doctor_workload.html',{"patients":patients})



#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})

@login_required
def admin_add_appointment_view(request):
    # doctor = models.Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        # print('kakladnmlk')
        # print('chek: DoctorId: ',request.POST.get('doctorId'))
        appointment_form = PatientAppointmentForm(request.POST)
        # print('if valid:',appointment_form.errors)
        if appointment_form.is_valid():
            dctId = request.POST.get('doctorId')
            ptId = request.user.id
            appointment = appointment_form.save(commit=False)
            # print('started parsing')
            appointment.doctorId=Doctor.objects.get(id=dctId)
            
            appointment.patientId= Patient.objects.get(id=ptId) #----user can choose any patient but only their info will be stored
            appointment.symptom=request.POST.get('symptom')
            appointment.appointmentDate=request.POST.get('appointmentDate')
            appointment.gender=request.POST.get('gender') 
            appointment.age=request.POST.get('age')
            appointment.neighbourhood=request.POST.get('neighbourhood')
            appointment.scholarship = request.POST.get('scholarship') == '1'
            appointment.hypertension = request.POST.get('hypertension') == '1'
            appointment.diabetes = request.POST.get('diabetes') == '1'
            appointment.alcoholism = request.POST.get('alcoholism') == '1'
            appointment.handicap = request.POST.get('handicap') == '1'

            print('aapppp:',appointment)
            # appointment.patient = patient
            # appointment.doctor = models.Doctor.objects.get(id=request.POST.get('doctorId'))
            appointment.save()
            return redirect('patient-dashboard')
    else:
        appointment_form = PatientAppointmentForm()

    return render(request, 'hospital/admin_add_appointment.html', {
        'appointmentForm': appointment_form,
        # 'patient': patient,
    })

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')

#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    doctor=models.Doctor.objects.get(user_id=patient.assignedDoctorId)
    mydict={
    'patient':patient,
    'doctorName':doctor.get_name,
    'doctorMobile':doctor.mobile,
    'doctorAddress':doctor.address,
    'symptoms':patient.symptoms,
    'doctorDepartment':doctor.department,
    'admitDate':patient.admitDate,
    }
    return render(request,'hospital/patient_dashboard.html',context=mydict)



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def appointment_booking(request):
    doctors = Doctor.objects.all()  # Fetch all doctors
    return render(request, 'patient_book_appointment.html', {'doctors': doctors})
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})
#created
def get_doctors(request):
    doctors = Doctor.objects.values('id', 'name')  # Fetch doctors from DB
    return JsonResponse({'doctors': list(doctors)})

from django.shortcuts import render, redirect

from django.http import HttpResponseRedirect
from . import models, forms
from django.contrib.auth.decorators import login_required

@login_required
# views.py



@login_required
def patient_book_appointment_view(request):
    # print('req method,',request.method)
    
    patient = models.Patient.objects.get(user=request.user)  # Get the current patient


    if request.method == 'POST':
        # print('kakladnmlk')
        # print('chek: DoctorId: ',request.POST.get('doctorId'))
        appointment_form = PatientAppointmentForm(request.POST)
        # print('if valid:',appointment_form.errors)
        if appointment_form.is_valid():
            dctId = request.POST.get('doctorId')
            ptId = request.user.id
            appointment = appointment_form.save(commit=False)
            # print('started parsing')
            # doctor = Doctor.objects.filter(id=dctId).first()
            # print('test:',Doctor.objects.get(id=str(dctId)))
            # print('doc:',Doctor.objects.all())
            # doctors = Doctor.objects.all()
            # for doc in doctors:
            #     print(f"Doctor ID: {doc.id} {type(doc.id)}, User ID: {doc.user.id}, Name: {doc.get_name}")
            # appointment.doctorId=Doctor.objects.get(user_id=dctId)
            if Doctor.objects.filter(user_id=dctId).exists():
                print('doctor exists')
                appointment.doctorId = Doctor.objects.get(user_id=dctId)
            else:
                print(f"Doctor with ID {dctId} does not exist!")
    # messages.error(request, "Selected doctor does not exist.")
                return redirect('patient_book_appointment')
            appointment.patientId= Patient.objects.get(user_id=request.user.id) #----user can choose any patient but only their info will be stored
            print('user:',request.user.id, Patient.objects.get(user_id=request.user.id))
            appointment.symptom=request.POST.get('symptom')
            appointment.appointmentDate=request.POST.get('appointmentDate')
            appointment.gender=request.POST.get('gender') 
            appointment.age=request.POST.get('age')
            appointment.neighbourhood=request.POST.get('neighbourhood')
            appointment.scholarship = request.POST.get('scholarship') == '1'
            appointment.hypertension = request.POST.get('hypertension') == '1'
            appointment.diabetes = request.POST.get('diabetes') == '1'
            appointment.alcoholism = request.POST.get('alcoholism') == '1'
            appointment.handicap = request.POST.get('handicap') == '1'

            # print('aapppp:',appointment)
            # appointment.patient = patient
            # appointment.doctor = models.Doctor.objects.get(id=request.POST.get('doctorId'))
            appointment.save()
            return redirect('patient-dashboard')
    else:
        appointment_form = PatientAppointmentForm()

    return render(request, 'hospital/patient_book_appointment.html', {
        'appointmentForm': appointment_form,
        'patient': patient,
    })


"""def patient_dashboard(request):
    if request.method == 'POST':
        form = PatientFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            patient_file = form.save(commit=False)
            patient_file.patient = request.user
            patient_file.save()
            return redirect('patient-dashboard')
    else:
        form = PatientFileUploadForm()

    return render(request, 'hospital/patient_dashboard.html', {'form': form})"""
def patient_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})
def dashboard(request):
    return render(request, 'dashboard.html')

def search_doctor_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    
    # whatever user write in search box we get in query
    query = request.GET['query']
    doctors=models.Doctor.objects.all().filter(status=True).filter(Q(department__icontains=query)| Q(user__first_name__icontains=query))
    return render(request,'hospital/patient_view_doctor.html',{'patient':patient,'doctors':doctors})




@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    appointments=models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request,'hospital/patient_view_appointment.html',{'appointments':appointments,'patient':patient})



@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict=None
    if dischargeDetails:
        patientDict ={
        'is_discharged':True,
        'patient':patient,
        'patientId':patient.id,
        'patientName':patient.get_name,
        'assignedDoctorName':dischargeDetails[0].assignedDoctorName,
        'address':patient.address,
        'mobile':patient.mobile,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
        }
        print(patientDict)
    else:
        patientDict={
            'is_discharged':False,
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_discharge.html',context=patientDict)

def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.save()
            res = getFileType(uploaded.file)
            print('results:',res)
            upload_to_s3(uploaded.file.path,res)
            return redirect('view_files')
    else:
        form = UploadFileForm()
    return render(request, 'hospital/patient-fileupload.html', {'form': form})

def view_files(request):
    files = UploadedFile.objects.all()
    return render(request, 'hospital/view_files.html', {'files': files})

import random as rn
def random_times2():
    hr = rn.randint(0,23)
    mn = rn.randint(0,59)
    return f'{hr:02d}:{mn:02d}'
def opd_management(request):
    
    doctors = Doctor.objects.all()
    # patients = Patient.objects.all()
    appointments = models.Appointment.objects.all().filter(status=True)
    patient_ids = appointments.values_list('patientId_id', flat=True).distinct()
    patients = Patient.objects.filter(status=True, id__in=patient_ids) if patient_ids else Patient.objects.none()
    patient_map = {patient.id: patient for patient in patients}
    appointments_with_patients = [(appointment, patient_map.get(appointment.patientId_id)) for appointment in appointments]

    for a,p in appointments_with_patients:
        time = random_times()
        a.time = time
    appointments_with_patients = sorted(appointments_with_patients, key=lambda x: x[0].time)

    return render(request, 'hospital/opd_management.html', {'data':appointments_with_patients,'patients':appointments,'doctors': doctors})
    
def random_times():
    now = datetime.now()
    random_minutes = rn.randint(0, 59)
    random_hours = rn.randint(8, 18)  # Office hours: 8 AM - 6 PM
    return (now.replace(hour=random_hours, minute=random_minutes)).strftime("%H:%M")



import numpy as np
from openai import OpenAI

# EMA Calculation
N = 5  # Window size
alpha = 2 / (N + 1)

def calculate_ema(waiting_times):
    ema = waiting_times[0]  # Initialize EMA with the first value
    for wt in waiting_times:
        ema = alpha * wt + (1 - alpha) * ema
    return ema

# Initialize OpenAI client
base_url = "https://api.novita.ai/v3/openai"
api_key = "sk_V8Dr3N66LTCPXvBTKDycukJi8S70QGYbUX6gnFBzRRo"
model = "deepseek/deepseek-r1-turbo"

client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

# Severity Adjustment using LLM
def get_severity_score(symptoms):
    chat_completion_res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a medical assistant estimating OPD priority."},
            {"role": "user", "content": f"Given the symptoms: {symptoms}, estimate the severity on a scale of 0 to 1.Do not offer any explanation,just return the numerical score."}
        ],
        stream=False,
        extra_body={},
        max_tokens=1000
    )
    val = chat_completion_res.choices[0].message.content.split('\n')[-1]
    print('converting:',val)
    # return float(89.0)
    val=float(val.strip())
    return val

# Adjust Service Time
def calculate_service_time(waiting_times, symptoms):
    ema_wait_time = calculate_ema(waiting_times)
    severity_score = get_severity_score(symptoms)

    # Apply exponential decay adjustment
    adjusted_wait_time = ema_wait_time * np.exp(-severity_score)
    print('ts',adjusted_wait_time)
    return round(adjusted_wait_time,0)

def filter_appointments(request):
    doctor_id = request.GET.get('doctor_id')

    # Filter appointments by doctorId
    appointments = models.Appointment.objects.filter(doctorId_id=doctor_id).select_related('patientId')

    past_waiting_times = [15, 18, 22, 20, 25, 30, 35, 28, 24, 22]
    # Serialize the appointment data
    data = [
        {
            'patient_name': appointment.patientId.get_name,
            'symptom': appointment.symptom,
            'appointment_date': appointment.appointmentDate.strftime("%Y-%m-%d"),
            'age': appointment.age,
            'gender': appointment.gender,
            'time': random_times(),
            'service_time': calculate_service_time(past_waiting_times, appointment.symptom)
        }
        for appointment in appointments
    ]
    # data = sorted(data,lambda dt: dt.time)

    return JsonResponse({'data': data})
#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START ------------------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'hospital/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})


#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------




