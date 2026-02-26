from .models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
import re
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError 

class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email=serializers.EmailField()
    username = serializers.CharField()

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

         # ✅ Match passwords
        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        
        # ✅ Password strength validation
        errors = []

        if len(password) < 8:
            errors.append("Minimum 8 characters required")

        if not re.search(r"[A-Z]", password):
            errors.append("At least one uppercase letter required")

        if not re.search(r"[0-9]", password):
            errors.append("At least one number required")

        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("At least one special character required")

        if errors:
            raise serializers.ValidationError({"password": errors})
        
        role = self.context.get('role')
        if role not in ['user', 'worker']:
            raise serializers.ValidationError("Invalid role")
        
        return data
    
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        role = self.context.get('role') 
        
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')

        full_name = validated_data.pop('full_name')

        user = User.objects.create_user(
            password=password,
            role=role,
            **validated_data
        )

        user.user_profile.full_name = full_name
        user.user_profile.save()

        return user
    
class UserMiniSerializer(serializers.ModelSerializer):
    kyc_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
    
class LoginSerializer(serializers.Serializer):

    username=serializers.CharField()
    password=serializers.CharField(write_only=True)

    def validate(self,data):
        user=authenticate(username=data['username'],password=data['password'])

        if not user:
            raise serializers.ValidationError("Email or password is mismatched")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")
        
        data["user"] = user
        
        # data['user_data'] = UserMiniSerializer(user).data

        return data
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        errors = []

        # 🔹 Custom strength rules (same as frontend)
        if len(value) < 8:
            errors.append("Minimum 8 characters required")

        if not re.search(r"[A-Z]", value):
            errors.append("At least one uppercase letter required")

        if not re.search(r"[0-9]", value):
            errors.append("At least one number required")

        if not re.search(r"[^A-Za-z0-9]", value):
            errors.append("At least one special character required")

        # 🔹 Django built-in validators (common passwords, numeric-only, etc.)
        try:
            validate_password(value)
        except DjangoValidationError as e:
            errors.extend(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        return value