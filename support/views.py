from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from login.models import User as LoginUser
from .models import SupportTicket, LoginSupportTicket
from .serializers import (
    SupportTicketCreateSerializer,
    SupportTicketDetailSerializer,
    SupportMessageCreateSerializer,
    LoginSupportTicketSerializer
)


class CreateSupportTicketAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SupportTicketCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(
            SupportTicketDetailSerializer(ticket).data,
            status=201
        )


class MySupportTicketsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = SupportTicket.objects.filter(
            created_by=request.user
        )
        serializer = SupportTicketDetailSerializer(tickets, many=True)
        return Response(serializer.data)


class SupportTicketDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id):
        ticket = get_object_or_404(SupportTicket, id=ticket_id)

        if ticket.created_by != request.user and request.user.role not in (
            LoginUser.ROLE_HR,
            LoginUser.ROLE_MANAGEMENT,
            LoginUser.ROLE_IT,
        ):
            return Response({"detail": "Not allowed"}, status=403)

        return Response(
            SupportTicketDetailSerializer(ticket).data
        )


class SendSupportMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        ticket = get_object_or_404(SupportTicket, id=ticket_id)

        if (
            ticket.created_by != request.user and
            request.user.role not in (
                LoginUser.ROLE_HR, LoginUser.ROLE_MANAGEMENT, LoginUser.ROLE_IT)
        ):
            return Response({"detail": "Not allowed"}, status=403)

        if ticket.status == 'CLOSED':
            return Response(
                {"detail": "Ticket is closed"},
                status=400
            )

        serializer = SupportMessageCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'ticket': ticket
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Sent"})


class SupportQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in (
            LoginUser.ROLE_HR,
            LoginUser.ROLE_MANAGEMENT,
            LoginUser.ROLE_IT,
        ):
            return Response({"detail": "Not allowed"}, status=403)

        tickets = SupportTicket.objects.exclude(status='CLOSED')
        return Response(
            SupportTicketDetailSerializer(tickets, many=True).data
        )


class CreateLoginSupportTicketAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSupportTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Your login issue has been reported. Support will contact you."
            },
            status=201
        )
