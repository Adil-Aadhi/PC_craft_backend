from rest_framework import serializers
from Authentication.models import WorkerProfile,UserProfile
from .models import WorkerKycProgress,ChatRequest,WorkerIdentityKYC,WorkerPayoutDetails
from Authentication.models import User

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
    
class ChatRequestCreateSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ChatRequest
        fields = ["id", "receiver_id", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_receiver_id(self, value):
        request = self.context["request"]
        sender = request.user

        if sender.id == value:
            raise serializers.ValidationError("You cannot send request to yourself")

        try:
            receiver = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Receiver not found")

        # check receiver is worker
        if not hasattr(receiver, "worker_profile"):
            raise serializers.ValidationError("You can only chat with workers")

        # prevent duplicate pending request
        if ChatRequest.objects.filter(
            sender=sender,
            receiver=receiver,
            status="pending"
        ).exists():
            raise serializers.ValidationError("Request already sent")

        self.context["receiver"] = receiver
        return value

    def create(self, validated_data):
        sender = self.context["request"].user
        receiver = self.context["receiver"]

        return ChatRequest.objects.create(
            sender=sender,
            receiver=receiver
        )
        
class WorkerListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id")
    name = serializers.CharField(source="user.username")
    has_requested = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorkerProfile
        fields = [
            "user_id",
            "name",
            "rating",
            "skills",
            "profile_image",
            "hourly_rate",
            "has_requested",   # 👈 new
        ]

class ChatRequestActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRequest
        fields = ["status"]

    def validate_status(self, value):
        if value not in ["accepted", "rejected"]:
            raise serializers.ValidationError("Invalid status")
        return value
    

class WorkerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = [
            "description",
            "skills",
            "experience_years",
            "hourly_rate",
        ]

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("Experience cannot be negative")
        return value

    def validate_hourly_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError("Hourly rate must be greater than 0")
        return value

class WorkerIdentityKYCSerializer(serializers.ModelSerializer):
    masked_id_number = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WorkerIdentityKYC
        fields = [
            "id_type",
            "id_number",        # write only
            "masked_id_number", # read only
            "id_front_url",
            "id_front_id",
            "id_back_url",
            "id_back_id",
        ]
        extra_kwargs = {
            "id_number": {"write_only": True},
            "id_back_url": {"required": False, "allow_null": True},
            "id_back_id": {"required": False, "allow_null": True},
        }

    # 🔐 Mask ID number when returning data
    def get_masked_id_number(self, obj):
        if obj.id_number and len(obj.id_number) > 4:
            return "XXXXXX" + obj.id_number[-4:]
        return obj.id_number

    # 🔒 Validation
    def validate(self, data):
        if not data.get("id_front_url"):
            raise serializers.ValidationError(
                {"id_front_url": "Front image is required"}
            )

        if not data.get("id_front_id"):
            raise serializers.ValidationError(
                {"id_front_id": "Front image public_id is required"}
            )

        return data

    # 🔄 Create or Update logic
    def create(self, validated_data):
        user = self.context["request"].user

        kyc, _ = WorkerIdentityKYC.objects.update_or_create(
            user=user,
            defaults=validated_data
        )

        return kyc

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    
class WorkerPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerPayoutDetails
        fields = ["upi_id"]

    def validate_upi_id(self, value):
        if "@" not in value:
            raise serializers.ValidationError("Invalid UPI ID")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        payout, _ = WorkerPayoutDetails.objects.update_or_create(
            user=user,
            defaults=validated_data
        )
        return payout
    
