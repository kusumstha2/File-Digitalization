# Generated by Django 5.1.7 on 2025-04-10 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Backup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(upload_to="backup_documents/")),
                ("name", models.CharField(max_length=255)),
                ("added_date", models.DateTimeField(auto_now_add=True)),
                (
                    "file_type",
                    models.CharField(
                        choices=[("private", "Private"), ("public", "Public")],
                        default="private",
                        max_length=10,
                    ),
                ),
                ("is_approved", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(default=1, max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file", models.FileField(unique=True, upload_to="documents/")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("added_date", models.DateTimeField(auto_now_add=True)),
                (
                    "file_type",
                    models.CharField(
                        choices=[("private", "Private"), ("public", "Public")],
                        default="private",
                        max_length=10,
                    ),
                ),
                ("is_approved", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="FileActivityLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("upload", "Upload"),
                            ("approve", "Approve"),
                            ("reject", "Reject"),
                            ("download", "Download"),
                            ("share", "Share"),
                            ("comment", "Comment"),
                        ],
                        max_length=10,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="FileApproval",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("request_date", models.DateTimeField(auto_now_add=True)),
                ("decision_date", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="OCRData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("extracted_text", models.TextField()),
            ],
        ),
    ]
