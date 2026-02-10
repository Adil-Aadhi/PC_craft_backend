from rest_framework import serializers
from Authentication.models import WorkerProfile,UserProfile
from .models import WorkerKycProgress

class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = ["profile_image","profile_image_id"]
        ref_name = "WorkerProfileImage"

class WorkerPersonalInfoSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    gender = serializers.CharField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "username",  
            "email",
            "full_name",
            "phone",
            "date_of_birth",
            "gender",
        ]

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits")
        if value and len(value) != 10:
            raise serializers.ValidationError("Phone must be exactly 10 digits")
        return value
    
    def update(self, instance, validated_data):
        """
        instance = UserProfile
        """

        # 🔹 1. Extract gender BEFORE calling super()
        gender = validated_data.pop("gender", None)

        # 🔹 2. Update UserProfile normally
        user_profile = super().update(instance, validated_data)

        # 🔹 3. Update WorkerProfile manually
        if gender is not None:
            worker = user_profile.user.worker_profile
            worker.gender = gender
            worker.save(update_fields=["gender"])

        return user_profile

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["gender"] = getattr(
            instance.user.worker_profile,
            "gender",
            None
        )
        return data
    
class WorkerBannerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = [
            "banner_image",
            "banner_image_id",
        ]

class WorkerKycProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerKycProgress
        fields = ["current_step", "progress"]

    def validate_current_step(self, value):
        if value < 0 or value > 4:
            raise serializers.ValidationError("Invalid KYC step")
        return value