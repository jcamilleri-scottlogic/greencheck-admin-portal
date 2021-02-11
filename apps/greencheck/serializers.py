import ipaddress

from rest_framework import serializers

from apps.accounts.models import Hostingprovider

from .models import GreencheckIp, GreenPresenting


class IPDecimalField(serializers.DecimalField):
    """
    A TGWF specific decimal field to account for the fact that
    we represent an IP address internall wth MySQL as a Decimal
    type, but we exposes it as a set of octets for ipv4, and
    an ipv6 representation
    """

    def to_representation(self, instance):
        """
        Convert a string or integer based ip
        address, and convert to a readable
        string.
        """
        addr = ipaddress.ip_address(instance)
        return str(addr)

    def to_internal_value(self, data):
        """
        Convert a octet based ip address into
        a native python ip address
        """
        addr = ipaddress.ip_address(data)
        return addr


class UserFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    A subclass of the normal PrimaryKeyRelatedField, that restricts choices to
    entities that have a relation back to the authenticated user.
    """

    def get_queryset(self):
        """
        This override restricts the possible options we show in an API
        documentation to just the hostingproviders that are related
        to the user. We want every IP range to correspond to a hosting
        provider, but we also want an authenticated user to only be able
        to update their own provider via the API.
        """
        request = self.context.get("request", None)
        queryset = super(UserFilteredPrimaryKeyRelatedField, self).get_queryset()
        if not request:
            return queryset
        return queryset.filter(user=request.user)


class GreenIPRangeSerializer(serializers.ModelSerializer):

    ip_start = IPDecimalField(max_digits=39, decimal_places=0)
    ip_end = IPDecimalField(max_digits=39, decimal_places=0)
    hostingprovider = UserFilteredPrimaryKeyRelatedField(
        queryset=Hostingprovider.objects.all()
    )

    def validate(self, data):
        """
        Check that start is before finish.
        """

        start = data["ip_start"]
        end = data["ip_end"]
        if start > end:
            raise serializers.ValidationError(
                "The IP range must start with a lower IP than the end IP"
            )
        return data

    class Meta:
        model = GreencheckIp
        fields = ["ip_start", "ip_end", "hostingprovider", "id"]


class GreenDomainSerializer(serializers.ModelSerializer):
    """
    The serialiser for our green domains checking table.
    """

    class Meta:
        model = GreenPresenting
        fields = [
            "url",
            "hosted_by",
            "hosted_by_website",
            "partner",
            "green",
            "hosted_by_id",
            "modified",
        ]


class GreenDomainBatchSerializer(serializers.Serializer):

    urls = serializers.FileField()

