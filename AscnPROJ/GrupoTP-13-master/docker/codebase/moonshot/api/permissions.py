from rest_framework.permissions import BasePermission
from .models import Manager, Notifier


class IsManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user is None or not user.is_authenticated:
            return False
        man = Manager.objects.filter(user=user).first()
        return man is not None


class IsNotifier(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user is None or not user.is_authenticated:
            return False
        noti = Notifier.objects.filter(user=user).first()
        return noti is not None
