from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Notifier,
    User,
    Vaccination,
    Recovery,
    Test,
    DigitalGreenCertificate,
    Person,
    Laboratory,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class ObtainJWTPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        noti = Notifier.objects.filter(user=user).first()
        if noti is not None:
            token["notifier_id"] = noti.id
        return token


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["id", "name", "nif", "ers_number", "telephone"]


class NotifierSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=False)
    laboratories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Notifier
        fields = ["id", "user", "nic", "laboratories"]

    def create(self, validated_data):
        user = validated_data.pop("user")
        user, _ = User.objects.get_or_create(**user)
        noti = Notifier.objects.create(user=user, **validated_data)
        return noti

    def update(self, instance, validated_data):
        user = validated_data.get("user", None)
        if user is not None:
            instance.user.first_name = user.get("first_name", instance.user.first_name)
            instance.user.last_name = user.get("last_name", instance.user.last_name)
            instance.user.email = user.get("email", instance.user.email)
            instance.user.save()
        instance.nic = validated_data.get("nic", instance.nic)
        instance.save()
        return instance


class DigitalGreenCertificateSerializer(serializers.ModelSerializer):
    qrcode = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)

    class Meta:
        model = DigitalGreenCertificate
        fields = [
            "uvci",
            "notifier",
            "qrcode",
            "content",
            "created_at",
            "certificate_type",
        ]


class DigitalGreenCertificateVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    class Meta:
        fields = ["token"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["name", "date_of_birth", "identifier", "sex"]


class VaccinationSerializer(serializers.ModelSerializer):
    person_identification = PersonSerializer(required=True, source="person")

    class Meta:
        model = Vaccination
        fields = [
            "id",
            "disease",
            "vaccine",
            "medicinal_product",
            "marketing_authorization_holder",
            "dosage_number",
            "batch_number",
            "vaccination_date",
            "administering_centre",
            "country",
            "next_vaccination_date",
            "person_identification",
        ]

    def create(self, validated_data):
        person_id = validated_data.pop("person")
        person, _ = Person.objects.get_or_create(**person_id)
        vacc = Vaccination.objects.create(person=person, **validated_data)
        return vacc


class RecoverySerializer(serializers.ModelSerializer):
    person_identification = PersonSerializer(required=True, source="person")

    class Meta:
        model = Recovery
        fields = [
            "id",
            "disease",
            "first_positive_test_date",
            "country",
            "person_identification",
        ]

    def create(self, validated_data):
        person_id = validated_data.pop("person")
        person, _ = Person.objects.get_or_create(**person_id)
        rec = Recovery.objects.create(person=person, **validated_data)
        return rec


class TestSerializer(serializers.ModelSerializer):
    person_identification = PersonSerializer(required=True, source="person")

    class Meta:
        model = Test
        fields = [
            "id",
            "disease",
            "test_type",
            "test_name",
            "test_manufacturer",
            "sample_origin",
            "sample_collection_date_time",
            "result",
            "testing_centre",
            "country",
            "person_identification",
        ]

    def create(self, validated_data):
        person_id = validated_data.pop("person")
        person, _ = Person.objects.get_or_create(**person_id)
        test = Test.objects.create(person=person, **validated_data)
        return test
