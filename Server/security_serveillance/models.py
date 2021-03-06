# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Snapshots(models.Model):
    # Auto updated when data is inserted
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when data is altered
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    # This field will store the snapshot of detected object
    picture = models.ImageField(upload_to='pictures')
    # The video url is localtunnel url to access the localhost and view the
    # camera live
    video_url = models.CharField(max_length=255, null=True)

    def __str__(self):
        return str(self.id)


class AlertChoice(models.Model):
    # Auto updated when data is inserted
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when data is altered
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    alert_status = models.CharField(
        max_length=255, null=True)  # stores the statuses of alert
    # remembers the object and helps to avoid resending the same message again

    def __str__(self):
        return self.alert_status


class AlertRecord(models.Model):
          # Auto updated when data is inserted
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    # Auto updated when data is altered/changed
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    # remembers the object and helps to avoid resending the same message again
    sms_record = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.sms_record
