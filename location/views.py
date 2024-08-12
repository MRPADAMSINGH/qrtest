import hmac
import pytz
import hashlib
from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, sqrt, atan2
import os
import subprocess
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import psutil

from location.forms import Test1Form
from qrcode_app.models import Device
from django.utils import timezone


# Secret key used for HMAC hashing (must match the one used for generating the QR code)
SECRET_KEY = 'loveyou3000'

# College location coordinates (latitude, longitude)
COLLEGE_LOCATION = (19.053706817710122, 72.87980643137657)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in meters between two locations on the Earth using the Haversine formula.
    """
    R = 6371000  # Radius of the Earth in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    
    a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def generate_map_image(user_lat, user_lon, college_lat, college_lon, in_range):
    """
    Generate a map image with the user's and college's locations marked, using generative AI.
    """
    prompt = f"Generate a map showing a location at ({college_lat}, {college_lon}) with a {20} meter radius circle."
    if in_range:
        prompt += f" Also, mark a second location at ({user_lat}, {user_lon}) within the circle."
    else:
        prompt += f" Also, mark a second location at ({user_lat}, {user_lon}) outside the circle."
    
    # Here, you would use a generative AI model (like DALL-E) to create the image
    # Example (this requires the appropriate API and configuration):
    map_image = dalle.text2im({ # type: ignore
        "size": "1024x1024",
        "prompt": prompt
    })

    return map_image

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

@csrf_exempt  # Exempt CSRF for testing purposes; use proper CSRF handling in production
def verify_location_qr_code(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Invalid request method.")
    
    # Extract query parameters
    user_email = request.GET.get('email')
    timestamp = request.GET.get('timestamp')
    received_hash = request.GET.get('hash')

    # Ensure all parameters are present
    if not all([user_email, timestamp, received_hash]):
        missing_params = [param for param in ['email', 'timestamp', 'hash'] if not request.GET.get(param)]
        return HttpResponseBadRequest(f"Missing required parameters: {', '.join(missing_params)}")
    
    try:
        timestamp = int(timestamp)
    except ValueError:
        return HttpResponseBadRequest("Invalid parameter format.")

    # Convert timestamp to a datetime object with timezone
    # timestamp_dt = datetime.fromtimestamp(timestamp, pytz.utc)
    # current_time = datetime.now(pytz.utc)
# Define IST timezone
    ist = pytz.timezone('Asia/Kolkata')

    # Convert the timestamp to a datetime object in IST
    timestamp_dt = datetime.fromtimestamp(timestamp, ist)

    # Get the current time in IST
    current_time = datetime.now(ist)

    # Verify that the QR code is still valid (within 5 minutes)
    time_diff = current_time - timestamp_dt
    if time_diff > timedelta(minutes=5):
        return HttpResponseBadRequest("QR code has expired.")
    
    # Recreate the hash using the secret key, email, and timestamp
    data_to_hash = f"{user_email}{timestamp}"
    expected_hash = hmac.new(SECRET_KEY.encode(), data_to_hash.encode(), hashlib.sha256).hexdigest()
    
    # Compare the received hash with the expected hash
    if not hmac.compare_digest(expected_hash, received_hash):
        return HttpResponseBadRequest("Invalid QR code.")
    
    # Get MAC address and serial number
    mac_address = get_mac_address(get_client_ip(request))
    serial_number = get_device_serial_number()

    # Check if the email, MAC address, and serial number match any record in the Device model
    device_record = Device.objects.filter(email=user_email, mac_address=mac_address, serial_number=serial_number).first()

    if device_record:
        context = {
            "email": user_email,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "college_location": COLLEGE_LOCATION,
            "mac_address": mac_address,
            "serial_number": serial_number,
            "device_info": device_record
        }
    else:
        context = {
            "email": user_email,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "college_location": COLLEGE_LOCATION,
            "mac_address": mac_address,
            "serial_number": serial_number,
            "message": "Not match in our record."
        }

    return render(request, 'location_verification.html', context)


def test1_form(request):
    current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')  # Format as needed
    if request.method == 'POST':
        form = Test1Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')  # Redirect to a success page or another view
    else:
        form = Test1Form()

    return render(request, 'test1_form.html', {'form': form, 'current_time': current_time})

def success(request):
    return render(request, 'success.html')
