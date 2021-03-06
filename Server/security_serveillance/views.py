# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File  # This is to save the raw file in db
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Snapshots, AlertChoice, AlertRecord
import os  # This is to execute the command in cmd
import json
import sms_alert  # Import this module to send text messages
from pushetta import Pushetta
from time import gmtime, strftime
from datetime import datetime

API_KEY = "367b8608009bf4e0fa9e68794305c6c6d84a07a2"
CHANNEL_NAME = "LMTech"
p = Pushetta(API_KEY)


mobile_number = '8983050329'
# Mobile number to which the alert message will be sent
media_path = 'http://13.126.171.131:8000/media/'


@login_required
@csrf_exempt   # post required response was creating an assertion error
def page_load(request):  # http://127.0.0.1:8000/
    if request.method == 'GET':

        global analysis  # Declare a global list var to use it in get function
        video_url = str(Snapshots.objects.latest('id').video_url)

        # Declare an empty list to send response
        analysis = [{'video_url': video_url, 'label': '',
                     'confidence': '', }]
        # Here, analysis list is declared because if RPi is not posting any
        # data then there will not be any variable 'analysis in get request

        try:
            # Get the status of all alerts from the database
            latest_alert_status = AlertChoice.objects.latest('id').alert_status
            status_list = latest_alert_status.split(',')
            # Make a list of those string formatted alert status
        except:  # if there is no data about alert status
            print('Setting initial values for the alerts to false')
            alerts = "false,false,false,false,false,false,false"
            alert_status = AlertChoice(alert_status=alerts)
            alert_status.save()  # save alerts in database

            latest_alert_status = AlertChoice.objects.latest('id').alert_status
            status_list = latest_alert_status.split(',')

        object_list = ['Person', 'Knife',
                       'Handbag', 'Bottle', 'Dog', 'Cat', 'Car']
        # Make a dict of object and its alert-status
        alert_states = dict(zip(map(str, object_list), map(str,
                                                           status_list)))
        context = {
            "alert_states": json.dumps(alert_states),
            "video_url": json.dumps(video_url)
        }
        return render(request, "security_serveillance/home_page.html", context)

    if request.method == 'POST':
        alert_status_string = request.POST.get('alerts')
        # Save the selected alerts only if there is change in status
        alert_list = alert_status_string.split(',')
        if 'true' in alert_list:
            response = 'SMS alerts are active!'
        else:
            response = 'SMS alerts are inactive!'
        try:
            # Get the existing latest status of alert choices
            latest_alert_status = AlertChoice.objects.latest('id').alert_status
        except:  # If there is no alert status in database
            print 'No alerts were saved in database'
            latest_alert_status = 0  # Flag that there were no alert status
        if latest_alert_status == 0 or \
                (latest_alert_status != alert_status_string):
            # User has changed the status of alerts
            # Therefore save the alert status in Database
            alert_update = AlertChoice(alert_status=alert_status_string)
            alert_update.save(force_insert=True)
            print 'Database updated with current alert status!'
        return HttpResponse(response)


