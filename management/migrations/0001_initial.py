# Generated by Django 3.2.16 on 2023-01-12 01:32

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', markdownx.models.MarkdownxField()),
                ('slug', models.SlugField(allow_unicode=True, blank=True, max_length=300, null=True, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('edited_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Announcement',
                'verbose_name_plural': 'Announcements',
            },
        ),
    ]
