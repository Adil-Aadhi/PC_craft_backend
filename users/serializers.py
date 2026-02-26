from rest_framework import serializers
from Authentication.models import UserProfile,User
from .models import Address
import re
from Worker.models import ChatRoom,ChatMessage
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError



class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email","role"]

class ProfileSerializer(serializers.ModelSerializer):
    user=UserMiniSerializer(read_only=True)

    class Meta:
        model=UserProfile
        fields = [
            "id",
            "user",
            "full_name",
            "phone",
            "date_of_birth",
            "profile_image",
        ]

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["full_name", "phone", "date_of_birth"]

    def validate_full_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Full name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value

class ProfileImageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserProfile
        fields = ["profile_image", "profile_image_id"]
        ref_name = "UserProfileImage"

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields= "__all__"
        read_only_fields = ["user"]


class ChatListSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "room_name",
            "other_user",
            "last_message",
            "last_message_time",
            "unread_count",
        ]

    # 👇 PASTE HERE — inside class
    def get_other_user(self, obj):
        request_user = self.context["request"].user

        other = obj.participants.exclude(id=request_user.id).first()

        if not other:
            return None

        profile = getattr(other, "userprofile", None)

        full_name = profile.full_name if profile and profile.full_name else other.username
        profile_image = (
            profile.profile_image.url
            if profile and profile.profile_image
            else None
        )

        return {
            "id": other.id,
            "full_name": full_name,
            "profile_image": profile_image,
        }

    def get_last_message(self, obj):
        last_msg = ChatMessage.objects.filter(
            room_name=obj.room_name
        ).order_by("-timestamp").first()

        return last_msg.message if last_msg else ""

    def get_last_message_time(self, obj):
        last_msg = ChatMessage.objects.filter(
            room_name=obj.room_name
        ).order_by("-timestamp").first()

        return last_msg.timestamp if last_msg else None

    def get_unread_count(self, obj):
        request_user = self.context["request"].user

        return ChatMessage.objects.filter(
            room_name=obj.room_name,
            is_seen=False
        ).exclude(sender=request_user).count()
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # 🔐 Check old password
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": ["Old password is incorrect"]}
            )

        # 🔐 Match new passwords
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": ["Passwords do not match"]}
            )

        # 🔐 New must be different
        if old_password == new_password:
            raise serializers.ValidationError(
                {"new_password": ["New password must be different from old password"]}
            )

        # 🔐 Custom strength rules (same as frontend)
        errors = []

        if len(new_password) < 8:
            errors.append("Minimum 8 characters required")

        if not re.search(r"[A-Z]", new_password):
            errors.append("At least one uppercase letter required")

        if not re.search(r"[0-9]", new_password):
            errors.append("At least one number required")

        if not re.search(r"[^A-Za-z0-9]", new_password):
            errors.append("At least one special character required")

        # 🔐 Django built-in validators
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            errors.extend(e.messages)

        if errors:
            raise serializers.ValidationError({"new_password": errors})

        return data