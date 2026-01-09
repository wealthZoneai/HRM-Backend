from rest_framework import serializers
from .models import SupportTicket, SupportMessage, LoginSupportTicket


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ('category', 'priority', 'subject')

    def create(self, validated_data):
        user = self.context['request'].user
        return SupportTicket.objects.create(
            created_by=user,
            **validated_data
        )


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_role = serializers.CharField(
        source='sender.role', read_only=True
    )

    class Meta:
        model = SupportMessage
        fields = ('id', 'sender', 'sender_role', 'message', 'created_at')


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'subject', 'category', 'priority',
            'status', 'assigned_to',
            'created_at', 'messages'
        )


class SupportMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ('message',)

    def create(self, validated_data):
        request = self.context['request']
        ticket = self.context['ticket']

        return SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=validated_data['message']
        )

class LoginSupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSupportTicket
        fields = ('email_or_empid', 'issue_type', 'message')

    def validate_email_or_empid(self, value):
        if not value.strip():
            raise serializers.ValidationError("Email or Employee ID is required.")
        return value
