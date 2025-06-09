from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import SMEUser
from .models import VoiceTextEntry
from .models import FinancialRecord
from rest_framework import serializers



class SMEUserSerializer(serializers.ModelSerializer):
    pin = serializers.CharField(write_only=True, min_length=4, max_length=8)

    class Meta:
        model = SMEUser
        fields = ['first_name', 'last_name', 'phone_number', 'username', 'email', 'pin']

    def create(self, validated_data):
        return SMEUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    pin = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        pin = data.get('pin')

        user = authenticate(username=username, password=pin)
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        data['user'] = user
        return data


class VoiceTextEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceTextEntry
        fields = ['text']

class FinancialRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = '__all__'
