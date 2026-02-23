from .models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import WorkerProfile

class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email=serializers.EmailField()
    username = serializers.CharField()

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password']!= data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
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