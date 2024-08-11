import hmac
import hashlib
import os
import subprocess
from urllib.parse import parse_qs
from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta, timezone

# both library use to take get network related info. on the server
import psutil
import socket

from qrcode_app.models import Device
from .forms import DeviceForm


SECRET_KEY = 'loveyou3000'  # Make sure this matches the one in your QR code generation

@csrf_exempt  # Exempt CSRF for testing purposes; use proper CSRF handling in production
def verify_qr_code(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Invalid request method.")
    
    # Extract query parameters
    user_email = request.GET.get('email')
    timestamp = request.GET.get('timestamp')
    received_hash = request.GET.get('hash')

    if not user_email or not timestamp or not received_hash:
        return HttpResponseBadRequest("Missing required parameters.")
    
    try:
        timestamp = int(timestamp)
    except ValueError:
        return HttpResponseBadRequest("Invalid timestamp format.")

    # Convert timestamp to datetime object with timezone
    timestamp_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    current_time = datetime.now(timezone.utc)

    # Verify timestamp (QR code should be valid for 5 minutes)
    time_diff = current_time - timestamp_dt
    if time_diff > timedelta(minutes=5):
        return HttpResponseBadRequest("QR code has expired.")
    
    # Recreate the hash
    data_to_hash = f"{user_email}{timestamp}"
    expected_hash = hmac.new(SECRET_KEY.encode(), data_to_hash.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_hash, received_hash):
        return HttpResponseBadRequest("Invalid QR code.")
    
    # Successful verification
    context = {
        "email": user_email,
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return render(request, 'qr_code_verification.html', context)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_mac_address(ip_address):
    # This function assumes it can map the IP to a MAC address in a controlled network.
    # Here we use the IP of the server as an example for demonstration.
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == psutil.AF_LINK:
                return snic.address
    return None

def device_info(request: HttpRequest):
    client_ip = get_client_ip(request)
    client_mac = get_mac_address(client_ip)

    context = {
        'ip_address': client_ip,
        'mac_address': client_mac or 'MAC address could not be determined',
    }
    return render(request, 'device_info.html', context)


def get_network_info():
    network_info = []
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            info = {
                'interface': interface,
                'address': snic.address,
                'netmask': snic.netmask,
                'broadcast': snic.broadcast,
                'family': snic.family,
            }
            network_info.append(info)
    return network_info

def get_device_serial_number():
    serial_number = "N/A"
    try:
        if os.name == 'nt':  # Windows
            command = 'wmic bios get serialnumber'
            serial_number = subprocess.check_output(command, shell=True).decode().split('\n')[1].strip()
        elif os.name == 'posix':  # Linux
            with open('/sys/class/dmi/id/product_serial') as f:
                serial_number = f.read().strip()
    except Exception as e:
        print(f"Error retrieving serial number: {e}")
    return serial_number

def device_info_full(request: HttpRequest):
    client_ip = get_client_ip(request)
    network_info = get_network_info()
    device_serial_no = get_device_serial_number()

    context = {
        'ip_address': client_ip,
        'network_info': network_info,
        'device_serial_no': device_serial_no,
    }
    return render(request, 'device_info_full.html', context)


# this is for the model code


def register_device(request):
    client_ip = get_client_ip(request)
    client_mac = get_mac_address(client_ip)
    device_serial_no = get_device_serial_number()

    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.mac_address = client_mac or 'MAC address could not be determined'
            device.serial_number = device_serial_no
            device.save()
            return render(request, 'success.html')  # Redirect to a success page or another page as needed
    else:
        form = DeviceForm()

    context = {
        'form': form,
        'ip_address': client_ip,
        'mac_address': client_mac or 'MAC address could not be determined',
        'device_serial_no': device_serial_no,
    }
    

    return render(request, 'register_device.html', context)




# New code for the verify and details
@csrf_exempt
def verify(request):
    if request.method == 'GET':
        # QR Code Verification Logic
        user_email = request.GET.get('email')
        timestamp = request.GET.get('timestamp')
        received_hash = request.GET.get('hash')

        if not user_email or not timestamp or not received_hash:
            return HttpResponseBadRequest("Missing required parameters.")

        try:
            timestamp = int(timestamp)
        except ValueError:
            return HttpResponseBadRequest("Invalid timestamp format.")

        timestamp_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - timestamp_dt

        if time_diff > timedelta(minutes=5):
            return HttpResponseBadRequest("QR code has expired.")

        data_to_hash = f"{user_email}{timestamp}"
        expected_hash = hmac.new(SECRET_KEY.encode(), data_to_hash.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            return HttpResponseBadRequest("Invalid QR code.")

        # Automatically save device information
        client_ip = get_client_ip(request)
        client_mac = get_mac_address(client_ip)
        device_serial_no = get_device_serial_number()

        device = Device(
            email=user_email,
            mac_address=client_mac or 'MAC address could not be determined',
            serial_number=device_serial_no
        )
        device.save()

        # Render confirmation page
        context = {
            'email': user_email,
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'ip_address': client_ip,
            'mac_address': client_mac or 'MAC address could not be determined',
            'device_serial_no': device_serial_no
        }
        
        return render(request, 'verify.html', context)
    else:
        return HttpResponseBadRequest("Invalid request method.")