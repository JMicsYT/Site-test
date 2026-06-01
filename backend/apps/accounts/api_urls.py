from rest_framework import routers, viewsets, permissions

from .models import User
from .serializers import UserSerializer


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    search_fields = ["email", "first_name", "last_name"]


router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls

