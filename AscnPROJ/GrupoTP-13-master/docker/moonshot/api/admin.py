from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission

from .models import (
    User,
    Laboratory,
    Notifier,
    Manager,
    Vaccination,
    Person,
    Recovery,
    Test,
    DigitalGreenCertificate,
)


class NotifierInline(admin.StackedInline):
    model = Notifier


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Define admin model for custom User model without username
    """

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Relevant dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    list_display = ("email", "first_name", "last_name", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    inlines = [
        NotifierInline,
    ]


class LaboratoryNotifiersInline(admin.StackedInline):
    model = Notifier.laboratories.through
    extra = 1


class LaboratoryManagersInline(admin.StackedInline):
    model = Manager.laboratories.through
    extra = 1


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "nif", "ers_number", "telephone")
    search_fields = ("name", "nif", "ers_number", "telephone")
    inlines = [
        LaboratoryNotifiersInline,
        LaboratoryManagersInline,
    ]
    pass


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Notifier)
class NotifierAdmin(admin.ModelAdmin):
    list_display = ("user", "nic")
    pass


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("user",)
    pass


class VaccinationInline(admin.StackedInline):
    model = Vaccination
    extra = 0


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = (
        "vaccine",
        "marketing_authorization_holder",
        "dosage_number",
        "vaccination_date",
        "health_professional_id",
        "person",
        "administering_centre",
    )
    pass


class RecoveryInline(admin.StackedInline):
    model = Recovery
    extra = 0


@admin.register(Recovery)
class RecoveryAdmin(admin.ModelAdmin):
    list_display = (
        "disease",
        "first_positive_test_date",
        "country",
        "health_professional_id",
        "person",
    )
    pass


class TestInline(admin.StackedInline):
    model = Test
    extra = 0


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        "test_type",
        "test_name",
        "sample_collection_date_time",
        "health_professional_id",
        "person",
    )
    pass


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [
        VaccinationInline,
        RecoveryInline,
        TestInline,
    ]
    pass


@admin.register(DigitalGreenCertificate)
class DigitalGreenCertificateAdmin(admin.ModelAdmin):
    list_display = (
        "uvci",
        "notifier",
        "created_at",
        "certificate_type",
    )
    search_fields = (
        "uvci",
        "certificate_type",
    )
    pass
