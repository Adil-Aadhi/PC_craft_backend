from rest_framework import serializers
from Authentication.models import UserProfile,User
from .models import Address
import re


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

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

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields= "__all__"
        read_only_fields = ["user"]