from rest_framework import parsers, status, serializers, viewsets, mixins, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
import segno
import io
import base64
import datetime

from .serializers import (
    DigitalGreenCertificateVerificationSerializer,
    VaccinationSerializer,
    RecoverySerializer,
    TestSerializer,
    PersonSerializer,
    NotifierSerializer,
    DigitalGreenCertificateSerializer,
    ObtainJWTPairSerializer,
)
from .models import SignedToken, Notifier, Manager, DigitalGreenCertificate
from .permissions import IsManager, IsNotifier
from moonshot.settings import SIGNING_CERTIFICATE_FILE, SIGNING_CERTIFICATE_KEY_FILE


def __generate_qr_base64(token: str):
    qr = segno.make(str(base64.b64encode(token.token), "utf-8"))
    buff = io.BytesIO()
    qr.save(buff, kind="png", scale=10)
    qr = buff.getvalue()
    buff.close()
    qr = str(base64.b64encode(qr), "utf-8")

    return qr


def create_digital_green_certificate(request, ser, cert_type):
    if ser.is_valid():
        payload = ser.validated_data
        user = request.user
        notifier = Notifier.objects.filter(user=user).first()

        ser.validated_data["health_professional_id"] = notifier
        ser.save()

        dgc = DigitalGreenCertificate(notifier=notifier, certificate_type=cert_type)
        dgc.gen_uvci()
        dgc.save()

        until = datetime.datetime.now() + datetime.timedelta(days=365)
        metadata = {
            "issuer": "Moonshot PT",
            "identifier": dgc.uvci,
            "valid_from": datetime.datetime.now().strftime("%Y-%m-%d"),
            "valid_until": until.strftime("%Y-%m-%d"),
            "schema_version": "1.0.0",
        }

        information = {}
        for key, val in ser.data.items():
            if key not in ["person", "id"]:
                information[key] = val

        person = PersonSerializer(payload.get("person"))
        certificate = {
            "person_identification": person.data,
            "information": information,
            "metadata": metadata,
        }

        token = SignedToken(record=certificate)
        token.gen_jws(
            cert_file=SIGNING_CERTIFICATE_FILE, key_file=SIGNING_CERTIFICATE_KEY_FILE
        )

        dgc.qrcode = __generate_qr_base64(token)
        dgc.save()

        return {
            "uvci": dgc.uvci,
            "qrcode": dgc.qrcode,
            "token": token.token,
        }
    else:
        raise serializers.ValidationError(ser.errors)


class VaccinationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = VaccinationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        notifier = Notifier.objects.filter(user=user).first()
        if not notifier:
            return []
        return notifier.vaccination_set.all()

    def create(self, request):
        # To prevent Managers from creating DGC
        if Manager.objects.filter(user=request.user).first() is not None:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                content_type="application/json",
            )

        ser = VaccinationSerializer(data=request.data)
        try:
            cert = create_digital_green_certificate(request, ser, "VC")
            return Response(
                data=cert,
                status=status.HTTP_201_CREATED,
                content_type="application/json",
            )
        except serializers.ValidationError as e:
            return Response(
                data={"error": e.args},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )


class RecoveryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RecoverySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        notifier = Notifier.objects.filter(user=user).first()
        if not notifier:
            return []
        return notifier.recovery_set.all()

    def create(self, request):
        # To prevent Managers from creating DGC
        if Manager.objects.filter(user=request.user).first() is not None:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                content_type="application/json",
            )

        ser = RecoverySerializer(data=request.data)
        try:
            cert = create_digital_green_certificate(request, ser, "RE")
            return Response(
                data=cert,
                status=status.HTTP_201_CREATED,
                content_type="application/json",
            )
        except serializers.ValidationError as e:
            return Response(
                data={"error": e.args},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )


class TestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        notifier = Notifier.objects.filter(user=user).first()
        if not notifier:
            return []
        return notifier.test_set.all()

    def create(self, request):
        # To prevent Managers from creating DGC
        if Manager.objects.filter(user=request.user).first() is not None:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                content_type="application/json",
            )

        ser = TestSerializer(data=request.data)
        try:
            cert = create_digital_green_certificate(request, ser, "TE")
            return Response(
                data=cert,
                status=status.HTTP_201_CREATED,
                content_type="application/json",
            )
        except serializers.ValidationError as e:
            return Response(
                data={"error": e.args},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )


class NotifierViewSet(viewsets.ModelViewSet):
    serializer_class = NotifierSerializer
    permission_classes = [IsManager | IsNotifier]
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        user = self.request.user
        # If anonymous, return None
        if not user.is_authenticated:
            return None
        # If staff return all Notifiers
        if user.is_staff:
            return Notifier.objects.all()

        # If manager, return all Notifiers of its Labs
        man = Manager.objects.filter(user=user).first()
        if man is not None:
            labs = man.laboratories.all()
            return Notifier.objects.distinct().filter(laboratories__in=labs)

        # Else return itself
        notifier = Notifier.objects.filter(user=user)
        return notifier


class DigitalGreenCertificateViewSet(viewsets.ModelViewSet):
    serializer_class = DigitalGreenCertificateSerializer
    permission_classes = [IsAuthenticated & IsNotifier]
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        user = self.request.user

        # If anonymous, return None
        if not user.is_authenticated:
            return None

        # if staff return all Certificates
        if user.is_staff:
            return DigitalGreenCertificate.objects.all()

        # if manager return all certificates issued by notifiers of its labs
        man = Manager.objects.filter(user=user).first()
        if man is not None:
            labs = man.laboratories.all()
            nots = Notifier.objects.distinct().filter(laboratories__in=labs)
            return DigitalGreenCertificate.objects.filter(notifier__in=nots)

        # else return certificates issued by him
        notifier = Notifier.objects.filter(user=user).first()
        return DigitalGreenCertificate.objects.filter(notifier=notifier).all()

    def retrieve(self, request, pk):
        try:
            query = DigitalGreenCertificate.objects.get(uvci=pk)
            serializer = DigitalGreenCertificateSerializer(query)
            return Response(serializer.data)
        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Digital Green Certificate not found."},
            )


class DigitalGreenCertificateVerificationViewSet(generics.ListAPIView):
    serializer_class = DigitalGreenCertificateVerificationSerializer
    permission_classes = []

    def get(self, request):
        token = SignedToken(token=request.GET.get("token", None))
        is_valid = token.validate_jws(key_file=SIGNING_CERTIFICATE_KEY_FILE)

        return Response({"valid": is_valid})


class HealthViewSet(generics.RetrieveAPIView):
    serializer_class = None
    permission_classes = []

    def get(self, request):
        return Response({"healthy": True})


class ObtainJWTPairView(TokenObtainPairView):
    serializer_class = ObtainJWTPairSerializer
