from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout

from .forms import ReportForm, PatientForm
from .models import Report, Patient


def index(request):
    return render(request, "patients/index.html")


def report(request):
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("patients:thank_you")
    else:
        form = ReportForm()
    return render(request, "patients/report.html", {"form": form})


def thank_you(request):
    return render(request, "patients/thank_you.html")


@login_required
def review(request):
    reports = Report.objects.filter(report_state=Report.REPORTED)
    return render(request, "patients/review.html", {"reports": reports})


def login_form(request):
    return render(request, "patients/login.html")


@login_required
def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect("patients:index")


@login_required
def review_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    request.session["reviewing_report"] = report_id
    return render(request, "patients/review_report.html", {"report": report})


@login_required
def add_patient(request):
    report_id = request.session.get("reviewing_report", None)
    if not report_id:
        return redirect("patients:review")

    report = get_object_or_404(Report, pk=report_id)
    patient = Patient.from_report(report)

    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            ## TODO add messages
            if "submit" in request.POST:
                form.save()
                report.report_state = report.PATIENT_ADDED
                report.save()
            elif "mark_verified" in request.POST:
                report.report_state = report.VERIFIED
                report.save()
            del request.session["reviewing_report"]
            return redirect("patients:review")
    else:
        form = PatientForm(instance=patient)
    return render(
        request,
        "patients/add_patient.html",
        {"patient": patient, "form": form, "report_id": report_id},
    )

@login_required
def mark_report_invalid(request):
    report_id = request.session.get("reviewing_report", None)
    if not report_id:
        return redirect("patients:review")

    report = get_object_or_404(Report, pk=report_id)
    report.report_state = Report.INVALID
    report.save()
    # TODO post a message
    del request.session["reviewing_report"]

    return render(request, "patients/review.html")