class PredictImageObject(APIView):    # http://127.0.0.1:8000/predict/

    def alert(self, detected_object, file_path):  # give alerts on pushetta andorid app
        try:
            ct = str(datetime.now())
            current_time = ct[11:19]
            msg = 'Time: ' + current_time + '\n' + detected_object + ' has been detected!\n'
            msg += 'You can visit the following link to see the snapshot.\n' + file_path
            p.pushMessage(CHANNEL_NAME, msg)
        except:
            print 'Message sending Failed!'

    def check_alerts(self, predicted_objects, confidence, file_path):
        print('Checking for alerts...')
        # Get the latest status of activated alerts from the database
        latest_alert_status = AlertChoice.objects.latest('id').alert_status
        status_list = latest_alert_status.split(',')
        # Make a list of those string formatted alert status

        try:
            latest_sms_record = AlertRecord.objects.latest('id').sms_record
            sms_list = latest_sms_record.split(',')
        except:  # if no record found in db then create one
            print 'No record found for sms'
            dummy_record = 'no_sms,'
            query = AlertRecord(sms_record=dummy_record)
            query.save(force_insert=True)
            print 'Therefore, created new sms record'

        # Check if the object is detected and alert for that object is ON
        # Call alert method to send text message
        sms_sent = ''  # remembers that which sms has been sent
        if (('person' in predicted_objects) and status_list[0] == 'true' and ('person' not in sms_list)) and ('no_person' in sms_list):
            self.alert('Person', file_path)
            sms_sent += 'person,'

        elif ('person' not in predicted_objects) and status_list[0] == 'true':
            sms_sent += 'no_person,'

        if (('knife' in predicted_objects) and status_list[1] == 'true' and ('knife' not in sms_list)) and ('no_knife' in sms_list):
            self.alert('Knife')
            sms_sent += 'knife,'
        elif ('knife' not in predicted_objects) and status_list[1] == 'true':
            sms_sent += 'no_knife,'

        if (('handbag' in predicted_objects) and status_list[2] == 'true' and ('handbag' not in sms_list)) and ('no_handbag' in sms_list):
            self.alert('Handbag')
            sms_sent += 'handbag,'
        elif ('handbag' not in predicted_objects) and status_list[2] == 'true':
            sms_sent += 'no_handbag,'

        if (('bottle' in predicted_objects) and status_list[3] == 'true' and ('bottle' not in sms_list)) and ('no_bottle' in sms_list):
            self.alert('Bottle')
            sms_sent += 'bottle,'
        elif ('bottle' not in predicted_objects) and status_list[3] == 'true':
            sms_sent += 'no_bottle,'

        if (('dog' in predicted_objects) and status_list[4] == 'true' and ('dog' not in sms_list)) and ('no_dog' in sms_list):
            self.alert('Dog')
            sms_sent += 'dog,'
        elif ('dog' not in predicted_objects) and status_list[4] == 'true':
            sms_sent += 'no_dog,'

        if (('cat' in predicted_objects) and status_list[5] == 'true' and ('cat' not in sms_list)) and ('no_cat' in sms_list):
            self.alert('Cat')
            sms_sent += 'cat,'
        elif ('cat' not in predicted_objects) and status_list[5] == 'true':
            sms_sent += 'no_cat,'

        if (('car' in predicted_objects) and status_list[6] == 'true' and ('car' not in sms_list)) and ('no_car' in sms_list):
            self.alert('Car')
            sms_sent += 'car,'
        elif ('car' not in predicted_objects) and status_list[6] == 'true':
            sms_sent += 'no_car,'

        if sms_sent:   # remember the sent messages
            # Get the existing latest status of sms sent
            latest_sms_record = AlertRecord.objects.latest('id').sms_record
            if latest_sms_record == sms_sent:
                pass  # do not save sms record in db again
                print('SMS Record has not been duplicatd!')
            else:
                alert_record = AlertRecord(sms_record=sms_sent)
                alert_record.save()
                print('SMS Record has been saved!')

    def post(self, request):  # RPi will post the detected objects on this url
        global predicted_objects  # Holds the list of detected objects
        predicted_objects = []

        global confidence  # Holds the list of probability of detected objects
        confidence = []

        global analysis  # Declare a global list var to use it in get function
        analysis = []    # Declare an empty list to send response
        # to display the message/status
        print 'Posted data:', request.data

        if request.data['message'] == ['abort']:  # clear the o/p screen
            print('Termination of post request from RPi!')
            video_url = request.data['video_url']
            while len(analysis) < 8:
                analysis.append({
                    'label': '',
                    'confidence': '',
                    'file_path': 'http://13.126.171.131:8000/info',
                    'video_url': str(video_url)
                })
            sms_sent = 'no_person,no_knife,no_handbag,no_bottle,no_dog,no_cat,no_car'
            alert_record = AlertRecord(sms_record=sms_sent)
            alert_record.save()
            return HttpResponse("Abort Response")

        try:
            if request.data['message'] == 'snapshot':
                media_file = Snapshots(picture=request.FILES[
                                       'snapshot'], video_url=request.data['video_url'])
                media_file.save()  # Save the snapshot in database
        except:
            print 'Error occurred while saving the snapshot'

        try:
            # Get the saved latest snapshot image name and path to show when
            # clicked on detected object
            file_path = media_path + \
                str(Snapshots.objects.latest('id').picture)
            video_url = request.data['video_url']  # provides live streaming

            for key, value in request.data.items():
                print key, value, str(value)[:5], str(file_path), str(video_url)
                if key == 'snapshot' or key == 'tv' or key == 'video_url' or key == 'message':
                    continue  # Do not consider these key as detected objects
                else:
                    predicted_objects.append(key)
                    confidence.append(value)
                    # Dict(json object) to give at frontend in get method
                    analysis.append({
                        'label': key,
                        'confidence': str(value)[:5],
                        'file_path': str(file_path),
                        'video_url': str(video_url)
                    })

            # Logic to remove previous data from the table
            while len(analysis) < 8:
                analysis.append({
                    'label': '',
                    'confidence': '',
                    'file_path': str(file_path),
                    'video_url': str(video_url)
                })

            self.check_alerts(predicted_objects, confidence, file_path)
            # Check whether SMS alerts are active for detected object so that
            # we can se the text message
        except:
            print 'Failed to get the detected objects!'
        return HttpResponse("Alright!")

    @csrf_exempt
    def get(self, request):
        return Response(analysis)


def info_page(request):  # http://127.0.0.1:8000/info/
    if request.method == 'GET':
        return HttpResponse('''<h2>
            Data is Unavailable!
            <br>
            This may happened because there was no significant information that device could send.
            </h2>''')
