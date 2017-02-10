# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-10 10:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdyenIssuer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=200)),
                ('adyen_id', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='AdyenNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification', models.TextField()),
                ('is_processed', models.BooleanField(default=False)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AdyenPaymentOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=200)),
                ('adyen_name', models.CharField(default='', max_length=200)),
                ('guid', models.CharField(default='', max_length=36, verbose_name='GUID')),
                ('image', models.ImageField(null=True, upload_to='')),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='adyenissuer',
            name='payment_option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='djadyen.AdyenPaymentOption'),
        ),
    ]
