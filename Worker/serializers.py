from rest_framework import serializers
from Authentication.models import WorkerProfile,UserProfile

class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = ["profile_image","profile_image_id"]

class WorkerPersonalInfoSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "username",  
            "email",
            "full_name",
            "phone",
            "date_of_birth",
        ]

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits")
        if value and len(value) != 10:
            raise serializers.ValidationError("Phone must be exactly 10 digits")
        return value
    
class WorkerBannerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = [
            "banner_image",
            "banner_image_id",
        ]